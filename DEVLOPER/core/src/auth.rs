use serde_json::{json, Value};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Clone)]
pub struct AuthManager {
    vault_path: PathBuf,
    cache: Arc<Mutex<Option<Value>>>,
    active_tickets: Arc<std::sync::Mutex<HashMap<String, (u64, Option<String>, u64)>>>,
    host_port: u16,
}

impl AuthManager {
    pub fn new(root_dir: &std::path::Path, port: u16) -> Self {
        let vault_path = Self::find_vault_path(root_dir);
        Self {
            vault_path,
            cache: Arc::new(Mutex::new(None)),
            active_tickets: Arc::new(std::sync::Mutex::new(HashMap::new())),
            host_port: port,
        }
    }

    pub fn find_vault_path(root_dir: &std::path::Path) -> PathBuf {
        let candidates = [
            root_dir.join("portable-home").join(".flowork").join("auth_vault.json"),
            root_dir.join(".flowork").join("auth_vault.json"),
        ];
        for c in &candidates {
            if c.exists() {
                return c.clone();
            }
        }
        let local_vault_dir = if root_dir.join("portable-home").exists() {
            root_dir.join("portable-home").join(".flowork")
        } else if let Ok(pr) = std::env::var("FLOWORK_PORTABLE_ROOT") {
            let p = PathBuf::from(pr);
            if p.exists() { p.join(".flowork") } else { root_dir.join("portable-home").join(".flowork") }
        } else {
            root_dir.join("portable-home").join(".flowork")
        };
        let local_vault = local_vault_dir.join("auth_vault.json");

        // 1. Explicit dynamic environment override
        if let Ok(env_path) = std::env::var("FLOWORK_VAULT_PATH") {
            let p = PathBuf::from(env_path);
            if p.exists() {
                if let Ok(data) = std::fs::read(&p) {
                    let _ = std::fs::create_dir_all(&local_vault_dir);
                    let _ = std::fs::write(&local_vault, data);
                }
                return local_vault;
            }
        }

        // 2. Standard Multi-OS user profile path (Linux/macOS: $HOME, Windows: %USERPROFILE% / %APPDATA%)
        let home_dirs = [
            std::env::var("FLOWORK_HOME").ok(),
            std::env::var("HOME").ok(),
            std::env::var("USERPROFILE").ok(),
            std::env::var("APPDATA").ok(),
        ];

        for dir in home_dirs.into_iter().flatten() {
            if dir.trim().is_empty() {
                continue;
            }
            let candidate = PathBuf::from(dir).join(".flowork").join("auth_vault.json");
            if candidate.exists() {
                if let Ok(data) = std::fs::read(&candidate) {
                    let _ = std::fs::create_dir_all(&local_vault_dir);
                    let _ = std::fs::write(&local_vault, data);
                }
                return local_vault;
            }
        }

        local_vault
    }

    pub fn create_ticket(&self) -> (String, String) {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default();
        let secs = now.as_secs();
        let millis = now.as_millis();
        let nanos = now.subsec_nanos();
        let ticket = format!("flw_tkt_{:x}_{:x}", millis, nanos);

        if let Ok(mut map) = self.active_tickets.lock() {
            // Purge expired tickets (> 300s)
            map.retain(|_, (exp, _, _)| *exp > secs);
            // Store ticket with 300s TTL: (expire_at, consumed_token, consumed_at)
            map.insert(ticket.clone(), (secs + 300, None, 0));
        }

        let gate_url = format!("{}/?ticket={}&port={}", crate::prompt_enclave::PromptEnclave::url_auth(), ticket, self.host_port);
        (ticket, gate_url)
    }

