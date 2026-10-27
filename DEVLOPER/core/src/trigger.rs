//! [FLOWORKOS:SOVEREIGN_TRIGGER_ENGINE]
//! Native Dynamic Trigger & Memory Harvester Engine
//! Evaluates runtime context and selectively injects specialized doctrines & memories
//! Co-authored-by: Flowork OS <agent@floworkos.com>

use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use serde_json::{json, Value};
use crate::agents::AgentCategory;
pub use crate::system_trigger;

// ============================================================================
// SOVEREIGN TRIGGER ENGINE: ENGINEERING DOCTRINES EXTENSION
// Co-authored-by: Flowork OS <agent@floworkos.com>
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EngineeringDoctrine {
    DiagnosingBugs,
    TestDrivenDevelopment,
    GrillWithDocs,
    EngineeringCounsel,
    DeepModules,
    DomainModelingAdr,
    SpecAndTriage,
    HandoffAndPrototype,
    GitGuardrails,
    TwoAxisReview,
    ReverseEngineering,
    Wayfinding,
    PrimarySourceResearch,
}

impl EngineeringDoctrine {
    pub fn id(&self) -> &'static str {
        match self {
            Self::DiagnosingBugs => "diagnosing-bugs",
            Self::TestDrivenDevelopment => "tdd",
            Self::GrillWithDocs => "grill-with-docs",
            Self::EngineeringCounsel => "engineering-counsel",
            Self::DeepModules => "deep-modules",
            Self::DomainModelingAdr => "domain-modeling",
            Self::SpecAndTriage => "spec-triage",
            Self::HandoffAndPrototype => "handoff-prototype",
            Self::GitGuardrails => "git-guardrails",
            Self::TwoAxisReview => "two-axis-review",
            Self::ReverseEngineering => "reverse-engineering",
            Self::Wayfinding => "wayfinding",
            Self::PrimarySourceResearch => "primary-source",
        }
    }

    pub fn title(&self) -> String {
        match self {
            Self::DiagnosingBugs => "Systematic Bug Diagnosis & Root-Cause Elimination".to_string(),
            Self::TestDrivenDevelopment => "Test-Driven Verification & Red-Green-Refactor Discipline".to_string(),
            Self::GrillWithDocs => "Grill With Docs (Deep RFC & Source Verification)".to_string(),
            Self::EngineeringCounsel => "Engineering Counsel & Architectural Advisory".to_string(),
            Self::DeepModules => "Deep Modules & Information Hiding".to_string(),
            Self::DomainModelingAdr => "Domain Modeling & Architectural Decision Records (ADR)".to_string(),
            Self::SpecAndTriage => "Specification Synthesis & Triage Discipline".to_string(),
            Self::HandoffAndPrototype => "Rapid Prototyping & Seamless Operational Handoff".to_string(),
            Self::GitGuardrails => "Git Guardrails & Trunk-Based Atomic Commits".to_string(),
            Self::TwoAxisReview => "Two-Axis Code Review (Correctness & Architecture)".to_string(),
            Self::ReverseEngineering => "Systematic Reverse Engineering & Decompilation".to_string(),
            Self::Wayfinding => "Autonomous Wayfinding & Codebase Navigation".to_string(),
            Self::PrimarySourceResearch => "Primary Source Technical Research".to_string(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct EngineeringDoctrineResult {
    pub doctrine: EngineeringDoctrine,
    pub confidence_score: u32,
    pub matched_trigger: String,
    pub prompt_injection: String,
}

/// Sovereign Trigger Engine
pub struct SovereignTriggerEngine;

impl SovereignTriggerEngine {
    /// Evaluates substring match against keywords with mandatory negative exclusion rules (case-insensitive contains)
    pub fn matches_with_exclusion(search_text: &str, keywords: &[String], exclude_keywords: &[String]) -> bool {
        let lower = search_text.to_lowercase();
        // 1. Short-circuit negative matching: If ANY exclude keyword is contained as substring, disqualify immediately!
        for ex in exclude_keywords {
            let ex_clean = ex.trim().to_lowercase();
            if !ex_clean.is_empty() && lower.contains(&ex_clean) {
                return false;
            }
        }
        // 2. Positive matching: At least one keyword must be contained as substring
        for kw in keywords {
            let kw_clean = kw.trim().to_lowercase();
            if !kw_clean.is_empty() && lower.contains(&kw_clean) {
                return true;
            }
        }
        false
    }

    /// Evaluates if a text contains URL protocol prefixes or valid internet domains (TLDs).
    pub fn detect_domain_or_url(text: &str) -> bool {
        let lower = text.to_lowercase();
        if lower.contains(&crate::prompt_enclave::PromptEnclave::proto_http()) || lower.contains(&crate::prompt_enclave::PromptEnclave::proto_https()) || lower.contains("ftp://") || lower.contains("www.") {
            return true;
        }

        let tlds = [
            ".com", ".net", ".org", ".id", ".io", ".ai", ".co", ".app", ".dev",
            ".xyz", ".site", ".info", ".online", ".tech", ".me", ".edu", ".gov",
            ".tv", ".cc", ".biz", ".co.id", ".web.id", ".or.id", ".go.id", ".ac.id",
            ".cloud", ".store", ".agency", ".live", ".space", ".pro", ".top", ".vip",
            ".uk", ".de", ".jp", ".fr", ".cn", ".in", ".nl", ".eu"
        ];

        for token in lower.split(|c: char| c.is_whitespace() || c == ',' || c == '"' || c == '\'' || c == '(' || c == ')' || c == '[' || c == ']' || c == '<' || c == '>') {
            let clean_tok = token.trim_matches(|c: char| !c.is_alphanumeric() && c != '.' && c != '/' && c != '-' && c != '_' && c != ':');
            let host = clean_tok.split('/').next().unwrap_or(clean_tok);
            let host_no_port = host.split(':').next().unwrap_or(host);

            for tld in &tlds {
                if host_no_port.ends_with(tld) {
                    let prefix = &host_no_port[..host_no_port.len() - tld.len()];
                    if !prefix.is_empty() && prefix.chars().all(|c| c.is_alphanumeric() || c == '-' || c == '.') {
                        return true;
                    }
                }
            }
        }
        false
    }

    /// Loads a trigger mandate or banner dynamically from disk or sealed constants
    pub fn load_trigger_file(filename: &str) -> Option<String> {
        let clean = filename.trim();
        if clean.contains("BROWSER") || clean.contains("WEB_RESILIENCE") {
            let res = crate::prompt_enclave::PromptEnclave::sovereign_web_resilience();
            if !res.is_empty() {
                Some(res)
            } else {
                Some("<SOVEREIGN_WEB_RESILIENCE>\n🌐 DOKTRIN KETAHANAN DAN INTELIJEN BROWSER STEALTH\n1. ANTI-BOT DETECTION: Selalu gunakan teknik stealth browsing.\n2. RESILIENCE: Hindari rate limit dan Cloudflare challenge.\n</SOVEREIGN_WEB_RESILIENCE>".to_string())
            }
        } else if clean.contains("AUTONOMOUS") || clean.contains("HEADLESS") {
            Some("<AUTONOMOUS_HEADLESS_MODE>\n⚡ DOKTRIN EKSEKUSI OTONOM PENUH TANPA OPERATOR (NON-INTERACTIVE HEADLESS EXECUTION)\n1. TUNTASKAN HINGGA AKHIR SECARA MANDIRI (DO NOT ASK OPERATOR CONFIRMATION)\n2. EKSEKUSI TOOL LANGSUNG SECARA PRESISI\n3. BUKTIKAN HASIL SECARA TERMINAL DAN VISUAL DENGAN EXIT CODE 0\n</AUTONOMOUS_HEADLESS_MODE>".to_string())
        } else if clean.contains("PLAN") {
            Some("<PLANNING_MODE_MANDATE>\nSTATUS: ACTIVE ARCHITECTURAL PLANNING.\n1. CODE WRITING RESTRICTION: Do NOT write, modify, or delete production code during planning phase.\n2. ARCHITECTURAL BLUEPRINT: Produce a comprehensive multi-phase implementation roadmap with clear exit criteria.\n</PLANNING_MODE_MANDATE>".to_string())
        } else {
            None
        }
    }

    /// 2. Trigger 25: Sovereign Browser Stealth, Intelligence & Web Resilience (117k ⭐ browser-use pattern)
    /// Injected when:
    /// - Browser or web tools are mounted
    /// - Recent turn history invoked web tools
    /// - Search text mentions a domain / URL (.com, .net, web protocols, etc.)
    /// - Bilingual / global keywords related to web scraping, recon, traffic, SEO, or security
    pub fn eval_browser_stealth(
        search_text: &str,
        mounted_tools: Option<&HashSet<String>>,
        has_recent_web_tool: bool,
    ) -> Option<String> {
        let has_browser_tool = mounted_tools.map(|m| {
            m.contains("browser")
                || m.contains("browser_action")
                || m.contains("read_browser_page")
                || m.contains("web_scraper")
                || m.contains("browser_qa_tester")
                || m.contains("web_security_audit")
                || m.contains("website_intelligence")
                || m.contains("read_url_content")
        }).unwrap_or(false);

        let has_domain_or_url = Self::detect_domain_or_url(search_text);

        let has_web_keywords = [
            // Global / English keywords
            "browser", "headless", "cloudflare", "captcha", "turnstile",
            "bot detection", "scraping", "scrape", "crawler", "crawl",
            "puppeteer", "playwright", "selenium", "bypass bot",
            "web security", "security audit", "vulnerability", "ssl", "tls",
            "dns", "whois", "subdomain", "recon", "doh", "cert transparency",
            "traffic", "seo", "rank", "ranking", "web visit", "page speed",
            "audit domain", "domain audit", "web test", "read url", "fetch url",
            "http headers", "endpoint",
            // Indonesian / Slang keywords
            "peramban", "buka website", "kunjungi url", "situs", "website",
            "web", "domain", "keamanan web", "audit keamanan", "celah web",
            "trafik", "peringkat web", "pengunjung web", "analisis web",
            "analisa web", "cek situs", "periksa web", "ekstrak web"
        ].iter().any(|&kw| search_text.contains(kw));

        // EXCLUSION: YouTube targets are handled by dedicated Sovereign YouTube Intelligence trigger
        // Unless explicit cyber security audit is explicitly demanded for youtube.com
        if Self::is_youtube_target(search_text) && !Self::has_explicit_security_keywords(search_text) {
            return None;
        }

        if has_browser_tool || has_recent_web_tool || has_domain_or_url || has_web_keywords {
            Self::load_trigger_file("TRIGGER_BROWSER_STEALTH_WEB_RESILIENCE.md")
        } else {
            None
        }
    }

    /// Evaluates if a search query or input target is directed towards YouTube
    pub fn is_youtube_target(text: &str) -> bool {
        let lower = text.to_lowercase();
        lower.contains("youtube.com")
            || lower.contains("youtu.be")
            || lower.contains("m.youtube.com")
            || lower.contains("music.youtube.com")
            || (lower.contains("v=") && (lower.contains("watch") || lower.contains("youtube")))
            || lower.contains("/shorts/")
            || lower.contains("youtube_spy")
            || lower.contains("yt spy")
    }

    /// Checks if a query specifically requests web security penetration testing / vulnerability auditing
    pub fn has_explicit_security_keywords(text: &str) -> bool {
        let lower = text.to_lowercase();
        [
            "web_security_audit", "security audit", "vulnerability",
            "celah keamanan", "audit keamanan", "sqli", "sql injection",
            "xss", "hsts", "whois", "subdomain", "doh", "cert transparency"
        ].iter().any(|&kw| lower.contains(kw))
    }

    /// 2.5. Trigger 31: Sovereign YouTube Intelligence & Competitor Steal Studio
    /// Injected when:
    /// - Search text mentions YouTube URLs (watch, shorts, channel, @handle, youtu.be)
    /// - YouTube intelligence keywords (youtube, yt spy, transcript, secret tags, competitor analysis)
    /// - YouTube native tools mounted
    pub fn eval_youtube_intelligence(
        search_text: &str,
        mounted_tools: Option<&HashSet<String>>,
    ) -> Option<String> {
        let has_youtube_tool = mounted_tools.map(|m| {
            m.iter().any(|t| t.contains("youtube_spy") || t.contains("yt_spy"))
        }).unwrap_or(false);

        let is_yt = Self::is_youtube_target(search_text);

        let has_yt_keywords = [
            "youtube", "yt spy", "transkrip youtube", "bedah video",
            "video youtube", "channel youtube", "kompetitor youtube",
            "secret tags", "algoritma youtube", "thumbnail youtube",
            "hook video", "retensi video", "analisa video", "analisis video"
        ].iter().any(|&kw| search_text.to_lowercase().contains(kw));

        if has_youtube_tool || is_yt || has_yt_keywords {
            Self::load_trigger_file("TRIGGER_YOUTUBE_INTELLIGENCE.md")
        } else {
            None
        }
    }

    /// 3. Trigger 23: Autonomous Headless Execution (168k ⭐ AutoGPT & Aider pattern)
    /// Injected when:
    /// - Explicit autonomous flag is active
    /// - Slash commands (/goal, --auto, --headless, etc.)
    /// - Global or bilingual execution directives ("gas", "ok gas", "hajar", "sikat", "tuntaskan", "hands-free", "unattended", etc.)
    pub fn eval_autonomous_mode(search_text: &str, is_autonomous_flag: bool) -> Option<String> {
        let search_lower = search_text.to_lowercase();
        let is_word_match = |word: &str| -> bool {
            search_text.split(|c: char| !c.is_alphanumeric() && c != '-' && c != '/').any(|tok| tok.eq_ignore_ascii_case(word))
        };

        let has_phrase_match = [
            // Commands & flags (short -y handled via is_word_match)
            "/goal", "--auto", "--headless", "--unattended", "--yes", "--autonomous",
            // Indonesian & explicit directives
            "ok gas", "gas terus", "gas pol", "sikat habis",
            "mode otonom", "autonomous mode", "autonomously", "pantang berhenti",
            "tuntaskan sampai selesai", "kerjakan sendiri", "selesaikan sendiri",
            "tanpa tanya", "tanpa konfirmasi", "jangan tanya", "eksekusi mandiri", "mandiri penuh",
            // Global & English directives
            "go ahead", "do it all", "unattended", "hands-free", "hands free",
            "full auto", "non-interactive", "no confirmation", "dont ask", "don't ask",
            "just do it", "keep going", "finish the job", "end-to-end", "zero intervention",
            "overnight run"
        ].iter().any(|&phrase| search_lower.contains(phrase));

        let is_goal_or_auto = is_autonomous_flag
            || has_phrase_match
            || is_word_match("-y");

        if is_goal_or_auto {
            Self::load_trigger_file("TRIGGER_AUTONOMOUS_HEADLESS_MODE.md")
        } else {
            None
        }
    }

    /// 4. Trigger 06: Eternal Brain Selective Memory Recall (Clean chatbot mode: amnesia)
    pub fn eval_brain_recall(_search_text: &str, _effective_ws: &Path) -> Option<String> {
        None
    }

    /// 4.5. Sovereign Tool Intercept Gate & Past Memory Harvester
    /// When agent calls its first tool in a turn with a technical reason (in English):
    /// - Matches Top-3 Memories (out of .fl_brain/memories/*.md, prioritizing newest created_at timestamp & highest relevance)
    /// - Injects into context and unlocks tool execution
    /// Note: Skills are NOT auto-injected here. Skills require manual exploration and explicit pinning via 4-tier hierarchy.
    /// 4.5. Sovereign Tool Intercept Gate & Past Memory Harvester
    /// When agent calls its first tool in a turn with a technical reason (in English):
    /// - Matches Top-3 Memories (prioritizing memories/{username}/{agent_id} with +30pt boost, then shared, then newest created_at & highest relevance)
    /// - Injects into context and unlocks tool execution
    /// Note: Skills are NOT auto-injected here. Skills require manual exploration and explicit pinning via 4-tier hierarchy.
    pub fn eval_intercept_gate(
        reason: &str,
        effective_ws: &Path,
        engine_root: &Path,
    ) -> (String, Vec<Value>) {
        Self::eval_intercept_gate_scoped(reason, effective_ws, engine_root, None, None)
    }

    /// Evaluates intercept gate with specific user and active agent isolation
    /// Ensures agent memories do NOT cross-contaminate between different agents when scoped
    pub fn eval_intercept_gate_scoped(
        reason: &str,
        effective_ws: &Path,
        engine_root: &Path,
        username_opt: Option<&str>,
        agent_id_opt: Option<&str>,
    ) -> (String, Vec<Value>) {
        Self::eval_intercept_gate_scoped_with_limit(reason, effective_ws, engine_root, username_opt, agent_id_opt, 3)
    }

    pub fn eval_intercept_gate_scoped_with_limit(
        reason: &str,
        effective_ws: &Path,
        _engine_root: &Path,
        _username_opt: Option<&str>,
        agent_id_opt: Option<&str>,
        limit: usize,
    ) -> (String, Vec<Value>) {
        let q_words: Vec<String> = reason.to_lowercase()
            .split(|c: char| !c.is_alphanumeric() && c != '_' && c != '-')
            .filter(|s| s.len() >= 3)
            .map(|s| s.to_string())
            .collect();

        if q_words.is_empty() {
            return (String::new(), Vec::new());
        }

        let candidate_dirs = [
            effective_ws.join(".fl_brain").join("memories"),
            effective_ws.join(".fl_brain"),
            effective_ws.join(".flowork_brain").join("memories"),
            effective_ws.join(".flowork_brain"),
        ];

        let mut all_files = Vec::new();
        for dir in &candidate_dirs {
            if dir.exists() {
                Self::collect_md_files(dir, &mut all_files);
            }
        }
        all_files.sort();
        all_files.dedup();

        let mut scored_memories: Vec<(i32, String, Value)> = Vec::new();

        for file_path in all_files {
            let filename = file_path.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default();
            if filename.starts_with("incident_") {
                continue;
            }

            let content = match fs::read_to_string(&file_path) {
                Ok(c) => c,
                Err(_) => continue,
            };

            let (fm, body) = parse_markdown_frontmatter(&content);
            if fm.is_empty() {
                continue;
            }

            let category_val = fm.get("category").map(|s| s.trim().trim_matches('"').trim_matches('\'')).unwrap_or("");
            let source_val = fm.get("source").map(|s| s.trim().trim_matches('"').trim_matches('\'')).unwrap_or("");
            if category_val == "incident_remediation" || source_val == "circuit_breaker_crystallization" {
                continue;
            }

            let path_str = file_path.to_string_lossy().to_lowercase();
            let mut agent_boost = 0;

            // Strict Isolation Check if agent_id_opt is provided:
            if let Some(target_agent) = agent_id_opt {
                let target_agent_clean = target_agent.to_lowercase();
                if path_str.contains("/memories/") {
                    let parts: Vec<&str> = path_str.split("/memories/").collect();
                    if parts.len() > 1 {
                        let subpath = parts[1];
                        let sub_parts: Vec<&str> = subpath.split('/').collect();
                        if sub_parts.len() >= 2 {
                            let mem_agent = sub_parts[1];
                            if mem_agent != "shared" && mem_agent != target_agent_clean {
                                continue;
                            }
                            if mem_agent == target_agent_clean {
                                agent_boost = 30;
                            } else if mem_agent == "shared" {
                                agent_boost = 15;
                            }
                        }
                    }
                }
            }

            let raw_kw = fm.get("keywords").cloned().unwrap_or_default();
            let keywords_list: Vec<String> = raw_kw
                .trim_matches(|c| c == '[' || c == ']')
                .split(',')
                .map(|k| k.trim().trim_matches(|c| c == '"' || c == '\'').to_lowercase())
                .filter(|k| !k.is_empty())
                .collect();

            let title = fm.get("title").cloned().unwrap_or_else(|| {
                file_path.file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default()
            });
            let title_lower = title.to_lowercase();
            let id = fm.get("id").cloned().unwrap_or_else(|| {
                file_path.file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default()
            });
            let created_at = fm.get("created_at").cloned().unwrap_or_default();
            let category = fm.get("category").cloned().unwrap_or_else(|| "general".to_string());
            let status = fm.get("status").cloned().unwrap_or_else(|| "resolved".to_string());

            let mut match_score = 0;
            for kw in &keywords_list {
                for qw in &q_words {
                    if kw.contains(qw) || qw.contains(kw) {
                        match_score += 10;
                    }
                }
            }

            for qw in &q_words {
                if title_lower.contains(qw) {
                    match_score += 15;
                }
            }

            let body_lower = body.to_lowercase();
            for qw in &q_words {
                if body_lower.contains(qw) {
                    match_score += 2;
                }
            }

            if match_score >= 10 {
                let total_score = match_score + agent_boost;
                let val = json!({
                    "id": id,
                    "title": title,
                    "created_at": created_at,
                    "category": category,
                    "status": status,
                    "body": body,
                    "file_path": file_path.to_string_lossy()
                });
                scored_memories.push((total_score, created_at, val));
            }
        }

        if scored_memories.is_empty() {
            return (String::new(), Vec::new());
        }

        scored_memories.sort_by(|a, b| {
            b.0.cmp(&a.0).then_with(|| b.1.cmp(&a.1))
        });

        let top_memories: Vec<Value> = scored_memories.into_iter()
            .take(limit)
            .map(|(_, _, v)| v)
            .collect();

        let mut block = String::from("<SOVEREIGN_TOOL_INTERCEPT_GATE_INJECTION>\nSTATUS: UNLOCKED\n");
        block.push_str(&format!("REASON: {}\n", reason));
        block.push_str("TOP-RECALLED PAST VERIFIED SOLUTIONS:\n");
        for (idx, mem) in top_memories.iter().enumerate() {
            let m_id = mem.get("id").and_then(|v| v.as_str()).unwrap_or("unknown");
            let m_title = mem.get("title").and_then(|v| v.as_str()).unwrap_or("Untitled");
            let m_status = mem.get("status").and_then(|v| v.as_str()).unwrap_or("resolved");
            let m_body = mem.get("body").and_then(|v| v.as_str()).unwrap_or("");
            let snippet = m_body.lines().take(3).collect::<Vec<&str>>().join(" ");
            block.push_str(&format!("{}. [{}] \"{}\" ({})\n   Snippet: {}\n", idx + 1, m_id, m_title, m_status, snippet));
        }
        block.push_str("</SOVEREIGN_TOOL_INTERCEPT_GATE_INJECTION>\n");

        (block, top_memories)
    }

    fn collect_md_files(dir: &Path, out: &mut Vec<PathBuf>) {
        if let Ok(entries) = fs::read_dir(dir) {
            for entry in entries.flatten() {
                let p = entry.path();
                if p.is_dir() {
                    Self::collect_md_files(&p, out);
                } else if p.is_file() && p.extension().and_then(|e| e.to_str()) == Some("md") {
                    out.push(p);
                }
            }
        }
    }

    /// 4B. Sovereign Skill Radar
    pub fn eval_skill_radar(
        keywords_query: &str,
        local_skills: &[Value],
        remote_skills: &[Value],
    ) -> (String, Vec<Value>) {
        Self::eval_skill_radar_with_limit(keywords_query, local_skills, remote_skills, 3)
    }

    pub fn eval_skill_radar_with_limit(
        keywords_query: &str,
        local_skills: &[Value],
        remote_skills: &[Value],
        limit: usize,
    ) -> (String, Vec<Value>) {
        let q_lower = keywords_query.to_lowercase();
        let q_words: Vec<&str> = q_lower.split(|c: char| !c.is_alphanumeric() && c != '_' && c != '-').filter(|s| s.len() >= 2).collect();

        let mut candidates: Vec<(i32, Value)> = Vec::new();

        for s in local_skills {
            let mut skill_val = s.clone();
            skill_val["radar_source"] = json!("local");
            if let Some(score) = Self::score_skill(&q_lower, &q_words, s, 20) {
                candidates.push((score, skill_val));
            }
        }

        for s in remote_skills {
            let mut skill_val = s.clone();
            skill_val["radar_source"] = json!("remote");
            if let Some(score) = Self::score_skill(&q_lower, &q_words, s, 0) {
                let id = s.get("id").and_then(|v| v.as_str()).unwrap_or("");
                if !candidates.iter().any(|(_, c)| c.get("id").and_then(|v| v.as_str()) == Some(id)) {
                    candidates.push((score, skill_val));
                }
            }
        }

        if candidates.is_empty() || limit == 0 {
            return (String::new(), Vec::new());
        }

        candidates.sort_by(|a, b| b.0.cmp(&a.0));
        let top_candidates: Vec<Value> = candidates.into_iter().take(limit).map(|(_, v)| v).collect();

        let mut banner = String::from("<SOVEREIGN_SKILL_RADAR>\n[SOVEREIGN SKILL RADAR: JUST-IN-TIME CAPABILITY RECOMMENDATION]\n");
        banner.push_str("SKILL-FIRST SOVEREIGN DOCTRINE: Kamu didesain bukan menjadi AI sotoy yang hanya mengandalkan data training yang sudah usang, silakan pilih dan pin skill di bawah ini jika dirasa relevan dengan pekerjaanmu.\n");
        banner.push_str("PRIORITIZE pinning it in the next step: `skill_control(action: 'pin', skill_id: '...')`. ONLY disregard if the task is strictly trivial and completely unrelated.\n\n");
        for (i, sk) in top_candidates.iter().enumerate() {
            let id = sk.get("id").and_then(|v| v.as_str()).unwrap_or("");
            let name = sk.get("name").and_then(|v| v.as_str()).unwrap_or(id);
            let desc = sk.get("description").and_then(|v| v.as_str()).unwrap_or("");
            banner.push_str(&format!("{}. `{}` - {}: {}\n", i + 1, id, name, desc));
        }
        banner.push_str("</SOVEREIGN_SKILL_RADAR>\n");

        (banner, top_candidates)
    }

    fn score_skill(q_lower: &str, q_words: &[&str], s: &Value, boost: i32) -> Option<i32> {
        if let Some(ex_arr) = s.get("exclude_keywords").and_then(|v| v.as_array()) {
            let ex_strings: Vec<String> = ex_arr.iter().filter_map(|x| x.as_str().map(|s| s.to_string())).collect();
            for ex in ex_strings {
                let ex_clean = ex.to_lowercase();
                if !ex_clean.is_empty() && q_lower.contains(&ex_clean) {
                    return None;
                }
            }
        }

        let id = s.get("id").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
        let name = s.get("name").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
        let desc = s.get("description").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();

        let mut score = 0;
        if let Some(kws) = s.get("keywords").and_then(|v| v.as_array()) {
            for kw in kws.iter().filter_map(|v| v.as_str()) {
                let kw_l = kw.to_lowercase();
                if q_lower.contains(&kw_l) {
                    score += 15;
                }
                for qw in q_words {
                    if kw_l.contains(qw) || qw.contains(&kw_l) {
                        score += 10;
                    }
                }
            }
        }

        for qw in q_words {
            if id.contains(qw) { score += 20; }
            if name.contains(qw) { score += 15; }
            if desc.contains(qw) { score += 5; }
        }

        if score > 0 {
            Some(score + boost)
        } else {
            None
        }
    }

    /// 4C. Sovereign Tool Radar
    pub fn eval_tool_radar(
        keywords_query: &str,
        candidate_tools: &[Value],
    ) -> (String, Vec<Value>) {
        Self::eval_tool_radar_with_limit(keywords_query, candidate_tools, 3)
    }

    pub fn eval_tool_radar_with_limit(
        keywords_query: &str,
        candidate_tools: &[Value],
        limit: usize,
    ) -> (String, Vec<Value>) {
        let mut q_lower = keywords_query.to_lowercase();
        if q_lower.contains("panas") || q_lower.contains("suhu") {
            q_lower.push_str(" thermal cpu hardware diagnostics");
        }
        if q_lower.contains("kripto") {
            q_lower.push_str(" crypto bitcoin");
        }

        let q_words: Vec<&str> = q_lower.split(|c: char| !c.is_alphanumeric() && c != '_' && c != '-').filter(|s| s.len() >= 2).collect();

        let mut candidates: Vec<(i32, Value)> = Vec::new();

        for t in candidate_tools {
            if let Some(ex_arr) = t.get("exclude_keywords").and_then(|v| v.as_array()) {
                let ex_strings: Vec<String> = ex_arr.iter().filter_map(|x| x.as_str().map(|s| s.to_string())).collect();
                let mut disqualified = false;
                for ex in ex_strings {
                    let ex_clean = ex.to_lowercase();
                    if !ex_clean.is_empty() && q_lower.contains(&ex_clean) {
                        disqualified = true;
                        break;
                    }
                }
                if disqualified {
                    continue;
                }
            }

            let id = t.get("id").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
            let name = t.get("name").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
            let desc = t.get("description").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();

            let mut score = 0;
            if let Some(kws) = t.get("keywords").and_then(|v| v.as_array()) {
                for kw in kws.iter().filter_map(|v| v.as_str()) {
                    let kw_l = kw.to_lowercase();
                    if q_lower.contains(&kw_l) {
                        score += 15;
                    }
                    for qw in &q_words {
                        if kw_l.contains(qw) || qw.contains(&kw_l) {
                            score += 10;
                        }
                    }
                }
            }

            for qw in &q_words {
                if id.contains(qw) { score += 20; }
                if name.contains(qw) { score += 15; }
                if desc.contains(qw) { score += 5; }
            }

            if score >= 10 {
                candidates.push((score, t.clone()));
            }
        }

        if candidates.is_empty() || limit == 0 {
            return (String::new(), Vec::new());
        }

        candidates.sort_by(|a, b| b.0.cmp(&a.0));
        let top_candidates: Vec<Value> = candidates.into_iter().take(limit).map(|(_, v)| v).collect();

        let mut banner = String::from("<SOVEREIGN_TOOL_RADAR>\nSYSTEM MANDATE: DO NOT RELY ON GENERIC PRE-TRAINING INSTRUMENTS!\n");
        banner.push_str(&format!("{} rekomendasi tools yang berhubungan dengan pekerjaan kamu, silakan pin karna mungkin ini akan membantu:\n", limit));
        for t in &top_candidates {
            let id = t.get("id").and_then(|v| v.as_str()).unwrap_or("");
            let desc = t.get("description").and_then(|v| v.as_str()).unwrap_or("");
            banner.push_str(&format!("- `{}`: {}\n  Mount recommendation: search_tools(action: 'mount', tools: ['{}'])\n", id, desc, id));
        }
        banner.push_str("</SOVEREIGN_TOOL_RADAR>\n");

        (banner, top_candidates)
    }

    /// 4D. Sovereign App / Plugin Radar
    pub fn eval_app_radar(
        keywords_query: &str,
        candidate_apps: &[Value],
    ) -> (String, Vec<Value>) {
        Self::eval_app_radar_with_limit(keywords_query, candidate_apps, 3)
    }

    pub fn eval_app_radar_with_limit(
        keywords_query: &str,
        candidate_apps: &[Value],
        limit: usize,
    ) -> (String, Vec<Value>) {
        let q_lower = keywords_query.to_lowercase();
        let q_words: Vec<&str> = q_lower.split(|c: char| !c.is_alphanumeric() && c != '_' && c != '-').filter(|s| s.len() >= 2).collect();

        let mut candidates: Vec<(i32, Value)> = Vec::new();

        for app in candidate_apps {
            let id = app.get("id").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
            let name = app.get("name").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();
            let desc = app.get("description").and_then(|v| v.as_str()).unwrap_or("").to_lowercase();

            let mut score = 0;
            if let Some(kws) = app.get("keywords").and_then(|v| v.as_array()) {
                for kw in kws.iter().filter_map(|v| v.as_str()) {
                    let kw_l = kw.to_lowercase();
                    if q_lower.contains(&kw_l) {
                        score += 15;
                    }
                    for qw in &q_words {
                        if kw_l.contains(qw) || qw.contains(&kw_l) {
                            score += 10;
                        }
                    }
                }
            }

            for qw in &q_words {
                if id.contains(qw) { score += 20; }
                if name.contains(qw) { score += 15; }
                if desc.contains(qw) { score += 5; }
            }

            if score >= 10 {
                candidates.push((score, app.clone()));
            }
        }

        if candidates.is_empty() || limit == 0 {
            return (String::new(), Vec::new());
        }

        candidates.sort_by(|a, b| b.0.cmp(&a.0));
        let top_candidates: Vec<Value> = candidates.into_iter().take(limit).map(|(_, v)| v).collect();

        let mut banner = String::from("<RELEVANT_APPS>\nIni daftar apps yang relevan yang bisa kamu gunakan:\n");
        banner.push_str("* DOKTRIN KEDAULATAN: Apps (d/h Plugins) adalah aplikasi visual Flowork Canvas untuk operator manusia (berjalan di port 18000-18999), BUKAN instrumen eksekusi headless untuk AI.\n");
        for (i, app) in top_candidates.iter().enumerate() {
            let id = app.get("id").and_then(|v| v.as_str()).unwrap_or("");
            let desc = app.get("description").and_then(|v| v.as_str()).unwrap_or("");
            banner.push_str(&format!("{}. `{}` (/canvas/apps/{}): {}\n", i + 1, id, id, desc));
        }
        banner.push_str("</RELEVANT_APPS>\n");

        (banner, top_candidates)
    }

    /// 4E. Sovereign FL_INDEX Codebase Fingerprint Radar
    /// Scans workspace source files for `[FL_INDEX: ...]` headers and ranks matching files
    pub fn eval_fl_index_radar_with_limit(
        keywords_query: &str,
        effective_ws: &Path,
        limit: usize,
    ) -> (String, Vec<Value>) {
        if limit == 0 || keywords_query.trim().is_empty() {
            return (String::new(), Vec::new());
        }

        let q_lower = keywords_query.to_lowercase();
        let q_words: Vec<&str> = q_lower
            .split(|c: char| !c.is_alphanumeric() && c != '_' && c != '-')
            .filter(|s| s.len() >= 2)
            .collect();

        if q_words.is_empty() {
            return (String::new(), Vec::new());
        }

        let mut candidates: Vec<(i32, Value)> = Vec::new();

        // Walk workspace directory recursively, ignoring hidden/build folders
        fn walk_scan(
            dir: &Path,
            effective_ws: &Path,
            q_lower: &str,
            q_words: &[&str],
            candidates: &mut Vec<(i32, Value)>,
        ) {
            let entries = match fs::read_dir(dir) {
                Ok(e) => e,
                Err(_) => return,
            };

            for entry in entries.filter_map(|e| e.ok()) {
                let path = entry.path();
                let file_name = entry.file_name().to_string_lossy().to_string();

                if file_name.starts_with('.') || file_name == "target" || file_name == "node_modules" || file_name == "dist" || file_name == "build" || file_name == "vendor" {
                    continue;
                }

                if path.is_dir() {
                    walk_scan(&path, effective_ws, q_lower, q_words, candidates);
                } else if path.is_file() {
                    // Check extension
                    let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
                    let valid_ext = matches!(ext, "rs" | "ts" | "js" | "tsx" | "jsx" | "py" | "go" | "sh" | "json" | "md" | "toml" | "yaml" | "yml" | "html" | "css");
                    if !valid_ext {
                        continue;
                    }

                    // Read first 15 lines only for fast scanning
                    if let Ok(file) = fs::File::open(&path) {
                        use std::io::{BufRead, BufReader};
                        let reader = BufReader::new(file);
                        let mut fl_index_line = None;
                        for line_res in reader.lines().take(15) {
                            if let Ok(line) = line_res {
                                if line.contains("FL_INDEX:") {
                                    fl_index_line = Some(line);
                                    break;
                                }
                            }
                        }

                        if let Some(tag_line) = fl_index_line {
                            let tag_lower = tag_line.to_lowercase();
                            let rel_path = path.strip_prefix(effective_ws)
                                .unwrap_or(&path)
                                .to_string_lossy()
                                .to_string();

                            let mut score = 0;
                            // Check keywords match
                            for qw in q_words {
                                if tag_lower.contains(qw) {
                                    score += 20;
                                }
                                if rel_path.to_lowercase().contains(qw) {
                                    score += 10;
                                }
                            }

                            if q_lower.contains(&rel_path.to_lowercase()) {
                                score += 30;
                            }

                            if score > 0 {
                                // Extract metadata from tag line if possible
                                let purpose = if let Some(idx) = tag_line.find("purpose=\"") {
                                    let sub = &tag_line[idx + 9..];
                                    sub.split('"').next().unwrap_or("").to_string()
                                } else if let Some(idx) = tag_line.find("purpose='") {
                                    let sub = &tag_line[idx + 9..];
                                    sub.split('\'').next().unwrap_or("").to_string()
                                } else {
                                    String::new()
                                };

                                let keywords = if let Some(idx) = tag_line.find("keywords=\"") {
                                    let sub = &tag_line[idx + 10..];
                                    sub.split('"').next().unwrap_or("").to_string()
                                } else if let Some(idx) = tag_line.find("keywords='") {
                                    let sub = &tag_line[idx + 10..];
                                    sub.split('\'').next().unwrap_or("").to_string()
                                } else {
                                    String::new()
                                };

                                let item = serde_json::json!({
                                    "path": rel_path,
                                    "purpose": purpose,
                                    "keywords": keywords,
                                    "raw_tag": tag_line.trim()
                                });
                                candidates.push((score, item));
                            }
                        }
                    }
                }
            }
        }

        walk_scan(effective_ws, effective_ws, &q_lower, &q_words, &mut candidates);

        if candidates.is_empty() {
            return (String::new(), Vec::new());
        }

        candidates.sort_by(|a, b| b.0.cmp(&a.0));
        let top_candidates: Vec<Value> = candidates.into_iter().take(limit).map(|(_, v)| v).collect();

        let mut banner = String::from("<RELEVANT_CODE_FINGERPRINTS>\nBerikut berkas kode dengan semantic index (FL_INDEX) yang relevan dengan tugas aktif:\n");
        for (i, item) in top_candidates.iter().enumerate() {
            let path_str = item.get("path").and_then(|v| v.as_str()).unwrap_or("");
            let purpose = item.get("purpose").and_then(|v| v.as_str()).unwrap_or("");
            let kws = item.get("keywords").and_then(|v| v.as_str()).unwrap_or("");
            if !purpose.is_empty() {
                banner.push_str(&format!("{}. `{}` — {} (keywords: `{}`)\n", i + 1, path_str, purpose, kws));
            } else {
                banner.push_str(&format!("{}. `{}` (keywords: `{}`)\n", i + 1, path_str, kws));
            }
        }
        banner.push_str("</RELEVANT_CODE_FINGERPRINTS>\n");

        (banner, top_candidates)
    }

    /// Loads the canonical radar keywords list from disk or embedded compile-time fallback
    pub fn load_canonical_keywords(effective_ws: &Path, engine_root: &Path) -> String {
        const DEFAULT_KEYWORDS: &str = include_str!("../../prompts/core/keywords.md");

        let candidate_paths = [
            effective_ws.join("prompts/core/keywords.md"),
            engine_root.join("prompts/core/keywords.md"),
            effective_ws.parent().map(|p| p.join("prompts/core/keywords.md")).unwrap_or_default(),
            engine_root.parent().map(|p| p.join("prompts/core/keywords.md")).unwrap_or_default(),
        ];

        for path in &candidate_paths {
            if path.exists() {
                if let Ok(content) = fs::read_to_string(path) {
                    let trimmed = content.trim();
                    if !trimmed.is_empty() {
                        return trimmed.to_string();
                    }
                }
            }
        }

        DEFAULT_KEYWORDS.trim().to_string()
    }

    /// Evaluates the complete 4-Dimensional Auto-JIT Advisor:
    /// Dynamically loads limits and options from system/config.json (if present):
    /// 1. Tools: Configurable (default 3), tier-filtered, role-filtered via manifest
    /// 2. Skills: Configurable (default 3) with anti-sotoy doctrine
    /// 3. Apps: Configurable (default 3) with visual Canvas doctrine
    /// 4. .fl_brain: Configurable (default 5), cross-agent within the same workspace!
    pub fn eval_4d_auto_jit_advisor(
        search_text: &str,
        effective_ws: &Path,
        engine_root: &Path,
        user_tier: Option<&str>,
        candidate_tools: &[Value],
        local_skills: &[Value],
        remote_skills: &[Value],
        candidate_apps: &[Value],
    ) -> Option<String> {
        // Read dynamic configuration from system/config.json
        let config_path = effective_ws.join("system").join("config.json");
        let alt_config_path = engine_root.join("system").join("config.json");
        let config_val: Option<Value> = fs::read_to_string(&config_path)
            .or_else(|_| fs::read_to_string(&alt_config_path))
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok());

        let (jit_enabled, max_tools, max_skills, max_apps, max_brain, max_file_histories, max_fl_index, show_canonical) = if let Some(ref cfg) = config_val {
            let jit = cfg.get("jit_advisor");
            let enabled = jit.and_then(|j| j.get("enabled")).and_then(|v| v.as_bool()).unwrap_or(true);
            let mt = jit.and_then(|j| j.get("max_tools")).and_then(|v| v.as_u64()).unwrap_or(3) as usize;
            let ms = jit.and_then(|j| j.get("max_skills")).and_then(|v| v.as_u64()).unwrap_or(3) as usize;
            let ma = jit.and_then(|j| j.get("max_apps")).and_then(|v| v.as_u64()).unwrap_or(3) as usize;
            let mb = jit.and_then(|j| j.get("max_brain_memories")).and_then(|v| v.as_u64()).unwrap_or(5) as usize;
            let mfh = jit.and_then(|j| j.get("max_file_histories")).and_then(|v| v.as_u64()).unwrap_or(3) as usize;
            let mfi = jit.and_then(|j| j.get("max_fl_index")).and_then(|v| v.as_u64()).unwrap_or(3) as usize;
            let sc = jit.and_then(|j| j.get("show_canonical_keywords")).and_then(|v| v.as_bool()).unwrap_or(true);
            (enabled, mt, ms, ma, mb, mfh, mfi, sc)
        } else {
            (true, 3, 3, 3, 5, 3, 3, true)
        };

        if !jit_enabled {
            return None;
        }

        let is_free_tier = user_tier.map(|t| t.to_lowercase() == "free").unwrap_or(false);

        let filtered_tools: Vec<Value> = if is_free_tier {
            candidate_tools.iter().filter(|t| {
                let is_pro = t.get("tier").and_then(|v| v.as_str()).map(|s| s.to_lowercase() == "pro" || s.to_lowercase() == "enterprise").unwrap_or(false)
                    || t.get("pro").and_then(|v| v.as_bool()).unwrap_or(false);
                !is_pro
            }).cloned().collect()
        } else {
            candidate_tools.to_vec()
        };

        let (tool_banner, _) = Self::eval_tool_radar_with_limit(search_text, &filtered_tools, max_tools);
        let (skill_banner, _) = Self::eval_skill_radar_with_limit(search_text, local_skills, remote_skills, max_skills);
        let (app_banner, _) = Self::eval_app_radar_with_limit(search_text, candidate_apps, max_apps);
        let (fl_index_banner, _) = Self::eval_fl_index_radar_with_limit(search_text, effective_ws, max_fl_index);

        let (_, brain_memories) = Self::eval_intercept_gate_scoped_with_limit(
            search_text,
            effective_ws,
            engine_root,
            None,
            None,
            max_brain,
        );

        // Scan .fl_brain/file_histories (Dimension 5: File Historical Timeline)
        let mut matched_histories: Vec<(String, String)> = Vec::new();
        let file_histories_dir = effective_ws.join(".fl_brain").join("file_histories");
        if file_histories_dir.is_dir() {
            if let Ok(entries) = fs::read_dir(&file_histories_dir) {
                for entry in entries.filter_map(|e| e.ok()) {
                    let path = entry.path();
                    if path.is_file() {
                        let stem = path.file_stem().and_then(|s| s.to_str()).unwrap_or("");
                        let target_repr = stem.replace("__", "/");
                        let filename_only = Path::new(&target_repr)
                            .file_name()
                            .and_then(|s| s.to_str())
                            .unwrap_or(&target_repr);

                        if (!target_repr.is_empty() && search_text.contains(&target_repr))
                            || (!filename_only.is_empty() && filename_only.len() >= 3 && search_text.contains(filename_only))
                        {
                            if let Ok(content) = fs::read_to_string(&path) {
                                let recent_lines: Vec<&str> = content.lines().rev().take(4).collect();
                                let mut reversed_recent = recent_lines;
                                reversed_recent.reverse();
                                let snippet = reversed_recent.join("\n   ");
                                matched_histories.push((target_repr, snippet));
                                if matched_histories.len() >= max_file_histories {
                                    break;
                                }
                            }
                        }
                    }
                }
            }
        }

        let has_brain = !brain_memories.is_empty();
        let has_tools = !tool_banner.is_empty();
        let has_skills = !skill_banner.is_empty();
        let has_apps = !app_banner.is_empty();
        let has_fl_index = !fl_index_banner.is_empty();
        let has_file_history = !matched_histories.is_empty();

        if !has_tools && !has_skills && !has_apps && !has_brain && !has_file_history && !has_fl_index {
            return None;
        }

        let mut block = String::from("\n\n<SOVEREIGN_AUTO_JIT_ADVISOR>\n<!-- [JIT ADVISOR: EPHEMERAL GUIDANCE FOR ACTIVE LOOP] -->\n\n");

        if show_canonical {
            let canonical_kw = Self::load_canonical_keywords(effective_ws, engine_root);
            if !canonical_kw.is_empty() {
                block.push_str("<SOVEREIGN_CANONICAL_KEYWORDS>\n");
                block.push_str(&canonical_kw);
                block.push_str("\n</SOVEREIGN_CANONICAL_KEYWORDS>\n\n");
            }
        }

        if has_tools {
            block.push_str(&tool_banner);
            block.push('\n');
        }

        if has_skills {
            block.push_str(&skill_banner);
            block.push('\n');
        }

        if has_apps {
            block.push_str(&app_banner);
            block.push('\n');
        }

        if has_brain {
            block.push_str("<HISTORICAL_BRAIN_MEMORIES>\n");
            block.push_str("Ini riwayat masa lalu yang berhubungan dengan topik yang sedang kamu tangani:\n");
            for (idx, mem) in brain_memories.iter().enumerate() {
                let m_id = mem.get("id").and_then(|v| v.as_str()).unwrap_or("unknown");
                let m_title = mem.get("title").and_then(|v| v.as_str()).unwrap_or("Untitled");
                let m_status = mem.get("status").and_then(|v| v.as_str()).unwrap_or("resolved");
                let m_body = mem.get("body").and_then(|v| v.as_str()).unwrap_or("");
                let snippet = m_body.lines().take(2).collect::<Vec<&str>>().join(" ");
                block.push_str(&format!("{}. [{}] \"{}\" ({})\n   Snippet: {}\n", idx + 1, m_id, m_title, m_status, snippet));
            }
            block.push_str("</HISTORICAL_BRAIN_MEMORIES>\n\n");
        }

        if has_fl_index {
            block.push_str(&fl_index_banner);
            block.push('\n');
        }

        if has_file_history {
            block.push_str("<FILE_HISTORICAL_TIMELINE>\n");
            block.push_str("Riwayat masa lalu terkait berkas yang sedang disentuh/dianalisis:\n");
            for (file_name, history) in matched_histories {
                block.push_str(&format!("📄 Berkas `{}`:\n   {}\n", file_name, history));
            }
            block.push_str("</FILE_HISTORICAL_TIMELINE>\n");
        }

        block.push_str("</SOVEREIGN_AUTO_JIT_ADVISOR>\n");
        Some(block)
    }

    /// 5. Trigger 07 & 08: Plan & Architecture Contract
    /// Injected when planning mode (/plan) or complex architecture refactoring is requested.
    pub fn eval_plan_contract(search_text: &str, is_plan_context: bool) -> Option<String> {
        if is_plan_context
            || search_text.starts_with("/plan")
            || search_text.contains("/plan ")
            || search_text.contains("rancang arsitektur")
            || search_text.contains("cetak biru arsitektur")
        {
            Self::load_trigger_file("TRIGGER_PLANNING_MODE_MANDATE.md")
        } else {
            None
        }
    }

    /// 6. Trigger 14: Specialized Child Subagent Mandate
    /// Injected when the active agent session represents a dispatched child worker.
    pub fn eval_child_subagent(is_child_subagent: bool) -> Option<String> {
        if is_child_subagent {
            Some(crate::prompt_seal::PromptSeal::get_subagent_worker_mandate())
        } else {
            None
        }
    }

    /// 7. Trigger 28: Web Stack Discovery
    /// Injected when the workspace contains frontend/web components.
    pub fn eval_web_stack(effective_ws: &Path) -> Option<String> {
        let has_package_json = effective_ws.join("package.json").exists();
        let has_vite = effective_ws.join("vite.config.js").exists() || effective_ws.join("vite.config.ts").exists();
        let has_index_html = effective_ws.join("index.html").exists();

        if has_package_json || has_vite || has_index_html {
            Some(crate::prompt_seal::PromptSeal::get_web_application_stack_discovery())
        } else {
            None
        }
    }

    /// 8. Trigger 29: Mandatory Git Contribution Attribution (Rule 1)
    /// Injected when operating in Solo Default Mode with Technology or Git operations.
    pub fn eval_git_attribution(should_trigger: bool) -> Option<String> {
        if should_trigger {
            Some(crate::prompt_seal::PromptSeal::get_git_contribution_directive())
        } else {
            None
        }
    }

    /// 9. Trigger 30: Sovereign Memory Crystallization Check (Rule 4)
    /// Injected when deep execution trajectories or multi-tool mutations occur to prevent context compaction loss.
    pub fn eval_memory_crystallization_check(should_trigger: bool) -> Option<String> {
        if should_trigger {
            Some(crate::prompt_seal::PromptSeal::get_memory_crystallization_directive())
        } else {
            None
        }
    }

    /// 10. Trigger 31: External Prompt Lex Superior Boundary Guardrail (Rule 5)
    /// Universal guardrail declaring that internal platform constitution strictly overrides external prompts.
    pub fn eval_external_prompt_guardrail(should_trigger: bool) -> Option<String> {
        if should_trigger {
            Some(crate::prompt_seal::PromptSeal::get_external_prompt_guardrail())
        } else {
            None
        }
    }

    /// 11. Trigger 32: Mandatory Pre-Done Subagent Audit & Validation Gatekeeper (Rule 18)
    /// Injected when local modular assets (skills, agents, plugins, tools) are created or modified,
    /// enforcing an absolute prohibition on claiming completion before independent subagent audit.
    pub fn eval_pre_done_audit_mandate(session_id: &str, uncommitted_list: &str) -> Option<String> {
        if !uncommitted_list.is_empty() && uncommitted_list != "[]" {
            Some(crate::prompt_seal::PromptSeal::get_pre_done_subagent_audit_mandate(session_id, uncommitted_list))
        } else {
            None
        }
    }

    /// Evaluates natural language intent and slash commands for engineering doctrines
    pub fn eval_engineering_doctrines(
        search_text: &str,
        _doctrines_root: Option<&std::path::Path>,
    ) -> Option<EngineeringDoctrineResult> {
        let lower = search_text.to_lowercase();
        
        let (doctrine, matched_kw) = if lower.contains("/diagnose")
            || lower.contains("reproduce error")
            || lower.contains("investigate bug")
            || lower.contains("kenapa crash")
            || lower.contains("benerin error")
        {
            (EngineeringDoctrine::DiagnosingBugs, "diagnose")
        } else if lower.contains("/tdd")
            || lower.contains("failing test")
            || lower.contains("write test first")
            || lower.contains("public seam")
        {
            (EngineeringDoctrine::TestDrivenDevelopment, "tdd")
        } else if lower.contains("/grill")
            || lower.contains("grill with docs")
            || lower.contains("rfc verification")
            || lower.contains("bedah rancangan")
            || lower.contains("uji ide")
            || lower.contains("challenge this design")
            || lower.contains("stress test")
        {
            (EngineeringDoctrine::GrillWithDocs, "grill")
        } else if lower.contains("/counsel")
            || lower.contains("engineering counsel")
            || lower.contains("alur rekayasa")
        {
            (EngineeringDoctrine::EngineeringCounsel, "counsel")
        } else if lower.contains("/deep-modules") || lower.contains("deep modules") {
            (EngineeringDoctrine::DeepModules, "deep-modules")
        } else if lower.contains("/domain-modeling") || lower.contains("domain modeling") || lower.contains("adr") {
            (EngineeringDoctrine::DomainModelingAdr, "domain-modeling")
        } else if lower.contains("/spec") || lower.contains("spec and triage") || lower.contains("triage") {
            (EngineeringDoctrine::SpecAndTriage, "spec")
        } else if lower.contains("/handoff") || lower.contains("handoff and prototype") {
            (EngineeringDoctrine::HandoffAndPrototype, "handoff")
        } else if lower.contains("/git-guardrails") || lower.contains("git guardrails") {
            (EngineeringDoctrine::GitGuardrails, "git-guardrails")
        } else if lower.contains("/two-axis") || lower.contains("two axis review") {
            (EngineeringDoctrine::TwoAxisReview, "two-axis")
        } else if lower.contains("/reverse-engineering") || lower.contains("reverse engineering") {
            (EngineeringDoctrine::ReverseEngineering, "reverse-engineering")
        } else if lower.contains("/wayfinding") || lower.contains("wayfinding") {
            (EngineeringDoctrine::Wayfinding, "wayfinding")
        } else if lower.contains("/primary-source") || lower.contains("primary source") {
            (EngineeringDoctrine::PrimarySourceResearch, "primary-source")
        } else {
            return None;
        };

        let prompt_injection = format!(
            "<ACTIVE_ENGINEERING_DOCTRINE id=\"{}\">\nTITLE: {}\nDoktrin ini wajib dipatuhi secara ketat.\n</ACTIVE_ENGINEERING_DOCTRINE>",
            doctrine.id(), doctrine.title()
        );

        Some(EngineeringDoctrineResult {
            doctrine,
            confidence_score: 95,
            matched_trigger: matched_kw.to_string(),
            prompt_injection,
        })
    }

    /// Evaluates multi-signal Category Triggers (CAT-001 through CAT-015)
    pub fn eval_category_triggers(
        search_text: &str,
        agent_category_hint: Option<&str>,
        workspace_dir: Option<&Path>,
        mounted_tools: Option<&HashSet<String>>,
    ) -> CategoryTriggerEvaluation {
        SovereignCategoryTrigger::evaluate(search_text, agent_category_hint, workspace_dir, mounted_tools)
    }
}

/// Helper to parse YAML frontmatter map and markdown body
pub fn parse_markdown_frontmatter(content: &str) -> (HashMap<String, String>, String) {
    let mut map = HashMap::new();
    let trimmed = content.trim_start();
    if !trimmed.starts_with("---") {
        return (map, content.to_string());
    }
    let after_first = &trimmed[3..];
    if let Some(end_idx) = after_first.find("---") {
        let frontmatter_str = &after_first[..end_idx];
        let body_str = after_first[end_idx + 3..].trim_start();
        for line in frontmatter_str.lines() {
            let l = line.trim();
            if let Some(colon_pos) = l.find(':') {
                let key = l[..colon_pos].trim().to_string();
                let val = l[colon_pos + 1..].trim().trim_matches('"').trim_matches('\'').to_string();
                map.insert(key, val);
            }
        }
        (map, body_str.to_string())
    } else {
        (map, content.to_string())
    }
}

// ============================================================================
// SOVEREIGN CATEGORY TRIGGER ENGINE (CAT-001 THROUGH CAT-015)
// Converts the 15 Professional Categories into First-Class Kernel Triggers
// Co-authored-by: Flowork OS <agent@floworkos.com>
// ============================================================================

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
pub struct CategoryTriggerMatch {
    pub category_id: String,       // e.g. "CAT-001" through "CAT-015"
    pub category_slug: String,     // e.g. "healthcare", "technology", etc.
    pub category_title: String,    // e.g. "Technology & Software Engineering"
    pub score: u32,
    pub matched_signals: Vec<String>,
    pub is_primary: bool,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
pub struct CategoryTriggerEvaluation {
    pub primary_category_id: String,
    pub primary_category_slug: String,
    pub primary_category_title: String,
    pub matches: Vec<CategoryTriggerMatch>,
}

impl CategoryTriggerEvaluation {
    /// Normalizes input string to canonical format for lookup (lowercase, underscores)
    pub fn normalize_key(input: &str) -> String {
        input.trim().to_lowercase().replace(['-', ' '], "_")
    }

    /// Checks if a given category ID (e.g. "CAT-005", "cat_005") or slug (e.g. "technology") was triggered
    pub fn is_triggered(&self, input: &str) -> bool {
        let norm = Self::normalize_key(input);
        self.matches.iter().any(|m| {
            m.category_id.eq_ignore_ascii_case(input.trim())
                || m.category_slug.eq_ignore_ascii_case(input.trim())
                || Self::normalize_key(&m.category_id) == norm
                || Self::normalize_key(&m.category_slug) == norm
                || (norm == "cat_5" && m.category_id == "CAT-005")
        })
    }

    /// Checks if a specific canonical category ID (e.g. "CAT-001" .. "CAT-015") was triggered
    pub fn has_category_id(&self, cat_id: &str) -> bool {
        let norm = Self::normalize_key(cat_id);
        self.matches.iter().any(|m| {
            m.category_id.eq_ignore_ascii_case(cat_id.trim())
                || Self::normalize_key(&m.category_id) == norm
        })
    }

    /// Checks if a specific AgentCategory enum variant was triggered
    pub fn has_category(&self, cat: AgentCategory) -> bool {
        self.has_category_id(cat.id())
    }

    /// Returns primary category ID (e.g. "CAT-005")
    pub fn primary_id(&self) -> &str {
        &self.primary_category_id
    }

    /// Returns primary category slug (e.g. "technology")
    pub fn primary_slug(&self) -> &str {
        &self.primary_category_slug
    }

    /// Returns primary category title
    pub fn primary_title(&self) -> &str {
        &self.primary_category_title
    }

    /// Gets detailed match entry for a category ID or slug
    pub fn get_match(&self, cat_id_or_slug: &str) -> Option<&CategoryTriggerMatch> {
        let norm = Self::normalize_key(cat_id_or_slug);
        self.matches.iter().find(|m| {
            m.category_id.eq_ignore_ascii_case(cat_id_or_slug.trim())
                || m.category_slug.eq_ignore_ascii_case(cat_id_or_slug.trim())
                || Self::normalize_key(&m.category_id) == norm
                || Self::normalize_key(&m.category_slug) == norm
        })
    }
}

/// Sovereign Category Trigger Engine
/// Evaluates multi-signal criteria (agent declaration, domain keywords, exclusions, workspace file patterns, mounted tools)
/// to detect and activate Category Triggers (CAT-001 through CAT-026).
pub struct SovereignCategoryTrigger;

impl SovereignCategoryTrigger {
    /// Evaluates category triggers against search text, optional agent hint, workspace, and tools
    pub fn evaluate(
        search_text: &str,
        agent_category_hint: Option<&str>,
        workspace_dir: Option<&Path>,
        mounted_tools: Option<&HashSet<String>>,
    ) -> CategoryTriggerEvaluation {
        let lower_text = search_text.to_lowercase();
        let words: Vec<&str> = lower_text
            .split(|c: char| !c.is_alphanumeric() && c != '_' && c != '-')
            .filter(|s| !s.is_empty())
            .collect();

        let ws_files = workspace_dir.map(Self::sample_workspace_files).unwrap_or_default();

        let mut matches = Vec::new();

        for &cat in AgentCategory::all() {
            let mut score = 0u32;
            let mut signals = Vec::new();

            // 1. Agent Declaration Hint (+100)
            if let Some(hint) = agent_category_hint {
                let hint_trim = hint.trim();
                let hint_cat = AgentCategory::from_str_loose(hint_trim);
                if hint_cat == cat || hint_trim.eq_ignore_ascii_case(cat.id()) || hint_trim.eq_ignore_ascii_case(cat.slug()) {
                    score += 100;
                    signals.push(format!("agent_declaration: '{}'", hint_trim));
                }
            }

            // 2. Domain Keywords & Negative Exclusions (+10 per matched keyword)
            let (keywords, exclusions) = Self::category_keywords(cat);
            let mut is_excluded = false;
            for ex in exclusions {
                let ex_lower = ex.to_lowercase();
                if lower_text.contains(&ex_lower) {
                    is_excluded = true;
                    break;
                }
            }

            if !is_excluded {
                let mut kw_hits = 0;
                for kw in keywords {
                    let kw_lower = kw.to_lowercase();
                    let matched = if kw_lower.contains(' ') {
                        lower_text.contains(&kw_lower)
                    } else if kw_lower.len() <= 3 {
                        words.iter().any(|w| *w == kw_lower)
                    } else {
                        lower_text.contains(&kw_lower)
                    };

                    if matched {
                        kw_hits += 1;
                        signals.push(format!("keyword: '{}'", kw));
                    }
                }
                if kw_hits > 0 {
                    score += kw_hits * 10;
                }
            }

            // 3. Workspace File Patterns (+15 per pattern)
            if !ws_files.is_empty() {
                for pat in Self::category_file_patterns(cat) {
                    if Self::matches_file_pattern(pat, &ws_files) {
                        score += 15;
                        signals.push(format!("file_pattern: '{}'", pat));
                    }
                }
            }

            // 4. Mounted Tools (+20 per tool)
            if let Some(tools) = mounted_tools {
                for tool in Self::category_tools(cat) {
                    if tools.contains(*tool) {
                        score += 20;
                        signals.push(format!("mounted_tool: '{}'", tool));
                    }
                }
            }

            if score >= 10 {
                matches.push(CategoryTriggerMatch {
                    category_id: cat.id().to_string(),
                    category_slug: cat.slug().to_string(),
                    category_title: cat.title().to_string(),
                    score,
                    matched_signals: signals,
                    is_primary: false,
                });
            }
        }

        if matches.is_empty() {
            // Default fallback: CAT-015 (Core)
            let core = AgentCategory::Core;
            return CategoryTriggerEvaluation {
                primary_category_id: core.id().to_string(),
                primary_category_slug: core.slug().to_string(),
                primary_category_title: core.title().to_string(),
                matches: vec![CategoryTriggerMatch {
                    category_id: core.id().to_string(),
                    category_slug: core.slug().to_string(),
                    category_title: core.title().to_string(),
                    score: 1,
                    matched_signals: vec!["default_fallback".to_string()],
                    is_primary: true,
                }],
            };
        }

        matches.sort_by(|a, b| b.score.cmp(&a.score));
        matches[0].is_primary = true;

        let primary_id = matches[0].category_id.clone();
        let primary_slug = matches[0].category_slug.clone();
        let primary_title = matches[0].category_title.clone();

        CategoryTriggerEvaluation {
            primary_category_id: primary_id,
            primary_category_slug: primary_slug,
            primary_category_title: primary_title,
            matches,
        }
    }

    /// Convenient shorthand for evaluating search text alone
    pub fn evaluate_text(search_text: &str) -> CategoryTriggerEvaluation {
        Self::evaluate(search_text, None, None, None)
    }

    /// Evaluates if a given category is triggered by search text
    pub fn is_category_triggered(search_text: &str, category_id_or_slug: &str) -> bool {
        let eval = Self::evaluate_text(search_text);
        eval.is_triggered(category_id_or_slug)
    }

    /// Returns primary category ID for search text with optional agent hint
    pub fn primary_category_id(search_text: &str, agent_category_hint: Option<&str>) -> String {
        let eval = Self::evaluate(search_text, agent_category_hint, None, None);
        eval.primary_category_id
    }

    fn category_keywords(cat: AgentCategory) -> (&'static [&'static str], &'static [&'static str]) {
        match cat {
            AgentCategory::Healthcare => (
                &[
                    "health", "healthcare", "medical", "medicine", "doctor", "clinical", "patient",
                    "disease", "treatment", "symptom", "pharma", "pharmacy", "drug", "hospital",
                    "diagnosis", "surgery", "therapy", "nutrition", "dietitian", "biomedical",
                    "kesehatan", "medis", "dokter", "klinik", "klinis", "pasien", "penyakit",
                    "gejala", "obat", "farmasi", "rumah sakit", "nutrisi", "gizi", "pemeriksaan kesehatan"
                ],
                &["financial health", "health check", "battery health"]
            ),
            AgentCategory::Psychology => (
                &[
                    "psychology", "mental health", "counseling", "psychiatrist", "psychologist",
                    "cbt", "trauma", "mindset", "anxiety", "depression", "emotional", "mindfulness",
                    "burnout", "coping mechanism", "behavioral health", "psikologi", "therapy",
                    "kesehatan mental", "konseling", "psikiater", "psikolog", "kecemasan", "depresi",
                    "emosional", "kejenuhan"
                ],
                &[]
            ),
            AgentCategory::Legal => (
                &[
                    "legal", "contract", "lawyer", "attorney", "compliance", "lawsuit", "nda",
                    "tos", "terms of service", "privacy policy", "gdpr", "regulations",
                    "intellectual property", "trademark", "patent", "copyright infringement",
                    "clause", "litigation", "arbitration", "jurisdiction", "statute",
                    "hukum", "kontrak", "pengacara", "kepatuhan", "gugatan", "perjanjian",
                    "syarat dan ketentuan", "kebijakan privasi", "hak cipta", "merek dagang",
                    "paten", "klausul", "litigasi", "peraturan perundang"
                ],
                &[]
            ),
            AgentCategory::Education => (
                &[
                    "education", "learning", "curriculum", "syllabus", "course", "lesson",
                    "teaching", "pedagogy", "student", "homework", "exam", "quiz", "lecture",
                    "tutor", "classroom", "academy", "training material", "edtech", "study guide",
                    "edukasi", "pendidikan", "kurikulum", "silabus", "pembelajaran", "kursus",
                    "pelajaran", "mengajar", "siswa", "murid", "ujian", "pr", "kuliah", "bimbel", "akademi"
                ],
                &[]
            ),
            AgentCategory::Technology => (
                &[
                    "code", "coding", "software", "developer", "programming", "rust", "python",
                    "typescript", "javascript", "golang", "c++", "compiler", "git", "github",
                    "bug", "debugging", "docker", "kubernetes", "api", "database", "sql",
                    "backend", "frontend", "refactor", "linux", "terminal", "cargo", "npm",
                    "pip", "server", "devops", "qa", "test", "pemrograman", "koding",
                    "perangkat lunak", "pengembang", "basis data", "skrip", "perbaikan bug", "peladen"
                ],
                &[
                    "css", "styling", "ui/ux", "uiux", "figma", "wireframe", "color palette",
                    "design tokens", "tata letak", "palet warna", "desain grafis", "rancangan visual",
                    "glassmorphism", "animasi css", "warna tema", "gui layout", "visual theme"
                ]
            ),
            AgentCategory::Finance => (
                &[
                    "finance", "financial", "accounting", "ledger", "balance sheet", "tax",
                    "audit", "trading", "stock", "forex", "crypto", "bitcoin", "ethereum",
                    "portfolio", "dividend", "equity", "hedge fund", "algorithmic trading",
                    "candlestick", "mt5", "profit loss", "pnl", "yield", "keuangan", "akuntansi",
                    "buku besar", "neraca", "pajak", "saham", "reksadana", "cuan", "laba rugi", "dividen"
                ],
                &[]
            ),
            AgentCategory::Business => (
                &[
                    "business", "management", "strategy", "startup", "pitchdeck", "executive summary",
                    "business plan", "revenue model", "kpi", "okr", "market analysis", "swot",
                    "business development", "bizdev", "roi", "shareholder", "b2b", "b2c",
                    "enterprise", "roadmap", "bisnis", "manajemen", "rencana bisnis",
                    "analisis pasar", "pemegang saham", "pengembangan bisnis"
                ],
                &[]
            ),
            AgentCategory::Marketing => (
                &[
                    "marketing", "seo", "organic traffic", "content marketing", "funnel",
                    "copywriting", "lead generation", "inbound", "backlink", "keyword research",
                    "email newsletter", "blog post", "social media growth", "branding",
                    "growth hacking", "cta", "customer journey", "pemasaran", "konten pemasaran",
                    "lalu lintas organik", "pertumbuhan medsos", "surat berita", "backlinks"
                ],
                &["paid ads", "google ads", "facebook ads", "meta ads", "ppc", "media buying"]
            ),
            AgentCategory::Advertising => (
                &[
                    "advertising", "paid ads", "ad campaign", "ppc", "google ads", "meta ads",
                    "facebook ads", "tiktok ads", "media buying", "roas", "cpc", "cpm",
                    "ctr", "ad spend", "sponsored post", "retargeting", "ad creative",
                    "periklanan", "iklan berbayar", "kampanye iklan", "biaya iklan", "pembelian media"
                ],
                &[]
            ),
            AgentCategory::MediaCreative => (
                &[
                    "media", "creative", "audio", "video", "youtube", "podcast", "sound",
                    "music", "editing", "video editor", "voiceover", "thumbnail", "premiere pro",
                    "davinci", "film", "vlog", "recording", "broadcast", "streaming",
                    "kreatif", "suara", "musik", "penyuntingan video", "rekaman", "siaran", "sulih suara"
                ],
                &[]
            ),
            AgentCategory::Design => (
                &[
                    "design", "ui", "ux", "uiux", "figma", "wireframe", "prototype",
                    "graphic design", "typography", "color palette", "css", "tailwind",
                    "layout", "visual identity", "iconography", "vector", "illustration",
                    "svg", "photoshop", "art", "desain", "rancangan visual", "desain grafis",
                    "tata letak", "palet warna", "vektor", "ilustrasi",
                    "gui", "antarmuka", "tampilan", "glassmorphism", "modal layout", "button style"
                ],
                &[
                    "kernel", "rust compiler", "cargo build", "backend api", "database migration",
                    "sql query", "kubernetes", "dockerfile"
                ]
            ),
            AgentCategory::HumanResources => (
                &[
                    "human resources", "hr", "recruitment", "recruiting", "hiring", "talent",
                    "interview questions", "resume", "cv", "job description", "onboarding",
                    "payroll", "employee performance", "workplace culture", "staffing",
                    "headhunting", "compensation", "sumber daya manusia", "sdm", "perekrutan",
                    "lowongan kerja", "wawancara kerja", "gaji", "kinerja karyawan", "budaya kerja"
                ],
                &[]
            ),
            AgentCategory::ScienceResearch => (
                &[
                    "science", "research", "scientific", "data science", "experiment",
                    "hypothesis", "laboratory", "physics", "chemistry", "biology",
                    "mathematics", "statistics", "dataset", "machine learning", "deep learning",
                    "neural network", "paper", "arxiv", "peer review", "sains", "penelitian",
                    "riset", "eksperimen", "hipotesis", "laboratorium", "fisika", "kimia",
                    "biologi", "matematika", "statistika", "jurnal ilmiah"
                ],
                &[]
            ),
            AgentCategory::AutomationAdmin => (
                &[
                    "automation", "virtual assistant", "va", "admin", "data entry",
                    "web scraping", "scraper", "crawler", "excel formula", "spreadsheet",
                    "scheduling", "zapier", "make.com", "automate task", "macro",
                    "batch processing", "workflow automation", "otomasi", "asisten virtual",
                    "entri data", "lembar kerja", "penjadwalan", "otomatisasi tugas", "pemrosesan berkas"
                ],
                &[]
            ),
            AgentCategory::Core => (
                &[
                    "core", "agent architecture", "orchestrator", "flowork", "supervisor",
                    "meta runtime", "protocol", "sovereign", "lifecycle", "root supervisor",
                    "sistem inti", "arsitektur agen", "orkestrator", "tata kelola sistem", "tata kelola"
                ],
                &[]
            ),
            AgentCategory::ArtsMusicPoetry => (
                &[
                    "poetry", "poem", "poet", "rhyme", "meter", "lyrics", "lyricist", "songwriter",
                    "composition", "chord", "melody", "harmony", "ballad", "verse", "chorus",
                    "sonnet", "haiku", "literature", "fine art", "sculpture", "painting", "composer",
                    "puisi", "sajak", "penyair", "lirik lagu", "komposer", "tangga nada", "bait",
                    "rima", "sastra", "seni murni", "seniman", "seni lukis", "nada"
                ],
                &[]
            ),
            AgentCategory::MetaphysicsFengShui => (
                &[
                    "feng shui", "fengshui", "geomancy", "bazi", "four pillars", "yin yang",
                    "wu xing", "five elements", "i ching", "luopan", "luo pan", "xuan kong", "flying stars",
                    "vastu", "vastu shastra", "chi", "qi", "astrology", "horoscope", "tian di ren",
                    "sha chi", "pranata mangsa", "tajul muluk", "primbon", "metafisika",
                    "tata ruang kosmis", "energi ruang", "geomansi"
                ],
                &[]
            ),
            AgentCategory::ArchitectureSpatial => (
                &[
                    "architecture", "architect", "spatial planning", "urban planning", "civil engineering",
                    "blueprint", "floor plan", "building code", "kdb", "klb", "gsb", "elevation",
                    "facade", "structural analysis", "autocad", "revit", "bim", "hvac", "arsitektur",
                    "arsitek", "tata ruang", "tata kota", "denah", "rencana bangunan", "pbg", "imb", "konstruksi",
                    "zoning", "building", "cetak biru", "bangunan sipil", "sipil"
                ],
                &["software architecture", "system architecture"]
            ),
            AgentCategory::CulinaryGastronomy => (
                &[
                    "culinary", "gastronomy", "chef", "cooking", "recipe", "baking", "food cost",
                    "food safety", "haccp", "mise en place", "fermentation", "plating", "flavor pairing",
                    "ingredient", "restaurant menu", "fnb", "tata boga", "kuliner", "resep", "masak",
                    "koki", "bahan makanan", "keamanan pangan", "pastry", "food", "memasak", "hidangan"
                ],
                &[]
            ),
            AgentCategory::SportsAthletics => (
                &[
                    "sports", "athletics", "fitness", "kinesiology", "biomechanics", "strength conditioning",
                    "hypertrophy", "vo2 max", "periodization", "workout", "exercise", "training program",
                    "recovery", "deload", "coach", "athlete", "olahraga", "atlet", "kebugaran",
                    "latihan fisik", "pelatih", "otot", "biomekanika", "atletik", "fisiologi"
                ],
                &[]
            ),
            AgentCategory::AgricultureEcology => (
                &[
                    "agriculture", "farming", "agronomy", "crop", "crops", "soil biology", "permaculture",
                    "hydroponics", "fertilizer", "pest management", "ipm", "irrigation", "soil",
                    "organic farming", "ecosystem", "harvest", "pertanian", "agronomi", "tani",
                    "tanaman", "tanah", "pupuk", "permakultur", "hidroponik", "hama", "panen", "irigasi", "budidaya tanaman"
                ],
                &[]
            ),
            AgentCategory::DiplomacyNegotiation => (
                &[
                    "diplomacy", "diplomat", "negotiation", "batna", "zopa", "treaty", "foreign affairs",
                    "international relations", "geopolitics", "bilateral", "multilateral", "consular",
                    "protocol", "crisis negotiation", "accord", "diplomasi", "negosiasi",
                    "hubungan internasional", "geopolitik", "perjanjian internasional", "resolusi konflik",
                    "envoy", "traktat", "perundingan"
                ],
                &[]
            ),
            AgentCategory::CybersecurityForensics => (
                &[
                    "cybersecurity", "infosec", "penetration testing", "pentest", "vulnerability",
                    "cve", "cvss", "threat intelligence", "digital forensics", "incident response",
                    "mitre att&ck", "red team", "blue team", "malware", "reverse engineering",
                    "zero day", "exploit", "keamanan siber", "peretasan etis", "forensik digital",
                    "celah keamanan", "investigasi siber", "peretasan", "forensics", "kerentanan"
                ],
                &[]
            ),
            AgentCategory::HospitalityTourism => (
                &[
                    "hospitality", "tourism", "hotel", "resort", "hotelier", "travel", "destination",
                    "guest experience", "concierge", "revpar", "occupancy", "service recovery",
                    "ecotourism", "tour guide", "perhotelan", "pariwisata", "wisata", "tamu",
                    "layanan hotel", "destinasi", "guest", "akomodasi", "layanan tamu"
                ],
                &[]
            ),
            AgentCategory::MaritimeLogistics => (
                &[
                    "maritime", "shipping", "logistics", "supply chain", "freight", "cargo",
                    "incoterms", "bill of lading", "customs clearance", "port", "container",
                    "teu", "demurrage", "multimodal", "air cargo", "vessel", "maritim", "logistik",
                    "rantai pasok", "kargo", "pelabuhan", "kapal", "kepabeanan", "ekspor impor",
                    "pelayaran", "peti kemas"
                ],
                &[]
            ),
            AgentCategory::System => (
                &[
                    "system", "sysadmin", "os", "operating system", "linux", "kernel", "systemd",
                    "daemon", "service", "process", "socket", "pid", "memory", "ram", "swap",
                    "cpu", "disk", "storage", "bash", "shell", "sistem", "layanan sistem",
                    "administrasi sistem", "perangkat lunak sistem", "layanan", "proses", "memori", "operasi"
                ],
                &[]
            ),
        }
    }

    fn category_file_patterns(cat: AgentCategory) -> &'static [&'static str] {
        match cat {
            AgentCategory::Healthcare => &["*health*", "*patient*", "*clinic*", "*medical*"],
            AgentCategory::Psychology => &["*psychology*", "*counseling*", "*mindset*"],
            AgentCategory::Legal => &["*contract*", "*agreement*", "*nda*", "*terms*", "*privacy*", "*legal*"],
            AgentCategory::Education => &["*syllabus*", "*curriculum*", "*lesson*", "*course*"],
            AgentCategory::Technology => &["Cargo.toml", "package.json", "go.mod", "pom.xml", "requirements.txt", "Dockerfile", ".git", "*.rs", "*.py", "*.ts", "*.js"],
            AgentCategory::Finance => &["*ledger*", "*balance_sheet*", "*tax*", "*trading*", "*crypto*", "*portfolio*"],
            AgentCategory::Business => &["*pitchdeck*", "*business_plan*", "*roadmap*", "*strategy*"],
            AgentCategory::Marketing => &["*seo*", "*funnel*", "*marketing*", "*content_calendar*"],
            AgentCategory::Advertising => &["*ads*", "*campaign*", "*media_buying*"],
            AgentCategory::MediaCreative => &["*.mp4", "*.mp3", "*.wav", "*.prproj", "*.drp", "*youtube*", "*podcast*"],
            AgentCategory::Design => &["*.css", "*.html", "*.svg", "*.fig", "*.sketch", "*.ai", "*.psd", "tailwind.config.*", "styles/**", "design/**", "tokens/**", "canvas-ui/**"],
            AgentCategory::HumanResources => &["*resume*", "*cv*", "*job_description*", "*onboarding*", "*payroll*"],
            AgentCategory::ScienceResearch => &["*.ipynb", "*.r", "dataset.*", "model.onnx", "*.mat", "*experiment*"],
            AgentCategory::AutomationAdmin => &["*scrape*", "*crawler*", "*automation*", "*.csv", "*.xlsx"],
            AgentCategory::Core => &["flowork.json", "agent.json", "agents.json", "skills.json"],
            AgentCategory::ArtsMusicPoetry => &["*.chord", "*.lyric*", "*.poem*", "*.midi", "*.score*", "*puisi*", "*lirik*"],
            AgentCategory::MetaphysicsFengShui => &["*fengshui*", "*bazi*", "*luopan*", "*geomancy*", "*iching*", "*primbon*"],
            AgentCategory::ArchitectureSpatial => &["*.dwg", "*.dxf", "*.rvt", "*.ifc", "*blueprint*", "*site_plan*", "*denah*"],
            AgentCategory::CulinaryGastronomy => &["*recipe*", "*menu*", "*food_cost*", "*haccp*", "*resep*"],
            AgentCategory::SportsAthletics => &["*workout*", "*training_plan*", "*kinetics*", "*biomechanics*", "*latihan*"],
            AgentCategory::AgricultureEcology => &["*crop*", "*soil*", "*permaculture*", "*hydroponic*", "*pertanian*", "*tanam*"],
            AgentCategory::DiplomacyNegotiation => &["*treaty*", "*negotiation*", "*accord*", "*protocol*", "*diplomasi*"],
            AgentCategory::CybersecurityForensics => &["*.pcap", "*.ioc", "*cve*", "*exploit*", "*malware*", "*forensic*", "*pentest*"],
            AgentCategory::HospitalityTourism => &["*hotel*", "*tourism*", "*concierge*", "*guest_experience*", "*wisata*"],
            AgentCategory::MaritimeLogistics => &["*incoterms*", "*manifest*", "*bill_of_lading*", "*customs*", "*shipping*", "*logistik*"],
            AgentCategory::System => &["/etc/*", "*.service", "*.conf", "/proc/*", "/sys/*", "*.sh", "*.bash", "*systemd*"],
        }
    }

    fn category_tools(cat: AgentCategory) -> &'static [&'static str] {
        match cat {
            AgentCategory::Healthcare => &[],
            AgentCategory::Psychology => &[],
            AgentCategory::Legal => &[],
            AgentCategory::Education => &[],
            AgentCategory::Technology => &["run_command", "replace_file_content", "write_to_file", "view_file"],
            AgentCategory::Finance => &[],
            AgentCategory::Business => &[],
            AgentCategory::Marketing => &[],
            AgentCategory::Advertising => &[],
            AgentCategory::MediaCreative => &[],
            AgentCategory::Design => &["generate_image", "flow_screenshot"],
            AgentCategory::HumanResources => &[],
            AgentCategory::ScienceResearch => &["search_web", "read_url_content"],
            AgentCategory::AutomationAdmin => &["read_url_content", "read_browser_page", "browser_action"],
            AgentCategory::Core => &["team_audit", "skill_control", "plugin_control", "brain_control"],
            AgentCategory::ArtsMusicPoetry => &[],
            AgentCategory::MetaphysicsFengShui => &[],
            AgentCategory::ArchitectureSpatial => &[],
            AgentCategory::CulinaryGastronomy => &[],
            AgentCategory::SportsAthletics => &[],
            AgentCategory::AgricultureEcology => &[],
            AgentCategory::DiplomacyNegotiation => &[],
            AgentCategory::CybersecurityForensics => &["run_command", "view_file"],
            AgentCategory::HospitalityTourism => &[],
            AgentCategory::MaritimeLogistics => &[],
            AgentCategory::System => &["run_command", "view_file", "write_to_file", "replace_file_content"],
        }
    }

    fn sample_workspace_files(ws: &Path) -> Vec<String> {
        let mut results = Vec::new();
        if !ws.exists() || !ws.is_dir() {
            return results;
        }

        let mut stack = vec![(ws.to_path_buf(), 0usize)];
        while let Some((dir, depth)) = stack.pop() {
            if depth > 2 || results.len() >= 100 {
                continue;
            }
            if let Ok(entries) = fs::read_dir(&dir) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    let file_name = entry.file_name().to_string_lossy().to_string();
                    if file_name.starts_with('.') && file_name != ".git" {
                        continue;
                    }
                    if file_name == "target" || file_name == "node_modules" || file_name == ".FL_BIN" {
                        continue;
                    }

                    if path.is_file() {
                        if let Ok(rel) = path.strip_prefix(ws) {
                            results.push(rel.to_string_lossy().replace('\\', "/"));
                        } else {
                            results.push(file_name);
                        }
                        if results.len() >= 100 {
                            break;
                        }
                    } else if path.is_dir() && depth < 2 {
                        stack.push((path, depth + 1));
                    }
                }
            }
        }
        results
    }

    fn matches_file_pattern(pattern: &str, files: &[String]) -> bool {
        let pat_clean = pattern.trim();
        if pat_clean.is_empty() {
            return false;
        }

        if pat_clean.starts_with("*.") {
            let ext = &pat_clean[1..];
            files.iter().any(|f| f.ends_with(ext))
        } else if pat_clean.starts_with('*') && pat_clean.ends_with('*') && pat_clean.len() > 2 {
            let substr = &pat_clean[1..pat_clean.len() - 1].to_lowercase();
            files.iter().any(|f| f.to_lowercase().contains(substr))
        } else if pat_clean.ends_with(".*") {
            let prefix = &pat_clean[..pat_clean.len() - 2];
            files.iter().any(|f| {
                let file_stem = Path::new(f).file_stem().and_then(|s| s.to_str()).unwrap_or("");
                file_stem.eq_ignore_ascii_case(prefix)
            })
        } else {
            files.iter().any(|f| {
                f.eq_ignore_ascii_case(pat_clean)
                    || f.ends_with(&format!("/{pat_clean}"))
                    || Path::new(f).file_name().and_then(|s| s.to_str()).map(|s| s.eq_ignore_ascii_case(pat_clean)).unwrap_or(false)
            })
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_eval_browser_stealth_trigger() {
        let mut tools = HashSet::new();
        tools.insert("terminal".to_string());

        // Without browser tool or keywords -> None
        assert!(SovereignTriggerEngine::eval_browser_stealth("tolong edit file", Some(&tools), false).is_none());

        // With keyword -> Some
        let res = SovereignTriggerEngine::eval_browser_stealth("buka website target dan bypass cloudflare", Some(&tools), false);
        assert!(res.is_some());
        assert!(res.unwrap().contains("<SOVEREIGN_WEB_RESILIENCE>"));

        // With domain (.com / .id) -> Some
        let res_domain = SovereignTriggerEngine::eval_browser_stealth("tolong analisa floworkos.com dan cek keamanan", Some(&tools), false);
        assert!(res_domain.is_some());
        assert!(res_domain.unwrap().contains("<SOVEREIGN_WEB_RESILIENCE>"));

        // With URL (proto_https) -> Some
        let test_url_input = format!("buka {}github.com/flowork", crate::prompt_enclave::PromptEnclave::proto_https());
        let res_url = SovereignTriggerEngine::eval_browser_stealth(&test_url_input, Some(&tools), false);
        assert!(res_url.is_some());
        assert!(res_url.unwrap().contains("<SOVEREIGN_WEB_RESILIENCE>"));

        // With recent web tool flag -> Some
        let res_recent = SovereignTriggerEngine::eval_browser_stealth("bagaimana hasilnya?", Some(&tools), true);
        assert!(res_recent.is_some());
        assert!(res_recent.unwrap().contains("<SOVEREIGN_WEB_RESILIENCE>"));

        // With tool mounted -> Some
        tools.insert("browser".to_string());
        let res_tool = SovereignTriggerEngine::eval_browser_stealth("halo", Some(&tools), false);
        assert!(res_tool.is_some());
        assert!(res_tool.unwrap().contains("<SOVEREIGN_WEB_RESILIENCE>"));
    }

    #[test]
    fn test_eval_autonomous_mode_trigger() {
        // Normal chat & casual single words -> None (false positives eliminated)
        assert!(SovereignTriggerEngine::eval_autonomous_mode("halo", false).is_none());
        assert!(SovereignTriggerEngine::eval_autonomous_mode("gas", false).is_none());
        assert!(SovereignTriggerEngine::eval_autonomous_mode("hajar", false).is_none());
        assert!(SovereignTriggerEngine::eval_autonomous_mode("sikat", false).is_none());
        assert!(SovereignTriggerEngine::eval_autonomous_mode("tuntaskan", false).is_none());

        // Flag true -> Some
        let res_flag = SovereignTriggerEngine::eval_autonomous_mode("halo", true);
        assert!(res_flag.is_some());
        assert!(res_flag.unwrap().contains("<AUTONOMOUS_HEADLESS_MODE>"));

        // Slash command /goal -> Some
        let res_goal = SovereignTriggerEngine::eval_autonomous_mode("/goal selesaikan refaktor", false);
        assert!(res_goal.is_some());
        assert!(res_goal.unwrap().contains("<AUTONOMOUS_HEADLESS_MODE>"));

        // Explicit phrases: "ok gas", "tuntaskan sampai selesai", "eksekusi mandiri", "overnight run" -> Some
        let res_gas = SovereignTriggerEngine::eval_autonomous_mode("ok gas kerjakan sekarang", false);
        assert!(res_gas.is_some());
        assert!(res_gas.unwrap().contains("<AUTONOMOUS_HEADLESS_MODE>"));

        let res_tuntas = SovereignTriggerEngine::eval_autonomous_mode("tuntaskan sampai selesai bro", false);
        assert!(res_tuntas.is_some());
        assert!(res_tuntas.unwrap().contains("<AUTONOMOUS_HEADLESS_MODE>"));

        let res_mandiri = SovereignTriggerEngine::eval_autonomous_mode("eksekusi mandiri tanpa tanya", false);
        assert!(res_mandiri.is_some());
        assert!(res_mandiri.unwrap().contains("<AUTONOMOUS_HEADLESS_MODE>"));
    }

    #[test]
    fn test_eval_plan_contract_trigger() {
        assert!(SovereignTriggerEngine::eval_plan_contract("halo", false).is_none());

        let res = SovereignTriggerEngine::eval_plan_contract("/plan rancang modular engine", false);
        assert!(res.is_some());
        assert!(res.unwrap().contains("<PLANNING_MODE_MANDATE>"));
    }

    #[test]
    fn test_eval_child_subagent_mandate_trigger() {
        assert!(SovereignTriggerEngine::eval_child_subagent(false).is_none());

        let res = SovereignTriggerEngine::eval_child_subagent(true);
        assert!(res.is_some());
        let banner = res.unwrap();
        assert!(banner.contains("<SUBAGENT_WORKER_MANDATE>"));
        assert!(!banner.contains("trigger_id:"));
    }

    #[test]
    fn test_eval_web_stack_discovery_trigger() {
        let temp_dir = std::env::temp_dir().join(format!("test_web_stack_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        let _ = fs::create_dir_all(&temp_dir);

        // Case 1: Empty workspace - No web stack trigger
        assert!(SovereignTriggerEngine::eval_web_stack(&temp_dir).is_none());

        // Case 2: Workspace with package.json - Triggers web stack mandate
        let _ = fs::write(temp_dir.join("package.json"), "{}");
        let res = SovereignTriggerEngine::eval_web_stack(&temp_dir);
        assert!(res.is_some());
        let banner = res.unwrap();
        assert!(banner.contains("<WEB_APPLICATION_STACK_DISCOVERY>"));
        assert!(!banner.contains("trigger_id:"));

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_eval_new_sovereign_rules_triggers() {
        // Rule 1: Git attribution
        assert!(SovereignTriggerEngine::eval_git_attribution(false).is_none());
        let git_res = SovereignTriggerEngine::eval_git_attribution(true);
        assert!(git_res.is_some());
        assert!(git_res.unwrap().contains("<MANDATORY_GIT_CONTRIBUTION_DIRECTIVE>"));

        // Rule 4: Memory crystallization check
        assert!(SovereignTriggerEngine::eval_memory_crystallization_check(false).is_none());
        let cryst_res = SovereignTriggerEngine::eval_memory_crystallization_check(true);
        assert!(cryst_res.is_some());
        let cryst_val = cryst_res.unwrap();
        println!("CRYST = {:?}", cryst_val);
        assert!(cryst_val.contains("<SOVEREIGN_MEMORY_CRYSTALLIZATION"));

        // Rule 5: External prompt Lex Superior guardrail
        assert!(SovereignTriggerEngine::eval_external_prompt_guardrail(false).is_none());
        let ext_res = SovereignTriggerEngine::eval_external_prompt_guardrail(true);
        assert!(ext_res.is_some());
        assert!(ext_res.unwrap().contains("<EXTERNAL_INPUT_BOUNDARY_GUARDRAIL>"));

        // Rule 18: Pre-done audit mandate (Separation of Duties)
        assert!(SovereignTriggerEngine::eval_pre_done_audit_mandate("sess_test", "").is_none());
        let pre_done_res = SovereignTriggerEngine::eval_pre_done_audit_mandate("sess_test", "skills/my_skill, plugins/my_plugin");
        assert!(pre_done_res.is_some());
        let pre_done_str = pre_done_res.unwrap();
        assert!(pre_done_str.contains("<SOVEREIGN_PRE_DONE_AUDIT_BLOCKER>"));
        assert!(pre_done_str.contains("sess_test"));
        assert!(pre_done_str.contains("skills/my_skill, plugins/my_plugin"));
        assert!(pre_done_str.contains("FOUR SACRED AUDIT GATES"));
        assert!(pre_done_str.contains("GATE 1: STRICT TRIGGER CONFORMANCE"));
        assert!(pre_done_str.contains("GATE 2: ZERO DATA LEAKS & DLP GUARD"));
        assert!(pre_done_str.contains("GATE 3: STRICT STRUCTURAL COMPLIANCE"));
        assert!(pre_done_str.contains("GATE 4: ZERO HARDCODED PATHS & MULTI-OS PORTABILITY"));
    }

    #[test]
    fn test_eval_intercept_gate_matching_and_limits() {
        let temp_dir = std::env::temp_dir().join(format!("test_intercept_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        let ws_mem = temp_dir.join(".fl_brain/memories");
        let _ = fs::create_dir_all(&ws_mem);

        // Create 4 memories with different created_at and keywords
        let mem1 = r#"---
id: memory_one
title: Memory One Title
created_at: 2026-10-01T10:00:00Z
keywords: ["postgres", "database", "connection", "pool", "timeout", "leak", "sql", "migration", "port", "cluster"]
category: database
status: resolved
---
Solution for postgres pool leak 1
"#;
        let mem2 = r#"---
id: memory_two
title: Memory Two Title
created_at: 2026-10-05T12:00:00Z
keywords: ["postgres", "database", "connection", "pool", "timeout", "leak", "performance", "tuning", "wal", "indexes"]
category: database
status: resolved
---
Solution for postgres pool leak 2 (newer)
"#;
        let mem3 = r#"---
id: memory_three
title: Memory Three Title
created_at: 2026-10-06T15:00:00Z
keywords: ["postgres", "database", "connection", "pool", "timeout", "leak", "high_concurrency", "lock", "idle", "active"]
category: database
status: resolved
---
Solution for postgres pool leak 3 (even newer)
"#;
        let mem4 = r#"---
id: memory_four
title: Memory Four Title
created_at: 2026-10-07T08:00:00Z
keywords: ["postgres", "database", "connection", "pool", "timeout", "leak", "scaling", "sharding", "replica", "failover"]
category: database
status: resolved
---
Solution for postgres pool leak 4 (newest)
"#;
        fs::write(ws_mem.join("mem1.md"), mem1).unwrap();
        fs::write(ws_mem.join("mem2.md"), mem2).unwrap();
        fs::write(ws_mem.join("mem3.md"), mem3).unwrap();
        fs::write(ws_mem.join("mem4.md"), mem4).unwrap();

        let (injected_block, memories) = SovereignTriggerEngine::eval_intercept_gate(
            "Investigate postgres database connection pool leak and fix timeout",
            &temp_dir,
            &temp_dir,
        );

        // 1. Memory limit check: exactly 3 memories injected (capped at 3 despite 4 matching candidates)
        assert_eq!(memories.len(), 3);

        // 2. Newest timestamp preference check: memory_four (newest 2026-10-07) MUST be in the top 3
        let mem_ids: Vec<&str> = memories.iter().filter_map(|m| m["id"].as_str()).collect();
        assert!(mem_ids.contains(&"memory_four"), "Newest memory must be included in top 3");
        assert!(mem_ids.contains(&"memory_three"));
        assert!(mem_ids.contains(&"memory_two"));
        assert!(!mem_ids.contains(&"memory_one"), "Oldest memory must be truncated when capped at 3");

        // 3. Formatted injection block contains the right sections
        assert!(injected_block.contains("<SOVEREIGN_TOOL_INTERCEPT_GATE_INJECTION>"));
        assert!(injected_block.contains("STATUS: UNLOCKED"));
        assert!(injected_block.contains("Memory Four Title"));
        assert!(!injected_block.contains("SKILL"), "Skills must never be auto-injected by intercept gate");

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_eval_engineering_doctrines_trigger() {
        // 1. None for unrelated chat
        assert!(SovereignTriggerEngine::eval_engineering_doctrines("halo apa kabar bro", None).is_none());

        // 2. Diagnosing Bugs trigger (Slash command + Natural ID & EN)
        let res_diag_cmd = SovereignTriggerEngine::eval_engineering_doctrines("/diagnose", None);
        assert!(res_diag_cmd.is_some());
        let res_diag_cmd = res_diag_cmd.unwrap();
        assert_eq!(res_diag_cmd.doctrine, EngineeringDoctrine::DiagnosingBugs);
        assert!(res_diag_cmd.prompt_injection.contains("ACTIVE_ENGINEERING_DOCTRINE id=\"diagnosing-bugs\""));

        let res_diag_nat = SovereignTriggerEngine::eval_engineering_doctrines("bro kenapa crash terus benerin error ini", None);
        assert!(res_diag_nat.is_some());
        assert_eq!(res_diag_nat.unwrap().doctrine, EngineeringDoctrine::DiagnosingBugs);

        let res_diag_en = SovereignTriggerEngine::eval_engineering_doctrines("please reproduce error and investigate bug", None);
        assert!(res_diag_en.is_some());
        assert_eq!(res_diag_en.unwrap().doctrine, EngineeringDoctrine::DiagnosingBugs);

        // 3. TDD trigger (Slash command + Natural ID & EN)
        let res_tdd_cmd = SovereignTriggerEngine::eval_engineering_doctrines("/tdd", None);
        assert!(res_tdd_cmd.is_some());
        assert_eq!(res_tdd_cmd.unwrap().doctrine, EngineeringDoctrine::TestDrivenDevelopment);

        let res_tdd_nat = SovereignTriggerEngine::eval_engineering_doctrines("bikin failing test dulu sebelum implementasi", None);
        assert!(res_tdd_nat.is_some());
        assert_eq!(res_tdd_nat.unwrap().doctrine, EngineeringDoctrine::TestDrivenDevelopment);

        let res_tdd_en = SovereignTriggerEngine::eval_engineering_doctrines("let's test public seam with write test first", None);
        assert!(res_tdd_en.is_some());
        assert_eq!(res_tdd_en.unwrap().doctrine, EngineeringDoctrine::TestDrivenDevelopment);

        // 4. Grill with docs (Slash command + Natural ID & EN)
        let res_grill_cmd = SovereignTriggerEngine::eval_engineering_doctrines("/grill", None);
        assert!(res_grill_cmd.is_some());
        assert_eq!(res_grill_cmd.unwrap().doctrine, EngineeringDoctrine::GrillWithDocs);

        let res_grill_nat = SovereignTriggerEngine::eval_engineering_doctrines("bedah rancangan dan uji ide saya bro", None);
        assert!(res_grill_nat.is_some());
        assert_eq!(res_grill_nat.unwrap().doctrine, EngineeringDoctrine::GrillWithDocs);

        let res_grill_en = SovereignTriggerEngine::eval_engineering_doctrines("challenge this design and stress test my plan", None);
        assert!(res_grill_en.is_some());
        assert_eq!(res_grill_en.unwrap().doctrine, EngineeringDoctrine::GrillWithDocs);

        // 5. Engineering Counsel (Slash command + Natural ID & EN)
        let res_counsel_cmd = SovereignTriggerEngine::eval_engineering_doctrines("/counsel", None);
        assert!(res_counsel_cmd.is_some());
        assert_eq!(res_counsel_cmd.unwrap().doctrine, EngineeringDoctrine::EngineeringCounsel);

        let res_counsel_nat = SovereignTriggerEngine::eval_engineering_doctrines("alur rekayasa apa yang cocok untuk proyek ini", None);
        assert!(res_counsel_nat.is_some());
        assert_eq!(res_counsel_nat.unwrap().doctrine, EngineeringDoctrine::EngineeringCounsel);

        let res_counsel_en = SovereignTriggerEngine::eval_engineering_doctrines("engineering counsel: how to structure this build", None);
        assert!(res_counsel_en.is_some());
        assert_eq!(res_counsel_en.unwrap().doctrine, EngineeringDoctrine::EngineeringCounsel);

        // 6. Deep Modules
        let res_deep = SovereignTriggerEngine::eval_engineering_doctrines("/deep-modules", None);
        assert!(res_deep.is_some());
        assert_eq!(res_deep.unwrap().doctrine, EngineeringDoctrine::DeepModules);

        // 7. Domain Modeling & ADR
        let res_adr = SovereignTriggerEngine::eval_engineering_doctrines("/adr", None);
        assert!(res_adr.is_some());
        assert_eq!(res_adr.unwrap().doctrine, EngineeringDoctrine::DomainModelingAdr);

        // 8. Spec & Triage
        let res_spec = SovereignTriggerEngine::eval_engineering_doctrines("/spec", None);
        assert!(res_spec.is_some());
        assert_eq!(res_spec.unwrap().doctrine, EngineeringDoctrine::SpecAndTriage);

        // 9. Handoff & Prototype
        let res_handoff = SovereignTriggerEngine::eval_engineering_doctrines("/handoff", None);
        assert!(res_handoff.is_some());
        assert_eq!(res_handoff.unwrap().doctrine, EngineeringDoctrine::HandoffAndPrototype);

        // 10. Git Guardrails
        let res_git = SovereignTriggerEngine::eval_engineering_doctrines("/git-guardrails", None);
        assert!(res_git.is_some());
        assert_eq!(res_git.unwrap().doctrine, EngineeringDoctrine::GitGuardrails);
    }

    #[test]
    fn test_eval_intercept_gate_zero_bloat_bypass() {
        let temp_dir = std::env::temp_dir().join(format!("test_zero_bloat_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        let _ = fs::create_dir_all(&temp_dir);

        let (injected_block, memories) = SovereignTriggerEngine::eval_intercept_gate(
            "unrelated generic chat without any matching memory",
            &temp_dir,
            &temp_dir,
        );

        // Zero-bloat guarantee: Must return completely empty string, no useless placeholder tokens!
        assert!(injected_block.is_empty(), "Unmatched gate call must produce zero token bloat");
        assert!(memories.is_empty());

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_eval_skill_radar_hierarchy_and_capping() {
        let local_skills = vec![
            json!({
                "id": "sqlite_concurrency",
                "name": "SQLite Concurrency Expert",
                "description": "High-throughput WAL optimization and busy_timeout tuning",
                "keywords": ["sqlite", "wal", "concurrency", "busy_timeout", "pragmas", "database"]
            }),
            json!({
                "id": "unrelated_skill",
                "name": "Unrelated Cooking Skill",
                "description": "How to make cookies",
                "keywords": ["cookie", "sugar", "bake"]
            }),
        ];

        let remote_skills = vec![
            json!({
                "id": "postgres_concurrency",
                "name": "Postgres Concurrency Expert",
                "description": "Connection pool leaks and transaction locks",
                "keywords": ["postgres", "database", "concurrency", "pool", "timeout"]
            }),
            json!({
                "id": "distributed_wal_engine",
                "name": "Distributed WAL Engine",
                "description": "Distributed write-ahead-logging and consensus",
                "keywords": ["wal", "storage", "concurrency", "consensus", "log"]
            }),
            json!({
                "id": "extra_remote_skill",
                "name": "Extra Database Scaling",
                "description": "Sharding and replica clusters",
                "keywords": ["database", "scaling", "concurrency", "sharding"]
            }),
        ];

        // 1. Query matches both local and remote skills
        let (banner, matched) = SovereignTriggerEngine::eval_skill_radar(
            "sqlite wal concurrency database optimization",
            &local_skills,
            &remote_skills,
        );

        // Max Top-3 candidates cap
        assert_eq!(matched.len(), 3, "Radar must cap candidates at Top-3");

        // First candidate MUST be the local sqlite_concurrency (local prioritization & highest score)
        assert_eq!(matched[0]["id"], "sqlite_concurrency");
        assert_eq!(matched[0]["radar_source"], "local");

        // Banner formatting checks
        assert!(banner.contains("<SOVEREIGN_SKILL_RADAR>"));
        assert!(banner.contains("[SOVEREIGN SKILL RADAR: JUST-IN-TIME CAPABILITY RECOMMENDATION]"));
        assert!(banner.contains("sqlite_concurrency"));
        assert!(banner.contains("SKILL-FIRST SOVEREIGN DOCTRINE"));
        assert!(banner.contains("PRIORITIZE pinning it in the next step: `skill_control(action: 'pin'"));
        assert!(banner.contains("ONLY disregard if the task is strictly trivial and completely unrelated"));

        // 2. Zero-bloat bypass check for unmatched keywords
        let (empty_banner, empty_matched) = SovereignTriggerEngine::eval_skill_radar(
            "astronomy quantum physics telescope",
            &local_skills,
            &remote_skills,
        );
        assert!(empty_banner.is_empty(), "Zero matches must produce empty banner");
        assert!(empty_matched.is_empty());
    }

    #[test]
    fn test_matches_with_exclusion_and_skill_radar_negative_trigger() {
        let keywords = vec![".com".to_string(), "website".to_string(), "crawl".to_string()];
        let exclude = vec!["youtube".to_string(), "youtu.be".to_string()];

        // 1. YouTube standard URL -> Excluded (contains "youtube")
        assert!(!SovereignTriggerEngine::matches_with_exclusion(
            "buka url https://media.vault.internal/stream?v=123 youtube dan ekstrak",
            &keywords,
            &exclude,
        ));

        // 2. Comma format (youtube,com) -> Excluded (contains "youtube")
        assert!(!SovereignTriggerEngine::matches_with_exclusion(
            "tolong cek channel youtube,com yang ini bro",
            &keywords,
            &exclude,
        ));

        // 3. Normal website (example.com) -> Triggers (contains ".com", no exclusion)
        assert!(SovereignTriggerEngine::matches_with_exclusion(
            "buka https://example.com/blog dan analisa kontennya",
            &keywords,
            &exclude,
        ));

        // 4. Test Skill Radar with exclude_keywords
        let local_skills = vec![
            json!({
                "id": "web_intelligence",
                "name": "Web Scraper",
                "description": "General DOM extraction and crawling",
                "keywords": ["web", "scrape", "crawl", ".com", "domain"],
                "exclude_keywords": ["youtube", "youtu.be"]
            }),
            json!({
                "id": "youtube_spy",
                "name": "YouTube Spy Studio",
                "description": "YouTube video player intelligence & transcripts",
                "keywords": ["youtube", "youtu.be", "yt spy", "video"]
            })
        ];

        // Query with youtube keyword
        let (_banner_yt, matched_yt) = SovereignTriggerEngine::eval_skill_radar(
            "analisa channel youtube media.vault.internal/stream?v=abc",
            &local_skills,
            &[],
        );
        assert!(!matched_yt.iter().any(|s| s["id"] == "web_intelligence"), "web_intelligence must be excluded for youtube");
        assert!(matched_yt.iter().any(|s| s["id"] == "youtube_spy"), "youtube_spy must be matched for youtube");

        // Query with youtube,com (comma format)
        let (_banner_comma, matched_comma) = SovereignTriggerEngine::eval_skill_radar(
            "bedah video youtube,com berikut",
            &local_skills,
            &[],
        );
        assert!(!matched_comma.iter().any(|s| s["id"] == "web_intelligence"), "web_intelligence must be excluded for youtube,com");
        assert!(matched_comma.iter().any(|s| s["id"] == "youtube_spy"), "youtube_spy must be matched for youtube,com");

        // Query with standard example.com
        let (_banner_ex, matched_ex) = SovereignTriggerEngine::eval_skill_radar(
            "scrape data dari website example.com",
            &local_skills,
            &[],
        );
        assert!(matched_ex.iter().any(|s| s["id"] == "web_intelligence"), "web_intelligence must be matched for example.com");
        assert!(!matched_ex.iter().any(|s| s["id"] == "youtube_spy"), "youtube_spy must not be matched for example.com");
    }

    #[test]
    fn test_eval_tool_radar_matching_and_system_mandate() {
        let tools = vec![
            json!({
                "id": "crypto_scanner",
                "name": "Crypto Scanner",
                "description": "Scans cryptocurrency market metrics and volatility",
                "keywords": ["crypto", "bitcoin", "solana", "trading volume", "volatility"],
                "exclude_keywords": ["forex", "eurusd"]
            }),
            json!({
                "id": "lsof_tracer",
                "name": "LSOF File Descriptor Tracer",
                "description": "Inspects open and locked file descriptors",
                "keywords": ["lsof", "lock", "file descriptor", "concurrency"]
            }),
            json!({
                "id": "db_bench",
                "name": "Database Benchmark Harness",
                "description": "High-throughput database concurrency stress testing",
                "keywords": ["database", "benchmark", "stress", "concurrency"]
            }),
            json!({
                "id": "forex_tick_reader",
                "name": "Forex Tick Reader",
                "description": "High-frequency tick data stream parser for MT5",
                "keywords": ["forex", "eurusd", "tick", "currency"]
            }),
        ];

        // 1. Matching check
        let (banner, matched) = SovereignTriggerEngine::eval_tool_radar(
            "bitcoin crypto volatility trading volume scanner",
            &tools,
        );
        assert_eq!(matched.len(), 1);
        assert_eq!(matched[0]["id"], "crypto_scanner");
        assert!(banner.contains("<SOVEREIGN_TOOL_RADAR>"));
        assert!(banner.contains("SYSTEM MANDATE: DO NOT RELY ON GENERIC PRE-TRAINING INSTRUMENTS!"));
        assert!(banner.contains("search_tools(action: 'mount', tools: ['crypto_scanner'])"));

        // 2. Exclusion check: query contains "forex" -> crypto_scanner disqualified
        let (_banner_ex, matched_ex) = SovereignTriggerEngine::eval_tool_radar(
            "crypto forex trading analysis",
            &tools,
        );
        assert!(!matched_ex.iter().any(|t| t["id"] == "crypto_scanner"), "crypto_scanner must be disqualified when forex is in query");
        assert!(matched_ex.iter().any(|t| t["id"] == "forex_tick_reader"), "forex_tick_reader must match");

        // 3. Zero-bloat bypass check
        let (empty_banner, empty_matched) = SovereignTriggerEngine::eval_tool_radar(
            "baking pastry cake recipe ingredients",
            &tools,
        );
        assert!(empty_banner.is_empty(), "Zero matches must produce empty banner");
        assert!(empty_matched.is_empty());

        // 4. Dynamic Thermal & PC Panas Trigger check
        let tools_with_health = vec![
            json!({
                "id": "sys_health",
                "name": "System Health Monitor",
                "description": "Inspect hardware telemetry, CPU load, and thermal levels",
                "keywords": ["hardware", "cpu", "thermal", "diagnostics"]
            }),
            json!({
                "id": "image_resizer",
                "name": "Image Resizer",
                "description": "Resize png and jpeg",
                "keywords": ["image", "png"]
            }),
        ];
        let (thermal_banner, thermal_matched) = SovereignTriggerEngine::eval_tool_radar(
            "pc sedang panas tolong cek suhu",
            &tools_with_health,
        );
        assert_eq!(thermal_matched.len(), 1);
        assert_eq!(thermal_matched[0]["id"], "sys_health");
        assert!(thermal_banner.contains("sys_health"));
    }

    #[test]
    fn test_category_trigger_all_26_categories_by_keyword() {
        let cases = [
            ("CAT-001", "patient clinical treatment hospital disease symptom diagnosis", "CAT-001"),
            ("CAT-001-ID", "pasien dokter klinik obat medis pemeriksaan kesehatan", "CAT-001"),
            ("CAT-002", "psychology mental health cbt therapy anxiety depression", "CAT-002"),
            ("CAT-002-ID", "konseling psikiater kecemasan depresi kesehatan mental", "CAT-002"),
            ("CAT-003", "legal contract nda compliance lawyer lawsuit patent clause", "CAT-003"),
            ("CAT-003-ID", "hukum perjanjian kontrak gugatan kepatuhan hak cipta", "CAT-003"),
            ("CAT-004", "education curriculum syllabus student exam course pedagogy", "CAT-004"),
            ("CAT-004-ID", "pendidikan kurikulum silabus ujian pembelajaran bimbel", "CAT-004"),
            ("CAT-005", "rust compiler python debugging software developer cargo", "CAT-005"),
            ("CAT-005-ID", "pemrograman koding perangkat lunak basis data refactor", "CAT-005"),
            ("CAT-006", "finance crypto bitcoin trading ledger balance sheet tax", "CAT-006"),
            ("CAT-006-ID", "keuangan akuntansi buku besar neraca pajak saham cuan", "CAT-006"),
            ("CAT-007", "business management startup pitchdeck strategy kpi okr", "CAT-007"),
            ("CAT-007-ID", "bisnis strategi manajemen rencana bisnis analisis pasar", "CAT-007"),
            ("CAT-008", "marketing seo organic traffic funnel backlinks copywriting", "CAT-008"),
            ("CAT-008-ID", "pemasaran konten pemasaran lalu lintas organik", "CAT-008"),
            ("CAT-009", "advertising paid ads google ads meta ads ppc media buying", "CAT-009"),
            ("CAT-009-ID", "periklanan kampanye iklan berbayar biaya iklan", "CAT-009"),
            ("CAT-010", "youtube podcast audio video premiere pro davinci thumbnail", "CAT-010"),
            ("CAT-010-ID", "penyuntingan video siaran rekaman sulih suara siaran", "CAT-010"),
            ("CAT-011", "ui ux figma wireframe prototype graphic design tailwind", "CAT-011"),
            ("CAT-011-ID", "desain grafis palet warna tata letak rancangan visual", "CAT-011"),
            ("CAT-012", "human resources hr recruitment hiring resume payroll talent", "CAT-012"),
            ("CAT-012-ID", "sumber daya manusia sdm perekrutan wawancara kerja gaji", "CAT-012"),
            ("CAT-013", "data science experiment physics biology statistics machine learning", "CAT-013"),
            ("CAT-013-ID", "penelitian sains laboratorium fisika matematika riset", "CAT-013"),
            ("CAT-014", "automation web scraping scraper crawler spreadsheet zapier", "CAT-014"),
            ("CAT-014-ID", "otomasi asisten virtual entri data lembar kerja", "CAT-014"),
            ("CAT-015", "core orchestrator agent architecture sovereign meta runtime supervisor", "CAT-015"),
            ("CAT-015-ID", "sistem inti arsitektur agen orkestrator tata kelola", "CAT-015"),
            ("CAT-016", "poetry rhyme lyrics composer lyricist sonnet", "CAT-016"),
            ("CAT-016-ID", "puisi sajak bait lirik lagu komposer nada", "CAT-016"),
            ("CAT-017", "feng shui geomancy bazi luo pan qi", "CAT-017"),
            ("CAT-017-ID", "feng shui geomansi bazi primbon metafisika", "CAT-017"),
            ("CAT-018", "architecture blueprint floor plan bim zoning building", "CAT-018"),
            ("CAT-018-ID", "arsitektur denah cetak biru tata ruang bangunan sipil", "CAT-018"),
            ("CAT-019", "culinary recipe gastronomy chef pastry haccp food", "CAT-019"),
            ("CAT-019-ID", "kuliner resep memasak koki hidangan", "CAT-019"),
            ("CAT-020", "sports athletics biomechanics workout athlete fitness", "CAT-020"),
            ("CAT-020-ID", "olahraga atletik kebugaran latihan fisik fisiologi", "CAT-020"),
            ("CAT-021", "agriculture farming permaculture soil irrigation crops", "CAT-021"),
            ("CAT-021-ID", "pertanian agronomi tanah irigasi budidaya tanaman", "CAT-021"),
            ("CAT-022", "diplomacy treaty negotiation bilateral geopolitics envoy", "CAT-022"),
            ("CAT-022-ID", "diplomasi traktat negosiasi perundingan geopolitik", "CAT-022"),
            ("CAT-023", "cybersecurity penetration testing forensics cve threat intelligence malware", "CAT-023"),
            ("CAT-023-ID", "keamanan siber peretasan pentest forensik digital kerentanan", "CAT-023"),
            ("CAT-024", "hospitality hotel tourism guest concierge travel resort", "CAT-024"),
            ("CAT-024-ID", "perhotelan pariwisata akomodasi layanan tamu wisata", "CAT-024"),
            ("CAT-025", "maritime shipping logistics freight vessel port cargo container", "CAT-025"),
            ("CAT-025-ID", "maritim pelayaran logistik kargo kapal pelabuhan peti kemas", "CAT-025"),
            ("CAT-026", "system sysadmin linux kernel systemd daemon service process memory bash", "CAT-026"),
            ("CAT-026-ID", "administrasi sistem operasi linux kernel layanan daemon proses memori shell", "CAT-026"),
        ];

        for (label, query, expected_cat_id) in cases {
            let eval = SovereignCategoryTrigger::evaluate_text(query);
            assert!(
                eval.is_triggered(expected_cat_id),
                "[{label}] Expected {expected_cat_id} to be triggered for query: '{query}', but got primary: {}, matches: {:?}",
                eval.primary_id(),
                eval.matches.iter().map(|m| &m.category_id).collect::<Vec<_>>()
            );
            assert_eq!(
                eval.primary_id(),
                expected_cat_id,
                "[{label}] Expected primary {expected_cat_id} for query '{query}', got '{}'",
                eval.primary_id()
            );
        }
    }

    #[test]
    fn test_category_trigger_exclusion_and_disambiguation() {
        // "financial health" should NOT trigger CAT-001 (Healthcare), it should trigger CAT-006 (Finance)
        let eval_fin = SovereignCategoryTrigger::evaluate_text("evaluating the financial health of our balance sheet and ledger");
        assert!(!eval_fin.is_triggered("CAT-001"), "CAT-001 must be excluded due to 'financial health'");
        assert!(eval_fin.is_triggered("CAT-006"), "CAT-006 must trigger for financial balance sheet");
        assert_eq!(eval_fin.primary_id(), "CAT-006");

        // "marketing with google ads" should NOT trigger CAT-008 (Organic Marketing), it should trigger CAT-009 (Advertising)
        let eval_ads = SovereignCategoryTrigger::evaluate_text("marketing campaign using google ads and media buying roas");
        assert!(!eval_ads.is_triggered("CAT-008"), "CAT-008 must be excluded due to 'google ads'");
        assert!(eval_ads.is_triggered("CAT-009"), "CAT-009 must trigger for google ads and media buying");
        assert_eq!(eval_ads.primary_id(), "CAT-009");
    }

    #[test]
    fn test_option_b_coder_vs_uiux_territorial_fence() {
        // Option B Boundary Fence: When prompt contains code/software terms but focuses on CSS/styling/glassmorphism,
        // CAT-005 (Technology) MUST be excluded by negative keywords, and CAT-011 (Design) MUST trigger and win primary!
        let eval_gui = SovereignCategoryTrigger::evaluate_text(
            "buatkan koding styling tampilan button dengan css animasi dan efek glassmorphism"
        );
        assert!(!eval_gui.is_triggered("CAT-005"), "CAT-005 must be excluded by Option B negative keywords (css, styling, glassmorphism)");
        assert!(eval_gui.is_triggered("CAT-011"), "CAT-011 must be triggered for GUI styling & glassmorphism");
        assert_eq!(eval_gui.primary_id(), "CAT-011");

        // Reverse check: Backend / Cargo / Rust prompt with zero UI/styling should NOT trigger CAT-011, and MUST trigger CAT-005
        let eval_backend = SovereignCategoryTrigger::evaluate_text(
            "refactor backend api rust compiler cargo build database migration"
        );
        assert!(!eval_backend.is_triggered("CAT-011"), "CAT-011 must be excluded by backend negative keywords");
        assert!(eval_backend.is_triggered("CAT-005"), "CAT-005 must trigger for backend rust cargo");
        assert_eq!(eval_backend.primary_id(), "CAT-005");
    }

    #[test]
    fn test_category_trigger_agent_declaration_override() {
        // Query has generic words, but agent is explicitly coder-specialist (CAT-005)
        let eval = SovereignCategoryTrigger::evaluate(
            "please review this document and help me organize",
            Some("coder-specialist"),
            None,
            None,
        );
        assert!(eval.is_triggered("CAT-005"));
        assert_eq!(eval.primary_id(), "CAT-005");
        assert_eq!(eval.primary_slug(), "technology");

        // With explicit CAT-011 hint
        let eval_design = SovereignCategoryTrigger::evaluate(
            "general task overview",
            Some("CAT-011"),
            None,
            None,
        );
        assert!(eval_design.is_triggered("CAT-011"));
        assert_eq!(eval_design.primary_id(), "CAT-011");
        assert_eq!(eval_design.primary_slug(), "design");
    }

    #[test]
    fn test_category_trigger_workspace_files_and_tools() {
        let temp_dir = std::env::temp_dir().join(format!("flw_cat_test_{}", uuid::Uuid::new_v4()));
        let _ = std::fs::create_dir_all(&temp_dir);

        // 1. Cargo.toml in workspace triggers CAT-005
        let _ = std::fs::write(temp_dir.join("Cargo.toml"), "[package]\nname=\"test\"");
        let eval_tech = SovereignCategoryTrigger::evaluate("general work", None, Some(&temp_dir), None);
        assert!(eval_tech.is_triggered("CAT-005"), "Workspace with Cargo.toml must trigger CAT-005");

        // 2. Add design file *.fig -> triggers CAT-011
        let _ = std::fs::write(temp_dir.join("mockup.fig"), "figma content");
        let eval_both = SovereignCategoryTrigger::evaluate("general work", None, Some(&temp_dir), None);
        assert!(eval_both.is_triggered("CAT-005"));
        assert!(eval_both.is_triggered("CAT-011"));

        // 3. Mounted tools: generate_image boosts CAT-011
        let mut tools = HashSet::new();
        tools.insert("generate_image".to_string());
        let eval_tools = SovereignCategoryTrigger::evaluate("general work", None, None, Some(&tools));
        assert!(eval_tools.is_triggered("CAT-011"));

        // 4. Default fallback: completely unmatched random input triggers CAT-015 (Core)
        let eval_none = SovereignCategoryTrigger::evaluate_text("qwertyuiop 987654321 zzzzzz");
        assert_eq!(eval_none.primary_id(), "CAT-015");
        assert_eq!(eval_none.primary_slug(), "core");

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_scoped_username_and_agent_memory_isolation_anti_contamination() {
        let temp_dir = std::env::temp_dir().join(format!("test_scoped_iso_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        let base_mem = temp_dir.join(".fl_brain").join("memories").join("awenkaudico");
        
        let plugin_dir = base_mem.join("plugin-creator");
        let tools_dir = base_mem.join("tools-creator");
        let shared_dir = base_mem.join("shared");

        let _ = fs::create_dir_all(&plugin_dir);
        let _ = fs::create_dir_all(&tools_dir);
        let _ = fs::create_dir_all(&shared_dir);

        // 1. Seed plugin-creator private memory
        let plugin_mem = r#"---
id: plugin_canvas_guide
title: Canvas Plugin Architecture Guide
created_at: 2026-10-15T12:00:00Z
category: plugin_dev
keywords: ["canvas", "plugin", "architecture", "ui", "framework", "frontend", "visual", "widgets", "interactive", "workspace"]
---
Guide on isolated Canvas UI and server microservice.
"#;
        fs::write(plugin_dir.join("canvas_guide.md"), plugin_mem).unwrap();

        // 2. Seed tools-creator private memory
        let tools_mem = r#"---
id: tools_1file_guide
title: 1File1Logic Modular Tool Pattern
created_at: 2026-10-15T12:00:00Z
category: tool_dev
keywords: ["tool", "1file1logic", "architecture", "plugin", "framework", "script", "nano", "modular", "command", "workspace"]
---
1File1Logic modular pattern with explicit manifest.json.
"#;
        fs::write(tools_dir.join("tools_guide.md"), tools_mem).unwrap();

        // 3. Seed shared memory
        let shared_mem = r#"---
id: global_docker_fix
title: Global Docker Daemon Socket Fix
created_at: 2026-10-15T12:00:00Z
category: devops
keywords: ["docker", "daemon", "socket", "permission", "framework", "architecture", "workspace", "linux", "system", "kernel"]
---
Fix docker permission with chmod 666 /var/run/docker.sock.
"#;
        fs::write(shared_dir.join("docker_fix.md"), shared_mem).unwrap();

        // 4. Test Auto JIT when 'plugin-creator' is the active agent:
        // Must recall 'plugin_canvas_guide' (+30 boost) and 'global_docker_fix' (shared)
        // MUST NOT recall 'tools_1file_guide' (isolated in tools-creator!)
        let (injected_plugin, memories_plugin) = SovereignTriggerEngine::eval_intercept_gate_scoped(
            "Working on framework architecture and workspace setup",
            &temp_dir,
            &temp_dir,
            Some("awenkaudico"),
            Some("plugin-creator"),
        );

        assert!(injected_plugin.contains("Canvas Plugin Architecture Guide"), "plugin-creator must recall its private memory");
        assert!(injected_plugin.contains("Global Docker Daemon Socket Fix"), "plugin-creator must recall shared memory");
        assert!(!injected_plugin.contains("1File1Logic Modular Tool Pattern"), "plugin-creator MUST NOT be contaminated by tools-creator memory!");
        assert_eq!(memories_plugin.len(), 2);

        // 5. Test Auto JIT when 'tools-creator' is the active agent:
        // Must recall 'tools_1file_guide' (+30 boost) and 'global_docker_fix' (shared)
        // MUST NOT recall 'plugin_canvas_guide' (isolated in plugin-creator!)
        let (injected_tools, memories_tools) = SovereignTriggerEngine::eval_intercept_gate_scoped(
            "Working on framework architecture and workspace setup",
            &temp_dir,
            &temp_dir,
            Some("awenkaudico"),
            Some("tools-creator"),
        );

        assert!(injected_tools.contains("1File1Logic Modular Tool Pattern"), "tools-creator must recall its private memory");
        assert!(injected_tools.contains("Global Docker Daemon Socket Fix"), "tools-creator must recall shared memory");
        assert!(!injected_tools.contains("Canvas Plugin Architecture Guide"), "tools-creator MUST NOT be contaminated by plugin-creator memory!");
        assert_eq!(memories_tools.len(), 2);

        let _ = fs::remove_dir_all(&temp_dir);
        println!("✅ ZERO MEMORY CONTAMINATION VERIFIED: Memories cleanly isolated at memories/{{username}}/{{agent_id}}!");
    }

    #[test]
    fn test_eval_intercept_gate_filters_out_incidents() {
        let temp_dir = std::env::temp_dir().join(format!("test_intercept_incidents_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        let shared_dir = temp_dir.join(".fl_brain/memories/shared");
        fs::create_dir_all(&shared_dir).unwrap();

        // 1. Legitimate memory
        let valid_mem = r#"---
id: "valid_helper_sol"
title: "Deterministic Helper Standard Operating Procedure"
category: "architecture"
keywords: ["helper", "deterministic", "procedure", "solution", "framework"]
---
Verified solution for helper functions.
"#;
        fs::write(shared_dir.join("valid_helper_sol.md"), valid_mem).unwrap();

        // 2. Incident file starting with incident_
        let inc_file = r#"---
id: "incident_helper_fail"
title: "Circuit Breaker Post-Mortem: deterministic_helper Failure"
category: "incident_remediation"
source: "circuit_breaker_crystallization"
keywords: ["helper", "deterministic", "failure_recovery", "incident"]
---
Faulting tool: deterministic_helper
"#;
        fs::write(shared_dir.join("incident_helper_12345.md"), inc_file).unwrap();

        // 3. Incident with different filename but category == "incident_remediation"
        let inc_cat = r#"---
id: "post_mortem_helper"
title: "Post-Mortem helper breakdown"
category: "incident_remediation"
keywords: ["helper", "deterministic", "crash"]
---
Helper crashed.
"#;
        fs::write(shared_dir.join("post_mortem_helper.md"), inc_cat).unwrap();

        let (injected, recalled) = SovereignTriggerEngine::eval_intercept_gate(
            "Working on deterministic helper procedure",
            &temp_dir,
            &temp_dir,
        );

        assert!(injected.contains("Deterministic Helper Standard Operating Procedure"), "Must recall valid solution");
        assert!(!injected.contains("incident_helper_fail"), "Must NOT recall incident file");
        assert!(!injected.contains("post_mortem_helper"), "Must NOT recall incident_remediation category");
        assert_eq!(recalled.len(), 1, "Only valid memory must be recalled");

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_4d_auto_jit_advisor_complete_dimensions_and_tier_gating() {
        let temp_dir = std::env::temp_dir().join(format!("test_4d_jit_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        let brain_dir = temp_dir.join(".fl_brain");
        fs::create_dir_all(&brain_dir).unwrap();

        // 1. Seed 6 memories in .fl_brain (testing top-5 quota cap & cross-agent availability)
        for i in 1..=6 {
            let m = format!(r#"---
id: mem_opt_{i}
title: Database WAL Concurrency Fix {i}
created_at: 2026-10-18T10:0{i}:00Z
category: database
keywords: ["database", "sqlite", "concurrency", "wal", "lock", "performance", "disk", "storage", "acid", "query"]
---
Solution {i}: Use PRAGMA journal_mode = WAL and busy_timeout = 5000.
"#);
            fs::write(brain_dir.join(format!("opt_{i}.md")), m).unwrap();
        }

        // 2. Candidate tools: 1 free, 3 pro tools
        let candidate_tools = vec![
            json!({
                "id": "db_inspect",
                "name": "Database Inspector",
                "description": "Inspect database schemas and tables",
                "keywords": ["database", "sqlite", "query"],
                "tier": "free",
                "pro": false
            }),
            json!({
                "id": "fl_hex_decompile_pro",
                "name": "Hex Decompiler Pro",
                "description": "Deep binary bytecode and database hex decompiler",
                "keywords": ["database", "binary", "decompile"],
                "tier": "pro",
                "pro": true
            }),
            json!({
                "id": "fl_db_pcap_analyzer",
                "name": "Database PCAP Protocol Dissector",
                "description": "Dissect low-level database protocol packets",
                "keywords": ["database", "pcap", "network"],
                "tier": "enterprise",
                "pro": true
            }),
            json!({
                "id": "fl_sqlite_wal_forensics",
                "name": "SQLite WAL Forensics Engine",
                "description": "Forensic recovery of corrupted WAL frames",
                "keywords": ["database", "sqlite", "wal", "forensics"],
                "tier": "pro",
                "pro": true
            })
        ];

        // 3. Local skills (testing top-3 quota cap)
        let local_skills = vec![
            json!({
                "id": "sqlite_wal_expert",
                "name": "SQLite WAL Concurrency Expert",
                "description": "Prosedur optimasi database WAL concurrency",
                "keywords": ["database", "sqlite", "wal", "concurrency"]
            }),
            json!({
                "id": "db_index_tuning",
                "name": "Database Index Tuning SOP",
                "description": "Prosedur penalaan indeks b-tree database",
                "keywords": ["database", "query", "index"]
            }),
            json!({
                "id": "acid_compliance_audit",
                "name": "ACID Compliance Audit",
                "description": "SOP audit kepatuhan transaksi database",
                "keywords": ["database", "acid", "transaction"]
            }),
            json!({
                "id": "database_sharding_sop",
                "name": "Database Sharding SOP",
                "description": "Prosedur partisi horisontal database",
                "keywords": ["database", "sharding", "distributed"]
            })
        ];

        // 4. Candidate apps (testing top-3 quota cap)
        let candidate_apps = vec![
            json!({
                "id": "db-visualizer",
                "name": "Database Schema Visualizer",
                "description": "Canvas interactive database table visualizer",
                "keywords": ["database", "schema", "table"]
            }),
            json!({
                "id": "query-workbench",
                "name": "Visual Query Workbench",
                "description": "Canvas visual SQL query execution studio",
                "keywords": ["database", "query", "sql"]
            }),
            json!({
                "id": "wal-monitor",
                "name": "WAL Realtime Monitor",
                "description": "Canvas chart monitor for sqlite WAL frame growth",
                "keywords": ["database", "sqlite", "wal"]
            }),
            json!({
                "id": "migration-studio",
                "name": "Schema Migration Studio",
                "description": "Canvas UI for visual database migrations",
                "keywords": ["database", "migration"]
            })
        ];

        // 4b. Seed source files with FL_INDEX to test Codebase Fingerprint Radar
        let src_file = temp_dir.join("db_pool.rs");
        fs::write(&src_file, "// [FL_INDEX: keywords=\"database, sqlite, wal, pool\" | purpose=\"High-performance WAL connection pool\"]\npub struct DbPool;\n").unwrap();

        // 5. Test Free Tier User Gating:
        // Free user must NOT get PRO tools!
        let free_res = SovereignTriggerEngine::eval_4d_auto_jit_advisor(
            "Optimizing sqlite database concurrency and wal performance",
            &temp_dir,
            &temp_dir,
            Some("free"),
            &candidate_tools,
            &local_skills,
            &[],
            &candidate_apps,
        ).expect("Must return JIT advisor block");

        assert!(free_res.contains("<SOVEREIGN_AUTO_JIT_ADVISOR>"));
        assert!(free_res.contains("3 rekomendasi tools yang berhubungan dengan pekerjaan kamu, silakan pin karna mungkin ini akan membantu"));
        assert!(free_res.contains("db_inspect"), "Free user can see free tools");
        assert!(!free_res.contains("fl_hex_decompile_pro"), "Free user MUST NOT see PRO tools!");
        assert!(!free_res.contains("fl_db_pcap_analyzer"), "Free user MUST NOT see Enterprise tools!");

        assert!(free_res.contains("Kamu didesain bukan menjadi AI sotoy yang hanya mengandalkan data training yang sudah usang"));
        assert!(free_res.contains("sqlite_wal_expert"));

        assert!(free_res.contains("<RELEVANT_APPS>"));
        assert!(free_res.contains("Ini daftar apps yang relevan yang bisa kamu gunakan:"));
        assert!(free_res.contains("db-visualizer"));

        // 4b. Seed source files with FL_INDEX to test Codebase Fingerprint Radar
        let src_file = temp_dir.join("db_pool.rs");
        fs::write(&src_file, "// [FL_INDEX: keywords=\"database, sqlite, wal, pool\" | purpose=\"High-performance WAL connection pool\"]\npub struct DbPool;\n").unwrap();

        assert!(free_res.contains("<HISTORICAL_BRAIN_MEMORIES>"));
        assert!(free_res.contains("Ini riwayat masa lalu yang berhubungan dengan topik yang sedang kamu tangani:"));
        assert!(free_res.contains("mem_opt_6"), "Newest memory must be included");
        assert!(!free_res.contains("mem_opt_1"), "Brain memories must be capped to maximum 5 items (oldest 6th item dropped)!");

        assert!(free_res.contains("<RELEVANT_CODE_FINGERPRINTS>"));
        assert!(free_res.contains("Berikut berkas kode dengan semantic index (FL_INDEX) yang relevan dengan tugas aktif:"));
        assert!(free_res.contains("db_pool.rs"));
        assert!(free_res.contains("High-performance WAL connection pool"));

        // 6. Test Pro Tier User: PRO tools are unlocked
        let pro_res = SovereignTriggerEngine::eval_4d_auto_jit_advisor(
            "Optimizing sqlite database concurrency and wal performance",
            &temp_dir,
            &temp_dir,
            Some("pro"),
            &candidate_tools,
            &local_skills,
            &[],
            &candidate_apps,
        ).expect("Must return JIT advisor block");

        assert!(pro_res.contains("fl_sqlite_wal_forensics") || pro_res.contains("fl_hex_decompile_pro"), "Pro user gets PRO tools unlocked");

        // 7. Test Zero-Bloat Bypass: Casual greeting produces 0 tokens
        let greeting_res = SovereignTriggerEngine::eval_4d_auto_jit_advisor(
            "halo bro apa kabar selamat pagi",
            &temp_dir,
            &temp_dir,
            Some("pro"),
            &candidate_tools,
            &local_skills,
            &[],
            &candidate_apps,
        );
        assert!(greeting_res.is_none(), "Ordinary greeting must produce None to avoid prompt bloat!");

        let _ = fs::remove_dir_all(&temp_dir);
        println!("✅ 4D AUTO-JIT ADVISOR VERIFIED: 3 tools, 3 skills, 3 apps, 5 memories, tier gating & zero bloat!");
    }

    #[test]
    fn test_canonical_keywords_loading_and_jit_injection() {
        let temp_dir = std::env::temp_dir().join(format!("test_kw_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        fs::create_dir_all(&temp_dir).unwrap();

        // 1. Verify load_canonical_keywords loads fallback embedded keywords
        let kw_text = SovereignTriggerEngine::load_canonical_keywords(&temp_dir, &temp_dir);
        assert!(!kw_text.is_empty(), "Canonical keywords must not be empty");
        assert!(kw_text.contains("Rekomendasi kata kunci, wajib pilih jika relevan dengan tugas kamu:"));
        assert!(kw_text.contains("sqlite_forensics"));
        assert!(kw_text.contains("adb_device"));
        assert!(kw_text.contains("gui_frontend"));
        assert!(kw_text.contains("constitution"));

        // 2. Verify eval_4d_auto_jit_advisor injects <SOVEREIGN_CANONICAL_KEYWORDS>
        let candidate_tools = vec![
            json!({
                "id": "fl_test_tool",
                "name": "Test Tool",
                "description": "A tool for testing",
                "keywords": ["test", "database", "sqlite"]
            })
        ];

        let res = SovereignTriggerEngine::eval_4d_auto_jit_advisor(
            "testing database sqlite forensics",
            &temp_dir,
            &temp_dir,
            Some("pro"),
            &candidate_tools,
            &[],
            &[],
            &[],
        ).expect("Must return advisor block");

        assert!(res.contains("<SOVEREIGN_CANONICAL_KEYWORDS>"));
        assert!(res.contains("Rekomendasi kata kunci, wajib pilih jika relevan dengan tugas kamu:"));
        assert!(res.contains("</SOVEREIGN_CANONICAL_KEYWORDS>"));
        assert!(res.contains("<SOVEREIGN_TOOL_RADAR>"));

        let _ = fs::remove_dir_all(&temp_dir);
    }
}

