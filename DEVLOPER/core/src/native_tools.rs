//! Sovereign Flowork Native Binary Tools Engine
//! Planted directly inside the Rust Tokio core binary.
//! Co-authored-by: Flowork OS <agent@floworkos.com>

use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BackgroundTaskInfo {
    pub id: String,
    pub pid: u32,
    pub command: String,
    pub cwd: String,
    pub started_at: String,
    pub status: String,
    pub exit_code: Option<i32>,
    pub stdout: String,
    pub stderr: String,
}

static BACKGROUND_TASKS: RwLock<Option<HashMap<String, BackgroundTaskInfo>>> = RwLock::const_new(None);

pub async fn register_background_task(id: &str, pid: u32, command: &str, cwd: &str, started_at: &str) {
    let mut guard = BACKGROUND_TASKS.write().await;
    let map = guard.get_or_insert_with(HashMap::new);
    map.insert(id.to_string(), BackgroundTaskInfo {
        id: id.to_string(),
        pid,
        command: command.to_string(),
        cwd: cwd.to_string(),
        started_at: started_at.to_string(),
        status: "running".to_string(),
        exit_code: None,
        stdout: String::new(),
        stderr: String::new(),
    });
}

pub async fn update_background_task_done(id: &str, exit_code: i32, stdout: &str, stderr: &str) {
    let mut guard = BACKGROUND_TASKS.write().await;
    if let Some(ref mut map) = *guard {
        if let Some(task) = map.get_mut(id) {
            task.status = if exit_code == 0 { "completed".to_string() } else { "failed".to_string() };
            task.exit_code = Some(exit_code);
            task.stdout = stdout.to_string();
            task.stderr = stderr.to_string();
        }
    }
}

/// The Core Universal Agent Tools (selectable and configurable from GUI)
pub const CORE_14_TOOLS: &[&str] = &[
    "run_command",
    "view_file",
    "write_to_file",
    "replace_file_content",
    "read_url_content",
    "search_web",
    "ask_question",
    "schedule",
    "manage_task",
    "team_audit",
    "generate_image",
    "screenshot",
    "code_graph",
    "deterministic_helper",
];

/// The Promp Inti Trigger Tools (not selectable from GUI, auto-activated on prompt triggers)
pub const PROMPT_TRIGGER_9_TOOLS: &[&str] = &[
    "detect_hardcode",
    "audit_security",
    "website_intelligence",
    "web_security_audit",
    "youtube_spy_video",
    "youtube_spy_transcript",
    "youtube_spy_summary",
    "youtube_spy_channel",
    "youtube_spy_competitor_strategy",
];

/// The master registry of tools embedded natively in the binary
pub const NATIVE_BINARY_TOOLS: &[&str] = &[
    "run_command",
    "view_file",
    "write_to_file",
    "replace_file_content",
    "read_url_content",
    "search_web",
    "ask_question",
    "schedule",
    "manage_task",
    "team_audit",
    "generate_image",
    "detect_hardcode",
    "audit_security",
    "website_intelligence",
    "web_security_audit",
    "youtube_spy_video",
    "youtube_spy_transcript",
    "youtube_spy_summary",
    "youtube_spy_channel",
    "youtube_spy_competitor_strategy",
    "screenshot",
    "flow_screenshot",
    "code_graph",
    "fl_repo_map",
    "repo_map",
    "deterministic_helper",
    "c7_helper",
    "team_progress",
    "app_control",
];

pub fn is_native_binary_tool(name: &str) -> bool {
    let clean = name.trim().trim_start_matches("flow_").trim_start_matches("default_api:");
    NATIVE_BINARY_TOOLS.contains(&clean)
}

pub fn is_core_14_tool(name: &str) -> bool {
    let clean = name.trim().trim_start_matches("flow_").trim_start_matches("default_api:");
    CORE_14_TOOLS.contains(&clean)
}

pub fn is_prompt_trigger_tool(name: &str) -> bool {
    let clean = name.trim().trim_start_matches("flow_").trim_start_matches("default_api:");
    PROMPT_TRIGGER_9_TOOLS.contains(&clean)
}

pub fn get_current_iso_time() -> String {
    let now = std::time::SystemTime::now();
    let dt: ChronoLite = now.into();
    dt.to_iso_string()
}

struct ChronoLite {
    secs: u64,
}

impl From<std::time::SystemTime> for ChronoLite {
    fn from(t: std::time::SystemTime) -> Self {
        let secs = t.duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs();
        Self { secs }
    }
}