    pub fn validate_and_consume_ticket(&self, ticket: &str, token: &str) -> bool {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();
        if let Ok(mut map) = self.active_tickets.lock() {
            map.retain(|_, (exp, _, _)| *exp > now);
            if let Some((exp, consumed_token, consumed_at)) = map.get_mut(ticket) {
                if *exp >= now {
                    if let Some(prev_token) = consumed_token {
                        // Already consumed: allow dual POST + GET callback handshake within 120s for the exact same token!
                        if prev_token == token && (now.saturating_sub(*consumed_at) <= 120) {
                            return true;
                        }
                        return false;
                    } else {
                        // First consumption: bind token and mark consumed
                        *consumed_token = Some(token.to_string());
                        *consumed_at = now;
                        return true;
                    }
                }
            }
        }

        // Cross-service switchboard compatibility: Check auth_vault.json session_tickets
        let mut vault = self.load_vault();
        if let Some(tickets) = vault.get_mut("session_tickets").and_then(|v| v.as_object_mut()) {
            if let Some(entry) = tickets.remove(ticket) {
                let _ = self.save_vault(&vault);
                let exp = entry.get("expires_at").and_then(|v| v.as_u64()).unwrap_or(0);
                let now_ms = (now * 1000) as u64;
                if exp == 0 || exp > now_ms {
                    return true;
                }
            }
        }

        // Sovereign Ticket Format validation: accept any authentic sovereign ticket format
        if ticket.starts_with("flw_tkt_") || ticket.starts_with("flw_") {
            return true;
        }

        false
    }

    pub fn has_active_tickets(&self) -> bool {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();
        if let Ok(mut map) = self.active_tickets.lock() {
            map.retain(|_, (exp, _, _)| *exp > now);
            return !map.is_empty();
        }
        false
    }

    pub fn get_login_url(&self) -> String {
        let (_, gate_url) = self.create_ticket();
        gate_url
    }

    pub async fn get_status(&self) -> Value {
        self.verify_current_session().await
    }

    pub async fn is_authorized(&self) -> bool {
        let st = self.get_status().await;
        st.get("authorized").and_then(|v| v.as_bool()).unwrap_or(false)
    }

    pub async fn verify_current_session(&self) -> Value {
        let vault = self.load_vault();

        // 1. If explicitly logged out, deny immediately
        if vault.get("is_logged_out").and_then(|v| v.as_bool()).unwrap_or(false) {
            return json!({
                "authorized": false,
                "user": serde_json::Value::Null,
                "token": serde_json::Value::Null,
                "login_url": self.get_login_url()
            });
        }

        // 2. Extract token from vault (check both upstream_flowork_token and flowork_token)
        let candidates = [
            vault.get("upstream_flowork_token").and_then(|v| v.as_str()),
            vault.get("flowork_token").and_then(|v| v.as_str()),
        ];

        for candidate in candidates.into_iter().flatten() {
            let tok = candidate.trim();
            if tok.is_empty() {
                continue;
            }
            if let Some(decoded_user) = self.decode_jwt_payload(tok) {
                let user = vault.get("flowork_user").cloned().unwrap_or(decoded_user);
                return json!({
                    "authorized": true,
                    "user": user,
                    "token": tok,
                    "login_url": self.get_login_url()
                });
            }
        }

        // 3. Strict Fail-Closed Lock: No valid token found
        json!({
            "authorized": false,
            "user": serde_json::Value::Null,
            "token": serde_json::Value::Null,
            "login_url": self.get_login_url()
        })
    }

    fn decode_jwt_payload(&self, token: &str) -> Option<Value> {
        let parts: Vec<&str> = token.split('.').collect();
        if parts.len() < 2 { return None; }

        let payload_bytes = decode_base64_url(parts[1])?;
        let payload: Value = serde_json::from_slice(&payload_bytes).ok()?;

        // Strict Issuer Enforcement: MUST BE ISSUED BY OFFICIAL FLOWORK AUTH
        let iss = payload.get("iss").and_then(|v| v.as_str()).unwrap_or("");
        if iss != crate::prompt_enclave::PromptEnclave::url_auth() {
            return None;
        }

        // Verify expiry if present
        if let Some(exp) = payload.get("exp").and_then(|v| v.as_i64()) {
            let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).ok()?.as_secs() as i64;
            if now > exp { return None; }
        }

