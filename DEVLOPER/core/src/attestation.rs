// [FLOWORKOS:SOVEREIGN-LOCKED] Attestation Guard & Core Ecosystem Integrity Engine
// Guarantees that only genuine, untampered Flowork OS builds can publish to the official public ecosystem.
// Unofficial/modified local builds can freely run skills, plugins, and custom member interfaces,
// but cannot pollute official public stores or registries.

use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlatformChecksums {
    pub binary_sha256: Vec<String>,
    pub auth_html_sha256: Vec<String>,
    pub launcher_html_sha256: Vec<String>,
    pub callback_html_sha256: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReleaseChecksums {
    pub supported_versions: Vec<String>,
    pub linux: PlatformChecksums,
    pub windows: PlatformChecksums,
}

impl Default for ReleaseChecksums {
    fn default() -> Self {
        Self {
            supported_versions: vec!["1.0.0".to_string()],
            linux: PlatformChecksums {
                binary_sha256: vec![
                    "d97f79139fb36ad87122fc131b04fce99474c78f0dfcdc49a5ba1d3f82cdc8f0".to_string(),
                ],
                auth_html_sha256: vec![
                    "647c0f6759ed6c357ca672323aac76985f1bc1150638ec718675dbd96e5c2051".to_string(),
                ],
                launcher_html_sha256: vec![
                    "655adb8e0c15111143aaa017b161af4cb557cde5eb611278bc6d59763ef34d1e".to_string(),
                ],
                callback_html_sha256: vec![
                    "d977a3225f4a72818716909bf1f4852183fc172376a6641aed2f4d669f0305fd".to_string(),
                ],
            },
            windows: PlatformChecksums {
                binary_sha256: vec![
                    "19dca8b830390eac19225a2f1dd130ff1186f33ce713964acacca3861d4b46ad".to_string(),
                ],
                auth_html_sha256: vec![
                    "647c0f6759ed6c357ca672323aac76985f1bc1150638ec718675dbd96e5c2051".to_string(),
                ],
                launcher_html_sha256: vec![
                    "655adb8e0c15111143aaa017b161af4cb557cde5eb611278bc6d59763ef34d1e".to_string(),
                ],
                callback_html_sha256: vec![
                    "d977a3225f4a72818716909bf1f4852183fc172376a6641aed2f4d669f0305fd".to_string(),
                ],
            },
        }
    }
}

pub fn sha256_hex(data: &[u8]) -> String {
    let hash = crate::prompt_seal::sha256(data);
    hash.iter().map(|b| format!("{:02x}", b)).collect()
}

pub fn sha256_normalized_text(text: &str) -> String {
    let normalized = text.replace("\r\n", "\n");
    let trimmed = normalized.trim();
    sha256_hex(trimmed.as_bytes())
}

/// Resolves candidate paths for the protected binary and golden generated UI files.
/// NOTE: member-area/ is intentionally EXEMPT from integrity locks to give users 100% design freedom.
pub fn resolve_core_paths(workspace_root: &Path) -> (Option<PathBuf>, Option<PathBuf>, Option<PathBuf>, Option<PathBuf>) {
    // 1. Binary candidate
    let bin_name = if cfg!(target_os = "windows") { "x-flow.exe" } else { "x-flow" };
    let binary_path = {
        let c1 = workspace_root.join(bin_name);
        if c1.exists() {
            Some(c1)
        } else if let Some(parent) = workspace_root.parent() {
            let c2 = parent.join(bin_name);
            if c2.exists() {
                Some(c2)
            } else {
                std::env::current_exe().ok()
            }
        } else {
            std::env::current_exe().ok()
        }
    };

    // 2. Canvas UI directory
    let mut canvas_dir: Option<PathBuf> = None;
    let candidates = [
        workspace_root.join("canvas-ui"),
        workspace_root.join("xflow").join("canvas-ui"),
    ];
    for c in &candidates {
        if c.exists() && c.is_dir() {
            canvas_dir = Some(c.clone());
            break;
        }
    }
    if canvas_dir.is_none() {
        if let Some(parent) = workspace_root.parent() {
            let p_cand = parent.join("canvas-ui");
            if p_cand.exists() && p_cand.is_dir() {
                canvas_dir = Some(p_cand);
            }
        }
    }

    let auth_path = canvas_dir.as_ref().map(|c| c.join("auth.html")).filter(|p| p.exists());
    let launcher_path = canvas_dir.as_ref().map(|c| c.join("launcher.html")).filter(|p| p.exists());
    let callback_path = canvas_dir.as_ref().and_then(|c| {
        let c1 = c.join("auth").join("flowork-callback.html");
        if c1.exists() { return Some(c1); }
        let c2 = c.join("auth").join("callback.html");
        if c2.exists() { return Some(c2); }
        let c3 = c.join("callback.html");
        if c3.exists() { return Some(c3); }
        None
    });

    (binary_path, auth_path, launcher_path, callback_path)
}

/// Fetches latest checksums from official GitHub repository or uses cached/embedded fallback
pub async fn fetch_or_cached_checksums(workspace_root: &Path) -> ReleaseChecksums {
    let cache_dir = workspace_root.join(".FL_BIN");
    let cache_file = cache_dir.join("release_checksums.json");

    // Check if cache is fresh (< 6 hours)
    if cache_file.exists() {
        if let Ok(metadata) = std::fs::metadata(&cache_file) {
            if let Ok(modified) = metadata.modified() {
                if let Ok(elapsed) = modified.elapsed() {
                    if elapsed.as_secs() < 6 * 3600 {
                        if let Ok(bytes) = std::fs::read(&cache_file) {
                            if let Ok(parsed) = serde_json::from_slice::<ReleaseChecksums>(&bytes) {
                                return parsed;
                            }
                        }
                    }
                }
            }
        }
    }

    // Attempt remote fetch from official repository
    let remote_url = crate::prompt_enclave::PromptEnclave::url_release_checksums();
    let output = tokio::process::Command::new("curl")
        .args(["-s", "-A", "Flowork-Attestation-Guard/1.0", "--max-time", "5", &remote_url])
        .output()
        .await;

    if let Ok(out) = output {
        if out.status.success() {
            if let Ok(parsed) = serde_json::from_slice::<ReleaseChecksums>(&out.stdout) {
                let _ = tokio::fs::create_dir_all(&cache_dir).await;
                let _ = tokio::fs::write(&cache_file, &out.stdout).await;
                return parsed;
            }
        }
    }

    // Fallback to existing stale cache if fetch failed
    if cache_file.exists() {
        if let Ok(bytes) = std::fs::read(&cache_file) {
            if let Ok(parsed) = serde_json::from_slice::<ReleaseChecksums>(&bytes) {
                return parsed;
            }
        }
    }

    // Ultimate fallback: embedded golden checksums
    ReleaseChecksums::default()
}

pub const DEV_MODE_PASSWORD_HASH: &str = "755edcc90dadcf187a487a608ad0d1140bd9313ddc3763c334e52518fddf15b4";

/// Validates whether Developer Mode is activated via dev.flowork or dev.flow with authenticated password.
pub fn is_dev_mode_authenticated(workspace_root: &Path) -> bool {
    let check_file = |path: &Path| -> bool {
        if path.exists() && path.is_file() {
            if let Ok(content) = std::fs::read_to_string(path) {
                let trimmed = content.trim();
                let hash = sha256_hex(trimmed.as_bytes());
                if hash == DEV_MODE_PASSWORD_HASH {
                    return true;
                }
            }
        }
        false
    };

    // 1. Direct workspace_root and candidate paths (prioritize dev.flowork)
    let direct_candidates = [
        workspace_root.join("dev.flowork"),
        workspace_root.join("dev.flow"),
        workspace_root.join("flowork").join("dev.flowork"),
        workspace_root.join("flowork").join("dev.flow"),
        workspace_root.join("portable-home").join("dev.flowork"),
        workspace_root.join("portable-home").join("dev.flow"),
        workspace_root.join("portable-home").join(".flowork").join("dev.flowork"),
        workspace_root.join("portable-home").join(".flowork").join("dev.flow"),
    ];
    for c in &direct_candidates {
        if check_file(c) {
            return true;
        }
    }

    // 2. Current working directory checks (skipped if workspace_root is an isolated temporary directory)
    if !workspace_root.starts_with(std::env::temp_dir()) {
        if let Ok(cur) = std::env::current_dir() {
            let cur_candidates = [
                cur.join("dev.flowork"),
                cur.join("dev.flow"),
                cur.join("flowork").join("dev.flowork"),
                cur.join("flowork").join("dev.flow"),
                cur.join("portable-home").join("dev.flowork"),
                cur.join("portable-home").join(".flowork").join("dev.flowork"),
            ];
            for c in &cur_candidates {
                if check_file(c) {
                    return true;
                }
            }
        }
    }

    // 3. Current executable directory checks
    if let Ok(exe) = std::env::current_exe() {
        if let Some(exe_dir) = exe.parent() {
            let exe_candidates = [
                exe_dir.join("dev.flowork"),
                exe_dir.join("dev.flow"),
                exe_dir.join("portable-home").join("dev.flowork"),
            ];
            for c in &exe_candidates {
                if check_file(c) {
                    return true;
                }
            }
            if let Some(parent) = exe_dir.parent() {
                let parent_exe_candidates = [
                    parent.join("dev.flowork"),
                    parent.join("dev.flow"),
                    parent.join("flowork").join("dev.flowork"),
                    parent.join("flowork").join("dev.flow"),
                ];
                for c in &parent_exe_candidates {
                    if check_file(c) {
                        return true;
                    }
                }
            }
        }
    }

    // 4. Walk up parent hierarchy of workspace_root
    let mut curr = workspace_root.to_path_buf();
    for _ in 0..4 {
        if let Some(parent) = curr.parent() {
            let parent_candidates = [
                parent.join("dev.flowork"),
                parent.join("dev.flow"),
                parent.join("flowork").join("dev.flowork"),
                parent.join("flowork").join("dev.flow"),
            ];
            for c in &parent_candidates {
                if check_file(c) {
                    return true;
                }
            }
            curr = parent.to_path_buf();
        } else {
            break;
        }
    }

    false
}

/// Core Attestation Gate: validates binary and golden UI integrity before permitting public ecosystem operations (upload or download).
/// Users are 100% free to customize member-area/ without triggering any block!
pub async fn verify_integrity_for_ecosystem_gate(workspace_root: &Path, operation: &str) -> Result<(), String> {
    // Multi-Layered Security Gate: Check for authenticated Dev Mode (dev.flowork / dev.flow with secret password)
    if is_dev_mode_authenticated(workspace_root) {
        println!("[Attestation Guard] 🛠️ DEV MODE ACTIVE: Authenticated via dev.flowork/dev.flow. Integrity checksum bypassed for {} (development mode).", operation);
        return Ok(());
    }

    let (bin_path, auth_path, launcher_path, callback_path) = resolve_core_paths(workspace_root);

    let bin_path = bin_path.ok_or_else(|| {
        format!("Attestation Guard: Unable to locate main Flowork execution binary to authorize {operation}.")
    })?;

    // Read and hash binary
    let bin_bytes = tokio::fs::read(&bin_path)
        .await
        .map_err(|e| format!("Attestation Guard: Failed to read binary {}: {e}", bin_path.display()))?;
    let bin_hash = sha256_hex(&bin_bytes);

    let auth_str = if let Some(ref p) = auth_path {
        tokio::fs::read_to_string(p).await.ok()
    } else {
        None
    };

    let launcher_str = if let Some(ref p) = launcher_path {
        tokio::fs::read_to_string(p).await.ok()
    } else {
        None
    };

    let callback_str = if let Some(ref p) = callback_path {
        tokio::fs::read_to_string(p).await.ok()
    } else {
        None
    };

    // Fetch official release checksum matrix
    let checksums = fetch_or_cached_checksums(workspace_root).await;
    let is_windows = cfg!(target_os = "windows");
    let platform_rules = if is_windows { &checksums.windows } else { &checksums.linux };

    let mut violations = Vec::new();

    let bin_matched = platform_rules.binary_sha256.iter().any(|h| h.eq_ignore_ascii_case(&bin_hash));
    if !bin_matched {
        violations.push(format!("Core binary ({}) hash mismatch: {bin_hash}", bin_path.file_name().unwrap_or_default().to_string_lossy()));
    }

    if let Some(auth_text) = auth_str {
        let auth_hash = sha256_normalized_text(&auth_text);
        let auth_matched = platform_rules.auth_html_sha256.iter().any(|h| h.eq_ignore_ascii_case(&auth_hash));
        if !auth_matched {
            violations.push(format!("Authentication interface (canvas-ui/auth.html) modified (hash: {auth_hash})"));
        }
    }

    if let Some(launcher_text) = launcher_str {
        let launcher_hash = sha256_normalized_text(&launcher_text);
        let launcher_matched = platform_rules.launcher_html_sha256.iter().any(|h| h.eq_ignore_ascii_case(&launcher_hash));
        if !launcher_matched {
            violations.push(format!("Welcome/Launcher interface (canvas-ui/launcher.html) modified (hash: {launcher_hash})"));
        }
    }

    if let Some(callback_text) = callback_str {
        let callback_hash = sha256_normalized_text(&callback_text);
        let callback_matched = platform_rules.callback_html_sha256.iter().any(|h| h.eq_ignore_ascii_case(&callback_hash));
        if !callback_matched {
            violations.push(format!("Authentication callback interface modified (hash: {callback_hash})"));
        }
    }

    if !violations.is_empty() {
        let violations_detail = violations.join("\n  • ");
        return Err(format!(
            "[Flowork Attestation Guard] 🛑 Official ecosystem {} is restricted to verified, untampered Flowork OS builds.\nCore modifications detected:\n  • {}\nLocal development, custom member workspaces, plugins, and private skills remain completely unrestricted on this machine. (To bypass in development, provide authenticated flowork/dev.flow).",
            operation, violations_detail
        ));
    }

    println!("[Attestation Guard] ✅ Core integrity verified for {operation}. Binary and UI match official Flowork OS release.");
    Ok(())
}

/// Core Attestation Gate for publishing/uploading to the official public ecosystem.
pub async fn verify_integrity_for_publish(workspace_root: &Path) -> Result<(), String> {
    verify_integrity_for_ecosystem_gate(workspace_root, "upload/publish").await
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_text_normalization_crlf_and_lf() {
        let text_lf = "<html>\n<body>\n<h1>Flowork OS</h1>\n</body>\n</html>\n";
        let text_crlf = "<html>\r\n<body>\r\n<h1>Flowork OS</h1>\r\n</body>\r\n</html>\r\n";
        assert_eq!(sha256_normalized_text(text_lf), sha256_normalized_text(text_crlf));
    }

    #[tokio::test]
    async fn test_attestation_blocks_tampered_auth_ui() {
        let temp_dir = std::env::temp_dir().join(format!("xflow_attest_test2_{}", std::process::id()));
        let canvas_dir = temp_dir.join("canvas-ui");
        let _ = std::fs::create_dir_all(&canvas_dir);

        // Dummy binary
        let bin_name = if cfg!(target_os = "windows") { "x-flow.exe" } else { "x-flow" };
        let _ = std::fs::write(temp_dir.join(bin_name), b"fake binary content");

        // Tampered auth.html
        let _ = std::fs::write(canvas_dir.join("auth.html"), b"<html>TAMPERED AUTH PAGE</html>");
        let _ = std::fs::write(canvas_dir.join("launcher.html"), b"<html>LAUNCHER</html>");
        let _ = std::fs::write(canvas_dir.join("callback.html"), b"<html>CALLBACK</html>");

        let res = verify_integrity_for_publish(&temp_dir).await;
        assert!(res.is_err());
        let err_msg = res.unwrap_err();
        assert!(err_msg.contains("[Flowork Attestation Guard]"));
        assert!(err_msg.contains("Core modifications detected"));

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[tokio::test]
    async fn test_real_workspace_verification() {
        let manifest_dir = std::path::PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string()));
        let candidates = [
            manifest_dir.join("..").join("FLOWORK"),
            manifest_dir.join("..").join("..").join("FLOWORK"),
            manifest_dir.join("..").join("xflow"),
        ];
        let mut ws = None;
        for c in &candidates {
            if c.join("canvas-ui").join("auth.html").exists() {
                ws = Some(c.clone());
                break;
            }
        }
        let ws = match ws {
            Some(w) => w,
            None => {
                println!("Skipping real workspace verification: canvas-ui/auth.html not found on this host");
                return;
            }
        };
        let res = verify_integrity_for_publish(&ws).await;
        println!("Real Linux workspace verification result: {:?}", res);
        assert!(res.is_ok(), "Expected Linux workspace to pass integrity verification: {:?}", res.err());
    }

    #[tokio::test]
    async fn test_dev_mode_bypass_when_dev_flow_authenticated() {
        let temp_dir = std::env::temp_dir().join(format!("xflow_dev_mode_ok_{}", std::process::id()));
        let flowork_dir = temp_dir.join("flowork");
        let canvas_dir = temp_dir.join("canvas-ui");
        let _ = std::fs::create_dir_all(&flowork_dir);
        let _ = std::fs::create_dir_all(&canvas_dir);

        // Put dev.flowork with valid password in temp_dir root
        let _ = std::fs::write(temp_dir.join("dev.flowork"), "Aola-#1987\n");

        // Tampered auth page that would normally fail attestation
        let bin_name = if cfg!(target_os = "windows") { "x-flow.exe" } else { "x-flow" };
        let _ = std::fs::write(temp_dir.join(bin_name), b"fake binary content");
        let _ = std::fs::write(canvas_dir.join("auth.html"), b"<html>TAMPERED AUTH PAGE</html>");
        let _ = std::fs::write(canvas_dir.join("launcher.html"), b"<html>LAUNCHER</html>");
        let _ = std::fs::write(canvas_dir.join("callback.html"), b"<html>CALLBACK</html>");

        assert!(is_dev_mode_authenticated(&temp_dir));
        let res = verify_integrity_for_publish(&temp_dir).await;
        assert!(res.is_ok(), "Dev mode via dev.flowork should bypass integrity check: {:?}", res.err());

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[tokio::test]
    async fn test_dev_mode_rejected_when_dev_flow_wrong_password() {
        let temp_dir = std::env::temp_dir().join(format!("xflow_dev_mode_err_{}", std::process::id()));
        let flowork_dir = temp_dir.join("flowork");
        let canvas_dir = temp_dir.join("canvas-ui");
        let _ = std::fs::create_dir_all(&flowork_dir);
        let _ = std::fs::create_dir_all(&canvas_dir);

        // Put dev.flow with WRONG password
        let _ = std::fs::write(flowork_dir.join("dev.flow"), "WrongPassword123\n");

        // Tampered auth page
        let bin_name = if cfg!(target_os = "windows") { "x-flow.exe" } else { "x-flow" };
        let _ = std::fs::write(temp_dir.join(bin_name), b"fake binary content");
        let _ = std::fs::write(canvas_dir.join("auth.html"), b"<html>TAMPERED AUTH PAGE</html>");
        let _ = std::fs::write(canvas_dir.join("launcher.html"), b"<html>LAUNCHER</html>");
        let _ = std::fs::write(canvas_dir.join("callback.html"), b"<html>CALLBACK</html>");

        assert!(!is_dev_mode_authenticated(&temp_dir));
        let res = verify_integrity_for_publish(&temp_dir).await;
        assert!(res.is_err(), "Wrong password in dev.flow must NOT bypass attestation");

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[tokio::test]
    async fn test_ecosystem_gate_download_and_upload_blocked_when_tampered() {
        let temp_dir = std::env::temp_dir().join(format!("xflow_gate_test_{}", std::process::id()));
        let canvas_dir = temp_dir.join("canvas-ui");
        let _ = std::fs::create_dir_all(&canvas_dir);

        let bin_name = if cfg!(target_os = "windows") { "x-flow.exe" } else { "x-flow" };
        let _ = std::fs::write(temp_dir.join(bin_name), b"fake binary content");
        let _ = std::fs::write(canvas_dir.join("auth.html"), b"<html>TAMPERED AUTH PAGE</html>");
        let _ = std::fs::write(canvas_dir.join("launcher.html"), b"<html>LAUNCHER</html>");
        let _ = std::fs::write(canvas_dir.join("callback.html"), b"<html>CALLBACK</html>");

        // Test download blocked
        let res_down = verify_integrity_for_ecosystem_gate(&temp_dir, "download/install").await;
        assert!(res_down.is_err(), "Download must be blocked when core is tampered");
        assert!(res_down.unwrap_err().contains("download/install"));

        // Test upload blocked
        let res_up = verify_integrity_for_ecosystem_gate(&temp_dir, "upload/publish").await;
        assert!(res_up.is_err(), "Upload must be blocked when core is tampered");
        assert!(res_up.unwrap_err().contains("upload/publish"));

        // Add valid dev.flow and verify both unblock
        let flowork_dir = temp_dir.join("flowork");
        let _ = std::fs::create_dir_all(&flowork_dir);
        let _ = std::fs::write(flowork_dir.join("dev.flow"), "Aola-#1987\n");

        let res_down_dev = verify_integrity_for_ecosystem_gate(&temp_dir, "download/install").await;
        assert!(res_down_dev.is_ok(), "Download must be permitted when dev.flow is authenticated");

        let res_up_dev = verify_integrity_for_ecosystem_gate(&temp_dir, "upload/publish").await;
        assert!(res_up_dev.is_ok(), "Upload must be permitted when dev.flow is authenticated");

        let _ = std::fs::remove_dir_all(&temp_dir);
    }
}
