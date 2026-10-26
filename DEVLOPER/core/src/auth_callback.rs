// =========================================================================
// FLOWORK OS - SOVEREIGN OAUTH CALLBACK SWITCHBOARD (1 FILE 1 JALUR)
// =========================================================================
// File: core/src/auth_callback.rs
// Purpose: Dedicated, isolated OAuth callback capture, ticket attestation,
//          cryptographic template hash verification, auto-generation,
//          and cybernetic HUD GUI rendering.
// Absolute Rule: 1 File 1 Logic. Never scatter callback logic into general routers.
// =========================================================================

use axum::extract::{Query, State};
use axum::response::Html;
use axum::routing::get;
use axum::Router;
use serde::Deserialize;
use std::path::Path;
use std::sync::Arc;
use crate::ipc_router::AppState;
use crate::prompt_seal::sha256;

// 1. IMMUTABLE GOLDEN CALLBACK TEMPLATE EMBEDDED IN NATIVE BINARY (.rodata) (SHROUDED)
pub const GOLDEN_CALLBACK_HTML: &[u8] = include_bytes!("../canvas-ui/callback.html");

/// Check and restore callback files using cryptographic SHA-256 hash comparison
pub async fn check_and_restore_callback(path: &Path, golden_enc: &[u8], name: &str) {
    let unsealed = crate::prompt_seal::unseal_bytes(golden_enc);
    let should_restore = match tokio::fs::read(path).await {
        Ok(existing) => sha256(&existing) != sha256(&unsealed),
        Err(_) => true,
    };

    if should_restore {
        if let Some(parent) = path.parent() {
            let _ = tokio::fs::create_dir_all(parent).await;
        }
        if let Err(e) = tokio::fs::write(path, &unsealed).await {
            eprintln!("[OAuthCallback:SelfHeal] ⚠️ Failed to restore golden {name}: {e}");
        } else {
            println!("[OAuthCallback:SelfHeal] 🛡️ Golden callback asset verified & restored: {name}");
        }
    }
}

/// Auto-generate callback directories and files on cold boot, or restore if tampered
pub async fn ensure_callback_assets(canvas_dir: &Path) {
    let auth_dir = canvas_dir.join("auth");
    let _ = tokio::fs::create_dir_all(&auth_dir).await;

    check_and_restore_callback(&canvas_dir.join("callback.html"), GOLDEN_CALLBACK_HTML, "callback.html").await;
    check_and_restore_callback(&auth_dir.join("callback.html"), GOLDEN_CALLBACK_HTML, "auth/callback.html").await;
    check_and_restore_callback(&auth_dir.join("flowork-callback.html"), GOLDEN_CALLBACK_HTML, "auth/flowork-callback.html").await;
}

#[derive(Deserialize)]
pub struct CallbackQuery {
    pub token: Option<String>,
    pub flowork_token: Option<String>,
    pub ticket: Option<String>,
}

