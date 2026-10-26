use axum::extract::{Path as AxPath, State};
use axum::http::{header, HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response, Redirect};
use std::sync::Arc;
use std::path::Path;
use crate::ipc_router::AppState;
use crate::auth_callback::ensure_callback_assets;

/// Pure disk-driven asset server initialization:
/// Ensures necessary canvas directory structure exists without auto-reconstituting or overwriting files from binary memory.
pub async fn ensure_golden_assets(canvas_dir: &Path) {
    let _ = tokio::fs::create_dir_all(canvas_dir).await;
    let sounds_dir = canvas_dir.join("sounds");
    let _ = tokio::fs::create_dir_all(&sounds_dir).await;
    let vendor_three_dir = canvas_dir.join("vendor").join("three");
    let vendor_addons_dir = vendor_three_dir.join("addons").join("controls");
    let _ = tokio::fs::create_dir_all(&vendor_addons_dir).await;

    // Isolated OAuth Callback Channel
    ensure_callback_assets(canvas_dir).await;

    // Member Area Directory
    let member_dir = canvas_dir.join("member-area");
    let _ = tokio::fs::create_dir_all(&member_dir).await;
}

// =========================================================================
// ROOT FAVICON & MANIFEST HANDLERS (Served purely from disk with 404 fallback)
// =========================================================================
pub async fn serve_favicon_ico(State(state): State<Arc<AppState>>) -> Response {
    serve_disk_file(&state.cfg.canvas_dir.join("favicon.ico")).await
}

pub async fn serve_favicon_png(State(state): State<Arc<AppState>>) -> Response {
    serve_disk_file(&state.cfg.canvas_dir.join("favicon.png")).await
}

pub async fn serve_favicon_svg(State(state): State<Arc<AppState>>) -> Response {
    serve_disk_file(&state.cfg.canvas_dir.join("favicon.svg")).await
}

pub async fn serve_manifest_json(State(state): State<Arc<AppState>>) -> Response {
    serve_disk_file(&state.cfg.canvas_dir.join("manifest.json")).await
}

pub const HYBRID_AUTH_HTML: &str = include_str!("assets/auth.html");

#[allow(dead_code)]
pub async fn get_edge_launcher_html() -> String {
    r#"<!DOCTYPE html><html><head><meta charset="utf-8"><title>Flowork OS</title><meta http-equiv="refresh" content="0; url=/canvas/member-area/index.html"></head><body style="background:#04060a;color:#00e5ff;font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"><div>⚡ Redirecting to Sovereign Canvas...</div></body></html>"#.to_string()
}

pub async fn serve_canvas_root(State(_state): State<Arc<AppState>>) -> Response {
    Redirect::temporary("/canvas/member-area/index.html").into_response()
}

pub async fn serve_canvas_file(AxPath(file): AxPath<String>, State(state): State<Arc<AppState>>) -> Response {
    let clean = file.replace("..", "").trim_start_matches('/').to_string();

    // Serve local sovereign launcher on local port
    if clean == "launcher.html" || clean == "launcher" || clean == "launcher/index.html" {
        return Redirect::temporary("/canvas/member-area/index.html").into_response();
    }

    // Serve hybrid auth attestation HTML directly on local port
    if clean == "auth.html" || clean == "auth" {
        return (
            StatusCode::OK,
            [(header::CONTENT_TYPE, HeaderValue::from_static("text/html; charset=utf-8"))],
            HYBRID_AUTH_HTML,
        ).into_response();
    }

    // Serve callback HTML directly from binary memory (Immutably locked)
    if clean == "callback.html" || clean == "callback" {
        let unsealed = crate::prompt_seal::unseal_bytes(crate::auth_callback::GOLDEN_CALLBACK_HTML);
        return (
            StatusCode::OK,
            [(header::CONTENT_TYPE, HeaderValue::from_static("text/html; charset=utf-8"))],
            unsealed,
        ).into_response();
    }

    // Redirect legacy /canvas/index.html to /canvas/member-area/index.html
    if clean == "index.html" {
        let member_index = state.cfg.canvas_dir.join("member-area").join("index.html");
        if member_index.exists() {
            return Redirect::temporary("/canvas/member-area/index.html").into_response();
        }
    }

    // Serve local office_3d.js if exists on disk, fallback to Cloudflare Pages stream
    if clean == "office_3d.js" {
        let local_office = state.cfg.canvas_dir.join("office_3d.js");
        if local_office.exists() {
            return serve_disk_file(&local_office).await;
        }
        return Redirect::temporary(&crate::prompt_enclave::PromptEnclave::url_canvas_office_3d()).into_response();
    }

    let mut path = if clean.starts_with("bin/") {
        state.cfg.root_dir.join(".FL_BIN").join(&clean[4..])
    } else if clean.starts_with(".FL_BIN/") {
        state.cfg.root_dir.join(".FL_BIN").join(&clean[8..])
    } else if clean.starts_with("screenshots/") {
        state.cfg.root_dir.join(".FL_BIN").join("screenshots").join(&clean[12..])
    } else if clean.starts_with("generated_images/") {
        state.cfg.root_dir.join(".FL_BIN").join("generated_images").join(&clean[17..])
    } else {
        state.cfg.canvas_dir.join(&clean)
    };

    if !path.exists() {
        let fallback = state.cfg.root_dir.join(&clean);
        if fallback.exists() {
            path = fallback;
        } else {
            let cdn_url = format!("{}/{}", crate::prompt_enclave::PromptEnclave::url_canvas_cdn_base(), clean);
            return Redirect::temporary(&cdn_url).into_response();
        }
    }

    serve_disk_file(&path).await
}

