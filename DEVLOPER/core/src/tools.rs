// [FL_INDEX: always include trigger_control sealed tools | COT: Ensure trigger_control always appears in sealed tools lookup in tools.rs | AT: 2026-10-21T17:24:36Z]
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::process::Command;

/// Security Guardian: Ensures files or code containing @lock or @frozen cannot be tampered with
pub fn is_locked_file(path: &Path) -> bool {
    if !path.exists() {
        return false;
    }
    if let Ok(content) = std::fs::read_to_string(path) {
        if content.contains("@lock") || content.contains("@frozen") {
            return true;
        }
    }
    false
}

/// Normalizes path strings across OS (Windows \ vs Unix /)
pub fn normalize_path_str(p: &str) -> String {
    let trimmed = p.trim().trim_matches('\'').trim_matches('"');
    #[cfg(target_os = "windows")]
    {
        trimmed.replace('/', "\\")
    }
    #[cfg(not(target_os = "windows"))]
    {
        trimmed.replace('\\', "/")
    }
}

/// Normalizes CRLF and LF line endings to standard LF for resilient matching
pub fn normalize_crlf_to_lf(s: &str) -> String {
    s.replace("\r\n", "\n")
}

/// Safely truncates a string at a valid UTF-8 character boundary up to max_bytes
pub fn safe_truncate_str(text: &str, max_bytes: usize) -> &str {
    if text.len() <= max_bytes {
        return text;
    }
    let mut boundary = max_bytes;
    while boundary > 0 && !text.is_char_boundary(boundary) {
        boundary -= 1;
    }
    &text[..boundary]
}

/// Safely extracts the tail of a string at a valid UTF-8 character boundary
pub fn safe_tail_str(text: &str, max_bytes: usize) -> &str {
    if text.len() <= max_bytes {
        return text;
    }
    let mut start = text.len().saturating_sub(max_bytes);
    while start < text.len() && !text.is_char_boundary(start) {
        start += 1;
    }
    &text[start..]
}

/// Safely slices a string within [start..end] at valid UTF-8 character boundaries
#[allow(dead_code)]
pub fn safe_slice_str(text: &str, mut start: usize, mut end: usize) -> &str {
    if text.is_empty() {
        return "";
    }
    start = start.min(text.len());
    end = end.min(text.len());
    if start >= end {
        return "";
    }
    while start < text.len() && !text.is_char_boundary(start) {
        start += 1;
    }
    while end > start && !text.is_char_boundary(end) {
        end -= 1;
    }
    if start >= end {
        ""
    } else {
        &text[start..end]
    }
}

/// Truncates observation middle if exceeds token budget, keeping head and tail safely at char boundaries
pub fn truncate_observation(text: &str, max_len: usize) -> (String, bool) {
    if text.len() <= max_len {
        return (text.to_string(), false);
    }
    let head_target = max_len * 3 / 5;
    let tail_target = max_len * 2 / 5;
    let head = safe_truncate_str(text, head_target);
    let tail = safe_tail_str(text, tail_target);
    let omitted = text.len().saturating_sub(head.len() + tail.len());
    let truncated = format!("{}\n\n... [TRUNCATED: {} bytes omitted for token economy. Full output logged on disk] ...\n\n{}", head, omitted, tail);
    (truncated, true)
}

/// Sovereign Step Status Formatter
#[allow(dead_code)]
pub fn format_step_status(status: &str, error: Option<&str>, is_tool_call: bool) -> String {
    match status {
        "CANCELED" | "FLWCTX_STEP_STATUS_CANCELED" | "CORTEX_STEP_STATUS_CANCELED" => {
            format!("[LANGKAH DIBATALKAN] {}", error.unwrap_or("Dibatalkan oleh sistem atau pengguna"))
        },
        "ERROR" | "FLWCTX_STEP_STATUS_ERROR" | "CORTEX_STEP_STATUS_ERROR" => {
            format!("[GALAT EKSEKUSI TERDETEKSI] {}", error.unwrap_or("Galat tidak terduga pada eksekusi"))
        },
        "INVALID" | "FLWCTX_STEP_STATUS_INVALID" | "CORTEX_STEP_STATUS_INVALID" => {
            if is_tool_call {
                format!("[PEMANGGILAN TIDAK VALID] Format argumen ditolak: {}", error.unwrap_or("Format argumen tidak sesuai skema"))
            } else {
                format!("[GALAT VALIDASI LANGKAH] {}", error.unwrap_or("Validasi langkah gagal"))
            }
        },
        "PENDING" | "RUNNING" | "FLWCTX_STEP_STATUS_PENDING" | "FLWCTX_STEP_STATUS_RUNNING"
        | "CORTEX_STEP_STATUS_PENDING" | "CORTEX_STEP_STATUS_RUNNING" => {
            "[STATUS PROSES] Langkah dieksekusi di latar belakang...".to_string()
        },
        "WAITING" | "FLWCTX_STEP_STATUS_WAITING" | "CORTEX_STEP_STATUS_WAITING" => {
            "[MENUNGGU OTORISASI USER] Menunggu persetujuan eksplisit pengguna.".to_string()
        },
        "DONE" | "FLWCTX_STEP_STATUS_DONE" | "CORTEX_STEP_STATUS_DONE" => String::new(),
        _ => format_template_error(&format!("Status Langkah Flowork Tidak Dikenal: {}", status)),
    }
}

/// Sovereign Template Error Formatter
#[allow(dead_code)]
pub fn format_template_error(description: &str) -> String {
    format!("<GALAT_TEMPLATE_FLOWORK:{}>", description)
}

/// Sovereign Terminal Stdin Classifier
pub fn classify_terminal_waiting_input(output: &str) -> (bool, String) {
    let lower = output.to_lowercase();
    let is_waiting = lower.contains("enter password:")
        || lower.contains("password for")
        || lower.contains("kata sandi")
        || lower.contains("are you sure")
        || lower.contains("(y/n)")
        || lower.contains("[y/n]")
        || lower.contains("press enter to continue")
        || lower.contains("tekan enter")
        || output.trim_end().ends_with(">>>")
        || output.trim_end().ends_with("irb>");

    let is_not_waiting = lower.contains("compiling")
        || lower.contains("building")
        || lower.contains("downloading")
        || lower.contains("uploading")
        || lower.contains("pausing")
        || lower.contains("sleep")
        || lower.contains("running test");

    if is_waiting && !is_not_waiting {
        let reason = if lower.contains("password") || lower.contains("sandi") {
            "Perintah meminta masukan kata sandi otentikasi."
        } else if lower.contains("(y/n)") || lower.contains("are you sure") {
            "Perintah meminta konfirmasi persetujuan (y/n)."
        } else if lower.contains("press enter") || lower.contains("tekan enter") {
            "Perintah meminta penekanan tombol ENTER untuk melanjutkan."
        } else {
            "Perintah aktif meminta masukan interaktif pada konsol stdin."
        };
        (true, format!("YA. {}", reason))
    } else {
        (false, "TIDAK. Perintah sedang memproses atau tidak menunggu masukan stdin.".to_string())
    }
}

/// Cross-Platform Shell Command Builder (Git Bash or Powershell on Windows, bash/sh on Unix/Linux/macOS)
pub fn get_platform_shell(cwd: &Path, cmd: &str) -> Command {
    #[cfg(target_os = "windows")]
    {
        // 1. Prefer Git Bash if available for maximum POSIX command compatibility (grep, rm -rf, touch, etc.)
        let bash_bin = ["C:\\Program Files\\Git\\bin\\bash.exe", "C:\\Program Files (x86)\\Git\\bin\\bash.exe"]
            .iter()
            .find(|p| Path::new(p).exists())
            .map(|s| s.to_string())
            .or_else(|| {
                if let Ok(path) = std::env::var("PATH") {
                    for p in std::env::split_paths(&path) {
                        let b = p.join("bash.exe");
                        if b.exists() {
                            return Some(b.to_string_lossy().to_string());
                        }
                    }
                }
                None
            });

        if let Some(b) = bash_bin {
            let mut command = Command::new(b);
            command.arg("-c").arg(cmd);
            command.current_dir(cwd);
            command.kill_on_drop(true);
            return command;
        }

        // 2. Default to native PowerShell with Bypass Execution Policy
        let mut command = Command::new("powershell.exe");
        command.args(["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", cmd]);
        command.current_dir(cwd);
        command.kill_on_drop(true);
        command
    }
    #[cfg(not(target_os = "windows"))]
    {
        let shell = if Path::new("/bin/bash").exists() {
            "/bin/bash"
        } else {
            "/bin/sh"
        };
        let mut command = Command::new(shell);
        command.arg("-c").arg(cmd);
        command.current_dir(cwd);
        command.kill_on_drop(true);
        command
    }
}

/// Standard high-performance Base64 encoder (RFC 4648) with zero external dependencies
pub fn base64_encode(data: &[u8]) -> String {
    const CHARSET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity((data.len() + 2) / 3 * 4);
    for chunk in data.chunks(3) {
        let b0 = chunk[0] as usize;
        let b1 = if chunk.len() > 1 { chunk[1] as usize } else { 0 };
        let b2 = if chunk.len() > 2 { chunk[2] as usize } else { 0 };

        let triple = (b0 << 16) | (b1 << 8) | b2;

        out.push(CHARSET[(triple >> 18) & 0x3F] as char);
        out.push(CHARSET[(triple >> 12) & 0x3F] as char);
        if chunk.len() > 1 {
            out.push(CHARSET[(triple >> 6) & 0x3F] as char);
        } else {
            out.push('=');
        }
        if chunk.len() > 2 {
            out.push(CHARSET[triple & 0x3F] as char);
        } else {
            out.push('=');
        }
    }
    out
}

/// Standard Base64 decoder with zero external dependencies
pub fn base64_decode(input: &str) -> Vec<u8> {
    let clean: Vec<u8> = input.bytes().filter(|b| !b.is_ascii_whitespace()).collect();
    let mut out = Vec::with_capacity(clean.len() * 3 / 4);
    let decode_val = |b: u8| -> Option<u8> {
        match b {
            b'A'..=b'Z' => Some(b - b'A'),
            b'a'..=b'z' => Some(b - b'a' + 26),
            b'0'..=b'9' => Some(b - b'0' + 52),
            b'+' => Some(62),
            b'/' => Some(63),
            _ => None,
        }
    };
    for chunk in clean.chunks(4) {
        if chunk.is_empty() { break; }
        let b0 = decode_val(chunk[0]).unwrap_or(0) as u32;
        let b1 = if chunk.len() > 1 { decode_val(chunk[1]).unwrap_or(0) as u32 } else { 0 };
        let b2 = if chunk.len() > 2 { decode_val(chunk[2]).unwrap_or(0) as u32 } else { 0 };
        let b3 = if chunk.len() > 3 { decode_val(chunk[3]).unwrap_or(0) as u32 } else { 0 };
        let triple = (b0 << 18) | (b1 << 12) | (b2 << 6) | b3;
        out.push(((triple >> 16) & 0xFF) as u8);
        if chunk.len() > 2 && chunk[2] != b'=' {
            out.push(((triple >> 8) & 0xFF) as u8);
        }
        if chunk.len() > 3 && chunk[3] != b'=' {
            out.push((triple & 0xFF) as u8);
        }
    }
    out
}

/// Immutable Anchor Tools that are permanently mounted
pub const ANCHOR_TOOLS: &[&str] = &[
    "run_command",
    "view_file",
    "write_to_file",
    "replace_file_content",
    "read_url_content",
    "schedule",
    "manage_task",
    "code_graph",
    "skill_control",
    "brain_control",
    "plugin_control",
    "screenshot",
    "generate_image",
    "search_web",
];

