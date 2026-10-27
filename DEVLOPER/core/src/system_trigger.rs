//! [FLOWORKOS:SYSTEM_TRIGGER_ENGINE]
//! Dynamic On-Disk System Directives & Multi-Dimensional Trigger Evaluation Engine
//! Evaluates runtime context across 11 internal dimensions from `agents/system/*.md`
//! Zero prompt literals in compiled binary - 100% on-disk dynamic evolution.
//! Co-authored-by: Flowork OS <agent@floworkos.com>

use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};
use serde_json::Value;

/// Target topology scope for system directives
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DirectiveScope {
    DefaultSolo,
    DefaultGroup,
    SpecialistSolo,
    SpecialistGroup,
    UniversalAll,
}

impl DirectiveScope {
    pub fn parse(s: &str) -> Option<Self> {
        match s.trim().to_lowercase().as_str() {
            "default_solo" => Some(Self::DefaultSolo),
            "default_group" => Some(Self::DefaultGroup),
            "specialist_solo" => Some(Self::SpecialistSolo),
            "specialist_group" => Some(Self::SpecialistGroup),
            "universal_all" | "all" => Some(Self::UniversalAll),
            _ => None,
        }
    }

    pub fn matches(&self, is_default_orchestrator: bool, is_group_mode: bool) -> bool {
        match self {
            Self::UniversalAll => true,
            Self::DefaultSolo => is_default_orchestrator && !is_group_mode,
            Self::DefaultGroup => is_default_orchestrator && is_group_mode,
            Self::SpecialistSolo => !is_default_orchestrator && !is_group_mode,
            Self::SpecialistGroup => !is_default_orchestrator && is_group_mode,
        }
    }
}

/// Parsed system trigger directive loaded from `agents/system/<name>.md`
#[derive(Debug, Clone)]
pub struct SystemDirective {
    pub trigger_id: String,
    pub name: String,
    pub scopes: Vec<DirectiveScope>,
    pub events: Vec<String>,
    pub categories: Vec<String>,
    pub conditions: SystemDirectiveConditions,
    pub linked_doctrines: Vec<String>,
    pub body: String,
    pub file_path: PathBuf,
}

/// Internal host & environment conditions supported by UNCE
#[derive(Debug, Clone, Default)]
pub struct SystemDirectiveConditions {
    // Temporal
    pub time_hour: Option<String>,
    pub time_clock: Option<String>,
    pub time_minute: Option<String>,
    pub time_second: Option<String>,
    pub time_timezone: Option<String>,
    pub time_day_of_week: Vec<String>,
    pub time_is_weekend: Option<bool>,
    pub time_day_of_month: Option<String>,
    pub time_month: Option<String>,
    pub time_year: Option<String>,
    pub time_market_session: Vec<String>,

    // Hardware & Compute
    pub hw_cpu_load_percent: Option<String>,
    pub hw_cpu_cores: Option<String>,
    pub hw_cpu_temp_celsius: Option<String>,
    pub hw_ram_free_mb: Option<String>,
    pub hw_ram_used_percent: Option<String>,
    pub hw_ram_total_gb: Option<String>,
    pub hw_has_gpu: Option<bool>,
    pub hw_gpu_count: Option<String>,
    pub hw_gpu_vram_free_mb: Option<String>,
    pub hw_gpu_vram_total_mb: Option<String>,
    pub hw_disk_free_gb: Option<String>,
    pub hw_disk_used_percent: Option<String>,
    pub hw_is_on_battery: Option<bool>,
    pub hw_battery_percent: Option<String>,

    // Environment
    pub env_is_headless: Option<bool>,
    pub env_is_root: Option<bool>,
    pub env_os_type: Vec<String>,
    pub env_has_binaries: Vec<String>,
    pub env_weather_status: Vec<String>,

    // Workspace
    pub ws_has_files: Vec<String>,
    pub ws_total_files: Option<String>,
    pub ws_has_uncommitted_changes: Option<bool>,

    // File Context
    pub file_extension: Vec<String>,
    pub file_size_lines: Option<String>,
    pub file_size_kb: Option<String>,

    // Tool Patterns
    pub tool_consecutive_failed_commands: Option<String>,
    pub tool_failure_rate_percent: Option<String>,
    pub tool_same_tool_loop_count: Option<String>,
    pub tool_last_tool_name: Vec<String>,
    pub tool_last_exit_code: Option<String>,

    // User Intent
    pub user_matches_regex: Option<String>,
    pub user_message_length_words: Option<String>,
    pub user_language: Vec<String>,

    // Local Services
    pub local_process_running: Vec<String>,
    pub local_port_open: Vec<u16>,

    // Session Trajectory
    pub session_turn_count: Option<String>,
    pub session_consecutive_errors: Option<String>,
    pub session_duration_seconds: Option<String>,
    pub session_total_tool_calls: Option<String>,
    pub session_uncommitted_creations: Option<String>,

    // Git
    pub git_is_git_repo: Option<bool>,
    pub git_branch: Vec<String>,

    // External Rust Logic Engine (.rs file)
    pub external_rule_file: Option<PathBuf>,
}

/// Evaluates a numeric expression with UNCE operators: ==, >, <, >=, <=, !=, between [min, max]
pub fn eval_numeric_expr(val: f64, expr: &str) -> bool {
    let s = expr.trim();
    if s.is_empty() {
        return true;
    }
    if s.starts_with("between") {
        if let Some(b_start) = s.find('[') {
            if let Some(b_end) = s.find(']') {
                let inner = &s[b_start + 1..b_end];
                let parts: Vec<&str> = inner.split(',').map(|p| p.trim().trim_matches('\'').trim_matches('"')).collect();
                if parts.len() == 2 {
                    if let (Ok(min_v), Ok(max_v)) = (parts[0].parse::<f64>(), parts[1].parse::<f64>()) {
                        if min_v <= max_v {
                            return val >= min_v && val <= max_v;
                        } else {
                            // Circular / overnight wraparound
                            return val >= min_v || val <= max_v;
                        }
                    }
                }
            }
        }
        return false;
    }
    if let Some(rest) = s.strip_prefix(">=") {
        if let Ok(target) = rest.trim().trim_matches('\'').trim_matches('"').parse::<f64>() {
            return val >= target;
        }
    }
    if let Some(rest) = s.strip_prefix("<=") {
        if let Ok(target) = rest.trim().trim_matches('\'').trim_matches('"').parse::<f64>() {
            return val <= target;
        }
    }
    if let Some(rest) = s.strip_prefix('>') {
        if let Ok(target) = rest.trim().trim_matches('\'').trim_matches('"').parse::<f64>() {
            return val > target;
        }
    }
    if let Some(rest) = s.strip_prefix('<') {
        if let Ok(target) = rest.trim().trim_matches('\'').trim_matches('"').parse::<f64>() {
            return val < target;
        }
    }
    if let Some(rest) = s.strip_prefix("==") {
        if let Ok(target) = rest.trim().trim_matches('\'').trim_matches('"').parse::<f64>() {
            return (val - target).abs() < 1e-6;
        }
    }
    if let Some(rest) = s.strip_prefix("!=") {
        if let Ok(target) = rest.trim().trim_matches('\'').trim_matches('"').parse::<f64>() {
            return (val - target).abs() >= 1e-6;
        }
    }
    if let Ok(target) = s.trim_matches('\'').trim_matches('"').parse::<f64>() {
        return (val - target).abs() < 1e-6;
    }
    false
}

/// Converts a "HH:MM" or "HH:MM:SS" clock string to seconds past midnight (0..86399)
pub fn parse_clock_str_to_seconds(clock_str: &str) -> Option<u32> {
    let parts: Vec<&str> = clock_str.trim().trim_matches('\'').trim_matches('"').split(':').collect();
    if parts.len() >= 2 {
        let h = parts[0].parse::<u32>().ok()?;
        let m = parts[1].parse::<u32>().ok()?;
        let s = if parts.len() >= 3 { parts[2].parse::<u32>().ok().unwrap_or(0) } else { 0 };
        return Some(h * 3600 + m * 60 + s);
    }
    None
}

