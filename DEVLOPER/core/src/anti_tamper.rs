// [FLOWORKOS:SOVEREIGN-ANTI-TAMPER-SHIELD]
// Active Anti-Debugging, Anti-Disassembly, and Process Integrity Enforcement
// Level 3 & Level 4 Defense-in-Depth Hardening

pub struct AntiTamper;

impl AntiTamper {
    /// Enforces active anti-debugger checks across platforms.
    /// Immediately aborts process execution if an interactive tracer,
    /// debugger, or unauthorized memory injector is detected.
    pub fn enforce_shield() {
        #[cfg(all(target_os = "linux", not(test)))]
        {
            if let Ok(status) = std::fs::read_to_string("/proc/self/status") {
                for line in status.lines() {
                    if line.starts_with("TracerPid:") {
                        let pid_str = line.trim_start_matches("TracerPid:").trim();
                        if let Ok(tracer_pid) = pid_str.parse::<i32>() {
                            if tracer_pid != 0 {
                                eprintln!("[Sovereign Guard] 🛑 Access violation: Debugger/tracer attached (PID: {}). Process terminated.", tracer_pid);
                                std::process::exit(1);
                            }
                        }
                    }
                }
            }
        }

        #[cfg(target_os = "windows")]
        {
            extern "system" {
                fn IsDebuggerPresent() -> i32;
                fn CheckRemoteDebuggerPresent(process: *mut std::ffi::c_void, debugger_present: *mut i32) -> i32;
                fn GetCurrentProcess() -> *mut std::ffi::c_void;
            }
            unsafe {
                if IsDebuggerPresent() != 0 {
                    eprintln!("[Sovereign Guard] 🛑 Access violation: Active debugger detected. Process terminated.");
                    std::process::exit(1);
                }

                let mut is_remote: i32 = 0;
                let cur_proc = GetCurrentProcess();
                if CheckRemoteDebuggerPresent(cur_proc, &mut is_remote) != 0 && is_remote != 0 {
                    eprintln!("[Sovereign Guard] 🛑 Access violation: Remote debugger detected. Process terminated.");
                    std::process::exit(1);
                }
            }
        }
    }
}
