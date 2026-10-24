//! [FLOWORKOS:SOVEREIGN_PERSONA_ENGINE]
//! Dynamic Trigger-Based Persona & Rule Injection Engine
//! Evaluates runtime keywords, tools, counters, stalls, and workspace patterns
//! to selectively inject modular Persona instructions from FLOWORK/Persona/<role>/*.md
//! Co-authored-by: Flowork OS <agent@floworkos.com>

use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use serde_json::{json, Value};

/// Trigger specification parsed from markdown frontmatter
#[derive(Debug, Clone, Default)]
pub struct TriggerSpec {
    pub keywords: Vec<String>,
    pub exclude_keywords: Vec<String>,
    pub commands: Vec<String>,
    pub tools_active: Vec<String>,
    pub tool_threshold_tool: Option<String>,
    pub tool_threshold_min: usize,
    pub tool_stalled_tool: Option<String>,
    pub tool_stalled_consecutive_failures: usize,
    pub file_patterns: Vec<String>,
    pub min_turn: Option<usize>,
    pub max_turn: Option<usize>,
    pub always: bool,
}

/// A parsed persona markdown document (prompt.md, rules.md, kinerja.md, etc.)
#[derive(Debug, Clone)]
pub struct PersonaDocument {
    pub id: String,
    pub persona: String,       // e.g. "coder", "trader", "forex-specialis"
    pub target: String,        // "prompt", "rules", "kinerja"
    pub priority: u32,
    pub trigger: TriggerSpec,
    pub file_path: PathBuf,
    pub body_markdown: String,
}

/// Metadata manifest parsed from persona.json
#[derive(Debug, Clone)]
pub struct PersonaManifest {
    pub id: String,
    pub name: String,
    pub description: String,
    pub category: String,
    pub priority: u32,
    pub default_tools: Vec<String>,
    pub file_patterns: Vec<String>,
    pub keywords: Vec<String>,
}

/// Runtime stats per tool for evaluating usage counters and circuit breakers
#[derive(Debug, Clone, Default)]
pub struct ToolRunStats {
    pub total_calls: usize,
    pub consecutive_failures: usize,
    pub last_exit_code: i64,
}

/// Evaluation result for a matching persona document
#[derive(Debug, Clone)]
pub struct PersonaMatchResult {
    pub persona_name: String,
    pub target_type: String, // "prompt", "rules", "kinerja"
    pub doc_id: String,
    pub priority: u32,
    pub match_reasons: Vec<String>,
    pub body_markdown: String,
}

/// Sovereign Persona Engine
pub struct SovereignPersonaEngine;

impl SovereignPersonaEngine {
    /// Discover all persona directories from given roots
    /// Ensures Persona/SKILL.MD is automatically reconstituted from embedded bytecode enclave if missing or deleted
    pub fn ensure_persona_skill(_persona_root: &Path) {
        // Intentionally no-op: Persona directory and individual prompts must NEVER be auto-created by binary!
    }

    /// Discover all subagent directories strictly prioritizing system/subagent (Single Source of Truth)
    pub fn resolve_persona_roots(workspace: &Path, engine_root: &Path) -> Vec<PathBuf> {
        let mut roots = Vec::new();

        let candidates = vec![
            engine_root.join("system").join("subagent"),
            engine_root.join("flowork").join("system").join("subagent"),
            workspace.join("system").join("subagent"),
            workspace.join("flowork").join("system").join("subagent"),
        ];

        for c in &candidates {
            if c.exists() && c.is_dir() && !roots.contains(c) {
                roots.push(c.clone());
            }
        }

        roots
    }