/// Evaluates a clock expression with UNCE operators
pub fn eval_clock_expr(current_sec: u32, expr: &str) -> bool {
    let s = expr.trim();
    if s.is_empty() {
        return true;
    }
    if s.starts_with("between") {
        if let Some(b_start) = s.find('[') {
            if let Some(b_end) = s.find(']') {
                let inner = &s[b_start + 1..b_end];
                let parts: Vec<&str> = inner.split(',').map(|p| p.trim()).collect();
                if parts.len() == 2 {
                    if let (Some(start_s), Some(end_s)) = (parse_clock_str_to_seconds(parts[0]), parse_clock_str_to_seconds(parts[1])) {
                        if start_s <= end_s {
                            return current_sec >= start_s && current_sec <= end_s;
                        } else {
                            // Overnight wrap
                            return current_sec >= start_s || current_sec <= end_s;
                        }
                    }
                }
            }
        }
        return false;
    }
    if let Some(rest) = s.strip_prefix(">=") {
        if let Some(target) = parse_clock_str_to_seconds(rest) {
            return current_sec >= target;
        }
    }
    if let Some(rest) = s.strip_prefix("<=") {
        if let Some(target) = parse_clock_str_to_seconds(rest) {
            return current_sec <= target;
        }
    }
    if let Some(rest) = s.strip_prefix('>') {
        if let Some(target) = parse_clock_str_to_seconds(rest) {
            return current_sec > target;
        }
    }
    if let Some(rest) = s.strip_prefix('<') {
        if let Some(target) = parse_clock_str_to_seconds(rest) {
            return current_sec < target;
        }
    }
    if let Some(rest) = s.strip_prefix("==") {
        if let Some(target) = parse_clock_str_to_seconds(rest) {
            return current_sec == target;
        }
    }
    if let Some(target) = parse_clock_str_to_seconds(s) {
        return current_sec == target;
    }
    false
}

/// Instant local loopback socket check (127.0.0.1:<port>) with 30ms timeout
pub fn is_local_port_open(port: u16) -> bool {
    use std::net::{SocketAddr, TcpStream};
    use std::time::Duration;
    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    TcpStream::connect_timeout(&addr, Duration::from_millis(30)).is_ok()
}

/// Instant local $PATH binary presence check (0 process spawning)
pub fn is_binary_in_path(bin_name: &str) -> bool {
    let clean = bin_name.trim();
    if clean.is_empty() {
        return false;
    }
    if let Some(paths) = std::env::var_os("PATH") {
        for path in std::env::split_paths(&paths) {
            let full = path.join(clean);
            if full.is_file() {
                return true;
            }
            #[cfg(target_os = "windows")]
            {
                if path.join(format!("{}.exe", clean)).is_file()
                    || path.join(format!("{}.cmd", clean)).is_file()
                    || path.join(format!("{}.bat", clean)).is_file()
                {
                    return true;
                }
            }
        }
    }
    false
}

/// Instant headless check (0 child process spawning)
pub fn is_headless_environment() -> bool {
    #[cfg(target_os = "linux")]
    {
        std::env::var("DISPLAY").is_err() && std::env::var("WAYLAND_DISPLAY").is_err()
    }
    #[cfg(not(target_os = "linux"))]
    {
        false
    }
}

/// Native Host Hardware Sensor: CPU temperature in Celsius
pub fn get_host_cpu_temp_celsius() -> Option<f64> {
    #[cfg(target_os = "linux")]
    {
        for i in 0..5 {
            let path = format!("/sys/class/thermal/thermal_zone{}/temp", i);
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(val) = content.trim().parse::<f64>() {
                    let temp = if val > 1000.0 { val / 1000.0 } else { val };
                    return Some(temp);
                }
            }
        }
    }
    None
}

/// Native Host Hardware Sensor: RAM metrics (free_mb, used_percent, total_gb)
pub fn get_host_ram_metrics() -> Option<(f64, f64, f64)> {
    #[cfg(target_os = "linux")]
    {
        if let Ok(content) = fs::read_to_string("/proc/meminfo") {
            let mut total_kb = 0.0;
            let mut avail_kb = 0.0;
            for line in content.lines() {
                if line.starts_with("MemTotal:") {
                    total_kb = line.split_whitespace().nth(1).and_then(|s| s.parse::<f64>().ok()).unwrap_or(0.0);
                } else if line.starts_with("MemAvailable:") {
                    avail_kb = line.split_whitespace().nth(1).and_then(|s| s.parse::<f64>().ok()).unwrap_or(0.0);
                }
            }
            if total_kb > 0.0 {
                let free_mb = avail_kb / 1024.0;
                let used_percent = ((total_kb - avail_kb) / total_kb) * 100.0;
                let total_gb = total_kb / (1024.0 * 1024.0);
                return Some((free_mb, used_percent, total_gb));
            }
        }
    }
    None
}

/// Native Host Hardware Sensor: CPU load percentage (normalized to core count)
pub fn get_host_cpu_load_percent() -> Option<f64> {
    #[cfg(target_os = "linux")]
    {
        if let Ok(content) = fs::read_to_string("/proc/loadavg") {
            if let Some(first) = content.split_whitespace().next() {
                if let Ok(load1) = first.parse::<f64>() {
                    let cores = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1) as f64;
                    let load_percent = (load1 / cores) * 100.0;
                    return Some(load_percent);
                }
            }
        }
    }
    None
}

/// Native Host Environment Sensor: Ambient weather status (from cache or environment variable)
pub fn get_host_weather_status(effective_ws: &Path) -> Option<String> {
    if let Ok(val) = std::env::var("FLOWORK_WEATHER_STATUS") {
        let clean = val.trim().to_lowercase();
        if !clean.is_empty() {
            return Some(clean);
        }
    }
    let candidates = [
        effective_ws.join("system").join("system_promp").join("weather.json"),
        effective_ws.join("system").join("system_promp").join("weather.txt"),
        PathBuf::from("/tmp/flowork_weather.json"),
        PathBuf::from("/tmp/flowork_weather.txt"),
    ];
    for c in &candidates {
        if c.is_file() {
            if let Ok(content) = fs::read_to_string(c) {
                if c.extension().and_then(|s| s.to_str()) == Some("json") {
                    if let Ok(val) = serde_json::from_str::<Value>(&content) {
                        if let Some(status) = val.get("status").or_else(|| val.get("weather")).and_then(|v| v.as_str()) {
                            return Some(status.trim().to_lowercase());
                        }
                    }
                } else {
                    let clean = content.trim().to_lowercase();
                    if !clean.is_empty() {
                        return Some(clean);
                    }
                }
            }
        }
    }
    None
}