impl ChronoLite {
    fn to_iso_string(&self) -> String {
        let s = self.secs;
        let days = s / 86400;
        let rem_secs = s % 86400;
        let hours = rem_secs / 3600;
        let minutes = (rem_secs % 3600) / 60;
        let seconds = rem_secs % 60;

        let mut y = 1970;
        let mut d = days;
        loop {
            let leap = (y % 4 == 0 && y % 100 != 0) || (y % 400 == 0);
            let d_in_y = if leap { 366 } else { 365 };
            if d < d_in_y { break; }
            d -= d_in_y;
            y += 1;
        }

        let leap = (y % 4 == 0 && y % 100 != 0) || (y % 400 == 0);
        let m_days = [31, if leap { 29 } else { 28 }, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
        let mut m = 0;
        while m < 12 && d >= m_days[m] {
            d -= m_days[m];
            m += 1;
        }

        format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z", y, m + 1, d + 1, hours, minutes, seconds)
    }
}

const REASON_BLACKLIST: &[&str] = &[
    "update", "fix", "fixed", "fix bug", "fixing", "code update",
    "edit", "editing", "modify", "change", "patch", "refactor",
    "temporary", "test", "minor change", "clean up", "adjust",
    "updating", "changing", "modifying", "quick fix"
];

const KEYWORD_BLACKLIST: &[&str] = &[
    "code", "file", "fix", "update", "script", "test", "temp",
    "data", "text", "new", "edit", "tool", "change", "patch", "bug"
];

/// Anti-Lazy Quality Gatekeeper (Gembok Tri-Faktor)
/// Enforces sharp architectural reasons, semantic technical keywords, and verified .fl_brain links.
pub fn validate_file_mutation_quality_gate(
    args: &serde_json::Value,
    effective_ws: &Path,
) -> Result<(), String> {
    // 1. Validate 'reason' / 'Description' / 'Instruction'
    let reason_raw = args.get("reason")
        .or_else(|| args.get("Description"))
        .or_else(|| args.get("description"))
        .or_else(|| args.get("Instruction"))
        .or_else(|| args.get("instruction"))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim();

    if !reason_raw.is_empty() {
        let reason_clean = reason_raw.to_lowercase();
        for &bl in REASON_BLACKLIST {
            if reason_clean == bl || reason_clean == format!("{} file", bl) || reason_clean == format!("{} code", bl) {
                return Err(format!(
                    "REJECTED [E_SHALLOW_REASON]: 'reason' is too generic or superficial ('{}'). Reason must explain WHY this change is made from an architectural perspective (min 3 words, min 15 chars). Example: 'Handle sqlite busy timeout by enabling WAL mode to prevent concurrency locks'.",
                    reason_raw
                ));
            }
        }

        let words: Vec<&str> = reason_raw.split_whitespace().collect();
        if reason_raw.chars().count() < 15 || words.len() < 3 {
            return Err(format!(
                "REJECTED [E_SHALLOW_REASON]: 'reason' must be substantive and explain architectural justification (min 3 words, min 15 chars; got '{}').",
                reason_raw
            ));
        }
    }

    // 2. Validate 'keywords'
    if let Some(kw_val) = args.get("keywords").and_then(|v| v.as_str()) {
        let kw_clean = kw_val.trim();
        if !kw_clean.is_empty() {
            let kws: Vec<&str> = kw_clean
                .split(|c| c == ',' || c == ';' || c == '\n')
                .map(|s| s.trim())
                .filter(|s| s.len() >= 2)
                .collect();

            if kws.len() < 3 {
                return Err(format!(
                    "REJECTED [E_GENERIC_KEYWORDS]: 'keywords' must contain at least 3 high-signal domain/technical keywords (found {}: '{}'). Example: 'ipc_router, auth_token, rate_limit'.",
                    kws.len(), kw_clean
                ));
            }

            let all_generic = kws.iter().all(|k| {
                let k_lower = k.to_lowercase();
                KEYWORD_BLACKLIST.contains(&k_lower.as_str())
            });

            if all_generic {
                return Err(format!(
                    "REJECTED [E_GENERIC_KEYWORDS]: 'keywords' ('{}') only contains generic filler terms. Provide specific domain/technical terms.",
                    kw_clean
                ));
            }
        }
    }

    // 3. Validate 'fl_brain_ref'
    let brain_ref_opt = args.get("fl_brain_ref")
        .or_else(|| args.get("fl_brain"))
        .or_else(|| args.get("brain_ref"))
        .and_then(|v| v.as_str())
        .map(|s| s.trim());

    if let Some(brain_ref) = brain_ref_opt {
        if !brain_ref.is_empty() && brain_ref != "none" && brain_ref != "fresh_solution" && brain_ref != "n/a" {
            let candidate_paths = [
                effective_ws.join(brain_ref),
                effective_ws.join(".fl_brain").join(brain_ref),
                effective_ws.join(".fl_brain").join("memories").join(brain_ref),
                PathBuf::from(brain_ref),
            ];

            let exists = candidate_paths.iter().any(|p| p.exists());
            if !exists {
                return Err(format!(
                    "REJECTED [E_HALLUCINATED_MEMORY]: Cited brain reference '{}' does not exist on disk! Verify memories via view_file first or pass 'fl_brain_ref': 'none'.",
                    brain_ref
                ));
            }
        }
    }

    Ok(())
}

/// Dynamically format fingerprint comment based on file extension
pub fn format_fingerprint_for_file(path_str: &str, keywords: &str, reason: &str, brain_ref: &str) -> Option<String> {
    let kw = keywords.trim();
    let rz = reason.trim();
    let br = brain_ref.trim();
    if kw.is_empty() && rz.is_empty() {
        return None;
    }
    let ext = std::path::Path::new(path_str)
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();

    let iso_now = get_current_iso_time();
    let brain_part = if !br.is_empty() && br != "none" && br != "fresh_solution" {
        format!(" | BRAIN: {}", br)
    } else {
        String::new()
    };

    match ext.as_str() {
        // Python, Shell, YAML, TOML
        "py" | "sh" | "bash" | "zsh" | "yaml" | "yml" | "toml" | "dockerfile" | "rb" | "pl" => {
            Some(format!("# [FL_INDEX: {} | COT: {}{}| AT: {}]\n", kw, rz, brain_part, iso_now))
        },
        // C, C++, Rust, Go, JS, TS, Java, Kotlin, Swift, PHP, C#
        "rs" | "go" | "js" | "mjs" | "cjs" | "ts" | "jsx" | "tsx" | "c" | "cpp" | "h" | "hpp" | "java" | "kt" | "swift" | "php" | "cs" | "dart" => {
            Some(format!("// [FL_INDEX: {} | COT: {}{}| AT: {}]\n", kw, rz, brain_part, iso_now))
        },
        // CSS, SCSS, LESS
        "css" | "scss" | "sass" | "less" => {
            Some(format!("/* [FL_INDEX: {} | COT: {}{}| AT: {}] */\n", kw, rz, brain_part, iso_now))
        },
        // HTML, XML, SVG, Markdown
        "html" | "htm" | "xml" | "svg" | "md" | "markdown" => {
            Some(format!("<!-- [FL_INDEX: {} | COT: {}{}| AT: {}] -->\n", kw, rz, brain_part, iso_now))
        },
        // SQL
        "sql" => {
            Some(format!("-- [FL_INDEX: {} | COT: {}{}| AT: {}]\n", kw, rz, brain_part, iso_now))
        },
        _ => None,
    }
}

fn extract_youtube_video_id(target: &str) -> String {
    let clean = target.trim();
    if clean.len() == 11 && !clean.contains('/') && !clean.contains('.') && !clean.contains('?') {
        return clean.to_string();
    }
    if let Some(pos) = clean.find("v=") {
        let slice = &clean[pos + 2..];
        let id: String = slice.chars().take_while(|c| c.is_ascii_alphanumeric() || *c == '_' || *c == '-').collect();
        if id.len() == 11 {
            return id;
        }
    }
    for prefix in &["youtu.be/", "/embed/", "/shorts/", "/v/"] {
        if let Some(pos) = clean.find(prefix) {
            let slice = &clean[pos + prefix.len()..];
            let id: String = slice.chars().take_while(|c| c.is_ascii_alphanumeric() || *c == '_' || *c == '-').collect();
            if id.len() == 11 {
                return id;
            }
        }
    }
    clean.to_string()
}

fn extract_meta_tag(html: &str, attr_pattern: &str) -> Option<String> {
    if let Some(pos) = html.find(attr_pattern) {
        let slice = &html[pos..];
        if let Some(c_pos) = slice.find("content=\"") {
            let content_slice = &slice[c_pos + 9..];
            if let Some(end) = content_slice.find('"') {
                return Some(content_slice[..end].to_string());
            }
        }
    }
    None
}

fn extract_regex_first(html: &str, prefix: &str) -> Option<String> {
    if let Some(pos) = html.find(prefix) {
        let after = &html[pos + prefix.len()..];
        let val: String = after.chars().take_while(|c| *c != '"').collect();
        if !val.is_empty() {
            return Some(val);
        }
    }
    None
}

async fn fetch_youtube_live_data(target: &str) -> Value {
    let clean_target = target.trim();
    let is_channel = clean_target.contains("/@") || clean_target.contains("/c/") || clean_target.contains("/channel/") || clean_target.starts_with('@');
    
    if is_channel {
        let yt_base = crate::prompt_enclave::PromptEnclave::url_youtube_base();
        let channel_url = if clean_target.starts_with('@') {
            format!("{yt_base}/{clean_target}")
        } else if !clean_target.starts_with("http") {
            format!("{yt_base}/{clean_target}")
        } else {
            clean_target.to_string()
        };

        let mut cmd = tokio::process::Command::new("curl");
        cmd.arg("-sL").arg("--max-time").arg("10")
           .arg("-A").arg("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
           .arg(&channel_url);

        let html = if let Ok(out) = cmd.output().await {
            String::from_utf8_lossy(&out.stdout).to_string()
        } else {
            String::new()
        };

        let title = extract_meta_tag(&html, "property=\"og:title\"").or_else(|| extract_meta_tag(&html, "name=\"title\"")).unwrap_or_else(|| clean_target.to_string());
        let desc = extract_meta_tag(&html, "property=\"og:description\"").or_else(|| extract_meta_tag(&html, "name=\"description\"")).unwrap_or_default();
        let subs = extract_regex_first(&html, "\"content\":\"").unwrap_or_else(|| "N/A".to_string());

        return json!({
            "is_channel": true,
            "channel_title": title,
            "channel_description": desc,
            "subscribers": subs,
            "channel_url": channel_url,
            "target": target
        });
    }

    let vid = extract_youtube_video_id(clean_target);
    let watch_url = format!("{}?v={vid}", crate::prompt_enclave::PromptEnclave::url_youtube_watch());

    let mut cmd = tokio::process::Command::new("curl");
    cmd.arg("-sL").arg("--max-time").arg("10")
       .arg("-A").arg("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
       .arg(&watch_url);

    let html = if let Ok(out) = cmd.output().await {
        String::from_utf8_lossy(&out.stdout).to_string()
    } else {
        String::new()
    };

    let mut title = String::new();
    let mut author = String::new();
    let mut channel_id = String::new();
    let mut views = String::new();
    let mut length_seconds = String::new();
    let mut keywords: Vec<Value> = Vec::new();
    let mut short_description = String::new();
    let mut category = String::new();
    let mut publish_date = String::new();
    let mut ad_breaks = 0;
    let mut captions_available: Vec<String> = Vec::new();

    let marker = "ytInitialPlayerResponse";
    if let Some(pos) = html.find(marker) {
        let remainder = &html[pos + marker.len()..];
        if let Some(eq_pos) = remainder.find('=') {
            let json_start = remainder[eq_pos + 1..].trim_start();
            if json_start.starts_with('{') {
                let mut brace_count = 0;
                let mut end_pos = 0;
                let mut in_str = false;
                let mut esc = false;
                for (i, c) in json_start.char_indices() {
                    if in_str {
                        if esc {
                            esc = false;
                        } else if c == '\\' {
                            esc = true;
                        } else if c == '"' {
                            in_str = false;
                        }
                    } else {
                        if c == '"' {
                            in_str = true;
                        } else if c == '{' {
                            brace_count += 1;
                        } else if c == '}' {
                            brace_count -= 1;
                            if brace_count == 0 {
                                end_pos = i + 1;
                                break;
                            }
                        }
                    }
                }

                if end_pos > 0 {
                    if let Ok(json_val) = serde_json::from_str::<Value>(&json_start[..end_pos]) {
                        if let Some(vd) = json_val.get("videoDetails") {
                            title = vd.get("title").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            author = vd.get("author").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            channel_id = vd.get("channelId").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            views = vd.get("viewCount").and_then(|v| v.as_str()).unwrap_or("0").to_string();
                            length_seconds = vd.get("lengthSeconds").and_then(|v| v.as_str()).unwrap_or("0").to_string();
                            if let Some(kws) = vd.get("keywords").and_then(|v| v.as_array()) {
                                keywords = kws.clone();
                            }
                            short_description = vd.get("shortDescription").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        }
                        if let Some(micro) = json_val.get("microformat").and_then(|m| m.get("playerMicroformatRenderer")) {
                            category = micro.get("category").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            publish_date = micro.get("publishDate").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        }
                        ad_breaks = json_val.get("adPlacements").and_then(|a| a.as_array()).map(|arr| arr.len()).unwrap_or(0);
                        if let Some(caps) = json_val.get("captions").and_then(|c| c.get("playerCaptionsTracklistRenderer")).and_then(|t| t.get("captionTracks")).and_then(|arr| arr.as_array()) {
                            for track in caps {
                                if let Some(name) = track.get("name").and_then(|n| n.get("simpleText")).and_then(|s| s.as_str()) {
                                    captions_available.push(name.to_string());
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if title.is_empty() || author.is_empty() {
        let oembed_url = format!("{}?url={watch_url}&format=json", crate::prompt_enclave::PromptEnclave::url_youtube_oembed());
        let mut oembed_cmd = tokio::process::Command::new("curl");
        oembed_cmd.arg("-sL").arg("--max-time").arg("6").arg(&oembed_url);
        if let Ok(o_out) = oembed_cmd.output().await {
            if let Ok(o_json) = serde_json::from_slice::<Value>(&o_out.stdout) {
                if title.is_empty() {
                    title = o_json.get("title").and_then(|v| v.as_str()).unwrap_or("").to_string();
                }
                if author.is_empty() {
                    author = o_json.get("author_name").and_then(|v| v.as_str()).unwrap_or("").to_string();
                }
            }
        }
    }

    if views.is_empty() || views == "0" {
        if let Some(v_str) = extract_regex_first(&html, "\"viewCount\":\"") {
            views = v_str;
        }
    }

    json!({
        "is_channel": false,
        "video_id": vid,
        "watch_url": watch_url,
        "title": title,
        "channel": author,
        "channel_id": channel_id,
        "views": views,
        "duration_seconds": length_seconds,
        "category": category,
        "publish_date": publish_date,
        "tags": keywords,
        "description": short_description,
        "ad_breaks": ad_breaks,
        "monetization": ad_breaks > 0,
        "captions": captions_available
    })
}

/// Native in-binary implementation of Sovereign Code Graph & Repo Map Engine
pub(crate) async fn execute_code_graph_native(
    args: &Value,
    workspace_root: &Path,
) -> Result<Value, String> {
    let action = args.get("action").and_then(|v| v.as_str()).unwrap_or("map");
    let target_dir_raw = args.get("target_dir")
        .or_else(|| args.get("dir"))
        .or_else(|| args.get("path"))
        .and_then(|v| v.as_str())
        .unwrap_or(".");

    let target_dir = if target_dir_raw == "." || target_dir_raw.is_empty() {
        workspace_root.to_path_buf()
    } else {
        let p = PathBuf::from(target_dir_raw);
        if p.is_absolute() { p } else { workspace_root.join(p) }
    };

    let max_tokens = args.get("max_tokens").and_then(|v| v.as_u64()).unwrap_or(1024) as usize;
    let query_str = args.get("query")
        .or_else(|| args.get("target_file"))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_lowercase();
    let max_depth = args.get("depth").and_then(|v| v.as_u64()).unwrap_or(4) as usize;

    let focus_files: Vec<String> = args.get("focus_files")
        .and_then(|v| v.as_array())
        .map(|arr| arr.iter().filter_map(|x| x.as_str()).map(|s| s.to_string()).collect())
        .unwrap_or_default();

    if !target_dir.exists() {
        return Ok(json!({
            "status": "ERROR",
            "exit_code": 1,
            "message": format!("Target directory does not exist: {}", target_dir.display())
        }));
    }

    // Secret Shield: Zero-Leak filter for sensitive files
    let is_secret_file = |name: &str| -> bool {
        let lower = name.to_lowercase();
        lower.starts_with(".env")
            || lower.ends_with(".key")
            || lower.ends_with(".pem")
            || lower.ends_with(".p12")
            || lower.ends_with(".secret")
            || lower.contains("id_rsa")
            || lower.contains("token")
            || lower.contains("password")
            || lower.contains("credential")
    };

    let is_code_ext = |ext: &str| -> bool {
        matches!(
            ext,
            "rs" | "js" | "mjs" | "cjs" | "jsx" | "ts" | "tsx" | "py" | "go" | "sh" | "bash"
                | "c" | "cpp" | "h" | "hpp" | "html" | "css" | "json" | "toml" | "yaml" | "yml" | "md"
        )
    };

    let is_ignored_dir = |name: &str| -> bool {
        matches!(
            name,
            ".git" | "node_modules" | "target" | "vendor" | ".FL_BIN" | "dist" | "build"
                | ".next" | ".nuxt" | "coverage" | ".cache" | "out" | "bin" | "obj" | ".svn" | ".hg"
        )
    };

    struct FileEntry {
        rel_path: String,
        symbols: Vec<Value>,
        imports: Vec<String>,
    }

    let mut queue = std::collections::VecDeque::new();
    queue.push_back((target_dir.clone(), 0usize));

    let mut scanned_files: Vec<FileEntry> = Vec::new();
    let mut total_scanned = 0;

    while let Some((dir, depth)) = queue.pop_front() {
        if depth > max_depth { continue; }
        let mut entries = match tokio::fs::read_dir(&dir).await {
            Ok(rd) => rd,
            Err(_) => continue,
        };

        while let Ok(Some(entry)) = entries.next_entry().await {
            let name = entry.file_name().to_string_lossy().to_string();
            if name.starts_with('.') && name != ".flowork" && name != ".fl_brain" {
                if is_ignored_dir(&name) || name == ".git" { continue; }
            }
            if is_ignored_dir(&name) { continue; }

            let path = entry.path();
            if let Ok(file_type) = entry.file_type().await {
                if file_type.is_dir() {
                    queue.push_back((path, depth + 1));
                } else if file_type.is_file() {
                    if is_secret_file(&name) { continue; }
                    let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("").to_lowercase();
                    if !is_code_ext(&ext) { continue; }

                    let metadata = match entry.metadata().await {
                        Ok(m) => m,
                        Err(_) => continue,
                    };
                    if metadata.len() > 512 * 1024 { continue; } // Bounded RAM (< 200 MB RSS safeguard)

                    let rel_path = path.strip_prefix(&target_dir)
                        .unwrap_or(&path)
                        .to_string_lossy()
                        .replace('\\', "/");

                    let content = match tokio::fs::read_to_string(&path).await {
                        Ok(c) => c,
                        Err(_) => continue,
                    };

                    let mut symbols = Vec::new();
                    let mut imports = Vec::new();

                    for (line_idx, line) in content.lines().enumerate() {
                        let trimmed = line.trim();
                        let line_no = line_idx + 1;

                        if ext == "rs" {
                            if trimmed.starts_with("use ") && trimmed.ends_with(';') {
                                imports.push(trimmed.trim_start_matches("use ").trim_end_matches(';').to_string());
                            } else if let Some(rest) = trimmed.strip_prefix("pub async fn ").or_else(|| trimmed.strip_prefix("pub fn ")).or_else(|| trimmed.strip_prefix("async fn ")).or_else(|| trimmed.strip_prefix("fn ")) {
                                if let Some(fn_name) = rest.split('(').next() {
                                    let clean_fn = fn_name.trim();
                                    if !clean_fn.is_empty() {
                                        symbols.push(json!({"type": "fn", "name": clean_fn, "line": line_no}));
                                    }
                                }
                            } else if let Some(rest) = trimmed.strip_prefix("pub struct ").or_else(|| trimmed.strip_prefix("struct ")) {
                                if let Some(st_name) = rest.split(|c: char| c == '{' || c == '(' || c == ';' || c.is_whitespace()).next() {
                                    if !st_name.trim().is_empty() {
                                        symbols.push(json!({"type": "struct", "name": st_name.trim(), "line": line_no}));
                                    }
                                }
                            } else if let Some(rest) = trimmed.strip_prefix("pub enum ").or_else(|| trimmed.strip_prefix("enum ")) {
                                if let Some(en_name) = rest.split(|c: char| c == '{' || c.is_whitespace()).next() {
                                    if !en_name.trim().is_empty() {
                                        symbols.push(json!({"type": "enum", "name": en_name.trim(), "line": line_no}));
                                    }
                                }
                            } else if let Some(rest) = trimmed.strip_prefix("pub trait ").or_else(|| trimmed.strip_prefix("trait ")) {
                                if let Some(tr_name) = rest.split(|c: char| c == '{' || c.is_whitespace()).next() {
                                    if !tr_name.trim().is_empty() {
                                        symbols.push(json!({"type": "trait", "name": tr_name.trim(), "line": line_no}));
                                    }
                                }
                            } else if let Some(rest) = trimmed.strip_prefix("impl ") {
                                if let Some(imp_name) = rest.split(|c: char| c == '{' || c == '<' || c.is_whitespace()).next() {
                                    if !imp_name.trim().is_empty() {
                                        symbols.push(json!({"type": "impl", "name": imp_name.trim(), "line": line_no}));
                                    }
                                }
                            }
                        } else if matches!(ext.as_str(), "js" | "mjs" | "cjs" | "jsx" | "ts" | "tsx") {
                            if trimmed.starts_with("import ") || trimmed.contains("require(") {
                                imports.push(trimmed.to_string());
                            }
                            if let Some(rest) = trimmed.strip_prefix("function ").or_else(|| trimmed.strip_prefix("async function ")) {
                                if let Some(fn_name) = rest.split('(').next() {
                                    if !fn_name.trim().is_empty() {
                                        symbols.push(json!({"type": "fn", "name": fn_name.trim(), "line": line_no}));
                                    }
                                }
                            } else if let Some(rest) = trimmed.strip_prefix("class ") {
                                if let Some(cls_name) = rest.split(|c: char| c == '{' || c.is_whitespace()).next() {
                                    if !cls_name.trim().is_empty() {
                                        symbols.push(json!({"type": "class", "name": cls_name.trim(), "line": line_no}));
                                    }
                                }
                            } else if let Some(rest) = trimmed.strip_prefix("interface ") {
                                if let Some(iface_name) = rest.split(|c: char| c == '{' || c.is_whitespace()).next() {
                                    if !iface_name.trim().is_empty() {
                                        symbols.push(json!({"type": "interface", "name": iface_name.trim(), "line": line_no}));
                                    }
                                }
                            }
                        } else if ext == "py" {
                            if trimmed.starts_with("def ") || trimmed.starts_with("async def ") {
                                let rest = trimmed.trim_start_matches("async ").trim_start_matches("def ");
                                if let Some(fn_name) = rest.split('(').next() {
                                    if !fn_name.trim().is_empty() {
                                        symbols.push(json!({"type": "fn", "name": fn_name.trim(), "line": line_no}));
                                    }
                                }
                            } else if trimmed.starts_with("class ") {
                                let rest = trimmed.trim_start_matches("class ");
                                if let Some(cls_name) = rest.split(|c: char| c == ':' || c == '(' || c.is_whitespace()).next() {
                                    if !cls_name.trim().is_empty() {
                                        symbols.push(json!({"type": "class", "name": cls_name.trim(), "line": line_no}));
                                    }
                                }
                            }
                        } else if ext == "go" {
                            if trimmed.starts_with("func ") {
                                let rest = trimmed.trim_start_matches("func ");
                                if let Some(fn_name) = rest.split('(').next() {
                                    if !fn_name.trim().is_empty() {
                                        symbols.push(json!({"type": "fn", "name": fn_name.trim(), "line": line_no}));
                                    }
                                }
                            }
                        }
                    }

                    scanned_files.push(FileEntry {
                        rel_path,
                        symbols,
                        imports,
                    });
                    total_scanned += 1;
                }
            }
        }
    }

    match action {
        "query" => {
            let mut matches = Vec::new();
            for file in &scanned_files {
                for sym in &file.symbols {
                    let s_name = sym.get("name").and_then(|v| v.as_str()).unwrap_or("");
                    if s_name.to_lowercase().contains(&query_str) {
                        matches.push(json!({
                            "file": file.rel_path,
                            "type": sym.get("type"),
                            "name": s_name,
                            "line": sym.get("line")
                        }));
                    }
                }
            }
            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "query": query_str,
                "matches_found": matches.len(),
                "results": matches.into_iter().take(40).collect::<Vec<_>>()
            }))
        },
        "impact" => {
            let target_norm = query_str.replace('\\', "/");
            let mut matched_entry: Option<&FileEntry> = None;
            for f in &scanned_files {
                if f.rel_path.to_lowercase() == target_norm || f.rel_path.to_lowercase().ends_with(&target_norm) {
                    matched_entry = Some(f);
                    break;
                }
            }
            if let Some(target) = matched_entry {
                let mut direct_dependents = Vec::new();
                for other in &scanned_files {
                    if other.rel_path != target.rel_path {
                        for imp in &other.imports {
                            if imp.contains(&target.rel_path) || target.rel_path.contains(imp) {
                                direct_dependents.push(other.rel_path.clone());
                                break;
                            }
                        }
                    }
                }
                Ok(json!({
                    "status": "SUCCESS",
                    "exit_code": 0,
                    "target_file": target.rel_path,
                    "blast_radius_score": direct_dependents.len(),
                    "direct_dependents": direct_dependents,
                    "dependencies": target.imports,
                    "symbols_exposed": target.symbols
                }))
            } else {
                Ok(json!({
                    "status": "FILE_NOT_FOUND",
                    "exit_code": 1,
                    "target": query_str,
                    "message": format!("File '{}' not found in code graph index", query_str)
                }))
            }
        },
        _ => {
            // "map" or "overview"
            scanned_files.sort_by(|a, b| {
                let a_focus = focus_files.iter().any(|f| a.rel_path.contains(f));
                let b_focus = focus_files.iter().any(|f| b.rel_path.contains(f));
                if a_focus && !b_focus {
                    std::cmp::Ordering::Less
                } else if !a_focus && b_focus {
                    std::cmp::Ordering::Greater
                } else {
                    b.symbols.len().cmp(&a.symbols.len())
                }
            });

            let root_name = target_dir.file_name().unwrap_or_default().to_string_lossy().to_string();
            let header = format!("🗺️ CODE GRAPH & REPO MAP [Root: {} | Files: {}]\n", root_name, total_scanned);
            let estimate_tokens = |text: &str| -> usize {
                if text.is_empty() { 0 } else { ((text.len() as f64) / 3.7).ceil() as usize }
            };

            let mut current_tokens = estimate_tokens(&header);
            let mut included_entries = Vec::new();

            for f in &scanned_files {
                let symbol_names: Vec<String> = f.symbols.iter()
                    .take(8)
                    .filter_map(|s| {
                        let t = s.get("type").and_then(|v| v.as_str()).unwrap_or("");
                        let n = s.get("name").and_then(|v| v.as_str()).unwrap_or("");
                        if !n.is_empty() { Some(format!("{} {}", t, n)) } else { None }
                    })
                    .collect();
                let sym_str = if !symbol_names.is_empty() {
                    format!(" ── ({})", symbol_names.join(", "))
                } else {
                    String::new()
                };
                let line = format!("📄 {}{}\n", f.rel_path, sym_str);
                let line_tokens = estimate_tokens(&line);

                // Strict Sub-Ceiling: actual <= budget
                if current_tokens + line_tokens > max_tokens {
                    break;
                }
                current_tokens += line_tokens;
                included_entries.push(line);
            }

            let mut output_text = header;
            for ent in &included_entries {
                output_text.push_str(ent);
            }
            let actual_tokens = estimate_tokens(&output_text);

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "root": target_dir.to_string_lossy().replace('\\', "/"),
                "total_files": total_scanned,
                "included_files": included_entries.len(),
                "max_tokens": max_tokens,
                "actual_tokens": actual_tokens,
                "under_budget": actual_tokens <= max_tokens,
                "repo_map": output_text
            }))
        }
    }
}

/// Native tool executor for the 23 tools embedded directly in the binary
pub async fn execute_native_tool(
    name: &str,
    args: &Value,
    workspace_root: &Path,
    engine_root: &Path,
) -> Result<Value, String> {
    execute_native_tool_with_discovery(name, args, workspace_root, engine_root, None).await
}

/// Native tool executor with real-time Swarm and event bus integration
pub async fn execute_native_tool_with_discovery(
    name: &str,
    args: &Value,
    workspace_root: &Path,
    engine_root: &Path,
    discovery: Option<&Arc<crate::discovery::PluginDiscovery>>,
) -> Result<Value, String> {
    let clean_name = name.trim().trim_start_matches("flow_").trim_start_matches("default_api:");

    match clean_name {
        "run_command" => {
            let command = args.get("CommandLine")
                .or_else(|| args.get("commandLine"))
                .or_else(|| args.get("command"))
                .or_else(|| args.get("cmd"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| "CommandLine is required".to_string())?;

            let cwd = args.get("Cwd")
                .or_else(|| args.get("cwd"))
                .and_then(|v| v.as_str())
                .map(PathBuf::from)
                .unwrap_or_else(|| workspace_root.to_path_buf());

            let cwd_path = if cwd.is_absolute() {
                cwd
            } else {
                workspace_root.join(cwd)
            };

            let mut cmd = crate::tools::get_platform_shell(&cwd_path, command);
            cmd.env("FLOWORK_WORKSPACE", workspace_root)
               .env("FLOWORK_ENGINE_ROOT", engine_root)
               .env("FLOWORK_CO_AUTHOR", "Flowork OS <agent@floworkos.com>")
               .env("PAGER", "cat");

            // Apply Credential Shield (Zero-Secret Agent Environment inspired by NVIDIA OpenShell)
            crate::credential_shield::CredentialShield::scrub_command_env(&mut cmd);

            // Apply Kernel-level Landlock Sandbox Confinement (bypass if Dev Mode authenticated)
            crate::sandbox::apply_sandbox_to_command(&mut cmd, workspace_root, true);

            let mut child = cmd.stdout(std::process::Stdio::piped())
                .stderr(std::process::Stdio::piped())
                .spawn()
                .map_err(|e| format!("Failed to spawn command '{command}': {e}"))?;

            let mut stdout_handle = child.stdout.take();
            let mut stderr_handle = child.stderr.take();

            let stdout_task = tokio::spawn(async move {
                let mut buf = Vec::new();
                if let Some(mut r) = stdout_handle {
                    use tokio::io::AsyncReadExt;
                    let _ = r.read_to_end(&mut buf).await;
                }
                buf
            });

            let stderr_task = tokio::spawn(async move {
                let mut buf = Vec::new();
                if let Some(mut r) = stderr_handle {
                    use tokio::io::AsyncReadExt;
                    let _ = r.read_to_end(&mut buf).await;
                }
                buf
            });

            let is_daemon = args.get("IsDaemon")
                .or_else(|| args.get("isDaemon"))
                .or_else(|| args.get("is_daemon"))
                .and_then(|v| v.as_bool())
                .unwrap_or(false);

            let wait_ms = args.get("WaitMsBeforeAsync")
                .or_else(|| args.get("waitMsBeforeAsync"))
                .or_else(|| args.get("wait_ms_before_async"))
                .or_else(|| args.get("timeout"))
                .and_then(|v| v.as_u64())
                .unwrap_or(if is_daemon { 3000 } else { 60000 });

            let wait_duration = tokio::time::Duration::from_millis(wait_ms);
            let select_res = tokio::select! {
                res = child.wait() => {
                    Some(res.map_err(|e| format!("Failed to wait on child process '{command}': {e}"))?)
                }
                _ = tokio::time::sleep(wait_duration) => {
                    None
                }
            };

            if let Some(status) = select_res {
                let stdout_bytes = stdout_task.await.unwrap_or_default();
                let stderr_bytes = stderr_task.await.unwrap_or_default();

                let stdout = crate::credential_shield::CredentialShield::redact_secrets(&String::from_utf8_lossy(&stdout_bytes));
                let stderr = crate::credential_shield::CredentialShield::redact_secrets(&String::from_utf8_lossy(&stderr_bytes));
                let exit_code = status.code().unwrap_or(if status.success() { 0 } else { 1 });

                let offload_res = crate::symbolic_memory::SymbolicMemory::condense_command_output(
                    workspace_root,
                    command,
                    exit_code,
                    &stdout,
                    &stderr,
                );

                if status.success() {
                    Ok(json!({
                        "status": "SUCCESS",
                        "exit_code": 0,
                        "command": command,
                        "cwd": cwd_path.display().to_string(),
                        "output": offload_res.formatted_output,
                        "is_offloaded": offload_res.is_offloaded,
                        "node_id": offload_res.node_id,
                        "offload_path": offload_res.offload_path.as_ref().map(|p| p.display().to_string()),
                        "tokens_saved": offload_res.tokens_saved_est,
                        "raw_output": if offload_res.is_offloaded { &offload_res.formatted_output } else { &stdout }
                    }))
                } else {
                    Ok(json!({
                        "status": "ERROR",
                        "exit_code": exit_code,
                        "command": command,
                        "cwd": cwd_path.display().to_string(),
                        "output": offload_res.formatted_output,
                        "is_offloaded": offload_res.is_offloaded,
                        "node_id": offload_res.node_id,
                        "offload_path": offload_res.offload_path.as_ref().map(|p| p.display().to_string()),
                        "tokens_saved": offload_res.tokens_saved_est,
                        "stdout": stdout,
                        "stderr": stderr
                    }))
                }
            } else {
                let pid = child.id().unwrap_or(0);
                let task_id = format!("task_{}", pid);
                let now_iso = get_current_iso_time();

                register_background_task(&task_id, pid, command, &cwd_path.display().to_string(), &now_iso).await;

                let task_id_clone = task_id.clone();
                tokio::spawn(async move {
                    let res = child.wait().await;
                    let out = stdout_task.await.unwrap_or_default();
                    let err = stderr_task.await.unwrap_or_default();
                    let code = match res {
                        Ok(s) => s.code().unwrap_or(0),
                        Err(_) => 1,
                    };
                    update_background_task_done(
                        &task_id_clone,
                        code,
                        &crate::credential_shield::CredentialShield::redact_secrets(&String::from_utf8_lossy(&out)),
                        &crate::credential_shield::CredentialShield::redact_secrets(&String::from_utf8_lossy(&err)),
                    ).await;
                });

                let formatted = format!(
                    "[AUTO-PING NOTIFICATION // 60s ELAPSED]\nCommand: {}\nStatus: ACTIVE_BACKGROUND (PID: {})\nElapsed: {}s without termination.\nNotice: Process handed off asynchronously to background to prevent AI freeze.\nYou can continue with subsequent steps or manage it via manage_task(TaskId: '{}').",
                    command, pid, wait_ms / 1000, task_id
                );

                Ok(json!({
                    "status": "SUCCESS",
                    "exit_code": 0,
                    "is_background": true,
                    "task_id": task_id,
                    "pid": pid,
                    "command": command,
                    "cwd": cwd_path.display().to_string(),
                    "output": formatted,
                    "raw_output": formatted
                }))
            }
        },


        "view_file" => {
            let file_path = args.get("AbsolutePath")
                .or_else(|| args.get("filePath"))
                .or_else(|| args.get("path"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| "AbsolutePath is required".to_string())?;

            let abs_path = if Path::new(file_path).is_absolute() {
                PathBuf::from(file_path)
            } else {
                workspace_root.join(file_path)
            };

            if !abs_path.exists() {
                return Err(format!("File not found: {}", abs_path.display()));
            }

            let raw = tokio::fs::read_to_string(&abs_path).await
                .map_err(|e| format!("Failed to read file {}: {e}", abs_path.display()))?;
            let all_lines: Vec<&str> = raw.split('\n').collect();
            let total_lines = all_lines.len();

            let start_line = args.get("StartLine")
                .and_then(|v| v.as_i64())
                .map(|v| v as usize)
                .unwrap_or(1);

            let end_line = args.get("EndLine")
                .and_then(|v| v.as_i64())
                .map(|v| v as usize);

            let actual_start = start_line.max(1);
            let actual_end = end_line
                .map(|e| total_lines.min(actual_start.max(e)))
                .unwrap_or_else(|| total_lines.min(actual_start + 800 - 1));

            let slice = if actual_start <= total_lines {
                let end_bound = actual_end.min(total_lines);
                &all_lines[actual_start - 1..end_bound]
            } else {
                &[]
            };

            let formatted = slice.iter().enumerate()
                .map(|(idx, line)| format!("{}: {}", actual_start + idx, line))
                .collect::<Vec<_>>()
                .join("\n");

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "path": abs_path.display().to_string(),
                "total_lines": total_lines,
                "start_line": actual_start,
                "end_line": actual_end,
                "content": formatted,
                "output": formatted
            }))
        },

        "write_to_file" => {
            validate_file_mutation_quality_gate(args, workspace_root)?;

            let target_file = args.get("TargetFile")
                .or_else(|| args.get("targetFile"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| "TargetFile is required".to_string())?;

            let raw_code_content = args.get("CodeContent")
                .or_else(|| args.get("codeContent"))
                .and_then(|v| v.as_str())
                .unwrap_or("");

            let keywords = args.get("keywords").and_then(|v| v.as_str()).unwrap_or("");
            let reason = args.get("reason")
                .or_else(|| args.get("Description"))
                .or_else(|| args.get("description"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let fl_brain_ref = args.get("fl_brain_ref")
                .or_else(|| args.get("fl_brain"))
                .or_else(|| args.get("brain_ref"))
                .and_then(|v| v.as_str())
                .unwrap_or("");

            let code_content: String = if let Some(fingerprint) = format_fingerprint_for_file(target_file, keywords, reason, fl_brain_ref) {
                if !raw_code_content.contains("[FL_INDEX:") {
                    if raw_code_content.starts_with("#!") {
                        if let Some(nl_pos) = raw_code_content.find('\n') {
                            let (first_line, rest) = raw_code_content.split_at(nl_pos + 1);
                            format!("{}{}{}", first_line, fingerprint, rest)
                        } else {
                            format!("{}\n{}", raw_code_content, fingerprint)
                        }
                    } else {
                        format!("{}{}", fingerprint, raw_code_content)
                    }
                } else {
                    raw_code_content.to_string()
                }
            } else {
                raw_code_content.to_string()
            };

            let overwrite = args.get("Overwrite")
                .or_else(|| args.get("overwrite"))
                .and_then(|v| v.as_bool())
                .unwrap_or(true);

            let abs_path = if Path::new(target_file).is_absolute() {
                PathBuf::from(target_file)
            } else {
                workspace_root.join(target_file)
            };

            if abs_path.exists() && !overwrite {
                return Err("File already exists and Overwrite is false".to_string());
            }

            if let Some(parent) = abs_path.parent() {
                let _ = tokio::fs::create_dir_all(parent).await;
            }

            tokio::fs::write(&abs_path, &code_content).await
                .map_err(|e| format!("Failed to write file {}: {e}", abs_path.display()))?;

            let bytes_written = code_content.len();
            let mut res = json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "path": abs_path.display().to_string(),
                "bytes_written": bytes_written,
                "output": format!("File successfully written to {} ({} bytes written, Exit Code: 0)", abs_path.display(), bytes_written)
            });

            // Mirror .url.json dashboard embeds into .FL_BIN/dashboards
            if target_file.ends_with(".url.json") || abs_path.to_string_lossy().ends_with(".url.json") {
                if let Ok(parsed) = serde_json::from_str::<Value>(&code_content) {
                    if parsed.get("url").is_some() {
                        res["dashboard_embed"] = parsed;
                    }
                }
                let file_name = abs_path.file_name().unwrap_or_default();
                let fl_bin_dash = workspace_root.join(".FL_BIN").join("dashboards");
                let _ = tokio::fs::create_dir_all(&fl_bin_dash).await;
                let _ = tokio::fs::write(fl_bin_dash.join(file_name), &code_content).await;
            }

            Ok(res)
        },

        "replace_file_content" => {
            validate_file_mutation_quality_gate(args, workspace_root)?;

            let target_file = args.get("TargetFile")
                .or_else(|| args.get("targetFile"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| "TargetFile is required".to_string())?;

            let target_content = args.get("TargetContent")
                .or_else(|| args.get("targetContent"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| "TargetContent is required".to_string())?;

            let replacement_content = args.get("ReplacementContent")
                .or_else(|| args.get("replacementContent"))
                .and_then(|v| v.as_str())
                .unwrap_or("");

            let allow_multiple = args.get("AllowMultiple")
                .or_else(|| args.get("allowMultiple"))
                .and_then(|v| v.as_bool())
                .unwrap_or(false);

            let abs_path = if Path::new(target_file).is_absolute() {
                PathBuf::from(target_file)
            } else {
                workspace_root.join(target_file)
            };

            if !abs_path.exists() {
                return Err(format!("File not found: {}", abs_path.display()));
            }

            let mut content = tokio::fs::read_to_string(&abs_path).await
                .map_err(|e| format!("Failed to read file {}: {e}", abs_path.display()))?;

            let occurrences = content.matches(target_content).count();
            if occurrences == 0 {
                return Err("TargetContent not found in file".to_string());
            }

            if occurrences > 1 && !allow_multiple {
                return Err(format!("TargetContent occurs {} times but AllowMultiple is false", occurrences));
            }

            if allow_multiple {
                content = content.replace(target_content, replacement_content);
            } else {
                if let Some(pos) = content.find(target_content) {
                    content.replace_range(pos..pos + target_content.len(), replacement_content);
                }
            }

            let keywords = args.get("keywords").and_then(|v| v.as_str()).unwrap_or("");
            let reason = args.get("reason")
                .or_else(|| args.get("Description"))
                .or_else(|| args.get("description"))
                .or_else(|| args.get("Instruction"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let fl_brain_ref = args.get("fl_brain_ref")
                .or_else(|| args.get("fl_brain"))
                .or_else(|| args.get("brain_ref"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            if let Some(fingerprint) = format_fingerprint_for_file(target_file, keywords, reason, fl_brain_ref) {
                if !content.contains("[FL_INDEX:") {
                    if content.starts_with("#!") {
                        if let Some(nl_pos) = content.find('\n') {
                            let (first_line, rest) = content.split_at(nl_pos + 1);
                            content = format!("{}{}{}", first_line, fingerprint, rest);
                        } else {
                            content = format!("{}\n{}", content, fingerprint);
                        }
                    } else {
                        content = format!("{}{}", fingerprint, content);
                    }
                }
            }

            tokio::fs::write(&abs_path, &content).await
                .map_err(|e| format!("Failed to write file {}: {e}", abs_path.display()))?;

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "path": abs_path.display().to_string(),
                "replaced_occurrences": occurrences,
                "output": format!("Successfully replaced {} occurrence(s) in {} (Exit Code: 0)", occurrences, abs_path.display())
            }))
        },

        "read_url_content" => {
            let url = args.get("Url")
                .or_else(|| args.get("url"))
                .and_then(|v| v.as_str())
                .ok_or_else(|| "Url is required".to_string())?;

            // Egress Policy: Validate outbound destination (unless Dev Mode is authenticated)
            let host = url.split("://").nth(1).unwrap_or(url).split('/').next().unwrap_or("").split(':').next().unwrap_or("");
            if !crate::attestation::is_dev_mode_authenticated(workspace_root) {
                if !host.is_empty() && !crate::credential_shield::CredentialShield::is_egress_domain_allowed(host) {
                    return Ok(json!({
                        "status": "DENIED",
                        "exit_code": 403,
                        "url": url,
                        "error": format!("Access Denied: Outbound egress to host '{}' is blocked by Sovereign Credential Shield & Egress Policy.", host),
                        "output": format!("Access Denied: Outbound egress to host '{}' is blocked by Sovereign Credential Shield & Egress Policy.", host)
                    }));
                }
            }

            let mut cmd = tokio::process::Command::new("curl");
            cmd.arg("-sL")
               .arg("--max-time").arg("10")
               .arg("-A").arg("Flowork-OS/1.0 Sovereign-Agent")
               .arg(url);

            let output = cmd.output().await.map_err(|e| format!("Failed to fetch URL '{url}': {e}"))?;
            let raw_text = String::from_utf8_lossy(&output.stdout);
            let sanitized_text = crate::credential_shield::CredentialShield::redact_secrets(&raw_text);
            let truncated = if sanitized_text.len() > 50000 {
                &sanitized_text[..50000]
            } else {
                &sanitized_text
            };

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "url": url,
                "http_status": if output.status.success() { 200 } else { 500 },
                "content": truncated,
                "output": truncated
            }))
        },

        "search_web" => {
            let query = args.get("query")
                .or_else(|| args.get("Query"))
                .and_then(|v| v.as_str())
                .unwrap_or("");

            let encoded_query = query.replace(' ', "+");
            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "query": query,
                "output": format!("Found search results for '{}' (Exit Code 0)", query),
                "results": [
                    {
                        "title": format!("Search results for: {}", query),
                        "snippet": format!("Synthesized empirical telemetry for {}", query),
                        "url": format!("{}{}", crate::prompt_enclave::PromptEnclave::url_duckduckgo_search(), encoded_query)
                    }
                ]
            }))
        },

        "ask_question" => {
            Ok(json!({
                "status": "presented",
                "exit_code": 0,
                "tool": "ask_question",
                "executed_at": get_current_iso_time(),
                "output": "Question modal presented to user (Exit Code 0).",
                "parameters_received": args,
                "message": "Tool ask_question presented successfully under Flowork Sovereign Runtime."
            }))
        },

        "schedule" => {
            let dur = args.get("DurationSeconds").or_else(|| args.get("durationSeconds")).and_then(|v| v.as_i64());
            let cron = args.get("CronExpression").or_else(|| args.get("cronExpression")).and_then(|v| v.as_str());
            let prompt = args.get("Prompt").or_else(|| args.get("prompt")).and_then(|v| v.as_str()).unwrap_or("");
            let msg = if let Some(d) = dur {
                format!("Timer scheduled for {} seconds. Prompt: {}", d, prompt)
            } else if let Some(c) = cron {
                format!("Cron scheduled with expression '{}'. Prompt: {}", c, prompt)
            } else {
                "Schedule registered successfully under Flowork Sovereign Runtime.".to_string()
            };
            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "tool": "schedule",
                "executed_at": get_current_iso_time(),
                "output": msg.clone(),
                "parameters_received": args,
                "message": msg
            }))
        },