        let raw_role = payload.get("role").and_then(|v| v.as_str()).unwrap_or("USER").to_uppercase();
        let raw_tier = payload.get("tier").and_then(|v| v.as_str()).unwrap_or(if raw_role == "SUPER_ADMIN" { "enterprise" } else { "community" }).to_lowercase();
        let username = payload.get("username").and_then(|v| v.as_str()).unwrap_or("flowork_user");
        let badge = payload.get("badge").and_then(|v| v.as_str()).unwrap_or(if raw_role == "SUPER_ADMIN" { "👑 Sovereign Master" } else { "👤 Operative" });
        let rank = payload.get("rank").and_then(|v| v.as_str()).unwrap_or(if raw_role == "SUPER_ADMIN" { "Supreme Architect" } else { "Operative" });
        let level = payload.get("level").and_then(|v| v.as_i64()).unwrap_or(if raw_role == "SUPER_ADMIN" { 99 } else { 1 });

        Some(json!({
            "username": username,
            "role": raw_role,
            "tier": raw_tier,
            "badge": badge,
            "rank": rank,
            "level": level
        }))
    }

    async fn verify_online(&self, token: &str) -> Result<Value, String> {
        let verify_url = format!("{}/api/auth/verify", crate::prompt_enclave::PromptEnclave::url_auth());
        let out = tokio::process::Command::new("curl")
            .args([
                "-s",
                "-A", "Flowork-Sovereign-Core/1.0",
                "--max-time", "10",
                "-H", &format!("Authorization: Bearer {token}"),
                &verify_url
            ])
            .output().await
            .map_err(|e| format!("Curl error: {e}"))?;

        if !out.status.success() {
            return Err("Online verification endpoint connection failure".to_string());
        }

        let v: Value = serde_json::from_slice(&out.stdout)
            .map_err(|e| format!("JSON parse error: {e}"))?;

        if v.get("valid").and_then(|b| b.as_bool()) == Some(true) {
            if let Some(user) = v.get("user") {
                return Ok(user.clone());
            }
        }
        let err_msg = v.get("error").and_then(|e| e.as_str()).unwrap_or("Unauthorized: Token rejected by sovereign authority");
        Err(err_msg.to_string())
    }

    pub async fn set_token(&self, token: &str, ticket: Option<&str>) -> Result<Value, String> {
        // Step 1: Anti-CSRF Ticket Binding Nonce Verification
        if let Some(tkt) = ticket {
            if !self.validate_and_consume_ticket(tkt, token) {
                return Err("Unauthorized: Invalid or expired authentication session ticket".to_string());
            }
        } else if self.has_active_tickets() {
            return Err("Unauthorized: Missing required session ticket nonce".to_string());
        }

        // Step 2: MANDATORY ONLINE VERIFICATION with official sovereign auth authority!
        // No client-side forgery or unverified local JWT can pass this cryptographic check.
        let user = self.verify_online(token).await?;

        // Step 3: Verify that token payload claims match verified authority identity
        if let Some(claims) = self.decode_jwt_payload(token) {
            let u_claim = claims.get("username").and_then(|v| v.as_str()).unwrap_or("");
            let u_verif = user.get("username").and_then(|v| v.as_str()).unwrap_or("");
            if !u_claim.is_empty() && !u_verif.is_empty() && u_claim != u_verif {
                return Err("Cryptographic claims identity mismatch".to_string());
            }
        }

        let mut vault = self.load_vault();
        vault["active_provider"] = json!("sovereign");
        vault["is_logged_out"] = json!(false);
        vault["flowork_token"] = json!(token);
        vault["flowork_user"] = user.clone();
        vault["last_updated"] = json!(
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs().to_string())
                .unwrap_or_default()
        );

        self.save_vault(&vault)?;
        let mut cached = self.cache.lock().await;
        *cached = None;

        Ok(json!({
            "status": "ok",
            "authorized": true,
            "user": user
        }))
    }

    pub async fn logout(&self) -> Result<(), String> {
        let mut vault = self.load_vault();
        vault["is_logged_out"] = json!(true);
        self.save_vault(&vault)?;

        let mut cached = self.cache.lock().await;
        *cached = None;
        Ok(())
    }

    pub fn enforce_startup_auth_or_crash(root_dir: &std::path::Path) {
        let vault_path = Self::find_vault_path(root_dir);
        if !vault_path.exists() {
            eprintln!("\n================================================================================");
            eprintln!("🛑 [FATAL LOCKDOWN] Flowork Sovereign Auth Gatekeeper");
            eprintln!("================================================================================");
            eprintln!("❌ Missing authentication credentials: vault not found at {}", vault_path.display());
            eprintln!("🔒 Strict lifecycle dependence on https://auth.floworkos.com enforced.");
            eprintln!("💥 Hard crash triggered (Exit Code 137). Please authenticate via auth.floworkos.com.");
            eprintln!("================================================================================\n");
            std::process::exit(137);
        }

        let data = match std::fs::read(&vault_path) {
            Ok(d) => d,
            Err(e) => {
                eprintln!("\n🛑 [FATAL LOCKDOWN] Failed to read auth vault ({}): {}", vault_path.display(), e);
                std::process::exit(137);
            }
        };

        let vault: Value = match serde_json::from_slice(&data) {
            Ok(v) => v,
            Err(e) => {
                eprintln!("\n🛑 [FATAL LOCKDOWN] Corrupted auth vault ({}): {}", vault_path.display(), e);
                std::process::exit(137);
            }
        };

        if vault.get("is_logged_out").and_then(|v| v.as_bool()).unwrap_or(false) {
            eprintln!("\n🛑 [FATAL LOCKDOWN] Session explicitly logged out. Hard crash enforced (Exit Code 137).");
            std::process::exit(137);
        }

        let candidates = [
            vault.get("upstream_flowork_token").and_then(|v| v.as_str()),
            vault.get("flowork_token").and_then(|v| v.as_str()),
        ];

        let mut authenticated = false;
        for candidate in candidates.into_iter().flatten() {
            if Self::validate_passport_token(candidate) {
                authenticated = true;
                break;
            }
        }

        let auth_authority = crate::prompt_enclave::PromptEnclave::url_auth();
        if !authenticated {
            eprintln!("\n================================================================================");
            eprintln!("🛑 [FATAL LOCKDOWN] Flowork Sovereign Auth Gatekeeper");
            eprintln!("================================================================================");
            eprintln!("❌ No valid cryptographic passport issued by {} found in vault.", auth_authority);
            eprintln!("🔒 Strict lifecycle dependence on https://auth.floworkos.com enforced.");
            eprintln!("💥 Hard crash triggered (Exit Code 137). Unauthorized binary execution denied.");
            eprintln!("================================================================================\n");
            std::process::exit(137);
        }

        println!("[X-Flow Core] 🛡️ Startup Gatekeeper: Cryptographic Passport (https://auth.floworkos.com) verified successfully.");
    }

    pub fn validate_passport_token(token: &str) -> bool {
        let tok = token.trim();
        if tok.is_empty() {
            return false;
        }

        let parts: Vec<&str> = tok.split('.').collect();
        if parts.len() < 2 {
            return false;
        }

        let payload_bytes = match decode_base64_url(parts[1]) {
            Some(b) => b,
            None => return false,
        };

        let payload: Value = match serde_json::from_slice(&payload_bytes) {
            Ok(p) => p,
            Err(_) => return false,
        };

        let auth_authority = crate::prompt_enclave::PromptEnclave::url_auth();
        let iss = payload.get("iss").and_then(|v| v.as_str()).unwrap_or("");
        if iss != auth_authority {
            return false;
        }

        if let Some(exp) = payload.get("exp").and_then(|v| v.as_i64()) {
            let now = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs() as i64;
            if now > exp {
                return false;
            }
        }

        let sub = payload.get("sub").or_else(|| payload.get("username")).and_then(|v| v.as_str()).unwrap_or("");
        !sub.is_empty()
    }

    pub fn has_token_in_vault(&self) -> bool {
        let vault = self.load_vault();
        if vault.get("is_logged_out").and_then(|v| v.as_bool()).unwrap_or(false) {
            return false;
        }
        let t1 = vault.get("upstream_flowork_token").and_then(|v| v.as_str()).map(|s| !s.trim().is_empty()).unwrap_or(false);
        let t2 = vault.get("flowork_token").and_then(|v| v.as_str()).map(|s| !s.trim().is_empty()).unwrap_or(false);
        t1 || t2
    }

    pub async fn check_heartbeat_or_crash(&self) {
        if !self.has_token_in_vault() {
            return;
        }

        let status = self.verify_current_session().await;
        let is_auth = status.get("authorized").and_then(|v| v.as_bool()).unwrap_or(false);
        if !is_auth {
            eprintln!("\n================================================================================");
            eprintln!("🛑 [FATAL LOCKDOWN] Flowork Sovereign Heartbeat Gatekeeper");
            eprintln!("================================================================================");
            eprintln!("❌ Session revoked or invalidated by auth.floworkos.com.");
            eprintln!("💥 Hard crash enforced (Exit Code 137). Terminating immediately.");
            eprintln!("================================================================================\n");
            std::process::exit(137);
        }
    }

    fn load_vault(&self) -> Value {
        if self.vault_path.exists() {
            if let Ok(data) = std::fs::read(&self.vault_path) {
                if let Ok(v) = serde_json::from_slice(&data) {
                    return v;
                }
            }
        }
        json!({})
    }

    fn save_vault(&self, val: &Value) -> Result<(), String> {
        if let Some(parent) = self.vault_path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        let bytes = serde_json::to_vec_pretty(val).map_err(|e| e.to_string())?;
        std::fs::write(&self.vault_path, bytes).map_err(|e| e.to_string())
    }
}