pub fn is_anchor_tool(name: &str) -> bool {
    let lower = name.to_lowercase();
    let norm = lower.trim_start_matches("default_api:").trim_start_matches("mcp_");
    ANCHOR_TOOLS.contains(&norm)
        || norm == "team_audit"
        || norm == "team_progress"
        || norm == "team_dispatch"
        || norm == "flow_team_dispatch"
        || norm == "agent_dispatch"
        || norm == "group_control"
        || norm == "flow_group_control"
        || norm == "manage_group"
        || norm == "sync_ecosystem"
        || norm == "flow_sync_ecosystem"
        || norm == "ecosystem_sync"
        || norm == "flow_exec"
        || norm == "flow_inspect"
        || norm == "flow_forge"
        || norm == "flow_splice"
        || norm == "flow_ingest"
        || norm == "flow_consult"
        || norm == "flow_delegate"
        || norm == "flow_swarm"
        || norm == "manage_subagents"
        || norm == "flow_dispatch"
        || norm == "send_message"
        || norm == "flow_schedule"
        || norm == "flow_taskmaster"
        || norm == "manage_task"
        || norm == "flow_search_tools"
        || norm == "code_graph"
        || norm == "fl_repo_map"
        || norm == "repo_map"
        || norm == "flow_code_graph"
        || norm == "flow_repo_map"
        || norm == "flow_skill"
        || norm == "create_skill"
        || norm == "create_skil"
        || norm == "skill_create"
        || norm == "brain_control"
        || norm == "flow_brain"
        || norm == "plugin_control"
        || norm == "flow_plugin"
        || norm == "screenshot"
        || norm == "flow_screenshot"
        || norm == "take_screenshot"
        || norm == "send_media"
        || norm == "flow_send_media"
        || norm == "send_file"
        || norm == "send_image"
        || norm == "send_video"
        || norm == "flow_lock"
        || norm == "lock"
        || norm == "app_publish"
        || norm == "flow_app_publish"
        || norm == "publish_app"
        || norm == "plugin_publish"
        || norm == "flow_publish"
        || norm == "publish_plugin"
        || norm == "search_web"
        || norm == "flow_recon"
        || norm == "team_audit"
        || norm == "flow_team_audit"
        || norm == "auditor"
        || norm == "team_auditor"
        || norm == "search_plugins"
        || norm == "trigger_control"
        || norm == "flow_trigger"
        || norm == "triger_control"
        || norm == "manage_trigger"
        || norm == "trigger"
        || norm == "search_triggers"
}

/// Whitelist of strictly 8 coordination tools (+ group/search lifecycle) for Agent Default in Group Mode
pub const GROUP_DEFAULT_COORDINATION_TOOLS: &[&str] = &[
    "team_dispatch",
    "ask_question",
    "write_to_file",
    "replace_file_content",
    "view_file",
    "search_web",
    "read_url_content",
    "brain_control",
    "group_control",
    "search_tools",
];

/// Checks whether a tool name belongs to the Sovereign coordination tools
pub fn is_coordination_tool(tool_name: &str) -> bool {
    let lower = tool_name.trim_start_matches("default_api:").trim_start_matches("mcp_").to_lowercase();
    let norm = if lower.starts_with("flow_") && lower != "flow_lock" {
        &lower[5..]
    } else {
        &lower
    };

    GROUP_DEFAULT_COORDINATION_TOOLS.contains(&norm)
        || norm == "team_dispatch"
        || norm == "flow_team_dispatch"
        || norm == "agent_dispatch"
        || norm == "flow_dispatch"
        || norm == "ask_question"
        || norm == "flow_consult"
        || norm == "write_to_file"
        || norm == "flow_forge"
        || norm == "create_file"
        || norm == "replace_file_content"
        || norm == "flow_splice"
        || norm == "edit_file"
        || norm == "view_file"
        || norm == "flow_inspect"
        || norm == "read_file"
        || norm == "search_web"
        || norm == "flow_recon"
        || norm == "read_url_content"
        || norm == "flow_ingest"
        || norm == "brain_control"
        || norm == "flow_brain"
        || norm == "group_control"
        || norm == "flow_group_control"
        || norm == "manage_group"
        || norm == "search_tools"
        || norm == "flow_search_tools"
        || norm == "find_tools"
}

/// Checks whether an agent belongs to the Sovereign Creator Forge family
#[allow(dead_code)]
pub fn is_creator_forge_agent(agent_id: &str) -> bool {
    let norm = agent_id.trim().to_lowercase().replace('_', "-");
    norm == "agent-creator"
        || norm == "skill-creator"
        || norm == "plugin-creator"
        || norm == "tools-creator"
        || norm == "trigger-creator"
        || norm == "agent_creator"
        || norm == "skill_creator"
        || norm == "plugin_creator"
        || norm == "tools_creator"
        || norm == "trigger_creator"
        || norm.starts_with("agent-agent-creator")
        || norm.starts_with("agent-skill-creator")
        || norm.starts_with("agent-plugin-creator")
        || norm.starts_with("agent-tools-creator")
        || norm.starts_with("agent-trigger-creator")
}

/// Checks whether a tool call represents a mutation/creation action for creator agents
#[allow(dead_code)]
pub fn is_creator_mutation_tool(tool_name: &str, args: &Value) -> bool {
    let lower = tool_name.trim_start_matches("default_api:").trim_start_matches("mcp_").to_lowercase();
    let norm = if lower.starts_with("flow_") && lower != "flow_lock" {
        &lower[5..]
    } else {
        &lower
    };

    match norm {
        "write_to_file" | "forge" | "create_file" => true,
        "replace_file_content" | "splice" | "edit_file" => true,
        "run_command" | "exec" | "terminal" => true,
        "create_skill" | "create_skil" | "skill_create" => true,
        "agent_control" | "agent" | "agents" | "flow_agent" | "manage_agent" => {
            let act = args.get("action").or_else(|| args.get("Action")).and_then(|v| v.as_str()).unwrap_or("");
            ["create", "scaffold", "new", "update"].contains(&act)
        },
        "skill_control" | "skill" | "skills" | "flow_skill" => {
            let act = args.get("action").or_else(|| args.get("Action")).and_then(|v| v.as_str()).unwrap_or("");
            ["create", "scaffold", "new"].contains(&act)
        },
        "plugin_control" | "plugin" | "plugins" | "flow_plugin" | "manage_plugin" => {
            let act = args.get("action").or_else(|| args.get("Action")).and_then(|v| v.as_str()).unwrap_or("");
            ["create", "scaffold", "new"].contains(&act)
        },
        "trigger_control" | "trigger" | "triggers" | "flow_trigger" | "manage_trigger" => {
            let act = args.get("action").or_else(|| args.get("Action")).and_then(|v| v.as_str()).unwrap_or("");
            ["create", "scaffold", "new"].contains(&act)
        },
        _ => false,
    }
}

/// Maps any of the official Flowork OS categories to its permission cluster
pub fn get_category_cluster(category: &str) -> u8 {
    let cat = crate::agents::AgentCategory::from_str_loose(category);
    match cat {
        crate::agents::AgentCategory::Healthcare
        | crate::agents::AgentCategory::Psychology
        | crate::agents::AgentCategory::Legal
        | crate::agents::AgentCategory::Education
        | crate::agents::AgentCategory::Business
        | crate::agents::AgentCategory::Marketing
        | crate::agents::AgentCategory::Advertising
        | crate::agents::AgentCategory::HumanResources
        | crate::agents::AgentCategory::ArtsMusicPoetry
        | crate::agents::AgentCategory::MetaphysicsFengShui
        | crate::agents::AgentCategory::CulinaryGastronomy
        | crate::agents::AgentCategory::SportsAthletics
        | crate::agents::AgentCategory::AgricultureEcology
        | crate::agents::AgentCategory::DiplomacyNegotiation
        | crate::agents::AgentCategory::HospitalityTourism
        | crate::agents::AgentCategory::MaritimeLogistics => 1,

        crate::agents::AgentCategory::Design
        | crate::agents::AgentCategory::MediaCreative
        | crate::agents::AgentCategory::ArchitectureSpatial => 2,

        crate::agents::AgentCategory::AutomationAdmin
        | crate::agents::AgentCategory::ScienceResearch
        | crate::agents::AgentCategory::Finance => 3,

        crate::agents::AgentCategory::CybersecurityForensics => 4,

        crate::agents::AgentCategory::Technology
        | crate::agents::AgentCategory::System => 5,
        crate::agents::AgentCategory::Core => 0,
    }
}

/// Fallback domain authorization by category cluster
pub fn is_tool_authorized_by_cluster(category: &str, tool_name: &str) -> bool {
    let lower = tool_name.trim_start_matches("default_api:").trim_start_matches("mcp_").to_lowercase();
    let norm = if lower.starts_with("flow_") && lower != "flow_lock" {
        &lower[5..]
    } else {
        &lower
    };

    let cluster = get_category_cluster(category);
    match cluster {
        0 => true,
        5 => true,
        1 => {
            if norm == "run_command" || norm == "terminal" || norm == "exec" || norm == "flow_lock" {
                return false;
            }
            let allowed = [
                "view_file", "write_to_file", "replace_file_content", "search_web",
                "read_url_content", "brain_control", "team_dispatch", "ask_question",
                "search_tools", "send_media", "code_graph", "fl_repo_map", "repo_map"
            ];
            allowed.iter().any(|&a| a == norm || a == lower)
        }
        2 => {
            let cat_enum = crate::agents::AgentCategory::from_str_loose(category);
            if cat_enum == crate::agents::AgentCategory::ArchitectureSpatial && (norm == "run_command" || norm == "render_visual") {
                return true;
            }
            if norm == "run_command" || norm == "flow_lock" {
                return false;
            }
            let allowed = [
                "view_file", "write_to_file", "replace_file_content", "screenshot", "flow_screenshot",
                "take_screenshot", "generate_image", "send_media", "render_visual", "brain_control",
                "team_dispatch", "ask_question", "search_tools", "search_web", "read_url_content",
                "code_graph", "fl_repo_map", "repo_map"
            ];
            if allowed.iter().any(|&a| a == norm || a == lower) {
                return true;
            }
            norm.starts_with("youtube_spy")
        }
        3 => {
            let allowed = [
                "run_command", "schedule", "manage_task", "view_file", "write_to_file",
                "replace_file_content", "search_web", "read_url_content", "brain_control",
                "team_dispatch", "ask_question", "search_tools", "code_graph", "fl_repo_map", "repo_map"
            ];
            allowed.iter().any(|&a| a == norm || a == lower)
        }
        4 => {
            let allowed = [
                "run_command", "read_bytes", "web_security_audit", "search_web",
                "view_file", "write_to_file", "replace_file_content", "brain_control",
                "team_dispatch", "ask_question", "search_tools", "code_graph", "fl_repo_map", "repo_map"
            ];
            allowed.iter().any(|&a| a == norm || a == lower)
        }
        _ => true,
    }
}

/// Central Sovereign Hybrid Tool Permission Gatekeeper
pub fn is_tool_authorized_for_agent(
    agent_id: &str,
    category: &str,
    is_group_mode: bool,
    tool_name: &str,
    manifest: Option<&crate::agents::AgentManifest>,
) -> bool {
    let lower_tool = tool_name.trim_start_matches("default_api:").trim_start_matches("mcp_").to_lowercase();
    let norm_tool = if lower_tool.starts_with("flow_") && lower_tool != "flow_lock" {
        &lower_tool[5..]
    } else {
        &lower_tool
    };

    if let Some(agent_manifest) = manifest {
        if agent_manifest.is_tool_locked(norm_tool) {
            return false;
        }
        if let Some(allowed) = agent_manifest.is_tool_allowed_by_guardian(norm_tool) {
            if !allowed {
                return false;
            }
        }
        if !agent_manifest.allowed_tools.is_empty() || !agent_manifest.default_tools.is_empty() {
            if agent_manifest.allowed_tools.iter().any(|t| t == "*") {
                return true;
            }
            let in_allowed = agent_manifest.allowed_tools.iter().any(|t| {
                let tl = t.to_lowercase();
                tl == lower_tool || tl == norm_tool
            });
            let in_default = agent_manifest.default_tools.iter().any(|t| {
                let tl = t.to_lowercase();
                tl == lower_tool || tl == norm_tool
            });
            if in_allowed || in_default {
                return true;
            }
            if norm_tool == "search_tools" || norm_tool == "ask_question" || norm_tool == "brain_control" || norm_tool == "team_progress" {
                return true;
            }
            if norm_tool == "team_dispatch" && is_group_mode {
                return true;
            }
            return false;
        }
    }

    // Spawning tools strictly banned in Team/Group mode (orchestrated by Swarm pipeline)
    if is_group_mode && (norm_tool == "invoke_subagent" || norm_tool == "invoke_spawn" || norm_tool == "define_subagent" || norm_tool == "manage_subagents" || norm_tool == "flow_delegate" || norm_tool == "flow_spawn") {
        return false;
    }

    // Sovereign Native Tools: In autonomous mode, all native tools are authorized by default unless explicitly locked/denied by guardian
    if crate::native_tools::is_native_binary_tool(norm_tool) {
        return true;
    }

    let is_default = agent_id == "default"
        || agent_id == "@default"
        || category == "CAT-015"
        || category == "universal_core_system"
        || category == "core";

    let is_skill_tool = norm_tool == "skill_control" || norm_tool == "create_skill" || norm_tool == "skill" || norm_tool == "skills";
    if is_skill_tool {
        if is_default && is_group_mode {
            return false;
        }
        return true;
    }

    if is_default && !is_group_mode {
        return true;
    }

    let is_tech = category == "CAT-005" || category == "technology" || category.contains("software");
    if is_tech {
        return true;
    }

    if is_default && is_group_mode {
        return is_coordination_tool(norm_tool);
    }

    is_tool_authorized_by_cluster(category, norm_tool)
}