/// Parses a JSON trigger entry (from `system/system_promp/triggers.json` or `prompts_trigger_registry.json`) into a `SystemDirective`
pub fn parse_system_directive_json(val: &Value, base_dir: &Path) -> Option<SystemDirective> {
    let trigger_id = val.get("id")
        .or_else(|| val.get("trigger_id"))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim()
        .to_string();
    if trigger_id.is_empty() {
        return None;
    }
    if val.get("enabled").and_then(|v| v.as_bool()) == Some(false) {
        return None;
    }
    let mut name = val.get("name")
        .or_else(|| val.get("title"))
        .and_then(|v| v.as_str())
        .unwrap_or(&trigger_id)
        .to_string();
    if name.is_empty() {
        name = trigger_id.clone();
    }

    let mut scopes = Vec::new();
    if let Some(scope_val) = val.get("scopes").or_else(|| val.get("scope")) {
        if let Some(arr) = scope_val.as_array() {
            for s in arr {
                if let Some(st) = s.as_str().and_then(DirectiveScope::parse) {
                    scopes.push(st);
                }
            }
        } else if let Some(st) = scope_val.as_str().and_then(DirectiveScope::parse) {
            scopes.push(st);
        }
    }
    if scopes.is_empty() {
        scopes.push(DirectiveScope::UniversalAll);
    }

    let mut events = Vec::new();
    if let Some(ev_val) = val.get("events").or_else(|| val.get("event")) {
        if let Some(arr) = ev_val.as_array() {
            for e in arr {
                if let Some(s) = e.as_str() {
                    events.push(s.to_lowercase());
                }
            }
        } else if let Some(s) = ev_val.as_str() {
            events.push(s.to_lowercase());
        }
    }

    let mut categories = Vec::new();
    if let Some(cat_val) = val.get("categories").or_else(|| val.get("category")) {
        if let Some(arr) = cat_val.as_array() {
            for c in arr {
                if let Some(s) = c.as_str() {
                    categories.push(s.to_uppercase());
                }
            }
        } else if let Some(s) = cat_val.as_str() {
            categories.push(s.to_uppercase());
        }
    }

    let mut conditions = SystemDirectiveConditions::default();
    if let Some(c_obj) = val.get("condition").or_else(|| val.get("conditions")).or_else(|| val.get("internal_conditions")) {
        // Temporal
        if let Some(v) = c_obj.get("time_clock").or_else(|| c_obj.get("clock")).or_else(|| c_obj.get("time")).and_then(|x| x.as_str()) {
            conditions.time_clock = Some(v.to_string());
        }
        if let Some(v) = c_obj.get("time_hour").or_else(|| c_obj.get("hour")) {
            if let Some(s) = v.as_str() {
                conditions.time_hour = Some(s.to_string());
            } else if let Some(n) = v.as_i64() {
                conditions.time_hour = Some(n.to_string());
            }
        }
        if let Some(v) = c_obj.get("time_minute").or_else(|| c_obj.get("minute")) {
            if let Some(s) = v.as_str() {
                conditions.time_minute = Some(s.to_string());
            } else if let Some(n) = v.as_i64() {
                conditions.time_minute = Some(n.to_string());
            }
        }
        if let Some(v) = c_obj.get("time_timezone").or_else(|| c_obj.get("timezone")).and_then(|x| x.as_str()) {
            conditions.time_timezone = Some(v.to_lowercase());
        }
        if let Some(v) = c_obj.get("time_is_weekend").or_else(|| c_obj.get("is_weekend")).and_then(|x| x.as_bool()) {
            conditions.time_is_weekend = Some(v);
        }
        if let Some(v) = c_obj.get("time_day_of_week").or_else(|| c_obj.get("day_of_week")) {
            if let Some(arr) = v.as_array() {
                for d in arr {
                    if let Some(ds) = d.as_str() { conditions.time_day_of_week.push(ds.to_lowercase()); }
                }
            } else if let Some(ds) = v.as_str() {
                conditions.time_day_of_week.push(ds.to_lowercase());
            }
        }

        // Hardware
        if let Some(v) = c_obj.get("hw_cpu_temp_celsius").or_else(|| c_obj.get("cpu_temp_celsius")).or_else(|| c_obj.get("cpu_temp")) {
            if let Some(s) = v.as_str() {
                conditions.hw_cpu_temp_celsius = Some(s.to_string());
            } else if let Some(n) = v.as_f64() {
                conditions.hw_cpu_temp_celsius = Some(format!(">= {}", n));
            }
        }
        if let Some(v) = c_obj.get("hw_cpu_load_percent").or_else(|| c_obj.get("cpu_load_percent")).or_else(|| c_obj.get("cpu_load")) {
            if let Some(s) = v.as_str() {
                conditions.hw_cpu_load_percent = Some(s.to_string());
            } else if let Some(n) = v.as_f64() {
                conditions.hw_cpu_load_percent = Some(format!(">= {}", n));
            }
        }
        if let Some(v) = c_obj.get("hw_ram_free_mb").or_else(|| c_obj.get("ram_free_mb")) {
            if let Some(s) = v.as_str() {
                conditions.hw_ram_free_mb = Some(s.to_string());
            } else if let Some(n) = v.as_f64() {
                conditions.hw_ram_free_mb = Some(format!("<= {}", n));
            }
        }

        // Weather
        if let Some(v) = c_obj.get("env_weather_status").or_else(|| c_obj.get("weather_status")).or_else(|| c_obj.get("weather")) {
            if let Some(arr) = v.as_array() {
                for w in arr {
                    if let Some(ws) = w.as_str() { conditions.env_weather_status.push(ws.to_lowercase()); }
                }
            } else if let Some(ws) = v.as_str() {
                for part in ws.split(',') {
                    let p = part.trim().to_lowercase();
                    if !p.is_empty() { conditions.env_weather_status.push(p); }
                }
            }
        }

        // User intent regex
        if let Some(v) = c_obj.get("user_matches_regex").or_else(|| c_obj.get("matches_regex")).and_then(|x| x.as_str()) {
            conditions.user_matches_regex = Some(v.to_string());
        }
    }

    // External Rust logic engine (.rs rule)
    if let Some(rf) = val.get("rule").or_else(|| val.get("rule_file")).and_then(|x| x.as_str()) {
        conditions.external_rule_file = Some(base_dir.join(rf));
    }

    // Load prompt payload: check prompt_file first, then prompt, then file
    let mut body = String::new();
    let mut resolved_path = base_dir.to_path_buf();
    if let Some(pf) = val.get("prompt_file").or_else(|| val.get("prompt")).or_else(|| val.get("file")).and_then(|x| x.as_str()) {
        let target = base_dir.join(pf);
        if target.is_file() {
            if let Ok(c) = fs::read_to_string(&target) {
                body = c;
                resolved_path = target;
            }
        }
    }
    if body.is_empty() {
        if let Some(b) = val.get("prompt").or_else(|| val.get("content")).or_else(|| val.get("body")).and_then(|x| x.as_str()) {
            body = b.to_string();
        }
    }

    if body.trim().is_empty() {
        return None;
    }

    Some(SystemDirective {
        trigger_id,
        name,
        scopes,
        events,
        categories,
        conditions,
        linked_doctrines: Vec::new(),
        body,
        file_path: resolved_path,
    })
}