pub async fn serve_app_gui_redirect(
    AxPath(id): AxPath<String>,
) -> Response {
    let target = format!("/apps/{}/gui/", id);
    (StatusCode::PERMANENT_REDIRECT, [(header::LOCATION, target)]).into_response()
}

pub async fn serve_plugin_gui_redirect(
    AxPath(id): AxPath<String>,
) -> Response {
    serve_app_gui_redirect(AxPath(id)).await
}

pub async fn serve_app_gui_root(
    AxPath(id): AxPath<String>,
    State(state): State<Arc<AppState>>,
) -> Response {
    serve_app_gui(AxPath((id, "".to_string())), State(state)).await
}

pub async fn serve_plugin_gui_root(
    AxPath(id): AxPath<String>,
    State(state): State<Arc<AppState>>,
) -> Response {
    serve_app_gui_root(AxPath(id), State(state)).await
}

fn escape_html(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#39;")
}

pub async fn serve_app_gui(
    AxPath((id, subpath)): AxPath<(String, String)>,
    State(state): State<Arc<AppState>>,
) -> Response {
    if !state.auth.is_authorized().await {
        crate::anti_tamper::AntiTamper::trigger_fatal_quarantine(&format!("Unauthorized access to app '{}' without valid session from auth.floworkos.com", id));
    }

    if let Some(plugin) = state.discovery.get(&id).await {
        let clean = subpath.replace("..", "").trim_start_matches('/').to_string();
        let is_root_html = clean.is_empty() || clean == "index.html";

        let configured_gui = plugin.entry.gui.as_deref().unwrap_or("gui/index.html");

        let candidate_path = if clean.is_empty() {
            let p_conf = plugin.root_dir.join(configured_gui);
            let p_gui = plugin.root_dir.join("gui").join("index.html");
            let p_root = plugin.root_dir.join("index.html");
            let p_dist = plugin.root_dir.join("dist").join("index.html");
            let p_pub = plugin.root_dir.join("public").join("index.html");

            if p_conf.exists() {
                Some(p_conf)
            } else if p_gui.exists() {
                Some(p_gui)
            } else if p_root.exists() {
                Some(p_root)
            } else if p_dist.exists() {
                Some(p_dist)
            } else if p_pub.exists() {
                Some(p_pub)
            } else {
                None
            }
        } else {
            let gui_parent = Path::new(configured_gui).parent().unwrap_or(Path::new("gui"));
            let p_conf_sub = plugin.root_dir.join(gui_parent).join(&clean);
            let p_gui_sub = plugin.root_dir.join("gui").join(&clean);
            let p_root_sub = plugin.root_dir.join(&clean);
            let p_dist_sub = plugin.root_dir.join("dist").join(&clean);
            let p_pub_sub = plugin.root_dir.join("public").join(&clean);

            if p_conf_sub.exists() {
                Some(p_conf_sub)
            } else if p_gui_sub.exists() {
                Some(p_gui_sub)
            } else if p_root_sub.exists() {
                Some(p_root_sub)
            } else if p_dist_sub.exists() {
                Some(p_dist_sub)
            } else if p_pub_sub.exists() {
                Some(p_pub_sub)
            } else {
                None
            }
        };

        if let Some(file_path) = candidate_path {
            if is_root_html {
                if let Ok(content) = tokio::fs::read_to_string(&file_path).await {
                    let base_tag = format!("<base href=\"/apps/{}/gui/\">", id);
                    let html = if !content.contains("<base href=") && content.contains("<head>") {
                        content.replacen("<head>", &format!("<head>\n    {}", base_tag), 1)
                    } else {
                        content
                    };
                    let mut res = html.into_response();
                    res.headers_mut().insert(
                        header::CONTENT_TYPE,
                        HeaderValue::from_static("text/html; charset=utf-8"),
                    );
                    return res;
                }
            }
            return serve_disk_file(&file_path).await;
        }

        // Developer Scaffold Fallback when no HTML file is found
        if is_root_html {
            let active_port_str = state
                .supervisor
                .get_port(&id)
                .await
                .map(|p| format!("Live Port :{}", p))
                .unwrap_or_else(|| "Backend: Idle / Headless".to_string());

            let html = format!(
                r#"<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{name} — Flowork OS</title>
  <style>
    :root {{
      --bg: #07090e;
      --card-bg: rgba(15, 23, 42, 0.85);
      --border: rgba(0, 229, 255, 0.3);
      --text: #f8fafc;
      --accent: #00e5ff;
      --sub: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: radial-gradient(circle at 50% 20%, #0d1b2a 0%, var(--bg) 100%);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}
    .capsule-box {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 36px 40px;
      max-width: 620px;
      width: 100%;
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6), 0 0 24px rgba(0, 229, 255, 0.1);
      backdrop-filter: blur(16px);
      text-align: center;
    }}
    .app-icon {{
      font-size: 54px;
      margin-bottom: 16px;
      filter: drop-shadow(0 0 16px rgba(0, 229, 255, 0.4));
    }}
    h1 {{
      font-size: 24px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 8px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-family: monospace;
      font-weight: 600;
      background: rgba(0, 229, 255, 0.12);
      color: var(--accent);
      border: 1px solid rgba(0, 229, 255, 0.3);
      margin-bottom: 20px;
    }}
    p.desc {{
      font-size: 14px;
      color: var(--sub);
      line-height: 1.6;
      margin-bottom: 24px;
    }}
    .dev-guide {{
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 10px;
      padding: 16px;
      text-align: left;
      font-size: 13px;
      font-family: monospace;
      color: #cbd5e1;
      margin-bottom: 24px;
    }}
    .dev-guide code {{
      color: var(--accent);
      background: rgba(0, 229, 255, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: linear-gradient(135deg, #00e5ff 0%, #0077b6 100%);
      color: #050b14;
      font-weight: 700;
      font-size: 13px;
      padding: 10px 22px;
      border-radius: 8px;
      border: none;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s ease;
    }}
    .btn:hover {{
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 229, 255, 0.4);
    }}
  </style>
</head>
<body>
  <div class="capsule-box">
    <div class="app-icon">{icon}</div>
    <h1>{name}</h1>
    <div class="badge">{status} • v{version}</div>
    <p class="desc">{desc}</p>
    <div class="dev-guide">
      <div style="font-weight: bold; margin-bottom: 6px; color: #fff;">💡 Sovereign App Scaffold Guide:</div>
      <div>• GUI Entry: <code>{gui_entry}</code> (Not found)</div>
      <div>• Create <code>gui/index.html</code> in <code>apps/{app_id}/</code></div>
      <div>• Or configure <code>entry.gui</code> in <code>app.manifest.json</code></div>
    </div>
    <button class="btn" onclick="location.reload()">🔄 Refresh GUI</button>
  </div>
</body>
</html>"#,
                name = escape_html(&plugin.name),
                icon = plugin.icon.as_deref().unwrap_or("⚡"),
                status = active_port_str,
                version = plugin.version,
                desc = plugin
                    .description
                    .as_deref()
                    .unwrap_or("Polyglot sovereign application under development."),
                gui_entry = configured_gui,
                app_id = id
            );

            let mut res = html.into_response();
            res.headers_mut().insert(
                header::CONTENT_TYPE,
                HeaderValue::from_static("text/html; charset=utf-8"),
            );
            return res;
        }
    }
    StatusCode::NOT_FOUND.into_response()
}

pub async fn serve_plugin_gui(
    path: AxPath<(String, String)>,
    state: State<Arc<AppState>>,
) -> Response {
    serve_app_gui(path, state).await
}

pub async fn serve_disk_file(path: &std::path::Path) -> Response {
    if !path.exists() {
        return StatusCode::NOT_FOUND.into_response();
    }
    match tokio::fs::read(path).await {
        Ok(bytes) => {
            let mime = mime_guess::from_path(path).first_or_octet_stream();
            let mut res = bytes.into_response();
            let h = res.headers_mut();
            h.insert(
                header::CONTENT_TYPE,
                HeaderValue::from_str(mime.as_ref()).unwrap_or(HeaderValue::from_static("application/octet-stream")),
            );
            h.insert(
                header::CACHE_CONTROL,
                HeaderValue::from_static("no-cache, no-store, must-revalidate, max-age=0"),
            );
            h.insert(
                header::PRAGMA,
                HeaderValue::from_static("no-cache"),
            );
            h.insert(
                header::EXPIRES,
                HeaderValue::from_static("0"),
            );
            h.insert(
                header::HeaderName::from_static("x-frame-options"),
                HeaderValue::from_static("SAMEORIGIN"),
            );
            h.insert(
                header::HeaderName::from_static("content-security-policy"),
                HeaderValue::from_static("frame-ancestors 'self'"),
            );
            h.insert(
                header::HeaderName::from_static("x-content-type-options"),
                HeaderValue::from_static("nosniff"),
            );
            res
        }
        Err(_) => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    }
}

pub async fn system_panic_trigger(
    axum::Json(payload): axum::Json<serde_json::Value>,
) -> Response {
    let reason = payload.get("reason").and_then(|v| v.as_str()).unwrap_or("Sovereign security tripwire triggered by frontend enclave");
    crate::anti_tamper::AntiTamper::trigger_fatal_quarantine(reason);
}