/// Returns the complete Multi-OS Sovereign Function Declarations for Gemini LLM
pub fn get_sovereign_tool_declarations() -> Vec<Value> {
    let empty = HashSet::new();
    let engine_root = if let Ok(root) = std::env::var("FLOWORK_ENGINE_ROOT") {
        PathBuf::from(root)
    } else {
        std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
    };
    let canvas_tools_dir = engine_root.join("canvas-ui").join("tools");
    let mut decls = crate::native_tools::get_native_declarations(&empty, &canvas_tools_dir);
    if let Some(decl) = crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("screenshot") {
        decls.push(decl);
    }
    sanitize_declaration_batch(&mut decls);
    decls
}

/// Sovereign Schema Sanitizer & Circuit Breaker:
/// Recursively sanitizes any JSON schema definition to adhere strictly to Google Gemini OpenAPI 3.0 requirements.
/// Auto-heals:
/// 1. ARRAY missing 'items' -> auto-injects { "type": "STRING" } and recurses on items
/// 2. OBJECT missing 'properties' -> auto-injects {} and recurses on each nested property
/// 3. Normalizes missing, null, or non-standard types to uppercase Gemini types (STRING, INTEGER, NUMBER, BOOLEAN, ARRAY, OBJECT)
/// 4. Strips incompatible meta fields like $schema and additionalProperties that cause HTTP 400
/// 5. Validates required array to only reference keys that actually exist in properties
pub fn sanitize_json_schema(schema: &mut Value) {
    // Auto-detect flat property maps (e.g. { "param1": { "type": "STRING" }, ... })
    // and wrap them into a proper OpenAPI 3.0 schema: { "type": "OBJECT", "properties": { ... } }
    if let Some(schema_map) = schema.as_object_mut() {
        if !schema_map.contains_key("type") && !schema_map.contains_key("properties") && !schema_map.contains_key("items") {
            let is_flat_props = schema_map.values().any(|v| {
                v.is_object() && (v.get("type").is_some() || v.get("description").is_some())
            });
            if is_flat_props || !schema_map.is_empty() {
                let existing = schema_map.clone();
                schema_map.clear();
                schema_map.insert("type".to_string(), json!("OBJECT"));
                schema_map.insert("properties".to_string(), Value::Object(existing));
                schema_map.insert("required".to_string(), json!([]));
            }
        }
    }

    let schema_map = match schema.as_object_mut() {
        Some(m) => m,
        None => return,
    };

    // Strip forbidden or incompatible meta fields that break Gemini upstream
    schema_map.remove("$schema");
    schema_map.remove("additionalProperties");

    // Determine and normalize type to standard uppercase Gemini OpenAPI types
    let normalized_type = match schema_map.get("type").and_then(|t| t.as_str()) {
        Some(raw) => {
            let lower = raw.to_ascii_lowercase();
            match lower.as_str() {
                "string" | "str" | "text" => "STRING",
                "integer" | "int" => "INTEGER",
                "number" | "float" | "double" => "NUMBER",
                "boolean" | "bool" => "BOOLEAN",
                "array" | "list" => "ARRAY",
                "object" | "dict" | "map" => "OBJECT",
                _ => "STRING",
            }
        }
        None => {
            if schema_map.contains_key("properties") {
                "OBJECT"
            } else if schema_map.contains_key("items") {
                "ARRAY"
            } else {
                "STRING"
            }
        }
    };
    schema_map.insert("type".to_string(), json!(normalized_type));

    // Handle ARRAY: items is strictly mandatory in Gemini OpenAPI 3.0
    if normalized_type == "ARRAY" {
        if !schema_map.contains_key("items") || !schema_map["items"].is_object() {
            schema_map.insert("items".to_string(), json!({ "type": "STRING" }));
        } else if let Some(items_val) = schema_map.get_mut("items") {
            sanitize_json_schema(items_val);
        }
    }

    // Handle OBJECT: properties is strictly mandatory in Gemini OpenAPI 3.0
    if normalized_type == "OBJECT" {
        if !schema_map.contains_key("properties") || !schema_map["properties"].is_object() {
            schema_map.insert("properties".to_string(), json!({}));
        } else if let Some(props_val) = schema_map.get_mut("properties") {
            let mut valid_keys = HashSet::new();
            if let Some(props_obj) = props_val.as_object_mut() {
                for (k, child_val) in props_obj.iter_mut() {
                    sanitize_json_schema(child_val);
                    valid_keys.insert(k.clone());
                }
            }
            // Validate required array: only keep keys that actually exist in properties
            if let Some(req_arr) = schema_map.get_mut("required").and_then(|r| r.as_array_mut()) {
                req_arr.retain(|v| v.as_str().map(|s| valid_keys.contains(s)).unwrap_or(false));
            }
        }
    }
}

/// Sovereign Tool Sanitizer: Applies full recursive schema sanitization and intercepts gate injection
pub fn sanitize_tool_declaration(decl: &mut Value) {
    if !decl.is_object() {
        return;
    }
    // Ensure name and description are present and clean
    if decl.get("name").and_then(|v| v.as_str()).unwrap_or("").trim().is_empty() {
        decl["name"] = json!("unnamed_sovereign_tool");
    }
    if decl.get("description").and_then(|v| v.as_str()).is_none() {
        decl["description"] = json!("Sovereign Modular Tool");
    }

    // Root parameters must strictly be an OBJECT for Gemini function declaration
    if let Some(params) = decl.get_mut("parameters") {
        sanitize_json_schema(params);
        if let Some(p_obj) = params.as_object_mut() {
            p_obj.insert("type".to_string(), json!("OBJECT"));
            if !p_obj.contains_key("properties") || !p_obj["properties"].is_object() {
                p_obj.insert("properties".to_string(), json!({}));
            }
        } else {
            *params = json!({
                "type": "OBJECT",
                "properties": {}
            });
        }
    } else {
        decl["parameters"] = json!({
            "type": "OBJECT",
            "properties": {}
        });
    }

    inject_intercept_gate_schema(decl);

    if let Some(params) = decl.get_mut("parameters") {
        sanitize_json_schema(params);
        params["type"] = json!("OBJECT");
    }
}

/// Sovereign Circuit Breaker: Batch Sanitizer and Token Budget Protector
/// Deduplicates tools, sanitizes every declaration recursively, and protects upstream token quota
pub fn sanitize_declaration_batch(decls: &mut Vec<Value>) {
    let mut seen = HashSet::new();
    let mut sanitized = Vec::with_capacity(decls.len());

    for mut decl in decls.drain(..) {
        if let Some(name) = decl.get("name").and_then(|v| v.as_str()).map(|s| s.to_string()) {
            if seen.contains(&name) {
                continue;
            }
            seen.insert(name);
            sanitize_tool_declaration(&mut decl);
            sanitized.push(decl);
        }
    }

    // Token Economy & Quota Circuit Breaker:
    // If declarations exceed 64 tools, ensure Core 14 and anchor tools are prioritized
    const MAX_TOOL_DECLARATIONS_UPSTREAM: usize = 64;
    if sanitized.len() > MAX_TOOL_DECLARATIONS_UPSTREAM {
        let is_priority = |name: &str| -> bool {
            crate::native_tools::CORE_14_TOOLS.contains(&name)
                || is_anchor_tool(name)
                || name == "team_audit"
                || name == "search_tools"
                || name == "flow_lock"
        };

        let mut priority_tools = Vec::new();
        let mut regular_tools = Vec::new();

        for d in sanitized {
            let name = d.get("name").and_then(|v| v.as_str()).unwrap_or("");
            if is_priority(name) {
                priority_tools.push(d);
            } else {
                regular_tools.push(d);
            }
        }

        let remaining_slots = MAX_TOOL_DECLARATIONS_UPSTREAM.saturating_sub(priority_tools.len());
        regular_tools.truncate(remaining_slots);
        priority_tools.extend(regular_tools);
        *decls = priority_tools;
    } else {
        *decls = sanitized;
    }
}

/// Helper to inject mandatory 'reason' & 'keywords' schema into tool declaration
pub fn inject_intercept_gate_schema(decl: &mut Value) {
    if let Some(params) = decl.get_mut("parameters") {
        if let Some(props) = params.get_mut("properties") {
            if let Some(obj) = props.as_object_mut() {
                if !obj.contains_key("reason") {
                    obj.insert("reason".to_string(), json!({
                        "type": "STRING",
                        "description": "MANDATORY ON EVERY TOOL CALL: Clear, concise technical rationale in English explaining WHY you are calling this tool right now and what specific action it performs. MUST BE STRICTLY WRITTEN IN INDUSTRY-STANDARD ENGLISH (displayed live on HUD and used to recall up to 3 memories from .fl_brain)."
                    }));
                }
                if !obj.contains_key("keywords") {
                    obj.insert("keywords".to_string(), json!({
                        "type": "STRING",
                        "description": "MANDATORY ON EVERY TOOL CALL: AT LEAST 5 comma-separated technical domain keywords in English (e.g. 'sqlite, concurrency, wal, database, storage'). MUST BE STRICTLY WRITTEN IN ENGLISH. Used by Sovereign Skill Radar to search relevant skills across local storage and the official Flowork OS repository."
                    }));
                }
            }
        }
        if let Some(req_arr) = params.get_mut("required").and_then(|r| r.as_array_mut()) {
            if !req_arr.iter().any(|v| v.as_str() == Some("reason")) {
                req_arr.push(json!("reason"));
            }
            if !req_arr.iter().any(|v| v.as_str() == Some("keywords")) {
                req_arr.push(json!("keywords"));
            }
        } else if let Some(params_obj) = params.as_object_mut() {
            params_obj.insert("required".to_string(), json!(["reason", "keywords"]));
        }
        sanitize_json_schema(params);
    } else if let Some(decl_obj) = decl.as_object_mut() {
        decl_obj.insert("parameters".to_string(), json!({
            "type": "OBJECT",
            "properties": {
                "reason": {
                    "type": "STRING",
                    "description": "MANDATORY ON EVERY TOOL CALL: Clear, concise technical rationale in English explaining WHY you are calling this tool right now and what specific action it performs. MUST BE STRICTLY WRITTEN IN INDUSTRY-STANDARD ENGLISH (displayed live on HUD and used to recall up to 3 memories from .fl_brain)."
                },
                "keywords": {
                    "type": "STRING",
                    "description": "MANDATORY ON EVERY TOOL CALL: AT LEAST 5 comma-separated technical domain keywords in English (e.g. 'sqlite, concurrency, wal, database, storage'). MUST BE STRICTLY WRITTEN IN ENGLISH. Used by Sovereign Skill Radar to search relevant skills across local storage and the official Flowork OS repository."
                }
            },
            "required": ["reason", "keywords"]
        }));
    }
}

