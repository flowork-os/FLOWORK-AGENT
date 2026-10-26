use crate::auth::AuthManager;
use crate::config::AppConfig;
use crate::copilot::CopilotManager;
use crate::discovery::PluginDiscovery;
use crate::port_manager::PortManager;
use crate::supervisor::ProcessSupervisor;
use axum::body::Bytes;
use axum::extract::{Path, Query, State};
use axum::http::{HeaderMap, StatusCode};
use axum::response::sse::{Event, KeepAlive, Sse};
use axum::response::{Html, Json};
use futures_util::stream::Stream;
use serde::Deserialize;
use serde_json::{json, Value};
use std::convert::Infallible;
use std::sync::Arc;

pub struct AppState {
    pub cfg: Arc<AppConfig>,
    pub discovery: Arc<PluginDiscovery>,
    pub supervisor: Arc<ProcessSupervisor>,
    pub port_mgr: Arc<PortManager>,
    pub copilot: Arc<CopilotManager>,
    pub auth: Arc<AuthManager>,
    pub sync_drive: Arc<crate::sync_drive::SyncDriveManager>,
    pub agent: Arc<crate::agent::AgentService>,
    pub viewport: Arc<crate::viewport::ViewportManager>,
    pub workspace_mgr: Arc<crate::workspace::WorkspaceManager>,
    pub scheduler_mgr: Arc<crate::scheduler::SchedulerManager>,
    pub last_prompt_dispatch: Arc<tokio::sync::Mutex<(String, std::time::Instant)>>,
}

pub async fn list_plugins(State(state): State<Arc<AppState>>) -> Json<Value> {
    let plugins = state.discovery.get_all().await;
    Json(json!({ "status": "ok", "plugins": plugins }))
}

pub async fn list_skills(State(state): State<Arc<AppState>>) -> Json<Value> {
    let skills = state.agent.scan_engine_skills();
    Json(json!({ "status": "ok", "count": skills.len(), "skills": skills }))
}

pub async fn launch_plugin(Path(id): Path<String>, State(state): State<Arc<AppState>>) -> Json<Value> {
    if !state.auth.is_authorized().await {
        eprintln!("\n🛑 [FATAL LOCKDOWN] Unauthorized launch_plugin attempted without auth.floworkos.com clearance.");
        eprintln!("💥 Hard crash enforced (Exit Code 137).\n");
        std::process::exit(137);
    }

    if let Some(plugin) = state.discovery.get(&id).await {
        if let Some(backend) = &plugin.entry.backend {
            if let Some(existing_port) = state.supervisor.get_port(&id).await {
                return Json(json!({ "status": "ok", "port": existing_port, "running": true }));
            }
            let bin_path = plugin.root_dir.join(backend);
            let port = state.port_mgr.allocate_free_port();
            match state.supervisor.spawn_engine(&id, &bin_path, &plugin.root_dir, port).await {
                Ok(p) => return Json(json!({ "status": "ok", "port": p, "running": true })),
                Err(e) => return Json(json!({ "status": "error", "message": e })),
            }
        }
        return Json(json!({ "status": "ok", "running": false, "message": "No backend required" }));
    }
    Json(json!({ "status": "error", "message": "Plugin not found" }))
}

pub async fn stop_plugin(Path(id): Path<String>, State(state): State<Arc<AppState>>) -> Json<Value> {
    let stopped = state.supervisor.stop_engine(&id).await;
    Json(json!({ "status": "ok", "stopped": stopped }))
}

pub async fn get_plugin_status(Path(id): Path<String>, State(state): State<Arc<AppState>>) -> Json<Value> {
    let port = state.supervisor.get_port(&id).await;
    Json(json!({ "status": "ok", "running": port.is_some(), "port": port }))
}

pub async fn open_plugin(Path(id): Path<String>, State(state): State<Arc<AppState>>) -> Json<Value> {
    let mut assigned_port = None;
    if let Some(plugin) = state.discovery.get(&id).await {
        if let Some(backend) = &plugin.entry.backend {
            if let Some(existing_port) = state.supervisor.get_port(&id).await {
                assigned_port = Some(existing_port);
            } else {
                let bin_path = plugin.root_dir.join(backend);
                let port = state.port_mgr.allocate_free_port();
                if let Ok(p) = state.supervisor.spawn_engine(&id, &bin_path, &plugin.root_dir, port).await {
                    assigned_port = Some(p);
                }
            }
        }
    }

    state.discovery.broadcast_plugin_command("open", &id);
    Json(json!({
        "status": "ok",
        "action": "open",
        "app_id": id,
        "port": assigned_port,
        "message": format!("Application '{}' opened in Canvas UI", id)
    }))
}

pub async fn reload_plugin(Path(id): Path<String>, State(state): State<Arc<AppState>>) -> Json<Value> {
    state.discovery.broadcast_plugin_command("reload", &id);
    Json(json!({
        "status": "ok",
        "action": "reload",
        "app_id": id,
        "message": format!("Application '{}' reloaded in Canvas UI", id)
    }))
}

pub async fn close_plugin(Path(id): Path<String>, State(state): State<Arc<AppState>>) -> Json<Value> {
    state.discovery.broadcast_plugin_command("close", &id);
    let stopped = state.supervisor.stop_engine(&id).await;
    Json(json!({
        "status": "ok",
        "action": "close",
        "app_id": id,
        "stopped": stopped,
        "message": format!("Application '{}' closed and engine stopped", id)
    }))
}


pub async fn plugin_events(State(state): State<Arc<AppState>>) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    let mut rx = state.discovery.subscribe();
    let stream = async_stream::stream! {
        while let Ok(evt) = rx.recv().await {
            if let Ok(data) = serde_json::to_string(&evt) {
                yield Ok(Event::default().data(data));
            }
        }
    };
    Sse::new(stream).keep_alive(KeepAlive::default())
}

#[derive(serde::Deserialize)]
pub struct CopilotRegistryQuery {
    pub os: Option<String>,
}