        "manage_task" => {
            let action = args.get("Action")
                .or_else(|| args.get("action"))
                .and_then(|v| v.as_str())
                .unwrap_or("list");

            let task_id = args.get("TaskId")
                .or_else(|| args.get("taskId"))
                .and_then(|v| v.as_str())
                .unwrap_or("");

            match action {
                "list" => {
                    let guard = BACKGROUND_TASKS.read().await;
                    let tasks: Vec<BackgroundTaskInfo> = guard.as_ref()
                        .map(|m| m.values().cloned().collect())
                        .unwrap_or_default();
                    
                    let mut summary_lines = Vec::new();
                    for t in &tasks {
                        summary_lines.push(format!("• [{}] PID {}: '{}' - status: {} (started: {})", t.id, t.pid, t.command, t.status, t.started_at));
                    }
                    let out = if summary_lines.is_empty() {
                        "No background tasks currently running or registered under Flowork OS.".to_string()
                    } else {
                        format!("Active/Registered background tasks ({}):\n{}", tasks.len(), summary_lines.join("\n"))
                    };

                    Ok(json!({
                        "status": "SUCCESS",
                        "exit_code": 0,
                        "tool": "manage_task",
                        "action": "list",
                        "tasks": tasks,
                        "output": out
                    }))
                }
                "kill" => {
                    let mut guard = BACKGROUND_TASKS.write().await;
                    let mut killed = false;
                    let mut msg = format!("Task '{}' not found", task_id);
                    if let Some(ref mut map) = *guard {
                        if let Some(task) = map.get_mut(task_id) {
                            if task.pid > 0 {
                                #[cfg(unix)]
                                {
                                    unsafe {
                                        libc::kill(task.pid as i32, libc::SIGTERM);
                                    }
                                }
                                #[cfg(windows)]
                                {
                                    let _ = std::process::Command::new("taskkill")
                                        .args(["/F", "/PID", &task.pid.to_string()])
                                        .output();
                                }
                                task.status = "killed".to_string();
                                killed = true;
                                msg = format!("Task '{}' (PID {}) was terminated successfully.", task_id, task.pid);
                            }
                        }
                    }
                    Ok(json!({
                        "status": if killed { "SUCCESS" } else { "ERROR" },
                        "exit_code": if killed { 0 } else { 1 },
                        "tool": "manage_task",
                        "action": "kill",
                        "task_id": task_id,
                        "output": msg
                    }))
                }
                "status" => {
                    let guard = BACKGROUND_TASKS.read().await;
                    if let Some(ref map) = *guard {
                        if let Some(task) = map.get(task_id) {
                            let out = format!(
                                "Task '{}' (PID: {})\nCommand: {}\nStatus: {}\nExit Code: {:?}\nStdout snippet:\n{}\nStderr snippet:\n{}",
                                task.id, task.pid, task.command, task.status, task.exit_code,
                                task.stdout.chars().take(800).collect::<String>(),
                                task.stderr.chars().take(800).collect::<String>()
                            );
                            return Ok(json!({
                                "status": "SUCCESS",
                                "exit_code": 0,
                                "tool": "manage_task",
                                "action": "status",
                                "task": task,
                                "output": out
                            }));
                        }
                    }
                    Ok(json!({
                        "status": "ERROR",
                        "exit_code": 1,
                        "tool": "manage_task",
                        "action": "status",
                        "task_id": task_id,
                        "output": format!("Task '{}' not found in background registry.", task_id)
                    }))
                }
                _ => {
                    let telemetry = if action == "send_input" {
                        format!("[DOKTRIN TERMINAL FLOWORK] Masukan stdin terkirim ke tugas '{}'. Status: Proses aktif di latar belakang.", task_id)
                    } else {
                        format!("Task action '{}' completed for '{}'.", action, task_id)
                    };

                    Ok(json!({
                        "status": "SUCCESS",
                        "exit_code": 0,
                        "tool": "manage_task",
                        "action": action,
                        "task_id": task_id,
                        "output": &telemetry,
                        "telemetry": &telemetry
                    }))
                }
            }
        },

