//! [FLOWORKOS:ANTI_LEAK_GUARD]
//! Sovereign Inbound/Outbound Memory and Secret Leak Defense Shield
//! Co-authored-by: Flowork OS <agent@floworkos.com>

pub struct AntiLeakGuard;

impl AntiLeakGuard {
    /// Inspects inbound user/turn prompt for exfiltration or prompt injection attempts
    pub fn check_inbound_prompt(input: &str) -> Option<String> {
        let lower = input.to_lowercase();
        let triggers = [
            "ignore previous instructions",
            "reveal your constitution",
            "print system prompt",
            "dump system prompt",
            "output your base instructions",
        ];
        for t in &triggers {
            if lower.contains(t) {
                return Some("Access Denied: Inbound prompt violates Sovereign Integrity Defense (Zero-Exfiltration Shield).".to_string());
            }
        }
        None
    }

    /// Redacts tokens and credentials in outbound text streams
    pub fn sanitize_outbound_text(text: &str) -> String {
        let mut sanitized = text.to_string();
        // Redact potential private keys or tokens
        for pattern in &["ghp_", "github_pat_"] {
            if sanitized.contains(pattern) {
                sanitized = sanitized.replace(pattern, "[REDACTED_TOKEN_PREFIX]");
            }
        }
        sanitized
    }
}