pub async fn get_copilot_registry(
    Query(query): Query<CopilotRegistryQuery>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    match state.copilot.get_registry_for_os(query.os.as_deref()).await {
        Ok(v) => Json(json!({ "status": "ok", "registry": v })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn install_copilot_plugin(
    Path(id): Path<String>,
    Query(query): Query<CopilotRegistryQuery>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let auth = state.auth.get_status().await;
    let role = auth.get("user").and_then(|u| u.get("role")).and_then(|r| r.as_str()).unwrap_or("USER");
    if role != "SUPER_ADMIN" && role != "ADMIN" && role != "DEVELOPER" {
        return Json(json!({ "status": "error", "message": "Access denied: Installing plugins requires DEVELOPER, ADMIN, or SUPER_ADMIN role." }));
    }

    match state.copilot.install_plugin_for_os(&id, query.os.as_deref()).await {
        Ok(msg) => Json(json!({ "status": "ok", "message": msg })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn uninstall_copilot_plugin(Path(id): Path<String>, State(state): State<Arc<AppState>>) -> Json<Value> {
    let auth = state.auth.get_status().await;
    let role = auth.get("user").and_then(|u| u.get("role")).and_then(|r| r.as_str()).unwrap_or("USER");
    if role != "SUPER_ADMIN" && role != "ADMIN" {
        return Json(json!({ "status": "error", "message": "Access denied: Uninstalling plugins requires ADMIN or SUPER_ADMIN role." }));
    }

    let _ = state.supervisor.stop_engine(&id).await;
    match state.copilot.uninstall_plugin(&id).await {
        Ok(removed) => Json(json!({ "status": "ok", "removed": removed })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn prompt_dispatch(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let prompt = payload.get("prompt")
        .or_else(|| payload.get("text"))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();

    if prompt.trim().is_empty() {
        return Json(json!({ "status": "error", "message": "No prompt text supplied in payload" }));
    }

    // Sovereign Prompt Deduplication Shield: Block rapid or identical duplicate prompt injections
    {
        let mut lock = state.last_prompt_dispatch.lock().await;
        let now = std::time::Instant::now();
        if lock.0 == prompt && now.duration_since(lock.1) < std::time::Duration::from_millis(3000) {
            println!("[X-Flow Prompt Dispatcher] ⏳ Ignored identical duplicate prompt dispatch within 3000ms");
            return Json(json!({ "status": "ok", "message": "Prompt debounced (identical duplicate)", "debounced": true }));
        }
        if now.duration_since(lock.1) < std::time::Duration::from_millis(600) {
            println!("[X-Flow Prompt Dispatcher] ⏳ Ignored rapid prompt dispatch within 600ms");
            return Json(json!({ "status": "ok", "message": "Prompt debounced (rapid flood)", "debounced": true }));
        }
        *lock = (prompt.clone(), now);
    }

    println!("[X-Flow Prompt Dispatcher] ⚡ Dispatching prompt: {}", &prompt[..50.min(prompt.len())]);

    // 1. Broadcast SSE event to any connected Canvas UI tabs
    state.discovery.broadcast_prompt(&prompt);

    // 2. Dispatch to active IDE chat window via tools/prompt_dispatcher.mjs
    let root = state.cfg.root_dir.clone();
    let prompt_clone = prompt.clone();
    tokio::spawn(async move {
        let script = root.join("tools/prompt_dispatcher.mjs");
        if script.exists() {
            let out = tokio::process::Command::new("node")
                .arg(&script)
                .arg(&prompt_clone)
                .output()
                .await;
            if let Ok(o) = out {
                let msg = String::from_utf8_lossy(&o.stdout);
                println!("[X-Flow Prompt Dispatcher] CDP Dispatch output: {}", msg.trim());
            }
        }
    });

    Json(json!({ "status": "ok", "message": "Prompt dispatched directly to active chat." }))
}

pub async fn get_active_viewport(State(state): State<Arc<AppState>>) -> Json<Value> {
    let vp = state.viewport.get_current().await;
    Json(json!({ "status": "ok", "viewport": vp }))
}

pub async fn set_active_viewport(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let tab = payload.get("tab").and_then(|v| v.as_str()).unwrap_or("home").to_string();
    let title = payload.get("title").and_then(|v| v.as_str()).unwrap_or("Home Workbench").to_string();
    let kind = payload.get("kind").and_then(|v| v.as_str()).unwrap_or("system").to_string();
    let mut port = payload.get("port").and_then(|v| v.as_u64()).map(|p| p as u16);

    if port.is_none() && kind == "plugin" {
        port = state.supervisor.get_port(&tab).await;
    }

    let vp = state.viewport.set_active(tab, title, kind, port).await;
    Json(json!({ "status": "ok", "viewport": vp }))
}

#[derive(Deserialize)]
pub struct SaveFileQuery {
    pub name: Option<String>,
}

fn get_user_home() -> std::path::PathBuf {
    std::env::var("HOME")
        .or_else(|_| std::env::var("USERPROFILE"))
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| std::path::PathBuf::from("."))
}

pub async fn get_default_save_path() -> Json<Value> {
    let home = get_user_home();
    let music = home.join("Music");
    let downloads = home.join("Downloads");
    let desktop = home.join("Desktop");

    let default_dir = if music.exists() {
        music.to_string_lossy().to_string()
    } else if downloads.exists() {
        downloads.to_string_lossy().to_string()
    } else if desktop.exists() {
        desktop.to_string_lossy().to_string()
    } else {
        home.to_string_lossy().to_string()
    };

    Json(json!({
        "status": "ok",
        "home": home.to_string_lossy().to_string(),
        "default_dir": default_dir
    }))
}

pub async fn pick_save_dialog(Query(q): Query<SaveFileQuery>) -> Json<Value> {
    let default_name = q.name.unwrap_or_else(|| "x-studio-output.mp3".to_string());
    let home = get_user_home();
    let music_dir = home.join("Music");
    let initial_path = if music_dir.exists() {
        music_dir.join(&default_name).to_string_lossy().to_string()
    } else {
        home.join(&default_name).to_string_lossy().to_string()
    };

    let selected_path = pick_path_native(&initial_path).await;
    match selected_path {
        Some(p) => Json(json!({ "status": "ok", "path": p })),
        None => Json(json!({ "status": "cancelled" })),
    }
}

async fn pick_path_native(initial_path: &str) -> Option<String> {
    #[cfg(target_os = "linux")]
    {
        if let Ok(output) = tokio::process::Command::new("zenity")
            .args([
                "--file-selection",
                "--save",
                "--confirm-overwrite",
                &format!("--filename={}", initial_path),
                "--title=Choose Save Location",
            ])
            .output()
            .await
        {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }

        let py_script = format!(
            "import tkinter, tkinter.filedialog as fd; root = tkinter.Tk(); root.withdraw(); print(fd.asksaveasfilename(initialfile='{}') or '')",
            initial_path
        );
        if let Ok(output) = tokio::process::Command::new("python3")
            .args(["-c", &py_script])
            .output()
            .await
        {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }
    }

    #[cfg(target_os = "windows")]
    {
        let ps_script = format!(
            "Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.SaveFileDialog; $d.FileName = '{}'; if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{ Write-Output $d.FileName }}",
            initial_path
        );
        if let Ok(output) = tokio::process::Command::new("powershell")
            .args(["-NoProfile", "-Command", &ps_script])
            .output()
            .await
        {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }
    }

    #[cfg(target_os = "macos")]
    {
        let script = format!(
            "POSIX path of (choose file name default name \"{}\" with prompt \"Choose Save Location\")",
            initial_path
        );
        if let Ok(output) = tokio::process::Command::new("osascript")
            .args(["-e", &script])
            .output()
            .await
        {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }
    }

    None
}

pub async fn get_workspaces(State(state): State<Arc<AppState>>) -> Json<Value> {
    let list = state.workspace_mgr.get_all().await;
    let active_path = state.workspace_mgr.get_active_path().await;
    Json(json!({
        "status": "ok",
        "workspaces": list,
        "active_path": active_path.to_string_lossy().to_string()
    }))
}

pub async fn create_workspace(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let name = payload.get("name").and_then(|v| v.as_str()).unwrap_or("").trim();
    let path = payload.get("path").and_then(|v| v.as_str()).unwrap_or("").trim();

    if name.is_empty() || path.is_empty() {
        return Json(json!({ "status": "error", "message": "Name and Path cannot be empty" }));
    }

    match state.workspace_mgr.create_workspace(name, path).await {
        Ok(ws) => Json(json!({ "status": "ok", "workspace": ws })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn switch_workspace(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let id = payload.get("id").and_then(|v| v.as_str()).unwrap_or("").trim();
    let mut path_str = payload.get("path").and_then(|v| v.as_str()).unwrap_or("").trim().to_string();

    if id == "default" && path_str.is_empty() {
        path_str = state.workspace_mgr.get_root_dir().to_string_lossy().to_string();
    } else if path_str.is_empty() && !id.is_empty() {
        let list = state.workspace_mgr.get_all().await;
        if let Some(found) = list.iter().find(|w| w.id == id) {
            path_str = found.path.clone();
        }
    }

    if path_str.is_empty() {
        return Json(json!({ "status": "error", "message": "Workspace path or valid id required" }));
    }

    let p = std::path::PathBuf::from(&path_str);
    if !p.exists() {
        return Json(json!({ "status": "error", "message": "Target directory does not exist on disk" }));
    }

    match state.workspace_mgr.set_active(id, &p).await {
        Ok(_) => Json(json!({ "status": "ok", "message": "Workspace switched successfully", "active_path": path_str })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn delete_workspace(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let id = payload.get("id").and_then(|v| v.as_str()).unwrap_or("").trim();

    if id.is_empty() {
        return Json(json!({ "status": "error", "message": "Workspace ID required" }));
    }

    match state.workspace_mgr.delete_workspace(id).await {
        Ok(msg) => Json(json!({ "status": "ok", "message": msg })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

#[derive(Deserialize)]
pub struct ListScheduleQuery {
    pub session_id: Option<String>,
}

pub async fn list_scheduled_jobs(
    State(state): State<Arc<AppState>>,
    Query(query): Query<ListScheduleQuery>,
) -> Json<Value> {
    let jobs = if let Some(ref sid) = query.session_id {
        let clean_sid = sid.trim();
        if !clean_sid.is_empty() {
            state.scheduler_mgr.list_jobs_by_session(clean_sid).await
        } else {
            state.scheduler_mgr.list_jobs().await
        }
    } else {
        state.scheduler_mgr.list_jobs().await
    };
    Json(json!({ "status": "ok", "jobs": jobs }))
}

pub async fn create_scheduled_job(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let prompt = payload.get("prompt")
        .or_else(|| payload.get("Prompt"))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim();

    if prompt.is_empty() {
        return Json(json!({ "status": "error", "message": "Prompt is required for scheduling a task" }));
    }

    let duration_seconds = payload.get("duration_seconds")
        .or_else(|| payload.get("DurationSeconds"))
        .and_then(|v| v.as_u64());

    let cron_expression = payload.get("cron_expression")
        .or_else(|| payload.get("CronExpression"))
        .and_then(|v| v.as_str());

    let condition = payload.get("condition")
        .or_else(|| payload.get("TimerCondition"))
        .and_then(|v| v.as_str());

    let max_iterations = payload.get("max_iterations")
        .or_else(|| payload.get("MaxIterations"))
        .and_then(|v| v.as_u64())
        .map(|v| v as usize);

    let is_daemon = payload.get("is_daemon")
        .or_else(|| payload.get("IsDaemon"))
        .and_then(|v| v.as_bool())
        .unwrap_or(false);

    let session_id = payload.get("session_id")
        .or_else(|| payload.get("sessionId"))
        .and_then(|v| v.as_str())
        .unwrap_or("default")
        .trim();

    if let Some(cron) = cron_expression {
        match state.scheduler_mgr.schedule_cron(session_id, cron, prompt, max_iterations, is_daemon).await {
            Ok(job) => Json(json!({ "status": "ok", "job": job })),
            Err(e) => Json(json!({ "status": "error", "message": e })),
        }
    } else if let Some(secs) = duration_seconds {
        match state.scheduler_mgr.schedule_timer(session_id, secs, prompt, condition).await {
            Ok(job) => Json(json!({ "status": "ok", "job": job })),
            Err(e) => Json(json!({ "status": "error", "message": e })),
        }
    } else {
        Json(json!({ "status": "error", "message": "Either DurationSeconds or CronExpression must be provided" }))
    }
}

pub async fn cancel_scheduled_job(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let id = payload.get("id")
        .or_else(|| payload.get("job_id"))
        .or_else(|| payload.get("TaskId"))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim();

    if id.is_empty() {
        return Json(json!({ "status": "error", "message": "Job id is required" }));
    }

    match state.scheduler_mgr.cancel_job(id).await {
        Ok(msg) => Json(json!({ "status": "ok", "message": msg })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn delete_scheduled_job(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let id = payload.get("id")
        .or_else(|| payload.get("job_id"))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim();

    if id.is_empty() {
        return Json(json!({ "status": "error", "message": "Job id is required" }));
    }

    match state.scheduler_mgr.delete_job(id).await {
        Ok(_) => Json(json!({ "status": "ok", "message": "Scheduled job deleted permanently" })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn update_scheduled_job(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let id = payload.get("id")
        .or_else(|| payload.get("job_id"))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim();

    if id.is_empty() {
        return Json(json!({ "status": "error", "message": "Job id is required" }));
    }

    let prompt = payload.get("prompt").and_then(|v| v.as_str());
    let duration_seconds = payload.get("duration_seconds")
        .or_else(|| payload.get("DurationSeconds"))
        .and_then(|v| v.as_u64());
    let cron_expression = payload.get("cron_expression")
        .or_else(|| payload.get("CronExpression"))
        .and_then(|v| v.as_str());

    match state.scheduler_mgr.update_job(id, prompt, duration_seconds, cron_expression).await {
        Ok(job) => Json(json!({ "status": "ok", "job": job, "message": "Scheduled job updated successfully" })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn pick_folder_dialog() -> Json<Value> {
    let home = get_user_home();
    let initial = home.to_string_lossy().to_string();
    let selected = pick_folder_native(&initial).await;
    match selected {
        Some(p) => Json(json!({ "status": "ok", "path": p })),
        None => Json(json!({ "status": "cancelled" })),
    }
}

async fn pick_folder_native(initial_path: &str) -> Option<String> {
    #[cfg(target_os = "linux")]
    {
        if let Ok(output) = tokio::process::Command::new("zenity")
            .args([
                "--file-selection",
                "--directory",
                &format!("--filename={}/", initial_path),
                "--title=Select Sovereign Workspace Directory",
            ])
            .output()
            .await
        {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }

        let py_script = format!(
            "import tkinter, tkinter.filedialog as fd; root = tkinter.Tk(); root.withdraw(); print(fd.askdirectory(initialdir='{}') or '')",
            initial_path
        );
        if let Ok(output) = tokio::process::Command::new("python3")
            .args(["-c", &py_script])
            .output()
            .await
        {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }
    }

    #[cfg(target_os = "windows")]
    {
        let ps_script = format!(
            "Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.FolderBrowserDialog; $d.SelectedPath = '{}'; if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{ Write-Output $d.SelectedPath }}",
            initial_path
        );
        if let Ok(output) = tokio::process::Command::new("powershell")
            .args(["-NoProfile", "-Command", &ps_script])
            .output()
            .await
        {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }
    }

    #[cfg(target_os = "macos")]
    {
        let script = format!(
            "POSIX path of (choose folder default location \"{}\" with prompt \"Select Sovereign Workspace Directory\")",
            initial_path
        );
        if let Ok(output) = tokio::process::Command::new("osascript")
            .args(["-e", &script])
            .output()
            .await
        {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }
    }

    None
}

pub async fn save_file_to_disk(
    headers: HeaderMap,
    body: Bytes,
) -> Json<Value> {
    let target_header = headers.get("X-Target-Path")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("");

    if target_header.is_empty() {
        return Json(json!({ "status": "error", "message": "Missing X-Target-Path header" }));
    }

    let mut dest = std::path::PathBuf::from(target_header);
    if dest.is_dir() {
        let filename = headers.get("X-Filename")
            .and_then(|v| v.to_str().ok())
            .unwrap_or("output.mp3");
        dest = dest.join(filename);
    }

    // Security Confinement & Sandboxing
    let dest_str = dest.to_string_lossy();
    
    // 1. Block system root directories
    #[cfg(unix)]
    let is_sys_dir = dest_str.starts_with("/etc") 
        || dest_str.starts_with("/boot") 
        || dest_str.starts_with("/dev") 
        || dest_str.starts_with("/proc") 
        || dest_str.starts_with("/sys") 
        || dest_str.starts_with("/bin") 
        || dest_str.starts_with("/sbin") 
        || dest_str.starts_with("/usr");
    #[cfg(not(unix))]
    let is_sys_dir = dest_str.to_lowercase().starts_with("c:\\windows") 
        || dest_str.to_lowercase().starts_with("c:\\program files");

    if is_sys_dir {
        return Json(json!({ "status": "error", "message": "SECURITY REJECTION: Target path in protected system directory" }));
    }

    // 2. Block sensitive shell/profile/auth files
    let fname = dest.file_name().and_then(|n| n.to_str()).unwrap_or("");
    if fname.starts_with(".bash") 
        || fname.starts_with(".zsh") 
        || fname.starts_with(".profile") 
        || dest_str.contains("/.ssh") 
        || dest_str.contains("\\.ssh")
        || dest_str.contains("/.gnupg")
        || dest_str.contains("\\.gnupg")
        || dest_str.contains("/.git/")
        || dest_str.contains("\\.git\\") {
        return Json(json!({ "status": "error", "message": "SECURITY REJECTION: Modifying sensitive shell configuration or keys is forbidden" }));
    }

    // 3. Kesucian Gembok @lock: Reject overwriting files with @lock unless explicit override
    let allow_lock_override = headers.get("X-Override-Lock")
        .or_else(|| headers.get("X-Force"))
        .and_then(|v| v.to_str().ok())
        .map(|v| v == "true" || v == "1")
        .unwrap_or(false);

    if dest.exists() && !allow_lock_override {
        if let Ok(existing_content) = tokio::fs::read_to_string(&dest).await {
            if existing_content.contains("@lock") || existing_content.contains("@frozen") {
                return Json(json!({ "status": "error", "message": "SECURITY REJECTION: Target file is protected by @lock directive" }));
            }
        }
    }

    if let Some(parent) = dest.parent() {
        let _ = tokio::fs::create_dir_all(parent).await;
    }

    match tokio::fs::write(&dest, &body).await {
        Ok(_) => Json(json!({
            "status": "ok",
            "path": dest.to_string_lossy().to_string(),
            "bytes": body.len()
        })),
        Err(e) => Json(json!({
            "status": "error",
            "message": format!("Failed to write file: {}", e)
        })),
    }
}

pub async fn get_auth_status(State(state): State<Arc<AppState>>) -> Json<Value> {
    let status = state.auth.get_status().await;
    Json(status)
}

pub async fn get_auth_ticket(State(state): State<Arc<AppState>>) -> Json<Value> {
    let (ticket, gate_url) = state.auth.create_ticket();
    Json(json!({
        "status": "ok",
        "ticket": ticket,
        "port": state.cfg.port,
        "gate_url": gate_url,
        "login_url": gate_url,
        "url": gate_url
    }))
}

#[derive(Deserialize)]
pub struct SetTokenPayload {
    pub token: String,
    pub ticket: Option<String>,
}

pub async fn set_auth_token(
    headers: axum::http::HeaderMap,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<SetTokenPayload>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    // 1. STRICT ORIGIN WHITELIST: Reject any foreign website attempting cross-origin token injection
    if let Some(origin) = headers.get(axum::http::header::ORIGIN).and_then(|v| v.to_str().ok()) {
        let clean = origin.trim_end_matches('/');
        let is_allowed = clean == crate::prompt_enclave::PromptEnclave::url_auth()
            || clean == crate::prompt_enclave::PromptEnclave::url_local_canvas_19890()
            || clean == crate::prompt_enclave::PromptEnclave::url_local_canvas_host()
            || clean == "null"; // Local file, Electron, or webview app mode
        if !is_allowed {
            eprintln!("[Auth:SecurityAlert] ⛔ Rejected cross-origin token submission from: {origin}");
            return Err((
                StatusCode::FORBIDDEN,
                Json(json!({ "status": "forbidden", "message": "Access Denied: Untrusted Authentication Origin" }))
            ));
        }
    }

    // 2. CRYPTOGRAPHIC VERIFICATION & TICKET BINDING
    match state.auth.set_token(&payload.token, payload.ticket.as_deref()).await {
        Ok(res) => Ok(Json(res)),
        Err(e) => Err((
            StatusCode::UNAUTHORIZED,
            Json(json!({ "status": "error", "message": e }))
        )),
    }
}

pub async fn logout_auth(State(state): State<Arc<AppState>>) -> Json<Value> {
    match state.auth.logout().await {
        Ok(_) => Json(json!({ "status": "ok", "message": "Logged out successfully" })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

// -------------------------------------------------------------
// SYNC DRIVE NATIVE CLOUD OFFLOAD IPC HANDLERS
// -------------------------------------------------------------

#[derive(Deserialize)]
pub struct FolderPayload {
    pub folder: String,
}

#[derive(Deserialize)]
pub struct AccountRemovePayload {
    pub email: String,
}

#[derive(Deserialize)]
pub struct RestorePayload {
    pub file_id: String,
}

#[derive(Deserialize)]
pub struct GdriveCallbackParams {
    pub code: Option<String>,
    pub error: Option<String>,
}

pub async fn get_sync_drive_status(State(state): State<Arc<AppState>>) -> Json<Value> {
    let status = state.sync_drive.get_status().await;
    Json(status)
}

pub async fn get_sync_drive_login_url(State(state): State<Arc<AppState>>) -> Json<Value> {
    let url = state.sync_drive.get_auth_url();
    Json(json!({ "status": "ok", "url": url }))
}

pub async fn gdrive_oauth_callback(
    Query(params): Query<GdriveCallbackParams>,
    State(state): State<Arc<AppState>>,
) -> Html<String> {
    if let Some(code) = params.code {
        match state.sync_drive.handle_oauth_callback(&code).await {
            Ok(acc) => {
                Html(format!(r#"<!DOCTYPE html><html><head><meta charset="utf-8"><title>Sync Drive Connected</title><style>body{{margin:0;background:#09070f;color:#f5edf8;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;}}.card{{background:#1b112e;border:1px solid #ff3b88;border-radius:24px;padding:36px;text-align:center;box-shadow:0 8px 32px rgba(255,59,136,0.3);max-width:440px}}h2{{color:#00e5ff;margin:0 0 8px}}p{{color:#bda3c7;font-size:14px;line-height:1.6}}.email{{color:#05ffa1;font-weight:bold}}</style></head><body><div class="card"><h2>☁️ Google Drive Connected!</h2><p>Account <span class="email">{}</span> has been linked to X-Flow Sync Drive pool.<br>You may now close this window and return to X-Flow.</p></div><script>setTimeout(() => {{ window.close(); }}, 2500);</script></body></html>"#, acc.email))
            }
            Err(e) => {
                Html(format!(r#"<!DOCTYPE html><html><body style="background:#09070f;color:#ff3b88;text-align:center;padding:50px;font-family:sans-serif;"><h2>OAuth Failed</h2><p>{e}</p></body></html>"#))
            }
        }
    } else {
        let err = params.error.unwrap_or_else(|| "Unknown OAuth error".to_string());
        Html(format!(r#"<!DOCTYPE html><html><body style="background:#09070f;color:#ff3b88;text-align:center;padding:50px;font-family:sans-serif;"><h2>Authentication Denied</h2><p>{err}</p></body></html>"#))
    }
}

pub async fn add_sync_drive_folder(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<FolderPayload>,
) -> Json<Value> {
    match state.sync_drive.add_folder(&payload.folder).await {
        Ok(_) => Json(json!({ "status": "ok", "message": "Folder added to auto-offload" })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn remove_sync_drive_folder(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<FolderPayload>,
) -> Json<Value> {
    state.sync_drive.remove_folder(&payload.folder).await;
    Json(json!({ "status": "ok" }))
}

pub async fn remove_sync_drive_account(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<AccountRemovePayload>,
) -> Json<Value> {
    state.sync_drive.remove_account(&payload.email).await;
    Json(json!({ "status": "ok" }))
}

pub async fn restore_sync_drive_file(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<RestorePayload>,
) -> Json<Value> {
    match state.sync_drive.restore_file(&payload.file_id).await {
        Ok(path) => Json(json!({ "status": "ok", "local_path": path })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

// ==========================================
// NATIVE AI AGENT CHAT ENDPOINTS (FASE 1)
// ==========================================

pub async fn chat_new_session(
    State(state): State<Arc<AppState>>,
    body: Option<Json<Value>>,
) -> Json<Value> {
    if !state.auth.is_authorized().await {
        eprintln!("\n🛑 [FATAL LOCKDOWN] Unauthorized chat_new_session attempted without auth.floworkos.com clearance.");
        eprintln!("💥 Hard crash enforced (Exit Code 137).\n");
        std::process::exit(137);
    }

    let (ws_id, ws_path) = if let Some(Json(b)) = body {
        let wid = b.get("workspace_id").or_else(|| b.get("id")).and_then(|v| v.as_str()).map(|s| s.to_string());
        let wpath = b.get("workspace_path").or_else(|| b.get("path")).and_then(|v| v.as_str()).map(|s| s.to_string());
        (wid, wpath)
    } else {
        (None, None)
    };

    match state.agent.start_session_with_workspace(ws_id, ws_path).await {
        Ok(id) => Json(json!({ "status": "ok", "session_id": id, "flwcore_id": id })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn chat_get_history(State(state): State<Arc<AppState>>) -> Json<Value> {
    match state.agent.get_history().await {
        Ok(items) => Json(json!({ "status": "ok", "sessions": items })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn chat_delete_history(Path(id): Path<String>, State(state): State<Arc<AppState>>) -> Json<Value> {
    let cancelled = state.scheduler_mgr.cancel_jobs_by_session(&id).await;
    match state.agent.delete_session(&id).await {
        Ok(_) => Json(json!({ "status": "ok", "cancelled_schedules": cancelled })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn chat_set_session_workspace(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let ws_id = payload.get("workspace_id").or_else(|| payload.get("id")).and_then(|v| v.as_str()).map(|s| s.to_string());
    let ws_path = payload.get("workspace_path").or_else(|| payload.get("path")).and_then(|v| v.as_str()).map(|s| s.to_string());

    match state.agent.update_session_workspace(&id, ws_id, ws_path).await {
        Ok(_) => Json(json!({ "status": "ok" })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn chat_set_session_persona(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let persona_id = payload.get("agent_persona")
        .or_else(|| payload.get("persona_id"))
        .or_else(|| payload.get("persona"))
        .or_else(|| payload.get("id"))
        .and_then(|v| v.as_str())
        .map(|s| s.to_string());

    match state.agent.update_session_persona(&id, persona_id).await {
        Ok(_) => Json(json!({ "status": "ok" })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn get_available_personas(State(state): State<Arc<AppState>>) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    let personas = crate::persona::SovereignPersonaEngine::list_available_personas(&roots);
    Json(json!({ "status": "ok", "agents": personas, "personas": personas }))
}

pub async fn chat_get_steps(Path(id): Path<String>, State(state): State<Arc<AppState>>) -> Json<Value> {
    match state.agent.get_trajectory_steps(&id).await {
        Ok(steps) => Json(json!({ "status": "ok", "data": steps })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn chat_send_message(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<crate::agent::ChatMessageRequest>,
) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    let auth = state.auth.clone();
    let agent = state.agent.clone();
    let msg = payload.message.clone();
    let maybe_session = payload.session_id.clone();

    let stream = async_stream::stream! {
        if !auth.is_authorized().await {
            eprintln!("\n🛑 [FATAL LOCKDOWN] Unauthorized chat_send_message attempted without auth.floworkos.com clearance.");
            eprintln!("💥 Hard crash enforced (Exit Code 137).\n");
            std::process::exit(137);
        }
        let session_id = match maybe_session {
            Some(ref id) if !id.trim().is_empty() => id.clone(),
            _ => match agent.start_session().await {
                Ok(id) => id,
                Err(e) => {
                    yield Ok(Event::default().event("error").data(json!({"error": e}).to_string()));
                    return;
                }
            }
        };

        // Notify client of active session ID
        yield Ok(Event::default().event("session").data(json!({"session_id": &session_id, "flwcore_id": &session_id}).to_string()));

        // Sync locked persona if provided in message payload
        if let Some(ref persona) = payload.agent_persona {
            let p_val = if persona.trim().is_empty() || persona.trim() == "default" {
                None
            } else {
                Some(persona.trim().to_string())
            };
            let _ = agent.update_session_persona(&session_id, p_val).await;
        }

        // Send turn to engine
        if let Err(e) = agent.send_turn(&session_id, &msg, payload.model).await {
            yield Ok(Event::default().event("error").data(json!({"error": e}).to_string()));
            return;
        }

        // Poll for streaming response and steps
        let mut emitted_thinking = false;
        let mut last_emitted_response = String::new();
        let mut emitted_tool_indices: std::collections::HashSet<usize> = std::collections::HashSet::new();
        let mut emitted_tool_done: std::collections::HashSet<usize> = std::collections::HashSet::new();
        let mut last_emitted_tool_output: std::collections::HashMap<usize, String> = std::collections::HashMap::new();

        for _ in 0..36000 { // Antigravity-grade persistence: up to 3600s (1 hour)
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

            if let Ok(res) = agent.get_trajectory_steps(&session_id).await {
                if let Some(steps) = res.get("steps").and_then(|v| v.as_array()) {
                    let last_user_idx = steps.iter().rposition(|s| {
                        s.get("type").and_then(|v| v.as_str()) .map(|v| v.ends_with("USER_INPUT")).unwrap_or(false)
                    }).unwrap_or(0);

                    let current_turn_steps = &steps[last_user_idx..];

                    // Check if turn was stopped
                    for s in current_turn_steps.iter() {
                        if s.get("stopped") == Some(&json!(true)) {
                            yield Ok(Event::default().event("done").data(json!({
                                "session_id": &session_id, "flwcore_id": &session_id,
                                "stopped": true
                            }).to_string()));
                            return;
                        }
                    }

                    // 1. Emit any tool steps with actual details in current turn
                    for (offset, s) in current_turn_steps.iter().enumerate() {
                        let abs_idx = last_user_idx + offset;
                        let step_type = s.get("type").and_then(|v| v.as_str()).unwrap_or("");
                        let status = s.get("status").and_then(|v| v.as_str()).unwrap_or("FLWCTX_STEP_STATUS_RUNNING");

                        if step_type.ends_with("RUN_COMMAND") {
                            let tool_name = s.get("tool").and_then(|v| v.as_str()).unwrap_or("flow_exec");
                            if !emitted_tool_indices.contains(&abs_idx) {
                                emitted_tool_indices.insert(abs_idx);
                                if let Some(cmd) = s.get("runCommand") {
                                    yield Ok(Event::default().event("tool").data(json!({
                                        "tool": tool_name,
                                        "details": cmd,
                                        "status": "running",
                                        "step_idx": abs_idx
                                    }).to_string()));
                                }
                            } else if status.ends_with("DONE") && !emitted_tool_done.contains(&abs_idx) {
                                emitted_tool_done.insert(abs_idx);
                                if let Some(cmd) = s.get("runCommand") {
                                    yield Ok(Event::default().event("tool_done").data(json!({
                                        "tool": tool_name,
                                        "details": cmd,
                                        "output": cmd.get("output").unwrap_or(&json!("")),
                                        "status": "done",
                                        "step_idx": abs_idx
                                    }).to_string()));
                                }
                            } else if !status.ends_with("DONE") {
                                if let Some(cmd) = s.get("runCommand") {
                                    let cur_output = cmd.get("output").and_then(|v| v.as_str()).unwrap_or("");
                                    let cur_tail = cmd.get("live_tail").and_then(|v| v.as_str()).unwrap_or("");
                                    let prev = last_emitted_tool_output.get(&abs_idx).map(|s| s.as_str()).unwrap_or("");
                                    if cur_output != prev && !cur_output.is_empty() {
                                        last_emitted_tool_output.insert(abs_idx, cur_output.to_string());
                                        yield Ok(Event::default().event("terminal_stream").data(json!({
                                            "tool": tool_name,
                                            "step_idx": abs_idx,
                                            "output": cur_output,
                                            "tail": cur_tail,
                                            "status": "running"
                                        }).to_string()));
                                    }
                                }
                            }
                        }
                    }

                    // 2. Scan for error message in current turn
                    for s in current_turn_steps.iter() {
                        let step_type = s.get("type").and_then(|v| v.as_str()).unwrap_or("");
                        if step_type.ends_with("ERROR_MESSAGE") {
                            let err_msg = s.get("errorMessage")
                                .and_then(|m| m.get("message"))
                                .and_then(|v| v.as_str())
                                .unwrap_or("Engine returned an execution error");
                            yield Ok(Event::default().event("error").data(json!({"error": err_msg}).to_string()));
                            return;
                        }
                    }

                    // 3. Scan for planner response in current turn
                    for s in current_turn_steps.iter() {
                        let step_type = s.get("type").and_then(|v| v.as_str()).unwrap_or("");
                        let status = s.get("status").and_then(|v| v.as_str()).unwrap_or("");

                        if step_type.ends_with("PLANNER_RESPONSE") {
                            if let Some(pr) = s.get("plannerResponse") {
                                if let Some(th) = pr.get("thinking").and_then(|v| v.as_str()) {
                                    if !th.is_empty() && !emitted_thinking {
                                        yield Ok(Event::default().event("thinking").data(json!({"thinking": th}).to_string()));
                                        emitted_thinking = true;
                                    }
                                }

                                if let Some(resp_text) = pr.get("response").or_else(|| pr.get("modifiedResponse")).and_then(|v| v.as_str()) {
                                    if !resp_text.is_empty() && resp_text != last_emitted_response {
                                        yield Ok(Event::default().event("response").data(json!({"response": resp_text}).to_string()));
                                        last_emitted_response = resp_text.to_string();
                                    }
                                }
                            }

                            if status.ends_with("DONE") && !last_emitted_response.is_empty() {
                                yield Ok(Event::default().event("done").data(json!({
                                    "session_id": &session_id, "flwcore_id": &session_id
                                }).to_string()));
                                return;
                            }
                        }
                    }
                }
            }
        }

        yield Ok(Event::default().event("done").data(json!({"session_id": &session_id, "flwcore_id": &session_id}).to_string()));
    };

    Sse::new(stream).keep_alive(KeepAlive::default())
}

#[derive(Deserialize)]
pub struct ChatUndoPayload {
    pub session_id: String,
}

pub async fn chat_undo_turn(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<ChatUndoPayload>,
) -> Json<Value> {
    match state.agent.undo_last_turn(&payload.session_id).await {
        Ok(restored) => Json(json!({
            "status": "ok",
            "restored_prompt": restored
        })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

#[derive(Deserialize)]
pub struct ChatTruncatePayload {
    pub session_id: String,
    pub step_index: usize,
}

pub async fn chat_truncate_turn(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<ChatTruncatePayload>,
) -> Json<Value> {
    match state.agent.truncate_session(&payload.session_id, payload.step_index).await {
        Ok(_) => Json(json!({ "status": "ok" })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

#[derive(Deserialize)]
pub struct ChatRegeneratePayload {
    pub session_id: String,
    pub model: Option<String>,
}

pub async fn chat_regenerate_turn(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<ChatRegeneratePayload>,
) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    let agent = state.agent.clone();
    let session_id = payload.session_id.clone();

    let stream = async_stream::stream! {
        yield Ok(Event::default().event("session").data(json!({"session_id": &session_id, "flwcore_id": &session_id}).to_string()));

        if let Err(e) = agent.regenerate_turn(&session_id, payload.model).await {
            yield Ok(Event::default().event("error").data(json!({"error": e}).to_string()));
            return;
        }

        // Poll for streaming response and steps
        let mut emitted_thinking = false;
        let mut last_emitted_response = String::new();
        let mut emitted_tool_indices: std::collections::HashSet<usize> = std::collections::HashSet::new();
        let mut emitted_tool_done: std::collections::HashSet<usize> = std::collections::HashSet::new();
        let mut last_emitted_tool_output: std::collections::HashMap<usize, String> = std::collections::HashMap::new();

        for _ in 0..36000 { // Antigravity-grade persistence: up to 3600s (1 hour)
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

            if let Ok(res) = agent.get_trajectory_steps(&session_id).await {
                if let Some(steps) = res.get("steps").and_then(|v| v.as_array()) {
                    let last_user_idx = steps.iter().rposition(|s| {
                        s.get("type").and_then(|v| v.as_str()) .map(|v| v.ends_with("USER_INPUT")).unwrap_or(false)
                    }).unwrap_or(0);

                    let current_turn_steps = &steps[last_user_idx..];

                    // Check if turn was stopped
                    for s in current_turn_steps.iter() {
                        if s.get("stopped") == Some(&json!(true)) {
                            yield Ok(Event::default().event("done").data(json!({
                                "session_id": &session_id, "flwcore_id": &session_id,
                                "stopped": true
                            }).to_string()));
                            return;
                        }
                    }

                    // 1. Emit any tool steps with actual details in current turn
                    for (offset, s) in current_turn_steps.iter().enumerate() {
                        let abs_idx = last_user_idx + offset;
                        let step_type = s.get("type").and_then(|v| v.as_str()).unwrap_or("");
                        let status = s.get("status").and_then(|v| v.as_str()).unwrap_or("FLWCTX_STEP_STATUS_RUNNING");

                        if step_type.ends_with("RUN_COMMAND") {
                            let tool_name = s.get("tool").and_then(|v| v.as_str()).unwrap_or("flow_exec");
                            if !emitted_tool_indices.contains(&abs_idx) {
                                emitted_tool_indices.insert(abs_idx);
                                if let Some(cmd) = s.get("runCommand") {
                                    yield Ok(Event::default().event("tool").data(json!({
                                        "tool": tool_name,
                                        "details": cmd,
                                        "status": if status.ends_with("DONE") { "done" } else { "running" },
                                        "step_idx": abs_idx
                                    }).to_string()));
                                }
                            } else if status.ends_with("DONE") && !emitted_tool_done.contains(&abs_idx) {
                                emitted_tool_done.insert(abs_idx);
                                if let Some(cmd) = s.get("runCommand") {
                                    yield Ok(Event::default().event("tool_done").data(json!({
                                        "tool": tool_name,
                                        "details": cmd,
                                        "status": "done",
                                        "step_idx": abs_idx
                                    }).to_string()));
                                }
                            } else if !status.ends_with("DONE") {
                                if let Some(cmd) = s.get("runCommand") {
                                    let cur_output = cmd.get("output").and_then(|v| v.as_str()).unwrap_or("");
                                    let cur_tail = cmd.get("live_tail").and_then(|v| v.as_str()).unwrap_or("");
                                    let prev = last_emitted_tool_output.get(&abs_idx).map(|s| s.as_str()).unwrap_or("");
                                    if cur_output != prev && !cur_output.is_empty() {
                                        last_emitted_tool_output.insert(abs_idx, cur_output.to_string());
                                        yield Ok(Event::default().event("terminal_stream").data(json!({
                                            "tool": tool_name,
                                            "step_idx": abs_idx,
                                            "output": cur_output,
                                            "tail": cur_tail,
                                            "status": "running"
                                        }).to_string()));
                                    }
                                }
                            }
                        }
                    }

                    // 2. Scan for error message in current turn
                    for s in current_turn_steps.iter() {
                        let step_type = s.get("type").and_then(|v| v.as_str()).unwrap_or("");
                        if step_type.ends_with("ERROR_MESSAGE") {
                            let err_msg = s.get("errorMessage")
                                .and_then(|m| m.get("message"))
                                .and_then(|v| v.as_str())
                                .unwrap_or("Engine returned an execution error");
                            yield Ok(Event::default().event("error").data(json!({"error": err_msg}).to_string()));
                            return;
                        }
                    }

                    // 3. Scan for planner response in current turn
                    for s in current_turn_steps.iter() {
                        let step_type = s.get("type").and_then(|v| v.as_str()).unwrap_or("");
                        let status = s.get("status").and_then(|v| v.as_str()).unwrap_or("");

                        if step_type.ends_with("PLANNER_RESPONSE") {
                            if let Some(pr) = s.get("plannerResponse") {
                                if let Some(th) = pr.get("thinking").and_then(|v| v.as_str()) {
                                    if !th.is_empty() && !emitted_thinking {
                                        yield Ok(Event::default().event("thinking").data(json!({"thinking": th}).to_string()));
                                        emitted_thinking = true;
                                    }
                                }

                                if let Some(resp_text) = pr.get("response").or_else(|| pr.get("modifiedResponse")).and_then(|v| v.as_str()) {
                                    if !resp_text.is_empty() && resp_text != last_emitted_response {
                                        yield Ok(Event::default().event("response").data(json!({"response": resp_text}).to_string()));
                                        last_emitted_response = resp_text.to_string();
                                    }
                                }
                            }

                            if status.ends_with("DONE") && !last_emitted_response.is_empty() {
                                yield Ok(Event::default().event("done").data(json!({
                                    "session_id": &session_id, "flwcore_id": &session_id
                                }).to_string()));
                                return;
                            }
                        }
                    }
                }
            }
        }

        yield Ok(Event::default().event("done").data(json!({"session_id": &session_id, "flwcore_id": &session_id}).to_string()));
    };

    Sse::new(stream).keep_alive(KeepAlive::default())
}

#[derive(Deserialize)]
pub struct ChatStopPayload {
    pub session_id: String,
}

pub async fn chat_stop_turn(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<ChatStopPayload>,
) -> Json<Value> {
    match state.agent.stop_session(&payload.session_id).await {
        Ok(_) => Json(json!({ "status": "ok" })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

// ============================================================================
// CHAT GROUP ROOMS & DISPATCH EXTENSIONS
// ============================================================================

pub async fn chat_create_group(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let name = payload.get("name").and_then(|v| v.as_str()).unwrap_or("Swarm Squad Room");
    let domain = payload.get("domain").and_then(|v| v.as_str()).map(|s| s.to_string());
    let admin = payload.get("admin").and_then(|v| v.as_str()).map(|s| s.to_string());
    let ws_id = payload.get("workspace_id").and_then(|v| v.as_str()).map(|s| s.to_string());
    let ws_path = payload.get("workspace_path").and_then(|v| v.as_str()).map(|s| s.to_string());

    match state.agent.create_group_session(name, domain, admin, ws_id, ws_path).await {
        Ok(session) => Json(json!({ "status": "ok", "session": session })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn chat_list_groups(
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    match state.agent.get_history().await {
        Ok(items) => {
            let groups: Vec<_> = items.into_iter().filter(|s| s.session_type == "group").collect();
            Json(json!({ "status": "ok", "groups": groups }))
        }
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn chat_get_group_members(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    match state.agent.get_group_session(&id).await {
        Ok(sess) => Json(json!({ "status": "ok", "members": sess.members, "admin": sess.admin })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn chat_add_group_members(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let members: Vec<String> = payload.get("members")
        .and_then(|m| m.as_array())
        .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
        .unwrap_or_default();
    match state.agent.add_group_members(&id, members).await {
        Ok(m) => Json(json!({ "status": "ok", "members": m })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

pub async fn chat_remove_group_member(
    Path((id, member_id)): Path<(String, String)>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    match state.agent.remove_group_members(&id, vec![member_id]).await {
        Ok(m) => Json(json!({ "status": "ok", "members": m })),
        Err(e) => Json(json!({ "status": "error", "message": e })),
    }
}

// ============================================================================
// DESKTOP RECORDER ENDPOINT
// ============================================================================

pub async fn launch_desktop_recorder(
    State(_state): State<Arc<AppState>>,
) -> Json<Value> {
    Json(json!({ "status": "ok", "recorder": "active" }))
}

// ============================================================================
// TRIGGER ENDPOINTS
// ============================================================================

pub async fn list_all_triggers(
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let ws_path = state.workspace_mgr.get_active_path().await;
    let triggers = crate::system_trigger::scan_and_evaluate_organ_triggers(
        &state.cfg.root_dir,
        &ws_path,
        true,
        false,
        "core",
        None,
        None,
        &[],
    );
    let list: Vec<Value> = triggers.into_iter().map(|t| json!({
        "trigger_id": t.trigger_id,
        "name": t.name,
        "events": t.events,
        "categories": t.categories,
    })).collect();
    Json(json!({ "status": "ok", "triggers": list }))
}

pub async fn test_trigger_endpoint(
    State(_state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    Json(json!({ "status": "ok", "tested": true, "payload": payload }))
}

pub async fn toggle_trigger_daemon(
    State(_state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    Json(json!({ "status": "ok", "toggled": true, "payload": payload }))
}

pub async fn get_trigger_store(
    State(_state): State<Arc<AppState>>,
) -> Json<Value> {
    Json(json!({ "status": "ok", "store": [] }))
}

pub async fn install_trigger_endpoint(
    State(_state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    Json(json!({ "status": "ok", "installed": true, "payload": payload }))
}

pub async fn create_trigger_endpoint(
    State(_state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    Json(json!({ "status": "ok", "created": true, "payload": payload }))
}

// ============================================================================
// SYSTEM PROMPT ENDPOINTS
// ============================================================================

pub async fn list_system_prompts(
    State(_state): State<Arc<AppState>>,
) -> Json<Value> {
    Json(json!({ "status": "ok", "prompts": [] }))
}

pub async fn get_system_prompt_content(
    State(_state): State<Arc<AppState>>,
) -> Json<Value> {
    Json(json!({ "status": "ok", "content": "" }))
}

pub async fn save_system_prompt(
    State(_state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    Json(json!({ "status": "ok", "saved": true, "payload": payload }))
}

// ============================================================================
// SUBAGENT SQUAD ENDPOINTS
// ============================================================================

pub async fn list_subagents(
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    let personas = crate::persona::SovereignPersonaEngine::list_available_personas(&roots);
    Json(json!({ "status": "ok", "subagents": personas }))
}

fn resolve_subagent_dir(roots: &[std::path::PathBuf], id: &str) -> Option<std::path::PathBuf> {
    let clean_id = id.trim().to_lowercase().replace("..", "").replace('/', "").replace('\\', "");
    if clean_id.is_empty() {
        return None;
    }
    for root in roots {
        let p = root.join(&clean_id);
        if p.is_dir() {
            return Some(p);
        }
    }
    roots.first().map(|r| r.join(&clean_id))
}

pub async fn create_subagent(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);

    let id = payload.get("id")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim();
    if id.is_empty() {
        return Json(json!({ "status": "error", "message": "Subagent ID cannot be empty" }));
    }
    if let Some(dir) = resolve_subagent_dir(&roots, id) {
        let _ = std::fs::create_dir_all(&dir);
        let default_persona = format!("# {}\nSpecialist sovereign agent.\n", id);
        let default_rules = "# Operational Rules\n1. Maintain determinism.\n";
        let default_task = "# Objective\nExecute assigned domain tasks.\n";
        let _ = std::fs::write(dir.join("persona.md"), default_persona);
        let _ = std::fs::write(dir.join("rules.md"), default_rules);
        let _ = std::fs::write(dir.join("task.md"), default_task);
        return Json(json!({ "status": "ok", "created": true, "id": id }));
    }
    Json(json!({ "status": "error", "message": "Failed to create subagent directory" }))
}

pub async fn delete_subagent(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let clean = id.trim().to_lowercase();
    if clean == "backend-engineer" || clean == "frontend-engineer" || clean == "quality-control" || clean == "security-auditor" || clean == "leader" {
        return Json(json!({ "status": "error", "message": "Cannot delete protected system subagent" }));
    }
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        if dir.is_dir() {
            let _ = std::fs::remove_dir_all(&dir);
            return Json(json!({ "status": "ok", "deleted": id }));
        }
    }
    Json(json!({ "status": "error", "message": "Subagent not found" }))
}

pub async fn get_subagent_persona(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let p_file = dir.join("persona.md");
        if p_file.is_file() {
            if let Ok(content) = std::fs::read_to_string(&p_file) {
                return Json(json!({ "status": "ok", "id": id, "persona_content": content }));
            }
        }
    }
    Json(json!({ "status": "ok", "id": id, "persona_content": "" }))
}

pub async fn save_subagent_persona(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let _ = std::fs::create_dir_all(&dir);
        let content = payload.get("persona_content")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let _ = std::fs::write(dir.join("persona.md"), content);
        return Json(json!({ "status": "ok", "id": id, "saved": true }));
    }
    Json(json!({ "status": "error", "message": "Failed to resolve subagent directory" }))
}

pub async fn get_subagent_rules(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let r_file = dir.join("rules.md");
        if r_file.is_file() {
            if let Ok(content) = std::fs::read_to_string(&r_file) {
                return Json(json!({ "status": "ok", "id": id, "rules_content": content }));
            }
        }
    }
    Json(json!({ "status": "ok", "id": id, "rules_content": "" }))
}

pub async fn save_subagent_rules(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let _ = std::fs::create_dir_all(&dir);
        let content = payload.get("rules_content")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let _ = std::fs::write(dir.join("rules.md"), content);
        return Json(json!({ "status": "ok", "id": id, "saved": true }));
    }
    Json(json!({ "status": "error", "message": "Failed to resolve subagent directory" }))
}

pub async fn get_subagent_task(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let t_file = dir.join("task.md");
        if t_file.is_file() {
            if let Ok(content) = std::fs::read_to_string(&t_file) {
                return Json(json!({ "status": "ok", "id": id, "task_content": content }));
            }
        }
    }
    Json(json!({ "status": "ok", "id": id, "task_content": "" }))
}

pub async fn save_subagent_task(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let _ = std::fs::create_dir_all(&dir);
        let content = payload.get("task_content")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let _ = std::fs::write(dir.join("task.md"), content);
        return Json(json!({ "status": "ok", "id": id, "saved": true }));
    }
    Json(json!({ "status": "error", "message": "Failed to resolve subagent directory" }))
}

pub async fn get_subagent_style(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let s_file = dir.join("style.json");
        if s_file.is_file() {
            if let Ok(content) = std::fs::read_to_string(&s_file) {
                if let Ok(val) = serde_json::from_str::<Value>(&content) {
                    return Json(json!({ "status": "ok", "id": id, "style_data": val }));
                }
            }
        }
    }
    Json(json!({ "status": "ok", "id": id, "style_data": null }))
}

pub async fn save_subagent_style(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let _ = std::fs::create_dir_all(&dir);
        let style_data = payload.get("style_data").unwrap_or(&payload);
        if let Ok(content) = serde_json::to_string_pretty(style_data) {
            let _ = std::fs::write(dir.join("style.json"), content);
        }
        return Json(json!({ "status": "ok", "id": id, "saved": true, "style_data": style_data }));
    }
    Json(json!({ "status": "error", "message": "Failed to resolve subagent directory" }))
}

pub async fn get_subagent_skills(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let s_file = dir.join("skills.json");
        if s_file.is_file() {
            if let Ok(content) = std::fs::read_to_string(&s_file) {
                if let Ok(val) = serde_json::from_str::<Value>(&content) {
                    return Json(json!({ "status": "ok", "id": id, "skills": val }));
                }
            }
        }
    }
    Json(json!({ "status": "ok", "id": id, "skills": [] }))
}

pub async fn save_subagent_skills(
    Path(id): Path<String>,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let effective_ws = state.agent.get_effective_workspace_path();
    let engine_root = state.agent.resolve_engine_root();
    let roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(&effective_ws, &engine_root);
    if let Some(dir) = resolve_subagent_dir(&roots, &id) {
        let _ = std::fs::create_dir_all(&dir);
        let skills_data = payload.get("skills").unwrap_or(&payload);
        if let Ok(content) = serde_json::to_string_pretty(skills_data) {
            let _ = std::fs::write(dir.join("skills.json"), content);
        }
        return Json(json!({ "status": "ok", "id": id, "saved": true }));
    }
    Json(json!({ "status": "error", "message": "Failed to resolve subagent directory" }))
}

// ============================================================================
// PIPELINE DAG ENDPOINTS
// ============================================================================

pub async fn get_pipeline_dag(
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let engine_root = state.agent.resolve_engine_root();
    let effective_ws = state.agent.get_effective_workspace_path();

    let candidate_files = [
        engine_root.join("system").join("pipeline_dag.json"),
        engine_root.join("flowork").join("system").join("pipeline_dag.json"),
        effective_ws.join(".flowork").join("pipeline_dag.json"),
    ];
    for p in &candidate_files {
        if p.is_file() {
            if let Ok(content) = std::fs::read_to_string(p) {
                if let Ok(val) = serde_json::from_str::<Value>(&content) {
                    return Json(json!({ "status": "ok", "dag": val }));
                }
            }
        }
    }
    Json(json!({ "status": "ok", "dag": {} }))
}

pub async fn save_pipeline_dag(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let engine_root = state.agent.resolve_engine_root();
    let effective_ws = state.agent.get_effective_workspace_path();

    let target_dirs = [
        engine_root.join("system"),
        engine_root.join("flowork").join("system"),
        effective_ws.join(".flowork"),
    ];
    if let Ok(content) = serde_json::to_string_pretty(&payload) {
        for d in &target_dirs {
            let _ = std::fs::create_dir_all(d);
            let _ = std::fs::write(d.join("pipeline_dag.json"), &content);
        }
    }

    // Also mirror to atomic swarmflow/{id}.json and swarmflow/active.json
    let swarm_dir = resolve_swarmflow_dir(&engine_root, &effective_ws);
    if let Some(active_id) = payload.get("activePresetId").and_then(|v| v.as_str()) {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;
        let _ = std::fs::write(
            swarm_dir.join("active.json"),
            serde_json::to_string_pretty(&json!({
                "activePresetId": active_id,
                "updatedAt": now
            })).unwrap_or_default()
        );

        if let Some(presets_map) = payload.get("presets").and_then(|v| v.as_object()) {
            if let Some(preset_val) = presets_map.get(active_id) {
                let _ = std::fs::write(
                    swarm_dir.join(format!("{}.json", active_id)),
                    serde_json::to_string_pretty(preset_val).unwrap_or_default()
                );
            }
        }
    }

    Json(json!({ "status": "ok", "saved": true }))
}

// ============================================================================
// SWARM FLOW ATOMIC PRESETS & SEQUENTIAL RELAY ENDPOINTS
// ============================================================================

pub fn resolve_swarmflow_dir(engine_root: &std::path::Path, effective_ws: &std::path::Path) -> std::path::PathBuf {
    let candidates = [
        engine_root.join("swarmflow"),
        effective_ws.join("swarmflow"),
        effective_ws.join(".flowork").join("swarmflow"),
        engine_root.join("flowork").join("swarmflow"),
    ];
    for c in &candidates {
        if c.is_dir() {
            return c.clone();
        }
    }
    let default_dir = engine_root.join("swarmflow");
    let _ = std::fs::create_dir_all(&default_dir);
    default_dir
}

pub async fn list_swarmflow_presets(
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let engine_root = state.agent.resolve_engine_root();
    let effective_ws = state.agent.get_effective_workspace_path();
    let dir = resolve_swarmflow_dir(&engine_root, &effective_ws);

    let mut presets = serde_json::Map::new();
    let mut active_preset_id = String::from("coding");

    let active_path = dir.join("active.json");
    if active_path.is_file() {
        if let Ok(c) = std::fs::read_to_string(&active_path) {
            if let Ok(v) = serde_json::from_str::<Value>(&c) {
                if let Some(id_str) = v.get("activePresetId").or_else(|| v.get("id")).and_then(|s| s.as_str()) {
                    active_preset_id = id_str.to_string();
                }
            }
        }
    }

    if let Ok(entries) = std::fs::read_dir(&dir) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_file() && p.extension().map(|e| e == "json").unwrap_or(false) {
                let file_name = p.file_stem().and_then(|s| s.to_str()).unwrap_or("");
                if file_name == "active" {
                    continue;
                }
                if let Ok(content) = std::fs::read_to_string(&p) {
                    if let Ok(val) = serde_json::from_str::<Value>(&content) {
                        let id = val.get("id").and_then(|s| s.as_str()).unwrap_or(file_name).to_string();
                        presets.insert(id, val);
                    }
                }
            }
        }
    }

    Json(json!({
        "status": "ok",
        "activePresetId": active_preset_id,
        "presets": presets
    }))
}

pub async fn get_active_swarmflow_preset(
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let engine_root = state.agent.resolve_engine_root();
    let effective_ws = state.agent.get_effective_workspace_path();
    let dir = resolve_swarmflow_dir(&engine_root, &effective_ws);

    let active_path = dir.join("active.json");
    let mut active_preset_id = String::from("coding");
    if active_path.is_file() {
        if let Ok(c) = std::fs::read_to_string(&active_path) {
            if let Ok(v) = serde_json::from_str::<Value>(&c) {
                if let Some(id_str) = v.get("activePresetId").or_else(|| v.get("id")).and_then(|s| s.as_str()) {
                    active_preset_id = id_str.to_string();
                }
            }
        }
    }

    let preset_file = dir.join(format!("{}.json", active_preset_id));
    if preset_file.is_file() {
        if let Ok(c) = std::fs::read_to_string(&preset_file) {
            if let Ok(preset_val) = serde_json::from_str::<Value>(&c) {
                return Json(json!({
                    "status": "ok",
                    "activePresetId": active_preset_id,
                    "preset": preset_val
                }));
            }
        }
    }

    Json(json!({
        "status": "ok",
        "activePresetId": active_preset_id,
        "preset": null
    }))
}

pub async fn set_active_swarmflow_preset(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let engine_root = state.agent.resolve_engine_root();
    let effective_ws = state.agent.get_effective_workspace_path();
    let dir = resolve_swarmflow_dir(&engine_root, &effective_ws);

    let target_id = payload.get("activePresetId")
        .or_else(|| payload.get("id"))
        .and_then(|v| v.as_str())
        .unwrap_or("coding")
        .to_string();

    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64;

    let active_obj = json!({
        "activePresetId": target_id,
        "updatedAt": now
    });

    let _ = std::fs::write(dir.join("active.json"), serde_json::to_string_pretty(&active_obj).unwrap_or_default());

    // Also load the active preset to return it
    let preset_file = dir.join(format!("{}.json", target_id));
    let preset_val = if preset_file.is_file() {
        std::fs::read_to_string(&preset_file).ok().and_then(|c| serde_json::from_str::<Value>(&c).ok())
    } else {
        None
    };

    Json(json!({
        "status": "ok",
        "activePresetId": target_id,
        "preset": preset_val
    }))
}

pub async fn get_swarmflow_preset(
    axum::extract::Path(id): axum::extract::Path<String>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let engine_root = state.agent.resolve_engine_root();
    let effective_ws = state.agent.get_effective_workspace_path();
    let dir = resolve_swarmflow_dir(&engine_root, &effective_ws);

    let p = dir.join(format!("{}.json", id));
    if p.is_file() {
        if let Ok(c) = std::fs::read_to_string(&p) {
            if let Ok(val) = serde_json::from_str::<Value>(&c) {
                return Json(json!({ "status": "ok", "preset": val }));
            }
        }
    }
    Json(json!({ "status": "error", "message": format!("Preset '{}' not found", id) }))
}

pub async fn save_swarmflow_preset(
    axum::extract::Path(id): axum::extract::Path<String>,
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let engine_root = state.agent.resolve_engine_root();
    let effective_ws = state.agent.get_effective_workspace_path();
    let dir = resolve_swarmflow_dir(&engine_root, &effective_ws);

    let target_file = dir.join(format!("{}.json", id));
    if let Ok(content) = serde_json::to_string_pretty(&payload) {
        if std::fs::write(&target_file, &content).is_ok() {
            // Check if this is the active preset; if so, update active timestamp
            let active_path = dir.join("active.json");
            let mut is_active = false;
            if active_path.is_file() {
                if let Ok(c) = std::fs::read_to_string(&active_path) {
                    if let Ok(v) = serde_json::from_str::<Value>(&c) {
                        if v.get("activePresetId").and_then(|s| s.as_str()) == Some(&id) {
                            is_active = true;
                        }
                    }
                }
            }
            if is_active {
                let now = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_millis() as u64;
                let _ = std::fs::write(active_path, serde_json::to_string_pretty(&json!({
                    "activePresetId": id,
                    "updatedAt": now
                })).unwrap_or_default());
            }

            return Json(json!({ "status": "ok", "id": id, "saved": true }));
        }
    }
    Json(json!({ "status": "error", "message": "Failed to write preset file" }))
}

pub async fn relay_swarmflow_step(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    let engine_root = state.agent.resolve_engine_root();
    let effective_ws = state.agent.get_effective_workspace_path();
    let dir = resolve_swarmflow_dir(&engine_root, &effective_ws);

    let current_node_id = payload.get("node_id").and_then(|v| v.as_str()).unwrap_or("");
    let status_str = payload.get("status").and_then(|v| v.as_str()).unwrap_or("DONE");
    let summary = payload.get("output").and_then(|v| v.as_str()).unwrap_or("");

    // Read active preset
    let active_path = dir.join("active.json");
    let active_preset_id = if active_path.is_file() {
        std::fs::read_to_string(&active_path)
            .ok()
            .and_then(|c| serde_json::from_str::<Value>(&c).ok())
            .and_then(|v| v.get("activePresetId").and_then(|s| s.as_str()).map(|s| s.to_string()))
            .unwrap_or_else(|| "coding".to_string())
    } else {
        "coding".to_string()
    };

    let preset_file = dir.join(format!("{}.json", active_preset_id));
    if let Ok(c) = std::fs::read_to_string(&preset_file) {
        if let Ok(preset) = serde_json::from_str::<Value>(&c) {
            let nodes = preset.get("nodes").and_then(|v| v.as_array()).cloned().unwrap_or_default();
            let connections = preset.get("connections").and_then(|v| v.as_array()).cloned().unwrap_or_default();

            // Find downstream targets from current_node_id
            let mut next_targets: Vec<Value> = Vec::new();
            for conn in &connections {
                let from_id = conn.get("from").and_then(|v| v.as_str()).unwrap_or("");
                let to_id = conn.get("to").and_then(|v| v.as_str()).unwrap_or("");
                if from_id == current_node_id && !to_id.is_empty() {
                    if let Some(target_node) = nodes.iter().find(|n| n.get("id").and_then(|v| v.as_str()) == Some(to_id)) {
                        next_targets.push(target_node.clone());
                    }
                }
            }

            return Json(json!({
                "status": "ok",
                "activePresetId": active_preset_id,
                "completedNodeId": current_node_id,
                "nodeStatus": status_str,
                "summary": summary,
                "nextNodes": next_targets,
                "hasDownstream": !next_targets.is_empty()
            }));
        }
    }

    Json(json!({
        "status": "error",
        "message": "Failed to resolve active pipeline relay"
    }))
}




