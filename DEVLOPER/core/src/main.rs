mod agent;
mod asset_server;
mod auth;
mod auth_callback;
mod config;
mod copilot;
mod discovery;
mod ipc_router;
mod manifest;
mod port_manager;
mod prompt_seal;
mod supervisor;
mod sync_drive;
mod sync_watcher;
mod tools;
mod viewport;
mod window;
mod workspace;
mod scheduler;
pub mod trigger;
pub mod system_trigger;
pub mod agents;
pub mod persona;
pub mod prompt_enclave;
pub mod attestation;
pub mod anti_tamper;
pub mod anti_leak;
pub mod connector_enclave;
pub mod root_pillars;
pub mod sealed_system;
pub mod rea_enclave;
pub mod engineering_enclave;
pub mod native_tools;
pub mod sealed_tools;
pub mod sovereign_enclave;
pub mod swarm_dag;
pub mod sandbox;
pub mod credential_shield;
pub mod symbolic_memory;

use agent::AgentService;
use asset_server::{
    serve_canvas_file, serve_canvas_root, serve_app_gui, serve_app_gui_redirect,
    serve_app_gui_root, serve_plugin_gui, serve_plugin_gui_redirect,
    serve_plugin_gui_root, serve_favicon_ico, serve_favicon_png, serve_favicon_svg,
    serve_manifest_json, system_panic_trigger,
};
use auth::AuthManager;
use axum::{routing::{delete, get, post}, Router};
use config::AppConfig;
use copilot::CopilotManager;
use discovery::PluginDiscovery;
use ipc_router::{
    add_sync_drive_folder, cancel_scheduled_job, chat_delete_history, chat_get_history, chat_get_steps,
    chat_new_session, chat_regenerate_turn, chat_send_message, chat_set_session_persona, update_chat_session_mode, chat_set_session_workspace, chat_stop_turn, chat_truncate_turn,
    chat_undo_turn, chat_create_group, chat_list_groups, chat_get_group_members, chat_add_group_members, chat_remove_group_member,
    create_scheduled_job, create_workspace, delete_scheduled_job, delete_workspace, gdrive_oauth_callback,
    get_active_viewport, get_auth_status, get_auth_ticket, get_available_personas, get_copilot_registry, get_default_save_path,
    get_plugin_status, get_sync_drive_login_url, get_sync_drive_status, get_workspaces,
    install_copilot_plugin, launch_desktop_recorder, launch_plugin, list_plugins, list_skills, list_scheduled_jobs, logout_auth, pick_folder_dialog, pick_save_dialog,
    open_plugin, reload_plugin, close_plugin,
    list_all_triggers, test_trigger_endpoint, toggle_trigger_daemon, get_trigger_store, install_trigger_endpoint, create_trigger_endpoint,
    list_system_prompts, get_system_prompt_content, save_system_prompt,
    get_subagent_persona, save_subagent_persona, get_subagent_rules, save_subagent_rules, get_subagent_task, save_subagent_task,
    get_subagent_style, save_subagent_style, get_subagent_skills, save_subagent_skills,
    get_subagent_circuit_breaker, save_subagent_circuit_breaker,
    list_subagents, create_subagent, delete_subagent,
    get_pipeline_dag, save_pipeline_dag,
    list_swarmflow_presets, get_active_swarmflow_preset, set_active_swarmflow_preset,
    get_swarmflow_preset, save_swarmflow_preset, relay_swarmflow_step,
    plugin_events, prompt_dispatch, remove_sync_drive_account, remove_sync_drive_folder,
    restore_sync_drive_file, save_file_to_disk, set_active_viewport, set_auth_token, stop_plugin,
    switch_workspace, uninstall_copilot_plugin, update_scheduled_job, AppState,
};
use scheduler::SchedulerManager;
use port_manager::PortManager;
use std::sync::Arc;
use supervisor::ProcessSupervisor;
use sync_drive::SyncDriveManager;
use sync_watcher::SyncWatcher;
use tower_http::cors::CorsLayer;
use window::WindowManager;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--help" || a == "-h") {
        println!("Flowork Sovereign OS Core Runtime");
        println!("Usage: flowork [OPTIONS]");
        println!();
        println!("Options:");
        println!("  -h, --help       Print this help message and exit");
        println!("  -v, --version    Print version information and exit");
        println!("  --headless       Run core in headless background mode (no GUI window)");
        println!("  --no-window      Alias for --headless");
        println!("  --restarted      Internal flag indicating post-restart recovery");
        return Ok(());
    }
    if args.iter().any(|a| a == "--version" || a == "-v") {
        println!("flowork {}", env!("CARGO_PKG_VERSION"));
        return Ok(());
    }

    let cfg = Arc::new(AppConfig::new());

    // 0. Sovereign Cryptographic Gatekeeper: Verify connection to auth authority & launcher seal
    let _ = prompt_enclave::PromptEnclave::url_auth();
    let _ = prompt_enclave::PromptEnclave::url_launcher();

    // 0.1 Enforce Level 3 Anti-Debugger and Process Tamper Shield
    anti_tamper::AntiTamper::enforce_shield();

    // 1. Verify Cryptographic Prompt Integrity Seal (Instant abort if tampered)
    let _ = prompt_enclave::PromptEnclave::prompt_solo();
    let _ = prompt_enclave::PromptEnclave::prompt_team();
    let _ = prompt_seal::PromptSeal::get_sovereign_constitution();
    let _ = prompt_seal::PromptSeal::get_anti_jailbreak_rules();
    let _ = prompt_seal::PromptSeal::get_subagent_fallback("system", "core");
    let _ = connector_enclave::ConnectorEnclave::manifest();
    let _ = prompt_enclave::PromptEnclave::url_auth();
    let _ = prompt_enclave::PromptEnclave::url_plugins();
    let _ = prompt_enclave::PromptEnclave::url_skills_repo();
    let _ = prompt_seal::PromptSeal::get_subagent_worker_mandate();
    println!("[X-Flow Core] 🛡️ All Cryptographic Prompt, URL & Morphological Fingerprint Seals verified (HMAC-SHA256, Length & Space/Vowel Lock OK).");

    // 2. Ensure Golden Assets Integrity and Authoritative SKILL.MD Enclaves in Tubuh Flowork
    asset_server::ensure_golden_assets(&cfg.canvas_dir).await;
    workspace::ensure_flowork_body_pillars(&cfg.root_dir);
    discovery::PluginDiscovery::ensure_plugin_skill(&cfg.plugins_dir);

    let port_mgr = Arc::new(PortManager::new());
    let supervisor = Arc::new(ProcessSupervisor::new());
    let copilot = Arc::new(CopilotManager::new(cfg.root_dir.clone(), cfg.plugins_dir.clone()));
    let (discovery, _) = PluginDiscovery::new(cfg.plugins_dir.clone(), cfg.skills_dir.clone());
    let discovery = Arc::new(discovery);
    let auth = Arc::new(AuthManager::new(&cfg.root_dir, cfg.port));

    // Verify existing vault session if token is present (Hard-crash on revocation or machine mismatch)
    auth.check_heartbeat_or_crash().await;

    // Start background auth heartbeat monitor (Strict lifecycle dependence on auth authority)
    let auth_heartbeat = auth.clone();
    tokio::spawn(async move {
        tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
        auth_heartbeat.check_heartbeat_or_crash().await;
        let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(300));
        loop {
            interval.tick().await;
            auth_heartbeat.check_heartbeat_or_crash().await;
        }
    });
    let sync_drive = Arc::new(SyncDriveManager::new(&cfg.root_dir, cfg.port));
    let viewport = Arc::new(viewport::ViewportManager::new(&cfg.root_dir));
    let workspace_mgr = Arc::new(workspace::WorkspaceManager::new(&cfg.root_dir));
    let scheduler_mgr = Arc::new(SchedulerManager::new_with_root(&cfg.root_dir));
    let agent = Arc::new(AgentService::new(&cfg.root_dir)
        .attach_plugin_mesh(discovery.clone(), supervisor.clone())
        .attach_viewport(viewport.clone())
        .attach_workspace_manager(workspace_mgr.clone())
        .attach_scheduler(scheduler_mgr.clone()));

    // Initial scan and start hot-plug watcher
    discovery.scan_all().await;
    discovery.clone().start_watcher();

    // Start background sync drive folder watcher
    let watcher = Arc::new(SyncWatcher::new(sync_drive.clone()));
    watcher.start_worker();

    // Spawn autonomous scheduler-to-agent dispatcher
    let mut sched_rx = scheduler_mgr.subscribe_events();
    let agent_for_sched = agent.clone();
    tokio::spawn(async move {
        while let Ok(event) = sched_rx.recv().await {
            if event.get("event").and_then(|e| e.as_str()) == Some("schedule_fired") {
                let session_id = event.get("session_id").and_then(|s| s.as_str()).unwrap_or("").to_string();
                let prompt = event.get("prompt").and_then(|p| p.as_str()).unwrap_or("").to_string();
                let job_id = event.get("job_id").and_then(|j| j.as_str()).unwrap_or("").to_string();
                if !session_id.is_empty() && !prompt.is_empty() {
                    let wakeup_msg = format!("⏰ [SCHEDULED TASK FIRED: {}]\n{}", job_id, prompt);
                    println!("[SchedulerDispatcher] ⚡ Injecting scheduled task {} into session {}", job_id, session_id);
                    let _ = agent_for_sched.send_turn(&session_id, &wakeup_msg, None).await;
                }
            }
        }
    });

    // Auto-resume persisted schedule routines and timers
    scheduler_mgr.start_persisted_workers().await;

    // Auto-resume pending restart handshake if any (Flowork Self-Evolution)
    let root_dir_resume = cfg.root_dir.clone();
    let agent_for_resume = agent.clone();
    let discovery_for_resume = discovery.clone();
    tokio::spawn(async move {
        tokio::time::sleep(tokio::time::Duration::from_millis(2000)).await;
        let candidate_resume_paths = [
            root_dir_resume.join("portable-home").join(".flowork").join("pending_restart_resume.json"),
            root_dir_resume.join(".flowork").join("pending_restart_resume.json"),
        ];
        for resume_path in candidate_resume_paths {
            if resume_path.exists() {
                if let Ok(content) = tokio::fs::read_to_string(&resume_path).await {
                    let _ = tokio::fs::remove_file(&resume_path).await;
                    if let Ok(data) = serde_json::from_str::<serde_json::Value>(&content) {
                        let session_id = data.get("session_id").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        let prompt = data.get("resume_prompt").and_then(|v| v.as_str())
                            .unwrap_or("Biner Flowork berhasil di-restart dan memuat pembaruan terbaru. Lanjutkan tugas.")
                            .to_string();
                        if !session_id.is_empty() {
                            println!("[SystemRestart] 🔄 Auto-resuming session {} post-restart: {}", session_id, prompt);
                            discovery_for_resume.broadcast_system_restarted(&session_id);
                            let _ = agent_for_resume.send_turn(&session_id, &prompt, None).await;
                        }
                    }
                }
                break;
            }
        }
    });

    let state = Arc::new(AppState {
        cfg: cfg.clone(),
        discovery: discovery.clone(),
        supervisor: supervisor.clone(),
        port_mgr,
        copilot,
        auth: auth.clone(),
        sync_drive,
        agent,
        viewport,
        workspace_mgr,
        scheduler_mgr,
        last_prompt_dispatch: Arc::new(tokio::sync::Mutex::new((String::new(), std::time::Instant::now() - std::time::Duration::from_secs(10)))),
    });

    let app = Router::new()
        .route("/", get(serve_canvas_root))
        .route("/canvas/*file", get(serve_canvas_file))
        .route("/apps/:id/gui", get(serve_app_gui_redirect))
        .route("/apps/:id/gui/", get(serve_app_gui_root))
        .route("/apps/:id/gui/*subpath", get(serve_app_gui))
        .route("/api/apps", get(list_plugins))
        .route("/api/apps/:id/launch", post(launch_plugin))
        .route("/api/apps/:id/open", post(open_plugin))
        .route("/api/apps/:id/reload", post(reload_plugin))
        .route("/api/apps/:id/close", post(close_plugin))
        .route("/api/apps/:id/stop", post(stop_plugin))
        .route("/api/apps/:id/status", get(get_plugin_status))
        .route("/plugins/:id/gui", get(serve_plugin_gui_redirect))
        .route("/plugins/:id/gui/", get(serve_plugin_gui_root))
        .route("/plugins/:id/gui/*subpath", get(serve_plugin_gui))
        .route("/api/plugins", get(list_plugins))
        .route("/api/skills", get(list_skills))
        .route("/api/agents", get(get_available_personas))
        .route("/api/personas", get(get_available_personas))
        .route("/api/plugins/:id/launch", post(launch_plugin))
        .route("/api/plugins/:id/open", post(open_plugin))
        .route("/api/plugins/:id/reload", post(reload_plugin))
        .route("/api/plugins/:id/close", post(close_plugin))
        .route("/api/plugins/:id/stop", post(stop_plugin))
        .route("/api/plugins/:id/status", get(get_plugin_status))
        .route("/api/viewport/active", get(get_active_viewport).post(set_active_viewport))
        .route("/api/workspaces", get(get_workspaces))
        .route("/api/workspaces/create", post(create_workspace))
        .route("/api/workspaces/switch", post(switch_workspace))
        .route("/api/workspaces/delete", post(delete_workspace))
        .route("/api/schedule", get(list_scheduled_jobs).post(create_scheduled_job))
        .route("/api/schedule/cancel", post(cancel_scheduled_job))
        .route("/api/schedule/delete", post(delete_scheduled_job))
        .route("/api/schedule/update", post(update_scheduled_job))
        .route("/api/triggers/list", get(list_all_triggers))
        .route("/api/triggers/test", post(test_trigger_endpoint))
        .route("/api/triggers/toggle", post(toggle_trigger_daemon))
        .route("/api/triggers/store", get(get_trigger_store))
        .route("/api/triggers/install", post(install_trigger_endpoint))
        .route("/api/triggers/create", post(create_trigger_endpoint))
        .route("/api/prompts/list", get(list_system_prompts))
        .route("/api/prompts/content", get(get_system_prompt_content))
        .route("/api/prompts/save", post(save_system_prompt))
        .route("/api/subagents", get(list_subagents).post(create_subagent))
        .route("/api/subagents/:id", delete(delete_subagent))
        .route("/api/subagents/:id/persona", get(get_subagent_persona).post(save_subagent_persona))
        .route("/api/subagents/:id/rules", get(get_subagent_rules).post(save_subagent_rules))
        .route("/api/subagents/:id/task", get(get_subagent_task).post(save_subagent_task))
        .route("/api/subagents/:id/style", get(get_subagent_style).post(save_subagent_style))
        .route("/api/subagents/:id/skills", get(get_subagent_skills).post(save_subagent_skills))
        .route("/api/subagents/:id/circuit_breaker", get(get_subagent_circuit_breaker).post(save_subagent_circuit_breaker))
        .route("/api/pipeline/dag", get(get_pipeline_dag).post(save_pipeline_dag))
        .route("/api/swarmflow/presets", get(list_swarmflow_presets))
        .route("/api/swarmflow/active", get(get_active_swarmflow_preset).post(set_active_swarmflow_preset))
        .route("/api/swarmflow/preset/:id", get(get_swarmflow_preset).post(save_swarmflow_preset))
        .route("/api/swarmflow/relay", post(relay_swarmflow_step))
        .route("/api/dialog/pick-folder", get(pick_folder_dialog))
        .route("/api/events", get(plugin_events))
        .route("/api/copilot/registry", get(get_copilot_registry))
        .route("/api/copilot/install/:id", post(install_copilot_plugin))
        .route("/api/copilot/uninstall/:id", post(uninstall_copilot_plugin))
        .route("/api/dialog/default-dir", get(get_default_save_path))
        .route("/api/dialog/save-file", get(pick_save_dialog))
        .route("/api/fs/save-file", post(save_file_to_disk))
        .route("/favicon.ico", get(serve_favicon_ico))
        .route("/favicon.png", get(serve_favicon_png))
        .route("/favicon.svg", get(serve_favicon_svg))
        .route("/apple-touch-icon.png", get(serve_favicon_png))
        .route("/apple-touch-icon-precomposed.png", get(serve_favicon_png))
        .route("/manifest.json", get(serve_manifest_json))
        .route("/auth/flowork-callback", get(auth_callback::flowork_callback))
        .route("/auth/callback", get(auth_callback::flowork_callback))
        .route("/auth/ticket", get(get_auth_ticket).post(get_auth_ticket))
        .route("/auth/login-url", get(get_auth_ticket))
        .route("/api/auth/ticket", get(get_auth_ticket).post(get_auth_ticket))
        .route("/api/auth/status", get(get_auth_status))
        .route("/api/auth/set-token", post(set_auth_token))
        .route("/api/auth/logout", post(logout_auth))
        .route("/api/system/panic", post(system_panic_trigger))
        .route("/api/sync-drive/status", get(get_sync_drive_status))
        .route("/api/sync-drive/auth/login-url", get(get_sync_drive_login_url))
        .route("/api/gdrive/auth/callback", get(gdrive_oauth_callback))
        .route("/api/sync-drive/folders/add", post(add_sync_drive_folder))
        .route("/api/sync-drive/folders/remove", post(remove_sync_drive_folder))
        .route("/api/sync-drive/accounts/remove", post(remove_sync_drive_account))
        .route("/api/sync-drive/restore", post(restore_sync_drive_file))
        .route("/api/recorder/launch", post(launch_desktop_recorder).get(launch_desktop_recorder))
        .route("/api/chat/new", post(chat_new_session))
        .route("/api/chat/history", get(chat_get_history))
        .route("/api/chat/history/:id", delete(chat_delete_history))
        .route("/api/chat/steps/:id", get(chat_get_steps))
        .route("/api/chat/sessions/:id/workspace", post(chat_set_session_workspace))
        .route("/api/chat/sessions/:id/persona", post(chat_set_session_persona))
        .route("/api/chat/sessions/:id/mode", post(update_chat_session_mode).put(update_chat_session_mode))
        .route("/api/chat/groups", post(chat_create_group))
        .route("/api/chat/groups", get(chat_list_groups))
        .route("/api/chat/sessions/:id/members", get(chat_get_group_members))
        .route("/api/chat/sessions/:id/members", post(chat_add_group_members))
        .route("/api/chat/sessions/:id/members/:member_id", delete(chat_remove_group_member))
        .route("/api/chat/message", post(chat_send_message))
        .route("/api/chat/stop", post(chat_stop_turn))
        .route("/api/chat/undo", post(chat_undo_turn))
        .route("/api/chat/truncate", post(chat_truncate_turn))
        .route("/api/chat/regenerate", post(chat_regenerate_turn))
        .route("/api/prompt-dispatch", post(prompt_dispatch))
        .route("/api/chat/prompt-dispatch", post(prompt_dispatch))
        .layer(axum::middleware::from_fn(pna_middleware))
        .layer(CorsLayer::permissive())
        .with_state(state.clone());

    let addr = format!("{}:{}", cfg.host, cfg.port);
    let mut listener = None;
    for attempt in 1..=20 {
        match tokio::net::TcpListener::bind(&addr).await {
            Ok(l) => {
                listener = Some(l);
                break;
            }
            Err(e) if e.kind() == std::io::ErrorKind::AddrInUse && attempt < 20 => {
                println!("[X-Flow Core] ⏳ Port {addr} still occupied, waiting... (attempt {attempt}/20)");
                tokio::time::sleep(tokio::time::Duration::from_millis(300)).await;
            }
            Err(e) => return Err(e.into()),
        }
    }
    let listener = listener.expect("Failed to bind TCP listener");
    let proto_http = crate::prompt_enclave::PromptEnclave::proto_http();
    println!("[X-Flow Core] Sovereign Canvas Host listening on {proto_http}{addr}");

    let is_restarted = std::env::args().any(|a| a == "--restarted");
    let is_headless = std::env::args().any(|a| a == "--headless" || a == "--no-window") || is_restarted;
    let window_rx = if !is_headless {
        let is_auth = state.auth.is_authorized().await;
        let url = if !is_auth {
            format!("{}?port={}", crate::prompt_enclave::PromptEnclave::url_launcher(), cfg.port)
        } else {
            format!("{proto_http}{addr}")
        };
        WindowManager::open_desktop_window(&url)
    } else {
        None
    };

    if let Some(rx) = window_rx {
        let addr_clone = addr.clone();
        tokio::spawn(async move {
            let _ = rx.await;
            let proto = crate::prompt_enclave::PromptEnclave::proto_http();
            println!("[X-Flow Core] ℹ️ Desktop window detached. Core host remains active on {proto}{addr_clone}. Press Ctrl+C or send SIGTERM to stop.");
        });
    }

    tokio::select! {
        res = axum::serve(listener, app) => {
            if let Err(e) = res {
                eprintln!("[X-Flow Core] ❌ Server error: {e}");
            }
        },
        _ = shutdown_signal() => {},
    }

    println!("\n[X-Flow Core] 🛑 Shutting down. Cleaning up all polyglot engines & agent daemons...");
    WindowManager::close_desktop_window();
    supervisor.stop_all().await;
    state.agent.stop_all_processes().await;

    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        let _ = tokio::signal::ctrl_c().await;
    };

    #[cfg(unix)]
    let terminate = async {
        if let Ok(mut sig) = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate()) {
            sig.recv().await;
        } else {
            std::future::pending::<()>().await;
        }
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }
}

async fn pna_middleware(req: axum::extract::Request, next: axum::middleware::Next) -> axum::response::Response {
    let mut resp = next.run(req).await;
    resp.headers_mut().insert(
        axum::http::header::HeaderName::from_static("access-control-allow-private-network"),
        axum::http::HeaderValue::from_static("true"),
    );
    resp
}

