use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::RwLock;

pub fn get_gdrive_client_id() -> String {
    if let Ok(id) = std::env::var("FLOWORK_GDRIVE_CLIENT_ID") {
        let trimmed = id.trim();
        if !trimmed.is_empty() {
            return trimmed.to_string();
        }
    }
    let p_home = std::env::var("FLOWORK_PORTABLE_ROOT").unwrap_or_else(|_| "portable-home".to_string());
    let id_path = std::path::Path::new(&p_home).join(".flowork").join("gdrive_client_id");
    if id_path.exists() {
        if let Ok(content) = std::fs::read_to_string(id_path) {
            let trimmed = content.trim();
            if !trimmed.is_empty() {
                return trimmed.to_string();
            }
        }
    }
    let enclave_id = crate::prompt_enclave::PromptEnclave::gdrive_client_id();
    if !enclave_id.trim().is_empty() {
        return enclave_id;
    }
    "1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com".to_string()
}

pub fn get_gdrive_client_secret() -> String {
    if let Ok(sec) = std::env::var("FLOWORK_GDRIVE_CLIENT_SECRET") {
        let trimmed = sec.trim();
        if !trimmed.is_empty() {
            return trimmed.to_string();
        }
    }
    let p_home = std::env::var("FLOWORK_PORTABLE_ROOT").unwrap_or_else(|_| "portable-home".to_string());
    let sec_path = std::path::Path::new(&p_home).join(".flowork").join("gdrive_secret");
    if sec_path.exists() {
        if let Ok(content) = std::fs::read_to_string(sec_path) {
            let trimmed = content.trim();
            if !trimmed.is_empty() {
                return trimmed.to_string();
            }
        }
    }
    String::new()
}