/// Parses a YAML frontmatter markdown file into a `SystemDirective`
pub fn parse_system_directive_markdown(content: &str, file_path: &Path) -> Option<SystemDirective> {
    let trimmed = content.trim_start();
    if !trimmed.starts_with("---") {
        return None;
    }
    let after_first = &trimmed[3..];
    let end_idx = after_first.find("---")?;
    let frontmatter_str = &after_first[..end_idx];
    let body = after_first[end_idx + 3..].trim().to_string();

    let mut trigger_id = String::new();
    let mut name = String::new();
    let mut scopes = Vec::new();
    let mut events = Vec::new();
    let mut categories = Vec::new();
    let mut linked_doctrines = Vec::new();
    let mut conditions = SystemDirectiveConditions::default();
    let mut has_evaluator_function = false;

    let mut active_section = String::new();
    let mut active_subsection = String::new();

    for raw_line in frontmatter_str.lines() {
        let line = raw_line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        let indent = raw_line.chars().take_while(|c| *c == ' ').count();

        // Top-level sections or sub-sections
        if line.ends_with(':') && !line.starts_with('-') {
            let key = line.trim_end_matches(':').trim().to_lowercase();
            if indent == 0 {
                active_section = key;
                active_subsection.clear();
            } else if indent >= 2 && indent < 6 {
                active_subsection = key;
            }
            continue;
        }

        // List items
        if line.starts_with("- ") || line == "-" {
            let item = line.trim_start_matches('-').trim().trim_matches('"').trim_matches('\'').to_string();
            if !item.is_empty() {
                if active_section == "scopes" {
                    if let Some(sc) = DirectiveScope::parse(&item) {
                        scopes.push(sc);
                    }
                } else if active_section == "events" {
                    events.push(item.to_lowercase());
                } else if active_section == "categories" {
                    categories.push(item.to_uppercase());
                } else if active_section == "linked_doctrines" || active_section == "linked_topics" || active_section == "related_doctrines" || active_section == "related" {
                    linked_doctrines.push(item);
                } else if active_section == "internal_conditions" || active_section == "conditions" {
                    match active_subsection.as_str() {
                        "process_running" => conditions.local_process_running.push(item.to_lowercase()),
                        "local_port_open" => {
                            if let Ok(p) = item.parse::<u16>() {
                                conditions.local_port_open.push(p);
                            }
                        }
                        "has_binaries" => conditions.env_has_binaries.push(item.to_lowercase()),
                        "has_files" => conditions.ws_has_files.push(item),
                        "extension" => conditions.file_extension.push(item.to_lowercase()),
                        "last_tool_name" => conditions.tool_last_tool_name.push(item.to_lowercase()),
                        "language" => conditions.user_language.push(item.to_lowercase()),
                        "branch" => conditions.git_branch.push(item),
                        "os_type" => conditions.env_os_type.push(item.to_lowercase()),
                        "day_of_week" => conditions.time_day_of_week.push(item.to_lowercase()),
                        "market_session" => conditions.time_market_session.push(item.to_lowercase()),
                        _ => {}
                    }
                }
            }
            continue;
        }

        // Key-Value pairs
        if let Some(colon_pos) = line.find(':') {
            let key = line[..colon_pos].trim().to_lowercase();
            let val = line[colon_pos + 1..].trim().trim_matches('"').trim_matches('\'').to_string();

            // Support inline array format like: has_files: ["Cargo.toml", "package.json"]
            if val.starts_with('[') && val.ends_with(']') {
                let inner = val.trim_start_matches('[').trim_end_matches(']');
                let items: Vec<String> = inner.split(',')
                    .map(|it| it.trim().trim_matches('"').trim_matches('\'').to_string())
                    .filter(|s| !s.is_empty())
                    .collect();

                if key == "scopes" {
                    for it in items {
                        if let Some(sc) = DirectiveScope::parse(&it) {
                            scopes.push(sc);
                        }
                    }
                } else if key == "events" {
                    events.extend(items.into_iter().map(|s| s.to_lowercase()));
                } else if key == "categories" {
                    categories.extend(items.into_iter().map(|s| s.to_uppercase()));
                } else if key == "linked_doctrines" || key == "linked_topics" || key == "related_doctrines" || key == "related" {
                    linked_doctrines.extend(items);
                } else if key == "has_files" {
                    conditions.ws_has_files.extend(items);
                } else if key == "has_binaries" {
                    conditions.env_has_binaries.extend(items.into_iter().map(|s| s.to_lowercase()));
                } else if key == "extension" {
                    conditions.file_extension.extend(items.into_iter().map(|s| s.to_lowercase()));
                } else if key == "day_of_week" {
                    conditions.time_day_of_week.extend(items.into_iter().map(|s| s.to_lowercase()));
                } else if key == "market_session" {
                    conditions.time_market_session.extend(items.into_iter().map(|s| s.to_lowercase()));
                } else if key == "language" {
                    conditions.user_language.extend(items.into_iter().map(|s| s.to_lowercase()));
                } else if key == "branch" {
                    conditions.git_branch.extend(items);
                } else if key == "os_type" {
                    conditions.env_os_type.extend(items.into_iter().map(|s| s.to_lowercase()));
                } else if key == "process_running" {
                    conditions.local_process_running.extend(items.into_iter().map(|s| s.to_lowercase()));
                } else if key == "local_port_open" {
                    conditions.local_port_open.extend(items.into_iter().filter_map(|s| s.parse::<u16>().ok()));
                } else if key == "weather_status" || key == "weather" {
                    conditions.env_weather_status.extend(items.into_iter().map(|s| s.to_lowercase()));
                }
                continue;
            }

            if indent == 0 {
                match key.as_str() {
                    "trigger_id" => trigger_id = val,
                    "name" => name = val,
                    "evaluator_function" => has_evaluator_function = true,
                    "linked_doctrines" | "linked_topics" | "related_doctrines" | "related" => linked_doctrines.push(val),
                    _ => {}
                }
            } else if active_section == "internal_conditions" || active_section == "conditions" {
                match key.as_str() {
                    // Temporal
                    "hour" => conditions.time_hour = Some(val),
                    "clock" | "time" => conditions.time_clock = Some(val),
                    "minute" => conditions.time_minute = Some(val),
                    "second" => conditions.time_second = Some(val),
                    "timezone" => conditions.time_timezone = Some(val.to_lowercase()),
                    "is_weekend" => conditions.time_is_weekend = val.parse::<bool>().ok(),
                    "day_of_month" => conditions.time_day_of_month = Some(val),
                    "month" => conditions.time_month = Some(val),
                    "year" => conditions.time_year = Some(val),

                    // Hardware
                    "cpu_load_percent" => conditions.hw_cpu_load_percent = Some(val),
                    "cpu_cores" => conditions.hw_cpu_cores = Some(val),
                    "cpu_temp_celsius" => conditions.hw_cpu_temp_celsius = Some(val),
                    "ram_free_mb" => conditions.hw_ram_free_mb = Some(val),
                    "ram_used_percent" => conditions.hw_ram_used_percent = Some(val),
                    "ram_total_gb" => conditions.hw_ram_total_gb = Some(val),
                    "has_gpu" => conditions.hw_has_gpu = val.parse::<bool>().ok(),
                    "gpu_count" => conditions.hw_gpu_count = Some(val),
                    "gpu_vram_free_mb" => conditions.hw_gpu_vram_free_mb = Some(val),
                    "gpu_vram_total_mb" => conditions.hw_gpu_vram_total_mb = Some(val),
                    "disk_free_gb" => conditions.hw_disk_free_gb = Some(val),
                    "disk_used_percent" => conditions.hw_disk_used_percent = Some(val),
                    "is_on_battery" => conditions.hw_is_on_battery = val.parse::<bool>().ok(),
                    "battery_percent" => conditions.hw_battery_percent = Some(val),

                    // Environment
                    "is_headless" => conditions.env_is_headless = val.parse::<bool>().ok(),
                    "is_root" => conditions.env_is_root = val.parse::<bool>().ok(),
                    "weather_status" | "weather" => {
                        for part in val.split(',') {
                            let p = part.trim().to_lowercase();
                            if !p.is_empty() {
                                conditions.env_weather_status.push(p);
                            }
                        }
                    }

                    // Workspace
                    "total_files" => conditions.ws_total_files = Some(val),
                    "has_uncommitted_changes" => conditions.ws_has_uncommitted_changes = val.parse::<bool>().ok(),

                    // File Context
                    "file_size_lines" => conditions.file_size_lines = Some(val),
                    "file_size_kb" => conditions.file_size_kb = Some(val),

                    // Tool Patterns
                    "consecutive_failed_commands" => conditions.tool_consecutive_failed_commands = Some(val),
                    "failure_rate_percent" => conditions.tool_failure_rate_percent = Some(val),
                    "same_tool_loop_count" => conditions.tool_same_tool_loop_count = Some(val),
                    "last_exit_code" => conditions.tool_last_exit_code = Some(val),

                    // User Intent
                    "matches_regex" => conditions.user_matches_regex = Some(val),
                    "message_length_words" => conditions.user_message_length_words = Some(val),

                    // Session Trajectory
                    "turn_count" => conditions.session_turn_count = Some(val),
                    "consecutive_errors" => conditions.session_consecutive_errors = Some(val),
                    "duration_seconds" => conditions.session_duration_seconds = Some(val),
                    "total_tool_calls" => conditions.session_total_tool_calls = Some(val),
                    "uncommitted_creations" => conditions.session_uncommitted_creations = Some(val),

                    // Git
                    "is_git_repo" => conditions.git_is_git_repo = val.parse::<bool>().ok(),

                    _ => {}
                }
            }
        }
    }

    if trigger_id.is_empty() || has_evaluator_function {
        return None;
    }

    if name.is_empty() {
        name = trigger_id.clone();
    }

    if scopes.is_empty() {
        scopes.push(DirectiveScope::UniversalAll);
    }

    Some(SystemDirective {
        trigger_id,
        name,
        scopes,
        events,
        categories,
        conditions,
        linked_doctrines,
        body,
        file_path: file_path.to_path_buf(),
    })
}

/// Compiles and evaluates an external Rust rule file with caching in `rules/.bin/<id>`.
/// Returns true if the compiled binary terminates with Exit Code 0.
pub fn evaluate_external_rust_rule(rule_file: &Path, trigger_id: &str) -> bool {
    if !rule_file.is_file() {
        return false;
    }

    let bin_dir = rule_file.parent().map(|p| p.join(".bin")).unwrap_or_else(|| PathBuf::from(".bin"));
    let _ = fs::create_dir_all(&bin_dir);
    let bin_file = bin_dir.join(trigger_id);

    let mut needs_compile = !bin_file.is_file();
    if !needs_compile {
        if let (Ok(src_meta), Ok(bin_meta)) = (fs::metadata(rule_file), fs::metadata(&bin_file)) {
            if let (Ok(src_mtime), Ok(bin_mtime)) = (src_meta.modified(), bin_meta.modified()) {
                if src_mtime > bin_mtime {
                    needs_compile = true;
                }
            }
        }
    }

    if needs_compile {
        let cargo_rustc = std::env::var("HOME").map(|h| std::path::PathBuf::from(h).join(".cargo").join("bin").join("rustc")).ok();
        let rustc_bin = if let Some(ref cr) = cargo_rustc {
            if cr.is_file() { cr.to_str().unwrap_or("rustc") } else if cfg!(target_os = "windows") { "rustc.exe" } else { "rustc" }
        } else if cfg!(target_os = "windows") { "rustc.exe" } else { "rustc" };

        let mut child = match std::process::Command::new(rustc_bin)
            .args(["-O", rule_file.to_str().unwrap_or(""), "-o", bin_file.to_str().unwrap_or("")])
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .spawn() {
                Ok(c) => c,
                Err(_) => return false,
            };

        // Compilation Circuit Breaker: 5000ms maximum
        let start = std::time::Instant::now();
        let mut compile_ok = false;
        loop {
            match child.try_wait() {
                Ok(Some(status)) => {
                    compile_ok = status.success();
                    break;
                }
                Ok(None) => {
                    if start.elapsed() > std::time::Duration::from_millis(5000) {
                        let _ = child.kill();
                        let _ = child.wait();
                        eprintln!("[SystemTrigger] ⚠️ Compilation timed out (5s circuit breaker) for rule: {:?}", rule_file);
                        return false;
                    }
                    std::thread::sleep(std::time::Duration::from_millis(25));
                }
                Err(_) => return false,
            }
        }
        if !compile_ok {
            return false;
        }
    }

    // Direct instantaneous execution with Circuit Breaker (500ms max timeout)
    let mut child = match std::process::Command::new(&bin_file)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn() {
            Ok(c) => c,
            Err(_) => return false,
        };

    let start = std::time::Instant::now();
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                return status.success();
            }
            Ok(None) => {
                if start.elapsed() > std::time::Duration::from_millis(500) {
                    let _ = child.kill();
                    let _ = child.wait();
                    eprintln!("[SystemTrigger] ⚠️ Execution timed out (500ms circuit breaker) for rule: {:?}", rule_file);
                    return false;
                }
                std::thread::sleep(std::time::Duration::from_millis(10));
            }
            Err(_) => return false,
        }
    }
}

