use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;
use tokio::process::{Child, Command};
use tokio::sync::Mutex;

type ProcessEntry = (u32, Child, u16);

pub struct ProcessSupervisor {
    processes: Arc<Mutex<HashMap<String, ProcessEntry>>>,
}

impl ProcessSupervisor {
    pub fn new() -> Self {
        Self { processes: Arc::new(Mutex::new(HashMap::new())) }
    }

    pub async fn spawn_engine(&self, id: &str, bin_path: &Path, work_dir: &Path, port: u16) -> Result<u16, String> {
        let mut map = self.processes.lock().await;
        if let Some((_, child, existing_port)) = map.get_mut(id) {
            match child.try_wait() {
                Ok(None) => return Ok(*existing_port),
                _ => {
                    // Process previously died/crashed, purge stale entry
                    map.remove(id);
                }
            }
        }

        let abs_bin = std::fs::canonicalize(bin_path).unwrap_or_else(|_| bin_path.to_path_buf());
        let abs_work = std::fs::canonicalize(work_dir).unwrap_or_else(|_| work_dir.to_path_buf());

        let ext = abs_bin.extension().and_then(|e| e.to_str()).unwrap_or("");
        let mut cmd = if ext == "py" {
            #[cfg(target_os = "windows")]
            let py_bin = "python";
            #[cfg(not(target_os = "windows"))]
            let py_bin = "python3";
            let mut c = Command::new(py_bin);
            c.arg(&abs_bin);
            c
        } else if ext == "mjs" || ext == "js" {
            let mut c = Command::new("node");
            c.arg(&abs_bin);
            c
        } else if ext == "cmd" || ext == "bat" {
            let mut c = Command::new("cmd");
            c.args(["/C", &abs_bin.to_string_lossy()]);
            c
        } else {
            Command::new(&abs_bin)
        };

        cmd.current_dir(abs_work)
            .stdin(std::process::Stdio::null())
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .env("FLOWORK_APP_PORT", port.to_string())
            .env("FLOWORK_PLUGIN_PORT", port.to_string())
            .env("FLOWORK_CHESS_PORT", port.to_string())
            .env("FLOWORK_SECURITY_PORT", port.to_string())
            .env("FLOWORK_WEBSITE_INTEL_PORT", port.to_string())
            .env("FLOWORK_YOUTUBE_SPY_PORT", port.to_string())
            .env("PORT", port.to_string())
            .kill_on_drop(true);

        #[cfg(unix)]
        cmd.process_group(0);

        let child = cmd.spawn().map_err(|e| format!("Failed to spawn engine: {e}"))?;
        let pid = child.id().unwrap_or(0);
        map.insert(id.to_string(), (pid, child, port));
        Ok(port)
    }

    pub async fn stop_engine(&self, id: &str) -> bool {
        let mut map = self.processes.lock().await;
        if let Some((pid, mut child, _)) = map.remove(id) {
            safe_kill_process_tree(pid).await;
            let _ = child.kill().await;
            // Zero-Zombie Reaper: await termination to release OS socket ports immediately
            let _ = tokio::time::timeout(tokio::time::Duration::from_millis(500), child.wait()).await;
            return true;
        }
        false
    }

    pub async fn stop_all(&self) {
        let mut map = self.processes.lock().await;
        for (_, (pid, mut child, _)) in map.drain() {
            safe_kill_process_tree(pid).await;
            let _ = child.kill().await;
            let _ = tokio::time::timeout(tokio::time::Duration::from_millis(300), child.wait()).await;
        }
    }

    pub async fn get_port(&self, id: &str) -> Option<u16> {
        let mut map = self.processes.lock().await;
        if let Some((_, child, port)) = map.get_mut(id) {
            match child.try_wait() {
                Ok(None) => Some(*port),
                _ => {
                    map.remove(id);
                    None
                }
            }
        } else {
            None
        }
    }

    #[allow(dead_code)]
    pub async fn get_running_engines(&self) -> Vec<(String, u16)> {
        let mut map = self.processes.lock().await;
        let mut running = Vec::new();
        let mut dead = Vec::new();
        for (id, (_, child, port)) in map.iter_mut() {
            match child.try_wait() {
                Ok(None) => running.push((id.clone(), *port)),
                _ => dead.push(id.clone()),
            }
        }
        for id in dead {
            map.remove(&id);
        }
        running
    }

    pub fn get_running_engines_now(&self) -> Vec<(String, u16)> {
        if let Ok(mut map) = self.processes.try_lock() {
            let mut running = Vec::new();
            let mut dead = Vec::new();
            for (id, (_, child, port)) in map.iter_mut() {
                match child.try_wait() {
                    Ok(None) => running.push((id.clone(), *port)),
                    _ => dead.push(id.clone()),
                }
            }
            for id in dead {
                map.remove(&id);
            }
            running
        } else {
            Vec::new()
        }
    }
}

/// Sovereign Process Shield: Safely terminates a process tree without collateral damage.
/// Positively targets ONLY specific PIDs and descendants via pgrep. NEVER uses negative PID or group kill.
pub async fn safe_kill_process_tree(pid: u32) {
    if pid <= 100 {
        eprintln!("[SafeKill] 🛡️ Blocked kill request for reserved/system PID: {pid}");
        return;
    }

    let my_pid = std::process::id();
    if pid == my_pid {
        eprintln!("[SafeKill] 🛡️ Blocked self-kill request (PID: {pid})");
        return;
    }

    #[cfg(unix)]
    {
        let my_pgid = unsafe { libc::getpgrp() as u32 };
        if pid == my_pgid {
            eprintln!("[SafeKill] 🛡️ Blocked kill request matching current process group (PGID: {pid})");
            return;
        }

        // Recursively terminate any child processes safely by explicit positive PID
        if let Ok(output) = std::process::Command::new("pgrep").args(["-P", &pid.to_string()]).output() {
            if let Ok(out_str) = String::from_utf8(output.stdout) {
                for line in out_str.lines() {
                    if let Ok(child_pid) = line.trim().parse::<u32>() {
                        if child_pid > 100 && child_pid != my_pid && child_pid != my_pgid {
                            Box::pin(safe_kill_process_tree(child_pid)).await;
                        }
                    }
                }
            }
        }

        // Positively target ONLY this specific PID - NEVER use negative PID or group kill
        let _ = std::process::Command::new("kill")
            .args(["-9", &pid.to_string()])
            .output();
    }

    #[cfg(windows)]
    {
        let _ = std::process::Command::new("taskkill")
            .args(["/F", "/T", "/PID", &pid.to_string()])
            .output();
    }
}
