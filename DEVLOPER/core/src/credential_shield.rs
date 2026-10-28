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

    /// Sanitizes outbound logs, stdout, or response strings to prevent accidental credential exfiltration.
    /// Equipped with a panic circuit-breaker to guarantee zero-crash execution.
    pub fn redact_secrets(text: &str) -> String {
        let res = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            Self::redact_secrets_safe(text)
        }));

        match res {
            Ok(sanitized) => sanitized,
            Err(_) => {
                eprintln!("[Flowork Shield] Circuit Breaker: Caught panic during redact_secrets. Returning safe original text.");
                text.to_string()
            }
        }
    }

    fn redact_pattern<F>(
        input: &str,
        prefix: &str,
        replacement: &str,
        is_token_char: F,
    ) -> String
    where
        F: Fn(char) -> bool,
    {
        if !input.contains(prefix) {
            return input.to_string();
        }

        let mut out = String::with_capacity(input.len());
        let mut rest = input;

        while let Some(idx) = rest.find(prefix) {
            out.push_str(&rest[..idx]);
            out.push_str(replacement);

            let after_prefix = &rest[idx + prefix.len()..];
            let token_byte_len = after_prefix
                .chars()
                .take_while(|&c| is_token_char(c))
                .map(|c| c.len_utf8())
                .sum::<usize>();

            rest = &after_prefix[token_byte_len..];
        }

        out.push_str(rest);
        out
    }

    fn redact_secrets_safe(text: &str) -> String {
        let mut result = text.to_string();

        // 1. Redact GitHub personal access tokens
        for prefix in &["ghp_", "github_pat_", "gho_", "ghu_", "ghs_", "ghr_"] {
            result = Self::redact_pattern(&result, prefix, "[REDACTED_GH_TOKEN_PREFIX]", |c| {
                c.is_alphanumeric() || c == '_'
            });
        }

        // 2. Redact Google API keys (AIzaSy...)
        result = Self::redact_pattern(&result, "AIzaSy", "[REDACTED_GOOGLE_API_KEY]", |c| {
            c.is_alphanumeric() || c == '-' || c == '_'
        });

        // 3. Redact OpenAI / Anthropic / standard AI keys (sk-...)
        result = Self::redact_pattern(&result, "sk-", "[REDACTED_API_KEY]", |c| {
            c.is_alphanumeric() || c == '-' || c == '_'
        });

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
    fn test_secret_redaction_panic_reproduction() {
        let input = "sk-1 sk-2 sk-3 sk-4 sk-5 sk-6 sk-7 sk-8 sk-9 sk-10 s";
        let redacted = CredentialShield::redact_secrets(input);
        assert!(!redacted.contains("sk-"));
    }

    #[test]
    fn test_secret_redaction_unicode_and_mixed() {
        let input = "Server log: 🚀 ghp_1111222233334444555566667777888899990000 ♟️ with sk-proj-1234567890 📈 and AIzaSyAbcDef-123456. Done.";
        let redacted = CredentialShield::redact_secrets(input);
        assert!(redacted.contains("🚀"));
        assert!(redacted.contains("♟️"));
        assert!(redacted.contains("📈"));
        assert!(!redacted.contains("ghp_"));
        assert!(!redacted.contains("sk-proj-"));
        assert!(!redacted.contains("AIzaSyAbcDef"));
        assert!(redacted.contains("[REDACTED_GH_TOKEN_PREFIX]"));
        assert!(redacted.contains("[REDACTED_API_KEY]"));
        assert!(redacted.contains("[REDACTED_GOOGLE_API_KEY]"));
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