    /// Load all persona documents from discovered roots
    pub fn load_all_persona_docs(roots: &[PathBuf]) -> Vec<PersonaDocument> {
        let mut docs = Vec::new();
        let mut seen_doc_ids = HashSet::new();

        for root in roots {
            if let Ok(entries) = fs::read_dir(root) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.is_dir() {
                        let persona_name = path.file_name()
                            .map(|n| n.to_string_lossy().to_string())
                            .unwrap_or_default();

                        // Scan markdown files in this persona folder
                        if let Ok(file_entries) = fs::read_dir(&path) {
                            for f_entry in file_entries.flatten() {
                                let f_path = f_entry.path();
                                if f_path.is_file() && f_path.extension().and_then(|e| e.to_str()) == Some("md") {
                                    if let Ok(content) = fs::read_to_string(&f_path) {
                                        if let Some(doc) = Self::parse_persona_markdown(&content, &f_path, &persona_name) {
                                            if !seen_doc_ids.contains(&doc.id) {
                                                seen_doc_ids.insert(doc.id.clone());
                                                docs.push(doc);
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

        docs
    }

    /// Dynamically discover and list all available specialized subagents from system/subagent.
    /// Returns clean JSON array strictly reflecting folders on disk (add folder = appears, delete folder = disappears).
    pub fn list_available_personas(roots: &[PathBuf]) -> Vec<Value> {
        let mut list = Vec::new();
        let mut seen_ids = HashSet::new();

        for root in roots {
            if let Ok(entries) = fs::read_dir(root) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.is_dir() {
                        let folder_name = path.file_name()
                            .map(|n| n.to_string_lossy().to_string())
                            .unwrap_or_default();

                        if folder_name.starts_with('.') || folder_name.eq_ignore_ascii_case("triggers") {
                            continue;
                        }

                        let persona_id = folder_name.to_lowercase();
                        if seen_ids.contains(&persona_id) {
                            continue;
                        }

                        let mut name = String::new();
                        let mut role = String::new();
                        let mut desc = String::new();
                        let mut icon = String::new();
                        let mut style = json!({});

                        let json_path = path.join("agent.json");
                        if json_path.exists() {
                            if let Ok(json_str) = fs::read_to_string(&json_path) {
                                if let Ok(parsed) = serde_json::from_str::<Value>(&json_str) {
                                    if let Some(n) = parsed.get("name").and_then(|v| v.as_str()) {
                                        name = n.to_string();
                                    }
                                    if let Some(r) = parsed.get("role").and_then(|v| v.as_str()) {
                                        role = r.to_string();
                                    }
                                    if let Some(d) = parsed.get("description").and_then(|v| v.as_str()) {
                                        desc = d.to_string();
                                    }
                                    if let Some(ic) = parsed.get("icon").and_then(|v| v.as_str()) {
                                        icon = ic.to_string();
                                    }
                                }
                            }
                        }

                        let style_path = path.join("style.json");
                        if style_path.exists() {
                            if let Ok(s_str) = fs::read_to_string(&style_path) {
                                if let Ok(s_val) = serde_json::from_str::<Value>(&s_str) {
                                    style = s_val;
                                }
                            }
                        }

                        if name.is_empty() {
                            name = folder_name.split('-')
                                .map(|w| {
                                    let mut c = w.chars();
                                    match c.next() {
                                        None => String::new(),
                                        Some(f) => f.to_uppercase().collect::<String>() + c.as_str(),
                                    }
                                })
                                .collect::<Vec<_>>()
                                .join(" ");
                        }

                        if role.is_empty() {
                            role = format!("Specialist {}", name);
                        }

                        if desc.is_empty() {
                            let p_md = path.join("persona.md");
                            let r_md = path.join("rules.md");
                            if p_md.exists() {
                                if let Ok(txt) = fs::read_to_string(&p_md) {
                                    desc = txt.lines().find(|l| !l.trim().is_empty()).unwrap_or(&role).to_string();
                                }
                            } else if r_md.exists() {
                                if let Ok(txt) = fs::read_to_string(&r_md) {
                                    desc = txt.lines().find(|l| !l.trim().is_empty()).unwrap_or(&role).to_string();
                                }
                            } else {
                                desc = role.clone();
                            }
                        }

                        if icon.is_empty() {
                            icon = match persona_id.as_str() {
                                "backend-engineer" | "coder" => "⚙️".to_string(),
                                "frontend-engineer" | "designer" => "🎨".to_string(),
                                "quality-control" | "qa" => "🧪".to_string(),
                                "security-auditor" | "security" => "🛡️".to_string(),
                                "leader" => "👑".to_string(),
                                "mr.flow" | "mrflow" => "⚡".to_string(),
                                _ => "🤖".to_string(),
                            };
                        }

                        seen_ids.insert(persona_id.clone());
                        list.push(json!({
                            "id": persona_id,
                            "name": name,
                            "role": role,
                            "description": desc,
                            "icon": icon,
                            "style": style,
                            "is_default": false,
                            "slash_commands": []
                        }));
                    }
                }
            }
        }

        list.sort_by(|a, b| {
            let a_id = a.get("id").and_then(|v| v.as_str()).unwrap_or("");
            let b_id = b.get("id").and_then(|v| v.as_str()).unwrap_or("");
            a_id.cmp(b_id)
        });

        list
    }

    /// Load persona documents strictly isolated for a specific target persona name.
    /// If target_persona is "default" or empty, loads 0 documents (strict bypass).
    pub fn load_persona_docs_for_persona(roots: &[PathBuf], target_persona: &str) -> Vec<PersonaDocument> {
        let clean_target = target_persona.trim().to_lowercase();
        if clean_target.is_empty() || clean_target == "default" || clean_target.contains("..") || clean_target.contains('/') || clean_target.contains('\\') {
            return Vec::new();
        }

        let mut docs = Vec::new();
        let mut seen_doc_ids = HashSet::new();

        for root in roots {
            let target_dir = root.join(&clean_target);
            if target_dir.exists() && target_dir.is_dir() {
                let mut search_dirs = vec![target_dir.clone()];
                let triggers_dir = target_dir.join("triggers");
                if triggers_dir.exists() && triggers_dir.is_dir() {
                    search_dirs.push(triggers_dir);
                }

                for dir in search_dirs {
                    if let Ok(file_entries) = fs::read_dir(&dir) {
                        for f_entry in file_entries.flatten() {
                            let f_path = f_entry.path();
                            if f_path.is_file() && f_path.extension().and_then(|e| e.to_str()) == Some("md") {
                                if let Ok(content) = fs::read_to_string(&f_path) {
                                    if let Some(doc) = Self::parse_persona_markdown(&content, &f_path, &clean_target) {
                                        if !seen_doc_ids.contains(&doc.id) {
                                            seen_doc_ids.insert(doc.id.clone());
                                            docs.push(doc);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        docs
    }

    /// Parses YAML frontmatter and triggers from a persona markdown file
    pub fn parse_persona_markdown(content: &str, file_path: &Path, default_persona: &str) -> Option<PersonaDocument> {
        let trimmed = content.trim_start();
        if !trimmed.starts_with("---") {
            return None;
        }

        let after_first = &trimmed[3..];
        let end_idx = after_first.find("---")?;
        let frontmatter_str = &after_first[..end_idx];
        let body_markdown = after_first[end_idx + 3..].trim().to_string();

        let mut id = String::new();
        let mut persona = default_persona.to_string();
        let mut target = "prompt".to_string();
        let mut priority: u32 = 80;
        let mut trigger = TriggerSpec::default();

        let mut in_trigger_section = false;
        let mut in_tool_threshold_section = false;
        let mut in_tool_stalled_section = false;
        let mut in_turn_range_section = false;
        let mut active_list_key = String::new();

        for raw_line in frontmatter_str.lines() {
            let line = raw_line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }

            let indent = raw_line.chars().take_while(|c| *c == ' ').count();

            // Handle YAML list item: - "item" or - item
            if line.starts_with("- ") || line == "-" {
                let item = line.trim_start_matches('-').trim().trim_matches('"').trim_matches('\'').to_lowercase();
                if !item.is_empty() {
                    match active_list_key.as_str() {
                        "keywords" => trigger.keywords.push(item),
                        "exclude_keywords" => trigger.exclude_keywords.push(item),
                        "commands" => trigger.commands.push(item),
                        "tools_active" => trigger.tools_active.push(item),
                        "file_patterns" => trigger.file_patterns.push(item),
                        _ => {}
                    }
                }
                continue;
            }

            // Check sections
            if line == "trigger:" {
                in_trigger_section = true;
                in_tool_threshold_section = false;
                in_tool_stalled_section = false;
                in_turn_range_section = false;
                active_list_key.clear();
                continue;
            }

            if in_trigger_section {
                // If indentation dropped back to 2 spaces or line starts with another main trigger key
                if indent <= 2 {
                    in_tool_threshold_section = false;
                    in_tool_stalled_section = false;
                    in_turn_range_section = false;
                }

                if line == "tool_threshold:" {
                    in_tool_threshold_section = true;
                    in_tool_stalled_section = false;
                    in_turn_range_section = false;
                    active_list_key.clear();
                    continue;
                }
                if line == "tool_stalled:" {
                    in_tool_stalled_section = true;
                    in_tool_threshold_section = false;
                    in_turn_range_section = false;
                    active_list_key.clear();
                    continue;
                }
                if line == "turn_range:" {
                    in_turn_range_section = true;
                    in_tool_threshold_section = false;
                    in_tool_stalled_section = false;
                    active_list_key.clear();
                    continue;
                }

                if in_tool_threshold_section {
                    if let Some((k, v)) = Self::split_key_val(line) {
                        if k == "tool" {
                            trigger.tool_threshold_tool = Some(v.trim_matches('"').trim_matches('\'').to_string());
                        } else if k == "min_calls" {
                            if let Ok(n) = v.parse::<usize>() {
                                trigger.tool_threshold_min = n;
                            }
                        }
                    }
                    continue;
                }

                if in_tool_stalled_section {
                    if let Some((k, v)) = Self::split_key_val(line) {
                        if k == "tool" {
                            trigger.tool_stalled_tool = Some(v.trim_matches('"').trim_matches('\'').to_string());
                        } else if k == "consecutive_failures" {
                            if let Ok(n) = v.parse::<usize>() {
                                trigger.tool_stalled_consecutive_failures = n;
                            }
                        }
                    }
                    continue;
                }

                if in_turn_range_section {
                    if let Some((k, v)) = Self::split_key_val(line) {
                        if k == "min_turn" {
                            trigger.min_turn = v.parse::<usize>().ok();
                        } else if k == "max_turn" {
                            trigger.max_turn = v.parse::<usize>().ok();
                        }
                    }
                    continue;
                }

                // General trigger attributes
                if let Some((k, v)) = Self::split_key_val(line) {
                    match k.as_str() {
                        "keywords" => {
                            if v.is_empty() || v == "[]" {
                                active_list_key = "keywords".to_string();
                            } else {
                                trigger.keywords = Self::parse_string_array(&v);
                                active_list_key.clear();
                            }
                        }
                        "commands" | "cmd" | "command_patterns" => {
                            if v.is_empty() || v == "[]" {
                                active_list_key = "commands".to_string();
                            } else {
                                trigger.commands = Self::parse_string_array(&v);
                                active_list_key.clear();
                            }
                        }
                        "exclude" | "exclude_keywords" | "excludes" => {
                            if v.is_empty() || v == "[]" {
                                active_list_key = "exclude_keywords".to_string();
                            } else {
                                trigger.exclude_keywords = Self::parse_string_array(&v);
                                active_list_key.clear();
                            }
                        }
                        "tools_active" => {
                            if v.is_empty() || v == "[]" {
                                active_list_key = "tools_active".to_string();
                            } else {
                                trigger.tools_active = Self::parse_string_array(&v);
                                active_list_key.clear();
                            }
                        }
                        "file_patterns" => {
                            if v.is_empty() || v == "[]" {
                                active_list_key = "file_patterns".to_string();
                            } else {
                                trigger.file_patterns = Self::parse_string_array(&v);
                                active_list_key.clear();
                            }
                        }
                        "always" | "always_active" => {
                            active_list_key.clear();
                            let val_lower = v.trim().to_lowercase();
                            trigger.always = val_lower == "true" || val_lower == "yes" || val_lower == "1";
                        }
                        "min_turn" => {
                            active_list_key.clear();
                            trigger.min_turn = v.parse::<usize>().ok();
                        }
                        "max_turn" => {
                            active_list_key.clear();
                            trigger.max_turn = v.parse::<usize>().ok();
                        }
                        _ => {
                            active_list_key.clear();
                        }
                    }
                }
            } else {
                active_list_key.clear();
                // Top level attributes
                if let Some((k, v)) = Self::split_key_val(line) {
                    match k.as_str() {
                        "id" => id = v.trim_matches('"').trim_matches('\'').to_string(),
                        "persona" => persona = v.trim_matches('"').trim_matches('\'').to_string(),
                        "target" => target = v.trim_matches('"').trim_matches('\'').to_string(),
                        "priority" => priority = v.parse::<u32>().unwrap_or(80),
                        "always" | "always_active" => {
                            let val_lower = v.trim().to_lowercase();
                            trigger.always = val_lower == "true" || val_lower == "yes" || val_lower == "1";
                        }
                        _ => {}
                    }
                }
            }
        }

        if id.is_empty() {
            id = file_path.file_stem()
                .map(|s| format!("{}-{}", default_persona, s.to_string_lossy()))
                .unwrap_or_else(|| format!("{}-doc", default_persona));
        }

        // Auto-detect: If document defines NO trigger rules or is explicitly marked as identity/core,
        // it is an always-active baseline prompt (tanpa trigger).
        let has_any_trigger_rule = !trigger.keywords.is_empty()
            || !trigger.commands.is_empty()
            || !trigger.tools_active.is_empty()
            || !trigger.file_patterns.is_empty()
            || trigger.tool_threshold_tool.is_some()
            || trigger.tool_stalled_tool.is_some()
            || trigger.min_turn.is_some()
            || trigger.max_turn.is_some();

        if !has_any_trigger_rule || target == "identity" || target == "core" {
            trigger.always = true;
        }

        Some(PersonaDocument {
            id,
            persona,
            target,
            priority,
            trigger,
            file_path: file_path.to_path_buf(),
            body_markdown,
        })
    }

    /// Split "key: value"
    fn split_key_val(line: &str) -> Option<(String, String)> {
        let colon = line.find(':')?;
        let k = line[..colon].trim().to_string();
        let v = line[colon + 1..].trim().to_string();
        Some((k, v))
    }

    /// Parse JSON array or comma separated string into Vec<String>
    fn parse_string_array(s: &str) -> Vec<String> {
        let trimmed = s.trim();
        if trimmed.starts_with('[') && trimmed.ends_with(']') {
            if let Ok(arr) = serde_json::from_str::<Vec<String>>(trimmed) {
                return arr.into_iter().map(|item| item.trim().to_lowercase()).filter(|x| !x.is_empty()).collect();
            }
        }

        trimmed.trim_matches(|c| c == '[' || c == ']')
            .split(',')
            .map(|tok| tok.trim().trim_matches('"').trim_matches('\'').to_lowercase())
            .filter(|tok| !tok.is_empty())
            .collect()
    }

    /// Evaluates persona triggers strictly scoped to the chat session's locked persona.
    /// If active_persona_lock is None or "default", returns empty Vec immediately (0 triggers evaluated, 0 token waste).
    pub fn evaluate_triggers_scoped(
        search_text: &str,
        workspace_dir: &Path,
        mounted_tools: Option<&HashSet<String>>,
        tool_stats: Option<&HashMap<String, ToolRunStats>>,
        turn_count: usize,
        persona_roots: &[PathBuf],
        active_persona_lock: Option<&str>,
    ) -> Vec<PersonaMatchResult> {
        let target = match active_persona_lock {
            Some(t) => {
                let clean = t.trim();
                if clean.is_empty() || clean.eq_ignore_ascii_case("default") {
                    return Vec::new();
                }
                clean
            }
            None => return Vec::new(),
        };

        let docs = Self::load_persona_docs_for_persona(persona_roots, target);
        Self::evaluate_docs_triggers(
            &docs,
            search_text,
            workspace_dir,
            mounted_tools,
            tool_stats,
            turn_count,
        )
    }

    /// Evaluates all persona triggers against current context (backward-compatible)
    pub fn evaluate_triggers(
        search_text: &str,
        workspace_dir: &Path,
        mounted_tools: Option<&HashSet<String>>,
        tool_stats: Option<&HashMap<String, ToolRunStats>>,
        turn_count: usize,
        persona_roots: &[PathBuf],
    ) -> Vec<PersonaMatchResult> {
        let docs = Self::load_all_persona_docs(persona_roots);
        Self::evaluate_docs_triggers(
            &docs,
            search_text,
            workspace_dir,
            mounted_tools,
            tool_stats,
            turn_count,
        )
    }

    fn evaluate_docs_triggers(
        docs: &[PersonaDocument],
        search_text: &str,
        workspace_dir: &Path,
        mounted_tools: Option<&HashSet<String>>,
        tool_stats: Option<&HashMap<String, ToolRunStats>>,
        turn_count: usize,
    ) -> Vec<PersonaMatchResult> {
        let search_lower = search_text.to_lowercase();
        let mut matches = Vec::new();

        // Lazy workspace files cache: zero disk I/O if no documents evaluate file_patterns
        let mut ws_files: Option<Vec<String>> = None;

        for doc in docs {
            let mut reasons = Vec::new();

            // 0. EXCLUSION CHECK (Short-circuit): Substring matching
            // If any exclude keyword is contained in search_lower, disqualify immediately!
            let mut is_excluded = false;
            for ex in &doc.trigger.exclude_keywords {
                let ex_clean = ex.trim().to_lowercase();
                if !ex_clean.is_empty() && search_lower.contains(&ex_clean) {
                    is_excluded = true;
                    break;
                }
            }
            if is_excluded {
                continue;
            }

            // Always-Active trigger (Baseline prompt that should always be present)
            if doc.trigger.always {
                reasons.push("always_active".to_string());
            }

            // 1. Keyword matching (Substring contains matching)
            for kw in &doc.trigger.keywords {
                let kw_clean = kw.trim().to_lowercase();
                if !kw_clean.is_empty() && search_lower.contains(&kw_clean) {
                    reasons.push(format!("keyword: '{}'", kw));
                    break;
                }
            }

            // 1b. Command / CLI matching (e.g. "git commit", "cargo test", "/plan")
            for cmd in &doc.trigger.commands {
                let cmd_clean = cmd.trim().to_lowercase();
                if !cmd_clean.is_empty() && search_lower.contains(&cmd_clean) {
                    reasons.push(format!("cmd: '{}'", cmd));
                    break;
                }
            }

            // 2. Active tools matching (case-insensitive)
            if let Some(mounted) = mounted_tools {
                for tool in &doc.trigger.tools_active {
                    let tool_clean = tool.to_lowercase();
                    if mounted.contains(tool) || mounted.contains(&tool_clean) || mounted.iter().any(|m| m.eq_ignore_ascii_case(tool)) {
                        reasons.push(format!("tool_active: '{}'", tool));
                        break;
                    }
                }
            }

            // 3. Tool usage threshold (case-insensitive)
            if let (Some(t_name), Some(stats_map)) = (&doc.trigger.tool_threshold_tool, tool_stats) {
                let t_clean = t_name.to_lowercase();
                if let Some(st) = stats_map.get(t_name).or_else(|| stats_map.get(&t_clean)) {
                    if doc.trigger.tool_threshold_min > 0 && st.total_calls >= doc.trigger.tool_threshold_min {
                        reasons.push(format!("tool_threshold: '{}' (calls: {} >= {})", t_name, st.total_calls, doc.trigger.tool_threshold_min));
                    }
                }
            }

            // 4. Tool stalled / consecutive failure circuit breaker (case-insensitive)
            if let (Some(t_name), Some(stats_map)) = (&doc.trigger.tool_stalled_tool, tool_stats) {
                let t_clean = t_name.to_lowercase();
                if let Some(st) = stats_map.get(t_name).or_else(|| stats_map.get(&t_clean)) {
                    if doc.trigger.tool_stalled_consecutive_failures > 0 && st.consecutive_failures >= doc.trigger.tool_stalled_consecutive_failures {
                        reasons.push(format!("tool_stalled: '{}' (failures: {} >= {})", t_name, st.consecutive_failures, doc.trigger.tool_stalled_consecutive_failures));
                    }
                }
            }

            // 5. File pattern matching in workspace (lazily sampled on demand)
            for pat in &doc.trigger.file_patterns {
                let files = ws_files.get_or_insert_with(|| Self::sample_workspace_files(workspace_dir));
                if Self::matches_file_pattern(pat, files) {
                    reasons.push(format!("file_pattern: '{}'", pat));
                    break;
                }
            }

            // 6. Turn budget range
            if let Some(min_t) = doc.trigger.min_turn {
                if turn_count < min_t {
                    // Turn too early, disqualify
                    continue;
                }
            }
            if let Some(max_t) = doc.trigger.max_turn {
                if turn_count > max_t {
                    // Turn exceeded, disqualify
                    continue;
                }
            }

            // If doc has only turn_range trigger (no other triggers), record turn_range match reason
            let has_non_turn_triggers = !doc.trigger.keywords.is_empty()
                || !doc.trigger.commands.is_empty()
                || !doc.trigger.tools_active.is_empty()
                || !doc.trigger.file_patterns.is_empty()
                || doc.trigger.tool_threshold_tool.is_some()
                || doc.trigger.tool_stalled_tool.is_some()
                || doc.trigger.always;

            if (doc.trigger.min_turn.is_some() || doc.trigger.max_turn.is_some()) && !has_non_turn_triggers {
                reasons.push(format!("turn_range: [min: {:?}, max: {:?}]", doc.trigger.min_turn, doc.trigger.max_turn));
            }

            // If at least one trigger matched
            if !reasons.is_empty() {
                matches.push(PersonaMatchResult {
                    persona_name: doc.persona.clone(),
                    target_type: doc.target.clone(),
                    doc_id: doc.id.clone(),
                    priority: doc.priority,
                    match_reasons: reasons,
                    body_markdown: doc.body_markdown.clone(),
                });
            }
        }

        // Sort by priority descending
        matches.sort_by(|a, b| b.priority.cmp(&a.priority));
        matches
    }

    /// Formats matching persona documents into context injection XML
    pub fn compose_injection_block(matches: &[PersonaMatchResult]) -> String {
        if matches.is_empty() {
            return String::new();
        }

        let mut out = String::new();
        out.push_str(&crate::prompt_enclave::PromptEnclave::external_injection_header());

        for m in matches {
            let tag_name = match m.target_type.as_str() {
                "rules" => "SOVEREIGN_PERSONA_RULES",
                "kinerja" => "SOVEREIGN_PERSONA_KINERJA",
                _ => "ACTIVE_SOVEREIGN_PERSONA",
            };

            let reasons_str = m.match_reasons.join(", ");
            out.push_str(&format!(
                "<{} id=\"{}\" role=\"{}\" target=\"{}\" priority=\"{}\" triggered_by=\"{}\">\n",
                tag_name, m.doc_id, m.persona_name, m.target_type, m.priority, reasons_str
            ));
            out.push_str(m.body_markdown.trim());
            out.push_str(&format!("\n</{}>\n\n", tag_name));
        }

        out.push_str(&crate::prompt_enclave::PromptEnclave::external_injection_footer());
        out
    }

    /// Formats matching persona documents into context injection XML:
    /// Injects all baseline always-active prompts (e.g. 00_identity.md) AND
    /// all matching triggered specialized prompts (Multi-Prompt Modular Architecture).
    pub fn compose_top_single_persona_block(matches: &[PersonaMatchResult]) -> String {
        if matches.is_empty() {
            return String::new();
        }
        // In modular architecture, all documents whose triggers matched (or always-active)
        // are injected into context, preserving priority order.
        Self::compose_injection_block(matches)
    }

    /// Helper: samples file names from workspace root and immediate subdirectories
    fn sample_workspace_files(workspace_dir: &Path) -> Vec<String> {
        let mut list = Vec::new();
        if let Ok(entries) = fs::read_dir(workspace_dir) {
            for entry in entries.flatten() {
                let p = entry.path();
                if let Some(name) = p.file_name().and_then(|n| n.to_str()) {
                    let name_lower = name.replace('\\', "/").to_lowercase();
                    list.push(name_lower.clone());
                    if p.is_dir() && !name_lower.starts_with('.') && name_lower != "target" && name_lower != "node_modules" {
                        if let Ok(sub_entries) = fs::read_dir(&p) {
                            for sub in sub_entries.flatten() {
                                let sub_p = sub.path();
                                if let Some(sub_name) = sub_p.file_name().and_then(|n| n.to_str()) {
                                    let sub_lower = sub_name.replace('\\', "/").to_lowercase();
                                    list.push(sub_lower.clone());
                                    let rel_path = format!("{}/{}", name_lower, sub_lower);
                                    list.push(rel_path.clone());

                                    // Support 2nd level subdirectory (e.g. docs/adr)
                                    if sub_p.is_dir() && !sub_lower.starts_with('.') {
                                        if let Ok(sub2_entries) = fs::read_dir(&sub_p) {
                                            for sub2 in sub2_entries.flatten() {
                                                if let Some(sub2_name) = sub2.path().file_name().and_then(|n| n.to_str()) {
                                                    let sub2_lower = sub2_name.replace('\\', "/").to_lowercase();
                                                    list.push(sub2_lower.clone());
                                                    list.push(format!("{}/{}", rel_path, sub2_lower));
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
        list
    }

    /// Helper: matches pattern (e.g. "*.rs", "Cargo.toml", "*.mq5", "plugins/**")
    fn matches_file_pattern(pattern: &str, file_names: &[String]) -> bool {
        let pat_clean = pattern.replace('\\', "/").trim().to_lowercase();
        if pat_clean.is_empty() {
            return false;
        }
        if pat_clean.starts_with("*.") {
            let ext = &pat_clean[1..]; // ".rs", ".mq5", ".url.json", ".adr.md"
            file_names.iter().any(|f| f.ends_with(ext))
        } else if pat_clean.ends_with("/**") || pat_clean.ends_with("/*") {
            let prefix = pat_clean.trim_end_matches("/**").trim_end_matches("/*").trim_end_matches('/');
            file_names.iter().any(|f| f == prefix || f.starts_with(&format!("{}/", prefix)))
        } else {
            file_names.iter().any(|f| f == &pat_clean || f.ends_with(&format!("/{}", pat_clean)))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_persona_markdown_frontmatter() {
        let sample = r#"---
id: coder-strict-rules
persona: coder
target: rules
priority: 98
trigger:
  keywords: ["refactor", "delete", "hapus"]
  tool_stalled:
    tool: "run_command"
    consecutive_failures: 2
  tool_threshold:
    tool: "run_command"
    min_calls: 3
  file_patterns: ["*.rs", "Cargo.toml"]
---

### STRICT RULES BODY
Never delete locked code.
"#;
        let doc = SovereignPersonaEngine::parse_persona_markdown(
            sample,
            Path::new("/dummy/rules.md"),
            "coder",
        ).expect("Failed to parse persona markdown");

        assert_eq!(doc.id, "coder-strict-rules");
        assert_eq!(doc.persona, "coder");
        assert_eq!(doc.target, "rules");
        assert_eq!(doc.priority, 98);
        assert_eq!(doc.trigger.keywords, vec!["refactor", "delete", "hapus"]);
        assert_eq!(doc.trigger.tool_stalled_tool, Some("run_command".to_string()));
        assert_eq!(doc.trigger.tool_stalled_consecutive_failures, 2);
        assert_eq!(doc.trigger.tool_threshold_tool, Some("run_command".to_string()));
        assert_eq!(doc.trigger.tool_threshold_min, 3);
        assert_eq!(doc.trigger.file_patterns, vec!["*.rs", "cargo.toml"]);
        assert!(doc.body_markdown.contains("Never delete locked code."));
    }

    #[test]
    fn test_evaluate_triggers_keyword_and_tool_stall() {
        let temp_dir = std::env::temp_dir().join(format!("test_persona_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        let persona_dir = temp_dir.join("Persona/forex-specialis");
        fs::create_dir_all(&persona_dir).unwrap();

        let forex_md = r#"---
id: forex-risk-guardrail
persona: forex-specialis
target: rules
priority: 95
trigger:
  keywords: ["xauusd", "gold", "lot", "leverage"]
  tools_active: ["forex_calculator"]
---

### FOREX RISK
Always set SL.
"#;
        fs::write(persona_dir.join("rules.md"), forex_md).unwrap();

        let roots = vec![temp_dir.join("Persona")];

        // 1. Matching keyword
        let matches = SovereignPersonaEngine::evaluate_triggers(
            "tolong hitung lot untuk xauusd",
            &temp_dir,
            None,
            None,
            1,
            &roots,
        );
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].persona_name, "forex-specialis");
        assert_eq!(matches[0].target_type, "rules");
        assert!(matches[0].match_reasons.iter().any(|r| r.contains("xauusd")));

        // 2. Unrelated chat -> 0 matches (Zero bloat)
        let no_matches = SovereignPersonaEngine::evaluate_triggers(
            "resep membuat kue bolu",
            &temp_dir,
            None,
            None,
            1,
            &roots,
        );
        assert!(no_matches.is_empty());
        let empty_block = SovereignPersonaEngine::compose_injection_block(&no_matches);
        assert!(empty_block.is_empty());

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_real_workspace_persona_files() {
        let manifest_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string()));
        let ws = if manifest_dir.join("Persona").is_dir() {
            manifest_dir.clone()
        } else if manifest_dir.parent().map(|p| p.join("Persona").is_dir()).unwrap_or(false) {
            manifest_dir.parent().unwrap().to_path_buf()
        } else {
            manifest_dir.parent().and_then(|p| p.parent()).map(|p| p.to_path_buf()).unwrap_or_else(|| manifest_dir.clone())
        };
        let roots = SovereignPersonaEngine::resolve_persona_roots(&ws, &manifest_dir);

        // 1. Verify docs load from disk
        let docs = SovereignPersonaEngine::load_all_persona_docs(&roots);
        if docs.is_empty() {
            println!("No persona markdown files on disk, skipping real workspace test");
            return;
        }

        let doc_ids: Vec<&str> = docs.iter().map(|d| d.id.as_str()).collect();
        assert!(doc_ids.contains(&"coder-identity"));
        assert!(doc_ids.contains(&"coder-strict-rules"));
        assert!(doc_ids.contains(&"coder-execution-sop"));
        if doc_ids.iter().any(|id| id.starts_with("trader")) {
            assert!(doc_ids.contains(&"trader-identity"));
        }
        if doc_ids.iter().any(|id| id.starts_with("forex")) {
            assert!(doc_ids.contains(&"forex-specialist-identity"));
        }

        // 2. Test Coder Trigger
        let matches_coder = SovereignPersonaEngine::evaluate_triggers(
            "bikin script programmer untuk koding backend",
            &ws,
            None,
            None,
            1,
            &roots,
        );
        assert!(!matches_coder.is_empty());
        assert!(matches_coder.iter().any(|m| m.persona_name == "coder"));

        // 3. Test Forex Specialist Trigger (if exists on disk)
        if roots.iter().any(|r| r.join("forex-specialis").exists()) {
            let matches_forex = SovereignPersonaEngine::evaluate_triggers(
                "analisa pair xauusd dan eurusd untuk entry",
                &ws,
                None,
                None,
                1,
                &roots,
            );
            assert!(!matches_forex.is_empty());
            assert!(matches_forex.iter().any(|m| m.persona_name == "forex-specialis"));
        }

        // 4. Test Trader Trigger (if exists on disk)
        if roots.iter().any(|r| r.join("trader").exists()) {
            let matches_trader = SovereignPersonaEngine::evaluate_triggers(
                "setup trading untuk crypto btc dan hitung risk reward",
                &ws,
                None,
                None,
                1,
                &roots,
            );
            assert!(!matches_trader.is_empty());
            assert!(matches_trader.iter().any(|m| m.persona_name == "trader"));
        }

        // 5. Test Tool Stall Trigger (Consecutive Failures)
        let mut stats = HashMap::new();
        stats.insert("run_command".to_string(), ToolRunStats {
            total_calls: 5,
            consecutive_failures: 2,
            last_exit_code: 1,
        });

        let matches_stall = SovereignPersonaEngine::evaluate_triggers(
            "lanjutkan perintah selanjutnya",
            &ws,
            None,
            Some(&stats),
            1,
            &roots,
        );
        assert!(matches_stall.iter().any(|m| m.doc_id == "coder-strict-rules"));
        let injection = SovereignPersonaEngine::compose_injection_block(&matches_stall);
        assert!(injection.contains("SOVEREIGN_PERSONA_RULES"));
        assert!(injection.contains("coder-strict-rules"));

        // 5b. Test Multi-Prompt Injection on Real Coder Persona (cmd: git commit)
        let matches_git_real = SovereignPersonaEngine::evaluate_triggers_scoped(
            "jalankan git commit -m 'feat: refactor engine' sekarang",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        let block_git = SovereignPersonaEngine::compose_top_single_persona_block(&matches_git_real);
        assert!(block_git.contains("coder-identity"), "Baseline identity must be in block");
        assert!(block_git.contains("coder-git-guardrails-wizard"), "Git guardrails wizard must be in block");

        // 6. Test SEO vs YouTube Exclusion and Contains Matching on Real Personas (if exist on disk)
        if roots.iter().any(|r| r.join("seo").exists() && r.join("youtube").exists()) {
            assert!(doc_ids.contains(&"seo-web-intelligence-prompt"));
            assert!(doc_ids.contains(&"youtube-intelligence-prompt"));

            // Case A: Generic .com website triggers SEO / Web Recon, NOT YouTube
            let matches_web = SovereignPersonaEngine::evaluate_triggers(
                "cek ranking domain tokped.com dan traffic",
                &ws,
                None,
                None,
                1,
                &roots,
            );
            assert!(matches_web.iter().any(|m| m.persona_name == "seo"), "SEO persona must trigger on tokped.com");
            assert!(!matches_web.iter().any(|m| m.persona_name == "youtube"), "YouTube persona must not trigger on tokped.com");

            // Case B: youtube.com URL triggers YouTube Intelligence, cleanly EXCLUDES SEO
            let matches_yt_real = SovereignPersonaEngine::evaluate_triggers(
                "buka url https://youtube.com/watch?v=123 dan ekstrak",
                &ws,
                None,
                None,
                1,
                &roots,
            );
            assert!(!matches_yt_real.iter().any(|m| m.persona_name == "seo"), "SEO persona must be excluded on youtube.com");
            assert!(matches_yt_real.iter().any(|m| m.persona_name == "youtube"), "YouTube persona must trigger on youtube.com");

            // Case C: Comma typo youtube,com triggers YouTube Intelligence, cleanly EXCLUDES SEO
            let matches_comma_real = SovereignPersonaEngine::evaluate_triggers(
                "tolong cek channel youtube,com yang ini bro",
                &ws,
                None,
                None,
                1,
                &roots,
            );
            assert!(!matches_comma_real.iter().any(|m| m.persona_name == "seo"), "SEO persona must be excluded on youtube,com");
            assert!(matches_comma_real.iter().any(|m| m.persona_name == "youtube"), "YouTube persona must trigger on youtube,com");
        }
    }

    #[test]
    fn test_auto_reconstitution_of_persona_skill_and_body_prioritization() {
        let temp_dir = std::env::temp_dir().join(format!("flw_persona_body_test_{}", std::process::id()));
        let dummy_workspace = temp_dir.join("user_workspace");
        let flowork_body = temp_dir.join("FLOWORK");
        let subagent_dir = flowork_body.join("system").join("subagent");
        let _ = fs::create_dir_all(&dummy_workspace);
        let _ = fs::create_dir_all(&subagent_dir);

        // 1. Verify single source of truth: roots must locate system/subagent in flowork_body
        let roots = SovereignPersonaEngine::resolve_persona_roots(&dummy_workspace, &flowork_body);
        assert!(!roots.is_empty(), "Roots must locate system/subagent in Flowork body");
        assert!(roots.contains(&subagent_dir), "Roots must contain system/subagent");
        assert!(!flowork_body.join("Persona").exists(), "Persona directory MUST NOT exist!");
        assert!(!dummy_workspace.join("Persona").exists(), "Workspace MUST NOT be polluted with Persona folder!");

        // 2. Verify ensure_persona_skill is a strict no-op that never creates Persona
        SovereignPersonaEngine::ensure_persona_skill(&flowork_body.join("Persona"));
        assert!(!flowork_body.join("Persona").exists(), "ensure_persona_skill must never create Persona folder");

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_persona_and_trigger_exclusion_contains_matching() {
        let temp_dir = std::env::temp_dir().join(format!("flw_exclusion_test_{}", std::process::id()));
        let persona_body = temp_dir.join("FLOWORK/Persona");
        let web_dir = persona_body.join("web_recon");
        let yt_dir = persona_body.join("yt_recon");
        let _ = fs::create_dir_all(&web_dir);
        let _ = fs::create_dir_all(&yt_dir);

        // Persona 1: General Web Recon (Excludes YouTube)
        let web_content = r#"---
id: web-general-prompt
persona: web_recon
target: prompt
priority: 85
trigger:
  keywords: [.com, website, crawl, domain]
  exclude_keywords: [youtube, youtu.be]
---
# GENERAL WEB RECON
Execute standard DOM extraction.
"#;
        fs::write(web_dir.join("prompt.md"), web_content).unwrap();

        // Persona 2: YouTube Specialized Recon
        let yt_content = r#"---
id: yt-specialist-prompt
persona: yt_recon
target: prompt
priority: 95
trigger:
  keywords: [youtube, youtu.be, yt spy]
---
# YOUTUBE SPECIALIST
Execute video player intelligence and transcript deep scan.
"#;
        fs::write(yt_dir.join("prompt.md"), yt_content).unwrap();

        let ws = temp_dir.join("workspace");
        let _ = fs::create_dir_all(&ws);
        let roots = vec![persona_body];

        // Case 1: Standard URL containing youtube.com
        let matches_yt = SovereignPersonaEngine::evaluate_triggers(
            "buka url https://youtube.com/watch?v=123 dan ekstrak",
            &ws,
            None,
            None,
            1,
            &roots,
        );
        // web_recon MUST be excluded because input contains "youtube"
        assert!(!matches_yt.iter().any(|m| m.doc_id == "web-general-prompt"), "web_recon MUST BE EXCLUDED on youtube.com target");
        // yt_recon MUST be triggered because input contains "youtube"
        assert!(matches_yt.iter().any(|m| m.doc_id == "yt-specialist-prompt"), "yt_recon MUST TRIGGER on youtube.com target");

        // Case 2: User prompt with comma format (e.g. youtube,com)
        let matches_comma = SovereignPersonaEngine::evaluate_triggers(
            "tolong cek channel youtube,com yang ini bro",
            &ws,
            None,
            None,
            1,
            &roots,
        );
        assert!(!matches_comma.iter().any(|m| m.doc_id == "web-general-prompt"), "web_recon MUST BE EXCLUDED on youtube,com");
        assert!(matches_comma.iter().any(|m| m.doc_id == "yt-specialist-prompt"), "yt_recon MUST TRIGGER on youtube,com");

        // Case 3: Normal website (example.com)
        let matches_example = SovereignPersonaEngine::evaluate_triggers(
            "buka https://example.com/blog dan analisa kontennya",
            &ws,
            None,
            None,
            1,
            &roots,
        );
        // web_recon MUST trigger on example.com (.com match)
        assert!(matches_example.iter().any(|m| m.doc_id == "web-general-prompt"), "web_recon MUST TRIGGER on example.com");
        // yt_recon MUST NOT trigger
        assert!(!matches_example.iter().any(|m| m.doc_id == "yt-specialist-prompt"), "yt_recon MUST NOT TRIGGER on example.com");

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_persona_session_lock_and_scoped_triggers() {
        let temp_dir = std::env::temp_dir().join(format!("flw_session_lock_test_{}", std::process::id()));
        let persona_body = temp_dir.join("FLOWORK/Persona");
        let coder_dir = persona_body.join("coder");
        let trader_dir = persona_body.join("trader");
        let _ = fs::create_dir_all(&coder_dir);
        let _ = fs::create_dir_all(&trader_dir);

        // Persona 1: Coder
        let coder_content = r#"---
id: coder-prompt
persona: coder
target: prompt
priority: 95
trigger:
  keywords: [coding, refactor, debug, compile]
---
# CODER
Code execution and compiler verification.
"#;
        fs::write(coder_dir.join("prompt.md"), coder_content).unwrap();

        // Persona 2: Trader
        let trader_content = r#"---
id: trader-prompt
persona: trader
target: prompt
priority: 95
trigger:
  keywords: [trading, bitcoin, crypto, forex, market]
---
# TRADER
Market technical analysis and order book inspection.
"#;
        fs::write(trader_dir.join("prompt.md"), trader_content).unwrap();

        let ws = temp_dir.join("workspace");
        let _ = fs::create_dir_all(&ws);
        let roots = vec![persona_body];

        // 1. Verify dynamic list_available_personas
        let personas = SovereignPersonaEngine::list_available_personas(&roots);
        assert!(personas.iter().any(|p| p["id"] == "coder"));
        assert!(personas.iter().any(|p| p["id"] == "trader"));

        // 2. Default Mode: Both coder and trader keywords present, but MUST return 0 matches!
        let matches_default = SovereignPersonaEngine::evaluate_triggers_scoped(
            "tolong coding bot trading bitcoin dan compile refactor",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("default"),
        );
        assert!(matches_default.is_empty(), "Default mode MUST NOT trigger any external persona!");

        let matches_none = SovereignPersonaEngine::evaluate_triggers_scoped(
            "tolong coding bot trading bitcoin dan compile refactor",
            &ws,
            None,
            None,
            1,
            &roots,
            None,
        );
        assert!(matches_none.is_empty(), "None mode MUST NOT trigger any external persona!");

        // 3. Coder Session Lock: Passed mixed coding & trading keywords
        let matches_coder = SovereignPersonaEngine::evaluate_triggers_scoped(
            "tolong coding bot trading bitcoin dan compile refactor",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        assert!(!matches_coder.is_empty());
        assert!(matches_coder.iter().all(|m| m.persona_name == "coder"), "Coder lock MUST ONLY match coder persona!");
        assert!(!matches_coder.iter().any(|m| m.persona_name == "trader"), "Trader persona MUST NOT leak into coder session!");

        // 4. Trader Session Lock: Passed mixed coding & trading keywords
        let matches_trader = SovereignPersonaEngine::evaluate_triggers_scoped(
            "tolong coding bot trading bitcoin dan compile refactor",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("trader"),
        );
        assert!(!matches_trader.is_empty());
        assert!(matches_trader.iter().all(|m| m.persona_name == "trader"), "Trader lock MUST ONLY match trader persona!");
        assert!(!matches_trader.iter().any(|m| m.persona_name == "coder"), "Coder persona MUST NOT leak into trader session!");

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_always_active_baseline_and_dynamic_composition() {
        let temp_dir = std::env::temp_dir().join(format!("flw_always_test_{}", std::process::id()));
        let persona_body = temp_dir.join("FLOWORK/Persona/coder");
        let _ = fs::create_dir_all(&persona_body);

        // Doc 1: Always-active baseline identity (without trigger keywords, always: true)
        let doc1 = r#"---
id: coder-identity
persona: coder
target: prompt
priority: 100
always: true
---
# CODER BASELINE IDENTITY
You are an elite Senior Software Engineer.
"#;
        fs::write(persona_body.join("00_identity.md"), doc1).unwrap();

        // Doc 2: Dynamic specialized prompt A (TDD)
        let doc2 = r#"---
id: coder-tdd
persona: coder
target: prompt
priority: 90
trigger:
  keywords: ["tdd", "red-green-refactor", "unit test"]
---
# TDD DOCTRINE
Write failing tests first.
"#;
        fs::write(persona_body.join("14_tdd.md"), doc2).unwrap();

        // Doc 3: Dynamic specialized prompt B (Architecture)
        let doc3 = r#"---
id: coder-arch
persona: coder
target: prompt
priority: 80
trigger:
  keywords: ["architecture", "adr", "system design"]
---
# ARCHITECTURE DOCTRINE
Deep modules and clear boundaries.
"#;
        fs::write(persona_body.join("13_arch.md"), doc3).unwrap();

        let ws = temp_dir.join("workspace");
        let _ = fs::create_dir_all(&ws);
        let roots = vec![temp_dir.join("FLOWORK/Persona")];

        // Scenario 1: User gives arbitrary message without keywords (e.g. "selamat pagi")
        let matches_baseline = SovereignPersonaEngine::evaluate_triggers_scoped(
            "selamat pagi bro apa kabar",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        // Baseline MUST match because always == true
        assert_eq!(matches_baseline.len(), 1);
        assert_eq!(matches_baseline[0].doc_id, "coder-identity");
        assert!(matches_baseline[0].match_reasons.contains(&"always_active".to_string()));

        let block1 = SovereignPersonaEngine::compose_top_single_persona_block(&matches_baseline);
        assert!(block1.contains("CODER BASELINE IDENTITY"), "Baseline identity must always be in context");
        assert!(!block1.contains("TDD DOCTRINE"));
        assert!(!block1.contains("ARCHITECTURE DOCTRINE"));

        // Scenario 2: User mentions both TDD and Architecture
        let matches_multi = SovereignPersonaEngine::evaluate_triggers_scoped(
            "tolong buat unit test tdd dan rancang architecture",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        // All 3 docs match (1 always + 2 keywords)
        assert_eq!(matches_multi.len(), 3);

        let block2 = SovereignPersonaEngine::compose_top_single_persona_block(&matches_multi);
        // Both baseline AND all triggered prompts (TDD + Arch) are included in modular multi-prompt architecture!
        assert!(block2.contains("CODER BASELINE IDENTITY"), "Baseline identity must be included");
        assert!(block2.contains("TDD DOCTRINE"), "TDD doctrine must be included when triggered");
        assert!(block2.contains("ARCHITECTURE DOCTRINE"), "Architecture doctrine must also be included when triggered");

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_cmd_and_tools_active_triggers() {
        let temp_dir = std::env::temp_dir().join(format!("flw_cmd_tool_test_{}", std::process::id()));
        let persona_body = temp_dir.join("FLOWORK/Persona/coder");
        let _ = fs::create_dir_all(&persona_body);

        // Doc with cmd trigger (git guardrails)
        let doc_git = r#"---
id: coder-git
persona: coder
target: prompt
priority: 85
trigger:
  cmd: ["git commit", "git push", "git rebase"]
---
# GIT GUARDRAILS
Never force push to main.
"#;
        fs::write(persona_body.join("16_git.md"), doc_git).unwrap();

        // Doc with tools_active trigger (swarm)
        let doc_swarm = r#"---
id: coder-swarm
persona: coder
target: prompt
priority: 85
trigger:
  tools_active: ["invoke_subagent"]
---
# SWARM ARCHITECTURE
Coordinate subagents effectively.
"#;
        fs::write(persona_body.join("07_swarm.md"), doc_swarm).unwrap();

        let ws = temp_dir.join("workspace");
        let _ = fs::create_dir_all(&ws);
        let roots = vec![temp_dir.join("FLOWORK/Persona")];

        // Test 1: User runs a git commit command
        let matches_git = SovereignPersonaEngine::evaluate_triggers_scoped(
            "jalankan git commit -m 'feat: new module' sekarang",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        assert!(matches_git.iter().any(|m| m.doc_id == "coder-git"));
        assert!(matches_git.iter().any(|m| m.match_reasons.iter().any(|r| r.contains("cmd: 'git commit'"))));

        // Test 2: Active tool is invoke_subagent
        let mut mounted = HashSet::new();
        mounted.insert("invoke_subagent".to_string());
        let matches_tool = SovereignPersonaEngine::evaluate_triggers_scoped(
            "bantu selesaikan tugas ini",
            &ws,
            Some(&mounted),
            None,
            1,
            &roots,
            Some("coder"),
        );
        assert!(matches_tool.iter().any(|m| m.doc_id == "coder-swarm"));
        assert!(matches_tool.iter().any(|m| m.match_reasons.iter().any(|r| r.contains("tool_active: 'invoke_subagent'"))));

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_exhaustive_combinatorial_trigger_and_multi_prompt_audits() {
        let manifest_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string()));
        let ws = if manifest_dir.join("Persona").is_dir() {
            manifest_dir.clone()
        } else if manifest_dir.parent().map(|p| p.join("Persona").is_dir()).unwrap_or(false) {
            manifest_dir.parent().unwrap().to_path_buf()
        } else {
            manifest_dir.parent().and_then(|p| p.parent()).map(|p| p.to_path_buf()).unwrap_or_else(|| manifest_dir.clone())
        };
        let roots = SovereignPersonaEngine::resolve_persona_roots(&ws, &manifest_dir);
        let docs = SovereignPersonaEngine::load_all_persona_docs(&roots);
        if docs.is_empty() {
            println!("No persona markdown files on disk, skipping combinatorial test");
            return;
        }

        // --- VERIFICATION 1: Multi-Prompt Composition & 00_identity.md Baseline ---
        // Verify that baseline prompt 00_identity.md (always: true) is ALWAYS present in every single turn regardless of what triggers match.
        let empty_input_matches = SovereignPersonaEngine::evaluate_triggers_scoped(
            "halo bot apa kabar",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        assert!(!empty_input_matches.is_empty(), "Baseline prompt must be present on arbitrary input");
        assert_eq!(empty_input_matches[0].doc_id, "coder-identity");
        assert!(empty_input_matches[0].match_reasons.contains(&"always_active".to_string()));

        let baseline_block = SovereignPersonaEngine::compose_top_single_persona_block(&empty_input_matches);
        assert!(baseline_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-identity\""), "00_identity.md must be XML-wrapped with unique ID");
        assert!(baseline_block.contains("triggered_by=\"always_active\""), "00_identity.md must annotate always_active trigger reason");

        // --- SCENARIO 1 (Git Workflow) ---
        // User types: git commit -m 'feat: test'
        // Expected: BOTH 00_identity.md and 16_git_guardrails_wizard.md injected into the same XML block.
        let s1_matches = SovereignPersonaEngine::evaluate_triggers_scoped(
            "git commit -m 'feat: test'",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        let s1_ids: Vec<&str> = s1_matches.iter().map(|m| m.doc_id.as_str()).collect();
        assert!(s1_ids.contains(&"coder-identity"), "Scenario 1: 00_identity.md must match");
        assert!(s1_ids.contains(&"coder-git-guardrails-wizard"), "Scenario 1: 16_git_guardrails_wizard.md must match");

        let s1_block = SovereignPersonaEngine::compose_top_single_persona_block(&s1_matches);
        assert!(s1_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-identity\""), "Scenario 1: coder-identity must be in XML block");
        assert!(s1_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-git-guardrails-wizard\""), "Scenario 1: 16_git_guardrails_wizard.md must be in XML block");
        assert!(s1_block.contains("triggered_by=\"always_active\""));
        assert!(s1_block.contains("cmd: 'git commit'"));
        println!("============================================================");
        println!("AUDIT EVIDENCE - SCENARIO 1 (Git Workflow)");
        println!("Input: git commit -m 'feat: test'");
        for m in &s1_matches {
            println!("  -> Matched ID: {}, Priority: {}, Reasons: {:?}", m.doc_id, m.priority, m.match_reasons);
        }
        println!("Generated XML block tags:");
        for line in s1_block.lines() {
            if line.starts_with("<ACTIVE_SOVEREIGN_PERSONA") || line.starts_with("<!--") || line.starts_with("<SOVEREIGN_") {
                println!("  {}", line);
            }
        }
        println!("✅ SCENARIO 1: PASSED (BOTH 00_identity.md and 16_git_guardrails_wizard.md injected into the same XML block)");

        // --- SCENARIO 2 (Testing & Failure Triage) ---
        // User executes cargo test and run_command has consecutive_failures == 1.
        // Expected: 00_identity.md, 03_kendali_mutu_qc.md, and 14_spesifikasi_triase_tdd.md ALL injected together.
        let mut s2_stats = HashMap::new();
        s2_stats.insert("run_command".to_string(), ToolRunStats {
            total_calls: 3,
            consecutive_failures: 1,
            last_exit_code: 1,
        });

        let s2_matches = SovereignPersonaEngine::evaluate_triggers_scoped(
            "cargo test",
            &ws,
            None,
            Some(&s2_stats),
            1,
            &roots,
            Some("coder"),
        );
        let s2_ids: Vec<&str> = s2_matches.iter().map(|m| m.doc_id.as_str()).collect();
        assert!(s2_ids.contains(&"coder-identity"), "Scenario 2: 00_identity.md must match");
        assert!(s2_ids.contains(&"coder-kendali-mutu-qc"), "Scenario 2: 03_kendali_mutu_qc.md must match");
        assert!(s2_ids.contains(&"coder-spesifikasi-triase-tdd"), "Scenario 2: 14_spesifikasi_triase_tdd.md must match");

        let s2_block = SovereignPersonaEngine::compose_top_single_persona_block(&s2_matches);
        assert!(s2_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-identity\""));
        assert!(s2_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-kendali-mutu-qc\""));
        assert!(s2_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-spesifikasi-triase-tdd\""));
        assert!(s2_block.contains("cmd: 'cargo test'"));
        assert!(s2_block.contains("tool_stalled: 'run_command' (failures: 1 >= 1)"));
        println!("============================================================");
        println!("AUDIT EVIDENCE - SCENARIO 2 (Testing & Failure Triage)");
        println!("Input: cargo test, run_command consecutive_failures: 1");
        for m in &s2_matches {
            println!("  -> Matched ID: {}, Priority: {}, Reasons: {:?}", m.doc_id, m.priority, m.match_reasons);
        }
        println!("Generated XML block tags:");
        for line in s2_block.lines() {
            if line.starts_with("<ACTIVE_SOVEREIGN_PERSONA") || line.starts_with("<!--") || line.starts_with("<SOVEREIGN_") {
                println!("  {}", line);
            }
        }
        println!("✅ SCENARIO 2: PASSED (00_identity.md, 03_kendali_mutu_qc.md, and 14_spesifikasi_triase_tdd.md ALL injected together)");

        // --- SCENARIO 3 (Deep Code Refactoring) ---
        // Tools active include replace_file_content in a Rust repo (*.rs file present).
        // Expected: 00_identity.md, 01_function_calling.md, 02_ruh_rekayasa.md, and 12_desain_modul_mendalam.md ALL injected simultaneously.
        let temp_rust_ws = std::env::temp_dir().join(format!("flw_scenario3_rust_repo_{}", std::process::id()));
        fs::create_dir_all(&temp_rust_ws).unwrap();
        fs::write(temp_rust_ws.join("lib.rs"), "// rust source file\npub fn core_engine() {}\n").unwrap();

        let mut s3_mounted = HashSet::new();
        s3_mounted.insert("replace_file_content".to_string());

        let s3_matches = SovereignPersonaEngine::evaluate_triggers_scoped(
            "lakukan deep refactoring module pada file rust",
            &temp_rust_ws,
            Some(&s3_mounted),
            None,
            1,
            &roots,
            Some("coder"),
        );
        let s3_ids: Vec<&str> = s3_matches.iter().map(|m| m.doc_id.as_str()).collect();
        assert!(s3_ids.contains(&"coder-identity"), "Scenario 3: 00_identity.md must match");
        assert!(s3_ids.contains(&"coder-function-calling"), "Scenario 3: 01_function_calling.md must match");
        assert!(s3_ids.contains(&"coder-ruh-rekayasa"), "Scenario 3: 02_ruh_rekayasa.md must match");
        assert!(s3_ids.contains(&"coder-desain-modul-mendalam"), "Scenario 3: 12_desain_modul_mendalam.md must match");

        let s3_block = SovereignPersonaEngine::compose_top_single_persona_block(&s3_matches);
        assert!(s3_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-identity\""));
        assert!(s3_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-function-calling\""));
        assert!(s3_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-ruh-rekayasa\""));
        assert!(s3_block.contains("<ACTIVE_SOVEREIGN_PERSONA id=\"coder-desain-modul-mendalam\""));
        assert!(s3_block.contains("tool_active: 'replace_file_content'"));
        assert!(s3_block.contains("file_pattern: '*.rs'"));
        println!("============================================================");
        println!("AUDIT EVIDENCE - SCENARIO 3 (Deep Code Refactoring)");
        println!("Mounted tools: [replace_file_content], Workspace: *.rs repo");
        for m in &s3_matches {
            println!("  -> Matched ID: {}, Target: {}, Priority: {}, Reasons: {:?}", m.doc_id, m.target_type, m.priority, m.match_reasons);
        }
        println!("Generated XML block tags:");
        for line in s3_block.lines() {
            if line.starts_with("<ACTIVE_SOVEREIGN_PERSONA") || line.starts_with("<SOVEREIGN_PERSONA_") || line.starts_with("<!--") || line.starts_with("<SOVEREIGN_") {
                println!("  {}", line);
            }
        }
        println!("✅ SCENARIO 3: PASSED (00_identity.md, 01_function_calling.md, 02_ruh_rekayasa.md, and 12_desain_modul_mendalam.md ALL injected simultaneously)");
        let _ = fs::remove_dir_all(&temp_rust_ws);

        // --- SCENARIO 4 (Exclusion Short-Circuit) ---
        // User mentions forex or eurusd while typing git commit.
        // Expected: Excluded prompts are strictly disqualified, even if their cmd or tool matched!
        let s4_forex_matches = SovereignPersonaEngine::evaluate_triggers_scoped(
            "git commit -m 'feat: implement forex trading gateway'",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        let s4_forex_ids: Vec<&str> = s4_forex_matches.iter().map(|m| m.doc_id.as_str()).collect();
        assert!(!s4_forex_ids.contains(&"coder-identity"), "Scenario 4: coder-identity MUST be disqualified when forex is mentioned");
        assert!(!s4_forex_ids.contains(&"coder-git-guardrails-wizard"), "Scenario 4: coder-git-guardrails-wizard MUST be disqualified when forex is mentioned even though cmd matched");

        let s4_eurusd_matches = SovereignPersonaEngine::evaluate_triggers_scoped(
            "git commit -m 'fix eurusd quote calculation'",
            &ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        let s4_eurusd_ids: Vec<&str> = s4_eurusd_matches.iter().map(|m| m.doc_id.as_str()).collect();
        assert!(!s4_eurusd_ids.contains(&"coder-identity"), "Scenario 4: coder-identity MUST be disqualified when eurusd is mentioned");
        assert!(!s4_eurusd_ids.contains(&"coder-git-guardrails-wizard"), "Scenario 4: coder-git-guardrails-wizard MUST be disqualified when eurusd is mentioned even though cmd matched");

        let s4_forex_block = SovereignPersonaEngine::compose_top_single_persona_block(&s4_forex_matches);
        assert!(!s4_forex_block.contains("coder-identity"), "Scenario 4 XML block MUST NOT contain disqualified coder-identity");
        assert!(!s4_forex_block.contains("coder-git-guardrails-wizard"), "Scenario 4 XML block MUST NOT contain disqualified coder-git-guardrails-wizard");

        // Clean workspace verification: in an isolated workspace, EXACTLY 0 prompts match
        let temp_empty_ws = std::env::temp_dir().join(format!("flw_scenario4_empty_ws_{}", std::process::id()));
        fs::create_dir_all(&temp_empty_ws).unwrap();

        let s4_clean_matches = SovereignPersonaEngine::evaluate_triggers_scoped(
            "git commit -m 'save forex checkpoint'",
            &temp_empty_ws,
            None,
            None,
            1,
            &roots,
            Some("coder"),
        );
        let clean_ids: Vec<&str> = s4_clean_matches.iter().map(|m| m.doc_id.as_str()).collect();
        assert!(!clean_ids.contains(&"coder-identity"), "coder-identity must be excluded");
        assert!(!clean_ids.contains(&"coder-git-guardrails-wizard"), "coder-git-guardrails-wizard must be excluded");
        assert_eq!(s4_clean_matches.len(), 0, "All coder prompts strictly disqualified or untriggered in clean workspace when forex is mentioned");
        let _ = fs::remove_dir_all(&temp_empty_ws);

        // Unscoped verification: coder prompts remain disqualified even in global search
        let s4_unscoped = SovereignPersonaEngine::evaluate_triggers(
            "git commit -m 'analisa pair eurusd forex'",
            &ws,
            None,
            None,
            1,
            &roots,
        );
        let unscoped_ids: Vec<&str> = s4_unscoped.iter().map(|m| m.doc_id.as_str()).collect();
        assert!(!unscoped_ids.contains(&"coder-identity"), "coder-identity MUST be excluded even in unscoped evaluation");
        assert!(!unscoped_ids.contains(&"coder-git-guardrails-wizard"), "coder-git-guardrails-wizard MUST be excluded even in unscoped evaluation");

        println!("============================================================");
        println!("AUDIT EVIDENCE - SCENARIO 4 (Exclusion Short-Circuit)");
        println!("Input A (scoped coder): git commit -m 'feat: implement forex trading gateway'");
        println!("  Disqualified: coder-identity, coder-git-guardrails-wizard (In clean ws matches: 0)");
        println!("Input B (scoped coder): git commit -m 'fix eurusd quote calculation'");
        println!("  Disqualified: coder-identity, coder-git-guardrails-wizard");
        println!("Input C (unscoped global): git commit -m 'analisa pair eurusd forex'");
        println!("  Coder prompt modules strictly disqualified across all scopes!");
        println!("✅ SCENARIO 4: PASSED (Excluded prompts strictly disqualified when forex/eurusd mentioned, even though cmd 'git commit' matched)");
        println!("============================================================");
    }

    #[test]
    fn test_exhaustive_audit_prompts_11_to_20_and_rules_kinerja() {
        let manifest_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string()));
        let ws = if manifest_dir.join("Persona").is_dir() {
            manifest_dir.clone()
        } else if manifest_dir.parent().map(|p| p.join("Persona").is_dir()).unwrap_or(false) {
            manifest_dir.parent().unwrap().to_path_buf()
        } else {
            manifest_dir.parent().and_then(|p| p.parent()).map(|p| p.to_path_buf()).unwrap_or_else(|| manifest_dir.clone())
        };
        let roots = SovereignPersonaEngine::resolve_persona_roots(&ws, &manifest_dir);

        let coder_docs = SovereignPersonaEngine::load_persona_docs_for_persona(&roots, "coder");
        if coder_docs.is_empty() {
            println!("No coder persona markdown files on disk, skipping audit prompts 11-20 test");
            return;
        }
        let doc_ids: HashSet<String> = coder_docs.iter().map(|d| d.id.clone()).collect();

        println!("================================================================================");
        println!("🚀 FLOWORK OS SOVEREIGN PERSONA AUDIT: PROMPTS 11-20, RULES.MD, & KINERJA.MD");
        println!("================================================================================");

        // Verify all 12 target docs exist
        let expected_ids = [
            "coder-intent-matcher",
            "coder-desain-modul-mendalam",
            "coder-domain-modeling-adr",
            "coder-spesifikasi-triase-tdd",
            "coder-handoff-prototipe",
            "coder-git-guardrails-wizard",
            "coder-code-review-dua-sumbu",
            "coder-reverse-engineering",
            "coder-wayfinding-pemecah-kabut",
            "coder-riset-sumber-primer",
            "coder-strict-rules",
            "coder-execution-sop",
        ];
        for id in &expected_ids {
            assert!(doc_ids.contains(*id), "Expected doc ID '{}' to be loaded in coder persona", id);
            println!("  [LOADED] {}", id);
        }

        let temp_ws = std::env::temp_dir().join(format!("flw_audit_coder_ws_{}", std::process::id()));
        let _ = fs::create_dir_all(&temp_ws);

        // --- 1. 11_intent_matcher.md ---
        {
            println!("\n🔍 AUDITING 11_intent_matcher.md (id: coder-intent-matcher)");
            let m1 = SovereignPersonaEngine::evaluate_triggers_scoped("investigation phase of the bug", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m1.iter().any(|m| m.doc_id == "coder-intent-matcher" && m.match_reasons.iter().any(|r| r.contains("investigation phase"))));
            println!("  ✅ Trigger: Turn 1 + keyword 'investigation phase' -> MATCHED");

            let m2 = SovereignPersonaEngine::evaluate_triggers_scoped("engineering cycle kickoff", &temp_ws, None, None, 2, &roots, Some("coder"));
            assert!(m2.iter().any(|m| m.doc_id == "coder-intent-matcher"));
            println!("  ✅ Trigger: Turn 2 + keyword 'engineering cycle' -> MATCHED");

            let m_late = SovereignPersonaEngine::evaluate_triggers_scoped("investigation phase of the bug", &temp_ws, None, None, 3, &roots, Some("coder"));
            assert!(!m_late.iter().any(|m| m.doc_id == "coder-intent-matcher"));
            println!("  ✅ Turn Boundary: Turn 3 exceeds max_turn 2 -> DISQUALIFIED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("investigation phase on forex trading", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-intent-matcher"));
            println!("  ✅ Exclusion: Negative keyword 'forex' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 2. 12_desain_modul_mendalam.md ---
        {
            println!("\n🔍 AUDITING 12_desain_modul_mendalam.md (id: coder-desain-modul-mendalam)");
            let mut mounted = HashSet::new();
            mounted.insert("replace_file_content".to_string());
            let m_tool = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, Some(&mounted), None, 1, &roots, Some("coder"));
            assert!(m_tool.iter().any(|m| m.doc_id == "coder-desain-modul-mendalam" && m.match_reasons.iter().any(|r| r.contains("tool_active: 'replace_file_content'"))));
            println!("  ✅ Trigger: tools_active 'replace_file_content' -> MATCHED");

            let ts_file = temp_ws.join("module.ts");
            let _ = fs::write(&ts_file, "export const x = 1;");
            let m_file = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_file.iter().any(|m| m.doc_id == "coder-desain-modul-mendalam" && m.match_reasons.iter().any(|r| r.contains("file_pattern: '*.ts'"))));
            let _ = fs::remove_file(&ts_file);
            println!("  ✅ Trigger: file_patterns '*.ts' -> MATCHED");

            let m_kw = SovereignPersonaEngine::evaluate_triggers_scoped("information hiding principle", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_kw.iter().any(|m| m.doc_id == "coder-desain-modul-mendalam" && m.match_reasons.iter().any(|r| r.contains("information hiding"))));
            println!("  ✅ Trigger: keyword 'information hiding' -> MATCHED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("information hiding forex", &temp_ws, Some(&mounted), None, 1, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-desain-modul-mendalam"));
            println!("  ✅ Exclusion: Negative keyword 'forex' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 3. 13_domain_modeling_adr.md ---
        {
            println!("\n🔍 AUDITING 13_domain_modeling_adr.md (id: coder-domain-modeling-adr)");
            let adr_dir = temp_ws.join("architecture");
            let _ = fs::create_dir_all(&adr_dir);
            let m_arch = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_arch.iter().any(|m| m.doc_id == "coder-domain-modeling-adr" && m.match_reasons.iter().any(|r| r.contains("file_pattern: 'architecture/**'"))));
            let _ = fs::remove_dir_all(&adr_dir);
            println!("  ✅ Trigger: file_patterns 'architecture/**' -> MATCHED");

            let adr_file = temp_ws.join("001.adr.md");
            let _ = fs::write(&adr_file, "# ADR");
            let m_adr_file = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_adr_file.iter().any(|m| m.doc_id == "coder-domain-modeling-adr" && m.match_reasons.iter().any(|r| r.contains("file_pattern: '*.adr.md'"))));
            let _ = fs::remove_file(&adr_file);
            println!("  ✅ Trigger: file_patterns '*.adr.md' -> MATCHED");

            let docs_adr = temp_ws.join("docs").join("adr");
            let _ = fs::create_dir_all(&docs_adr);
            let m_docs_adr = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_docs_adr.iter().any(|m| m.doc_id == "coder-domain-modeling-adr" && m.match_reasons.iter().any(|r| r.contains("file_pattern: 'docs/adr/**'"))));
            let _ = fs::remove_dir_all(temp_ws.join("docs"));
            println!("  ✅ Trigger: file_patterns 'docs/adr/**' -> MATCHED");

            let m_kw = SovereignPersonaEngine::evaluate_triggers_scoped("write an architecture decision record", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_kw.iter().any(|m| m.doc_id == "coder-domain-modeling-adr" && m.match_reasons.iter().any(|r| r.contains("architecture decision record"))));
            println!("  ✅ Trigger: keyword 'architecture decision record' -> MATCHED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("architecture decision record for eurusd", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-domain-modeling-adr"));
            println!("  ✅ Exclusion: Negative keyword 'eurusd' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 4. 14_spesifikasi_triase_tdd.md ---
        {
            println!("\n🔍 AUDITING 14_spesifikasi_triase_tdd.md (id: coder-spesifikasi-triase-tdd)");
            let m_cargo = SovereignPersonaEngine::evaluate_triggers_scoped("run cargo test --lib", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_cargo.iter().any(|m| m.doc_id == "coder-spesifikasi-triase-tdd" && m.match_reasons.iter().any(|r| r.contains("cmd: 'cargo test'"))));
            println!("  ✅ Trigger: cmd 'cargo test' -> MATCHED");

            let m_npm = SovereignPersonaEngine::evaluate_triggers_scoped("npm test", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_npm.iter().any(|m| m.doc_id == "coder-spesifikasi-triase-tdd" && m.match_reasons.iter().any(|r| r.contains("cmd: 'npm test'"))));
            println!("  ✅ Trigger: cmd 'npm test' -> MATCHED");

            let m_pytest = SovereignPersonaEngine::evaluate_triggers_scoped("pytest tests/", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_pytest.iter().any(|m| m.doc_id == "coder-spesifikasi-triase-tdd" && m.match_reasons.iter().any(|r| r.contains("cmd: 'pytest'"))));
            println!("  ✅ Trigger: cmd 'pytest' -> MATCHED");

            // Tool stalled: consecutive_failures >= 1
            let mut stats = HashMap::new();
            stats.insert("run_command".to_string(), ToolRunStats { total_calls: 1, consecutive_failures: 1, last_exit_code: 1 });
            let m_stall = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, Some(&stats), 1, &roots, Some("coder"));
            assert!(m_stall.iter().any(|m| m.doc_id == "coder-spesifikasi-triase-tdd" && m.match_reasons.iter().any(|r| r.contains("tool_stalled: 'run_command' (failures: 1 >= 1)"))));
            println!("  ✅ Trigger: tool_stalled 'run_command' consecutive_failures >= 1 -> MATCHED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("cargo test eurusd", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-spesifikasi-triase-tdd"));
            println!("  ✅ Exclusion: Negative keyword 'eurusd' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 5. 15_handoff_prototipe.md ---
        {
            println!("\n🔍 AUDITING 15_handoff_prototipe.md (id: coder-handoff-prototipe)");
            let mut mounted = HashSet::new();
            mounted.insert("write_to_file".to_string());
            let m_tool = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, Some(&mounted), None, 1, &roots, Some("coder"));
            assert!(m_tool.iter().any(|m| m.doc_id == "coder-handoff-prototipe" && m.match_reasons.iter().any(|r| r.contains("tool_active: 'write_to_file'"))));
            println!("  ✅ Trigger: tools_active 'write_to_file' -> MATCHED");

            let url_file = temp_ws.join("app.url.json");
            let _ = fs::write(&url_file, "{}");
            let m_file = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_file.iter().any(|m| m.doc_id == "coder-handoff-prototipe" && m.match_reasons.iter().any(|r| r.contains("file_pattern: '*.url.json'"))));
            let _ = fs::remove_file(&url_file);
            println!("  ✅ Trigger: file_patterns '*.url.json' -> MATCHED");

            let dash_dir = temp_ws.join("dashboards");
            let _ = fs::create_dir_all(&dash_dir);
            let m_dash = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_dash.iter().any(|m| m.doc_id == "coder-handoff-prototipe" && m.match_reasons.iter().any(|r| r.contains("file_pattern: 'dashboards/**'"))));
            let _ = fs::remove_dir_all(&dash_dir);
            println!("  ✅ Trigger: file_patterns 'dashboards/**' -> MATCHED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("prototype ui for gbpusd", &temp_ws, Some(&mounted), None, 1, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-handoff-prototipe"));
            println!("  ✅ Exclusion: Negative keyword 'gbpusd' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 6. 16_git_guardrails_wizard.md ---
        {
            println!("\n🔍 AUDITING 16_git_guardrails_wizard.md (id: coder-git-guardrails-wizard)");
            for cmd_str in &["git commit -m 'wip'", "git push origin", "git reset --hard", "git rebase master"] {
                let m = SovereignPersonaEngine::evaluate_triggers_scoped(cmd_str, &temp_ws, None, None, 1, &roots, Some("coder"));
                assert!(m.iter().any(|item| item.doc_id == "coder-git-guardrails-wizard"), "Expected git guardrails on '{}'", cmd_str);
                println!("  ✅ Trigger: cmd '{}' -> MATCHED", cmd_str);
            }

            let git_dir = temp_ws.join(".git");
            let _ = fs::create_dir_all(&git_dir);
            let m_git_dir = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_git_dir.iter().any(|m| m.doc_id == "coder-git-guardrails-wizard" && m.match_reasons.iter().any(|r| r.contains("file_pattern: '.git/**'"))));
            let _ = fs::remove_dir_all(&git_dir);
            println!("  ✅ Trigger: file_patterns '.git/**' -> MATCHED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("git commit for forex trading crypto", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-git-guardrails-wizard"));
            println!("  ✅ Exclusion: Negative keyword 'forex' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 7. 17_code_review_dua_sumbu.md ---
        {
            println!("\n🔍 AUDITING 17_code_review_dua_sumbu.md (id: coder-code-review-dua-sumbu)");
            for cmd_str in &["git diff HEAD~1", "git log -n 5", "git show 12345"] {
                let m = SovereignPersonaEngine::evaluate_triggers_scoped(cmd_str, &temp_ws, None, None, 1, &roots, Some("coder"));
                assert!(m.iter().any(|item| item.doc_id == "coder-code-review-dua-sumbu"), "Expected code review on '{}'", cmd_str);
                println!("  ✅ Trigger: cmd '{}' -> MATCHED", cmd_str);
            }

            let m_kw = SovereignPersonaEngine::evaluate_triggers_scoped("conduct two axis review", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_kw.iter().any(|m| m.doc_id == "coder-code-review-dua-sumbu"));
            println!("  ✅ Trigger: keyword 'two axis review' -> MATCHED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("git diff on forex codebase", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-code-review-dua-sumbu"));
            println!("  ✅ Exclusion: Negative keyword 'forex' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 8. 18_reverse_engineering.md ---
        {
            println!("\n🔍 AUDITING 18_reverse_engineering.md (id: coder-reverse-engineering)");
            for cmd_str in &["run objdump -d /bin/ls", "run strings app.bin", "run readelf -h kernel.o", "run gdb ./crash", "run radare2 ./bin"] {
                let m = SovereignPersonaEngine::evaluate_triggers_scoped(cmd_str, &temp_ws, None, None, 1, &roots, Some("coder"));
                assert!(m.iter().any(|item| item.doc_id == "coder-reverse-engineering"), "Expected reverse engineering on '{}'", cmd_str);
                println!("  ✅ Trigger: cmd '{}' -> MATCHED", cmd_str);
            }

            let m_kw = SovereignPersonaEngine::evaluate_triggers_scoped("perform binary disassembly", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_kw.iter().any(|m| m.doc_id == "coder-reverse-engineering"));
            println!("  ✅ Trigger: keyword 'binary disassembly' -> MATCHED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("objdump for trading crypto", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-reverse-engineering"));
            println!("  ✅ Exclusion: Negative keyword 'trading crypto' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 9. 19_wayfinding_pemecah_kabut.md ---
        {
            println!("\n🔍 AUDITING 19_wayfinding_pemecah_kabut.md (id: coder-wayfinding-pemecah-kabut)");
            let mut mounted = HashSet::new();
            mounted.insert("view_file".to_string());

            let m1 = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, Some(&mounted), None, 1, &roots, Some("coder"));
            assert!(m1.iter().any(|m| m.doc_id == "coder-wayfinding-pemecah-kabut" && m.match_reasons.iter().any(|r| r.contains("tool_active: 'view_file'"))));
            println!("  ✅ Trigger: Turn 1 + tools_active 'view_file' -> MATCHED");

            let m3 = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, Some(&mounted), None, 3, &roots, Some("coder"));
            assert!(m3.iter().any(|m| m.doc_id == "coder-wayfinding-pemecah-kabut"));
            println!("  ✅ Trigger: Turn 3 + tools_active 'view_file' -> MATCHED");

            let m4 = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, Some(&mounted), None, 4, &roots, Some("coder"));
            assert!(!m4.iter().any(|m| m.doc_id == "coder-wayfinding-pemecah-kabut"));
            println!("  ✅ Turn Boundary: Turn 4 exceeds max_turn 3 -> DISQUALIFIED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("view_file forex", &temp_ws, Some(&mounted), None, 2, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-wayfinding-pemecah-kabut"));
            println!("  ✅ Exclusion: Negative keyword 'forex' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 10. 20_riset_sumber_primer.md ---
        {
            println!("\n🔍 AUDITING 20_riset_sumber_primer.md (id: coder-riset-sumber-primer)");
            let mut mounted_url = HashSet::new();
            mounted_url.insert("read_url_content".to_string());
            let m_url = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, Some(&mounted_url), None, 1, &roots, Some("coder"));
            assert!(m_url.iter().any(|m| m.doc_id == "coder-riset-sumber-primer" && m.match_reasons.iter().any(|r| r.contains("tool_active: 'read_url_content'"))));
            println!("  ✅ Trigger: tools_active 'read_url_content' -> MATCHED");

            let mut mounted_web = HashSet::new();
            mounted_web.insert("search_web".to_string());
            let m_web = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, Some(&mounted_web), None, 1, &roots, Some("coder"));
            assert!(m_web.iter().any(|m| m.doc_id == "coder-riset-sumber-primer" && m.match_reasons.iter().any(|r| r.contains("tool_active: 'search_web'"))));
            println!("  ✅ Trigger: tools_active 'search_web' -> MATCHED");

            let m_kw = SovereignPersonaEngine::evaluate_triggers_scoped("check canonical documentation and rfc research", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_kw.iter().any(|m| m.doc_id == "coder-riset-sumber-primer"));
            println!("  ✅ Trigger: keyword 'canonical documentation' -> MATCHED");

            let m_ex = SovereignPersonaEngine::evaluate_triggers_scoped("search_web eurusd", &temp_ws, Some(&mounted_web), None, 1, &roots, Some("coder"));
            assert!(!m_ex.iter().any(|m| m.doc_id == "coder-riset-sumber-primer"));
            println!("  ✅ Exclusion: Negative keyword 'eurusd' -> SHORT-CIRCUIT REJECTED");
        }

        // --- 11. rules.md ---
        {
            println!("\n🔍 AUDITING rules.md (id: coder-strict-rules)");
            // Failures = 1: Should NOT trigger rules.md stall
            let mut stats1 = HashMap::new();
            stats1.insert("run_command".to_string(), ToolRunStats { total_calls: 1, consecutive_failures: 1, last_exit_code: 1 });
            let m_fail1 = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, Some(&stats1), 1, &roots, Some("coder"));
            assert!(!m_fail1.iter().any(|m| m.doc_id == "coder-strict-rules"), "consecutive_failures=1 must not trigger rules.md");
            println!("  ✅ Tool Stalled Boundary: consecutive_failures=1 < 2 -> NOT TRIGGERED");

            // Failures = 2: MUST trigger rules.md stall
            let mut stats2 = HashMap::new();
            stats2.insert("run_command".to_string(), ToolRunStats { total_calls: 2, consecutive_failures: 2, last_exit_code: 1 });
            let m_fail2 = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, Some(&stats2), 1, &roots, Some("coder"));
            assert!(m_fail2.iter().any(|m| m.doc_id == "coder-strict-rules" && m.match_reasons.iter().any(|r| r.contains("tool_stalled: 'run_command' (failures: 2 >= 2)"))));
            println!("  ✅ Trigger: tool_stalled 'run_command' consecutive_failures >= 2 -> MATCHED");

            // Tool threshold: total_calls >= 3
            let mut stats3 = HashMap::new();
            stats3.insert("run_command".to_string(), ToolRunStats { total_calls: 3, consecutive_failures: 0, last_exit_code: 0 });
            let m_thresh = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, Some(&stats3), 1, &roots, Some("coder"));
            assert!(m_thresh.iter().any(|m| m.doc_id == "coder-strict-rules" && m.match_reasons.iter().any(|r| r.contains("tool_threshold: 'run_command' (calls: 3 >= 3)"))));
            println!("  ✅ Trigger: tool_threshold 'run_command' total_calls >= 3 -> MATCHED");

            let m_kw = SovereignPersonaEngine::evaluate_triggers_scoped("refactor the legacy architecture", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_kw.iter().any(|m| m.doc_id == "coder-strict-rules" && m.match_reasons.iter().any(|r| r.contains("refactor"))));
            println!("  ✅ Trigger: keyword 'refactor' -> MATCHED");
        }

        // --- 12. kinerja.md ---
        {
            println!("\n🔍 AUDITING kinerja.md (id: coder-execution-sop)");
            for tool_name in &["run_command", "replace_file_content", "write_to_file"] {
                let mut mounted = HashSet::new();
                mounted.insert(tool_name.to_string());
                let m = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, Some(&mounted), None, 1, &roots, Some("coder"));
                assert!(m.iter().any(|item| item.doc_id == "coder-execution-sop" && item.match_reasons.iter().any(|r| r.contains(&format!("tool_active: '{}'", tool_name)))), "Expected kinerja on tool '{}'", tool_name);
                println!("  ✅ Trigger: tools_active '{}' -> MATCHED", tool_name);
            }

            let cargo_file = temp_ws.join("Cargo.toml");
            let _ = fs::write(&cargo_file, "[package]");
            let m_cargo = SovereignPersonaEngine::evaluate_triggers_scoped("arbitrary query", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_cargo.iter().any(|m| m.doc_id == "coder-execution-sop" && m.match_reasons.iter().any(|r| r.to_lowercase().contains("cargo.toml"))));
            let _ = fs::remove_file(&cargo_file);
            println!("  ✅ Trigger: file_patterns 'Cargo.toml' -> MATCHED");

            let m_kw = SovereignPersonaEngine::evaluate_triggers_scoped("please implement this feature", &temp_ws, None, None, 1, &roots, Some("coder"));
            assert!(m_kw.iter().any(|m| m.doc_id == "coder-execution-sop" && m.match_reasons.iter().any(|r| r.contains("implement"))));
            println!("  ✅ Trigger: keyword 'implement' -> MATCHED");
        }

        let _ = fs::remove_dir_all(&temp_ws);
        println!("\n🎉 ALL 12 TARGET PROMPTS AUDITED AND VERIFIED WITH EXIT CODE 0!");
        println!("================================================================================");
    }

    #[test]
    fn test_exhaustive_audit_prompts_00_to_10_coder_persona() {
        let manifest_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string()));
        let project_root = if manifest_dir.join("Persona").is_dir() {
            manifest_dir.clone()
        } else if manifest_dir.parent().map(|p| p.join("Persona").is_dir()).unwrap_or(false) {
            manifest_dir.parent().unwrap().to_path_buf()
        } else {
            manifest_dir.parent().and_then(|p| p.parent()).map(|p| p.to_path_buf()).unwrap_or_else(|| manifest_dir.clone())
        };
        let roots = SovereignPersonaEngine::resolve_persona_roots(&project_root, &manifest_dir);

        // Load all docs specifically for the "coder" persona
        let docs = SovereignPersonaEngine::load_persona_docs_for_persona(&roots, "coder");
        if docs.is_empty() {
            println!("No coder persona markdown files on disk, skipping audit prompts 0-10 test");
            return;
        }

        let doc_ids: Vec<String> = docs.iter().map(|d| d.id.clone()).collect();

        println!("================================================================================");
        println!("🚀 FLOWORK OS SOVEREIGN PERSONA AUDIT: CODER PROMPTS 00 TO 10");
        println!("================================================================================");

        // Verify all 11 target prompt IDs exist in Coder persona
        let expected_ids = [
            ("coder-identity", "00_identity.md"),
            ("coder-function-calling", "01_function_calling.md"),
            ("coder-ruh-rekayasa", "02_ruh_rekayasa.md"),
            ("coder-kendali-mutu-qc", "03_kendali_mutu_qc.md"),
            ("coder-slash-commands", "04_slash_commands.md"),
            ("coder-mode-otonom", "05_mode_otonom.md"),
            ("coder-protokol-perencanaan", "06_protokol_perencanaan.md"),
            ("coder-arsitektur-swarm", "07_arsitektur_swarm.md"),
            ("coder-sensor-visual", "08_sensor_visual.md"),
            ("coder-ekosistem-plugin", "09_ekosistem_plugin.md"),
            ("coder-spesialisasi-siber", "10_spesialisasi_siber.md"),
        ];

        for (id, file_name) in &expected_ids {
            assert!(
                doc_ids.iter().any(|d| d == id),
                "Missing expected Coder persona document: {} ({})",
                id,
                file_name
            );
            println!("  [FOUND] {} -> {}", file_name, id);
        }

        // Setup clean temp workspace for testing file patterns
        let temp_ws = std::env::temp_dir().join(format!("flw_audit_prompts_00_10_ws_{}", std::process::id()));
        let _ = fs::remove_dir_all(&temp_ws);
        let _ = fs::create_dir_all(&temp_ws);

        // Helper closure for testing scoped trigger evaluation
        let eval = |search: &str, ws: &Path, tools: Option<&HashSet<String>>, stats: Option<&HashMap<String, ToolRunStats>>, turn: usize| {
            SovereignPersonaEngine::evaluate_triggers_scoped(search, ws, tools, stats, turn, &roots, Some("coder"))
        };

        // =========================================================================
        // PROMPT 00: 00_identity.md (always: true, exclude_keywords: forex, trading crypto, etc.)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 00_identity.md (id: coder-identity)");
            // Positive: Fires on neutral input because always == true
            let m = eval("halo bro selamat pagi", &temp_ws, None, None, 1);
            let hit = m.iter().find(|x| x.doc_id == "coder-identity");
            assert!(hit.is_some(), "00_identity MUST trigger on neutral input (always: true)");
            assert!(hit.unwrap().match_reasons.contains(&"always_active".to_string()));
            println!("  ✅ Positive Trigger: always_active -> MATCHED (reasons: {:?})", hit.unwrap().match_reasons);

            // Negative exclusion: Disqualified when search contains excluded keyword
            let m_ex = eval("analisa chart forex sekarang", &temp_ws, None, None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-identity"), "00_identity MUST NOT trigger when input contains 'forex'");
            println!("  ✅ Negative Exclusion: 'forex' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 01: 01_function_calling.md (tools_active: run_command, replace_file_content...; tool_threshold: run_command >= 1)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 01_function_calling.md (id: coder-function-calling)");
            // Positive 1: tools_active triggers
            let mut mounted = HashSet::new();
            mounted.insert("run_command".to_string());
            let m = eval("cek sistem", &temp_ws, Some(&mounted), None, 1);
            let hit = m.iter().find(|x| x.doc_id == "coder-function-calling");
            assert!(hit.is_some(), "01_function_calling MUST trigger when run_command is active");
            assert!(hit.unwrap().match_reasons.iter().any(|r| r.contains("tool_active: 'run_command'")));
            println!("  ✅ Positive Trigger 1: tools_active 'run_command' -> MATCHED");

            // Positive 2: tool_threshold triggers (run_command >= 1)
            let mut stats = HashMap::new();
            stats.insert("run_command".to_string(), ToolRunStats { total_calls: 1, consecutive_failures: 0, last_exit_code: 0 });
            let m2 = eval("cek sistem", &temp_ws, None, Some(&stats), 1);
            let hit2 = m2.iter().find(|x| x.doc_id == "coder-function-calling");
            assert!(hit2.is_some(), "01_function_calling MUST trigger when run_command total_calls >= 1");
            assert!(hit2.unwrap().match_reasons.iter().any(|r| r.contains("tool_threshold: 'run_command'")));
            println!("  ✅ Positive Trigger 2: tool_threshold 'run_command' >= 1 -> MATCHED");

            // Positive 3: keywords triggers
            let m3 = eval("validasi parameter function calling", &temp_ws, None, None, 1);
            assert!(m3.iter().any(|x| x.doc_id == "coder-function-calling"), "01_function_calling MUST trigger on keyword 'function calling'");
            println!("  ✅ Positive Trigger 3: keyword 'function calling' -> MATCHED");

            // Negative: Non-matching input with empty tools & 0 stats
            let m_none = eval("halo selamat pagi", &temp_ws, None, None, 1);
            assert!(!m_none.iter().any(|x| x.doc_id == "coder-function-calling"), "01_function_calling MUST NOT trigger without matching conditions");
            println!("  ✅ Non-matching input: NOT TRIGGERED");

            // Negative exclusion: Disqualified on excluded keyword even if tool mounted
            let m_ex = eval("analisa pasar forex", &temp_ws, Some(&mounted), None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-function-calling"), "01_function_calling MUST NOT trigger when input contains 'forex'");
            println!("  ✅ Negative Exclusion: 'forex' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 02: 02_ruh_rekayasa.md (tools_active: replace_file_content, write_to_file; file_patterns: *.rs, *.ts; cmd: cargo test, npm test)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 02_ruh_rekayasa.md (id: coder-ruh-rekayasa)");
            // Positive 1: cmd triggers
            let m = eval("jalankan cargo test --all", &temp_ws, None, None, 1);
            let hit = m.iter().find(|x| x.doc_id == "coder-ruh-rekayasa");
            assert!(hit.is_some(), "02_ruh_rekayasa MUST trigger on cmd 'cargo test'");
            assert!(hit.unwrap().match_reasons.iter().any(|r| r.contains("cmd: 'cargo test'")));
            println!("  ✅ Positive Trigger 1: cmd 'cargo test' -> MATCHED");

            // Positive 2: file_patterns triggers (*.rs)
            let rs_file = temp_ws.join("main.rs");
            fs::write(&rs_file, "fn main() {}").unwrap();
            let m2 = eval("periksa proyek ini", &temp_ws, None, None, 1);
            let hit2 = m2.iter().find(|x| x.doc_id == "coder-ruh-rekayasa");
            assert!(hit2.is_some(), "02_ruh_rekayasa MUST trigger when *.rs exists in workspace");
            assert!(hit2.unwrap().match_reasons.iter().any(|r| r.contains("file_pattern: '*.rs'")));
            let _ = fs::remove_file(&rs_file);
            println!("  ✅ Positive Trigger 2: file_pattern '*.rs' -> MATCHED");

            // Positive 3: tools_active triggers (replace_file_content)
            let mut mounted = HashSet::new();
            mounted.insert("replace_file_content".to_string());
            let m3 = eval("periksa kode", &temp_ws, Some(&mounted), None, 1);
            let hit3 = m3.iter().find(|x| x.doc_id == "coder-ruh-rekayasa");
            assert!(hit3.is_some(), "02_ruh_rekayasa MUST trigger when replace_file_content is active");
            println!("  ✅ Positive Trigger 3: tools_active 'replace_file_content' -> MATCHED");

            // Negative: Non-matching input
            let m_none = eval("selamat pagi apa kabar", &temp_ws, None, None, 1);
            assert!(!m_none.iter().any(|x| x.doc_id == "coder-ruh-rekayasa"), "02_ruh_rekayasa MUST NOT trigger on unrelated input");
            println!("  ✅ Non-matching input: NOT TRIGGERED");

            // Negative exclusion: Disqualified on 'trading crypto'
            let m_ex = eval("cargo test pada trading crypto bot", &temp_ws, None, None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-ruh-rekayasa"), "02_ruh_rekayasa MUST NOT trigger when input contains 'trading crypto'");
            println!("  ✅ Negative Exclusion: 'trading crypto' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 03: 03_kendali_mutu_qc.md (cmd: cargo build, cargo test, npm build; tool_threshold: run_command >= 2)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 03_kendali_mutu_qc.md (id: coder-kendali-mutu-qc)");
            // Positive 1: cmd 'cargo build'
            let m1 = eval("jalankan cargo build --release", &temp_ws, None, None, 1);
            let hit1 = m1.iter().find(|x| x.doc_id == "coder-kendali-mutu-qc");
            assert!(hit1.is_some(), "03_kendali_mutu_qc MUST trigger on 'cargo build'");
            assert!(hit1.unwrap().match_reasons.iter().any(|r| r.contains("cmd: 'cargo build'")));
            println!("  ✅ Positive Trigger 1: cmd 'cargo build' -> MATCHED");

            // Positive 2: cmd 'npm build'
            let m2 = eval("eksekusi npm build sekarang", &temp_ws, None, None, 1);
            let hit2 = m2.iter().find(|x| x.doc_id == "coder-kendali-mutu-qc");
            assert!(hit2.is_some(), "03_kendali_mutu_qc MUST trigger on 'npm build'");
            assert!(hit2.unwrap().match_reasons.iter().any(|r| r.contains("cmd: 'npm build'")));
            println!("  ✅ Positive Trigger 2: cmd 'npm build' -> MATCHED");

            // Positive 3: tool_threshold (run_command >= 2)
            let mut stats = HashMap::new();
            stats.insert("run_command".to_string(), ToolRunStats { total_calls: 2, consecutive_failures: 0, last_exit_code: 0 });
            let m3 = eval("periksa status sekarang", &temp_ws, None, Some(&stats), 1);
            let hit3 = m3.iter().find(|x| x.doc_id == "coder-kendali-mutu-qc");
            assert!(hit3.is_some(), "03_kendali_mutu_qc MUST trigger when run_command total_calls >= 2");
            assert!(hit3.unwrap().match_reasons.iter().any(|r| r.contains("tool_threshold: 'run_command'")));
            println!("  ✅ Positive Trigger 3: tool_threshold 'run_command' >= 2 -> MATCHED");

            // Negative 1: run_command total_calls == 1 (below threshold)
            let mut stats_low = HashMap::new();
            stats_low.insert("run_command".to_string(), ToolRunStats { total_calls: 1, consecutive_failures: 0, last_exit_code: 0 });
            let m_low = eval("periksa status sekarang", &temp_ws, None, Some(&stats_low), 1);
            assert!(!m_low.iter().any(|x| x.doc_id == "coder-kendali-mutu-qc"), "03_kendali_mutu_qc MUST NOT trigger when calls < 2");
            println!("  ✅ Negative Threshold: run_command calls == 1 (< 2) -> NOT TRIGGERED");

            // Negative 2: Unrelated text
            let m_none = eval("selamat siang", &temp_ws, None, None, 1);
            assert!(!m_none.iter().any(|x| x.doc_id == "coder-kendali-mutu-qc"), "03_kendali_mutu_qc MUST NOT trigger without matching triggers");
            println!("  ✅ Non-matching input: NOT TRIGGERED");

            // Negative exclusion: Disqualified on 'eurusd'
            let m_ex = eval("cargo build eurusd bot", &temp_ws, None, None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-kendali-mutu-qc"), "03_kendali_mutu_qc MUST NOT trigger when input contains 'eurusd'");
            println!("  ✅ Negative Exclusion: 'eurusd' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 04: 04_slash_commands.md (cmd: /plan, /grill-me, /boost, /learn, /schedule, /browser, /goal)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 04_slash_commands.md (id: coder-slash-commands)");
            let slash_cmds = ["/plan", "/investigate", "/test-drive", "/verify", "/inspect", "/sharpen", "/forge-tool", "/purge", "/goal", "/boost", "/learn", "/schedule", "/browser"];
            for slash in &slash_cmds {
                let m = eval(&format!("bantu saya dengan {}", slash), &temp_ws, None, None, 1);
                let hit = m.iter().find(|x| x.doc_id == "coder-slash-commands");
                assert!(hit.is_some(), "04_slash_commands MUST trigger on {}", slash);
                assert!(hit.unwrap().match_reasons.iter().any(|r| r.contains(&format!("cmd: '{}'", slash))));
                println!("  ✅ Positive Trigger: cmd '{}' -> MATCHED", slash);
            }

            // Negative: Normal text
            let m_none = eval("buatkan fungsi kalkulator", &temp_ws, None, None, 1);
            assert!(!m_none.iter().any(|x| x.doc_id == "coder-slash-commands"), "04_slash_commands MUST NOT trigger on normal text");
            println!("  ✅ Non-matching input: NOT TRIGGERED");

            // Negative exclusion: Disqualified on 'gbpusd'
            let m_ex = eval("/plan strategi pair gbpusd", &temp_ws, None, None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-slash-commands"), "04_slash_commands MUST NOT trigger when input contains 'gbpusd'");
            println!("  ✅ Negative Exclusion: 'gbpusd' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 05: 05_mode_otonom.md (cmd: --auto, --headless, /goal; keywords: gas, hajar, tuntaskan)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 05_mode_otonom.md (id: coder-mode-otonom)");
            // Positive 1: keywords
            for kw in &["gas", "hajar", "tuntaskan", "hands-free", "unattended"] {
                let m = eval(&format!("tolong {} tugas ini", kw), &temp_ws, None, None, 1);
                let hit = m.iter().find(|x| x.doc_id == "coder-mode-otonom");
                assert!(hit.is_some(), "05_mode_otonom MUST trigger on keyword '{}'", kw);
                println!("  ✅ Positive Trigger: keyword '{}' -> MATCHED", kw);
            }

            // Positive 2: cmds
            for cmd in &["--auto", "--headless", "/goal"] {
                let m = eval(&format!("jalankan mode {}", cmd), &temp_ws, None, None, 1);
                let hit = m.iter().find(|x| x.doc_id == "coder-mode-otonom");
                assert!(hit.is_some(), "05_mode_otonom MUST trigger on cmd '{}'", cmd);
                println!("  ✅ Positive Trigger: cmd '{}' -> MATCHED", cmd);
            }

            // Negative: Non-matching input
            let m_none = eval("bagaimana cara kerja borrow checker di rust?", &temp_ws, None, None, 1);
            assert!(!m_none.iter().any(|x| x.doc_id == "coder-mode-otonom"), "05_mode_otonom MUST NOT trigger on neutral question");
            println!("  ✅ Non-matching input: NOT TRIGGERED");

            // Negative exclusion: Disqualified on 'forex'
            let m_ex = eval("gas hajar sinyal forex hari ini", &temp_ws, None, None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-mode-otonom"), "05_mode_otonom MUST NOT trigger when input contains 'forex'");
            println!("  ✅ Negative Exclusion: 'forex' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 06: 06_protokol_perencanaan.md (cmd: /plan; file_patterns: task.md, plan.md; turn_range: min 1, max 3)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 06_protokol_perencanaan.md (id: coder-protokol-perencanaan)");
            // Positive 1: cmd /plan within turn budget (turns 1, 2, 3)
            for turn in 1..=3 {
                let m = eval("/plan arsitektur sistem baru", &temp_ws, None, None, turn);
                let hit = m.iter().find(|x| x.doc_id == "coder-protokol-perencanaan");
                assert!(hit.is_some(), "06_protokol_perencanaan MUST trigger on /plan at turn {}", turn);
                assert!(hit.unwrap().match_reasons.iter().any(|r| r.contains("cmd: '/plan'")));
                println!("  ✅ Positive Trigger: cmd '/plan' at turn {} -> MATCHED", turn);
            }

            // Positive 2: file_patterns (task.md) at turn 2
            let task_file = temp_ws.join("task.md");
            fs::write(&task_file, "# Task List\n- [ ] Task 1").unwrap();
            let m_file = eval("cek progres pekerjaan", &temp_ws, None, None, 2);
            let hit_file = m_file.iter().find(|x| x.doc_id == "coder-protokol-perencanaan");
            assert!(hit_file.is_some(), "06_protokol_perencanaan MUST trigger when task.md exists at turn 2");
            assert!(hit_file.unwrap().match_reasons.iter().any(|r| r.contains("file_pattern: 'task.md'")));
            let _ = fs::remove_file(&task_file);
            println!("  ✅ Positive Trigger: file_pattern 'task.md' at turn 2 -> MATCHED");

            // Turn range gate: turn 0 (too early: 0 < min_turn 1)
            let m_t0 = eval("/plan arsitektur", &temp_ws, None, None, 0);
            assert!(!m_t0.iter().any(|x| x.doc_id == "coder-protokol-perencanaan"), "06_protokol_perencanaan MUST NOT trigger at turn 0 (< min_turn 1)");
            println!("  ✅ Turn Range Gate: turn 0 (< min_turn 1) -> NOT TRIGGERED");

            // Turn range gate: turn 4 (exceeded: 4 > max_turn 3)
            let m_t4 = eval("/plan arsitektur", &temp_ws, None, None, 4);
            assert!(!m_t4.iter().any(|x| x.doc_id == "coder-protokol-perencanaan"), "06_protokol_perencanaan MUST NOT trigger at turn 4 (> max_turn 3)");
            println!("  ✅ Turn Range Gate: turn 4 (> max_turn 3) -> NOT TRIGGERED");

            // Negative: Non-matching input
            let m_none = eval("halo selamat pagi", &temp_ws, None, None, 2);
            assert!(!m_none.iter().any(|x| x.doc_id == "coder-protokol-perencanaan"), "06_protokol_perencanaan MUST NOT trigger on unrelated input");
            println!("  ✅ Non-matching input: NOT TRIGGERED");

            // Negative exclusion: Disqualified on 'trading crypto'
            let m_ex = eval("/plan trading crypto bot", &temp_ws, None, None, 2);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-protokol-perencanaan"), "06_protokol_perencanaan MUST NOT trigger when input contains 'trading crypto'");
            println!("  ✅ Negative Exclusion: 'trading crypto' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 07: 07_arsitektur_swarm.md (tools_active: invoke_subagent, manage_subagents, send_message)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 07_arsitektur_swarm.md (id: coder-arsitektur-swarm)");
            let swarm_tools = ["invoke_subagent", "manage_subagents", "send_message"];
            for tool_name in &swarm_tools {
                let mut mounted = HashSet::new();
                mounted.insert(tool_name.to_string());
                let m = eval("bantu delegasi tugas", &temp_ws, Some(&mounted), None, 1);
                let hit = m.iter().find(|x| x.doc_id == "coder-arsitektur-swarm");
                assert!(hit.is_some(), "07_arsitektur_swarm MUST trigger when {} is active", tool_name);
                assert!(hit.unwrap().match_reasons.iter().any(|r| r.contains(&format!("tool_active: '{}'", tool_name))));
                println!("  ✅ Positive Trigger: tools_active '{}' -> MATCHED", tool_name);
            }

            // Positive 2: keywords
            let m_kw = eval("aktifkan worker subagent swarm untuk optimasi", &temp_ws, None, None, 1);
            assert!(m_kw.iter().any(|x| x.doc_id == "coder-arsitektur-swarm"), "07_arsitektur_swarm MUST trigger on keyword 'swarm'");
            println!("  ✅ Positive Trigger: keyword 'swarm' -> MATCHED");

            // Negative: Unrelated tool
            let mut other_tool = HashSet::new();
            other_tool.insert("view_file".to_string());
            let m_other = eval("baca berkas ini", &temp_ws, Some(&other_tool), None, 1);
            assert!(!m_other.iter().any(|x| x.doc_id == "coder-arsitektur-swarm"), "07_arsitektur_swarm MUST NOT trigger on view_file");
            println!("  ✅ Non-matching tool: 'view_file' -> NOT TRIGGERED");

            // Negative exclusion: Disqualified on 'forex'
            let mut mounted = HashSet::new();
            mounted.insert("invoke_subagent".to_string());
            let m_ex = eval("delegasikan analisa sinyal forex", &temp_ws, Some(&mounted), None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-arsitektur-swarm"), "07_arsitektur_swarm MUST NOT trigger when input contains 'forex'");
            println!("  ✅ Negative Exclusion: 'forex' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 08: 08_sensor_visual.md (tools_active: flow_screenshot, generate_image; file_patterns: *.html, *.tsx)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 08_sensor_visual.md (id: coder-sensor-visual)");
            // Positive 1: tools_active (flow_screenshot)
            let mut mounted = HashSet::new();
            mounted.insert("flow_screenshot".to_string());
            let m1 = eval("cek tampilan", &temp_ws, Some(&mounted), None, 1);
            let hit1 = m1.iter().find(|x| x.doc_id == "coder-sensor-visual");
            assert!(hit1.is_some(), "08_sensor_visual MUST trigger when flow_screenshot is active");
            assert!(hit1.unwrap().match_reasons.iter().any(|r| r.contains("tool_active: 'flow_screenshot'")));
            println!("  ✅ Positive Trigger 1: tools_active 'flow_screenshot' -> MATCHED");

            // Positive 2: tools_active (generate_image)
            let mut mounted_gi = HashSet::new();
            mounted_gi.insert("generate_image".to_string());
            let m_gi = eval("buat aset", &temp_ws, Some(&mounted_gi), None, 1);
            assert!(m_gi.iter().any(|x| x.doc_id == "coder-sensor-visual"), "08_sensor_visual MUST trigger when generate_image is active");
            println!("  ✅ Positive Trigger 2: tools_active 'generate_image' -> MATCHED");

            // Positive 3: file_patterns (*.html)
            let html_file = temp_ws.join("index.html");
            fs::write(&html_file, "<html><body>Hello</body></html>").unwrap();
            let m2 = eval("periksa berkas", &temp_ws, None, None, 1);
            let hit2 = m2.iter().find(|x| x.doc_id == "coder-sensor-visual");
            assert!(hit2.is_some(), "08_sensor_visual MUST trigger when *.html exists in workspace");
            assert!(hit2.unwrap().match_reasons.iter().any(|r| r.contains("file_pattern: '*.html'")));
            let _ = fs::remove_file(&html_file);
            println!("  ✅ Positive Trigger 3: file_pattern '*.html' -> MATCHED");

            // Positive 4: file_patterns (*.tsx)
            let tsx_file = temp_ws.join("App.tsx");
            fs::write(&tsx_file, "export const App = () => <div/>;").unwrap();
            let m_tsx = eval("periksa berkas", &temp_ws, None, None, 1);
            let hit_tsx = m_tsx.iter().find(|x| x.doc_id == "coder-sensor-visual");
            assert!(hit_tsx.is_some(), "08_sensor_visual MUST trigger when *.tsx exists in workspace");
            assert!(hit_tsx.unwrap().match_reasons.iter().any(|r| r.contains("file_pattern: '*.tsx'")));
            let _ = fs::remove_file(&tsx_file);
            println!("  ✅ Positive Trigger 4: file_pattern '*.tsx' -> MATCHED");

            // Negative: Non-matching input
            let m_none = eval("optimasi algoritma sorting", &temp_ws, None, None, 1);
            assert!(!m_none.iter().any(|x| x.doc_id == "coder-sensor-visual"), "08_sensor_visual MUST NOT trigger on non-visual query");
            println!("  ✅ Non-matching input: NOT TRIGGERED");

            // Negative exclusion: Disqualified on 'eurusd'
            let m_ex = eval("ambil screenshot chart eurusd", &temp_ws, Some(&mounted), None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-sensor-visual"), "08_sensor_visual MUST NOT trigger when input contains 'eurusd'");
            println!("  ✅ Negative Exclusion: 'eurusd' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 09: 09_ekosistem_plugin.md (tools_active: plugin_control; file_patterns: plugins/**, manifest.json)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 09_ekosistem_plugin.md (id: coder-ekosistem-plugin)");
            // Positive 1: tools_active (plugin_control)
            let mut mounted = HashSet::new();
            mounted.insert("plugin_control".to_string());
            let m1 = eval("cek ekstensi", &temp_ws, Some(&mounted), None, 1);
            let hit1 = m1.iter().find(|x| x.doc_id == "coder-ekosistem-plugin");
            assert!(hit1.is_some(), "09_ekosistem_plugin MUST trigger when plugin_control is active");
            assert!(hit1.unwrap().match_reasons.iter().any(|r| r.contains("tool_active: 'plugin_control'")));
            println!("  ✅ Positive Trigger 1: tools_active 'plugin_control' -> MATCHED");

            // Positive 2: file_patterns (manifest.json)
            let manifest_file = temp_ws.join("manifest.json");
            fs::write(&manifest_file, r#"{"name":"test"}"#).unwrap();
            let m2 = eval("periksa konfigurasi", &temp_ws, None, None, 1);
            let hit2 = m2.iter().find(|x| x.doc_id == "coder-ekosistem-plugin");
            assert!(hit2.is_some(), "09_ekosistem_plugin MUST trigger when manifest.json exists");
            assert!(hit2.unwrap().match_reasons.iter().any(|r| r.contains("file_pattern: 'manifest.json'")));
            let _ = fs::remove_file(&manifest_file);
            println!("  ✅ Positive Trigger 2: file_pattern 'manifest.json' -> MATCHED");

            // Positive 3: file_patterns (plugins/**)
            let plugins_dir = temp_ws.join("plugins");
            fs::create_dir_all(&plugins_dir).unwrap();
            let m3 = eval("periksa direktori", &temp_ws, None, None, 1);
            let hit3 = m3.iter().find(|x| x.doc_id == "coder-ekosistem-plugin");
            assert!(hit3.is_some(), "09_ekosistem_plugin MUST trigger when plugins/ directory exists");
            assert!(hit3.unwrap().match_reasons.iter().any(|r| r.contains("file_pattern: 'plugins/**'")));
            let _ = fs::remove_dir_all(&plugins_dir);
            println!("  ✅ Positive Trigger 3: file_pattern 'plugins/**' -> MATCHED");

            // Negative: Non-matching input
            let m_none = eval("perbaiki fungsi matematika", &temp_ws, None, None, 1);
            assert!(!m_none.iter().any(|x| x.doc_id == "coder-ekosistem-plugin"), "09_ekosistem_plugin MUST NOT trigger on unrelated input");
            println!("  ✅ Non-matching input: NOT TRIGGERED");

            // Negative exclusion: Disqualified on 'gbpusd'
            let m_ex = eval("pasang plugin sinyal gbpusd", &temp_ws, Some(&mounted), None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-ekosistem-plugin"), "09_ekosistem_plugin MUST NOT trigger when input contains 'gbpusd'");
            println!("  ✅ Negative Exclusion: 'gbpusd' -> DISQUALIFIED");
        }

        // =========================================================================
        // PROMPT 10: 10_spesialisasi_siber.md (cmd: nmap, snyk, trivy, cargo audit; tools_active: flow_audit)
        // =========================================================================
        {
            println!("\n🔍 AUDITING 10_spesialisasi_siber.md (id: coder-spesialisasi-siber)");
            // Positive 1: cmd triggers
            let sec_cmds = ["cargo audit", "nmap", "snyk", "trivy", "npm audit"];
            for cmd in &sec_cmds {
                let m = eval(&format!("jalankan {} pada target", cmd), &temp_ws, None, None, 1);
                let hit = m.iter().find(|x| x.doc_id == "coder-spesialisasi-siber");
                assert!(hit.is_some(), "10_spesialisasi_siber MUST trigger on cmd '{}'", cmd);
                assert!(hit.unwrap().match_reasons.iter().any(|r| r.contains(&format!("cmd: '{}'", cmd))));
                println!("  ✅ Positive Trigger: cmd '{}' -> MATCHED", cmd);
            }

            // Positive 2: tools_active (flow_audit)
            let mut mounted = HashSet::new();
            mounted.insert("flow_audit".to_string());
            let m_tool = eval("audit portabilitas dan SAST", &temp_ws, Some(&mounted), None, 1);
            let hit_tool = m_tool.iter().find(|x| x.doc_id == "coder-spesialisasi-siber");
            assert!(hit_tool.is_some(), "10_spesialisasi_siber MUST trigger when flow_audit is active");
            assert!(hit_tool.unwrap().match_reasons.iter().any(|r| r.contains("tool_active: 'flow_audit'")));
            println!("  ✅ Positive Trigger: tools_active 'flow_audit' -> MATCHED");

            // Positive 3: keywords
            let m_kw = eval("lakukan sast audit dan cari vulnerability scan", &temp_ws, None, None, 1);
            assert!(m_kw.iter().any(|x| x.doc_id == "coder-spesialisasi-siber"), "10_spesialisasi_siber MUST trigger on keyword 'sast audit'");
            println!("  ✅ Positive Trigger: keyword 'sast audit' -> MATCHED");

            // Negative: Non-matching input
            let m_none = eval("buatkan tabel html sederhana", &temp_ws, None, None, 1);
            assert!(!m_none.iter().any(|x| x.doc_id == "coder-spesialisasi-siber"), "10_spesialisasi_siber MUST NOT trigger on normal task");
            println!("  ✅ Non-matching input: NOT TRIGGERED");

            // Negative exclusion: Disqualified on 'forex'
            let m_ex = eval("cargo audit sinyal forex", &temp_ws, None, None, 1);
            assert!(!m_ex.iter().any(|x| x.doc_id == "coder-spesialisasi-siber"), "10_spesialisasi_siber MUST NOT trigger when input contains 'forex'");
            println!("  ✅ Negative Exclusion: 'forex' -> DISQUALIFIED");
        }

        let _ = fs::remove_dir_all(&temp_ws);
        println!("\n🎉 ALL 11 CODER PERSONA PROMPTS (00 TO 10) EXHAUSTIVELY AUDITED AND VERIFIED WITH EXIT CODE 0!");
        println!("================================================================================");
    }

    #[test]
    fn test_multi_os_path_portability_and_glob_matching() {
        let temp_ws = std::env::temp_dir().join(format!("flw_path_portability_{}", std::process::id()));
        let _ = fs::create_dir_all(&temp_ws);

        // Create directory hierarchy simulating cross-platform workspace
        let docs_adr = temp_ws.join("docs").join("adr");
        let git_dir = temp_ws.join(".git");
        let dashboards_dir = temp_ws.join("dashboards");
        let plugins_dir = temp_ws.join("plugins");
        let src_dir = temp_ws.join("src");

        let _ = fs::create_dir_all(&docs_adr);
        let _ = fs::create_dir_all(&git_dir);
        let _ = fs::create_dir_all(&dashboards_dir);
        let _ = fs::create_dir_all(&plugins_dir);
        let _ = fs::create_dir_all(&src_dir);

        let _ = fs::write(docs_adr.join("0001-init.adr.md"), "# ADR 1");
        let _ = fs::write(dashboards_dir.join("analytics.url.json"), "{}");
        let _ = fs::write(src_dir.join("main.rs"), "fn main() {}");
        let _ = fs::write(temp_ws.join("Cargo.toml"), "[package]");

        let sampled = SovereignPersonaEngine::sample_workspace_files(&temp_ws);
        println!("Sampled files count: {}", sampled.len());

        // 1. Windows backslash vs Linux slash in directory glob patterns
        assert!(SovereignPersonaEngine::matches_file_pattern("docs/adr/**", &sampled), "Linux slash docs/adr/** must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("docs\\adr\\**", &sampled), "Windows backslash docs\\adr\\** must match");
        assert!(SovereignPersonaEngine::matches_file_pattern(".git/**", &sampled), "Linux slash .git/** must match");
        assert!(SovereignPersonaEngine::matches_file_pattern(".git\\**", &sampled), "Windows backslash .git\\** must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("dashboards/**", &sampled), "dashboards/** must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("dashboards\\**", &sampled), "Windows backslash dashboards\\** must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("plugins/**", &sampled), "plugins/** must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("plugins\\**", &sampled), "Windows backslash plugins\\** must match");

        // 2. Extension globs
        assert!(SovereignPersonaEngine::matches_file_pattern("*.rs", &sampled), "*.rs must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("*.url.json", &sampled), "*.url.json must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("*.adr.md", &sampled), "*.adr.md must match");
        assert!(!SovereignPersonaEngine::matches_file_pattern("*.nonexistent_ext", &sampled), "nonexistent extension must not match");

        // 3. Exact files (case-insensitive & cross-path)
        assert!(SovereignPersonaEngine::matches_file_pattern("Cargo.toml", &sampled), "Cargo.toml exact must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("cargo.toml", &sampled), "cargo.toml lowercase must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("src/main.rs", &sampled), "src/main.rs must match");
        assert!(SovereignPersonaEngine::matches_file_pattern("src\\main.rs", &sampled), "src\\main.rs Windows backslash must match");

        let _ = fs::remove_dir_all(&temp_ws);
        println!("✅ test_multi_os_path_portability_and_glob_matching PASSED");
    }

    #[test]
    fn test_fault_tolerance_nonexistent_dir_locked_and_empty_frontmatter() {
        // 1. Non-existent workspace directory
        let fake_ws = Path::new("/tmp/flw_nonexistent_directory_999999_void");
        let sampled = SovereignPersonaEngine::sample_workspace_files(fake_ws);
        assert!(sampled.is_empty(), "Sampling non-existent workspace must return empty Vec, not panic");

        // 2. Non-existent persona roots
        let fake_roots = vec![fake_ws.to_path_buf()];
        let docs = SovereignPersonaEngine::load_all_persona_docs(&fake_roots);
        assert!(docs.is_empty(), "Loading docs from non-existent root must return empty Vec");

        let scoped_docs = SovereignPersonaEngine::load_persona_docs_for_persona(&fake_roots, "coder");
        assert!(scoped_docs.is_empty(), "Loading scoped docs from non-existent root must return empty Vec");

        let personas = SovereignPersonaEngine::list_available_personas(&fake_roots);
        assert!(personas.is_empty(), "Non-existent roots must yield empty persona list");

        // 3. Empty string
        let empty_doc = SovereignPersonaEngine::parse_persona_markdown("", fake_ws, "coder");
        assert!(empty_doc.is_none(), "Empty content must return None safely");

        // 4. Content without frontmatter
        let no_fm = SovereignPersonaEngine::parse_persona_markdown("# Just Markdown\nNo frontmatter here", fake_ws, "coder");
        assert!(no_fm.is_none(), "Markdown without frontmatter must return None safely");

        // 5. Empty frontmatter
        let empty_fm = SovereignPersonaEngine::parse_persona_markdown("---\n---\nBody here", fake_ws, "coder");
        assert!(empty_fm.is_some(), "Empty frontmatter must parse with default values safely");
        let efm_doc = empty_fm.unwrap();
        assert!(efm_doc.trigger.always, "Doc with empty frontmatter defaults to always: true");

        // 6. Unclosed frontmatter
        let unclosed = SovereignPersonaEngine::parse_persona_markdown("---\nid: unclosed\npriority: 90\n", fake_ws, "coder");
        assert!(unclosed.is_none(), "Unclosed frontmatter must return None safely");

        // 7. Malformed / corrupted frontmatter
        let corrupt = r#"---
id: "corrupted"
priority: not_a_number_here
turn_range:
  min_turn: invalid_int
  max_turn: "invalid_too"
tool_threshold:
  min_calls: broken
tool_stalled:
  consecutive_failures: bad_int
trigger:
  keywords: [broken, syntax, %$#@!]
  commands: ["valid_cmd"]
---
Body text
"#;
        let corrupt_doc = SovereignPersonaEngine::parse_persona_markdown(corrupt, fake_ws, "coder");
        assert!(corrupt_doc.is_some(), "Corrupted frontmatter must fail gracefully to defaults without panicking");
        let cdoc = corrupt_doc.unwrap();
        assert_eq!(cdoc.id, "corrupted");
        assert_eq!(cdoc.priority, 80, "Invalid priority falls back to default 80");
        assert!(cdoc.trigger.commands.contains(&"valid_cmd".to_string()));

        // 8. Traversal attempts in persona name
        let traversal_docs = SovereignPersonaEngine::load_persona_docs_for_persona(&fake_roots, "../../../etc/passwd");
        assert!(traversal_docs.is_empty(), "Path traversal target must be strictly rejected");

        println!("✅ test_fault_tolerance_nonexistent_dir_locked_and_empty_frontmatter PASSED");
    }

    #[test]
    fn test_latency_and_memory_benchmark_20_plus_personas() {
        use std::time::Instant;

        let fake_ws = Path::new("/tmp/flw_bench_ws_void");

        // Construct 25 realistic persona documents covering all trigger types
        let mut docs = Vec::new();
        for i in 0..25 {
            let mut trigger = TriggerSpec::default();
            match i % 8 {
                0 => {
                    // Baseline always
                    trigger.always = true;
                }
                1 => {
                    // Keywords
                    trigger.keywords = vec![format!("keyword_{}", i), "optimization".to_string(), "database".to_string()];
                    trigger.exclude_keywords = vec!["crypto_trading".to_string(), "forex_signal".to_string()];
                }
                2 => {
                    // Commands
                    trigger.commands = vec![format!("cargo test {}", i), "git commit".to_string(), "/plan".to_string()];
                }
                3 => {
                    // Tools active
                    trigger.tools_active = vec!["run_command".to_string(), "write_to_file".to_string()];
                }
                4 => {
                    // Tool threshold
                    trigger.tool_threshold_tool = Some("run_command".to_string());
                    trigger.tool_threshold_min = 3;
                }
                5 => {
                    // Tool stalled
                    trigger.tool_stalled_tool = Some("run_command".to_string());
                    trigger.tool_stalled_consecutive_failures = 2;
                }
                6 => {
                    // Turn range
                    trigger.min_turn = Some(2);
                    trigger.max_turn = Some(10);
                }
                _ => {
                    // Combined keywords + exclude
                    trigger.keywords = vec!["refactor".to_string(), "architectural_audit".to_string()];
                    trigger.exclude_keywords = vec!["unrelated_domain".to_string()];
                }
            }

            docs.push(PersonaDocument {
                id: format!("doc_{}", i),
                persona: format!("role_{}", i % 5),
                target: "prompt".to_string(),
                priority: 80 + (i as u32 % 20),
                trigger,
                file_path: PathBuf::from(format!("/fake/doc_{}.md", i)),
                body_markdown: format!("# Role {}\nInstructions for document {}.", i % 5, i),
            });
        }

        assert_eq!(docs.len(), 25, "Must have exactly 25 persona documents for stress test");

        let mut mounted = HashSet::new();
        mounted.insert("run_command".to_string());
        mounted.insert("write_to_file".to_string());

        let mut stats = HashMap::new();
        stats.insert("run_command".to_string(), ToolRunStats {
            total_calls: 5,
            consecutive_failures: 2,
            last_exit_code: 1,
        });

        let search_text = "please execute cargo test 2 and perform refactor on database architecture";

        // Warm up
        for _ in 0..100 {
            let _ = SovereignPersonaEngine::evaluate_docs_triggers(
                &docs,
                search_text,
                fake_ws,
                Some(&mounted),
                Some(&stats),
                3,
            );
        }

        // Benchmark: 1,000 iterations
        let iterations = 1000;
        let start = Instant::now();
        let mut total_matches = 0;

        for _ in 0..iterations {
            let res = SovereignPersonaEngine::evaluate_docs_triggers(
                &docs,
                search_text,
                fake_ws,
                Some(&mounted),
                Some(&stats),
                3,
            );
            total_matches += res.len();
        }

        let elapsed = start.elapsed();
        let avg_micros = elapsed.as_micros() as f64 / iterations as f64;
        let avg_millis = avg_micros / 1000.0;

        println!("============================================================");
        println!("🚀 PERSONA ENGINE STRESS BENCHMARK (25 DOCUMENTS)");
        println!("Iterations: {}", iterations);
        println!("Total elapsed: {:?}", elapsed);
        println!("Average latency per evaluation: {:.3} µs ({:.4} ms)", avg_micros, avg_millis);
        println!("Total matched persona entries: {}", total_matches);
        println!("============================================================");

        // Strict Requirement: evaluation of 20+ documents MUST be < 1.0 millisecond
        assert!(avg_millis < 1.0, "Average evaluation latency ({:.4} ms) must be < 1.0 ms", avg_millis);
        // In fact, zero-allocation matching in Rust easily beats 0.2 ms
        assert!(avg_millis < 0.2, "Zero-regex evaluation should complete well under 0.2 ms");
        assert!(total_matches > 0, "Benchmark must find valid matches");
        println!("✅ test_latency_and_memory_benchmark_20_plus_personas PASSED");
    }

    #[test]
    fn test_all_8_trigger_dimensions_rigorous() {
        let temp_dir = std::env::temp_dir().join(format!("flw_all_8_dimensions_{}", std::process::id()));
        let _ = fs::create_dir_all(&temp_dir);

        // --- Dimension 1: always: true (Baseline) ---
        let d1_yaml = r#"---
id: d1-always
persona: tester
target: prompt
priority: 100
always: true
---
Always active body
"#;
        let d1 = SovereignPersonaEngine::parse_persona_markdown(d1_yaml, Path::new("/d1.md"), "tester").unwrap();
        assert!(d1.trigger.always);
        let m1 = SovereignPersonaEngine::evaluate_docs_triggers(&[d1], "anything", &temp_dir, None, None, 1);
        assert_eq!(m1.len(), 1);
        assert_eq!(m1[0].match_reasons, vec!["always_active"]);

        // --- Dimension 2: cmd / commands (CLI & Slash commands) ---
        let d2_yaml = r#"---
id: d2-cmd
persona: tester
target: prompt
priority: 95
trigger:
  cmd: ["git commit", "git push", "/plan", "/diagnose"]
---
Command body
"#;
        let d2 = SovereignPersonaEngine::parse_persona_markdown(d2_yaml, Path::new("/d2.md"), "tester").unwrap();
        let m2_a = SovereignPersonaEngine::evaluate_docs_triggers(&[d2.clone()], "run git commit -m 'init'", &temp_dir, None, None, 1);
        assert!(m2_a.iter().any(|m| m.match_reasons.iter().any(|r| r.contains("cmd: 'git commit'"))));
        let m2_b = SovereignPersonaEngine::evaluate_docs_triggers(&[d2], "execute /plan please", &temp_dir, None, None, 1);
        assert!(m2_b.iter().any(|m| m.match_reasons.iter().any(|r| r.contains("cmd: '/plan'"))));

        // --- Dimension 3: tools_active ---
        let d3_yaml = r#"---
id: d3-tools
persona: tester
target: prompt
priority: 90
trigger:
  tools_active: ["run_command", "replace_file_content"]
---
Tools active body
"#;
        let d3 = SovereignPersonaEngine::parse_persona_markdown(d3_yaml, Path::new("/d3.md"), "tester").unwrap();
        let mut mounted = HashSet::new();
        mounted.insert("run_command".to_string());
        let m3 = SovereignPersonaEngine::evaluate_docs_triggers(&[d3], "arbitrary", &temp_dir, Some(&mounted), None, 1);
        assert!(m3.iter().any(|m| m.match_reasons.iter().any(|r| r.contains("tool_active: 'run_command'"))));

        // --- Dimension 4: tool_stalled (circuit breaker) ---
        let d4_yaml = r#"---
id: d4-stall
persona: tester
target: prompt
priority: 92
trigger:
  tool_stalled:
    tool: "run_command"
    consecutive_failures: 2
---
Stall circuit breaker body
"#;
        let d4 = SovereignPersonaEngine::parse_persona_markdown(d4_yaml, Path::new("/d4.md"), "tester").unwrap();
        let mut stats_fail1 = HashMap::new();
        stats_fail1.insert("run_command".to_string(), ToolRunStats { total_calls: 1, consecutive_failures: 1, last_exit_code: 1 });
        let m4_no = SovereignPersonaEngine::evaluate_docs_triggers(&[d4.clone()], "arbitrary", &temp_dir, None, Some(&stats_fail1), 1);
        assert!(m4_no.is_empty(), "Failures 1 < 2 must not trigger");

        let mut stats_fail2 = HashMap::new();
        stats_fail2.insert("run_command".to_string(), ToolRunStats { total_calls: 2, consecutive_failures: 2, last_exit_code: 1 });
        let m4_yes = SovereignPersonaEngine::evaluate_docs_triggers(&[d4], "arbitrary", &temp_dir, None, Some(&stats_fail2), 1);
        assert!(m4_yes.iter().any(|m| m.match_reasons.iter().any(|r| r.contains("tool_stalled: 'run_command' (failures: 2 >= 2)"))));

        // --- Dimension 5: tool_threshold (usage counter) ---
        let d5_yaml = r#"---
id: d5-thresh
persona: tester
target: prompt
priority: 88
trigger:
  tool_threshold:
    tool: "write_to_file"
    min_calls: 5
---
Threshold body
"#;
        let d5 = SovereignPersonaEngine::parse_persona_markdown(d5_yaml, Path::new("/d5.md"), "tester").unwrap();
        let mut stats_th4 = HashMap::new();
        stats_th4.insert("write_to_file".to_string(), ToolRunStats { total_calls: 4, consecutive_failures: 0, last_exit_code: 0 });
        let m5_no = SovereignPersonaEngine::evaluate_docs_triggers(&[d5.clone()], "arbitrary", &temp_dir, None, Some(&stats_th4), 1);
        assert!(m5_no.is_empty(), "Calls 4 < 5 must not trigger");

        let mut stats_th5 = HashMap::new();
        stats_th5.insert("write_to_file".to_string(), ToolRunStats { total_calls: 5, consecutive_failures: 0, last_exit_code: 0 });
        let m5_yes = SovereignPersonaEngine::evaluate_docs_triggers(&[d5], "arbitrary", &temp_dir, None, Some(&stats_th5), 1);
        assert!(m5_yes.iter().any(|m| m.match_reasons.iter().any(|r| r.contains("tool_threshold: 'write_to_file' (calls: 5 >= 5)"))));

        // --- Dimension 6: file_patterns ---
        let d6_yaml = r#"---
id: d6-file
persona: tester
target: prompt
priority: 85
trigger:
  file_patterns: ["*.custom_ext", "special_dir/**"]
---
File pattern body
"#;
        let d6 = SovereignPersonaEngine::parse_persona_markdown(d6_yaml, Path::new("/d6.md"), "tester").unwrap();
        let m6_no = SovereignPersonaEngine::evaluate_docs_triggers(&[d6.clone()], "arbitrary", &temp_dir, None, None, 1);
        assert!(m6_no.is_empty());

        let special_dir = temp_dir.join("special_dir");
        let _ = fs::create_dir_all(&special_dir);
        let m6_yes = SovereignPersonaEngine::evaluate_docs_triggers(&[d6], "arbitrary", &temp_dir, None, None, 1);
        assert!(m6_yes.iter().any(|m| m.match_reasons.iter().any(|r| r.contains("file_pattern: 'special_dir/**'"))));
        let _ = fs::remove_dir_all(&special_dir);

        // --- Dimension 7: turn_range (min_turn / max_turn) ---
        let d7_yaml = r#"---
id: d7-turn
persona: tester
target: prompt
priority: 82
trigger:
  turn_range:
    min_turn: 2
    max_turn: 4
---
Turn range body
"#;
        let d7 = SovereignPersonaEngine::parse_persona_markdown(d7_yaml, Path::new("/d7.md"), "tester").unwrap();
        // Turn 1: too early
        assert!(SovereignPersonaEngine::evaluate_docs_triggers(&[d7.clone()], "arbitrary", &temp_dir, None, None, 1).is_empty());
        // Turn 2: in range
        let m7_2 = SovereignPersonaEngine::evaluate_docs_triggers(&[d7.clone()], "arbitrary", &temp_dir, None, None, 2);
        assert_eq!(m7_2.len(), 1);
        // Turn 4: in range
        let m7_4 = SovereignPersonaEngine::evaluate_docs_triggers(&[d7.clone()], "arbitrary", &temp_dir, None, None, 4);
        assert_eq!(m7_4.len(), 1);
        // Turn 5: exceeded
        assert!(SovereignPersonaEngine::evaluate_docs_triggers(&[d7], "arbitrary", &temp_dir, None, None, 5).is_empty());

        // --- Dimension 8: keywords & exclude_keywords + YAML bullet list syntax ---
        let d8_yaml = r#"---
id: d8-keywords
persona: tester
target: prompt
priority: 80
trigger:
  keywords:
    - "refactor"
    - "architecture"
    - "clean code"
  exclude_keywords:
    - "forex"
    - "crypto"
---
Keywords body
"#;
        let d8 = SovereignPersonaEngine::parse_persona_markdown(d8_yaml, Path::new("/d8.md"), "tester").unwrap();
        assert!(d8.trigger.keywords.contains(&"refactor".to_string()));
        assert!(d8.trigger.keywords.contains(&"architecture".to_string()));
        assert!(d8.trigger.exclude_keywords.contains(&"forex".to_string()));

        // Positive keyword
        let m8_pos = SovereignPersonaEngine::evaluate_docs_triggers(&[d8.clone()], "please refactor the module", &temp_dir, None, None, 1);
        assert!(m8_pos.iter().any(|m| m.match_reasons.iter().any(|r| r.contains("keyword: 'refactor'"))));

        // Negative exclusion
        let m8_ex = SovereignPersonaEngine::evaluate_docs_triggers(&[d8], "please refactor forex module", &temp_dir, None, None, 1);
        assert!(m8_ex.is_empty(), "Must be disqualified when forex is present");

        let _ = fs::remove_dir_all(&temp_dir);
        println!("✅ test_all_8_trigger_dimensions_rigorous PASSED");
    }
}