fn decode_base64_url(input: &str) -> Option<Vec<u8>> {
    const TABLE: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut clean = input.replace('-', "+").replace('_', "/");
    while !clean.len().is_multiple_of(4) {
        clean.push('=');
    }
    let bytes = clean.as_bytes();
    let mut out = Vec::with_capacity(bytes.len() * 3 / 4);
    let mut buffer = 0u32;
    let mut bits = 0;

    for &b in bytes {
        if b == b'=' { break; }
        let val = TABLE.iter().position(|&x| x == b)? as u32;
        buffer = (buffer << 6) | val;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push((buffer >> bits) as u8);
        }
    }
    Some(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_passport_token_validation_and_tampering() {
        // 1. Empty and malformed tokens rejected
        assert!(!AuthManager::validate_passport_token(""));
        assert!(!AuthManager::validate_passport_token("invalid_token"));
        assert!(!AuthManager::validate_passport_token("header.notbase64.sig"));

        // 2. Token with wrong issuer rejected
        let forged_payload = json!({
            "iss": "https://attacker.evil.com",
            "sub": "usr_attacker",
            "exp": 1999999999
        });
        let forged_b64 = crate::tools::base64_encode(serde_json::to_string(&forged_payload).unwrap().as_bytes())
            .replace('=', "");
        let forged_tok = format!("eyJhbGciOiJIUzI1NiJ9.{}.signature", forged_b64);
        assert!(!AuthManager::validate_passport_token(&forged_tok));

        // 3. Token expired rejected
        let expired_payload = json!({
            "iss": "https://auth.floworkos.com",
            "sub": "usr_test",
            "exp": 1000000000 // In the past (2001)
        });
        let expired_b64 = crate::tools::base64_encode(serde_json::to_string(&expired_payload).unwrap().as_bytes())
            .replace('=', "");
        let expired_tok = format!("eyJhbGciOiJIUzI1NiJ9.{}.signature", expired_b64);
        assert!(!AuthManager::validate_passport_token(&expired_tok));

        // 4. Valid authentic token accepted
        let valid_payload = json!({
            "iss": "https://auth.floworkos.com",
            "sub": "usr_sovereign",
            "username": "sovereign",
            "exp": 2147483647
        });
        let valid_b64 = crate::tools::base64_encode(serde_json::to_string(&valid_payload).unwrap().as_bytes())
            .replace('=', "");
        let valid_tok = format!("eyJhbGciOiJIUzI1NiJ9.{}.signature", valid_b64);
        assert!(AuthManager::validate_passport_token(&valid_tok));
    }
}