pub fn get_flowork_token() -> String {
    if let Ok(tok) = std::env::var("FLOWORK_TOKEN") {
        let trimmed = tok.trim();
        if !trimmed.is_empty() {
            return trimmed.to_string();
        }
    }
    let p_home = std::env::var("FLOWORK_PORTABLE_ROOT").unwrap_or_else(|_| "portable-home".to_string());
    let candidates = [
        std::path::Path::new(&p_home).join(".flowork").join("auth_vault.json"),
        std::path::PathBuf::from("portable-home/.flowork/auth_vault.json"),
        std::path::PathBuf::from(".flowork/auth_vault.json"),
    ];
    for p in &candidates {
        if p.exists() {
            if let Ok(content) = std::fs::read_to_string(p) {
                if let Ok(v) = serde_json::from_str::<serde_json::Value>(&content) {
                    if let Some(tok) = v.get("flowork_token").and_then(|t| t.as_str()).or_else(|| v.get("upstream_flowork_token").and_then(|t| t.as_str())) {
                        let trimmed = tok.trim();
                        if !trimmed.is_empty() {
                            return trimmed.to_string();
                        }
                    }
                }
            }
        }
    }
    if let Ok(home) = std::env::var("HOME").or_else(|_| std::env::var("USERPROFILE")) {
        let p = std::path::PathBuf::from(home).join(".flowork").join("auth_vault.json");
        if p.exists() {
            if let Ok(content) = std::fs::read_to_string(&p) {
                if let Ok(v) = serde_json::from_str::<serde_json::Value>(&content) {
                    if let Some(tok) = v.get("flowork_token").and_then(|t| t.as_str()).or_else(|| v.get("upstream_flowork_token").and_then(|t| t.as_str())) {
                        let trimmed = tok.trim();
                        if !trimmed.is_empty() {
                            return trimmed.to_string();
                        }
                    }
                }
            }
        }
    }
    String::new()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DriveAccount {
    pub id: String,
    pub email: String,
    pub name: Option<String>,
    pub picture: Option<String>,
    pub access_token: String,
    pub refresh_token: String,
    pub expires_at: i64,
    pub quota_limit: u64,
    pub quota_usage: u64,
    pub priority: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OffloadedFile {
    pub local_path: String,
    pub shortcut_path: String,
    pub file_name: String,
    pub size: u64,
    pub account_email: String,
    pub gdrive_file_id: String,
    pub web_view_link: String,
    pub offloaded_at: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SyncDriveState {
    pub accounts: Vec<DriveAccount>,
    pub backup_folders: Vec<String>,
    pub offloaded_files: Vec<OffloadedFile>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncActivity {
    pub is_uploading: bool,
    pub current_file: String,
    pub status_text: String,
    pub progress_percent: u32,
}

impl Default for SyncActivity {
    fn default() -> Self {
        Self {
            is_uploading: false,
            current_file: String::new(),
            status_text: "Idle • Monitoring folders for new files".to_string(),
            progress_percent: 0,
        }
    }
}

pub struct SyncDriveManager {
    vault_path: PathBuf,
    host_port: u16,
    pub state: Arc<RwLock<SyncDriveState>>,
    pub activity: Arc<RwLock<SyncActivity>>,
}

#[allow(dead_code)]
impl SyncDriveManager {
    pub fn new(root_dir: &Path, port: u16) -> Self {
        let vault_dir = if root_dir.join("portable-home/.flowork").exists() {
            root_dir.join("portable-home/.flowork")
        } else if let Some(parent) = root_dir.parent() {
            if parent.join("portable-home/.flowork").exists() {
                parent.join("portable-home/.flowork")
            } else {
                root_dir.join("portable-home/.flowork")
            }
        } else {
            root_dir.join("portable-home/.flowork")
        };
        let _ = std::fs::create_dir_all(&vault_dir);
        let vault_path = vault_dir.join("sync_drive.json");

        let initial_state = if vault_path.exists() {
            std::fs::read_to_string(&vault_path)
                .ok()
                .and_then(|s| serde_json::from_str::<SyncDriveState>(&s).ok())
                .unwrap_or_default()
        } else {
            SyncDriveState::default()
        };

        Self {
            vault_path,
            host_port: port,
            state: Arc::new(RwLock::new(initial_state)),
            activity: Arc::new(RwLock::new(SyncActivity::default())),
        }
    }

    pub async fn save_state(&self) {
        let lock = self.state.read().await;
        if let Ok(data) = serde_json::to_string_pretty(&*lock) {
            let _ = std::fs::write(&self.vault_path, data);
        }
    }

    pub fn get_auth_url(&self) -> String {
        let redirect_uri = format!("{}127.0.0.1:{}/api/gdrive/auth/callback", crate::prompt_enclave::PromptEnclave::proto_http(), self.host_port);
        let client_id = get_gdrive_client_id();
        let base = crate::prompt_enclave::PromptEnclave::url_gdrive_auth();
        let scope = "https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/userinfo.email";
        format!(
            "{}?client_id={}&redirect_uri={}&response_type=code&scope={}&access_type=offline&prompt=consent",
            base,
            url_encode(&client_id),
            url_encode(&redirect_uri),
            url_encode(scope)
        )
    }

    pub async fn handle_oauth_callback(&self, code: &str) -> Result<DriveAccount, String> {
        let redirect_uri = format!("{}127.0.0.1:{}/api/gdrive/auth/callback", crate::prompt_enclave::PromptEnclave::proto_http(), self.host_port);
        let client_id = get_gdrive_client_id();
        let client_secret = get_gdrive_client_secret();
        let (access_token, refresh_token, expires_in) = if !client_secret.is_empty() {
            let post_data = format!(
                "client_id={}&client_secret={}&code={}&grant_type=authorization_code&redirect_uri={}",
                client_id, client_secret, code, redirect_uri
            );

            let out = tokio::process::Command::new("curl")
                .args([
                    "-s", "-X", "POST",
                    "-H", "Content-Type: application/x-www-form-urlencoded",
                    "-d", &post_data,
                    &crate::prompt_enclave::PromptEnclave::url_gdrive_token(),
                ])
                .output().await
                .map_err(|e| format!("Failed to exchange token: {e}"))?;

            let token_res: Value = serde_json::from_slice(&out.stdout)
                .map_err(|e| format!("Invalid token response: {e}"))?;

            if let Some(err) = token_res.get("error_description").and_then(|s| s.as_str()) {
                return Err(err.to_string());
            }

            let access_token = token_res["access_token"].as_str()
                .ok_or_else(|| "Missing access_token".to_string())?.to_string();
            let refresh_token = token_res["refresh_token"].as_str().unwrap_or("").to_string();
            let expires_in = token_res["expires_in"].as_i64().unwrap_or(3600);
            (access_token, refresh_token, expires_in)
        } else {
            // Sovereign Edge Broker Exchange (auth.floworkos.com)
            let post_json = json!({
                "code": code,
                "verifier": "",
                "code_verifier": "",
                "provider": "antigravity",
                "redirectUri": redirect_uri
            }).to_string();

            let flowork_token = get_flowork_token();
            let mut cmd = tokio::process::Command::new("curl");
            cmd.args([
                "-s", "-X", "POST",
                "-H", "Content-Type: application/json",
            ]);
            if !flowork_token.is_empty() {
                cmd.args(["-H", &format!("Authorization: Bearer {}", flowork_token)]);
            }
            cmd.args([
                "-d", &post_json,
                "https://auth.floworkos.com/api/auth/oauth/exchange",
            ]);

            let out = cmd.output().await
                .map_err(|e| format!("Failed to connect to edge auth broker: {e}"))?;

            let res: Value = serde_json::from_slice(&out.stdout)
                .map_err(|e| format!("Invalid edge token response: {e}"))?;

            if !res.get("success").and_then(|v| v.as_bool()).unwrap_or(false) {
                let err_msg = res.get("error").and_then(|s| s.as_str())
                    .or_else(|| res.get("error_description").and_then(|s| s.as_str()))
                    .unwrap_or("Edge token exchange failed");
                return Err(err_msg.to_string());
            }

            let access_token = res.get("accessToken").or_else(|| res.get("access_token"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| "Edge broker returned no access_token".to_string())?.to_string();
            let refresh_token = res.get("refreshToken").or_else(|| res.get("refresh_token"))
                .and_then(|v| v.as_str()).unwrap_or("").to_string();
            let expires_in = res.get("expiresIn").or_else(|| res.get("expires_in"))
                .and_then(|v| v.as_i64()).unwrap_or(3600);

            (access_token, refresh_token, expires_in)
        };
        let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs() as i64;
        let expires_at = now + expires_in;

        // Fetch user profile and storage quota
        let about = self.fetch_about(&access_token).await?;
        let user = about.get("user").cloned().unwrap_or(json!({}));
        let email = user.get("emailAddress").and_then(|s| s.as_str()).unwrap_or("unknown@gmail.com").to_string();
        let name = user.get("displayName").and_then(|s| s.as_str()).map(|s| s.to_string());
        let picture = user.get("photoLink").and_then(|s| s.as_str()).map(|s| s.to_string());

        let quota = about.get("storageQuota").cloned().unwrap_or(json!({}));
        let quota_limit: u64 = quota.get("limit").and_then(|v| v.as_str()).and_then(|s| s.parse().ok()).unwrap_or(16106127360);
        let quota_usage: u64 = quota.get("usage").and_then(|v| v.as_str()).and_then(|s| s.parse().ok()).unwrap_or(0);

        let mut lock = self.state.write().await;
        // Check if account already exists
        if let Some(existing) = lock.accounts.iter_mut().find(|a| a.email == email) {
            existing.access_token = access_token.clone();
            if !refresh_token.is_empty() {
                existing.refresh_token = refresh_token.clone();
            }
            existing.expires_at = expires_at;
            existing.quota_limit = quota_limit;
            existing.quota_usage = quota_usage;
            let acc = existing.clone();
            drop(lock);
            self.save_state().await;
            return Ok(acc);
        }

        let priority = lock.accounts.len() + 1;
        let account = DriveAccount {
            id: format!("acc_{}", lock.accounts.len() + 1),
            email,
            name,
            picture,
            access_token,
            refresh_token,
            expires_at,
            quota_limit,
            quota_usage,
            priority,
        };

        lock.accounts.push(account.clone());
        drop(lock);
        self.save_state().await;
        Ok(account)
    }

    async fn fetch_about(&self, access_token: &str) -> Result<Value, String> {
        let out = tokio::process::Command::new("curl")
            .args([
                "-s",
                "-H", &format!("Authorization: Bearer {access_token}"),
                &crate::prompt_enclave::PromptEnclave::url_gdrive_about(),
            ])
            .output().await
            .map_err(|e| format!("Curl error: {e}"))?;

        serde_json::from_slice(&out.stdout).map_err(|e| format!("JSON parse error: {e}"))
    }

    pub async fn refresh_token_for_account(acc: &mut DriveAccount) -> Result<(), String> {
        let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs() as i64;
        if now < acc.expires_at - 180 {
            return Ok(());
        }

        if acc.refresh_token.is_empty() {
            return Err(format!("No refresh_token for account {}", acc.email));
        }

        let client_secret = get_gdrive_client_secret();
        if !client_secret.is_empty() {
            let client_id = get_gdrive_client_id();
            let post_data = format!(
                "client_id={}&client_secret={}&refresh_token={}&grant_type=refresh_token",
                client_id, client_secret, acc.refresh_token
            );

            let out = match tokio::process::Command::new("curl")
                .args([
                    "-s", "-X", "POST",
                    "-H", "Content-Type: application/x-www-form-urlencoded",
                    "-d", &post_data,
                    &crate::prompt_enclave::PromptEnclave::url_gdrive_token(),
                ])
                .output().await {
                    Ok(o) => o,
                    Err(e) => {
                        // Backoff cooldown to prevent tight retry loop on network error
                        acc.expires_at = now + 300;
                        return Err(format!("Token refresh network error: {e}"));
                    }
                };

            let res: Value = match serde_json::from_slice(&out.stdout) {
                Ok(v) => v,
                Err(e) => {
                    // Backoff cooldown on malformed response
                    acc.expires_at = now + 300;
                    return Err(format!("Token refresh parse error: {e}"));
                }
            };

            if let Some(token) = res["access_token"].as_str() {
                acc.access_token = token.to_string();
                let expires_in = res["expires_in"].as_i64().unwrap_or(3600);
                acc.expires_at = now + expires_in;
                Ok(())
            } else {
                // Backoff cooldown to prevent spamming Google OAuth if credentials or grant are invalid
                acc.expires_at = now + 300;
                let err_desc = res.get("error_description").and_then(|v| v.as_str())
                    .or_else(|| res.get("error").and_then(|v| v.as_str()))
                    .unwrap_or("Failed to refresh access token");
                Err(err_desc.to_string())
            }
        } else {
            // Refresh via Sovereign Edge Broker (auth.floworkos.com)
            let post_json = json!({
                "refreshToken": acc.refresh_token,
                "provider": "antigravity"
            }).to_string();

            let flowork_token = get_flowork_token();
            let mut cmd = tokio::process::Command::new("curl");
            cmd.args([
                "-s", "-X", "POST",
                "-H", "Content-Type: application/json",
            ]);
            if !flowork_token.is_empty() {
                cmd.args(["-H", &format!("Authorization: Bearer {}", flowork_token)]);
            }
            cmd.args([
                "-d", &post_json,
                "https://auth.floworkos.com/api/auth/oauth/refresh",
            ]);

            let out = match cmd.output().await {
                Ok(o) => o,
                Err(e) => {
                    acc.expires_at = now + 300;
                    return Err(format!("Edge refresh network error: {e}"));
                }
            };

            let res: Value = match serde_json::from_slice(&out.stdout) {
                Ok(v) => v,
                Err(e) => {
                    acc.expires_at = now + 300;
                    return Err(format!("Edge refresh parse error: {e}"));
                }
            };

            if res.get("success").and_then(|v| v.as_bool()).unwrap_or(false) {
                if let Some(tok) = res.get("accessToken").or_else(|| res.get("access_token")).and_then(|v| v.as_str()) {
                    acc.access_token = tok.to_string();
                    if let Some(rt) = res.get("refreshToken").or_else(|| res.get("refresh_token")).and_then(|v| v.as_str()) {
                        if !rt.is_empty() {
                            acc.refresh_token = rt.to_string();
                        }
                    }
                    let expires_in = res.get("expiresIn").or_else(|| res.get("expires_in")).and_then(|v| v.as_i64()).unwrap_or(3600);
                    acc.expires_at = now + expires_in;
                    return Ok(());
                }
            }

            acc.expires_at = now + 300;
            let err_desc = res.get("error").and_then(|v| v.as_str())
                .or_else(|| res.get("error_description").and_then(|v| v.as_str()))
                .unwrap_or("Failed to refresh access token via Edge broker");
            Err(err_desc.to_string())
        }
    }

    pub async fn refresh_account_token(&self, acc: &mut DriveAccount) -> Result<(), String> {
        Self::refresh_token_for_account(acc).await
    }

    pub async fn refresh_all_quotas(&self) {
        let mut lock = self.state.write().await;
        for acc in lock.accounts.iter_mut() {
            let _ = Self::refresh_account_quota_internal(acc).await;
        }
        drop(lock);
        self.save_state().await;
    }

    async fn refresh_account_quota_internal(acc: &mut DriveAccount) -> Result<(), String> {
        if let Err(e) = Self::refresh_token_for_account(acc).await {
            eprintln!("[Sync Drive] Token refresh failed for {}: {e} (cooldown active)", acc.email);
            return Err(e);
        }

        let out = tokio::process::Command::new("curl")
            .args([
                "-s",
                "-H", &format!("Authorization: Bearer {}", acc.access_token),
                &crate::prompt_enclave::PromptEnclave::url_gdrive_quota(),
            ])
            .output().await
            .map_err(|e| e.to_string())?;

        let res: Value = serde_json::from_slice(&out.stdout).map_err(|e| e.to_string())?;
        if let Some(quota) = res.get("storageQuota") {
            if let Some(limit) = quota.get("limit").and_then(|v| v.as_str()).and_then(|s| s.parse().ok()) {
                acc.quota_limit = limit;
            }
            if let Some(usage) = quota.get("usage").and_then(|v| v.as_str()).and_then(|s| s.parse().ok()) {
                acc.quota_usage = usage;
            }
        }
        Ok(())
    }

    pub async fn ensure_folder(&self, access_token: &str) -> Result<String, String> {
        let query = "name='X-Flow AutoBackup' and mimeType='application/vnd.google-apps.folder' and trashed=false";
        let out = tokio::process::Command::new("curl")
            .args([
                "-s",
                "-H", &format!("Authorization: Bearer {access_token}"),
                &format!("{}?q={}", crate::prompt_enclave::PromptEnclave::url_gdrive_files(), url_encode(query)),
            ])
            .output().await
            .map_err(|e| format!("Folder search error: {e}"))?;

        let res: Value = serde_json::from_slice(&out.stdout).unwrap_or(json!({}));
        if let Some(files) = res["files"].as_array() {
            if let Some(first) = files.first() {
                if let Some(id) = first["id"].as_str() {
                    return Ok(id.to_string());
                }
            }
        }

        // Create folder
        let body = json!({
            "name": "X-Flow AutoBackup",
            "mimeType": "application/vnd.google-apps.folder"
        }).to_string();

        let out = tokio::process::Command::new("curl")
            .args([
                "-s", "-X", "POST",
                "-H", &format!("Authorization: Bearer {access_token}"),
                "-H", "Content-Type: application/json",
                "-d", &body,
                &crate::prompt_enclave::PromptEnclave::url_gdrive_files(),
            ])
            .output().await
            .map_err(|e| format!("Folder creation error: {e}"))?;

        let created: Value = serde_json::from_slice(&out.stdout).map_err(|e| e.to_string())?;
        created["id"].as_str().map(|s| s.to_string()).ok_or_else(|| "Failed to get folder id".to_string())
    }

    pub async fn upload_and_offload(&self, local_path: &Path) -> Result<OffloadedFile, String> {
        if !local_path.exists() || !local_path.is_file() {
            return Err("File does not exist or is a directory".to_string());
        }

        let file_name = local_path.file_name().and_then(|f| f.to_str()).unwrap_or("file").to_string();
        let meta = std::fs::metadata(local_path).map_err(|e| format!("Failed to read metadata: {e}"))?;
        let size = meta.len();

        let mut lock = self.state.write().await;
        if lock.accounts.is_empty() {
            return Err("No Google Drive accounts connected! Add an account in Sync Drive.".to_string());
        }

        // Sort by priority
        lock.accounts.sort_by_key(|a| a.priority);

        // Find eligible account (Multi-account cascading)
        let mut target_acc_idx = None;
        for (i, acc) in lock.accounts.iter_mut().enumerate() {
            let _ = Self::refresh_account_quota_internal(acc).await;
            let remaining = acc.quota_limit.saturating_sub(acc.quota_usage);
            if remaining > (size + 5_000_000) {
                target_acc_idx = Some(i);
                break;
            }
        }

        let acc_idx = target_acc_idx.ok_or_else(|| {
            "All connected Google Drive accounts are FULL! Add another account to spillover.".to_string()
        })?;

        let account = &mut lock.accounts[acc_idx];
        let acc_email = account.email.clone();
        let token = account.access_token.clone();
        drop(lock);

        // Update live activity indicator
        {
            let mut act = self.activity.write().await;
            act.is_uploading = true;
            act.current_file = file_name.clone();
            act.progress_percent = 25;
            act.status_text = format!("Uploading {} ({}) to {}...", file_name, format_bytes_str(size), acc_email);
        }

        let folder_id = self.ensure_folder(&token).await?;

        // Perform Resumable / Standard Upload
        let metadata_json = json!({
            "name": file_name,
            "parents": [folder_id]
        }).to_string();

        let mime = mime_guess::from_path(local_path).first_or_octet_stream().to_string();

        let out = match tokio::process::Command::new("curl")
            .args([
                "-s", "-X", "POST",
                "-H", &format!("Authorization: Bearer {token}"),
                "-F", &format!("metadata={metadata_json};type=application/json;charset=UTF-8"),
                "-F", &format!("file=@{};type={mime}", local_path.display()),
                &crate::prompt_enclave::PromptEnclave::url_gdrive_upload(),
            ])
            .output().await {
                Ok(o) => o,
                Err(e) => {
                    let err_msg = format!("Upload error: {e}");
                    let mut act_lock = self.activity.write().await;
                    act_lock.is_uploading = false;
                    act_lock.status_text = err_msg.clone();
                    return Err(err_msg);
                }
            };

        let upload_res: Value = serde_json::from_slice(&out.stdout)
            .map_err(|e| format!("Invalid upload response: {e}"))?;

        let gdrive_file_id = upload_res["id"].as_str()
            .ok_or_else(|| format!("Upload failed: {}", String::from_utf8_lossy(&out.stdout)))?
            .to_string();

        let web_view_link = upload_res["webViewLink"].as_str()
            .unwrap_or(&format!("{}/{gdrive_file_id}/view", crate::prompt_enclave::PromptEnclave::url_gdrive_view()))
            .to_string();

        // Integrity check: verify remote size matches local file size
        if let Some(r_size) = upload_res.get("size").and_then(|v| v.as_str().and_then(|s| s.parse::<u64>().ok()).or_else(|| v.as_u64())) {
            if r_size != size {
                let err_msg = format!("Integrity failure: remote size ({r_size}) does not match local file size ({size}). Local file preserved.");
                let mut act_lock = self.activity.write().await;
                act_lock.is_uploading = false;
                act_lock.status_text = err_msg.clone();
                return Err(err_msg);
            }
        }

        // Integrity check: verify md5 checksum if returned by Google
        if let Some(r_md5) = upload_res.get("md5Checksum").and_then(|v| v.as_str()) {
            #[cfg(unix)]
            {
                if let Ok(md5_out) = std::process::Command::new("md5sum").arg(local_path).output() {
                    if let Ok(stdout_s) = String::from_utf8(md5_out.stdout) {
                        if let Some(l_md5) = stdout_s.split_whitespace().next() {
                            if !r_md5.eq_ignore_ascii_case(l_md5) {
                                let err_msg = format!("Integrity failure: remote MD5 ({r_md5}) does not match local MD5 ({l_md5}). Local file preserved.");
                                let mut act_lock = self.activity.write().await;
                                act_lock.is_uploading = false;
                                act_lock.status_text = err_msg.clone();
                                return Err(err_msg);
                            }
                        }
                    }
                }
            }
        }

        // Update progress
        {
            let mut act = self.activity.write().await;
            act.progress_percent = 85;
            act.status_text = format!("Verifying {} and creating desktop stub...", file_name);
        }

        // Create OS Native Shortcut / Stub File
        let parent = local_path.parent().unwrap_or_else(|| Path::new("."));
        #[cfg(target_os = "windows")]
        let shortcut_path = parent.join(format!("{}.url", file_name));
        #[cfg(not(target_os = "windows"))]
        let shortcut_path = parent.join(format!("{}.desktop", file_name));

        #[cfg(target_os = "windows")]
        let shortcut_content = format!("[InternetShortcut]\r\nURL={}\r\n", web_view_link);
        #[cfg(not(target_os = "windows"))]
        let shortcut_content = format!(
            "[Desktop Entry]\nVersion=1.0\nType=Link\nName={} [Cloud: {}]\nURL={}\nIcon=google-chrome\n",
            file_name, acc_email, web_view_link
        );

        std::fs::write(&shortcut_path, shortcut_content)
            .map_err(|e| format!("Failed to create shortcut stub: {e}"))?;

        // Safely remove the physical file from PC to free up local disk space!
        std::fs::remove_file(local_path)
            .map_err(|e| format!("Failed to remove local physical file after upload: {e}"))?;

        let now_str = chrono_or_simple_time();
        let offloaded = OffloadedFile {
            local_path: local_path.to_string_lossy().to_string(),
            shortcut_path: shortcut_path.to_string_lossy().to_string(),
            file_name: file_name.clone(),
            size,
            account_email: acc_email.clone(),
            gdrive_file_id,
            web_view_link,
            offloaded_at: now_str,
        };

        let mut lock = self.state.write().await;
        // Update account quota
        if let Some(acc) = lock.accounts.iter_mut().find(|a| a.email == offloaded.account_email) {
            acc.quota_usage += size;
        }
        lock.offloaded_files.retain(|f| f.local_path != offloaded.local_path);
        lock.offloaded_files.insert(0, offloaded.clone());
        drop(lock);

        // Reset activity to finished
        {
            let mut act = self.activity.write().await;
            act.is_uploading = false;
            act.progress_percent = 100;
            act.status_text = format!("SUCCESS: Offloaded {} to {} • Physical file deleted from PC.", file_name, acc_email);
        }

        self.save_state().await;
        Ok(offloaded)
    }

    pub async fn restore_file(&self, gdrive_file_id: &str) -> Result<String, String> {
        let lock = self.state.read().await;
        let entry = lock.offloaded_files.iter().find(|f| f.gdrive_file_id == gdrive_file_id)
            .cloned()
            .ok_or_else(|| "Offloaded file not found in registry".to_string())?;

        let account = lock.accounts.iter().find(|a| a.email == entry.account_email)
            .cloned()
            .ok_or_else(|| "Associated Google account is missing".to_string())?;
        drop(lock);

        let token = account.access_token;
        let target_path = PathBuf::from(&entry.local_path);
        let shortcut_path = PathBuf::from(&entry.shortcut_path);

        if let Some(parent) = target_path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }

        // Download physical file back to PC
        let out = tokio::process::Command::new("curl")
            .args([
                "-sL",
                "-H", &format!("Authorization: Bearer {token}"),
                &format!("{}/{}?alt=media", crate::prompt_enclave::PromptEnclave::url_gdrive_files(), gdrive_file_id),
                "-o", &entry.local_path,
            ])
            .output().await
            .map_err(|e| format!("Download error: {e}"))?;

        if !out.status.success() || !target_path.exists() {
            return Err("Failed to download file from Google Drive".to_string());
        }

        // Remove the shortcut stub
        if shortcut_path.exists() {
            let _ = std::fs::remove_file(shortcut_path);
        }

        // Remove from offloaded files
        let mut lock = self.state.write().await;
        lock.offloaded_files.retain(|f| f.gdrive_file_id != gdrive_file_id);
        drop(lock);
        self.save_state().await;

        Ok(entry.local_path)
    }

    pub async fn add_folder(&self, folder: &str) -> Result<(), String> {
        let p = Path::new(folder);
        if !p.exists() || !p.is_dir() {
            return Err("Path does not exist or is not a directory".to_string());
        }
        let canonical = p.canonicalize().map_err(|e| e.to_string())?;
        let str_path = canonical.to_string_lossy().to_string();

        let mut lock = self.state.write().await;
        if !lock.backup_folders.contains(&str_path) {
            lock.backup_folders.push(str_path);
            drop(lock);
            self.save_state().await;
        }
        Ok(())
    }

    pub async fn remove_folder(&self, folder: &str) {
        let mut lock = self.state.write().await;
        lock.backup_folders.retain(|f| f != folder);
        drop(lock);
        self.save_state().await;
    }

    pub async fn remove_account(&self, email: &str) {
        let mut lock = self.state.write().await;
        lock.accounts.retain(|a| a.email != email);
        for (i, a) in lock.accounts.iter_mut().enumerate() {
            a.priority = i + 1;
        }
        drop(lock);
        self.save_state().await;
    }

    pub async fn get_status(&self) -> Value {
        let lock = self.state.read().await;
        let mut total_limit = 0u64;
        let mut total_usage = 0u64;

        let accounts_json: Vec<Value> = lock.accounts.iter().map(|a| {
            total_limit += a.quota_limit;
            total_usage += a.quota_usage;
            let remaining = a.quota_limit.saturating_sub(a.quota_usage);
            json!({
                "id": a.id,
                "email": a.email,
                "name": a.name,
                "picture": a.picture,
                "quota_limit": a.quota_limit,
                "quota_usage": a.quota_usage,
                "remaining": remaining,
                "priority": a.priority,
            })
        }).collect();

        let total_remaining = total_limit.saturating_sub(total_usage);
        let act = self.activity.read().await.clone();

        json!({
            "status": "ok",
            "activity": act,
            "accounts": accounts_json,
            "total_limit": total_limit,
            "total_usage": total_usage,
            "total_remaining": total_remaining,
            "backup_folders": lock.backup_folders,
            "offloaded_files": lock.offloaded_files,
        })
    }
}

fn format_bytes_str(bytes: u64) -> String {
    if bytes < 1024 {
        format!("{bytes} B")
    } else if bytes < 1024 * 1024 {
        format!("{:.1} KB", bytes as f64 / 1024.0)
    } else if bytes < 1024 * 1024 * 1024 {
        format!("{:.1} MB", bytes as f64 / (1024.0 * 1024.0))
    } else {
        format!("{:.2} GB", bytes as f64 / (1024.0 * 1024.0 * 1024.0))
    }
}

fn chrono_or_simple_time() -> String {
    let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs();
    format!("{now}")
}

fn url_encode(input: &str) -> String {
    let mut encoded = String::new();
    for b in input.bytes() {
        match b {
            b'a'..=b'z' | b'A'..=b'Z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => encoded.push(b as char),
            _ => encoded.push_str(&format!("%{:02X}", b)),
        }
    }
    encoded
}