/// Evaluates a single system directive against runtime context
pub fn evaluate_directive(
    directive: &SystemDirective,
    is_default_orchestrator: bool,
    is_group_mode: bool,
    eff_category: &str,
    user_msg: Option<&str>,
    mounted_tools: Option<&HashSet<String>>,
    effective_ws: &Path,
    active_events: &[&str],
) -> bool {
    // 1. Scopes Check: At least one scope must match
    if !directive.scopes.iter().any(|s| s.matches(is_default_orchestrator, is_group_mode)) {
        return false;
    }

    // 2. Events Check: If directive declares events, at least one must match active_events
    if !directive.events.is_empty() && !directive.events.iter().any(|e| e == "always_active") {
        let has_matching_event = directive.events.iter().any(|e| active_events.contains(&e.as_str()));
        if !has_matching_event {
            return false;
        }
    }

    // 3. Categories Check: If directive declares categories, must include "ALL" or eff_category
    // DOKTRIN KEDAULATAN: Mr. Flow (Solo Default) memiliki hak akses universal di mode solo.
    // Spesialis hanya menerima jika kategorinya cocok (misal CAT-005 Teknologi). Leader (Group Default) tetap digate via Scopes.
    if !directive.categories.is_empty() {
        let is_solo_default = is_default_orchestrator && !is_group_mode;
        let cat_clean = eff_category.trim().to_uppercase();
        let matches_cat = is_solo_default || directive.categories.iter().any(|c| c == "ALL" || c == &cat_clean);
        if !matches_cat {
            return false;
        }
    }

    // 4. External Rust Rule Engine (.rs file)
    if let Some(ref rule_file) = directive.conditions.external_rule_file {
        if !evaluate_external_rust_rule(rule_file, &directive.trigger_id) {
            return false;
        }
    }

    let cond = &directive.conditions;

    // 4. Temporal Evaluation (UTC default or Local)
    let (cur_hour, cur_clock_sec, cur_minute, cur_second, cur_day_of_week, cur_is_weekend, cur_day_of_month, cur_month, cur_year) = {
        let now = std::time::SystemTime::now();
        let dur = now.duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
        let is_local = cond.time_timezone.as_deref() == Some("local");
        #[cfg(unix)]
        let use_libc_local = is_local;
        #[cfg(not(unix))]
        let use_libc_local = false;

        if use_libc_local {
            #[cfg(unix)]
            {
                let epoch_secs = dur.as_secs() as i64;
                let mut tm: libc::tm = unsafe { std::mem::zeroed() };
                let t = epoch_secs as libc::time_t;
                unsafe { libc::localtime_r(&t, &mut tm); }
                let hour = tm.tm_hour as u32;
                let minute = tm.tm_min as u32;
                let second = tm.tm_sec as u32;
                let day_of_week = tm.tm_wday as u32;
                let is_weekend = day_of_week == 0 || day_of_week == 6;
                let d = tm.tm_mday as u32;
                let m = (tm.tm_mon + 1) as u32;
                let year = (tm.tm_year + 1900) as i64;
                let time_in_day = hour * 3600 + minute * 60 + second;
                (hour, time_in_day, minute, second, day_of_week, is_weekend, d, m, year)
            }
            #[cfg(not(unix))]
            {
                unreachable!()
            }
        } else {
            let offset_secs = if is_local { 7 * 3600 } else { 0 };
            let epoch_s = dur.as_secs() + offset_secs;
            let days = epoch_s / 86400;
            let time_in_day = epoch_s % 86400;
            let hour = (time_in_day / 3600) as u32;
            let minute = ((time_in_day % 3600) / 60) as u32;
            let second = (time_in_day % 60) as u32;
            let day_of_week = ((days + 4) % 7) as u32; // 0=Sunday, 1=Monday... 6=Saturday
            let is_weekend = day_of_week == 0 || day_of_week == 6;

            // Gregorian calculation
            let z = (days as i64) + 719468;
            let era = if z >= 0 { z } else { z - 146096 } / 146097;
            let doe = (z - era * 146097) as u64;
            let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
            let y = (yoe as i64) + era * 400;
            let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
            let mp = (5 * doy + 2) / 153;
            let d = doy - (153 * mp + 2) / 5 + 1;
            let m = if mp < 10 { mp + 3 } else { mp - 9 };
            let year = if m <= 2 { y + 1 } else { y };

            (hour, time_in_day as u32, minute, second, day_of_week, is_weekend, d as u32, m as u32, year)
        }
    };

    if let Some(ref h_expr) = cond.time_hour {
        if !eval_numeric_expr(cur_hour as f64, h_expr) {
            return false;
        }
    }
    if let Some(ref clk_expr) = cond.time_clock {
        if !eval_clock_expr(cur_clock_sec, clk_expr) {
            return false;
        }
    }
    if let Some(ref m_expr) = cond.time_minute {
        if !eval_numeric_expr(cur_minute as f64, m_expr) {
            return false;
        }
    }
    if let Some(ref s_expr) = cond.time_second {
        if !eval_numeric_expr(cur_second as f64, s_expr) {
            return false;
        }
    }
    if let Some(w_target) = cond.time_is_weekend {
        if cur_is_weekend != w_target {
            return false;
        }
    }
    if let Some(ref dom_expr) = cond.time_day_of_month {
        if !eval_numeric_expr(cur_day_of_month as f64, dom_expr) {
            return false;
        }
    }
    if let Some(ref mon_expr) = cond.time_month {
        if !eval_numeric_expr(cur_month as f64, mon_expr) {
            return false;
        }
    }
    if let Some(ref yr_expr) = cond.time_year {
        if !eval_numeric_expr(cur_year as f64, yr_expr) {
            return false;
        }
    }

    if !cond.time_day_of_week.is_empty() {
        let day_str = match cur_day_of_week {
            0 => "sunday",
            1 => "monday",
            2 => "tuesday",
            3 => "wednesday",
            4 => "thursday",
            5 => "friday",
            _ => "saturday",
        };
        let matches_dow = cond.time_day_of_week.iter().any(|d| {
            let dl = d.to_lowercase();
            dl == day_str || (dl == "weekday" && !cur_is_weekend) || (dl == "weekend" && cur_is_weekend)
        });
        if !matches_dow {
            return false;
        }
    }

    // Market session bounds (UTC based)
    if !cond.time_market_session.is_empty() {
        let utc_hour = cur_hour;
        let in_session = cond.time_market_session.iter().any(|sess| match sess.to_lowercase().as_str() {
            "london" => utc_hour >= 8 && utc_hour < 16,
            "new_york" => utc_hour >= 13 && utc_hour < 21,
            "tokyo" => utc_hour < 8,
            "sydney" => utc_hour >= 22 || utc_hour < 6,
            "overlap_london_ny" => utc_hour >= 13 && utc_hour < 16,
            _ => false,
        });
        if !in_session {
            return false;
        }
    }

    // Browser activity verification
    if directive.events.contains(&"using_browser".to_string()) && active_events.contains(&"using_browser") {
        if let Some(mt) = mounted_tools {
            let has_browser_tool = mt.contains("browser")
                || mt.contains("browser_action")
                || mt.contains("read_browser_page")
                || mt.contains("search_web")
                || mt.contains("read_url_content");
            let has_domain = user_msg.map(|m| m.contains(".com") || m.contains("http")).unwrap_or(false);
            if !has_browser_tool && !has_domain {
                return false;
            }
        }
    }

    // 4.5 Hardware & Thermal Sensors (UNCE evaluated)
    if let Some(ref cpu_load_expr) = cond.hw_cpu_load_percent {
        if let Some(load) = get_host_cpu_load_percent() {
            if !eval_numeric_expr(load, cpu_load_expr) {
                return false;
            }
        }
    }
    if let Some(ref cpu_temp_expr) = cond.hw_cpu_temp_celsius {
        if let Some(temp) = get_host_cpu_temp_celsius() {
            if !eval_numeric_expr(temp, cpu_temp_expr) {
                return false;
            }
        }
    }
    if let Some(ref ram_free_expr) = cond.hw_ram_free_mb {
        if let Some((free_mb, _, _)) = get_host_ram_metrics() {
            if !eval_numeric_expr(free_mb, ram_free_expr) {
                return false;
            }
        }
    }
    if let Some(ref ram_used_expr) = cond.hw_ram_used_percent {
        if let Some((_, used_pct, _)) = get_host_ram_metrics() {
            if !eval_numeric_expr(used_pct, ram_used_expr) {
                return false;
            }
        }
    }
    if let Some(ref cores_expr) = cond.hw_cpu_cores {
        let cores = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1) as f64;
        if !eval_numeric_expr(cores, cores_expr) {
            return false;
        }
    }

    // 5. Environment Sensors
    if let Some(target_headless) = cond.env_is_headless {
        if is_headless_environment() != target_headless {
            return false;
        }
    }
    if let Some(target_root) = cond.env_is_root {
        #[cfg(unix)]
        let is_root = unsafe { libc::geteuid() == 0 };
        #[cfg(not(unix))]
        let is_root = false;
        if is_root != target_root {
            return false;
        }
    }
    if !cond.env_has_binaries.is_empty() {
        for b in &cond.env_has_binaries {
            if !is_binary_in_path(b) {
                return false;
            }
        }
    }
    if !cond.env_weather_status.is_empty() {
        if let Some(cur_weather) = get_host_weather_status(effective_ws) {
            let matches = cond.env_weather_status.iter().any(|w| cur_weather.contains(&w.to_lowercase()));
            if !matches {
                return false;
            }
        } else {
            return false;
        }
    }

    // 6. Workspace Probes
    if !cond.ws_has_files.is_empty() {
        for f in &cond.ws_has_files {
            if !effective_ws.join(f).exists() {
                return false;
            }
        }
    }

    // 7. Local Services & Ports
    if !cond.local_port_open.is_empty() {
        for port in &cond.local_port_open {
            if !is_local_port_open(*port) {
                return false;
            }
        }
    }

    // 8. User Intent Pattern Regex
    if let Some(ref regex_str) = cond.user_matches_regex {
        if let Some(msg) = user_msg {
            let lower = msg.to_lowercase();
            // Simple keyword/regex check without external heavy engine
            let pattern_clean = regex_str.trim_start_matches("(?i)").trim_matches('(').trim_matches(')');
            let any_match = pattern_clean.split('|').any(|pat| {
                let p = pat.trim().to_lowercase();
                !p.is_empty() && lower.contains(&p)
            });
            if !any_match {
                return false;
            }
        } else {
            return false;
        }
    }

    // 9. Git Repository Check
    if let Some(require_git) = cond.git_is_git_repo {
        let has_git = effective_ws.join(".git").exists();
        if has_git != require_git {
            return false;
        }
    }

    true
}