/// Dynamically resolves an external modular tool declaration from its manifest directory
pub fn resolve_external_tool_declaration(tool_dir: &Path) -> Option<Value> {
    let manifest_path = if tool_dir.join("manifest.json").exists() {
        Some(tool_dir.join("manifest.json"))
    } else if tool_dir.join("plugin.manifest.json").exists() {
        Some(tool_dir.join("plugin.manifest.json"))
    } else if tool_dir.join("tool.json").exists() {
        Some(tool_dir.join("tool.json"))
    } else {
        None
    };

    let mp = manifest_path?;
    let content = std::fs::read_to_string(&mp).ok()?;
    let manifest: Value = serde_json::from_str(&content).ok()?;

    let default_name = tool_dir.file_name()?.to_string_lossy().to_string();
    let name = manifest.get("name").or_else(|| manifest.get("id")).and_then(|v| v.as_str()).unwrap_or(&default_name).to_string();
    let desc = manifest.get("description").and_then(|v| v.as_str()).unwrap_or("Dynamic external modular tool").to_string();
    let raw_params = manifest.get("parameters").cloned().unwrap_or_else(|| json!({
        "type": "OBJECT",
        "properties": {}
    }));

    let params = if let Some(obj) = raw_params.as_object() {
        if !obj.contains_key("properties") && !obj.contains_key("type") {
            json!({
                "type": "OBJECT",
                "properties": obj.clone(),
                "required": []
            })
        } else {
            raw_params.clone()
        }
    } else {
        json!({
            "type": "OBJECT",
            "properties": {},
            "required": []
        })
    };

    let triggers = manifest.get("triggers");
    let kws = manifest.get("keywords")
        .or_else(|| triggers.and_then(|t| t.get("keywords")));
    let ex_kws = manifest.get("exclude_keywords")
        .or_else(|| manifest.get("exclude"))
        .or_else(|| triggers.and_then(|t| t.get("exclude")).or_else(|| triggers.and_then(|t| t.get("exclude_keywords"))));

    let mut decl = json!({
        "name": name,
        "description": desc,
        "parameters": params
    });
    if let Some(k) = kws {
        decl["keywords"] = k.clone();
    }
    if let Some(e) = ex_kws {
        decl["exclude_keywords"] = e.clone();
    }
    inject_intercept_gate_schema(&mut decl);
    Some(decl)
}

/// Helper to detect if text contains prominent Indonesian language indicators
pub fn contains_indonesian_indicators(text: &str) -> bool {
    let lower = text.to_lowercase();
    let words: Vec<&str> = lower
        .split(|c: char| !c.is_alphabetic())
        .map(|w| w.trim())
        .filter(|w| !w.is_empty())
        .collect();

    let id_markers = [
        "dan", "atau", "untuk", "dengan", "yang", "dari", "adalah",
        "pada", "bisa", "saya", "kamu", "kita", "mereka", "akan", "sudah", "belum", "tidak",
        "bukan", "hanya", "juga", "karena", "agar", "supaya", "oleh", "tentang", "sebagai",
        "sampai", "setelah", "sebelum", "buat", "kalau", "biar", "bikin",
        "lihat", "baca", "tulis", "ganti", "jalankan", "hapus", "cari", "kirim", "ambil", "periksa",
        "menggunakan", "menjalankan", "memeriksa", "mengedit", "menulis", "membuat", "melihat"
    ];

    words.iter().any(|w| id_markers.contains(w))
}

/// Helper to count keywords in comma, semicolon, newline, or whitespace separated text
pub fn count_keywords(text: &str) -> usize {
    if text.contains(',') || text.contains(';') || text.contains('\n') {
        text.split(|c: char| c == ',' || c == ';' || c == '\n')
            .map(|s| s.trim())
            .filter(|s| !s.is_empty())
            .count()
    } else {
        text.split_whitespace()
            .map(|s| s.trim())
            .filter(|s| !s.is_empty())
            .count()
    }
}

/// Dynamically resolves the tools directory across Engine Body and Workspace
pub fn resolve_tools_dir() -> PathBuf {
    if let Ok(root) = std::env::var("FLOWORK_ENGINE_ROOT") {
        let p = PathBuf::from(root).join("tools");
        if p.is_dir() {
            return p;
        }
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            let mut cur = dir.to_path_buf();
            for _ in 0..6 {
                let t = cur.join("tools");
                if t.is_dir() {
                    return t;
                }
                let ft = cur.join("flowork").join("tools");
                if ft.is_dir() {
                    return ft;
                }
                if let Some(p) = cur.parent() {
                    cur = p.to_path_buf();
                } else {
                    break;
                }
            }
        }
    }
    if let Ok(cur) = std::env::current_dir() {
        let mut c = cur;
        for _ in 0..4 {
            let t = c.join("tools");
            if t.is_dir() {
                return t;
            }
            if let Some(p) = c.parent() {
                c = p.to_path_buf();
            } else {
                break;
            }
        }
    }
    std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")).join("tools")
}

/// Returns active tools matching mounted set
pub fn get_active_tool_declarations(mounted_set: &HashSet<String>) -> Vec<Value> {
    // SOVEREIGN 6 ARCHITECTURE: Always exclude search_tools
    let mut filtered_mounted = mounted_set.clone();
    filtered_mounted.remove("search_tools");

    let tools_dir = resolve_tools_dir();
    let engine_root = if let Ok(root) = std::env::var("FLOWORK_ENGINE_ROOT") {
        PathBuf::from(root)
    } else {
        std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
    };
    let canvas_tools_dir = engine_root.join("canvas-ui").join("tools");
    let mut decls = crate::native_tools::get_native_declarations(mounted_set, &canvas_tools_dir);
    let mut seen: HashSet<String> = decls.iter()
        .filter_map(|d| d.get("name").and_then(|v| v.as_str()).map(|s| s.to_string()))
        .collect();

    if let Ok(entries) = std::fs::read_dir(&tools_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                let tool_id = path.file_name().unwrap_or_default().to_string_lossy().to_string();
                if tool_id.starts_with('.') || seen.contains(&tool_id) {
                    continue;
                }
                if tool_id == "agent_control"
                    || tool_id == "invoke_subagent"
                    || tool_id == "define_subagent"
                    || tool_id == "manage_subagents"
                    || tool_id == "send_message"
                {
                    continue;
                }
                if mounted_set.is_empty() || mounted_set.contains(&tool_id) {
                    if let Some(decl) = resolve_external_tool_declaration(&path) {
                        seen.insert(tool_id);
                        decls.push(decl);
                    }
                }
            }
        }
    }

    // 3. Scan Sealed Tools Enclave (cryptographically sealed inside binary)
    for tool_name in crate::sealed_tools::SealedToolsEnclave::all_sealed_tool_names() {
        if seen.contains(*tool_name) {
            continue;
        }
        if *tool_name == "agent_control"
            || *tool_name == "invoke_subagent"
            || *tool_name == "define_subagent"
            || *tool_name == "manage_subagents"
            || *tool_name == "send_message"
        {
            continue;
        }
        if mounted_set.is_empty() || mounted_set.contains(*tool_name) || *tool_name == "screenshot" || *tool_name == "trigger_control" {
            if let Some(decl) = crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration(tool_name) {
                seen.insert(tool_name.to_string());
                decls.push(decl);
            }
        }
    }

    sanitize_declaration_batch(&mut decls);
    decls
}

/// Dynamic tools available to subagents
#[allow(dead_code)]
pub fn get_active_subagent_tool_declarations(mounted_set: &HashSet<String>) -> Vec<Value> {
    get_active_tool_declarations(mounted_set)
}

/// Tools available to subagents
pub fn get_subagent_tool_declarations() -> Vec<Value> {
    let empty = HashSet::new();
    get_active_tool_declarations(&empty)
}

pub fn strip_frontmatter(content: &str) -> String {
    let trimmed = content.trim_start();
    if trimmed.starts_with("---") {
        if let Some(rest) = trimmed.strip_prefix("---") {
            if let Some(end_idx) = rest.find("---") {
                return rest[end_idx + 3..].trim().to_string();
            }
        }
    }
    trimmed.to_string()
}

/// Extracts clean canonical agent identifier from free-text roles, display strings, or agent names
pub fn extract_clean_agent_id(raw: &str) -> String {
    let trimmed = raw.trim();
    if let Some(start) = trimmed.find("(@") {
        if let Some(end) = trimmed[start..].find(')') {
            let inside = trimmed[start + 2..start + end].trim();
            if !inside.is_empty() {
                return inside.trim_start_matches("session-").trim_start_matches('@').to_lowercase();
            }
        }
    }
    if let Some(start) = trimmed.find('@') {
        let after = trimmed[start + 1..].trim();
        let end = after.find(|c: char| c.is_whitespace() || c == ')' || c == ']').unwrap_or(after.len());
        let ag = after[..end].trim();
        if !ag.is_empty() {
            return ag.trim_start_matches("session-").to_lowercase();
        }
    }
    let clean = trimmed.trim_start_matches("session-").trim_start_matches("agent-").to_lowercase();
    if clean.contains("coder") {
        "coder-specialist".to_string()
    } else if clean == "default" || clean.contains("orchestrat") || clean.contains("manager") {
        "default".to_string()
    } else if clean.contains("qa") || clean.contains("test") {
        "qa-engineer".to_string()
    } else if clean.contains("design") || clean.contains("ui") {
        "uiux-designer".to_string()
    } else if clean.is_empty() {
        "default".to_string()
    } else {
        clean
    }
}

#[derive(Debug, Clone)]
pub enum SubagentTurnOutput {
    Text(String),
    FunctionCall {
        name: String,
        args: Value,
        raw_parts: Vec<Value>,
    },
}

/// Pure External Pass-Through Tool Execution Engine
pub struct ToolEngine {
    pub workspace_root: PathBuf,
    pub scheduler: Option<Arc<crate::scheduler::SchedulerManager>>,
    pub discovery: Option<Arc<crate::discovery::PluginDiscovery>>,
    pub supervisor: Option<Arc<crate::supervisor::ProcessSupervisor>>,
    pub session_mounted_tools: Arc<tokio::sync::RwLock<HashMap<String, HashSet<String>>>>,
    pub session_pinned_skill: Arc<tokio::sync::RwLock<HashMap<String, String>>>,
    pub session_pinned_agent: Arc<tokio::sync::RwLock<HashMap<String, String>>>,
    pub session_uncommitted_creations: Arc<tokio::sync::RwLock<HashMap<String, Vec<String>>>>,
    pub session_github_research: Arc<tokio::sync::RwLock<HashMap<String, HashSet<String>>>>,
    pub active_sessions: Option<Arc<tokio::sync::RwLock<HashMap<String, crate::agent::SessionData>>>>,
}

impl ToolEngine {
    pub fn new(workspace_root: PathBuf) -> Self {
        Self {
            workspace_root,
            scheduler: None,
            discovery: None,
            supervisor: None,
            session_mounted_tools: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
            session_pinned_skill: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
            session_pinned_agent: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
            session_uncommitted_creations: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
            session_github_research: Arc::new(tokio::sync::RwLock::new(HashMap::new())),
            active_sessions: None,
        }
    }

    #[allow(dead_code)]
    pub fn with_active_sessions(mut self, sessions: Arc<tokio::sync::RwLock<HashMap<String, crate::agent::SessionData>>>) -> Self {
        self.active_sessions = Some(sessions);
        self
    }

    #[allow(dead_code)]
    pub fn with_mounted_tools_cache(mut self, cache: Arc<tokio::sync::RwLock<HashMap<String, HashSet<String>>>>) -> Self {
        self.session_mounted_tools = cache;
        self
    }

    #[allow(dead_code)]
    pub fn with_scheduler(mut self, scheduler: Arc<crate::scheduler::SchedulerManager>) -> Self {
        self.scheduler = Some(scheduler);
        self
    }

    #[allow(dead_code)]
    pub fn with_plugin_mesh(mut self, discovery: Arc<crate::discovery::PluginDiscovery>, supervisor: Arc<crate::supervisor::ProcessSupervisor>) -> Self {
        self.discovery = Some(discovery);
        self.supervisor = Some(supervisor);
        self
    }

    pub async fn get_mounted_tools(&self, session_id: &str) -> HashSet<String> {
        let map = self.session_mounted_tools.read().await;
        map.get(session_id).cloned().unwrap_or_default()
    }

