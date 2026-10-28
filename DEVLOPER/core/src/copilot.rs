use serde_json::{json, Value};
use std::path::PathBuf;
use tokio::process::Command;

pub struct CopilotManager {
    _root_dir: PathBuf,
    plugins_dir: PathBuf,
}

impl CopilotManager {
    pub fn new(root_dir: PathBuf, plugins_dir: PathBuf) -> Self {
        Self { _root_dir: root_dir, plugins_dir }
    }

    pub fn target_repo_for_os(_target_os: &str) -> &'static str {
        "apps"
    }

    pub fn target_repo() -> &'static str {
        "apps"
    }

    #[allow(dead_code)]
    pub async fn get_registry(&self) -> Result<Value, String> {
        self.get_registry_for_os(None).await
    }

    pub async fn get_registry_for_os(&self, req_os: Option<&str>) -> Result<Value, String> {
        let target_os = match req_os {
            Some(o) if o.eq_ignore_ascii_case("windows") => "windows",
            Some(o) if o.eq_ignore_ascii_case("linux") => "linux",
            _ => {
                if cfg!(target_os = "windows") {
                    "windows"
                } else {
                    "linux"
                }
            }
        };
        let repo = Self::target_repo_for_os(target_os);
        let cache_path = self.plugins_dir.join(format!(".registry_cache_{target_os}.json"));

        // 1. Fetch live authoritative App Store catalog from Cloudflare Edge (auth.floworkos.com)
        let mut fetched_reg: Option<(Value, String)> = None;
        let edge_url = format!("{}/api/store/catalog", crate::prompt_enclave::PromptEnclave::url_auth());
        let edge_out = Command::new("curl")
            .args([
                "-sL",
                "-A", "FloworkOS-Client/1.0",
                "-H", "Cache-Control: no-cache, no-store",
                "-H", "Pragma: no-cache",
                "--max-time", "8",
                &edge_url
            ])
            .output()
            .await;

        if let Ok(o) = edge_out {
            if o.status.success() {
                let reg_str = String::from_utf8_lossy(&o.stdout);
                if let Ok(val) = serde_json::from_str::<Value>(&reg_str) {
                    if val.get("apps").is_some() || val.get("plugins").is_some() {
                        let _ = std::fs::write(&cache_path, reg_str.as_bytes());
                        // SELF-HEALING: Overwrite local apps.json so any unauthorized local modifications are immediately reverted back
                        let master_apps = self.plugins_dir.join("apps.json");
                        let _ = std::fs::write(&master_apps, reg_str.as_bytes());
                        fetched_reg = Some((val, "live_cloudflare_edge".to_string()));
                    }
                }
            }
        }

        // 1.2. Fallback to unified GitHub repo
        if fetched_reg.is_none() {
            let base_raw = crate::prompt_enclave::PromptEnclave::url_github_raw_base();
            let base_trimmed = base_raw.trim_end_matches('/');
            let reg_url = format!("{base_trimmed}/{repo}/main/apps.json");

            let out = Command::new("curl")
                .args([
                    "-sL", // Follow HTTP 301/302/307 redirects from GitHub raw CDN
                    "-A", "FloworkOS-Client/1.0",
                    "-H", "Cache-Control: no-cache, no-store",
                    "-H", "Pragma: no-cache",
                    "--max-time", "10",
                    &reg_url
                ])
                .output()
                .await;

            if let Ok(o) = out {
                if o.status.success() {
                    let reg_str = String::from_utf8_lossy(&o.stdout);
                    if let Ok(val) = serde_json::from_str::<Value>(&reg_str) {
                        if val.get("apps").is_some() || val.get("plugins").is_some() {
                            let _ = std::fs::write(&cache_path, reg_str.as_bytes());
                            let master_apps = self.plugins_dir.join("apps.json");
                            let _ = std::fs::write(&master_apps, reg_str.as_bytes());
                            fetched_reg = Some((val, "live_github".to_string()));
                        }
                    }
                }
            }
        }

        // 1.5. Local Unified Repo fallback (for local development or pre-release before remote git push)
        if fetched_reg.is_none() {
            let candidates = [
                self.plugins_dir.join("apps.json"),
                self.plugins_dir.join("plugins.json"),
                self._root_dir.join("apps").join("apps.json"),
                self._root_dir.join("apps").join("plugins.json"),
                self._root_dir.join("plugins").join("plugins.json"),
            ];
            for candidate in &candidates {
                if candidate.exists() {
                    if let Ok(reg_str) = std::fs::read_to_string(candidate) {
                        if let Ok(val) = serde_json::from_str::<Value>(&reg_str) {
                            if val.get("apps").is_some() || val.get("plugins").is_some() {
                                let _ = std::fs::write(&cache_path, reg_str.as_bytes());
                                fetched_reg = Some((val, "local_unified_repo".to_string()));
                                break;
                            }
                        }
                    }
                }
            }
        }

        // 2. Resolve registry from GitHub, Cache, or Sovereign Default
        let (mut reg, commit_sha) = if let Some((v, s)) = fetched_reg {
            (v, s)
        } else if let Ok(cache_str) = std::fs::read_to_string(&cache_path) {
            let v = serde_json::from_str::<Value>(&cache_str).unwrap_or_else(|_| Self::default_registry_for_os(target_os));
            (v, "cached".to_string())
        } else {
            (Self::default_registry_for_os(target_os), "sovereign".to_string())
        };

        // 3. Mark installed status for each plugin in the registry
        if let Some(plugins) = reg.get_mut("plugins").and_then(|p| p.as_array_mut()) {
            for p in plugins.iter_mut() {
                if let Some(id) = p.get("id").and_then(|i| i.as_str()) {
                    let local_dir = self.plugins_dir.join(id);
                    let installed = local_dir.exists() && (local_dir.join("plugin.manifest.json").exists() || local_dir.join("manifest.json").exists() || local_dir.join("app.manifest.json").exists());
                    let local_hash = std::fs::read_to_string(local_dir.join(".plugin_hash")).unwrap_or_default().trim().to_string();
                    let remote_hash = p.get("hash").and_then(|h| h.as_str()).unwrap_or("");
                    let update_available = installed && !local_hash.is_empty() && local_hash != remote_hash;

                    p["installed"] = json!(installed);
                    p["local_hash"] = json!(local_hash);
                    p["update_available"] = json!(update_available);
                }
            }
        }

        let repo_base = crate::prompt_enclave::PromptEnclave::url_github_flowork_base();
        let repo_base_trimmed = repo_base.trim_end_matches('/');
        let repo_url = format!("{repo_base_trimmed}/{repo}");
        reg["repo"] = json!(format!("flowork-os/{repo}"));
        reg["repo_name"] = json!(format!("flowork-os/{repo}"));
        reg["repo_url"] = json!(repo_url);
        reg["target_os"] = json!(target_os);
        reg["commit_sha"] = json!(commit_sha);
        Ok(reg)
    }

    #[allow(dead_code)]
    pub fn default_registry() -> Value {
        let target_os = if cfg!(target_os = "windows") { "windows" } else { "linux" };
        Self::default_registry_for_os(target_os)
    }

    pub fn default_registry_for_os(target_os: &str) -> Value {
        let repo = Self::target_repo_for_os(target_os);
        let repo_base = crate::prompt_enclave::PromptEnclave::url_github_flowork_base();
        let repo_base_trimmed = repo_base.trim_end_matches('/');
        json!({
            "version": "2.0.0",
            "repo": format!("flowork-os/{repo}"),
            "repo_name": format!("flowork-os/{repo}"),
            "repo_url": format!("{repo_base_trimmed}/{repo}"),
            "target_os": target_os,
            "plugins": [
                {
                    "id": "chess",
                    "name": "Sovereign Chess Arena",
                    "version": "1.0.0",
                    "author": "Flowork OS",
                    "description": "Dual-Actor Chess Arena: Human vs Agent AI. Play solo or duel with open Agent chat in real-time.",
                    "category": "Games & Strategy",
                    "icon": "♟️",
                    "hash": "8b16a3add0db016d",
                    "source_path": "plugins/ch/chess"
                },
                {
                    "id": "yt-downloader",
                    "name": "YouTube Downloader & Suno Studio",
                    "version": "1.2.0",
                    "author": "Flowork OS",
                    "description": "Sovereign High-Speed YouTube Audio/Video Extractor & DSP Processor — 59s Anti-Copyright Speed Ramp for Suno AI, Custom Folders, and Multi-Format Audio/Video Export.",
                    "category": "Media & Network",
                    "icon": "📹",
                    "hash": "9dd08b12db5ad295",
                    "source_path": "plugins/yt/yt-downloader"
                }
            ]
        })
    }

    async fn try_tar_extract(tarball_url: &str, target_dir: &std::path::Path, pattern: &str, strip_components: usize) -> bool {
        let shell_cmd = format!(
            "curl -sL --max-time 60 '{}' | tar -xz -C '{}' --strip-components={} '{}' 2>/dev/null",
            tarball_url,
            target_dir.display(),
            strip_components,
            pattern
        );

        let out = if cfg!(target_os = "windows") {
            let win_cmd = format!(
                "curl.exe -sL --max-time 60 \"{}\" | tar.exe -xz -C \"{}\" --strip-components={} \"{}\"",
                tarball_url,
                target_dir.display(),
                strip_components,
                pattern
            );
            Command::new("cmd").args(["/C", &win_cmd]).output().await
        } else {
            Command::new("sh").args(["-c", &shell_cmd]).output().await
        };

        match out {
            Ok(res) => res.status.success(),
            Err(_) => false,
        }
    }

    fn copy_dir_all(src: &std::path::Path, dst: &std::path::Path) -> std::io::Result<()> {
        std::fs::create_dir_all(dst)?;
        for entry in std::fs::read_dir(src)? {
            let entry = entry?;
            let entry_path = entry.path();
            let target_path = dst.join(entry.file_name());
            if entry_path.is_dir() {
                Self::copy_dir_all(&entry_path, &target_path)?;
            } else {
                std::fs::copy(&entry_path, &target_path)?;
            }
        }
        Ok(())
    }

    #[allow(dead_code)]
    pub async fn install_plugin(&self, plugin_id: &str) -> Result<String, String> {
        self.install_plugin_for_os(plugin_id, None).await
    }

    pub async fn install_plugin_for_os(&self, plugin_id: &str, req_os: Option<&str>) -> Result<String, String> {
        let clean_id = plugin_id.trim();
        if clean_id.is_empty() {
            return Err("Missing required argument 'plugin_id'".to_string());
        }

        if !clean_id.chars().all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_') {
            return Err(format!("Invalid plugin_id '{clean_id}'. Alphanumeric, hyphens, and underscores only."));
        }

        let repo = match req_os {
            Some(o) => Self::target_repo_for_os(o),
            None => Self::target_repo(),
        };
        let final_plugin_dir = self.plugins_dir.join(clean_id);
        let _ = tokio::fs::create_dir_all(&final_plugin_dir).await;

        let base_codeload = crate::prompt_enclave::PromptEnclave::url_github_codeload_base();
        let codeload_trimmed = base_codeload.trim_end_matches('/');
        let tarball_url = format!("{codeload_trimmed}/{repo}/tar.gz/refs/heads/main");
        let prefix = crate::tools::safe_truncate_str(clean_id, 2);
        let sharded_pattern = format!("{repo}-main/plugins/{prefix}/{clean_id}");
        let legacy_pattern = format!("{repo}-main/{clean_id}");

        // Attempt 1: Sharded repository path (plugins/{prefix}/{clean_id}) with strip-components=4
        let _ = Self::try_tar_extract(&tarball_url, &final_plugin_dir, &sharded_pattern, 4).await;
        let mut manifest_exists = final_plugin_dir.join("plugin.manifest.json").exists()
            || final_plugin_dir.join("manifest.json").exists()
            || final_plugin_dir.join("app.manifest.json").exists();

        if manifest_exists {
            return Ok(format!("Successfully installed plugin '{clean_id}' from flowork-os/{repo} via Public Codeload CDN (Sharded Path)."));
        }

        // Attempt 2: Fallback to root legacy path ({clean_id}) with strip-components=2
        let _ = Self::try_tar_extract(&tarball_url, &final_plugin_dir, &legacy_pattern, 2).await;
        manifest_exists = final_plugin_dir.join("plugin.manifest.json").exists()
            || final_plugin_dir.join("manifest.json").exists()
            || final_plugin_dir.join("app.manifest.json").exists();

        if manifest_exists {
            return Ok(format!("Successfully installed plugin '{clean_id}' from flowork-os/{repo} via Public Codeload CDN (Legacy Path)."));
        }

        // Attempt 3: Local Sovereign Repository Fallback (Dynamic Multi-OS)
        let local_candidates = [
            self.plugins_dir.join(&clean_id),
            self._root_dir.join("apps").join(&clean_id),
            self._root_dir.join("apps").join(prefix).join(&clean_id),
            self._root_dir.join("plugins").join(prefix).join(&clean_id),
        ];
        for local_src in &local_candidates {
            if local_src.exists() && (local_src.join("plugin.manifest.json").exists() || local_src.join("manifest.json").exists() || local_src.join("app.manifest.json").exists()) {
                if Self::copy_dir_all(local_src, &final_plugin_dir).is_ok() && (final_plugin_dir.join("plugin.manifest.json").exists() || final_plugin_dir.join("manifest.json").exists() || final_plugin_dir.join("app.manifest.json").exists()) {
                    return Ok(format!("Successfully installed plugin '{clean_id}' from sovereign local repository ({local_src:?})."));
                }
            }
        }

        let _ = tokio::fs::remove_dir_all(&final_plugin_dir).await;
        Err(format!("Plugin '{clean_id}' not found in remote repository '{repo}' (neither sharded nor root)."))
    }

    pub async fn uninstall_plugin(&self, plugin_id: &str) -> Result<bool, String> {
        let target = self.plugins_dir.join(plugin_id);
        if !target.exists() {
            return Ok(false);
        }
        tokio::fs::remove_dir_all(&target).await
            .map_err(|e| format!("Delete error: {e}"))?;
        Ok(true)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_copilot_registry_zero_token() {
        let temp_dir = std::env::temp_dir().join(format!("copilot_test_{}", std::process::id()));
        let plugins_dir = temp_dir.join("plugins");
        let _ = tokio::fs::create_dir_all(&plugins_dir).await;

        let mgr = CopilotManager::new(temp_dir.clone(), plugins_dir);
        let reg = mgr.get_registry().await.expect("Registry should resolve without token");

        assert!(reg.get("plugins").is_some());
        let list = reg["plugins"].as_array().expect("plugins must be array");
        assert!(!list.is_empty(), "Plugins list should not be empty");

        // Verify whale-radar is present in Linux registry when live github is accessible
        if reg.get("commit_sha").and_then(|s| s.as_str()) == Some("live_github") {
            let has_whale = list.iter().any(|p| p.get("id").and_then(|i| i.as_str()) == Some("whale-radar"));
            assert!(has_whale, "Live Linux registry must contain whale-radar plugin");
        }

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_copilot_registry_multi_os_selection() {
        let temp_dir = std::env::temp_dir().join(format!("copilot_os_test_{}", std::process::id()));
        let plugins_dir = temp_dir.join("plugins");
        let _ = tokio::fs::create_dir_all(&plugins_dir).await;

        let mgr = CopilotManager::new(temp_dir.clone(), plugins_dir);
        let linux_reg = mgr.get_registry_for_os(Some("linux")).await.expect("Linux registry should resolve");
        assert_eq!(linux_reg.get("target_os").and_then(|s| s.as_str()), Some("linux"));
        assert_eq!(linux_reg.get("repo").and_then(|s| s.as_str()), Some("flowork-os/apps"));

        let win_reg = mgr.get_registry_for_os(Some("windows")).await.expect("Windows registry should resolve");
        assert_eq!(win_reg.get("target_os").and_then(|s| s.as_str()), Some("windows"));
        assert_eq!(win_reg.get("repo").and_then(|s| s.as_str()), Some("flowork-os/apps"));

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    #[ignore = "Live integration test requiring remote plugins server"]
    async fn test_copilot_install_plugin_sharded() {
        let temp_dir = std::env::temp_dir().join(format!("copilot_install_test_{}", std::process::id()));
        let plugins_dir = temp_dir.join("plugins");
        let _ = tokio::fs::create_dir_all(&plugins_dir).await;

        let mgr = CopilotManager::new(temp_dir.clone(), plugins_dir.clone());
        let res = mgr.install_plugin("chess").await;
        assert!(res.is_ok(), "Installation of chess from sharded repo should succeed: {:?}", res.err());

        let chess_dir = plugins_dir.join("chess");
        assert!(chess_dir.exists(), "chess plugin directory must exist");
        assert!(chess_dir.join("plugin.manifest.json").exists(), "plugin.manifest.json must exist");

        let uninst = mgr.uninstall_plugin("chess").await;
        assert!(uninst.is_ok() && uninst.unwrap());

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }
}