/// Scans candidate directories for system directives (`agents/system/*.md`), excluding `readme.md`
pub fn scan_and_evaluate_system_directives(
    engine_root: &Path,
    effective_ws: &Path,
    is_default_orchestrator: bool,
    is_group_mode: bool,
    eff_category: &str,
    user_msg: Option<&str>,
    mounted_tools: Option<&HashSet<String>>,
    active_events: &[&str],
) -> Vec<SystemDirective> {
    let mut candidate_dirs = vec![
        engine_root.join("system").join("system_promp"),
        engine_root.join("system").join("system_promp").join("promp"),
        engine_root.join("system").join("system_promp").join("rules"),
        effective_ws.join("system").join("system_promp"),
        effective_ws.join("system").join("system_promp").join("promp"),
        effective_ws.join("system").join("system_promp").join("rules"),
        engine_root.join("flowork").join("system").join("system_promp"),
        engine_root.join("flowork").join("system").join("system_promp").join("promp"),
        engine_root.join("flowork").join("system").join("system_promp").join("rules"),
        effective_ws.join("flowork").join("system").join("system_promp"),
        effective_ws.join("flowork").join("system").join("system_promp").join("promp"),
        effective_ws.join("flowork").join("system").join("system_promp").join("rules"),
        engine_root.join("flowork").join("agents").join("system"),
        engine_root.join("agents").join("system"),
        effective_ws.join("agents").join("system"),
        effective_ws.join("flowork").join("agents").join("system"),
    ];

    if let Ok(p_root) = std::env::var("FLOWORK_PORTABLE_ROOT") {
        candidate_dirs.push(PathBuf::from(&p_root).join("system").join("system_promp"));
        candidate_dirs.push(PathBuf::from(&p_root).join("agents").join("system"));
    }

    let mut matched = Vec::new();
    let mut seen_ids = HashSet::new();

    for dir in candidate_dirs {
        if !dir.is_dir() {
            continue;
        }

        // 1. Scan external passive triggers registry (triggers.json or prompts_trigger_registry.json)
        let triggers_json = dir.join("triggers.json");
        let reg_file = if triggers_json.is_file() {
            Some(triggers_json)
        } else {
            let alt = dir.join("prompts_trigger_registry.json");
            if alt.is_file() { Some(alt) } else { None }
        };

        if let Some(rf) = reg_file {
            if let Ok(c) = fs::read_to_string(&rf) {
                if let Ok(val) = serde_json::from_str::<Value>(&c) {
                    let list = val.as_array()
                        .or_else(|| val.get("prompts").and_then(|p| p.as_array()))
                        .or_else(|| val.get("triggers").and_then(|p| p.as_array()));
                    if let Some(triggers) = list {
                        for t in triggers {
                            if let Some(directive) = parse_system_directive_json(t, &dir) {
                                if !seen_ids.contains(&directive.trigger_id) {
                                    if evaluate_directive(
                                        &directive,
                                        is_default_orchestrator,
                                        is_group_mode,
                                        eff_category,
                                        user_msg,
                                        mounted_tools,
                                        effective_ws,
                                        active_events,
                                    ) {
                                        seen_ids.insert(directive.trigger_id.clone());
                                        matched.push(directive);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // 2. Scan individual on-disk markdown directives
        if let Ok(entries) = fs::read_dir(&dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_file() {
                    let fname = path.file_name().and_then(|s| s.to_str()).unwrap_or("");
                    let fname_lower = fname.to_lowercase();
                    if fname_lower.contains("readme")
                        || fname_lower.contains("trigger")
                        || fname_lower.contains("triger")
                        || fname_lower.contains("event")
                        || fname_lower.starts_with('.')
                        || fname_lower.starts_with("protocol")
                        || fname_lower.starts_with("radar")
                        || fname_lower.starts_with("constitution")
                        || fname_lower.starts_with("guardrail")
                        || fname_lower.starts_with("promp_")
                    {
                        continue;
                    }
                    if path.extension().map(|e| e == "md").unwrap_or(false) {
                        if let Ok(content) = fs::read_to_string(&path) {
                            if let Some(directive) = parse_system_directive_markdown(&content, &path) {
                                if !seen_ids.contains(&directive.trigger_id) {
                                    if evaluate_directive(
                                        &directive,
                                        is_default_orchestrator,
                                        is_group_mode,
                                        eff_category,
                                        user_msg,
                                        mounted_tools,
                                        effective_ws,
                                        active_events,
                                    ) {
                                        seen_ids.insert(directive.trigger_id.clone());
                                        matched.push(directive);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Also scan sensory triggers in system/triger/*/trigger.md
    let mut ext_candidate_roots = vec![
        engine_root.join("flowork").join("system").join("triger"),
        engine_root.join("system").join("triger"),
        effective_ws.join("system").join("triger"),
        effective_ws.join("flowork").join("system").join("triger"),
        engine_root.join("flowork").join("external_triger"),
        engine_root.join("external_triger"),
        effective_ws.join("external_triger"),
        effective_ws.join("flowork").join("external_triger"),
    ];
    if let Ok(p_root) = std::env::var("FLOWORK_PORTABLE_ROOT") {
        ext_candidate_roots.push(PathBuf::from(&p_root).join("system").join("triger"));
        ext_candidate_roots.push(PathBuf::from(p_root).join("external_triger"));
    }

    for ext_root in ext_candidate_roots {
        let ext_matches = scan_and_evaluate_organ_triggers(
            &ext_root,
            effective_ws,
            is_default_orchestrator,
            is_group_mode,
            eff_category,
            user_msg,
            mounted_tools,
            active_events,
        );
        for directive in ext_matches {
            if !seen_ids.contains(&directive.trigger_id) {
                seen_ids.insert(directive.trigger_id.clone());
                matched.push(directive);
            }
        }
    }

    matched
}

/// Composes the matched directives into a unified prompt injection block with Lex Superior preamble
pub fn compose_system_directives_injection(directives: &[SystemDirective]) -> String {
    if directives.is_empty() {
        return String::new();
    }

    let mut out = String::new();
    for dir in directives {
        out.push_str(&format!(
            "================================================================================\n\
             🌿 [PASSIVE SENSORY TRIGGER ACTIVATED: {}]\n\
             • Trigger ID : {}\n\
             • Evaluator  : JIT Native Sensor Rule (system/system_promp/)\n\
             • Nature     : Ambient Environmental Instinct (Quiescent JIT Evaluated)\n\
             • Notice     : Conditionally activated by host/workspace telemetry. NOT a user request.\n\
             ================================================================================\n\n",
            dir.name, dir.trigger_id
        ));
        out.push_str(&dir.body);
        if !dir.linked_doctrines.is_empty() {
            out.push_str("\n\n## Linked Engineering Doctrines (Wikipedia Breadcrumbs)\n");
            for doc in &dir.linked_doctrines {
                match doc.as_str() {
                    "01_diagnosing_hard_bugs" => {
                        out.push_str("- **[[01] Diagnosing Hard Bugs & Performance Regressions]**: Root cause elimination before code edits.\n  *Trigger keywords*: diagnose, bug, crash\n");
                    }
                    "deep_modules_architecture" => {
                        out.push_str("- **[[02] Deep Modules & Seam Architecture]**: Hide complexity behind simple APIs.\n");
                    }
                    other => {
                        out.push_str(&format!("- **[{}]**: Associated engineering doctrine.\n", other));
                    }
                }
            }
        }
        out.push_str("\n\n");
    }
    out
}

/// Scans and evaluates trigger specifications for a specific organ (`skills/`, `agents/`, `tools/`, `plugins/`).
/// Discovers triggers from both subdirectories (`<organ_root>/*/trigger.md`) and dedicated files.
pub fn scan_and_evaluate_organ_triggers(
    organ_root: &Path,
    effective_ws: &Path,
    is_default_orchestrator: bool,
    is_group_mode: bool,
    eff_category: &str,
    user_msg: Option<&str>,
    mounted_tools: Option<&HashSet<String>>,
    active_events: &[&str],
) -> Vec<SystemDirective> {
    if !organ_root.is_dir() {
        return Vec::new();
    }

    let mut matched = Vec::new();
    let mut seen_ids = HashSet::new();

    if let Ok(entries) = fs::read_dir(organ_root) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                let trigger_file = path.join("trigger.md");
                if trigger_file.is_file() {
                    if let Ok(content) = fs::read_to_string(&trigger_file) {
                        if let Some(directive) = parse_system_directive_markdown(&content, &trigger_file) {
                            if !seen_ids.contains(&directive.trigger_id) {
                                if evaluate_directive(
                                    &directive,
                                    is_default_orchestrator,
                                    is_group_mode,
                                    eff_category,
                                    user_msg,
                                    mounted_tools,
                                    effective_ws,
                                    active_events,
                                ) {
                                    seen_ids.insert(directive.trigger_id.clone());
                                    matched.push(directive);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    matched
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_unce_numeric_operators() {
        // Equal
        assert!(eval_numeric_expr(14.0, "== 14"));
        assert!(eval_numeric_expr(14.0, "14"));
        assert!(!eval_numeric_expr(15.0, "== 14"));

        // Greater / Greater equal
        assert!(eval_numeric_expr(85.0, "> 80"));
        assert!(!eval_numeric_expr(80.0, "> 80"));
        assert!(eval_numeric_expr(80.0, ">= 80"));

        // Less / Less equal
        assert!(eval_numeric_expr(15.0, "< 20"));
        assert!(eval_numeric_expr(20.0, "<= 20"));
        assert!(!eval_numeric_expr(21.0, "<= 20"));

        // Between normal
        assert!(eval_numeric_expr(85.0, "between [75, 95]"));
        assert!(eval_numeric_expr(75.0, "between [75, 95]"));
        assert!(eval_numeric_expr(95.0, "between [75, 95]"));
        assert!(!eval_numeric_expr(74.9, "between [75, 95]"));
        assert!(!eval_numeric_expr(95.1, "between [75, 95]"));

        // Between overnight/circular wrap (e.g. 22..4)
        assert!(eval_numeric_expr(23.0, "between [22, 4]"));
        assert!(eval_numeric_expr(2.0, "between [22, 4]"));
        assert!(!eval_numeric_expr(12.0, "between [22, 4]"));
    }

    #[test]
    fn test_clock_evaluation() {
        let sec_14_30 = 14 * 3600 + 30 * 60;
        assert!(eval_clock_expr(sec_14_30, "== '14:30'"));
        assert!(eval_clock_expr(sec_14_30, "> '08:00'"));
        assert!(eval_clock_expr(sec_14_30, "< '17:00'"));
        assert!(eval_clock_expr(sec_14_30, "between ['08:30', '16:30']"));

        let sec_23_15 = 23 * 3600 + 15 * 60;
        assert!(eval_clock_expr(sec_23_15, "between ['22:00', '04:00']"));
    }

    #[test]
    fn test_parse_system_directive_markdown() {
        let raw = r#"---
trigger_id: "SYS-TEST-001"
name: "Test Directive"
scopes:
  - "default_solo"
  - "specialist_group"
categories:
  - "CAT-005"
internal_conditions:
  time:
    hour: "between [8, 16]"
  workspace:
    has_files: ["Cargo.toml"]
---
<TEST_POLICY>
Hello Sovereign World!
</TEST_POLICY>
"#;
        let dummy_path = PathBuf::from("test.md");
        let parsed = parse_system_directive_markdown(raw, &dummy_path).expect("Must parse");
        assert_eq!(parsed.trigger_id, "SYS-TEST-001");
        assert_eq!(parsed.name, "Test Directive");
        assert_eq!(parsed.scopes.len(), 2);
        assert_eq!(parsed.categories, vec!["CAT-005"]);
        assert_eq!(parsed.conditions.time_hour.as_deref(), Some("between [8, 16]"));
        assert_eq!(parsed.conditions.ws_has_files, vec!["Cargo.toml"]);
        assert!(parsed.body.contains("Hello Sovereign World!"));
    }

    #[test]
    fn test_directive_scope_matching() {
        assert!(DirectiveScope::DefaultSolo.matches(true, false));
        assert!(!DirectiveScope::DefaultSolo.matches(true, true));
        assert!(!DirectiveScope::DefaultSolo.matches(false, false));

        assert!(DirectiveScope::DefaultGroup.matches(true, true));
        assert!(!DirectiveScope::DefaultGroup.matches(true, false));

        assert!(DirectiveScope::SpecialistSolo.matches(false, false));
        assert!(!DirectiveScope::SpecialistSolo.matches(false, true));

        assert!(DirectiveScope::SpecialistGroup.matches(false, true));
        assert!(!DirectiveScope::SpecialistGroup.matches(false, false));

        assert!(DirectiveScope::UniversalAll.matches(true, false));
        assert!(DirectiveScope::UniversalAll.matches(true, true));
        assert!(DirectiveScope::UniversalAll.matches(false, false));
        assert!(DirectiveScope::UniversalAll.matches(false, true));
    }

    #[test]
    fn test_scan_and_evaluate_live_on_disk_directives() {
        let nanos = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
        let temp_dir = std::env::temp_dir().join(format!("flw_sys_trig_test_{}", nanos));
        let sys_dir = temp_dir.join("agents").join("system");
        let _ = fs::create_dir_all(&sys_dir);

        let sample_directive = r#"---
trigger_id: "SYS-TRIG-HERMETIC-POLICY"
name: "Hermetic Policy Directive"
scopes:
  - "universal_all"
events:
  - "always_active"
categories:
  - "all"
internal_conditions:
  user_intent:
    matches_regex: "(?i)(audit|inspect|verify)"
  workspace:
    has_files: ["Cargo.toml"]
---
<TEST_POLICY>
Hermetic multi-dimensional test directive body.
</TEST_POLICY>
"#;
        let _ = fs::write(sys_dir.join("hermetic_policy.md"), sample_directive);
        let _ = fs::write(sys_dir.join("readme.md"), "# System Directive Readme");
        let _ = fs::write(temp_dir.join("Cargo.toml"), "[package]\nname = \"hermetic_test\"");

        // Test 1: Hermetic multi-dimensional directive matching (independent of deleted disk files)
        let matched = scan_and_evaluate_system_directives(
            &temp_dir,
            &temp_dir,
            true,  // is_default_orchestrator
            false, // is_group_mode
            "CAT-005",
            Some("please audit and verify workspace health"),
            None,
            &["always_active"],
        );
        let has_policy = matched.iter().any(|d| d.trigger_id == "SYS-TRIG-HERMETIC-POLICY");
        assert!(has_policy, "Hermetic policy directive must match when intent and workspace match");

        // Test 2: Verify readme.md is NEVER loaded as a directive
        let has_readme = matched.iter().any(|d| d.trigger_id.to_lowercase().contains("readme"));
        assert!(!has_readme, "readme.md must NEVER be parsed or loaded as a trigger directive!");

        // Test 3: Verify purged directives (SYS-TRIG-RISK-SAFETY & SYS-TRIG-RUST-WORKSPACE) are absent from disk
        let engine_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().and_then(|p| p.parent()).map(|p| p.to_path_buf()).unwrap_or_else(|| PathBuf::from(env!("CARGO_MANIFEST_DIR")));
        let effective_ws = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        let matched_live = scan_and_evaluate_system_directives(
            &engine_root,
            &effective_ws,
            true,
            false,
            "CAT-005",
            Some("drop table users in rust workspace"),
            None,
            &["always_active"],
        );
        assert!(!matched_live.iter().any(|d| d.trigger_id == "SYS-TRIG-RISK-SAFETY"), "Purged SYS-TRIG-RISK-SAFETY must not exist on disk");
        assert!(!matched_live.iter().any(|d| d.trigger_id == "SYS-TRIG-RUST-WORKSPACE"), "Purged SYS-TRIG-RUST-WORKSPACE must not exist on disk");
        assert!(!matched_live.iter().any(|d| d.trigger_id == "SYS-TRIG-BROWSER-STEALTH"), "Purged SYS-TRIG-BROWSER-STEALTH must not exist on disk");

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_scan_and_evaluate_organ_triggers() {
        let nanos = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
        let organ_dir = std::env::temp_dir().join(format!("flw_organ_trig_test_{}", nanos));
        let tool_dir = organ_dir.join("sys_health");
        let _ = fs::create_dir_all(&tool_dir);

        let ws_dir = std::env::temp_dir().join(format!("flw_ws_trig_test_{}", nanos));
        let _ = fs::create_dir_all(&ws_dir);
        let _ = fs::write(ws_dir.join("test_file.txt"), "hello");

        let sample_trigger = r#"---
trigger_id: "TOOL-SYS-HEALTH-SAMPLE"
name: "System Health Trigger"
scopes:
  - "universal_all"
events:
  - "always_active"
categories:
  - "all"
conditions:
  ws:
    has_files: ["test_file.txt"]
---
# Trigger Action
Recommend sys_health tool when files exist.
"#;
        let _ = fs::write(tool_dir.join("trigger.md"), sample_trigger);

        let matched = scan_and_evaluate_organ_triggers(
            &organ_dir,
            &ws_dir,
            true,
            false,
            "CAT-005",
            None,
            None,
            &["always_active"],
        );

        assert_eq!(matched.len(), 1, "Must match exactly 1 organ trigger");
        assert_eq!(matched[0].trigger_id, "TOOL-SYS-HEALTH-SAMPLE");

        let _ = fs::remove_dir_all(&organ_dir);
        let _ = fs::remove_dir_all(&ws_dir);
    }

    #[test]
    fn test_system_directive_linked_doctrines_injection() {
        let content = r#"---
trigger_id: "SYS-TEST-LINKED"
name: "Test Directive With Linked Doctrines"
scopes:
  - universal_all
linked_doctrines:
  - 01_diagnosing_hard_bugs
  - deep_modules_architecture
---
# Action Body
Monitor system status.
"#;
        let p = PathBuf::from("test.md");
        let dir = parse_system_directive_markdown(content, &p).expect("Should parse directive");
        assert_eq!(dir.linked_doctrines.len(), 2);
        assert_eq!(dir.linked_doctrines[0], "01_diagnosing_hard_bugs");
        assert_eq!(dir.linked_doctrines[1], "deep_modules_architecture");

        let injection = compose_system_directives_injection(&[dir]);
        assert!(injection.contains("Linked Engineering Doctrines (Wikipedia Breadcrumbs)"));
        assert!(injection.contains("[01] Diagnosing Hard Bugs & Performance Regressions"));
        assert!(injection.contains("[02] Deep Modules & Seam Architecture"));
        assert!(injection.contains("diagnose, bug, crash"));
    }

    #[test]
    fn test_passive_triggers_json_and_weather_sensor() {
        let nanos = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
        let temp_dir = std::env::temp_dir().join(format!("flw_passive_trig_{}", nanos));
        let sys_promp_dir = temp_dir.join("system").join("system_promp");
        let promp_dir = sys_promp_dir.join("promp");
        let _ = fs::create_dir_all(&promp_dir);

        let ws_dir = temp_dir.join("ws");
        let _ = fs::create_dir_all(&ws_dir);

        // Write sample promp payloads
        let _ = fs::write(promp_dir.join("sleep.md"), "# Sleep Reminder\nGo to bed now.\n");
        let _ = fs::write(promp_dir.join("weather.md"), "# Weather Lighting\nTurn on workspace lights.\n");

        let triggers_json = r#"[
            {
                "id": "test_sleep",
                "name": "Midnight Sleep",
                "enabled": true,
                "scope": "universal_all",
                "condition": {
                    "time_clock": "between ['00:00', '23:59']"
                },
                "prompt_file": "promp/sleep.md"
            },
            {
                "id": "test_weather",
                "name": "Weather Light",
                "enabled": true,
                "scope": "universal_all",
                "condition": {
                    "weather_status": ["cloudy", "rain"]
                },
                "prompt_file": "promp/weather.md"
            }
        ]"#;
        let _ = fs::write(sys_promp_dir.join("triggers.json"), triggers_json);

        // Test with weather environment variable set
        std::env::set_var("FLOWORK_WEATHER_STATUS", "cloudy");

        let matched = scan_and_evaluate_system_directives(
            &temp_dir,
            &ws_dir,
            true,
            false,
            "ALL",
            None,
            None,
            &[],
        );

        assert!(matched.iter().any(|d| d.trigger_id == "test_sleep"), "Clock trigger must match");
        assert!(matched.iter().any(|d| d.trigger_id == "test_weather"), "Weather trigger must match");

        let injection = compose_system_directives_injection(&matched);
        assert!(injection.contains("Go to bed now."));
        assert!(injection.contains("Turn on workspace lights."));

        std::env::remove_var("FLOWORK_WEATHER_STATUS");
        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_sovereign_symbolic_memory_directive_evaluation() {
        let live_root = PathBuf::from("/home/mrflow/flowork");
        let matched = scan_and_evaluate_system_directives(
            &live_root,
            &live_root,
            true,
            false,
            "ALL",
            None,
            None,
            &[],
        );

        let has_mem_directive = matched.iter().any(|d| d.trigger_id == "SYS-MEM-001");
        assert!(has_mem_directive, "SYS-MEM-001 Sovereign Symbolic Memory directive must be discovered");
        let injection = compose_system_directives_injection(&matched);
        assert!(injection.contains("SOVEREIGN SYMBOLIC MEMORY & CONTEXT OFF-LOAD DIRECTIVE"));
    }
}