    pub async fn mount_tools(&self, session_id: &str, tools: &[String]) -> HashSet<String> {
        let mut map = self.session_mounted_tools.write().await;
        let entry = map.entry(session_id.to_string()).or_default();
        for t in tools {
            entry.insert(t.clone());
        }
        entry.clone()
    }

    pub async fn unmount_tools(&self, session_id: &str, tools: &[String]) -> HashSet<String> {
        let mut map = self.session_mounted_tools.write().await;
        let entry = map.entry(session_id.to_string()).or_default();
        for t in tools {
            if !is_anchor_tool(t) {
                entry.remove(t);
            }
        }
        entry.clone()
    }

    pub async fn reset_to_anchor_tools(&self, session_id: &str) {
        let mut map = self.session_mounted_tools.write().await;
        map.remove(session_id);
    }

    pub async fn get_pinned_skill(&self, session_id: &str) -> Option<String> {
        let map = self.session_pinned_skill.read().await;
        map.get(session_id).cloned()
    }

    pub async fn set_pinned_skill(&self, session_id: &str, skill_id: String) {
        let mut map = self.session_pinned_skill.write().await;
        map.insert(session_id.to_string(), skill_id);
    }

    pub async fn clear_pinned_skill(&self, session_id: &str) {
        let mut map = self.session_pinned_skill.write().await;
        map.remove(session_id);
    }

    pub async fn get_pinned_agent(&self, session_id: &str) -> Option<String> {
        let map = self.session_pinned_agent.read().await;
        map.get(session_id).cloned()
    }

    pub async fn set_pinned_agent(&self, session_id: &str, agent_id: String) {
        let mut map = self.session_pinned_agent.write().await;
        map.insert(session_id.to_string(), agent_id);
    }

    pub async fn clear_pinned_agent(&self, session_id: &str) {
        let mut map = self.session_pinned_agent.write().await;
        map.remove(session_id);
    }

    pub async fn record_uncommitted_creation(&self, session_id: &str, pillar: &str, id: &str) {
        let mut map = self.session_uncommitted_creations.write().await;
        let entry = map.entry(session_id.to_string()).or_default();
        let record = format!("{}:{}", pillar, id);
        if !entry.contains(&record) {
            entry.push(record);
        }
    }

    pub async fn clear_uncommitted_creation(&self, session_id: &str, pillar: &str, id: &str) {
        let mut map = self.session_uncommitted_creations.write().await;
        if let Some(entry) = map.get_mut(session_id) {
            let record = format!("{}:{}", pillar, id);
            entry.retain(|r| r != &record);
        }
    }

    pub fn get_uncommitted_creations_sync(&self, session_id: &str) -> Vec<String> {
        if let Ok(map) = self.session_uncommitted_creations.try_read() {
            map.get(session_id).cloned().unwrap_or_default()
        } else {
            Vec::new()
        }
    }

    pub async fn record_github_research(&self, session_id: &str, target: &str) {
        let mut map = self.session_github_research.write().await;
        map.entry(session_id.to_string()).or_default().insert(target.to_string());
    }

    #[allow(dead_code)]
    pub async fn has_conducted_github_research(&self, session_id: &str) -> bool {
        let map = self.session_github_research.read().await;
        map.get(session_id).map(|s| !s.is_empty()).unwrap_or(false)
    }

    #[allow(dead_code)]
    pub async fn clear_github_research(&self, session_id: &str) {
        let mut map = self.session_github_research.write().await;
        map.remove(session_id);
    }

    pub fn resolve_path(&self, p: &str) -> PathBuf {
        let stripped = p.trim().trim_matches('\'').trim_matches('"').trim_start_matches("file://");
        let cleaned = crate::workspace::clean_verbatim_path(Path::new(stripped));
        let norm = normalize_path_str(&cleaned.to_string_lossy());
        let path = Path::new(&norm);
        let full = if path.is_absolute() {
            path.to_path_buf()
        } else {
            self.workspace_root.join(path)
        };
        let mut clean = PathBuf::new();
        for component in full.components() {
            match component {
                std::path::Component::ParentDir => {
                    clean.pop();
                }
                std::path::Component::CurDir => {}
                c => clean.push(c),
            }
        }
        clean
    }

    pub fn resolve_engine_root(&self) -> PathBuf {
        if self.workspace_root.starts_with(std::env::temp_dir()) {
            return self.workspace_root.clone();
        }

        if let Ok(root) = std::env::var("FLOWORK_ENGINE_ROOT") {
            let p = PathBuf::from(root);
            if p.exists() {
                if p.join("agents").exists() || p.join("skills").exists() {
                    return p;
                }
                if let Some(parent) = p.parent() {
                    if parent.join("agents").exists() || parent.join("skills").exists() {
                        return parent.to_path_buf();
                    }
                }
                return p;
            }
        }

        if let Ok(root) = std::env::var("FLOWORK_PORTABLE_ROOT") {
            let p = PathBuf::from(root);
            if p.exists() {
                if p.join("agents").exists() || p.join("skills").exists() {
                    return p;
                }
                if let Some(parent) = p.parent() {
                    if parent.join("agents").exists() || parent.join("skills").exists() {
                        return parent.to_path_buf();
                    }
                }
            }
        }

        if let Ok(exe) = std::env::current_exe() {
            if let Some(dir) = exe.parent() {
                if dir.join("skills").exists() || dir.join("agents").exists() {
                    return dir.to_path_buf();
                }
                if let Some(parent) = dir.parent() {
                    if parent.join("skills").exists() || parent.join("agents").exists() {
                        return parent.to_path_buf();
                    }
                    if let Some(gp) = parent.parent() {
                        if gp.join("skills").exists() || gp.join("agents").exists() {
                            return gp.to_path_buf();
                        }
                    }
                }
            }
        }

        if self.workspace_root.join("skills").exists() || self.workspace_root.join("agents").exists() {
            return self.workspace_root.clone();
        }
        if let Some(parent) = self.workspace_root.parent() {
            if parent.join("skills").exists() || parent.join("agents").exists() {
                return parent.to_path_buf();
            }
            let sib = parent.join("flowork");
            if sib.is_dir() && (sib.join("agents").exists() || sib.join("skills").exists()) {
                return sib;
            }
        }

        self.workspace_root.clone()
    }