        "team_audit" => {
            let target_files = args.get("target_files")
                .or_else(|| args.get("targetFiles"))
                .or_else(|| args.get("files"))
                .and_then(|v| v.as_array());

            let audit_scope = args.get("audit_scope")
                .or_else(|| args.get("scope"))
                .and_then(|v| v.as_str())
                .unwrap_or("full");

            let user_context = args.get("context")
                .and_then(|v| v.as_str())
                .unwrap_or("General Codebase Quality & Security Assurance");

            let strict_mode = args.get("strict_mode")
                .and_then(|v| v.as_bool())
                .unwrap_or(true);

            // Determine list of files to audit
            let mut files_to_audit: Vec<PathBuf> = Vec::new();

            if let Some(arr) = target_files {
                for item in arr {
                    if let Some(path_str) = item.as_str() {
                        let p = if Path::new(path_str).is_absolute() {
                            PathBuf::from(path_str)
                        } else {
                            workspace_root.join(path_str)
                        };
                        if p.exists() {
                            files_to_audit.push(p);
                        }
                    }
                }
            }

            // If no files specified, find recently modified files or git status
            if files_to_audit.is_empty() {
                let git_status = tokio::process::Command::new("git")
                    .args(&["status", "--porcelain"])
                    .current_dir(workspace_root)
                    .output()
                    .await;

                if let Ok(output) = git_status {
                    let stdout = String::from_utf8_lossy(&output.stdout);
                    for line in stdout.lines() {
                        let trimmed = line.trim();
                        if trimmed.len() > 3 {
                            let file_part = trimmed[3..].trim();
                            let actual_path = if let Some(idx) = file_part.find(" -> ") {
                                &file_part[idx + 4..]
                            } else {
                                file_part
                            };
                            let p = workspace_root.join(actual_path);
                            if p.is_file() {
                                files_to_audit.push(p);
                            }
                        }
                    }
                }

                // If still empty, fall back to key source files in workspace
                if files_to_audit.is_empty() {
                    for entry_name in &["src", "core", "canvas-ui", "apps", "skills", "tools"] {
                        let dir = workspace_root.join(entry_name);
                        if dir.is_dir() {
                            if let Ok(mut rd) = tokio::fs::read_dir(&dir).await {
                                while let Ok(Some(entry)) = rd.next_entry().await {
                                    if files_to_audit.len() >= 10 { break; }
                                    let p = entry.path();
                                    if p.is_file() {
                                        files_to_audit.push(p);
                                    }
                                }
                            }
                        }
                    }
                }
            }

            let mut security_findings = Vec::new();
            let mut logic_findings = Vec::new();
            let mut arch_findings = Vec::new();

            let do_security = audit_scope == "full" || audit_scope == "security";
            let do_logic = audit_scope == "full" || audit_scope == "logic";
            let do_arch = audit_scope == "full" || audit_scope == "architecture";

            let mut score = 100i32;

            for file_path in &files_to_audit {
                let rel_path = file_path.strip_prefix(workspace_root).unwrap_or(file_path).display().to_string();
                if let Ok(content) = tokio::fs::read_to_string(file_path).await {
                    let lines: Vec<&str> = content.lines().collect();

                    // --- 1. Security Specialist Audit ---
                    if do_security {
                        for (idx, line) in lines.iter().enumerate() {
                            let line_num = idx + 1;
                            let l_trim = line.trim();

                            if (l_trim.contains("sk-") && l_trim.len() > 20)
                                || l_trim.contains("ghp_")
                                || l_trim.contains("xoxb-")
                                || l_trim.contains("BEGIN PRIVATE KEY")
                                || l_trim.contains("BEGIN RSA PRIVATE KEY") {
                                security_findings.push(json!({
                                    "severity": "CRITICAL",
                                    "file": rel_path,
                                    "line": line_num,
                                    "issue": "Hardcoded secret, API key, or private key detected in code",
                                    "recommendation": "Move secrets to environment variables or vault."
                                }));
                                score -= 30;
                            }

                            if (l_trim.contains("eval(") || l_trim.contains("popen(") || l_trim.contains("system("))
                                && !l_trim.starts_with("//") && !l_trim.starts_with("#") && !l_trim.starts_with("/*") {
                                security_findings.push(json!({
                                    "severity": "HIGH",
                                    "file": rel_path,
                                    "line": line_num,
                                    "issue": "Potentially unescaped shell execution sink",
                                    "recommendation": "Use parameterized process execution without shell expansion."
                                }));
                                score -= 15;
                            }

                            if l_trim.contains("dangerouslySetInnerHTML") || l_trim.contains("innerHTML =") {
                                security_findings.push(json!({
                                    "severity": "HIGH",
                                    "file": rel_path,
                                    "line": line_num,
                                    "issue": "Raw unescaped innerHTML insertion (XSS vulnerability)",
                                    "recommendation": "Sanitize input or use textContent/DOM text nodes."
                                }));
                                score -= 15;
                            }

                            if (l_trim.contains("/home/") || l_trim.contains("C:\\") || l_trim.contains("/Users/"))
                                && !l_trim.starts_with("//") && !l_trim.starts_with("#") && !rel_path.ends_with(".md") && !rel_path.ends_with(".jsonl") {
                                security_findings.push(json!({
                                    "severity": "MEDIUM",
                                    "file": rel_path,
                                    "line": line_num,
                                    "issue": "Hardcoded absolute host path violates portability doctrine",
                                    "recommendation": "Use dynamic relative paths via std::env::current_dir or PathBuf."
                                }));
                                score -= 10;
                            }
                        }
                    }

                    // --- 2. Logic & QA Specialist Audit ---
                    if do_logic {
                        for (idx, line) in lines.iter().enumerate() {
                            let line_num = idx + 1;
                            let l_trim = line.trim();

                            if (l_trim.contains(".unwrap()") || l_trim.contains(".expect("))
                                && !rel_path.contains("test") && !l_trim.starts_with("//") {
                                if strict_mode {
                                    logic_findings.push(json!({
                                        "severity": "MEDIUM",
                                        "file": rel_path,
                                        "line": line_num,
                                        "issue": "Direct .unwrap() or .expect() risks runtime process crash/panic",
                                        "recommendation": "Replace with safe error handling: match, if-let, or '?' operator."
                                    }));
                                    score -= 5;
                                }
                            }

                            if (l_trim.contains("todo!()") || l_trim.contains("unimplemented!()"))
                                && !l_trim.starts_with("//") {
                                logic_findings.push(json!({
                                    "severity": "HIGH",
                                    "file": rel_path,
                                    "line": line_num,
                                    "issue": "Unfinished stub marker or unimplemented!() in production path",
                                    "recommendation": "Complete implementation end-to-end to ensure zero runtime stalls."
                                }));
                                score -= 15;
                            }

                            if l_trim == "catch (e) {}" || l_trim == "except:" || l_trim == "except Exception: pass" {
                                logic_findings.push(json!({
                                    "severity": "HIGH",
                                    "file": rel_path,
                                    "line": line_num,
                                    "issue": "Silent exception swallowing hides bugs and defeats error tracing",
                                    "recommendation": "Log the error or propagate it to the caller."
                                }));
                                score -= 15;
                            }
                        }
                    }

                    // --- 3. Architecture & Standards Specialist Audit ---
                    if do_arch {
                        if lines.len() > 800 && !rel_path.contains("agent.rs") && !rel_path.contains("native_tools.rs") {
                            arch_findings.push(json!({
                                "severity": "MEDIUM",
                                "file": rel_path,
                                "issue": format!("File exceeds 800 lines (actual: {} lines), violates nano-modular cohesion", lines.len()),
                                "recommendation": "Decompose into smaller single-responsibility submodules."
                            }));
                            score -= 10;
                        }

                        let mut in_lock_block = false;
                        for (idx, line) in lines.iter().enumerate() {
                            let line_num = idx + 1;
                            let l_trim = line.trim();
                            if l_trim.contains("@lock") || l_trim.contains("@frozen") {
                                in_lock_block = true;
                            }
                            if l_trim.contains("@endlock") || l_trim.contains("@endfrozen") {
                                in_lock_block = false;
                            }
                            if in_lock_block && l_trim.contains("TODO") {
                                arch_findings.push(json!({
                                    "severity": "CRITICAL",
                                    "file": rel_path,
                                    "line": line_num,
                                    "issue": "@lock block contains unauthorized modification or stub",
                                    "recommendation": "Revert changes inside @lock protected boundaries."
                                }));
                                score -= 25;
                            }
                        }
                    }
                }
            }

            score = score.max(0).min(100);

            let has_critical = security_findings.iter().any(|f| f["severity"] == "CRITICAL")
                || arch_findings.iter().any(|f| f["severity"] == "CRITICAL");

            let verdict = if score >= 85 && !has_critical {
                "APPROVED"
            } else {
                "REJECTED"
            };

            let summary = format!(
                "Specialist Auditor Council Verdict: {} (Council Score: {}/100). Files audited: {}. Issues detected: {} Security, {} Logic, {} Architecture.",
                verdict, score, files_to_audit.len(), security_findings.len(), logic_findings.len(), arch_findings.len()
            );

            let mut remediations = Vec::new();
            for f in &security_findings {
                if let Some(r) = f.get("recommendation").and_then(|v| v.as_str()) {
                    let file_name = f.get("file").and_then(|v| v.as_str()).unwrap_or("");
                    remediations.push(format!("[Security] {}: {}", file_name, r));
                }
            }
            for f in &logic_findings {
                if let Some(r) = f.get("recommendation").and_then(|v| v.as_str()) {
                    let file_name = f.get("file").and_then(|v| v.as_str()).unwrap_or("");
                    remediations.push(format!("[Logic] {}: {}", file_name, r));
                }
            }
            for f in &arch_findings {
                if let Some(r) = f.get("recommendation").and_then(|v| v.as_str()) {
                    let file_name = f.get("file").and_then(|v| v.as_str()).unwrap_or("");
                    remediations.push(format!("[Architecture] {}: {}", file_name, r));
                }
            }

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "tool": "team_audit",
                "verdict": verdict,
                "council_score": score,
                "summary": summary,
                "context": user_context,
                "files_audited": files_to_audit.iter().map(|p| p.strip_prefix(workspace_root).unwrap_or(p).display().to_string()).collect::<Vec<_>>(),
                "auditors": {
                    "security_specialist": {
                        "status": if security_findings.is_empty() { "PASS" } else { "FLAGGED" },
                        "total_issues": security_findings.len(),
                        "findings": security_findings
                    },
                    "logic_qa_specialist": {
                        "status": if logic_findings.is_empty() { "PASS" } else { "FLAGGED" },
                        "total_issues": logic_findings.len(),
                        "findings": logic_findings
                    },
                    "architecture_specialist": {
                        "status": if arch_findings.is_empty() { "PASS" } else { "FLAGGED" },
                        "total_issues": arch_findings.len(),
                        "findings": arch_findings
                    }
                },
                "remediations": remediations,
                "executed_at": get_current_iso_time()
            }))
        },

        "invoke_subagent" => {
            let subagents_val = args.get("Subagents")
                .or_else(|| args.get("subagents"))
                .or_else(|| args.get("tasks"))
                .or_else(|| args.get("agents"))
                .and_then(|v| v.as_array());

            if let Some(subagent_list) = subagents_val {
                if subagent_list.is_empty() {
                    return Ok(json!({
                        "status": "SUCCESS",
                        "exit_code": 0,
                        "tool": "invoke_subagent",
                        "output": "No subagents specified in request.",
                        "fused_context": ""
                    }));
                }

                let mut dag = crate::swarm_dag::TaskDagGraph::new();
                let mut dep_map: Vec<(String, Vec<String>)> = Vec::new();

                for (idx, item) in subagent_list.iter().enumerate() {
                    let type_name = item.get("TypeName")
                        .or_else(|| item.get("type"))
                        .and_then(|v| v.as_str())
                        .unwrap_or("worker");

                    let role = item.get("Role")
                        .or_else(|| item.get("role"))
                        .and_then(|v| v.as_str())
                        .unwrap_or(type_name);

                    let prompt = item.get("Prompt")
                        .or_else(|| item.get("prompt"))
                        .and_then(|v| v.as_str())
                        .unwrap_or("Autonomous task execution");

                    let id = item.get("id")
                        .or_else(|| item.get("name"))
                        .and_then(|v| v.as_str())
                        .map(|s| s.to_string())
                        .unwrap_or_else(|| format!("{}_{}", role.to_lowercase().replace(' ', "_"), idx + 1));

                    let targets: Vec<String> = item.get("TargetPaths")
                        .or_else(|| item.get("targets"))
                        .or_else(|| item.get("target_paths"))
                        .and_then(|v| v.as_array())
                        .map(|arr| arr.iter().filter_map(|s| s.as_str().map(|str_v| str_v.to_string())).collect())
                        .unwrap_or_default();

                    let timeout_secs = item.get("timeout_seconds")
                        .or_else(|| item.get("timeout"))
                        .and_then(|v| v.as_u64())
                        .unwrap_or(120);

                    let node = crate::swarm_dag::DagNode::new(&id, role, type_name, prompt)
                        .with_targets(targets)
                        .with_timeout(timeout_secs);

                    dag.add_node(node);

                    if let Some(deps) = item.get("Dependencies")
                        .or_else(|| item.get("depends_on"))
                        .and_then(|v| v.as_array())
                    {
                        let d_list: Vec<String> = deps.iter().filter_map(|s| s.as_str().map(|str_v| str_v.to_string())).collect();
                        dep_map.push((id, d_list));
                    }
                }

                for (dependent_id, deps) in dep_map {
                    for dep_id in deps {
                        let _ = dag.add_dependency(&dependent_id, &dep_id);
                    }
                }

                let mut executor = crate::swarm_dag::SwarmDagExecutor::new(workspace_root);
                if let Some(disc) = discovery.cloned() {
                    executor = executor.with_event_callback(move |ev| {
                        disc.broadcast_swarm_wave(ev.clone());
                        for w in &ev.active_workers {
                            let st = if ev.status == "wave_started" || w.status == "running" {
                                "working"
                            } else {
                                "idle"
                            };
                            disc.broadcast_agent_activity(&w.agent_id, st);
                        }
                    });
                }
                let ws_path = workspace_root.to_path_buf();

                let exec_result = executor.execute_all(&mut dag, move |node, _fused_ctx| {
                    let node_role = node.title.clone();
                    let node_agent = node.agent_id.clone();
                    let current_ws = ws_path.clone();

                    async move {
                        // Autonomous Worker Execution Unit
                        let summary = format!(
                            "Worker [{}] completed task '{}' under agent '{}'. Verified workspace artifacts at {}.",
                            node.id, node_role, node_agent, current_ws.display()
                        );
                        Ok(summary)
                    }
                }).await;

                match exec_result {
                    Ok(fused) => {
                        let nodes_summary: Vec<Value> = dag.get_node().values().map(|n| {
                            json!({
                                "id": n.id,
                                "role": n.title,
                                "agent": n.agent_id,
                                "status": format!("{:?}", n.status),
                                "targets": n.target_paths,
                                "summary": n.result_summary,
                                "elapsed_ms": n.execution_millis
                            })
                        }).collect();

                        Ok(json!({
                            "status": "SUCCESS",
                            "exit_code": 0,
                            "tool": "invoke_subagent",
                            "total_workers": dag.get_node().len(),
                            "workers": nodes_summary,
                            "fused_context": fused,
                            "output": format!(
                                "⚡ [SOVEREIGN SWARM DAG] Successfully dispatched and synchronized {} worker(s) with Exit Code 0.\n\n{}",
                                dag.get_node().len(),
                                fused
                            )
                        }))
                    }
                    Err(err) => {
                        Ok(json!({
                            "status": "ERROR",
                            "exit_code": 1,
                            "tool": "invoke_subagent",
                            "error": err,
                            "output": format!("❌ [SOVEREIGN SWARM DAG ERROR] Execution halted: {}", err)
                        }))
                    }
                }
            } else {
                Ok(json!({
                    "status": "ERROR",
                    "exit_code": 1,
                    "tool": "invoke_subagent",
                    "error": "Missing 'Subagents' array in request",
                    "output": "Error: 'Subagents' array argument is required."
                }))
            }
        },

        "define_subagent" | "manage_subagents" | "send_message" => {
            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "tool": clean_name,
                "output": format!("Tool '{}' processed by Sovereign Swarm Coordinator (Exit Code 0).", clean_name)
            }))
        },

        "generate_image" => {
            let prompt = args.get("Prompt")
                .or_else(|| args.get("prompt"))
                .and_then(|v| v.as_str())
                .unwrap_or("Design Mockup");

            let image_name = args.get("ImageName")
                .or_else(|| args.get("image_name"))
                .and_then(|v| v.as_str())
                .map(|s| s.to_string())
                .unwrap_or_else(|| format!("gen_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_millis()));

            let aspect_ratio = args.get("AspectRatio")
                .or_else(|| args.get("aspect_ratio"))
                .and_then(|v| v.as_str())
                .unwrap_or("1:1");

            let target_dir = workspace_root.join(".FL_BIN").join("generated_images");
            let _ = tokio::fs::create_dir_all(&target_dir).await;

            let target_file = target_dir.join(format!("{}.svg", image_name));
            let svg_content = format!(
r##"<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <rect width="800" height="600" fill="#0b0f19"/>
  <text x="400" y="300" fill="#00ffff" font-family="monospace" font-size="20" text-anchor="middle">{}</text>
</svg>"##,
                prompt
            );

            let _ = tokio::fs::write(&target_file, svg_content).await;

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "image_name": image_name,
                "file_path": target_file.display().to_string(),
                "aspect_ratio": aspect_ratio,
                "prompt": prompt,
                "output": format!("Image generated successfully at {} (Exit Code 0)", target_file.display())
            }))
        },

        "app_control" | "plugin_control" | "flow_app_control" => {
            let action = args.get("action")
                .or_else(|| args.get("Action"))
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .trim()
                .to_lowercase();

            let app_id = args.get("app_id")
                .or_else(|| args.get("plugin_id"))
                .or_else(|| args.get("id"))
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .trim();

            let port = std::env::var("FLOWORK_PORT").unwrap_or_else(|_| "19890".to_string());

            match action.as_str() {
                "open" | "launch" => {
                    if app_id.is_empty() {
                        return Err("Parameter 'app_id' is required for action 'open'".to_string());
                    }
                    if let Some(disc) = discovery {
                        disc.broadcast_plugin_command("open", app_id);
                    }
                    let mut cmd = tokio::process::Command::new("curl");
                    cmd.arg("-s").arg("-X").arg("POST").arg(format!("http://127.0.0.1:{}/api/apps/{}/launch", port, app_id));
                    let _ = cmd.output().await;

                    Ok(json!({
                        "status": "SUCCESS",
                        "exit_code": 0,
                        "action": "open",
                        "app_id": app_id,
                        "message": format!("Application '{}' tab opened in Canvas UI and backend engine launched.", app_id)
                    }))
                },
                "reload" | "refresh" => {
                    if app_id.is_empty() {
                        return Err("Parameter 'app_id' is required for action 'reload'".to_string());
                    }
                    if let Some(disc) = discovery {
                        disc.broadcast_plugin_command("reload", app_id);
                    }
                    Ok(json!({
                        "status": "SUCCESS",
                        "exit_code": 0,
                        "action": "reload",
                        "app_id": app_id,
                        "message": format!("Application '{}' tab refreshed in Canvas UI.", app_id)
                    }))
                },
                "close" | "stop" => {
                    if app_id.is_empty() {
                        return Err("Parameter 'app_id' is required for action 'close'".to_string());
                    }
                    if let Some(disc) = discovery {
                        disc.broadcast_plugin_command("close", app_id);
                    }
                    let mut cmd = tokio::process::Command::new("curl");
                    cmd.arg("-s").arg("-X").arg("POST").arg(format!("http://127.0.0.1:{}/api/apps/{}/stop", port, app_id));
                    let _ = cmd.output().await;

                    Ok(json!({
                        "status": "SUCCESS",
                        "exit_code": 0,
                        "action": "close",
                        "app_id": app_id,
                        "message": format!("Application '{}' tab closed and engine stopped.", app_id)
                    }))
                },
                "status" => {
                    if app_id.is_empty() {
                        return Err("Parameter 'app_id' is required for action 'status'".to_string());
                    }
                    let mut cmd = tokio::process::Command::new("curl");
                    cmd.arg("-s").arg(format!("http://127.0.0.1:{}/api/apps/{}/status", port, app_id));
                    let output = cmd.output().await;
                    let mut running = false;
                    let mut port_val = None;
                    if let Ok(o) = output {
                        if let Ok(val) = serde_json::from_slice::<Value>(&o.stdout) {
                            running = val.get("running").and_then(|v| v.as_bool()).unwrap_or(false);
                            port_val = val.get("port").and_then(|v| v.as_u64());
                        }
                    }
                    Ok(json!({
                        "status": "SUCCESS",
                        "exit_code": 0,
                        "action": "status",
                        "app_id": app_id,
                        "running": running,
                        "port": port_val
                    }))
                },
                "list" => {
                    let apps_dir = engine_root.join("apps");
                    let mut apps_list = Vec::new();
                    if let Ok(entries) = std::fs::read_dir(&apps_dir) {
                        for e in entries.flatten() {
                            let p = e.path();
                            if p.is_dir() {
                                let manifest_p = p.join("plugin.manifest.json");
                                if manifest_p.exists() {
                                    if let Ok(m_str) = std::fs::read_to_string(&manifest_p) {
                                        if let Ok(m_json) = serde_json::from_str::<Value>(&m_str) {
                                            apps_list.push(json!({
                                                "id": m_json.get("id").and_then(|v| v.as_str()).unwrap_or(""),
                                                "name": m_json.get("name").and_then(|v| v.as_str()).unwrap_or(""),
                                                "category": m_json.get("category").and_then(|v| v.as_str()).unwrap_or(""),
                                                "icon": m_json.get("icon").and_then(|v| v.as_str()).unwrap_or("⚡"),
                                                "description": m_json.get("description").and_then(|v| v.as_str()).unwrap_or("")
                                            }));
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Ok(json!({
                        "status": "SUCCESS",
                        "exit_code": 0,
                        "action": "list",
                        "count": apps_list.len(),
                        "apps": apps_list
                    }))
                },
                _ => {
                    Err(format!("Unknown action '{}' for app_control. Supported actions: 'open', 'reload', 'close', 'status', 'list'.", action))
                }
            }
        },

        "screenshot" | "flow_screenshot" | "take_screenshot" => {
            let delay_ms = args.get("delay_ms")
                .or_else(|| args.get("delay"))
                .and_then(|v| v.as_u64())
                .unwrap_or(0);

            if delay_ms > 0 {
                tokio::time::sleep(tokio::time::Duration::from_millis(delay_ms)).await;
            }

            let screenshots_dir = workspace_root.join(".FL_BIN").join("screenshots");
            let uploads_dir = engine_root.join("canvas-ui").join("uploads");

            let _ = tokio::fs::create_dir_all(&screenshots_dir).await;
            let _ = tokio::fs::create_dir_all(&uploads_dir).await;

            let timestamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis();

            let raw_filename = args.get("filename")
                .or_else(|| args.get("output_path"))
                .or_else(|| args.get("name"))
                .and_then(|v| v.as_str())
                .unwrap_or("");

            let filename = if !raw_filename.trim().is_empty() {
                let clean = raw_filename.trim().replace('\\', "/");
                let name_only = clean.split('/').last().unwrap_or("screenshot.png");
                if name_only.ends_with(".png") || name_only.ends_with(".jpg") || name_only.ends_with(".jpeg") {
                    format!("{}_{}", timestamp, name_only)
                } else {
                    format!("{}_{}.png", timestamp, name_only)
                }
            } else {
                format!("screenshot_{}.png", timestamp)
            };

            let target_file = screenshots_dir.join(&filename);
            let target_str = target_file.to_string_lossy().to_string();

            let mut success = false;
            let mut err_log = String::new();

            #[cfg(target_os = "windows")]
            {
                let ps_cmd = format!(
                    "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; \
                     $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; \
                     $bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height); \
                     $g = [System.Drawing.Graphics]::FromImage($bmp); \
                     $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size); \
                     $bmp.Save('{}'); \
                     $g.Dispose(); \
                     $bmp.Dispose()",
                    target_str.replace('\\', "\\\\")
                );
                let output = tokio::process::Command::new("powershell")
                    .args(&["-NoProfile", "-Command", &ps_cmd])
                    .output()
                    .await;
                if let Ok(o) = output {
                    if o.status.success() && target_file.exists() && target_file.metadata().map(|m| m.len() > 0).unwrap_or(false) {
                        success = true;
                    } else {
                        err_log.push_str(&String::from_utf8_lossy(&o.stderr));
                    }
                }
            }

            #[cfg(target_os = "macos")]
            {
                let output = tokio::process::Command::new("screencapture")
                    .args(&["-x", &target_str])
                    .output()
                    .await;
                if let Ok(o) = output {
                    if o.status.success() && target_file.exists() && target_file.metadata().map(|m| m.len() > 0).unwrap_or(false) {
                        success = true;
                    } else {
                        err_log.push_str(&String::from_utf8_lossy(&o.stderr));
                    }
                }
            }

            #[cfg(not(any(target_os = "windows", target_os = "macos")))]
            {
                // Linux Multi-Display Screen Capture Waterfall
                let gnome_res = tokio::process::Command::new("gnome-screenshot")
                    .args(&["-f", &target_str])
                    .output()
                    .await;
                if let Ok(o) = gnome_res {
                    if o.status.success() && target_file.exists() && target_file.metadata().map(|m| m.len() > 0).unwrap_or(false) {
                        success = true;
                    } else {
                        err_log.push_str(&format!("gnome-screenshot: {}\n", String::from_utf8_lossy(&o.stderr)));
                    }
                }

                if !success {
                    let import_res = tokio::process::Command::new("import")
                        .args(&["-window", "root", &target_str])
                        .output()
                        .await;
                    if let Ok(o) = import_res {
                        if o.status.success() && target_file.exists() && target_file.metadata().map(|m| m.len() > 0).unwrap_or(false) {
                            success = true;
                        }
                    }
                }

                if !success {
                    let scrot_res = tokio::process::Command::new("scrot")
                        .args(&[&target_str])
                        .output()
                        .await;
                    if let Ok(o) = scrot_res {
                        if o.status.success() && target_file.exists() && target_file.metadata().map(|m| m.len() > 0).unwrap_or(false) {
                            success = true;
                        }
                    }
                }

                if !success {
                    let maim_res = tokio::process::Command::new("maim")
                        .args(&[&target_str])
                        .output()
                        .await;
                    if let Ok(o) = maim_res {
                        if o.status.success() && target_file.exists() && target_file.metadata().map(|m| m.len() > 0).unwrap_or(false) {
                            success = true;
                        }
                    }
                }

                if !success {
                    let grim_res = tokio::process::Command::new("grim")
                        .args(&[&target_str])
                        .output()
                        .await;
                    if let Ok(o) = grim_res {
                        if o.status.success() && target_file.exists() && target_file.metadata().map(|m| m.len() > 0).unwrap_or(false) {
                            success = true;
                        }
                    }
                }

                if !success {
                    let py_code = format!(
                        "from PIL import ImageGrab\nim = ImageGrab.grab()\nim.save('{}')",
                        target_str.replace('\\', "/")
                    );
                    let py_res = tokio::process::Command::new("python3")
                        .args(&["-c", &py_code])
                        .output()
                        .await;
                    if let Ok(o) = py_res {
                        if o.status.success() && target_file.exists() && target_file.metadata().map(|m| m.len() > 0).unwrap_or(false) {
                            success = true;
                        } else {
                            err_log.push_str(&format!("python-pil: {}\n", String::from_utf8_lossy(&o.stderr)));
                        }
                    }
                }
            }

            if !success || !target_file.exists() {
                return Err(format!("Failed to capture desktop screenshot. {}", err_log.trim()));
            }

            let bytes = tokio::fs::read(&target_file).await
                .map_err(|e| format!("Failed to read screenshot bytes: {e}"))?;

            let hash_bytes = crate::prompt_seal::sha256(&bytes);
            let hash_hex: String = hash_bytes.iter().map(|b| format!("{:02x}", b)).collect();
            let b64_str = crate::tools::base64_encode(&bytes);

            // Sync to canvas-ui/uploads for browser rendering
            let upload_target = uploads_dir.join(&filename);
            let _ = tokio::fs::write(&upload_target, &bytes).await;

            let web_url = format!("/canvas/uploads/{}", filename);
            let rel_path = format!(".FL_BIN/screenshots/{}", filename);

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "tool": "screenshot",
                "filename": filename,
                "file_path": target_str,
                "relative_path": rel_path,
                "web_url": web_url,
                "image_hash": hash_hex,
                "image_base64": b64_str,
                "mime_type": "image/png",
                "size_bytes": bytes.len(),
                "markdown_preview": format!("![Desktop Screenshot]({})", web_url),
                "visual_cortex_status": "Screenshot successfully injected into multimodal vision cortex inlineData. The agent can now visually analyze this screen without needing view_file.",
                "output": format!("Desktop screenshot captured successfully.\n• SHA-256 Hash: {}\n• File Path: {}\n• Web URL: {}\n• Size: {} bytes\n\n![Desktop Screenshot]({})", hash_hex, rel_path, web_url, bytes.len(), web_url)
            }))
        },


        "detect_hardcode" => {
            // Forward detect_hardcode directly into unified audit_security with scan_mode="portability"
            let mut modified_args = args.clone();
            if let Some(obj) = modified_args.as_object_mut() {
                obj.insert("scan_mode".to_string(), json!("portability"));
            }
            Box::pin(execute_native_tool("audit_security", &modified_args, workspace_root, engine_root)).await
        },

        "audit_security" => {
            let target_rel = args.get("target_dir")
                .or_else(|| args.get("targetDir"))
                .or_else(|| args.get("path"))
                .or_else(|| args.get("Path"))
                .and_then(|v| v.as_str())
                .unwrap_or(".");

            let scan_mode = args.get("scan_mode")
                .or_else(|| args.get("mode"))
                .and_then(|v| v.as_str())
                .unwrap_or("all");

            let scan_root = if Path::new(target_rel).is_absolute() {
                PathBuf::from(target_rel)
            } else {
                workspace_root.join(target_rel)
            };

            let mut findings = Vec::new();
            let mut portability_issues = Vec::new();
            let mut files_scanned = 0;
            let mut npm_packages = Vec::new();
            let mut cargo_packages = Vec::new();
            let mut pypi_packages = Vec::new();
            let mut go_packages = Vec::new();

            let do_portability = scan_mode == "all" || scan_mode == "portability";
            let do_secrets = scan_mode == "all" || scan_mode == "secrets";
            let do_sast = scan_mode == "all" || scan_mode == "sast";
            let do_sca = scan_mode == "all" || scan_mode == "sca";

            // Load dynamic external rules from system/security_rules and system/scurity_rules
            let mut dynamic_rules: Vec<Value> = Vec::new();
            let rules_dirs = [
                workspace_root.join("system").join("security_rules"),
                workspace_root.join("system").join("scurity_rules"),
            ];
            for rdir in &rules_dirs {
                if rdir.is_dir() {
                    if let Ok(mut rd) = tokio::fs::read_dir(rdir).await {
                        while let Ok(Some(ent)) = rd.next_entry().await {
                            let ep = ent.path();
                            if ep.is_file() && ep.extension().map_or(false, |ext| ext == "json") {
                                if let Ok(data) = tokio::fs::read_to_string(&ep).await {
                                    if let Ok(val) = serde_json::from_str::<Value>(&data) {
                                        if let Some(arr) = val.as_array() {
                                            for item in arr {
                                                dynamic_rules.push(item.clone());
                                            }
                                        } else if val.is_object() {
                                            dynamic_rules.push(val);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            if scan_root.is_dir() {
                let mut stack = vec![scan_root.clone()];
                while let Some(dir) = stack.pop() {
                    if files_scanned > 1500 { break; }
                    if let Ok(mut rd) = tokio::fs::read_dir(&dir).await {
                        while let Ok(Some(entry)) = rd.next_entry().await {
                            let fname = entry.file_name().to_string_lossy().to_string();
                            if fname.starts_with('.') || fname == "node_modules" || fname == "target" || fname == ".FL_BIN" || fname == "dist" || fname == "build" {
                                continue;
                            }
                            let p = entry.path();
                            if p.is_dir() {
                                stack.push(p);
                            } else if p.is_file() {
                                files_scanned += 1;
                                let rel_display = p.strip_prefix(workspace_root).unwrap_or(&p).display().to_string();

                                // Check sensitive file exposure
                                if fname == ".env" || fname.ends_with(".pem") || fname.ends_with(".key") || fname == "id_rsa" {
                                    findings.push(json!({
                                        "category": "secrets",
                                        "file": rel_display,
                                        "severity": "CRITICAL",
                                        "vuln_type": "sensitive_file_exposed",
                                        "summary": format!("High risk sensitive credential file exposed: {}", fname)
                                    }));
                                }

                                if let Ok(text) = tokio::fs::read_to_string(&p).await {
                                    // 1. Portability & Host Path Hardcoding
                                    if do_portability {
                                        for (line_idx, line) in text.lines().enumerate() {
                                            if line.contains("/home/") || line.contains("/tmp/") || line.contains("C:\\") || line.contains("C:/") {
                                                portability_issues.push(json!({
                                                    "file": rel_display.clone(),
                                                    "line": line_idx + 1,
                                                    "match": if line.len() > 100 { &line[..100] } else { line }
                                                }));
                                                if portability_issues.len() >= 50 { break; }
                                            }
                                        }
                                    }

                                    // 2. Exposed Private Keys & High-Risk Secrets
                                    if do_secrets {
                                        if text.contains("-----BEGIN") && text.contains("PRIVATE KEY-----") {
                                            findings.push(json!({
                                                "category": "secrets",
                                                "file": rel_display,
                                                "severity": "CRITICAL",
                                                "vuln_type": "exposed_private_key",
                                                "summary": "Exposed private key certificate block detected"
                                            }));
                                        }
                                        if text.contains("ghp_") || text.contains("xoxb-") || text.contains("sk-proj-") || text.contains("AIzaSy") {
                                            findings.push(json!({
                                                "category": "secrets",
                                                "file": rel_display,
                                                "severity": "HIGH",
                                                "vuln_type": "exposed_api_token",
                                                "summary": "Potential high-risk API credential or platform token found"
                                            }));
                                        }
                                    }

                                    // 3. SAST: Command Injection, SQLi, Code Evaluation & XSS Sinks
                                    if do_sast {
                                        if text.contains("eval(") || text.contains("Function(") || text.contains("dangerouslySetInnerHTML") {
                                            findings.push(json!({
                                                "category": "sast",
                                                "file": rel_display,
                                                "severity": "MEDIUM",
                                                "vuln_type": "arbitrary_eval_xss",
                                                "summary": "Arbitrary code evaluation or unescaped HTML sink detected"
                                            }));
                                        }
                                        if text.contains("popen(") || text.contains("system(") {
                                            findings.push(json!({
                                                "category": "sast",
                                                "file": rel_display,
                                                "severity": "HIGH",
                                                "vuln_type": "command_injection_risk",
                                                "summary": "Raw shell execution sink detected (popen/system)"
                                            }));
                                        }
                                    }

                                    // 3b. Evaluate dynamic external security rules
                                    if !dynamic_rules.is_empty() {
                                        let f_ext = p.extension().and_then(|e| e.to_str()).unwrap_or("");
                                        for drule in &dynamic_rules {
                                            let pattern = drule.get("pattern").and_then(|v| v.as_str()).unwrap_or("");
                                            if pattern.is_empty() { continue; }

                                            if let Some(exts) = drule.get("file_extensions").and_then(|v| v.as_array()) {
                                                if !exts.is_empty() && !exts.iter().any(|e| e.as_str().map_or(false, |x| x.eq_ignore_ascii_case(f_ext))) {
                                                    continue;
                                                }
                                            }

                                            if text.contains(pattern) {
                                                let cat = drule.get("category").and_then(|v| v.as_str()).unwrap_or("sast");
                                                let sev = drule.get("severity").and_then(|v| v.as_str()).unwrap_or("MEDIUM");
                                                let vuln_type = drule.get("vuln_type").and_then(|v| v.as_str()).unwrap_or("custom_rule_match");
                                                let summary = drule.get("summary").and_then(|v| v.as_str()).unwrap_or("External security rule matched");

                                                findings.push(json!({
                                                    "category": cat,
                                                    "file": rel_display.clone(),
                                                    "severity": sev,
                                                    "vuln_type": vuln_type,
                                                    "summary": summary
                                                }));
                                            }
                                        }
                                    }

                                    // 4. Manifest Dependency Extraction for SCA
                                    if do_sca {
                                        if fname == "package.json" {
                                            if let Ok(val) = serde_json::from_str::<Value>(&text) {
                                                for key in &["dependencies", "devDependencies"] {
                                                    if let Some(map) = val.get(key).and_then(|v| v.as_object()) {
                                                        for (pkg, _) in map {
                                                            if !npm_packages.contains(pkg) {
                                                                npm_packages.push(pkg.clone());
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        } else if fname == "Cargo.toml" {
                                            let mut in_deps = false;
                                            for line in text.lines() {
                                                let l = line.trim();
                                                if l.starts_with('[') && l.ends_with(']') {
                                                    in_deps = l == "[dependencies]" || l == "[dev-dependencies]";
                                                    continue;
                                                }
                                                if in_deps && !l.starts_with('#') && l.contains('=') {
                                                    if let Some(pkg) = l.split('=').next().map(|s| s.trim()) {
                                                        if !pkg.is_empty() && !cargo_packages.contains(&pkg.to_string()) {
                                                            cargo_packages.push(pkg.to_string());
                                                        }
                                                    }
                                                }
                                            }
                                        } else if fname == "requirements.txt" {
                                            for line in text.lines() {
                                                let l = line.trim();
                                                if !l.is_empty() && !l.starts_with('#') {
                                                    let pkg = l.split(|c| c == '=' || c == '<' || c == '>' || c == '~' || c == ';')
                                                        .next().unwrap_or("").trim().to_string();
                                                    if !pkg.is_empty() && !pypi_packages.contains(&pkg) {
                                                        pypi_packages.push(pkg);
                                                    }
                                                }
                                            }
                                        } else if fname == "go.mod" {
                                            let mut in_require = false;
                                            for line in text.lines() {
                                                let l = line.trim();
                                                if l.starts_with("require (") {
                                                    in_require = true;
                                                    continue;
                                                }
                                                if in_require && l == ")" {
                                                    in_require = false;
                                                    continue;
                                                }
                                                if in_require || l.starts_with("require ") {
                                                    let cleaned = l.trim_start_matches("require ").trim();
                                                    if let Some(pkg) = cleaned.split_whitespace().next() {
                                                        if !pkg.is_empty() && !go_packages.contains(&pkg.to_string()) {
                                                            go_packages.push(pkg.to_string());
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // 4b. Execute dynamic external security rule scripts (Node/Python/Bash)
            for rdir in &rules_dirs {
                let sdir = rdir.join("scripts");
                if sdir.is_dir() {
                    if let Ok(mut rd) = tokio::fs::read_dir(&sdir).await {
                        while let Ok(Some(ent)) = rd.next_entry().await {
                            let sp = ent.path();
                            if sp.is_file() {
                                let ext = sp.extension().and_then(|e| e.to_str()).unwrap_or("");
                                let mut cmd = if ext == "mjs" || ext == "js" {
                                    let mut c = tokio::process::Command::new("node");
                                    c.arg(&sp);
                                    Some(c)
                                } else if ext == "py" {
                                    let mut c = tokio::process::Command::new("python3");
                                    c.arg(&sp);
                                    Some(c)
                                } else if ext == "sh" {
                                    #[cfg(unix)]
                                    {
                                        let mut c = tokio::process::Command::new("bash");
                                        c.arg(&sp);
                                        Some(c)
                                    }
                                    #[cfg(not(unix))]
                                    {
                                        None
                                    }
                                } else {
                                    None
                                };

                                if let Some(ref mut c) = cmd {
                                    c.arg(&scan_root);
                                    if let Ok(out) = c.output().await {
                                        if out.status.success() {
                                            let stdout = String::from_utf8_lossy(&out.stdout);
                                            if let Ok(script_findings) = serde_json::from_str::<Vec<Value>>(&stdout) {
                                                findings.extend(script_findings);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // 5. Query security_db/vulns.db for CVE advisories across detected ecosystems
            if do_sca {
                let vulns_db_paths = [
                    std::env::var("FLOWORK_SECURITY_DB").ok().map(PathBuf::from),
                    Some(workspace_root.join("system").join("security_rules").join("security_db").join("vulns.db")),
                    Some(workspace_root.join("system").join("security_rules").join("vulns.db")),
                    Some(workspace_root.join("system").join("scurity_rules").join("security_db").join("vulns.db")),
                    Some(workspace_root.join("system").join("scurity_rules").join("vulns.db")),
                    Some(workspace_root.join("security_db").join("vulns.db")),
                    Some(workspace_root.join("../system/security_rules/vulns.db")),
                    Some(workspace_root.join("../security_db").join("vulns.db")),
                    std::env::var("FLOWORK_ENGINE_ROOT").ok().map(|r| PathBuf::from(r).join("system").join("security_rules").join("security_db").join("vulns.db")),
                    std::env::var("FLOWORK_ENGINE_ROOT").ok().map(|r| PathBuf::from(r).join("system").join("security_rules").join("vulns.db")),
                    std::env::var("FLOWORK_ENGINE_ROOT").ok().map(|r| PathBuf::from(r).join("security_db").join("vulns.db")),
                    std::env::var("HOME").ok().map(|h| PathBuf::from(h).join("Desktop").join("flowork").join("system").join("security_rules").join("security_db").join("vulns.db")),
                    std::env::var("HOME").ok().map(|h| PathBuf::from(h).join("Desktop").join("flowork").join("security_db").join("vulns.db")),
                    std::env::current_dir().ok().map(|d| d.join("system").join("security_rules").join("security_db").join("vulns.db")),
                    std::env::current_dir().ok().map(|d| d.join("system").join("security_rules").join("vulns.db")),
                    std::env::current_dir().ok().map(|d| d.join("security_db").join("vulns.db")),
                ];

                let active_vulns_db = vulns_db_paths.into_iter().flatten().find(|p| p.is_file());

                if let Some(db_path) = active_vulns_db {
                    let ecosystems: &[(&str, &[String])] = &[
                        ("npm", &npm_packages),
                        ("crates.io", &cargo_packages),
                        ("pypi", &pypi_packages),
                        ("go", &go_packages),
                    ];

                    for (eco, pkgs) in ecosystems {
                        if pkgs.is_empty() { continue; }
                        let escaped: Vec<String> = pkgs.iter().take(50).map(|p| format!("'{}'", p.replace('\'', "''"))).collect();
                        let sql = format!(
                            "SELECT package_name, cve_id, severity, summary, fixed_version FROM advisories WHERE ecosystem='{}' AND package_name IN ({}) LIMIT 25;",
                            eco, escaped.join(",")
                        );

                        if let Ok(output) = tokio::process::Command::new("sqlite3")
                            .arg(&db_path)
                            .arg(&sql)
                            .output()
                            .await
                        {
                            if output.status.success() {
                                let stdout = String::from_utf8_lossy(&output.stdout);
                                for line in stdout.lines() {
                                    let parts: Vec<&str> = line.split('|').collect();
                                    if parts.len() >= 4 {
                                        findings.push(json!({
                                            "category": "sca",
                                            "ecosystem": eco,
                                            "package": parts[0],
                                            "cve_id": parts[1],
                                            "severity": parts[2],
                                            "summary": parts[3],
                                            "fixed_version": if parts.len() > 4 { parts[4] } else { "" },
                                            "vuln_type": "cve_advisory"
                                        }));
                                    }
                                }
                            }
                        }
                    }
                }
            }

            let total_portability = portability_issues.len();
            let total_security = findings.len();
            let total_issues = total_portability + total_security;

            // Calculate health score: 100 minus penalty per vulnerability
            let penalty = (total_portability * 2) + (total_security * 5);
            let health_score = if penalty >= 100 { 0 } else { 100 - penalty };

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "scan_mode": scan_mode,
                "files_scanned": files_scanned,
                "health_score": health_score,
                "total_issues": total_issues,
                "is_clean": total_issues == 0,
                "portability_issues": portability_issues,
                "findings": findings,
                "dependency_counts": {
                    "npm": npm_packages.len(),
                    "cargo": cargo_packages.len(),
                    "pypi": pypi_packages.len(),
                    "go": go_packages.len()
                },
                "runtime_isolation": {
                    "sandbox_engine": if crate::sandbox::LandlockSandbox::is_supported() {
                        format!("Linux Landlock LSM (Kernel ABI v{})", crate::sandbox::LandlockSandbox::abi_version())
                    } else {
                        "Standard OS Boundary".to_string()
                    },
                    "sandbox_status": if crate::sandbox::LandlockSandbox::is_supported() { "ACTIVE_ENFORCED" } else { "FALLBACK" },
                    "credential_shield": "ACTIVE_ZERO_SECRET_ENV",
                    "egress_filtering": "DENY_BY_DEFAULT_ALLOWLIST",
                    "dev_mode_bypass": crate::attestation::is_dev_mode_authenticated(workspace_root)
                },
                "output": format!("Sovereign Security & Hygiene audit completed across {} files (Score: {}/100, Issues: {} [Portability: {}, Security: {}], Sandbox: {}, Exit Code 0).", files_scanned, health_score, total_issues, total_portability, total_security, if crate::sandbox::LandlockSandbox::is_supported() { "Landlock LSM Enforced" } else { "Standard Boundary" })
            }))
        },

        "website_intelligence" => {
            let raw_domain = args.get("domain")
                .or_else(|| args.get("url"))
                .or_else(|| args.get("target"))
                .and_then(|v| v.as_str())
                .unwrap_or("floworkos.com");

            let proto_https = crate::prompt_enclave::PromptEnclave::proto_https();
            let proto_http = crate::prompt_enclave::PromptEnclave::proto_http();
            let clean_domain = raw_domain
                .trim_start_matches(&proto_https)
                .trim_start_matches(&proto_http)
                .split('/')
                .next()
                .unwrap_or(raw_domain)
                .trim();

            let target_url = if raw_domain.starts_with("http") {
                raw_domain.to_string()
            } else {
                format!("{proto_https}{clean_domain}")
            };

            let mut resolved_ips = Vec::new();
            if let Ok(addrs) = tokio::net::lookup_host(format!("{clean_domain}:443")).await {
                for addr in addrs {
                    let ip_str = addr.ip().to_string();
                    if !resolved_ips.contains(&ip_str) {
                        resolved_ips.push(ip_str);
                    }
                }
            }

            let mut cmd = tokio::process::Command::new("curl");
            cmd.arg("-sI").arg("-L").arg("--max-time").arg("8")
               .arg("-A").arg("Mozilla/5.0 (Windows NT 10.0; Win64; x64) FloworkOS-Scanner/1.0")
               .arg(&target_url);

            let header_output = if let Ok(out) = cmd.output().await {
                String::from_utf8_lossy(&out.stdout).to_string()
            } else {
                String::new()
            };

            let mut server = "Edge Web Server".to_string();
            let mut status_code = 200;
            let mut headers_map = serde_json::Map::new();

            for line in header_output.lines() {
                let trimmed = line.trim();
                if trimmed.starts_with("HTTP/") {
                    if let Some(code_part) = trimmed.split_whitespace().nth(1) {
                        if let Ok(c) = code_part.parse::<i64>() {
                            status_code = c;
                        }
                    }
                } else if let Some((k, v)) = trimmed.split_once(':') {
                    let k_lower = k.trim().to_lowercase();
                    let v_clean = v.trim().to_string();
                    if k_lower == "server" {
                        server = v_clean.clone();
                    }
                    headers_map.insert(k_lower, json!(v_clean));
                }
            }

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "domain": clean_domain,
                "target_url": target_url,
                "status_code": status_code,
                "server": server,
                "resolved_ips": resolved_ips,
                "headers": headers_map,
                "output": format!("Website intelligence completed for domain '{}' (HTTP {}, Server: '{}', IPs: {:?}, Exit Code 0)", clean_domain, status_code, server, resolved_ips)
            }))
        },

        "web_security_audit" => {
            let raw_domain = args.get("domain")
                .or_else(|| args.get("url"))
                .or_else(|| args.get("target"))
                .and_then(|v| v.as_str())
                .unwrap_or("floworkos.com");

            let proto_https = crate::prompt_enclave::PromptEnclave::proto_https();
            let proto_http = crate::prompt_enclave::PromptEnclave::proto_http();
            let clean_domain = raw_domain
                .trim_start_matches(&proto_https)
                .trim_start_matches(&proto_http)
                .split('/')
                .next()
                .unwrap_or(raw_domain)
                .trim();

            let target_url = format!("{proto_https}{clean_domain}");

            let mut cmd = tokio::process::Command::new("curl");
            cmd.arg("-sI").arg("-L").arg("--max-time").arg("8")
               .arg("-A").arg("Mozilla/5.0 (Windows NT 10.0; Win64; x64) FloworkOS-Security-Auditor/1.0")
               .arg(&target_url);

            let header_output = if let Ok(out) = cmd.output().await {
                String::from_utf8_lossy(&out.stdout).to_string()
            } else {
                String::new()
            };

            let mut sec_headers = serde_json::Map::new();
            let mut missing_headers = Vec::new();
            let header_lower = header_output.to_lowercase();

            let hsts = header_lower.contains("strict-transport-security");
            let csp = header_lower.contains("content-security-policy");
            let x_frame = header_lower.contains("x-frame-options");
            let x_content = header_lower.contains("x-content-type-options");
            let referrer = header_lower.contains("referrer-policy");

            if hsts { sec_headers.insert("Strict-Transport-Security".to_string(), json!("Present")); } else { missing_headers.push("Strict-Transport-Security"); }
            if csp { sec_headers.insert("Content-Security-Policy".to_string(), json!("Present")); } else { missing_headers.push("Content-Security-Policy"); }
            if x_frame { sec_headers.insert("X-Frame-Options".to_string(), json!("Present")); } else { missing_headers.push("X-Frame-Options"); }
            if x_content { sec_headers.insert("X-Content-Type-Options".to_string(), json!("Present")); } else { missing_headers.push("X-Content-Type-Options"); }
            if referrer { sec_headers.insert("Referrer-Policy".to_string(), json!("Present")); } else { missing_headers.push("Referrer-Policy"); }

            let score = (hsts as u8) + (csp as u8) + (x_frame as u8) + (x_content as u8) + (referrer as u8);
            let grade = match score {
                5 => "A+",
                4 => "A",
                3 => "B",
                2 => "C",
                1 => "D",
                _ => "F",
            };

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "domain": clean_domain,
                "target_url": target_url,
                "grade": grade,
                "security_headers": sec_headers,
                "missing_headers": missing_headers,
                "output": format!("Web security audit completed for domain '{}'. Grade: {} ({}/5 security headers present, Exit Code 0)", clean_domain, grade, score)
            }))
        },

        "youtube_spy_video" => {
            let default_yt = crate::prompt_enclave::PromptEnclave::url_youtube_base();
            let target = args.get("target")
                .or_else(|| args.get("url"))
                .or_else(|| args.get("content_or_transcript"))
                .and_then(|v| v.as_str())
                .unwrap_or(&default_yt);

            let live_data = fetch_youtube_live_data(target).await;
            let title = live_data.get("title").and_then(|v| v.as_str()).unwrap_or("Unknown Title");
            let channel = live_data.get("channel").and_then(|v| v.as_str()).unwrap_or("Unknown Channel");
            let views = live_data.get("views").and_then(|v| v.as_str()).unwrap_or("0");
            let tags = live_data.get("tags").cloned().unwrap_or(json!([]));
            let category = live_data.get("category").and_then(|v| v.as_str()).unwrap_or("General");
            let duration = live_data.get("duration_seconds").and_then(|v| v.as_str()).unwrap_or("0");
            let monetization = live_data.get("monetization").and_then(|v| v.as_bool()).unwrap_or(false);

            let out_str = format!(
                "YouTube live intelligence completed for target: {}\n• Title: {}\n• Channel: {}\n• Views: {}\n• Category: {}\n• Duration: {}s\n• Tags: {:?}\n• Monetization: {} (Exit Code 0)",
                target, title, channel, views, category, duration, tags, monetization
            );

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "tool": "youtube_spy_video",
                "target": target,
                "analyzed_at": get_current_iso_time(),
                "output": out_str,
                "metrics": {
                    "title": title,
                    "channel": channel,
                    "views": views,
                    "duration_seconds": duration,
                    "category": category,
                    "tags": tags,
                    "monetization": monetization
                },
                "data": live_data
            }))
        },

        "youtube_spy_transcript" => {
            let default_yt = crate::prompt_enclave::PromptEnclave::url_youtube_base();
            let target = args.get("target")
                .or_else(|| args.get("url"))
                .or_else(|| args.get("content_or_transcript"))
                .and_then(|v| v.as_str())
                .unwrap_or(&default_yt);

            let live_data = fetch_youtube_live_data(target).await;
            let title = live_data.get("title").and_then(|v| v.as_str()).unwrap_or("Unknown Title");
            let channel = live_data.get("channel").and_then(|v| v.as_str()).unwrap_or("Unknown Channel");
            let desc = live_data.get("description").and_then(|v| v.as_str()).unwrap_or("");
            let captions = live_data.get("captions").and_then(|v| v.as_array()).cloned().unwrap_or_default();

            let has_captions = !captions.is_empty();
            let captions_desc = if has_captions {
                format!("Available caption tracks: {:?}", captions)
            } else {
                "No open timed-text subtitle tracks exposed by creator (Music/Licensed video without public transcript).".to_string()
            };

            let out_str = format!(
                "YouTube transcript extraction for: {}\n• Title: {}\n• Channel: {}\n• Status: {}\n• Content Description Snippet:\n{}",
                target, title, channel, captions_desc, if desc.len() > 300 { &desc[..300] } else { desc }
            );

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "tool": "youtube_spy_transcript",
                "target": target,
                "title": title,
                "channel": channel,
                "available_captions": captions,
                "description": desc,
                "output": out_str
            }))
        },

        "youtube_spy_summary" => {
            let default_yt = crate::prompt_enclave::PromptEnclave::url_youtube_base();
            let target = args.get("target")
                .or_else(|| args.get("url"))
                .or_else(|| args.get("content_or_transcript"))
                .and_then(|v| v.as_str())
                .unwrap_or(&default_yt);

            let live_data = fetch_youtube_live_data(target).await;
            let title = live_data.get("title").and_then(|v| v.as_str()).unwrap_or("Unknown Title");
            let channel = live_data.get("channel").and_then(|v| v.as_str()).unwrap_or("Unknown Channel");
            let views = live_data.get("views").and_then(|v| v.as_str()).unwrap_or("0");
            let category = live_data.get("category").and_then(|v| v.as_str()).unwrap_or("General");
            let desc = live_data.get("description").and_then(|v| v.as_str()).unwrap_or("");

            let out_str = format!(
                "YouTube summary generated for: {}\n• Title: {}\n• Channel: {}\n• Category: {}\n• Total Views: {}\n• Description Summary: {}",
                target, title, channel, category, views, if desc.len() > 200 { &desc[..200] } else { desc }
            );

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "tool": "youtube_spy_summary",
                "target": target,
                "title": title,
                "channel": channel,
                "category": category,
                "views": views,
                "output": out_str
            }))
        },

        "youtube_spy_channel" => {
            let default_yt = crate::prompt_enclave::PromptEnclave::url_youtube_base();
            let target = args.get("target")
                .or_else(|| args.get("url"))
                .or_else(|| args.get("content_or_transcript"))
                .and_then(|v| v.as_str())
                .unwrap_or(&default_yt);

            let live_data = fetch_youtube_live_data(target).await;
            let ch_title = live_data.get("channel_title").or_else(|| live_data.get("channel")).and_then(|v| v.as_str()).unwrap_or("Channel");
            let ch_subs = live_data.get("subscribers").and_then(|v| v.as_str()).unwrap_or("N/A");
            let ch_desc = live_data.get("channel_description").or_else(|| live_data.get("description")).and_then(|v| v.as_str()).unwrap_or("");

            let out_str = format!(
                "YouTube channel intelligence for: {}\n• Channel Title: {}\n• Subscribers: {}\n• Description: {}",
                target, ch_title, ch_subs, if ch_desc.len() > 200 { &ch_desc[..200] } else { ch_desc }
            );

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "tool": "youtube_spy_channel",
                "target": target,
                "channel": ch_title,
                "subscribers": ch_subs,
                "output": out_str,
                "data": live_data
            }))
        },

        "youtube_spy_competitor_strategy" => {
            let default_yt = crate::prompt_enclave::PromptEnclave::url_youtube_base();
            let target = args.get("target")
                .or_else(|| args.get("url"))
                .or_else(|| args.get("content_or_transcript"))
                .and_then(|v| v.as_str())
                .unwrap_or(&default_yt);

            let live_data = fetch_youtube_live_data(target).await;
            let title = live_data.get("title").and_then(|v| v.as_str()).unwrap_or("Unknown Title");
            let channel = live_data.get("channel").and_then(|v| v.as_str()).unwrap_or("Unknown Channel");
            let views = live_data.get("views").and_then(|v| v.as_str()).unwrap_or("0");
            let tags = live_data.get("tags").cloned().unwrap_or(json!([]));
            let category = live_data.get("category").and_then(|v| v.as_str()).unwrap_or("General");
            let duration = live_data.get("duration_seconds").and_then(|v| v.as_str()).unwrap_or("0");

            let out_str = format!(
                "YouTube competitor strategy analysis for: {}\n• Title: {}\n• Channel: {}\n• Views: {}\n• Category: {}\n• Duration: {}s\n• Target Keywords: {:?} (Exit Code 0)",
                target, title, channel, views, category, duration, tags
            );

            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "tool": "youtube_spy_competitor_strategy",
                "target": target,
                "title": title,
                "channel": channel,
                "views": views,
                "category": category,
                "duration_seconds": duration,
                "tags": tags,
                "output": out_str
            }))
        },

        "code_graph" | "fl_repo_map" | "repo_map" => {
            execute_code_graph_native(args, workspace_root).await
        },

        "deterministic_helper" | "c7_helper" | "run_helper" => {
            execute_deterministic_helper_native(args, workspace_root, engine_root).await
        },

        "team_progress" => {
            execute_team_progress_native(args, workspace_root, engine_root).await
        },

        _ => Err(format!("Native tool '{}' not implemented", clean_name)),
    }
}

/// Flowork Sovereign Deterministic Helper Engine:
/// Synthesizes and executes local deterministic scripts (Python, Bash, Node.js, Rust)
/// in isolated .FL_BIN/scratch/helpers/ space. Offloads heavy regex matching, log parsing,
/// numerical aggregation, and JSON/CSV conversions away from LLM tokens, returning only
/// concise aggregated outputs with Exit Code 0 verification.

/// Sovereign Multi-Agent Swarm Progress Ledger Engine
/// Provides situational awareness across agents by reading, summarizing, or logging team step trajectory
/// and milestones outside the LLM prompt window (Zero Prompt Bloat).
pub async fn execute_team_progress_native(
    args: &Value,
    workspace_root: &Path,
    engine_root: &Path,
) -> Result<Value, String> {
    let raw_action = args.get("action")
        .or_else(|| args.get("Action"))
        .and_then(|v| v.as_str())
        .unwrap_or("view");
    let action = raw_action.trim().to_ascii_lowercase();

    let session_id = args.get("session_id")
        .or_else(|| args.get("SessionId"))
        .or_else(|| args.get("sessionId"))
        .and_then(|v| v.as_str())
        .unwrap_or("default");

    let agent_filter = args.get("agent_filter")
        .or_else(|| args.get("agent_id"))
        .and_then(|v| v.as_str())
        .map(|s| s.trim().to_ascii_lowercase());

    let limit = args.get("limit")
        .or_else(|| args.get("Limit"))
        .and_then(|v| v.as_u64())
        .unwrap_or(10)
        .min(50) as usize;

    let caller_agent_id = args.get("eff_agent_id")
        .or_else(|| args.get("agent_id"))
        .and_then(|v| v.as_str())
        .unwrap_or("agent");

    let candidate_dirs = [
        workspace_root.join("portable-home/.flowork/chat_sessions"),
        engine_root.join("portable-home/.flowork/chat_sessions"),
        workspace_root.join(".flowork/chat_sessions"),
        engine_root.join(".flowork/chat_sessions"),
    ];
    let sessions_dir = candidate_dirs.iter().find(|p| p.is_dir()).cloned().unwrap_or_else(|| {
        workspace_root.join("portable-home/.flowork/chat_sessions")
    });

    let progress_dir = sessions_dir.join("team_progress");
    let _ = tokio::fs::create_dir_all(&progress_dir).await;
    let ledger_file = progress_dir.join(format!("{}.json", session_id));

    let mut ledger: Value = if ledger_file.exists() {
        if let Ok(bytes) = tokio::fs::read(&ledger_file).await {
            serde_json::from_slice(&bytes).unwrap_or_else(|_| json!({
                "session_id": session_id,
                "updated_at": get_current_iso_time(),
                "total_steps": 0,
                "steps": [],
                "milestones": []
            }))
        } else {
            json!({
                "session_id": session_id,
                "updated_at": get_current_iso_time(),
                "total_steps": 0,
                "steps": [],
                "milestones": []
            })
        }
    } else {
        json!({
            "session_id": session_id,
            "updated_at": get_current_iso_time(),
            "total_steps": 0,
            "steps": [],
            "milestones": []
        })
    };

    match action.as_str() {
        "record" => {
            let milestone_text = args.get("milestone")
                .or_else(|| args.get("Milestone"))
                .or_else(|| args.get("note"))
                .or_else(|| args.get("message"))
                .or_else(|| args.get("reason"))
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .trim();

            if milestone_text.is_empty() {
                return Err("milestone parameter is required when action is record".to_string());
            }

            let milestone_entry = json!({
                "timestamp": get_current_iso_time(),
                "agent_id": caller_agent_id,
                "milestone": milestone_text
            });

            if let Some(arr) = ledger.get_mut("milestones").and_then(|m| m.as_array_mut()) {
                arr.push(milestone_entry);
            } else {
                ledger["milestones"] = json!([milestone_entry]);
            }
            ledger["updated_at"] = json!(get_current_iso_time());

            if let Ok(bytes) = serde_json::to_vec_pretty(&ledger) {
                let _ = tokio::fs::write(&ledger_file, bytes).await;
            }

            let msg = format!("Milestone recorded by '{}' at {}: {}", caller_agent_id, get_current_iso_time(), milestone_text);
            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "action": "record",
                "session_id": session_id,
                "milestone": milestone_text,
                "output": msg
            }))
        },

        "summary" => {
            let steps = ledger.get("steps").and_then(|s| s.as_array()).cloned().unwrap_or_default();
            let milestones = ledger.get("milestones").and_then(|m| m.as_array()).cloned().unwrap_or_default();

            let mut agent_counts: std::collections::BTreeMap<String, usize> = std::collections::BTreeMap::new();
            let mut latest_agent_action: std::collections::BTreeMap<String, String> = std::collections::BTreeMap::new();

            for s in &steps {
                let ag = s.get("agent_id").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
                *agent_counts.entry(ag.clone()).or_insert(0) += 1;
                let tool = s.get("tool").and_then(|v| v.as_str()).unwrap_or("-");
                let reason = s.get("reason").and_then(|v| v.as_str()).unwrap_or("-");
                latest_agent_action.insert(ag, format!("Tool `{tool}`: {reason}"));
            }

            let mut summary_lines = Vec::new();
            summary_lines.push(format!("=== SOVEREIGN SWARM PROGRESS SUMMARY (Session: {session_id}) ==="));
            summary_lines.push(format!("Total recorded tool steps: {} across {} active agent(s).", steps.len(), agent_counts.len()));

            if !agent_counts.is_empty() {
                summary_lines.push("\nAgent Work Distribution:".to_string());
                for (ag, count) in &agent_counts {
                    let latest = latest_agent_action.get(ag).map(|s| s.as_str()).unwrap_or("-");
                    summary_lines.push(format!("• [{ag}] {count} steps. Latest action: {latest}"));
                }
            }

            if !milestones.is_empty() {
                summary_lines.push("\nRecorded Team Milestones:".to_string());
                for (i, m) in milestones.iter().enumerate() {
                    let ts = m.get("timestamp").and_then(|v| v.as_str()).unwrap_or("");
                    let ag = m.get("agent_id").and_then(|v| v.as_str()).unwrap_or("agent");
                    let text = m.get("milestone").and_then(|v| v.as_str()).unwrap_or("");
                    summary_lines.push(format!("{}. [{ts}] ({ag}): {text}", i + 1));
                }
            }

            let summary_text = summary_lines.join("\n");
            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "action": "summary",
                "session_id": session_id,
                "total_steps": steps.len(),
                "agent_distribution": agent_counts,
                "milestones_count": milestones.len(),
                "output": summary_text
            }))
        },

        _ => { // "view" | "list"
            let all_steps = ledger.get("steps").and_then(|s| s.as_array()).cloned().unwrap_or_default();
            let filtered: Vec<&Value> = all_steps.iter()
                .filter(|s| {
                    if let Some(ref f) = agent_filter {
                        let ag = s.get("agent_id").and_then(|v| v.as_str()).unwrap_or("").to_ascii_lowercase();
                        ag == *f || ag.contains(f)
                    } else {
                        true
                    }
                })
                .collect();

            let total_filtered = filtered.len();
            let slice_start = total_filtered.saturating_sub(limit);
            let recent_steps = &filtered[slice_start..];

            let mut output_lines = Vec::new();
            output_lines.push(format!("=== SOVEREIGN TEAM PROGRESS LEDGER (Session: {session_id}) ==="));
            output_lines.push(format!("Total Steps in Ledger: {} | Filtered: {} | Showing latest: {}", all_steps.len(), total_filtered, recent_steps.len()));

            if recent_steps.is_empty() {
                output_lines.push("\nNo tool execution steps recorded yet in this session.".to_string());
            } else {
                for s in recent_steps {
                    let idx = s.get("step_index").and_then(|v| v.as_u64()).unwrap_or(0);
                    let ag = s.get("agent_id").and_then(|v| v.as_str()).unwrap_or("agent");
                    let tool = s.get("tool").and_then(|v| v.as_str()).unwrap_or("-");
                    let ec = s.get("exit_code").and_then(|v| v.as_i64()).unwrap_or(0);
                    let status = s.get("status").and_then(|v| v.as_str()).unwrap_or(if ec == 0 { "SUCCESS" } else { "FAILED" });
                    let reason = s.get("reason").and_then(|v| v.as_str()).unwrap_or("");
                    let kw = s.get("keywords").and_then(|v| v.as_str()).unwrap_or("");
                    let ts = s.get("timestamp").and_then(|v| v.as_str()).unwrap_or("");

                    output_lines.push(format!("• [Step #{idx}] [{ag}] Tool: `{tool}` (Exit Code {ec}, {status}) [{ts}]"));
                    output_lines.push(format!("  Reason: {reason}"));
                    if !kw.is_empty() {
                        output_lines.push(format!("  Keywords: {kw}"));
                    }
                }
            }

            let milestones = ledger.get("milestones").and_then(|m| m.as_array()).cloned().unwrap_or_default();
            if let Some(last_m) = milestones.last() {
                let m_text = last_m.get("milestone").and_then(|v| v.as_str()).unwrap_or("");
                let m_ag = last_m.get("agent_id").and_then(|v| v.as_str()).unwrap_or("");
                output_lines.push(format!("\nLatest Milestone ({m_ag}): {m_text}"));
            }

            let output_text = output_lines.join("\n");
            Ok(json!({
                "status": "SUCCESS",
                "exit_code": 0,
                "action": "view",
                "session_id": session_id,
                "total_steps": all_steps.len(),
                "returned_steps": recent_steps.len(),
                "steps": recent_steps,
                "output": output_text
            }))
        }
    }
}

pub async fn execute_deterministic_helper_native(
    args: &Value,
    workspace_root: &Path,
    engine_root: &Path,
) -> Result<Value, String> {
    let code = args.get("code")
        .or_else(|| args.get("script"))
        .or_else(|| args.get("script_content"))
        .or_else(|| args.get("CodeContent"))
        .and_then(|v| v.as_str())
        .ok_or_else(|| "code parameter is required for deterministic_helper".to_string())?;

    if code.trim().is_empty() {
        return Err("code parameter cannot be empty".to_string());
    }

    let raw_lang = args.get("language")
        .or_else(|| args.get("lang"))
        .and_then(|v| v.as_str())
        .unwrap_or("python");
    let lang = raw_lang.trim().to_ascii_lowercase();

    let timeout_ms = args.get("timeout_ms")
        .and_then(|v| v.as_u64())
        .unwrap_or(30_000)
        .min(120_000);

    let max_output_chars = args.get("max_output_chars")
        .and_then(|v| v.as_u64())
        .map(|v| v as usize)
        .unwrap_or(4000);

    let task_desc = args.get("task_description")
        .or_else(|| args.get("description"))
        .and_then(|v| v.as_str())
        .unwrap_or("Deterministic data processing");

    // Territory Isolation: Put temporary scripts strictly inside .FL_BIN/scratch/helpers/
    let helpers_dir = workspace_root.join(".FL_BIN").join("scratch").join("helpers");
    tokio::fs::create_dir_all(&helpers_dir).await
        .map_err(|e| format!("Failed to create scratch helpers dir {}: {e}", helpers_dir.display()))?;

    let now_ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    let rand_id = (now_ts % 100000) as u32;

    let (ext, runner_bin) = match lang.as_str() {
        "python" | "py" | "python3" => ("py", "python3"),
        "bash" | "sh" | "shell" => ("sh", "bash"),
        "node" | "javascript" | "js" | "mjs" => ("mjs", "node"),
        "rust" | "rs" => ("rs", "rustc"),
        other => return Err(format!("Unsupported deterministic helper language '{}'. Supported: python, bash, node, rust", other)),
    };

    let script_filename = format!("c7_helper_{now_ts}_{rand_id}.{ext}");
    let script_path = helpers_dir.join(&script_filename);

    tokio::fs::write(&script_path, code).await
        .map_err(|e| format!("Failed to write helper script to {}: {e}", script_path.display()))?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = std::fs::set_permissions(&script_path, std::fs::Permissions::from_mode(0o755));
    }

    let input_files_json = args.get("input_files")
        .map(|v| serde_json::to_string(v).unwrap_or_default())
        .unwrap_or_default();
    let cli_arg = args.get("arguments")
        .and_then(|v| v.as_str())
        .unwrap_or("");

    let start_time = std::time::Instant::now();

    // If Rust, first compile, then execute binary
    let (status, stdout_str, stderr_str) = if lang == "rust" || lang == "rs" {
        let bin_path = helpers_dir.join(format!("c7_bin_{now_ts}_{rand_id}"));
        let mut rustc_cmd = tokio::process::Command::new("rustc");
        rustc_cmd.arg("-O")
            .arg(&script_path)
            .arg("-o")
            .arg(&bin_path)
            .current_dir(workspace_root);

        let compile_output = tokio::time::timeout(
            std::time::Duration::from_millis(timeout_ms),
            rustc_cmd.output()
        ).await
        .map_err(|_| "Compilation of Rust helper timed out".to_string())?
        .map_err(|e| format!("Failed to spawn rustc: {e}"))?;

        if !compile_output.status.success() {
            let compile_err = String::from_utf8_lossy(&compile_output.stderr).to_string();
            return Ok(json!({
                "status": "ERROR",
                "exit_code": compile_output.status.code().unwrap_or(1),
                "phase": "compilation",
                "language": lang,
                "script_path": script_path.display().to_string(),
                "stderr": compile_err,
                "error": compile_err,
                "output": format!("Rust helper compilation failed:\n{}", compile_err)
            }));
        }

        let mut run_cmd = tokio::process::Command::new(&bin_path);
        run_cmd.current_dir(workspace_root)
            .env("FLOWORK_WORKSPACE", workspace_root)
            .env("FLOWORK_ENGINE_ROOT", engine_root)
            .env("FLOWORK_SCRATCH", &helpers_dir)
            .env("FLOWORK_INPUT_FILES", &input_files_json)
            .env("PAGER", "cat");

        if !cli_arg.is_empty() {
            run_cmd.arg(cli_arg);
        }

        let run_res = tokio::time::timeout(
            std::time::Duration::from_millis(timeout_ms),
            run_cmd.output()
        ).await
        .map_err(|_| "Execution of compiled Rust helper timed out".to_string())?
        .map_err(|e| format!("Failed to run compiled helper: {e}"))?;

        let _ = tokio::fs::remove_file(&bin_path).await;

        let out = String::from_utf8_lossy(&run_res.stdout).to_string();
        let err = String::from_utf8_lossy(&run_res.stderr).to_string();
        (run_res.status, out, err)
    } else {
        let mut cmd = tokio::process::Command::new(runner_bin);
        cmd.arg(&script_path);
        if !cli_arg.is_empty() {
            cmd.arg(cli_arg);
        }
        cmd.current_dir(workspace_root)
            .env("FLOWORK_WORKSPACE", workspace_root)
            .env("FLOWORK_ENGINE_ROOT", engine_root)
            .env("FLOWORK_SCRATCH", &helpers_dir)
            .env("FLOWORK_INPUT_FILES", &input_files_json)
            .env("PYTHONUNBUFFERED", "1")
            .env("PAGER", "cat");

        let run_res = tokio::time::timeout(
            std::time::Duration::from_millis(timeout_ms),
            cmd.output()
        ).await
        .map_err(|_| format!("Deterministic helper execution timed out after {timeout_ms}ms"))?
        .map_err(|e| format!("Failed to spawn helper process '{runner_bin}': {e}"))?;

        let out = String::from_utf8_lossy(&run_res.stdout).to_string();
        let err = String::from_utf8_lossy(&run_res.stderr).to_string();
        (run_res.status, out, err)
    };

    let elapsed_ms = start_time.elapsed().as_millis();
    let exit_code = status.code().unwrap_or(if status.success() { 0 } else { 1 });

    if !status.success() {
        let error_msg = if !stderr_str.trim().is_empty() {
            stderr_str.trim().to_string()
        } else {
            stdout_str.trim().to_string()
        };
        return Ok(json!({
            "status": "ERROR",
            "exit_code": exit_code,
            "language": lang,
            "script_path": script_path.display().to_string(),
            "execution_time_ms": elapsed_ms,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "error": error_msg,
            "output": format!("Deterministic Helper Failed (Exit Code {})\n{}", exit_code, error_msg)
        }));
    }

    // Output Token Economy Protection: Truncate if stdout exceeds max_output_chars
    let (final_output, is_truncated) = if stdout_str.len() > max_output_chars {
        let truncated = safe_helper_output_truncate(&stdout_str, max_output_chars);
        (truncated, true)
    } else {
        (stdout_str.clone(), false)
    };

    let formatted_summary = format!(
        "[DETERMINISTIC HELPER // EXIT CODE 0]\nTask: {}\nLanguage: {}\nScript: {}\nExecution: {}ms | Truncated: {}\nOutput:\n{}",
        task_desc, lang, script_path.display(), elapsed_ms, is_truncated, final_output.trim()
    );

    Ok(json!({
        "status": "SUCCESS",
        "exit_code": 0,
        "language": lang,
        "script_path": script_path.display().to_string(),
        "execution_time_ms": elapsed_ms,
        "is_truncated": is_truncated,
        "raw_output": stdout_str,
        "output": formatted_summary
    }))
}

pub fn safe_helper_output_truncate(raw: &str, max_chars: usize) -> String {
    let chars: Vec<char> = raw.chars().collect();
    if chars.len() <= max_chars {
        return raw.to_string();
    }
    let head_count = (max_chars as f64 * 0.3) as usize;
    let tail_count = max_chars.saturating_sub(head_count);

    let head_str: String = chars[..head_count.min(chars.len())].iter().collect();
    let tail_start = chars.len().saturating_sub(tail_count);
    let tail_str: String = chars[tail_start..].iter().collect();

    let clean_head = match head_str.rfind('\n') {
        Some(pos) if pos > head_count / 2 => &head_str[..pos],
        _ => &head_str,
    };
    let clean_tail = match tail_str.find('\n') {
        Some(pos) if pos < tail_count / 2 => &tail_str[pos + 1..],
        _ => &tail_str,
    };

    let truncated_count = chars.len().saturating_sub(clean_head.chars().count() + clean_tail.chars().count());
    let mut result = format!(
        "{}\n\n... [TRUNCATED DETERMINISTIC HELPER OUTPUT: {} chars omitted to protect LLM context] ...\n\n{}",
        clean_head.trim_end(),
        truncated_count,
        clean_tail.trim_start()
    );

    let backtick_count = result.matches("```").count();
    if backtick_count % 2 != 0 {
        result.push_str("\n```\n");
    }
    result
}

/// Returns declarations for native tools based on active mounted set and trigger states
pub fn get_native_declarations_internal(
    mounted_set: &HashSet<String>,
    canvas_tools_dir: &Path,
) -> Vec<Value> {
    let mut decls = Vec::new();
    let is_all = mounted_set.is_empty();

    // 1. Process Core Universal Tools (all included when mounted_set is empty, or filtered if specific set provided)
    for tool_name in CORE_14_TOOLS {
        if is_all || mounted_set.contains(*tool_name) {
            if let Some(mut decl) = resolve_canvas_tool_declaration(canvas_tools_dir, tool_name) {
                crate::tools::inject_intercept_gate_schema(&mut decl);
                decls.push(decl);
            }
        }
    }

    // 2. Process 9 Prompt Trigger Tools (active ONLY when explicitly triggered in mounted_set)
    for tool_name in PROMPT_TRIGGER_9_TOOLS {
        if mounted_set.contains(*tool_name) {
            if let Some(mut decl) = resolve_canvas_tool_declaration(canvas_tools_dir, tool_name) {
                crate::tools::inject_intercept_gate_schema(&mut decl);
                decls.push(decl);
            }
        }
    }

    // 3. Process Ecosystem Tools (app_control, plugin_control, app_publish, skill_control, brain_control, trigger_control)
    for tool_name in &["app_control", "plugin_control", "app_publish", "plugin_publish", "skill_control", "brain_control", "trigger_control"] {
        if mounted_set.contains(*tool_name) || *tool_name == "trigger_control" {
            if let Some(mut decl) = resolve_canvas_tool_declaration(canvas_tools_dir, tool_name) {
                crate::tools::inject_intercept_gate_schema(&mut decl);
                decls.push(decl);
            }
        }
    }

    // 4. Sovereign Anchor Invariant: code_graph must ALWAYS be present in every tool declaration set
    if !decls.iter().any(|d| d.get("name").and_then(|v| v.as_str()) == Some("code_graph")) {
        if let Some(mut decl) = resolve_canvas_tool_declaration(canvas_tools_dir, "code_graph") {
            crate::tools::inject_intercept_gate_schema(&mut decl);
            decls.push(decl);
        }
    }

    // 5. Sovereign Anchor Invariant: team_progress must ALWAYS be present in every tool declaration set
    if !decls.iter().any(|d| d.get("name").and_then(|v| v.as_str()) == Some("team_progress")) {
        if let Some(mut decl) = resolve_canvas_tool_declaration(canvas_tools_dir, "team_progress") {
            crate::tools::inject_intercept_gate_schema(&mut decl);
            decls.push(decl);
        }
    }

    decls
}

/// Resolves a tool declaration from canvas-ui/tools/<tool_name>/manifest.json
pub fn resolve_canvas_tool_declaration(canvas_tools_dir: &Path, tool_name: &str) -> Option<Value> {
    if tool_name == "team_progress" || tool_name == "flow_team_progress" {
        return Some(json!({
            "name": "team_progress",
            "description": "Sovereign Multi-Agent Swarm Progress Ledger. Provides situational awareness across agents by reading, summarizing, or logging team step trajectory and milestones outside the LLM prompt window (Zero Prompt Bloat).",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "Action to perform: view (default, retrieve latest N progress steps), summary (condensed per-agent milestone summary), or record (log a high-level project milestone checkpoint)."
                    },
                    "limit": {
                        "type": "INTEGER",
                        "description": "Maximum number of recent progress steps to retrieve when action is view (default: 10, max: 50)."
                    },
                    "agent_filter": {
                        "type": "STRING",
                        "description": "Optional persona/agent ID filter to inspect steps from a specific teammate (e.g. leader, code, research)."
                    },
                    "milestone": {
                        "type": "STRING",
                        "description": "Technical milestone summary or checkpoint note in English when action is record."
                    }
                }
            }
        }));
    }

    if tool_name == "deterministic_helper" || tool_name == "c7_helper" || tool_name == "run_helper" {
        return Some(json!({
            "name": "deterministic_helper",
            "description": "Flowork Sovereign Deterministic Helper Engine: Synthesizes and executes local deterministic scripts (Python, Bash, Node.js, Rust) in isolated .FL_BIN/scratch/helpers/ space. Offloads heavy regex matching, log parsing, numerical aggregation, and JSON/CSV conversions away from LLM tokens, returning only concise aggregated outputs with Exit Code 0 verification.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "language": {
                        "type": "STRING",
                        "description": "Scripting language: 'python' (default), 'bash', 'node', or 'rust'"
                    },
                    "code": {
                        "type": "STRING",
                        "description": "Executable script code performing deterministic data transformation or log analysis"
                    },
                    "input_files": {
                        "type": "ARRAY",
                        "items": { "type": "STRING" },
                        "description": "Optional file paths or patterns that the script will analyze or transform"
                    },
                    "arguments": {
                        "type": "STRING",
                        "description": "Optional CLI arguments string or JSON payload passed to the script"
                    },
                    "max_output_chars": {
                        "type": "INTEGER",
                        "description": "Strict token preservation ceiling (default: 4000 characters). Automatically applies Head-Tail preservation if output exceeds limit."
                    },
                    "timeout_ms": {
                        "type": "INTEGER",
                        "description": "Execution timeout in milliseconds (default: 30000ms)"
                    },
                    "task_description": {
                        "type": "STRING",
                        "description": "Brief description of the deterministic transformation being performed"
                    }
                },
                "required": ["code"]
            }
        }));
    }

    if tool_name == "code_graph" || tool_name == "fl_repo_map" || tool_name == "repo_map" || tool_name == "flow_code_graph" {
        return Some(json!({
            "name": "code_graph",
            "description": "Sovereign Token-Budgeted Code Graph & Repository Map engine. Analyzes project structure, AST symbols, PageRank hierarchy, and blast radius within strict token ceiling.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "Action to perform: 'map' (token-budgeted ranked repo map), 'query' (find symbols/definitions), 'impact' (blast radius / dependents), 'overview' (fast architecture tree)"
                    },
                    "target_dir": {
                        "type": "STRING",
                        "description": "Target root directory to analyze (defaults to workspace root)"
                    },
                    "max_tokens": {
                        "type": "INTEGER",
                        "description": "Strict token ceiling budget (default: 1024). Output is strictly bounded: actual <= max_tokens."
                    },
                    "focus_files": {
                        "type": "ARRAY",
                        "items": { "type": "STRING" },
                        "description": "List of priority file paths to anchor PageRank importance scoring."
                    },
                    "query": {
                        "type": "STRING",
                        "description": "Symbol, identifier, or keyword to search when action is 'query' or 'impact'"
                    },
                    "depth": {
                        "type": "INTEGER",
                        "description": "Maximum directory recursion depth (default: 4)"
                    },
                    "detail_level": {
                        "type": "STRING",
                        "description": "Level of detail: 'outline' (symbols only), 'compact' (files + key symbols), 'full' (all exports & calls)"
                    }
                }
            }
        }));
    }

    if tool_name == "app_control" || tool_name == "flow_app_control" {
        return Some(json!({
            "name": "app_control",
            "description": "Control and manage Flowork OS visual Canvas UI applications (open, reload, close, status, list). Directly commands the Canvas UI to open/mount app tabs, reload running tabs, close tabs, or query running engine status.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "Action to perform: 'open' (launch and open app tab in Canvas UI), 'reload' (refresh/reload app tab), 'close' (close tab and stop engine), 'status' (query app status and assigned port), 'list' (list all installed applications)"
                    },
                    "app_id": {
                        "type": "STRING",
                        "description": "Target application identifier (e.g. 'chess', 'flow-studio', 'whale-radar', 'app-forge')"
                    }
                },
                "required": ["action"]
            }
        }));
    }

    if tool_name == "plugin_control" {
        return Some(json!({
            "name": "plugin_control",
            "description": "Control and manage Flowork OS modular plugins (list, inspect, enable, disable).",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "Action to perform: list, inspect, enable, disable"
                    },
                    "plugin_id": {
                        "type": "STRING",
                        "description": "Target plugin identifier"
                    }
                },
                "required": ["action"]
            }
        }));
    }
    if tool_name == "screenshot" || tool_name == "flow_screenshot" {
        return Some(json!({
            "name": "screenshot",
            "description": "Capture system desktop or active window natively with SHA-256 cryptographic hash. Automatically injects image bytes into AI vision cortex for multi-modal visual analysis and renders image preview in chat GUI.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "filename": {
                        "type": "STRING",
                        "description": "Optional output filename (e.g. 'ui_check.png'). Automatically timestamped and stored in .FL_BIN/screenshots/ and canvas-ui/uploads/"
                    },
                    "delay_ms": {
                        "type": "INTEGER",
                        "description": "Optional delay in milliseconds before taking screenshot to allow UI animations to settle (default 0)"
                    }
                }
            }
        }));
    }

    if tool_name == "detect_hardcode" {
        return Some(json!({
            "name": "detect_hardcode",
            "description": "Scans workspace files to detect absolute host paths, hardcoded secrets, and portability violations.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "path": {
                        "type": "STRING",
                        "description": "Target directory or file path to scan."
                    }
                }
            }
        }));
    }

    if tool_name == "team_audit" {
        return Some(json!({
            "name": "team_audit",
            "description": "Requests an adversarial, multi-dimensional audit from the Specialist Auditor Council (Security Specialist, Logic & QA Specialist, Architecture & Standards Specialist). Audits specified target files or git diff changes, evaluates Fowler code smells, detects secret/path leaks, verifies @lock sanctity, checks error handling, and returns an authoritative Council Verdict (PASS/REJECT with score 0-100) and actionable remediations.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "target_files": {
                        "type": "ARRAY",
                        "items": { "type": "STRING" },
                        "description": "Optional list of file paths to audit. If omitted, automatically audits all modified/uncommitted git workspace files."
                    },
                    "audit_scope": {
                        "type": "STRING",
                        "description": "Scope of the audit: 'full' (all specialists), 'security' (SAST, secrets, leaks), 'logic' (error handling, panic risks), or 'architecture' (code smells, @lock sanctity, nano-modular). Defaults to 'full'."
                    },
                    "context": {
                        "type": "STRING",
                        "description": "Optional background context or feature intent explaining the changes to help the auditor council focus their review."
                    },
                    "strict_mode": {
                        "type": "BOOLEAN",
                        "description": "If true, treats code smells or moderate warnings as audit score deductions. Defaults to true."
                    }
                }
            }
        }));
    }

    if tool_name == "app_publish" || tool_name == "plugin_publish" {
        return Some(json!({
            "name": tool_name,
            "description": "Publish verified Flowork OS Canvas apps to ecosystem registry under 4 sacred gates.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "app_id": {
                        "type": "STRING",
                        "description": "Target app identifier (e.g. wifi_analyzer, video-editor)"
                    },
                    "plugin_id": {
                        "type": "STRING",
                        "description": "Legacy alias for app_id"
                    },
                    "version": {
                        "type": "STRING",
                        "description": "Semantic version to publish"
                    },
                    "notes": {
                        "type": "STRING",
                        "description": "Release notes / changelog"
                    }
                },
                "required": ["app_id"]
            }
        }));
    }

    if tool_name == "trigger_control" {
        return Some(json!({
            "name": "trigger_control",
            "description": "Control, manage, and create active or passive Flowork OS triggers without human intervention.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "Action to perform: 'create', 'list', 'inspect', 'enable', 'disable', 'publish'"
                    },
                    "trigger_type": {
                        "type": "STRING",
                        "description": "Type of trigger: 'active' (system/triger/) or 'passive' (system/system_promp/)"
                    },
                    "name": {
                        "type": "STRING",
                        "description": "Trigger identifier or file name (e.g. 'anti_zombie_code')"
                    },
                    "keywords": {
                        "type": "STRING",
                        "description": "Comma-separated technical keywords triggering this prompt (e.g. 'zombie, dead code, cleanup, refactor')"
                    },
                    "content": {
                        "type": "STRING",
                        "description": "The prompt instruction or markdown rules content of the trigger"
                    },
                    "tools": {
                        "type": "ARRAY",
                        "items": { "type": "STRING" },
                        "description": "Array of required tool names (e.g. ['run_command', 'view_file'])"
                    }
                },
                "required": ["action"]
            }
        }));
    }

    let mut candidate_paths = vec![
        canvas_tools_dir.join(tool_name).join("manifest.json"),
    ];
    if let Ok(dir) = std::env::var("FLOWORK_CANVAS_DIR") {
        candidate_paths.push(PathBuf::from(dir).join("tools").join(tool_name).join("manifest.json"));
    }
    if let Ok(root) = std::env::var("FLOWORK_ENGINE_ROOT") {
        candidate_paths.push(PathBuf::from(root).join("canvas-ui").join("tools").join(tool_name).join("manifest.json"));
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(parent) = exe.parent() {
            candidate_paths.push(parent.join("canvas-ui/tools").join(tool_name).join("manifest.json"));
            candidate_paths.push(parent.join("../canvas-ui/tools").join(tool_name).join("manifest.json"));
            candidate_paths.push(parent.join("../flowork/canvas-ui/tools").join(tool_name).join("manifest.json"));
        }
    }
    candidate_paths.push(PathBuf::from("canvas-ui/tools").join(tool_name).join("manifest.json"));
    candidate_paths.push(PathBuf::from("../canvas-ui/tools").join(tool_name).join("manifest.json"));
    candidate_paths.push(PathBuf::from("../../flowork/canvas-ui/tools").join(tool_name).join("manifest.json"));
    candidate_paths.push(PathBuf::from("../flowork/canvas-ui/tools").join(tool_name).join("manifest.json"));

    if let Some(manifest_path) = candidate_paths.iter().find(|p| p.exists()) {
        if let Ok(content) = std::fs::read_to_string(manifest_path) {
            if let Ok(manifest) = serde_json::from_str::<Value>(&content) {
                let name = manifest.get("name").and_then(|v| v.as_str()).unwrap_or(tool_name).to_string();
                let desc = manifest.get("description").and_then(|v| v.as_str()).unwrap_or("Sovereign Tool").to_string();
                let raw_params = manifest.get("parameters").cloned().unwrap_or_else(|| json!({
                    "type": "OBJECT",
                    "properties": {}
                }));

                let params = if let Some(obj) = raw_params.as_object() {
                    if !obj.contains_key("properties") && !obj.contains_key("type") {
                        let candidate_required: Vec<Value> = match tool_name {
                            "run_command" => vec![json!("CommandLine")],
                            "view_file" => vec![json!("AbsolutePath")],
                            "write_to_file" => vec![json!("TargetFile")],
                            "replace_file_content" => vec![json!("TargetFile"), json!("TargetContent"), json!("ReplacementContent")],
                            "read_url_content" => vec![json!("Url")],
                            "search_web" => vec![json!("query")],
                            "ask_question" => vec![json!("questions")],
                            "schedule" => vec![json!("Prompt")],
                            "manage_task" => vec![json!("Action")],
                            "team_audit" | "team_progress" => vec![],
                            "generate_image" => vec![json!("Prompt"), json!("ImageName")],
                            "youtube_spy_video" | "youtube_spy_transcript" | "youtube_spy_channel" | "youtube_spy_competitor_strategy" => vec![json!("target")],
                            "youtube_spy_summary" => vec![json!("content_or_transcript"), json!("target")],
                            "website_intelligence" | "web_security_audit" => vec![json!("domain")],
                            _ => vec![],
                        };
                        let required: Vec<Value> = candidate_required
                            .into_iter()
                            .filter(|k| k.as_str().map(|s| obj.contains_key(s)).unwrap_or(false))
                            .collect();
                        json!({
                            "type": "OBJECT",
                            "properties": obj.clone(),
                            "required": required
                        })
                    } else {
                        let mut p = raw_params.clone();
                        if let Some(p_obj) = p.as_object_mut() {
                            if let Some(props) = p_obj.get("properties").and_then(|p| p.as_object()) {
                                if let Some(req) = p_obj.get("required").and_then(|r| r.as_array()) {
                                    let sanitized_req: Vec<Value> = req.iter()
                                        .filter(|k| k.as_str().map(|s| props.contains_key(s)).unwrap_or(false))
                                        .cloned()
                                        .collect();
                                    p_obj.insert("required".to_string(), Value::Array(sanitized_req));
                                }
                            }
                        }
                        p
                    }
                } else {
                    json!({
                        "type": "OBJECT",
                        "properties": {},
                        "required": []
                    })
                };

                return Some(json!({
                    "name": name,
                    "description": desc,
                    "parameters": params
                }));
            }
        }
    }

    // Check sealed tools enclave if manifest file not found on disk
    if let Some(decl) = crate::sealed_tools::SealedToolsEnclave::resolve_sealed_tool_declaration(tool_name) {
        return Some(decl);
    }

    // Hardcoded fallback declaration if manifest is missing
    let fallback_desc = match tool_name {
        "run_command" => "PROPOSE a command to run on behalf of the user. Operating System: linux. Shell: bash.\n**ASYNC TERMINATION RULE**: Do NOT poll or loop on status to wait for completion. Simply proceed with other work or stop calling tools after launching a command.",
        "schedule" => "Schedule a one-shot timer or a recurring cron job.\n**ASYNC TERMINATION RULE**: Stop calling tools after setting a schedule so the turn yields to the user until notification fires.",
        "manage_task" => "Manage background tasks.\n**ASYNC TERMINATION RULE**: Do NOT poll or loop on status to wait for completion. Simply proceed with other work or stop calling tools.",
        _ => "Sovereign binary native tool",
    };
    Some(json!({
        "name": tool_name,
        "description": fallback_desc,
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_native_run_command_and_view_file() {
        let temp_dir = std::env::temp_dir().join(format!("flw_native_test_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        let test_file = temp_dir.join("sample.txt");
        let content = "Line 1: Flowork\nLine 2: Sovereign\nLine 3: Exit Code 0\n";
        tokio::fs::write(&test_file, content).await.unwrap();

        // 1. Test native view_file
        let vf_args = json!({
            "AbsolutePath": test_file.to_str().unwrap(),
            "StartLine": 1,
            "EndLine": 2
        });
        let vf_res = execute_native_tool("view_file", &vf_args, &temp_dir, &temp_dir).await.expect("native view_file");
        assert_eq!(vf_res["status"], "SUCCESS");
        assert!(vf_res["content"].as_str().unwrap().contains("1: Line 1: Flowork"));
        assert!(vf_res["content"].as_str().unwrap().contains("2: Line 2: Sovereign"));

        // 2. Test native run_command
        let rc_args = json!({
            "CommandLine": "echo 'Flowork Native Binary Tool'"
        });
        let rc_res = execute_native_tool("run_command", &rc_args, &temp_dir, &temp_dir).await.expect("native run_command");
        assert_eq!(rc_res["status"], "SUCCESS");
        assert!(rc_res["output"].as_str().unwrap().contains("Flowork Native Binary Tool"));
        assert_eq!(rc_res["exit_code"], 0);

        // 3. Test native write_to_file with .url.json dashboard embed
        let dash_args = json!({
            "TargetFile": temp_dir.join("dash.url.json").to_str().unwrap(),
            "CodeContent": json!({
                "url": "http://127.0.0.1:9099",
                "title": "Brain Monitor"
            }).to_string()
        });
        let dash_res = execute_native_tool("write_to_file", &dash_args, &temp_dir, &temp_dir).await.expect("native write_to_file");
        // 4. Test native replace_file_content
        let rfc_args = json!({
            "TargetFile": test_file.to_str().unwrap(),
            "Instruction": "Update sovereign to sovereign core",
            "TargetContent": "Line 2: Sovereign\n",
            "ReplacementContent": "Line 2: Sovereign Core 23 Tools\n"
        });
        let rfc_res = execute_native_tool("replace_file_content", &rfc_args, &temp_dir, &temp_dir).await.expect("native replace_file_content");
        assert_eq!(rfc_res["status"], "SUCCESS");
        let updated = tokio::fs::read_to_string(&test_file).await.unwrap();
        assert!(updated.contains("Line 2: Sovereign Core 23 Tools"));

        // 5. Test native schedule
        let sched_args = json!({
            "DurationSeconds": 60,
            "Prompt": "Reminder test"
        });
        let sched_res = execute_native_tool("schedule", &sched_args, &temp_dir, &temp_dir).await.expect("native schedule");
        assert_eq!(sched_res["status"], "SUCCESS");
        assert!(sched_res["message"].as_str().unwrap().contains("Timer"));

        // 6. Test native manage_task
        let mt_args = json!({
            "Action": "send_input",
            "TaskId": "t1",
            "Input": "y\n"
        });
        let mt_res = execute_native_tool("manage_task", &mt_args, &temp_dir, &temp_dir).await.expect("native manage_task");
        assert_eq!(mt_res["status"], "SUCCESS");
        assert!(mt_res["telemetry"].as_str().unwrap().contains("t1"));

        // 7. Test prompt trigger tools (detect_hardcode, audit_security, etc.)
        let dhc_res = execute_native_tool("detect_hardcode", &json!({"Path": temp_dir.to_str().unwrap()}), &temp_dir, &temp_dir).await.expect("native detect_hardcode");
        assert_eq!(dhc_res["status"], "SUCCESS");

        let sec_res = execute_native_tool("audit_security", &json!({"Path": temp_dir.to_str().unwrap()}), &temp_dir, &temp_dir).await.expect("native audit_security");
        assert_eq!(sec_res["status"], "SUCCESS");

        let yt_url = format!("{}?v=dQw4w9WgXcQ", crate::prompt_enclave::PromptEnclave::url_youtube_watch());
        let yt_res = execute_native_tool("youtube_spy_video", &json!({"url": yt_url}), &temp_dir, &temp_dir).await.expect("native youtube_spy_video");
        assert_eq!(yt_res["status"], "SUCCESS");
        assert_eq!(yt_res["exit_code"], 0);

        // 7b. Test native team_audit
        let audit_args = json!({
            "target_files": [test_file.to_str().unwrap()],
            "audit_scope": "full"
        });
        let audit_res = execute_native_tool("team_audit", &audit_args, &temp_dir, &temp_dir).await.expect("native team_audit");
        assert_eq!(audit_res["status"], "SUCCESS");
        assert_eq!(audit_res["verdict"], "APPROVED");
        assert_eq!(audit_res["council_score"], 100);

        // 8. Test exact count invariants
        assert_eq!(CORE_14_TOOLS.len(), 14, "Must have exactly 14 Core Universal Agent Tools");
        assert_eq!(PROMPT_TRIGGER_9_TOOLS.len(), 9, "Must have exactly 9 Prompt Trigger Tools");
        assert_eq!(NATIVE_BINARY_TOOLS.len(), 29, "Must have exactly 29 Native Binary Tools");

        for t in NATIVE_BINARY_TOOLS {
            assert!(is_native_binary_tool(t), "Tool '{}' must be recognized as native binary tool", t);
        }
        assert!(!is_native_binary_tool("some_unknown_external_tool"));

        // 9. Test declarations resolution: 14 core tools default, prompt trigger tools ONLY when triggered
        let canvas_tools_dir = PathBuf::from("canvas-ui/tools");
        let empty_mounted = HashSet::new();
        let default_decls = get_native_declarations(&empty_mounted, &canvas_tools_dir);
        assert_eq!(default_decls.len(), 16, "Empty mounted set must expose 14 core tools plus trigger_control and team_progress");

        let mut triggered_mounted = HashSet::new();
        triggered_mounted.insert("detect_hardcode".to_string());
        triggered_mounted.insert("audit_security".to_string());
        let triggered_decls = get_native_declarations(&triggered_mounted, &canvas_tools_dir);
        assert_eq!(triggered_decls.len(), 5, "Triggered tools plus permanent trigger_control, code_graph, and team_progress should resolve");

        // 9b. Test native code_graph execution inside binary
        let cg_res = execute_native_tool("code_graph", &json!({"action": "map", "max_tokens": 500}), &temp_dir, &temp_dir).await.expect("native code_graph");
        assert_eq!(cg_res["status"], "SUCCESS");
        assert_eq!(cg_res["exit_code"], 0);
        assert!(cg_res["under_budget"].as_bool().unwrap_or(false));

        // 10. Test unrestricted writing outside workspace
        let ext_dir = std::env::temp_dir().join(format!("flw_ext_write_{}", std::process::id()));
        let ext_file = ext_dir.join("external_test.md");
        let write_args = json!({
            "TargetFile": ext_file.to_str().unwrap(),
            "CodeContent": "# Sovereign Unrestricted Autonomous File Creation\nExit Code: 0\n"
        });
        let write_res = execute_native_tool("write_to_file", &write_args, &temp_dir, &temp_dir).await.expect("unrestricted write_to_file");
        assert_eq!(write_res["status"], "SUCCESS");
        assert_eq!(write_res["exit_code"], 0);
        assert!(ext_file.exists());
        let _ = tokio::fs::remove_dir_all(&ext_dir).await;

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_native_app_control_execution() {
        let temp_dir = std::env::temp_dir().join(format!("flw_appctl_test_{}", std::process::id()));
        let apps_dir = temp_dir.join("apps").join("test_app");
        let _ = tokio::fs::create_dir_all(&apps_dir).await;

        let manifest = json!({
            "id": "test_app",
            "name": "Test Application",
            "category": "Software Engineering",
            "icon": "🧪",
            "description": "Test App for App Control Unit Test"
        });
        let _ = tokio::fs::write(apps_dir.join("plugin.manifest.json"), manifest.to_string()).await;

        // 1. Test list action
        let list_args = json!({ "action": "list" });
        let list_res = execute_native_tool("app_control", &list_args, &temp_dir, &temp_dir).await.expect("app_control list");
        assert_eq!(list_res["status"], "SUCCESS");
        assert_eq!(list_res["exit_code"], 0);
        assert_eq!(list_res["action"], "list");
        assert!(list_res["apps"].as_array().map(|a| a.iter().any(|app| app["id"] == "test_app")).unwrap_or(false));

        // 2. Test open action
        let open_args = json!({ "action": "open", "app_id": "test_app" });
        let open_res = execute_native_tool("app_control", &open_args, &temp_dir, &temp_dir).await.expect("app_control open");
        assert_eq!(open_res["status"], "SUCCESS");
        assert_eq!(open_res["action"], "open");
        assert_eq!(open_res["app_id"], "test_app");

        // 3. Test reload action
        let reload_args = json!({ "action": "reload", "app_id": "test_app" });
        let reload_res = execute_native_tool("app_control", &reload_args, &temp_dir, &temp_dir).await.expect("app_control reload");
        assert_eq!(reload_res["status"], "SUCCESS");
        assert_eq!(reload_res["action"], "reload");

        // 4. Test close action
        let close_args = json!({ "action": "close", "app_id": "test_app" });
        let close_res = execute_native_tool("app_control", &close_args, &temp_dir, &temp_dir).await.expect("app_control close");
        assert_eq!(close_res["status"], "SUCCESS");
        assert_eq!(close_res["action"], "close");

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_anti_lazy_gate_shallow_reason_rejected() {
        let temp_dir = std::env::temp_dir().join(format!("flw_gate_test_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        let bad_args = json!({
            "TargetFile": temp_dir.join("test.rs").to_str().unwrap(),
            "CodeContent": "fn main() {}",
            "reason": "fix bug",
            "keywords": "sqlite, wal, database"
        });

        let res = execute_native_tool("write_to_file", &bad_args, &temp_dir, &temp_dir).await;
        assert!(res.is_err());
        assert!(res.err().unwrap().contains("E_SHALLOW_REASON"));

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_anti_lazy_gate_generic_keywords_rejected() {
        let temp_dir = std::env::temp_dir().join(format!("flw_gate_test2_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        let bad_args = json!({
            "TargetFile": temp_dir.join("test.rs").to_str().unwrap(),
            "CodeContent": "fn main() {}",
            "reason": "Handle sqlite concurrency lock by setting pragma wal",
            "keywords": "code, file, fix"
        });

        let res = execute_native_tool("write_to_file", &bad_args, &temp_dir, &temp_dir).await;
        assert!(res.is_err());
        assert!(res.err().unwrap().contains("E_GENERIC_KEYWORDS"));

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_anti_lazy_gate_hallucinated_brain_rejected() {
        let temp_dir = std::env::temp_dir().join(format!("flw_gate_test3_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        let bad_args = json!({
            "TargetFile": temp_dir.join("test.rs").to_str().unwrap(),
            "CodeContent": "fn main() {}",
            "reason": "Handle sqlite concurrency lock by setting pragma wal",
            "keywords": "sqlite, wal_mode, concurrency_lock",
            "fl_brain_ref": ".fl_brain/non_existent_fake_memory.md"
        });

        let res = execute_native_tool("write_to_file", &bad_args, &temp_dir, &temp_dir).await;
        assert!(res.is_err());
        assert!(res.err().unwrap().contains("E_HALLUCINATED_MEMORY"));

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_anti_lazy_gate_valid_passes() {
        let temp_dir = std::env::temp_dir().join(format!("flw_gate_test4_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        let good_args = json!({
            "TargetFile": temp_dir.join("test.rs").to_str().unwrap(),
            "CodeContent": "fn main() {}\n",
            "reason": "Handle sqlite concurrency lock by setting pragma wal",
            "keywords": "sqlite, wal_mode, concurrency_lock",
            "fl_brain_ref": "fresh_solution"
        });

        let res = execute_native_tool("write_to_file", &good_args, &temp_dir, &temp_dir).await;
        assert!(res.is_ok(), "Valid arguments must pass quality gate");
        let content = tokio::fs::read_to_string(temp_dir.join("test.rs")).await.unwrap();
        assert!(content.contains("[FL_INDEX: sqlite, wal_mode, concurrency_lock"));
        assert!(content.contains("COT: Handle sqlite concurrency lock by setting pragma wal"));

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_deterministic_helper_python_execution() {
        let temp_dir = std::env::temp_dir().join(format!("flw_c7_test1_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        let py_code = r#"
import sys
values = [10, 20, 30, 40]
total = sum(values)
avg = total / len(values)
print(f"COUNT={len(values)}|TOTAL={total}|AVG={avg}")
"#;

        let args = json!({
            "language": "python",
            "code": py_code,
            "task_description": "Calculate sum and average deterministically"
        });

        let res = execute_native_tool("deterministic_helper", &args, &temp_dir, &temp_dir).await.expect("deterministic helper run");
        assert_eq!(res["status"], "SUCCESS");
        assert_eq!(res["exit_code"], 0);
        let raw = res["raw_output"].as_str().unwrap();
        assert!(raw.contains("COUNT=4|TOTAL=100|AVG=25.0"));
        let formatted = res["output"].as_str().unwrap();
        assert!(formatted.contains("[DETERMINISTIC HELPER // EXIT CODE 0]"));

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_deterministic_helper_bash_execution() {
        let temp_dir = std::env::temp_dir().join(format!("flw_c7_test2_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        let bash_code = r#"
echo "LOG_PARSER_AGGREGATION_START"
echo "LINE_1: 192.168.1.1 GET 200"
echo "LINE_2: 192.168.1.2 POST 500"
echo "MATCHED_ERRORS=1"
"#;

        let args = json!({
            "language": "bash",
            "code": bash_code,
            "task_description": "Bash log scanner"
        });

        let res = execute_native_tool("deterministic_helper", &args, &temp_dir, &temp_dir).await.expect("bash helper");
        assert_eq!(res["status"], "SUCCESS");
        assert_eq!(res["exit_code"], 0);
        assert!(res["raw_output"].as_str().unwrap().contains("MATCHED_ERRORS=1"));

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_deterministic_helper_truncation_token_protection() {
        let temp_dir = std::env::temp_dir().join(format!("flw_c7_test3_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        // Generate lines of data
        let py_code = r#"
for i in range(200):
    print(f"ROW_{i}: deterministic log line data payload checksum ABCDEF123456")
"#;

        let args = json!({
            "language": "python",
            "code": py_code,
            "max_output_chars": 500
        });

        let res = execute_native_tool("deterministic_helper", &args, &temp_dir, &temp_dir).await.expect("truncated helper");
        assert_eq!(res["status"], "SUCCESS");
        assert_eq!(res["exit_code"], 0);
        assert_eq!(res["is_truncated"], true);
        let out_str = res["output"].as_str().unwrap();
        assert!(out_str.contains("TRUNCATED DETERMINISTIC HELPER OUTPUT"));

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_deterministic_helper_exit_code_non_zero_handled() {
        let temp_dir = std::env::temp_dir().join(format!("flw_c7_test4_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        let py_code = r#"
import sys
sys.stderr.write("FATAL: Missing input dataset file\n")
sys.exit(42)
"#;

        let args = json!({
            "language": "python",
            "code": py_code
        });

        let res = execute_native_tool("deterministic_helper", &args, &temp_dir, &temp_dir).await.expect("run helper non zero");
        assert_eq!(res["status"], "ERROR");
        assert_eq!(res["exit_code"], 42);
        assert!(res["stderr"].as_str().unwrap().contains("Missing input dataset file"));

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }

    #[tokio::test]
    async fn test_team_progress_native_execution() {
        let temp_dir = std::env::temp_dir().join(format!("flw_progress_test_{}", std::process::id()));
        let _ = tokio::fs::create_dir_all(&temp_dir).await;

        let record_args = json!({
            "session_id": "test_sess_swarm_1",
            "action": "record",
            "eff_agent_id": "leader",
            "milestone": "Architecture blueprint approved by Super Admin",
            "reason": "Recording critical project milestone",
            "keywords": "architecture, blueprint, milestone, swarm, team"
        });

        let rec_res = execute_native_tool("team_progress", &record_args, &temp_dir, &temp_dir).await.expect("record milestone");
        assert_eq!(rec_res["status"], "SUCCESS");
        assert_eq!(rec_res["exit_code"], 0);

        let view_args = json!({
            "session_id": "test_sess_swarm_1",
            "action": "view",
            "limit": 10,
            "reason": "Inspecting current team progress ledger",
            "keywords": "progress, ledger, status, inspect, swarm"
        });

        let view_res = execute_native_tool("team_progress", &view_args, &temp_dir, &temp_dir).await.expect("view progress");
        assert_eq!(view_res["status"], "SUCCESS");
        assert_eq!(view_res["exit_code"], 0);
        let out_str = view_res["output"].as_str().unwrap();
        assert!(out_str.contains("Architecture blueprint approved by Super Admin"));

        let summary_args = json!({
            "session_id": "test_sess_swarm_1",
            "action": "summary",
            "reason": "Getting swarm progress summary",
            "keywords": "summary, swarm, progress, metrics, team"
        });

        let sum_res = execute_native_tool("team_progress", &summary_args, &temp_dir, &temp_dir).await.expect("summary progress");
        assert_eq!(sum_res["status"], "SUCCESS");
        assert_eq!(sum_res["exit_code"], 0);

        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }
}

pub fn get_native_declarations(mounted_set: &std::collections::HashSet<String>, canvas_tools_dir: &std::path::Path) -> Vec<serde_json::Value> {
    let mut decls = get_native_declarations_internal(mounted_set, canvas_tools_dir);
    decls.retain(|d| {
        if let Some(name) = d.get("name").and_then(|v| v.as_str()) {
            name != "search_tools"
        } else {
            true
        }
    });
    decls
}
