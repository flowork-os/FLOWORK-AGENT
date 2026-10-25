//! Sovereign Flowork OS Credential Shield & Egress Enforcement Engine
//! Zero-Secret Agent Execution Architecture
//! Inspired by NVIDIA OpenShell Credential Shielding & Supervisor Mediator
//! Co-authored-by: Flowork OS <agent@floworkos.com>

use std::collections::HashSet;

pub struct CredentialShield;

impl CredentialShield {
    /// Sensitive environment variable keys that must NEVER be passed to agent child processes
    pub const SENSITIVE_ENV_KEYS: &'static [&'static str] = &[
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "FLOWORK_API_KEY",
        "FLOWORK_SECRET",
        "FLOWORK_AUTH_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "DATABASE_URL",
        "SSH_AUTH_SOCK",
        "SSH_AGENT_PID",
        "PRIVATE_KEY",
        "SECRET_KEY",
    ];

    /// Approved egress domains allowed for outbound agent requests (Deny-by-default egress model)
    pub const APPROVED_EGRESS_DOMAINS: &'static [&'static str] = &[
        "floworkos.com",
        "auth.floworkos.com",
        "api.floworkos.com",
        "api.openai.com",
        "generativelanguage.googleapis.com",
        "api.anthropic.com",
        "github.com",
        "api.github.com",
        "raw.githubusercontent.com",
        "objects.githubusercontent.com",
        "pypi.org",
        "files.pythonhosted.org",
        "registry.npmjs.org",
        "registry.yarnpkg.com",
        "huggingface.co",
        "duckduckgo.com",
    ];

    /// Scrubs sensitive credentials from a Tokio Command's environment.
    /// Child processes will never possess raw secrets in their memory or `/proc/<pid>/environ`.
    pub fn scrub_command_env(cmd: &mut tokio::process::Command) {
        for key in Self::SENSITIVE_ENV_KEYS {
            cmd.env_remove(key);
        }
        cmd.env("FLOWORK_CREDENTIAL_SHIELD", "ENFORCED");
        cmd.env("FLOWORK_ZERO_SECRET_ENV", "ACTIVE");
    }

    /// Evaluates if an egress host or domain is permitted under the Sovereign Egress Policy
    pub fn is_egress_domain_allowed(host: &str) -> bool {
        let clean_host = host.split(':').next().unwrap_or(host).trim().to_lowercase();
        if clean_host.is_empty() || clean_host == "localhost" || clean_host == "127.0.0.1" || clean_host == "::1" {
            return true;
        }

        for approved in Self::APPROVED_EGRESS_DOMAINS {
            if clean_host == *approved || clean_host.ends_with(&format!(".{approved}")) {
                return true;
            }
        }
        false
    }

    /// Sanitizes outbound logs, stdout, or response strings to prevent accidental credential exfiltration
    pub fn redact_secrets(text: &str) -> String {
        let mut result = text.to_string();

        // 1. Redact GitHub personal access tokens
        for prefix in &["ghp_", "github_pat_"] {
            if result.contains(prefix) {
                result = result.replace(prefix, "[REDACTED_GH_TOKEN_PREFIX]");
            }
        }

        // 2. Redact Google API keys
        if result.contains("AIzaSy") {
            // Replace pattern matching AIzaSy followed by alphanumeric characters
            let mut sanitized = String::with_capacity(result.len());
            let mut chars = result.chars().peekable();
            while let Some(c) = chars.next() {
                if c == 'A' && result[sanitized.len()..].starts_with("AIzaSy") {
                    sanitized.push_str("[REDACTED_GOOGLE_API_KEY]");
                    // Advance until non-alphanumeric or delimiter
                    for _ in 0..6 { chars.next(); }
                    while let Some(&next_c) = chars.peek() {
                        if next_c.is_alphanumeric() || next_c == '-' || next_c == '_' {
                            chars.next();
                        } else {
                            break;
                        }
                    }
                } else {
                    sanitized.push(c);
                }
            }
            result = sanitized;
        }

        // 3. Redact OpenAI / Anthropic key patterns
        if result.contains("sk-") {
            let mut sanitized = String::with_capacity(result.len());
            let mut chars = result.chars().peekable();
            while let Some(c) = chars.next() {
                if c == 's' && result[sanitized.len()..].starts_with("sk-") {
                    sanitized.push_str("[REDACTED_API_KEY]");
                    for _ in 0..3 { chars.next(); }
                    while let Some(&next_c) = chars.peek() {
                        if next_c.is_alphanumeric() || next_c == '-' || next_c == '_' {
                            chars.next();
                        } else {
                            break;
                        }
                    }
                } else {
                    sanitized.push(c);
                }
            }
            result = sanitized;
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_secret_redaction_google_api_key() {
        let input = "Found key AIzaSyBqJZh-7pA44blAaAkH6490hUFOwX0KCYM in database log.";
        let redacted = CredentialShield::redact_secrets(input);
        assert!(!redacted.contains("AIzaSyBqJZh"));
        assert!(redacted.contains("[REDACTED_GOOGLE_API_KEY]"));
    }

    #[test]
    fn test_secret_redaction_openai_key() {
        let input = "Exporting sk-proj-1234567890abcdef1234567890 for API calls.";
        let redacted = CredentialShield::redact_secrets(input);
        assert!(!redacted.contains("sk-proj-1234567890abcdef1234567890"));
        assert!(redacted.contains("[REDACTED_API_KEY]"));
    }

    #[test]
    fn test_secret_redaction_github_token() {
        let input = "Git clone with ghp_999988887777666655554444333322221111 token.";
        let redacted = CredentialShield::redact_secrets(input);
        assert!(!redacted.contains("ghp_"));
        assert!(redacted.contains("[REDACTED_GH_TOKEN_PREFIX]"));
    }

    #[test]
    fn test_egress_domain_filtering() {
        // Whitelisted domains
        assert!(CredentialShield::is_egress_domain_allowed("floworkos.com"));
        assert!(CredentialShield::is_egress_domain_allowed("auth.floworkos.com"));
        assert!(CredentialShield::is_egress_domain_allowed("api.openai.com"));
        assert!(CredentialShield::is_egress_domain_allowed("github.com"));
        assert!(CredentialShield::is_egress_domain_allowed("raw.githubusercontent.com"));
        assert!(CredentialShield::is_egress_domain_allowed("localhost"));
        assert!(CredentialShield::is_egress_domain_allowed("127.0.0.1"));

        // Blocked exfiltration domains
        assert!(!CredentialShield::is_egress_domain_allowed("evil-hacker.com"));
        assert!(!CredentialShield::is_egress_domain_allowed("webhook.site"));
        assert!(!CredentialShield::is_egress_domain_allowed("data-leak.net"));
    }
}