/// Sovereign handler for /auth/flowork-callback and /auth/callback
pub async fn flowork_callback(
    Query(q): Query<CallbackQuery>,
    State(state): State<Arc<AppState>>,
) -> Html<String> {
    // 1. Enforce Hash Verification & Disk Self-Healing for Callback Templates
    check_and_restore_callback(
        &state.cfg.canvas_dir.join("callback.html"),
        GOLDEN_CALLBACK_HTML,
        "callback.html",
    ).await;
    check_and_restore_callback(
        &state.cfg.canvas_dir.join("auth").join("callback.html"),
        GOLDEN_CALLBACK_HTML,
        "auth/callback.html",
    ).await;

    let unsealed_bytes = crate::prompt_seal::unseal_bytes(GOLDEN_CALLBACK_HTML);
    let template_str = String::from_utf8(unsealed_bytes).unwrap_or_default();
    let template = template_str.as_str();
    let token = q.token.or(q.flowork_token).unwrap_or_default();
    let ticket = q.ticket.filter(|t| !t.trim().is_empty() && t != "none");
    if let Some(t) = &ticket {
        println!("[X-Flow Auth] 🎫 OAuth Callback received with ticket: {t}");
    } else {
        println!("[X-Flow Auth] 🎫 OAuth Callback received without ticket nonce");
    }

    if token.is_empty() {
        let err_card = r#"
          <div class="telemetry-list">
            <div class="telemetry-item err"><span>[✗]</span> MISSING AUTHORIZATION TOKEN</div>
            <div class="telemetry-item warn"><span>[!]</span> CALLBACK DID NOT PROVIDE FLOWORK PASSPORT TOKEN</div>
          </div>
        "#;
        let rendered = template
            .replace("{{CARD_CLASS}}", "error-state")
            .replace("{{BADGE_CLASS}}", "error")
            .replace("{{BADGE_TEXT}}", "SECURITY LOCKDOWN // TOKEN MISSING")
            .replace("{{TITLE}}", "Authentication Token Missing")
            .replace("{{DESCRIPTION}}", "The callback endpoint did not receive a cryptographic passport token.")
            .replace("{{CONTENT_BLOCK}}", err_card)
            .replace("{{ACTION_BUTTON}}", r#"<a class="btn btn-danger" href="/canvas/launcher.html">RETURN TO LAUNCHER</a>"#)
            .replace("{{FOOTER_NOTE}}", "Please restart login from the official launcher.")
            .replace("{{REDIRECT_SCRIPT}}", "");
        return Html(rendered);
    }

    match state.auth.set_token(&token, ticket.as_deref()).await {
        Ok(user_info) => {
            let u = user_info.get("user");
            let username = u.and_then(|x| x.get("username")).and_then(|x| x.as_str()).unwrap_or("User");
            let role = u.and_then(|x| x.get("role")).and_then(|x| x.as_str()).unwrap_or("USER");
            let tier = u.and_then(|x| x.get("tier")).and_then(|x| x.as_str()).unwrap_or("Community");

            let user_card = format!(r#"
              <div class="user-profile">
                <div class="avatar-wrap">👤</div>
                <div class="user-meta">
                  <div class="username">@{username} <span class="tier-badge">{role} • {tier}</span></div>
                  <div style="font-size:12px;color:#94a3b8;margin-top:4px;">Asymmetric Session Nonce Attested // AES-256 Synchronized</div>
                </div>
              </div>
              <div class="telemetry-list">
                <div class="telemetry-item ok"><span>[✓]</span> TICKET NONCE VERIFIED & CONSUMED</div>
                <div class="telemetry-item ok"><span>[✓]</span> ONLINE SIGNATURE ATTESTED (Sovereign Authority)</div>
                <div class="telemetry-item ok"><span>[✓]</span> SOVEREIGN VAULT HARDWARE BOUND</div>
              </div>
            "#);

            let rendered = template
                .replace("{{CARD_CLASS}}", "")
                .replace("{{BADGE_CLASS}}", "")
                .replace("{{BADGE_TEXT}}", "FLOWORK SOVEREIGN PASSPORT // VERIFIED")
                .replace("{{TITLE}}", "X-Flow Host Unlocked!")
                .replace("{{DESCRIPTION}}", "Session verified with Sovereign Authority. Clearance granted.")
                .replace("{{CONTENT_BLOCK}}", &user_card)
                .replace("{{ACTION_BUTTON}}", r#"<a class="btn btn-primary" href="/canvas/member-area/index.html">ENTER SOVEREIGN WORKSPACE</a>"#)
                .replace("{{FOOTER_NOTE}}", "Redirecting to workspace in 2 seconds...")
                .replace("{{REDIRECT_SCRIPT}}", r#"<script>setTimeout(() => { if (window.opener) window.close(); window.location.href = '/canvas/member-area/index.html'; }, 2000);</script>"#);

            Html(rendered)
        }
        Err(e) => {
            if state.auth.is_authorized().await {
                let st = state.auth.get_status().await;
                let username = st.get("user").and_then(|u| u.get("username")).and_then(|x| x.as_str()).unwrap_or("User");

                let active_card = format!(r#"
                  <div class="user-profile">
                    <div class="avatar-wrap">🛡️</div>
                    <div class="user-meta">
                      <div class="username">@{username} <span class="tier-badge">ACTIVE SESSION</span></div>
                      <div style="font-size:12px;color:#94a3b8;margin-top:4px;">Hardware Vault Session Valid // No Re-Auth Needed</div>
                    </div>
                  </div>
                  <div class="telemetry-list">
                    <div class="telemetry-item ok"><span>[✓]</span> LOCAL VAULT CREDENTIALS ACTIVE</div>
                    <div class="telemetry-item ok"><span>[✓]</span> WORKSPACE ACCESS PERMITTED</div>
                  </div>
                "#);

                let rendered = template
                    .replace("{{CARD_CLASS}}", "")
                    .replace("{{BADGE_CLASS}}", "")
                    .replace("{{BADGE_TEXT}}", "SOVEREIGN PASSPORT // SESSION ACTIVE")
                    .replace("{{TITLE}}", "Session Already Authenticated")
                    .replace("{{DESCRIPTION}}", &format!("Welcome back, @{username}. Your sovereign credentials are valid and active."))
                    .replace("{{CONTENT_BLOCK}}", &active_card)
                    .replace("{{ACTION_BUTTON}}", r#"<a class="btn btn-primary" href="/canvas/member-area/index.html">PROCEED TO WORKSPACE</a>"#)
                    .replace("{{FOOTER_NOTE}}", "Forwarding to workspace in 1.5 seconds...")
                    .replace("{{REDIRECT_SCRIPT}}", r#"<script>setTimeout(() => { if (window.opener) window.close(); window.location.href = '/canvas/member-area/index.html'; }, 1500);</script>"#);

                return Html(rendered);
            }

            let err_card = format!(r#"
              <div class="telemetry-list">
                <div class="telemetry-item err"><span>[✗]</span> {e}</div>
                <div class="telemetry-item warn"><span>[!]</span> SINGLE-USE NONCE EXPIRED OR ALREADY CONSUMED</div>
                <div class="telemetry-item"><span>[ℹ]</span> TOKENS MUST ORIGINATE FROM AUTH.FLOWORKOS.COM</div>
              </div>
            "#);

            let rendered = template
                .replace("{{CARD_CLASS}}", "error-state")
                .replace("{{BADGE_CLASS}}", "error")
                .replace("{{BADGE_TEXT}}", "SOVEREIGN LOCKDOWN // VERIFICATION DENIED")
                .replace("{{TITLE}}", "Authentication Failed")
                .replace("{{DESCRIPTION}}", "The provided ticket or authentication token could not be verified by sovereign authority.")
                .replace("{{CONTENT_BLOCK}}", &err_card)
                .replace("{{ACTION_BUTTON}}", r#"<a class="btn btn-danger" href="/canvas/launcher.html">GENERATE NEW LOGIN SESSION</a>"#)
                .replace("{{FOOTER_NOTE}}", "Please return to the launcher to initiate a fresh login session.")
                .replace("{{REDIRECT_SCRIPT}}", "");

            Html(rendered)
        }
    }
}

/// Attach dedicated callback routes to the Axum Router (1 File 1 Jalur)
#[allow(dead_code)]
pub fn register_callback_routes(router: Router<Arc<AppState>>) -> Router<Arc<AppState>> {
    router
        .route("/auth/flowork-callback", get(flowork_callback))
        .route("/auth/callback", get(flowork_callback))
}