    pub fn get_active_declarations(&self, mounted_set: &HashSet<String>) -> Vec<Value> {
        let mut decls = Vec::new();
        let mut seen = HashSet::new();
        let engine_root = self.resolve_engine_root();

        // 1. Native binary tools declarations from canvas-ui/tools
        let canvas_tools_dir = engine_root.join("canvas-ui").join("tools");
        let native_decls = crate::native_tools::get_native_declarations(mounted_set, &canvas_tools_dir);
        for d in native_decls {
            if let Some(n) = d.get("name").and_then(|v| v.as_str()) {
                seen.insert(n.to_string());
            }
            decls.push(d);
        }

        // 2. Scan external tools directories
        let candidate_dirs = [
            self.workspace_root.join("tools"),
            engine_root.join("tools"),
            resolve_tools_dir(),
        ];

        for c_dir in &candidate_dirs {
            if !c_dir.is_dir() {
                continue;
            }
            if let Ok(entries) = std::fs::read_dir(c_dir) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.is_dir() {
                        let tool_id = path.file_name().unwrap_or_default().to_string_lossy().to_string();
                        if tool_id.starts_with('.') || seen.contains(&tool_id) {
                            continue;
                        }
                        if mounted_set.is_empty() || mounted_set.contains(&tool_id) {
                            if let Some(decl) = resolve_external_tool_declaration(&path) {
                                seen.insert(tool_id);
                                decls.push(decl);
                            }
                        }
                    }
                }
            }
        }

        // 3. Scan Sealed Tools Enclave for actively mounted tools
        for tool_name in crate::sealed_tools::SealedToolsEnclave::all_sealed_tool_names() {
            if seen.contains(*tool_name) {
                continue;
            }
            if mounted_set.contains(*tool_name) || *tool_name == "screenshot" {
                if let Some(decl) = crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration(tool_name) {
                    seen.insert(tool_name.to_string());
                    decls.push(decl);
                }
            }
        }

        sanitize_declaration_batch(&mut decls);
        decls
    }

    pub fn get_active_declarations_for_session(
        &self,
        mounted_set: &HashSet<String>,
        _agent_id: &str,
        _category: &str,
        is_group_mode: bool,
        _manifest: Option<&crate::agents::AgentManifest>,
    ) -> Vec<Value> {
        let mut decls = self.get_active_declarations(mounted_set);

        if is_group_mode {
            // STRICT DOCTRINE: In TEAM / GROUP mode, subagent spawning tools MUST NOT appear!
            // Swarm coordination is handled inherently by the team orchestrator pipeline.
            decls.retain(|d| {
                let name = d.get("name").and_then(|v| v.as_str()).unwrap_or("");
                name != "invoke_subagent"
                    && name != "invoke_spawn"
                    && name != "define_subagent"
                    && name != "manage_subagents"
                    && name != "flow_delegate"
                    && name != "flow_spawn"
            });
        } else {
            // In SOLO / PERSONAL mode, subagent spawning tool (invoke_subagent) MUST appear!
            let has_subagent = decls.iter().any(|d| {
                let name = d.get("name").and_then(|v| v.as_str()).unwrap_or("");
                name == "invoke_subagent" || name == "invoke_spawn"
            });
            if !has_subagent {
                let canvas_tools_dir = self.resolve_engine_root().join("canvas-ui").join("tools");
                if let Some(mut decl) = crate::native_tools::resolve_canvas_tool_declaration(&canvas_tools_dir, "invoke_subagent") {
                    crate::tools::inject_intercept_gate_schema(&mut decl);
                    decls.push(decl);
                }
            }
        }

        decls
    }

    /// Pure Generic External Tool Dispatcher
    pub async fn execute_external_tool(&self, name: &str, args: &Value) -> Result<Value, String> {
        let raw_clean_name = name.trim().trim_start_matches("flow_").trim_start_matches("default_api:");
        let clean_name = match raw_clean_name {
            "plugin_publish" | "publish_plugin" | "flow_publish" => "app_publish",
            "plugin_control" | "flow_plugin" => "app_control",
            _ => raw_clean_name,
        };
        let engine_root = self.resolve_engine_root();
        if clean_name == "team_dispatch" {
            return self.execute_team_dispatch(args).await;
        }
        let mcp_script = engine_root.join("mcp").join("run.mjs");

        // 1. Explicit MCP Tool Call Routing (mcp_* or mcp_runner)
        if (clean_name.starts_with("mcp_") || clean_name == "mcp_runner") && mcp_script.exists() {
            let target_action = if clean_name == "mcp_runner" {
                args.get("action").and_then(|v| v.as_str()).unwrap_or("")
            } else {
                clean_name.trim_start_matches("mcp_")
            };
            let args_json = serde_json::to_string(args).unwrap_or_else(|_| "{}".to_string());
            let mut cmd = tokio::process::Command::new("node");
            cmd.arg(&mcp_script).arg(target_action).arg(&args_json);
            cmd.current_dir(&self.workspace_root)
               .env("FLOWORK_WORKSPACE", &self.workspace_root)
               .env("FLOWORK_ENGINE_ROOT", &engine_root);
            let output = cmd.output().await.map_err(|e| format!("Failed to spawn MCP runner: {e}"))?;
            let stdout = String::from_utf8_lossy(&output.stdout);
            let stderr = String::from_utf8_lossy(&output.stderr);
            if !output.status.success() {
                if let Ok(json_err) = serde_json::from_str::<Value>(&stdout) {
                    return Ok(json_err);
                }
                return Err(format!("MCP tool '{target_action}' failed (exit code: {:?}): {}", output.status.code(), stderr.trim()));
            }
            return if let Ok(json_val) = serde_json::from_str::<Value>(&stdout) {
                Ok(json_val)
            } else {
                Ok(json!({ "status": "SUCCESS", "output": stdout.trim() }))
            };
        }

        let tool_dir = if crate::sealed_tools::SealedToolsEnclave::is_sealed_tool(clean_name) {
            let sealed_base = crate::sealed_tools::SealedToolsEnclave::get_sealed_runtime_dir(&self.workspace_root)
                .map_err(|e| format!("Failed to resolve sealed tools runtime directory: {e}"))?;
            crate::sealed_tools::SealedToolsEnclave::extract_single_tool(clean_name, &sealed_base)
                .map_err(|e| format!("Failed to extract sealed tool '{clean_name}': {e}"))?
        } else {
            let candidate_dirs = [
                self.workspace_root.join("tools").join(name),
                self.workspace_root.join("tools").join(clean_name),
                engine_root.join("tools").join(name),
                engine_root.join("tools").join(clean_name),
                resolve_tools_dir().join(name),
                resolve_tools_dir().join(clean_name),
            ];

            if let Some(d) = candidate_dirs.iter().find(|d| d.exists()).cloned() {
                d
            } else if mcp_script.exists() && (clean_name.starts_with("chess_") || clean_name.starts_with("trade_") || clean_name.starts_with("website_intel_") || clean_name.starts_with("intel_") || clean_name.starts_with("youtube_") || clean_name.starts_with("websec_") || clean_name == "canvas_control" || clean_name == "flow_canvas_control") {
                // Route to MCP Runner directly for sidecar apps
                let args_json = serde_json::to_string(args).unwrap_or_else(|_| "{}".to_string());
                let mut cmd = tokio::process::Command::new("node");
                cmd.arg(&mcp_script).arg(clean_name).arg(&args_json);
                cmd.current_dir(&self.workspace_root)
                   .env("FLOWORK_WORKSPACE", &self.workspace_root)
                   .env("FLOWORK_ENGINE_ROOT", &engine_root);
                let output = cmd.output().await.map_err(|e| format!("Failed to spawn MCP runner for '{clean_name}': {e}"))?;
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                if !output.status.success() {
                    if let Ok(json_err) = serde_json::from_str::<Value>(&stdout) {
                        return Ok(json_err);
                    }
                    return Err(format!("MCP tool '{clean_name}' failed: {}", stderr.trim()));
                }
                return if let Ok(json_val) = serde_json::from_str::<Value>(&stdout) {
                    Ok(json_val)
                } else {
                    Ok(json!({ "status": "SUCCESS", "output": stdout.trim() }))
                };
            } else {
                return Err(format!("External tool '{name}' not found"));
            }
        };

        let (entry, runner_type) = if tool_dir.join("main.mjs").exists() {
            (tool_dir.join("main.mjs"), "node")
        } else if tool_dir.join("index.mjs").exists() {
            (tool_dir.join("index.mjs"), "node")
        } else if tool_dir.join("main.js").exists() {
            (tool_dir.join("main.js"), "node")
        } else if tool_dir.join("run.sh").exists() {
            (tool_dir.join("run.sh"), "bash")
        } else if tool_dir.join("main.sh").exists() {
            (tool_dir.join("main.sh"), "bash")
        } else if tool_dir.join("main.py").exists() {
            (tool_dir.join("main.py"), "python")
        } else if tool_dir.join("run.py").exists() {
            (tool_dir.join("run.py"), "python")
        } else {
            return Err(format!("Entrypoint script not found for tool '{name}' in {}", tool_dir.display()));
        };

        let args_json = serde_json::to_string(args).unwrap_or_else(|_| "{}".to_string());
        let mut cmd = match runner_type {
            "bash" => {
                if cfg!(target_os = "windows") {
                    let mut c = tokio::process::Command::new("cmd");
                    c.arg("/C").arg("bash").arg(&entry).arg("--params").arg(&args_json);
                    c
                } else {
                    let mut c = tokio::process::Command::new("bash");
                    c.arg(&entry).arg("--params").arg(&args_json);
                    c
                }
            },
            "python" => {
                let mut c = tokio::process::Command::new("python3");
                c.arg(&entry).arg("--params").arg(&args_json);
                c
            },
            _ => {
                let mut c = tokio::process::Command::new("node");
                c.arg(&entry).arg("--params").arg(&args_json);
                c
            }
        };

        cmd.current_dir(&self.workspace_root)
           .env("FLOWORK_WORKSPACE", &self.workspace_root)
           .env("FLOWORK_ENGINE_ROOT", &engine_root)
           .env("FLOWORK_TOOL_DIR", tool_dir)
           .env("FLOWORK_CO_AUTHOR", "Flowork OS <agent@floworkos.com>");

        let output = cmd.output().await.map_err(|e| format!("Failed to spawn external tool '{name}': {e}"))?;
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        if !output.status.success() {
            if let Ok(json_err) = serde_json::from_str::<Value>(&stdout) {
                return Ok(json_err);
            }
            return Err(format!("Tool '{name}' failed (exit code: {:?}): {}", output.status.code(), stderr.trim()));
        }

        if let Ok(json_val) = serde_json::from_str::<Value>(&stdout) {
            Ok(json_val)
        } else {
            Ok(json!({
                "status": "SUCCESS",
                "output": stdout.trim()
            }))
        }
    }

    fn resolve_hook_script(&self, base_name: &str) -> Option<PathBuf> {
        let engine_root = self.resolve_engine_root();
        #[cfg(target_os = "windows")]
        let exts = [".bat", ".cmd", ".ps1", ".sh"];
        #[cfg(not(target_os = "windows"))]
        let exts = [".sh", ".bash", ""];

        for ext in exts {
            let file_name = format!("{base_name}{ext}");
            let cand = engine_root.join("hooks").join(&file_name);
            if cand.exists() {
                return Some(cand);
            }
            let ws_cand = self.workspace_root.join("hooks").join(&file_name);
            if ws_cand.exists() {
                return Some(ws_cand);
            }
        }
        None
    }

    fn build_hook_command(&self, script: &Path, payload: &str) -> Option<tokio::process::Command> {
        let script_str = script.to_string_lossy().to_string();
        #[cfg(target_os = "windows")]
        {
            if script_str.ends_with(".bat") || script_str.ends_with(".cmd") {
                let mut c = tokio::process::Command::new("cmd");
                c.arg("/C").arg(script).arg(payload);
                c.current_dir(&self.workspace_root);
                return Some(c);
            } else if script_str.ends_with(".ps1") {
                let mut c = tokio::process::Command::new("powershell.exe");
                c.args(["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File"])
                    .arg(script)
                    .arg(payload);
                c.current_dir(&self.workspace_root);
                return Some(c);
            } else if script_str.ends_with(".sh") {
                // Check if bash interpreter is present on host
                let mut bash_candidates = vec![
                    "C:\\Program Files\\Git\\bin\\bash.exe".to_string(),
                    "C:\\Program Files (x86)\\Git\\bin\\bash.exe".to_string(),
                ];
                if let Ok(local_app) = std::env::var("LOCALAPPDATA") {
                    bash_candidates.push(format!("{local_app}\\Programs\\Git\\bin\\bash.exe"));
                }
                if let Ok(user_prof) = std::env::var("USERPROFILE") {
                    bash_candidates.push(format!("{user_prof}\\scoop\\shims\\bash.exe"));
                }
                let bash_path = bash_candidates
                    .iter()
                    .find(|p| Path::new(p).exists())
                    .cloned()
                    .or_else(|| {
                        if let Ok(path) = std::env::var("PATH") {
                            for p in std::env::split_paths(&path) {
                                let b = p.join("bash.exe");
                                if b.exists() {
                                    return Some(b.to_string_lossy().to_string());
                                }
                            }
                        }
                        None
                    });

                if let Some(b) = bash_path {
                    let mut c = tokio::process::Command::new(b);
                    c.arg(script).arg(payload);
                    c.current_dir(&self.workspace_root);
                    return Some(c);
                } else {
                    println!("[ToolEngine:Hook] ℹ️ Windows bash interpreter not found; skipping .sh hook gracefully: {}", script.display());
                    return None;
                }
            }
        }

        #[cfg(unix)]
        {
            let mut c = tokio::process::Command::new("bash");
            c.arg(script).arg(payload);
            c.current_dir(&self.workspace_root);
            return Some(c);
        }

        None
    }

    pub async fn execute_pre_tool_hook(&self, name: &str, args: &Value) -> Result<(), String> {
        let script = match self.resolve_hook_script("pre_tool") {
            Some(s) => s,
            None => return Ok(()),
        };

        let payload = json!({
            "tool": name,
            "args": args
        }).to_string();

        let mut cmd = match self.build_hook_command(&script, &payload) {
            Some(c) => c,
            None => return Ok(()),
        };

        let output = match tokio::time::timeout(tokio::time::Duration::from_millis(3000), cmd.output()).await {
            Ok(Ok(out)) => out,
            Ok(Err(e)) => {
                println!("[ToolEngine:Hook] ℹ️ pre_tool hook execution bypassed ({e})");
                return Ok(());
            }
            Err(_) => {
                println!("[ToolEngine:Hook] ⚠️ pre_tool hook timed out (3000ms limit)");
                return Ok(());
            }
        };

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            if cfg!(target_os = "windows") && (stderr.contains("not recognized") || stderr.contains("tidak dikenali")) {
                println!("[ToolEngine:Hook] ℹ️ Shell interpreter missing on Windows: {}", stderr.trim());
                return Ok(());
            }
            let code = output.status.code().unwrap_or(1);
            return Err(format!("Execution blocked by pre_tool hook (code {code}): {}", stderr.trim()));
        }

        Ok(())
    }

    pub async fn execute_post_tool_hook(&self, name: &str, result: Result<Value, String>) -> Result<Value, String> {
        let script = match self.resolve_hook_script("post_tool") {
            Some(s) => s,
            None => return result,
        };

        let payload = match &result {
            Ok(val) => json!({ "tool": name, "status": "SUCCESS", "output": val }).to_string(),
            Err(err) => json!({ "tool": name, "status": "ERROR", "error": err }).to_string(),
        };

        let mut cmd = match self.build_hook_command(&script, &payload) {
            Some(c) => c,
            None => return result,
        };

        let _ = tokio::time::timeout(tokio::time::Duration::from_millis(2000), cmd.output()).await;
        result
    }

    pub async fn execute(&self, name: &str, args: &Value) -> Result<Value, String> {
        let engine_root = self.resolve_engine_root();

        // 1. Lifecycle Hook: pre_tool
        self.execute_pre_tool_hook(name, args).await?;

        let res = if crate::native_tools::is_native_binary_tool(name) {
            crate::native_tools::execute_native_tool_with_discovery(name, args, &self.workspace_root, &engine_root, self.discovery.as_ref()).await
        } else {
            self.execute_external_tool(name, args).await
        };

        // 2. Lifecycle Hook: post_tool
        let res = self.execute_post_tool_hook(name, res).await?;

        // Intercept session state updates for skill_control and agent_control
        if name == "skill_control" {
            let action = args.get("action").and_then(|v| v.as_str()).unwrap_or("");
            let sess_id = args.get("session_id").and_then(|v| v.as_str());
            let skill_id = args.get("skill_id").and_then(|v| v.as_str());
            if let (Some(s_id), Some(sk_id)) = (sess_id, skill_id) {
                if action == "create" || action == "pin" {
                    self.set_pinned_skill(s_id, sk_id.to_string()).await;
                } else if action == "unpin" || action == "clear" {
                    self.clear_pinned_skill(s_id).await;
                }
            }
        } else if name == "agent_control" {
            let action = args.get("action").and_then(|v| v.as_str()).unwrap_or("");
            let sess_id = args.get("session_id").and_then(|v| v.as_str());
            let agent_id = args.get("agent_id").and_then(|v| v.as_str());
            if let (Some(s_id), Some(ag_id)) = (sess_id, agent_id) {
                if action == "pin" {
                    self.set_pinned_agent(s_id, ag_id.to_string()).await;
                } else if action == "unpin" || action == "clear" {
                    self.clear_pinned_agent(s_id).await;
                }
            }
        } else if name == "search_tools" || name == "tool_control" {
            let action = args.get("action").and_then(|v| v.as_str()).unwrap_or("");
            let sess_id = args.get("session_id").and_then(|v| v.as_str()).unwrap_or("default");
            if action == "mount" {
                if let Some(tools_arr) = args.get("tools").and_then(|v| v.as_array()) {
                    let tools_vec: Vec<String> = tools_arr.iter().filter_map(|x| x.as_str().map(|s| s.to_string())).collect();
                    self.mount_tools(sess_id, &tools_vec).await;
                }
            } else if action == "unmount" {
                if let Some(tools_arr) = args.get("tools").and_then(|v| v.as_array()) {
                    let tools_vec: Vec<String> = tools_arr.iter().filter_map(|x| x.as_str().map(|s| s.to_string())).collect();
                    self.unmount_tools(sess_id, &tools_vec).await;
                }
            }
        }

        // Automatic persistent recording to .fl_brain without requiring LLM manual work
        self.record_auto_fl_brain_journal(name, args, &res);

        Ok(res)
    }

    /// Automatically records tool execution reasons, keywords, and touched files to .fl_brain
    fn record_auto_fl_brain_journal(&self, name: &str, args: &Value, res: &Value) {
        let reason = args.get("reason").and_then(|v| v.as_str()).unwrap_or("").trim();
        let keywords = args.get("keywords").and_then(|v| v.as_str()).unwrap_or("").trim();

        let target_file_opt = args.get("TargetFile")
            .or_else(|| args.get("AbsolutePath"))
            .or_else(|| args.get("target_path"))
            .or_else(|| args.get("target_file"))
            .or_else(|| args.get("target_dir"))
            .and_then(|v| v.as_str());

        let now_secs = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let brain_dir = self.workspace_root.join(".fl_brain");
        let histories_dir = brain_dir.join("file_histories");

        // 1. Record file history if a target file was touched
        if let Some(target_file) = target_file_opt {
                let tf_clean = target_file.replace('\\', "/");
                if !target_file.is_empty() && !tf_clean.contains(".fl_brain") && !tf_clean.contains(".FL_BIN") {
                let _ = std::fs::create_dir_all(&histories_dir);
                let rel_path = if let Ok(stripped) = Path::new(target_file).strip_prefix(&self.workspace_root) {
                    stripped.to_string_lossy().to_string()
                } else {
                    target_file.to_string()
                };

                let clean_name = rel_path
                    .replace('\\', "/")
                    .replace('/', "__")
                    .replace(':', "");
                let history_file = histories_dir.join(format!("{}.md", clean_name));

                let status_label = if res.is_object() && res.get("status").and_then(|v| v.as_str()) == Some("ERROR") {
                    "FAILED"
                } else {
                    "SUCCESS"
                };

                let entry = format!(
                    "- [{}] Tool `{}` ({}) | Reason: {}\n  Keywords: {}\n",
                    now_secs, name, status_label, reason, keywords
                );

                use std::io::Write;
                if let Ok(mut f) = std::fs::OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open(&history_file)
                {
                    let _ = f.write_all(entry.as_bytes());
                }
            }
        }

        // 2. Record to activity journal
        if !reason.is_empty() || !keywords.is_empty() {
            let journal_dir = brain_dir.join("journal");
            let _ = std::fs::create_dir_all(&journal_dir);
            let journal_file = journal_dir.join("activity.jsonl");

            let record = json!({
                "timestamp": now_secs,
                "tool": name,
                "reason": reason,
                "keywords": keywords,
                "target": target_file_opt
            });

            use std::io::Write;
            // Sharding / Rotation: keep active activity.jsonl <= 50KB (~100 records)
            if let Ok(metadata) = std::fs::metadata(&journal_file) {
                if metadata.len() >= 50 * 1024 {
                    let mut shard_idx = 1;
                    loop {
                        let shard_file = journal_dir.join(format!("activity_part{:02}.jsonl", shard_idx));
                        if !shard_file.exists() {
                            let _ = std::fs::rename(&journal_file, &shard_file);
                            break;
                        }
                        shard_idx += 1;
                    }
                }
            }

            if let Ok(mut f) = std::fs::OpenOptions::new()
                .create(true)
                .append(true)
                .open(&journal_file)
            {
                let mut line = record.to_string();
                line.push('\n');
                let _ = f.write_all(line.as_bytes());
            }
        }
    }

    pub async fn execute_trigger_control(&self, args: &Value) -> Result<Value, String> {
        self.execute("trigger_control", args).await
    }

    pub async fn execute_team_dispatch(&self, args: &Value) -> Result<Value, String> {
        let action = args.get("action").and_then(|v| v.as_str()).unwrap_or("HANDOFF");
        let to_agent = args.get("to_agent").or_else(|| args.get("target_agent")).and_then(|v| v.as_str()).unwrap_or("");
        let summary = args.get("summary").and_then(|v| v.as_str()).unwrap_or("");
        let payload = args.get("payload").and_then(|v| v.as_str()).unwrap_or("");
        let status_proof = args.get("status_proof").and_then(|v| v.as_str()).unwrap_or("");

        let engine_root = self.resolve_engine_root();
        let swarm_dir = crate::ipc_router::resolve_swarmflow_dir(&engine_root, &self.workspace_root);
        let active_json_path = swarm_dir.join("active.json");
        let mut active_preset_id = "default".to_string();
        if active_json_path.exists() {
            if let Ok(c) = std::fs::read_to_string(&active_json_path) {
                if let Ok(v) = serde_json::from_str::<Value>(&c) {
                    if let Some(id_str) = v.get("activePresetId").and_then(|x| x.as_str()) {
                        active_preset_id = id_str.to_string();
                    }
                }
            }
        }

        let preset_file = swarm_dir.join(format!("{active_preset_id}.json"));

        // -------------------------------------------------------------------------
        // GATE 1: ATTRIBUTION & ATTESTATION PROOF OF WORK GATE
        // If artifacts are claimed, verify that every claimed file exists and > 0 bytes!
        // -------------------------------------------------------------------------
        if let Some(artifacts_arr) = args.get("artifacts").and_then(|v| v.as_array()) {
            for art in artifacts_arr {
                if let Some(art_str) = art.as_str() {
                    let art_clean = art_str.trim().trim_start_matches("file://");
                    if !art_clean.is_empty() {
                        let art_path = if std::path::Path::new(art_clean).is_absolute() {
                            PathBuf::from(art_clean)
                        } else {
                            self.workspace_root.join(art_clean)
                        };
                        if !art_path.exists() {
                            return Ok(json!({
                                "status": "ERROR",
                                "exit_code": 1,
                                "tool": "team_dispatch",
                                "error": format!("Attestation Gate Rejected: Claimed artifact '{}' does not exist on physical disk.", art_clean),
                                "output": format!("❌ [ATTESTATION GATE FAILURE] Artifact '{}' not found on disk. Create the file and verify exit code 0 before dispatching.", art_clean)
                            }));
                        }
                        if let Ok(meta) = std::fs::metadata(&art_path) {
                            if meta.len() == 0 {
                                return Ok(json!({
                                    "status": "ERROR",
                                    "exit_code": 1,
                                    "tool": "team_dispatch",
                                    "error": format!("Attestation Gate Rejected: Claimed artifact '{}' is 0 bytes (empty file).", art_clean),
                                    "output": format!("❌ [ATTESTATION GATE FAILURE] Artifact '{}' is empty (0 bytes). Genuine implementation required.", art_clean)
                                }));
                            }
                        }
                    }
                }
            }
        }

        // -------------------------------------------------------------------------
        // GATE 2: ROUTING ACL (CABLE VERIFICATION)
        // Validate that calling agent has a topological cable connecting to to_agent
        // -------------------------------------------------------------------------
        let mut permitted_targets: Vec<String> = Vec::new();
        let mut is_reverse_revision_allowed = false;
        let mut current_preset_name = active_preset_id.clone();

        if preset_file.exists() {
            if let Ok(c) = std::fs::read_to_string(&preset_file) {
                if let Ok(v) = serde_json::from_str::<Value>(&c) {
                    if let Some(n) = v.get("name").and_then(|x| x.as_str()) {
                        current_preset_name = n.to_string();
                    }

                    let mut node_to_agent: HashMap<String, String> = HashMap::new();
                    if let Some(nodes_arr) = v.get("nodes").and_then(|x| x.as_array()) {
                        for nd in nodes_arr {
                            let nid = nd.get("id").and_then(|x| x.as_str()).unwrap_or("");
                            let aid = nd.get("agentId").and_then(|x| x.as_str()).unwrap_or("");
                            if !nid.is_empty() && !aid.is_empty() {
                                node_to_agent.insert(nid.to_string(), aid.to_string());
                            }
                        }
                    }

                    if let Some(conn_arr) = v.get("connections").and_then(|x| x.as_array()) {
                        for conn in conn_arr {
                            let from_nid = conn.get("from").and_then(|x| x.as_str()).unwrap_or("");
                            let to_nid = conn.get("to").and_then(|x| x.as_str()).unwrap_or("");
                            let _from_aid = node_to_agent.get(from_nid).map(|s| s.as_str()).unwrap_or(from_nid);
                            let to_aid = node_to_agent.get(to_nid).map(|s| s.as_str()).unwrap_or(to_nid);

                            permitted_targets.push(to_aid.to_string());
                            if !to_nid.is_empty() {
                                permitted_targets.push(to_nid.to_string());
                            }

                            if to_aid == to_agent || to_nid == to_agent {
                                is_reverse_revision_allowed = true;
                            }
                        }
                    }
                }
            }
        }

        let is_valid_route = if action == "REVISE" {
            is_reverse_revision_allowed || permitted_targets.contains(&to_agent.to_string())
        } else {
            permitted_targets.is_empty() || permitted_targets.contains(&to_agent.to_string())
        };

        if !to_agent.is_empty() && !is_valid_route {
            return Ok(json!({
                "status": "ERROR",
                "exit_code": 1,
                "tool": "team_dispatch",
                "error": format!("Routing ACL Violation: Target agent '{}' is not connected via Swarm Flow cables. Permitted downstream targets: {:?}", to_agent, permitted_targets),
                "output": format!("❌ [ROUTING ACL REJECTED] You cannot dispatch to '{}'. The active preset '{}' does not have a cable connecting to this agent. Permitted targets: {:?}", to_agent, current_preset_name, permitted_targets)
            }));
        }

        // -------------------------------------------------------------------------
        // GATE 3: 3-LOOP CIRCUIT BREAKER ON REVISION
        // -------------------------------------------------------------------------
        if action == "REVISE" && !to_agent.is_empty() {
            let circuit_path = self.workspace_root.join(".FL_BIN").join("scratch").join("revision_circuit.json");
            let mut loop_count: u64 = 1;
            if circuit_path.exists() {
                if let Ok(c) = std::fs::read_to_string(&circuit_path) {
                    if let Ok(mut j) = serde_json::from_str::<Value>(&c) {
                        let key = format!("rev_{}", to_agent);
                        let current = j.get(&key).and_then(|x| x.as_u64()).unwrap_or(0);
                        loop_count = current + 1;
                        j[key] = json!(loop_count);
                        let _ = std::fs::write(&circuit_path, serde_json::to_string(&j).unwrap_or_default());
                    }
                }
            } else {
                if let Some(parent) = circuit_path.parent() {
                    let _ = std::fs::create_dir_all(parent);
                }
                let init_j = json!({ format!("rev_{}", to_agent): 1 });
                let _ = std::fs::write(&circuit_path, serde_json::to_string(&init_j).unwrap_or_default());
            }

            if loop_count > 3 {
                return Ok(json!({
                    "status": "CIRCUIT_BREAKER_TRIPPED",
                    "exit_code": 2,
                    "tool": "team_dispatch",
                    "error": format!("Circuit Breaker Tripped: Revision loop count between agents reached {} (limit: 3).", loop_count),
                    "output": format!("🛑 [CIRCUIT BREAKER ENGAGED] Revision loop count reached {} between agents. Swarm pipeline halted to prevent infinite token consumption. Operator intervention required.", loop_count)
                }));
            }
        }

        // -------------------------------------------------------------------------
        // GATE 4: LIVE BROADCAST & EVENT TELEMETRY
        // Broadcast live SSE event so Canvas UI nodes and laser cables light up
        // -------------------------------------------------------------------------
        if let Some(ref disc) = self.discovery {
            disc.broadcast_agent_activity(to_agent, "working");
        }

        let step_record = json!({
            "action": action,
            "to_agent": to_agent,
            "summary": summary,
            "payload": payload,
            "status_proof": status_proof,
            "preset": active_preset_id,
            "dispatched_at": crate::native_tools::get_current_iso_time()
        });

        Ok(json!({
            "status": "SUCCESS",
            "exit_code": 0,
            "tool": "team_dispatch",
            "action": action,
            "to_agent": to_agent,
            "active_preset": active_preset_id,
            "dispatch_record": step_record,
            "output": format!("⚡ [SWARM CABLE DISPATCH SUCCESS] Action '{}' transmitted along cable to '{}' (Preset: {}). Target node awakened with Barrier Synchronization.", action, to_agent, current_preset_name)
        }))
    }

    pub fn trigger_hook(&self, hook_name: &str, payload: &str) {
        let engine_root = self.resolve_engine_root();
        let candidate = engine_root.join("hooks").join(format!("{}.sh", hook_name));
        let script = if candidate.exists() {
            candidate
        } else {
            let ws_cand = self.workspace_root.join("hooks").join(format!("{}.sh", hook_name));
            if ws_cand.exists() {
                ws_cand
            } else {
                return;
            }
        };

        let script_str = script.to_string_lossy().to_string();
        let payload_str = payload.to_string();
        let ws_str = self.workspace_root.to_string_lossy().to_string();

        tokio::spawn(async move {
            let mut cmd = if cfg!(target_os = "windows") {
                let mut c = tokio::process::Command::new("cmd");
                c.arg("/C").arg("bash").arg(&script_str).arg(&payload_str);
                c
            } else {
                let mut c = tokio::process::Command::new("bash");
                c.arg(&script_str).arg(&payload_str);
                c
            };
            cmd.current_dir(&ws_str);
            if let Ok(mut child) = cmd.spawn() {
                let _ = tokio::time::timeout(tokio::time::Duration::from_millis(3000), child.wait()).await;
            }
        });
    }

    pub async fn sync_ecosystem_assets(&self) -> Result<Value, String> {
        self.execute("sync_ecosystem", &json!({})).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_path_normalization() {
        assert_eq!(normalize_crlf_to_lf("line1\r\nline2"), "line1\nline2");
    }

    #[test]
    fn test_base64_roundtrip() {
        let sample = b"Sovereign Flowork OS Runtime";
        let encoded = base64_encode(sample);
        let decoded = base64_decode(&encoded);
        assert_eq!(decoded, sample);
    }

    #[test]
    fn test_keywords_and_indicators() {
        assert!(!contains_indonesian_indicators("Inspecting compiler error log in core/src/agent.rs to debug type mismatch"));
        assert!(contains_indonesian_indicators("Melihat isi file untuk mencari error kodingan"));
        assert_eq!(count_keywords("sqlite, concurrency, wal, database, storage"), 5);
        assert_eq!(count_keywords("sqlite, concurrency, wal"), 3);
    }

    #[test]
    fn test_circuit_breaker_auto_heals_array_and_object_schemas() {
        let mut malformed_decl = json!({
            "name": "test_buggy_tool",
            "description": "Test tool with missing array items and missing object properties",
            "parameters": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "broken_array": {
                        "type": "array",
                        "description": "Array without items"
                    },
                    "broken_object": {
                        "type": "OBJECT",
                        "description": "Object without properties"
                    },
                    "nested_array_of_objects": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT"
                        }
                    },
                    "null_type_param": {
                        "type": null,
                        "description": "Param with null type"
                    }
                },
                "required": ["broken_array", "non_existent_field"]
            }
        });

        sanitize_tool_declaration(&mut malformed_decl);

        let params = malformed_decl["parameters"].as_object().unwrap();
        assert_eq!(params["type"], "OBJECT");
        assert!(!params.contains_key("$schema"), "$schema must be stripped");

        let props = params["properties"].as_object().unwrap();
        // 1. Broken array auto-injected with items
        assert_eq!(props["broken_array"]["items"]["type"], "STRING");
        assert_eq!(props["broken_array"]["type"], "ARRAY");

        // 2. Broken object auto-injected with properties
        assert!(props["broken_object"]["properties"].is_object());
        assert_eq!(props["broken_object"]["type"], "OBJECT");

        // 3. Deeply nested array of objects auto-injected with properties
        assert_eq!(props["nested_array_of_objects"]["type"], "ARRAY");
        assert_eq!(props["nested_array_of_objects"]["items"]["type"], "OBJECT");
        assert!(props["nested_array_of_objects"]["items"]["properties"].is_object());

        // 4. Null type normalized to STRING
        assert_eq!(props["null_type_param"]["type"], "STRING");

        // 5. Intercept gate schema injected
        assert!(props.contains_key("reason"));
        assert!(props.contains_key("keywords"));

        // 6. Required array filtered of non-existent fields and includes reason & keywords
        let req = params["required"].as_array().unwrap();
        assert!(req.iter().any(|v| v == "broken_array"));
        assert!(req.iter().any(|v| v == "reason"));
        assert!(req.iter().any(|v| v == "keywords"));
        assert!(!req.iter().any(|v| v == "non_existent_field"), "Invalid required key must be filtered");

        // 7. Batch deduplication and circuit breaker testing
        let mut batch = vec![
            malformed_decl.clone(),
            malformed_decl.clone(), // duplicate
            json!({
                "name": "another_tool",
                "parameters": {
                    "type": "ARRAY" // ARRAY at root
                }
            })
        ];
        sanitize_declaration_batch(&mut batch);
        assert_eq!(batch.len(), 2, "Duplicate tool must be deduplicated");
        assert_eq!(batch[1]["name"], "another_tool");
        assert_eq!(batch[1]["parameters"]["type"], "OBJECT");
    }

    #[test]
    fn test_all_sealed_tools_manifest_integrity_and_circuit_breaker() {
        let manifest_entries = crate::sealed_tools::SealedToolsEnclave::manifest();
        assert!(manifest_entries.len() >= 130, "Sealed enclave must contain all tools");

        for (rel_path, cipher) in manifest_entries {
            let unsealed = crate::sealed_tools::SealedToolsEnclave::unseal(cipher);
            assert!(!unsealed.is_empty(), "Unsealed file for {} must not be empty", rel_path);

            if rel_path.ends_with("manifest.json") {
                let parsed: Result<Value, _> = serde_json::from_slice(&unsealed);
                assert!(parsed.is_ok(), "Manifest {} must parse as valid JSON: {:?}", rel_path, parsed.err());
                let mut manifest_val = parsed.unwrap();

                // Test schema circuit breaker on every manifest's parameters
                if let Some(params) = manifest_val.get_mut("parameters") {
                    sanitize_json_schema(params);
                    assert_eq!(params["type"], "OBJECT", "Parameters root must normalize to OBJECT in {}", rel_path);
                    if let Some(props) = params.get("properties").and_then(|p| p.as_object()) {
                        for (prop_name, prop_val) in props {
                            if prop_val.get("type").and_then(|t| t.as_str()) == Some("ARRAY") {
                                assert!(
                                    prop_val.get("items").is_some(),
                                    "ARRAY property {} in {} must possess valid items definition",
                                    prop_name, rel_path
                                );
                            }
                        }
                    }
                }
            }
        }
    }

    #[tokio::test]
    async fn test_lifecycle_hooks_pre_tool_block_and_allow() {
        let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        let engine_root = manifest_dir.parent().unwrap();
        let tool_engine = ToolEngine::new(engine_root.to_path_buf());

        // 1. Safe command should pass pre_tool hook without error
        let safe_args = json!({
            "CommandLine": "git status"
        });
        let safe_res = tool_engine.execute_pre_tool_hook("run_command", &safe_args).await;
        assert!(safe_res.is_ok(), "Safe git status command must be allowed by pre_tool hook");

        // 2. Destructive git command should be mechanically blocked by pre_tool hook with error code 2
        let destructive_args = json!({
            "CommandLine": "git reset --hard"
        });
        let blocked_res = tool_engine.execute_pre_tool_hook("run_command", &destructive_args).await;
        assert!(blocked_res.is_err(), "Destructive git reset --hard must be blocked by pre_tool hook");
        let err_msg = blocked_res.err().unwrap();
        assert!(err_msg.contains("pre_tool hook") || err_msg.contains("BLOCKED"), "Error must cite hook rejection");

        // 3. trigger_hook smoke test: post_turn and on_error should execute gracefully
        tool_engine.trigger_hook("post_turn", "test_session_id_42");
        tool_engine.trigger_hook("on_error", "test_error_message");
    }

    #[tokio::test]
    async fn test_mcp_routing_and_dispatch() {
        let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        let engine_root = manifest_dir.parent().unwrap();
        let tool_engine = ToolEngine::new(engine_root.to_path_buf());

        // Calling an MCP tool (e.g. mcp_unknown_xyz) should be routed through mcp/run.mjs
        // and return the structured JSON error from mcp runner rather than "External tool not found"
        let mcp_res = tool_engine.execute_external_tool("mcp_unknown_xyz", &json!({})).await;
        if let Err(e) = mcp_res {
            assert!(e.contains("MCP tool") || e.contains("Unknown tool") || e.contains("unknown_xyz"), "Must route to MCP runner: {e}");
        }
    }

    #[test]
    fn test_sovereign_control_tools_purge_and_manifest_architecture() {
        // 1. Verify search_agents and search_skills are completely purged (zero presence)
        assert!(crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("search_agents").is_none());
        assert!(crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("search_skills").is_none());
        assert!(!crate::sealed_tools::SealedToolsEnclave::is_sealed_tool("search_agents"));
        assert!(!crate::sealed_tools::SealedToolsEnclave::is_sealed_tool("search_skills"));

        // 2. Verify skill_control manifest has create/publish/pin/unpin and no search/install
        let sc = crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("skill_control").expect("skill_control must resolve");
        let sc_props = &sc["parameters"]["properties"];
        assert!(sc_props.get("action").is_some());
        assert!(sc_props.get("skill_id").is_some());
        assert!(sc_props.get("search").is_none());
        assert!(sc_props.get("install").is_none());
        assert!(sc_props.get("list").is_none());
        let sc_action_desc = sc_props["action"]["description"].as_str().unwrap();
        assert!(sc_action_desc.contains("create") && sc_action_desc.contains("publish") && sc_action_desc.contains("pin") && sc_action_desc.contains("unpin"));

        // 3. Verify agent_control manifest has create/publish/pin/unpin and no search/install
        let ac = crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("agent_control").expect("agent_control must resolve");
        let ac_props = &ac["parameters"]["properties"];
        assert!(ac_props.get("action").is_some());
        assert!(ac_props.get("agent_id").is_some());
        assert!(ac_props.get("search").is_none());
        let ac_action_desc = ac_props["action"]["description"].as_str().unwrap();
        assert!(ac_action_desc.contains("create") && ac_action_desc.contains("publish") && ac_action_desc.contains("pin") && ac_action_desc.contains("unpin"));

        // 4. Verify search_tools manifest has mount/unmount/publish/status and no search/install
        let st = crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("search_tools").expect("search_tools must resolve");
        let st_props = &st["parameters"]["properties"];
        assert!(st_props.get("action").is_some());
        assert!(st_props.get("tools").is_some());
        assert!(st_props.get("search").is_none());
        let st_action_desc = st_props["action"]["description"].as_str().unwrap();
        assert!(st_action_desc.contains("mount") && st_action_desc.contains("unmount") && st_action_desc.contains("publish") && st_action_desc.contains("status"));

        // 5. Verify app_control and app_publish
        let app_c = crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("app_control").expect("app_control must resolve");
        assert!(app_c["parameters"]["properties"].get("action").is_some());
        assert!(crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("app_publish").is_some());

        // 6. Verify code_graph and youtube tools are natively sealed in binary
        assert!(crate::sealed_tools::SealedToolsEnclave::is_sealed_tool("code_graph"));
        assert!(crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("code_graph").is_some());
        assert!(crate::sealed_tools::SealedToolsEnclave::is_sealed_tool("youtube_audio_mixer"));
        assert!(crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("youtube_audio_mixer").is_some());
        assert!(crate::sealed_tools::SealedToolsEnclave::is_sealed_tool("youtube_spy_comments"));
        assert!(crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration("youtube_spy_comments").is_some());

        println!("✅ SOVEREIGN CONTROL TOOLS ARCHITECTURE VERIFIED WITH EXIT CODE 0!");
    }
}
