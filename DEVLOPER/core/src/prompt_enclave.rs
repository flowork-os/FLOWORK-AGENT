// [FLOWORKOS:CRYPTOGRAPHIC_PROMPT_AND_URL_ENCLAVE]
// Dynamic disk reader enclave. ZERO prompts locked in binary.
// Prompts, doctrines, and templates are dynamically loaded from disk at runtime.

use crate::prompt_seal::CIPHER_KEY;

pub struct PromptEnclave;

impl PromptEnclave {
    #[inline]
    pub fn unseal(cipher: &[u8]) -> String {
        let mut decrypted = Vec::with_capacity(cipher.len());
        for (i, &byte) in cipher.iter().enumerate() {
            let k = CIPHER_KEY[i % CIPHER_KEY.len()];
            let s = (((i * 7) + 13) & 0xFF) as u8;
            decrypted.push(byte ^ k ^ s);
        }
        String::from_utf8(decrypted).unwrap_or_default()
    }

    pub fn read_system_file(rel_path: &str) -> String {
        if let Some(content) = crate::sealed_system::SealedSystemPrompts::get_by_path(rel_path) {
            return content;
        }
        let candidates = [
            format!("flowork/agents/system/{}", rel_path),
            format!("agents/system/{}", rel_path),
            format!("generator/xflow/agents/system/{}", rel_path),
            format!("../flowork/agents/system/{}", rel_path),
            format!("../../flowork/agents/system/{}", rel_path),
            format!("../../../flowork/agents/system/{}", rel_path),
        ];
        for path in &candidates {
            if let Ok(content) = std::fs::read_to_string(path) {
                return content;
            }
        }
        String::new()
    }

    #[inline] pub fn sovereign_engineering_soul() -> String { Self::read_system_file("sovereign_engineering_soul.md") }
    #[inline] pub fn sacred_files_directive() -> String { Self::read_system_file("sacred_files_directive.md") }
    #[inline] pub fn lock_immutability_rule() -> String { Self::read_system_file("lock_immutability.md") }
    #[inline] pub fn function_calling_protocol() -> String { Self::read_system_file("function_calling_protocol.md") }
    #[inline] pub fn ephemeral_message_doctrine() -> String { Self::read_system_file("doctrines/ephemeral_message_doctrine.md") }
    #[inline] pub fn vision_cortex_doctrine() -> String { Self::read_system_file("doctrines/vision_cortex_doctrine.md") }
    #[inline] pub fn caste_hierarchy_warning() -> String { Self::read_system_file("caste_hierarchy_warning.md") }
    #[inline] pub fn sacred_pillars_alert_prefix() -> String { Self::read_system_file("sacred_pillars_alert_prefix.md") }
    #[inline] pub fn sacred_pillars_alert_suffix() -> String { Self::read_system_file("sacred_pillars_alert_suffix.md") }
    #[inline] pub fn plugin_lifecycle_mandate() -> String { Self::read_system_file("plugin_lifecycle_mandate.md") }
    #[inline] pub fn slash_commands() -> String { Self::read_system_file("slash_commands.md") }
    #[inline] pub fn post_refactor_qc() -> String { Self::read_system_file("post_refactor_qc.md") }

    #[inline] pub fn autonomous_goal_directive() -> String { Self::read_system_file("autonomous_goal_directive.md") }
    #[inline] pub fn sovereign_task_continuation_directive() -> String { Self::read_system_file("sovereign_task_continuation_directive.md") }
    #[inline] pub fn conversation_transcript_doctrine(sessions_dir: &str) -> String {
        let tpl = Self::read_system_file("doctrines/conversation_transcript_doctrine.md");
        tpl.replace("{}", sessions_dir)
    }
    #[inline] pub fn active_viewport_awareness(tab: &str, title: &str, kind: &str, port: Option<u16>) -> String {
        let h = Self::read_system_file("active_viewport_awareness_header.md");
        let f = Self::read_system_file("active_viewport_awareness_footer.md");
        let mut out = format!("{}\n", h.replacen("{}", tab, 1).replacen("{}", title, 1).replacen("{}", kind, 1));
        if let Some(p) = port {
            out.push_str(&format!("• Port Engine      : `:{}` (Backend Live)\n", p));
        } else {
            out.push_str("• Port Engine      : None (Murni Tampilan GUI / Statis)\n");
        }
        out.push_str(&f);
        out
    }

    #[inline] pub fn sovereign_plugins_registry_header() -> String { Self::read_system_file("sovereign_plugins_registry_header.md") }
    #[inline] pub fn sovereign_plugins_registry_footer() -> String { Self::read_system_file("sovereign_plugins_registry_footer.md") }
    #[inline] pub fn active_open_plugins_header() -> String { Self::read_system_file("active_open_plugins_header.md") }
    #[inline] pub fn active_open_plugins_empty() -> String { Self::read_system_file("active_open_plugins_empty.md") }
    #[inline] pub fn active_open_plugins_footer() -> String { Self::read_system_file("active_open_plugins_footer.md") }
    #[inline] pub fn plugin_tool_auto_mount_header() -> String { Self::read_system_file("plugin_tool_auto_mount.md") }
    #[inline] pub fn plugin_tool_auto_mount_footer() -> String { Self::read_system_file("plugin_tool_auto_mount_footer.md") }
    #[inline] pub fn master_plugin_cognitive_instinct(path: &str) -> String {
        let tpl = Self::read_system_file("master_plugin_cognitive_instinct.md");
        tpl.replace("{}", path)
    }
    #[inline] pub fn sub_plugin_cognitive_instinct_header(sub_id: &str) -> String {
        let tpl = Self::read_system_file("sub_plugin_cognitive_instinct.md");
        tpl.replace("{}", sub_id)
    }
    #[inline] pub fn sub_plugin_cognitive_instinct_end() -> String { Self::read_system_file("sub_plugin_cognitive_instinct_end.md") }
    #[inline] pub fn mandatory_plugin_skill_doctrine() -> String { Self::read_system_file("doctrines/mandatory_plugin_skill_doctrine.md") }
    #[inline] pub fn planning_mode_artifacts() -> String { Self::read_system_file("planning_mode_artifacts.md") }
    #[inline] pub fn mandatory_plan_and_architecture_protocol() -> String { Self::read_system_file("mandatory_plan_and_architecture_protocol.md") }
    #[inline] pub fn sovereign_architect_blueprint() -> String { Self::read_system_file("sovereign_architect_blueprint.md") }
    #[inline] pub fn subagent_swarm_architecture() -> String { Self::read_system_file("subagent_swarm_architecture.md") }
    #[inline] pub fn swarm_coordinator_directive() -> String { Self::read_system_file("swarm_coordinator_directive.md") }
    #[inline] pub fn dynamic_external_tools_directive() -> String { Self::read_system_file("dynamic_external_tools_directive.md") }
    #[inline] pub fn domain_financial_markets() -> String { Self::read_system_file("domain_financial_markets.md") }
    #[inline] pub fn domain_digital_marketing() -> String { Self::read_system_file("domain_digital_marketing.md") }
    #[inline] pub fn domain_audio_engineering() -> String { Self::read_system_file("domain_audio_engineering.md") }
    #[inline] pub fn domain_cyber_security() -> String { Self::read_system_file("domain_cyber_security.md") }
    #[inline] pub fn persistent_context_header() -> String { Self::read_system_file("persistent_context_header.md") }
    #[inline] pub fn persistent_context_footer() -> String { Self::read_system_file("persistent_context_footer.md") }

    #[inline] pub fn sovereign_web_resilience() -> String { Self::read_system_file("sovereign_web_resilience.md") }
    #[inline] pub fn sovereign_youtube_intelligence() -> String { Self::read_system_file("sovereign_youtube_intelligence.md") }
    #[inline] pub fn autonomous_headless_mode() -> String { Self::read_system_file("autonomous_headless_mode.md") }
    #[inline] pub fn planning_mode_mandate() -> String { Self::read_system_file("planning_mode_mandate.md") }
    #[inline] pub fn subagent_worker_mandate() -> String { Self::read_system_file("subagent_worker_mandate.md") }
    #[inline] pub fn web_application_stack_discovery() -> String { Self::read_system_file("web_application_stack_discovery.md") }

    #[inline] pub fn doctrine_diagnosing_bugs() -> String { Self::read_system_file("doctrines/diagnosing_bugs.md") }
    #[inline] pub fn doctrine_tdd() -> String { Self::read_system_file("doctrines/tdd.md") }
    #[inline] pub fn doctrine_grill() -> String { Self::read_system_file("doctrines/grill.md") }
    #[inline] pub fn doctrine_counsel() -> String { Self::read_system_file("doctrines/counsel.md") }
    #[inline] pub fn active_engineering_doctrine_warning() -> String { Self::read_system_file("doctrines/active_engineering_doctrine_warning.md") }
    #[inline] pub fn doctrine_title_diagnose() -> String { Self::read_system_file("doctrines/title_diagnose.md") }
    #[inline] pub fn doctrine_title_tdd() -> String { Self::read_system_file("doctrines/title_tdd.md") }
    #[inline] pub fn doctrine_title_grill() -> String { Self::read_system_file("doctrines/title_grill.md") }
    #[inline] pub fn doctrine_title_counsel() -> String { Self::read_system_file("doctrines/title_counsel.md") }
    #[inline] pub fn doctrine_deep_modules() -> String { Self::read_system_file("doctrines/deep_modules.md") }
    #[inline] pub fn doctrine_domain_modeling_adr() -> String { Self::read_system_file("doctrines/domain_modeling_adr.md") }
    #[inline] pub fn doctrine_spec_and_triage() -> String { Self::read_system_file("doctrines/spec_and_triage.md") }
    #[inline] pub fn doctrine_handoff_and_prototype() -> String { Self::read_system_file("doctrines/handoff_and_prototype.md") }
    #[inline] pub fn doctrine_git_guardrails() -> String { Self::read_system_file("doctrines/git_guardrails.md") }
    #[inline] pub fn doctrine_title_deep_modules() -> String { Self::read_system_file("doctrines/title_deep_modules.md") }
    #[inline] pub fn doctrine_title_domain_modeling() -> String { Self::read_system_file("doctrines/title_domain_modeling.md") }
    #[inline] pub fn doctrine_title_spec_triage() -> String { Self::read_system_file("doctrines/title_spec_triage.md") }
    #[inline] pub fn doctrine_title_handoff_prototype() -> String { Self::read_system_file("doctrines/title_handoff_prototype.md") }
    #[inline] pub fn doctrine_title_git_guardrails() -> String { Self::read_system_file("doctrines/title_git_guardrails.md") }

    #[inline] pub fn doctrine_two_axis_review() -> String { Self::read_system_file("doctrines/two_axis_review.md") }
    #[inline] pub fn doctrine_reverse_engineering() -> String { Self::read_system_file("doctrines/reverse_engineering.md") }
    #[inline] pub fn doctrine_wayfinding() -> String { Self::read_system_file("doctrines/wayfinding.md") }
    #[inline] pub fn doctrine_primary_source() -> String { Self::read_system_file("doctrines/primary_source.md") }

    #[inline] pub fn doctrine_title_two_axis_review() -> String { Self::read_system_file("doctrines/title_two_axis_review.md") }
    #[inline] pub fn doctrine_title_reverse_engineering() -> String { Self::read_system_file("doctrines/title_reverse_engineering.md") }
    #[inline] pub fn doctrine_title_wayfinding() -> String { Self::read_system_file("doctrines/title_wayfinding.md") }
    #[inline] pub fn doctrine_title_primary_source() -> String { Self::read_system_file("doctrines/title_primary_source.md") }

    #[inline] pub fn universal_memory_doctrine() -> String { Self::read_system_file("doctrines/universal_memory_doctrine.md") }
    pub fn caller_and_workspace_boundary(username: &str, badge: &str, role: &str, level: u32, rank: &str, tier: &str, issuer: &str, date_time_str: &str, effective_ws: &str, ws_name: &str, session_id: &str, sessions_dir: &str) -> String {
        let tpl = Self::read_system_file("caller_and_workspace_template.md");
        tpl.replace("{username}", username)
            .replace("{badge}", badge)
            .replace("{role}", role)
            .replace("{level}", &level.to_string())
            .replace("{rank}", rank)
            .replace("{tier}", tier)
            .replace("{issuer}", issuer)
            .replace("{date_time_str}", date_time_str)
            .replace("{effective_ws}", effective_ws)
            .replace("{ws_name}", ws_name)
            .replace("{session_id}", session_id)
            .replace("{sessions_dir}", sessions_dir)
    }
    #[inline] pub fn caller_context_start() -> String { Self::read_system_file("caller_context_start.md") }
    #[inline] pub fn caller_context_end() -> String { Self::read_system_file("caller_context_end.md") }
    #[inline] pub fn active_workspace_territory_header() -> String { Self::read_system_file("active_workspace_territory_header.md") }
    #[inline] pub fn active_workspace_territory_footer() -> String { Self::read_system_file("active_workspace_territory_footer.md") }
    #[inline] pub fn pinned_skill_start() -> String { Self::read_system_file("pinned_skill_start.md") }
    #[inline] pub fn pinned_skill_end() -> String { Self::read_system_file("pinned_skill_end.md") }
    #[inline] pub fn pinned_skill_directive() -> String { Self::read_system_file("pinned_skill_directive.md") }
    #[inline] pub fn external_injection_header() -> String { Self::read_system_file("external_injection_header.md") }
    #[inline] pub fn external_injection_footer() -> String { Self::read_system_file("external_injection_footer.md") }
    #[inline] pub fn pinned_skill_warning() -> String { Self::read_system_file("pinned_skill_warning.md") }

    #[inline]
    pub fn sovereign_tool_declarations_json() -> String {
        let dump = Self::read_system_file("tool_declarations_dump.json");
        if !dump.is_empty() {
            return dump;
        }
        Self::read_system_file("sovereign_tool_declarations.json")
    }
    #[inline] pub fn plugin_skill_markdown() -> String { Self::read_system_file("plugin_skill.md") }
    #[inline] pub fn skills_skill_markdown() -> String { Self::read_system_file("skills_readme.md") }
    #[inline]
    pub fn persona_skill_markdown() -> String {
        let content = Self::read_system_file("persona_skill.md");
        if !content.is_empty() {
            return content;
        }
        r#"---
name: persona-trigger-architecture
description: Sovereign Persona Trigger Architecture & Specialist Runbook Routing
keywords:
  - persona
  - trigger
  - architecture
  - specialist
  - routing
  - dispatcher
  - isolation
  - execution
  - sovereign
  - system
  - engine
  - agent
  - protocol
  - lifecycle
  - autonomous
  - context
  - workspace
  - workflow
  - security
  - guard
---
# Persona Trigger Architecture
Privilege Separation & Isolation Guard
Autonomous Self-Healing
"#.to_string()
    }
    #[inline] pub fn tools_skill_markdown() -> String { Self::read_system_file("tools_readme.md") }
    #[inline] pub fn skills_readme_markdown() -> String { Self::skills_skill_markdown() }
    #[inline] pub fn tools_readme_markdown() -> String { Self::tools_skill_markdown() }

    #[inline] pub fn name_awenk() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_NAME_AWENK, &crate::sovereign_enclave::FP_NAME_AWENK) }
    #[inline] pub fn name_teguh() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_NAME_TEGUH, &crate::sovereign_enclave::FP_NAME_TEGUH) }
    #[inline] pub fn name_awenk_lower() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_NAME_AWENK_LOWER, &crate::sovereign_enclave::FP_NAME_AWENK_LOWER) }
    #[inline] pub fn name_teguh_lower() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_NAME_TEGUH_LOWER, &crate::sovereign_enclave::FP_NAME_TEGUH_LOWER) }
    #[inline] pub fn title_creator() -> String { "PENCIPTA UTAMA & PEMILIK OTORITAS RESMI TERTINGGI".to_string() }
    #[inline] pub fn title_authority() -> String { "PEMILIK OTORITAS RESMI TERTINGGI".to_string() }

    #[inline] pub fn proto_https() -> String { "https://".to_string() }
    #[inline] pub fn proto_http() -> String { "http://".to_string() }

    #[inline] pub fn url_auth() -> String { crate::sovereign_enclave::unseal_verified_granular(crate::sovereign_enclave::CIPHER_URL_AUTH, &crate::sovereign_enclave::FP_URL_AUTH_GRANULAR) }
    #[inline] pub fn url_launcher() -> String { crate::sovereign_enclave::unseal_verified_granular(crate::sovereign_enclave::CIPHER_URL_LAUNCHER, &crate::sovereign_enclave::FP_URL_LAUNCHER) }
    #[inline] pub fn url_canvas_stage() -> String { crate::sovereign_enclave::unseal_verified_granular(crate::sovereign_enclave::CIPHER_URL_CANVAS_STAGE, &crate::sovereign_enclave::FP_URL_CANVAS_STAGE) }
    #[inline] pub fn url_plugins() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_PLUGINS, &crate::sovereign_enclave::FP_URL_PLUGINS) }
    #[inline] pub fn url_plugins_search() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_PLUGINS_SEARCH, &crate::sovereign_enclave::FP_URL_PLUGINS_SEARCH) }
    #[inline] pub fn url_plugins_contribute() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_PLUGINS_CONTRIBUTE, &crate::sovereign_enclave::FP_URL_PLUGINS_CONTRIBUTE) }
    #[inline] pub fn url_skills_search() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_SKILLS_SEARCH, &crate::sovereign_enclave::FP_URL_SKILLS_SEARCH) }
    #[inline] pub fn url_skills_contribute() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_SKILLS_CONTRIBUTE, &crate::sovereign_enclave::FP_URL_SKILLS_CONTRIBUTE) }
    #[inline] pub fn url_skills_repo() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_SKILLS_REPO, &crate::sovereign_enclave::FP_URL_SKILLS_REPO) }
    #[inline] pub fn url_linux_plugin() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_LINUX_PLUGIN, &crate::sovereign_enclave::FP_URL_LINUX_PLUGIN) }
    #[inline] pub fn url_windows_plugin() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_WINDOWS_PLUGIN, &crate::sovereign_enclave::FP_URL_WINDOWS_PLUGIN) }
    #[inline] pub fn url_skills_tarball() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_SKILLS_TARBALL, &crate::sovereign_enclave::FP_URL_SKILLS_TARBALL) }
    #[inline] pub fn url_skills_raw_json() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_SKILLS_RAW_JSON, &crate::sovereign_enclave::FP_URL_SKILLS_RAW_JSON) }
    #[inline] pub fn url_github_raw_base() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_GITHUB_RAW_BASE, &crate::sovereign_enclave::FP_URL_GITHUB_RAW_BASE) }
    #[inline] pub fn url_github_codeload_base() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_GITHUB_CODELOAD_BASE, &crate::sovereign_enclave::FP_URL_GITHUB_CODELOAD_BASE) }
    #[inline] pub fn url_github_api_repos() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_GITHUB_API_REPOS, &crate::sovereign_enclave::FP_URL_GITHUB_API_REPOS) }
    #[inline] pub fn url_github_flowork_base() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_GITHUB_FLOWORK_BASE, &crate::sovereign_enclave::FP_URL_GITHUB_FLOWORK_BASE) }
    #[inline] pub fn url_release_checksums() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_RELEASE_CHECKSUMS, &crate::sovereign_enclave::FP_URL_RELEASE_CHECKSUMS) }
    #[inline] pub fn url_local_canvas_19890() -> String { format!("{}127.0.0.1:19890", Self::proto_http()) }
    #[inline] pub fn url_local_canvas_host() -> String { format!("{}localhost:19890", Self::proto_http()) }

    #[inline] pub fn url_crates_search() -> String { "https://crates.io/api/v1/crates?q={}&per_page=5".to_string() }
    #[inline] pub fn url_crates_base() -> String { "https://crates.io/crates/".to_string() }
    #[inline] pub fn url_wikipedia_search() -> String { "https://en.wikipedia.org/w/api.php?action=opensearch&search={}&limit=4&format=json".to_string() }
    #[inline] pub fn url_rdap_base() -> String { "https://rdap.org/domain/".to_string() }
    #[inline] pub fn url_dns_google_base() -> String { "https://dns.google/resolve".to_string() }
    #[inline] pub fn url_crt_sh_base() -> String { "https://crt.sh/?q=%25.".to_string() }
    #[inline] pub fn url_similarweb_base() -> String { "https://data.similarweb.com/api/v1/data?domain=".to_string() }
    #[inline] pub fn url_wayback_base() -> String { "https://web.archive.org/cdx/search/cdx?url=".to_string() }
    #[inline] pub fn url_youtube_base() -> String { "https://www.youtube.com/".to_string() }
    #[inline] pub fn url_youtube_watch() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_YOUTUBE_WATCH, &crate::sovereign_enclave::FP_URL_YOUTUBE_WATCH) }
    #[inline] pub fn url_youtube_m_watch() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_YOUTUBE_M_WATCH, &crate::sovereign_enclave::FP_URL_YOUTUBE_M_WATCH) }
    #[inline] pub fn url_youtube_channel() -> String { "https://www.youtube.com/channel/".to_string() }
    #[inline] pub fn url_youtube_user() -> String { "https://www.youtube.com/@".to_string() }
    #[inline] pub fn url_youtube_oembed() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_YOUTUBE_OEMBED, &crate::sovereign_enclave::FP_URL_YOUTUBE_OEMBED) }
    #[inline] pub fn url_youtube_player_api() -> String { "https://www.youtube.com/youtubei/v1/player?prettyPrint=false".to_string() }
    #[inline] pub fn url_youtube_origin() -> String { "https://m.youtube.com".to_string() }
    #[inline] pub fn url_youtube_img_hq() -> String { "https://i.ytimg.com/vi/".to_string() }

    #[inline] pub fn url_gdrive_auth() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_GDRIVE_AUTH, &crate::sovereign_enclave::FP_URL_GDRIVE_AUTH) }
    #[inline] pub fn url_gdrive_token() -> String { format!("{}oauth2.googleapis.com/token", Self::proto_https()) }
    #[inline] pub fn url_gdrive_about() -> String { format!("{}www.googleapis.com/drive/v3/about?fields=user", Self::proto_https()) }
    #[inline] pub fn url_gdrive_quota() -> String { format!("{}www.googleapis.com/drive/v3/about?fields=storageQuota", Self::proto_https()) }
    #[inline] pub fn url_gdrive_files() -> String { format!("{}www.googleapis.com/drive/v3/files", Self::proto_https()) }
    #[inline] pub fn url_gdrive_upload() -> String { format!("{}www.googleapis.com/upload/drive/v3/files?uploadType=multipart", Self::proto_https()) }
    #[inline] pub fn url_gdrive_view() -> String { format!("{}drive.google.com/file/d/", Self::proto_https()) }

    #[inline] pub fn jurisdiction_matrix() -> String { Self::read_system_file("categories/JURISDICTION_MATRIX.md") }
    #[inline] pub fn url_prompt_dispatch_19890() -> String { "http://127.0.0.1:19890/api/prompt-dispatch".to_string() }
    #[inline] pub fn url_prompt_dispatch_9099() -> String { "http://127.0.0.1:9099/api/prompt-dispatch".to_string() }
    #[inline] pub fn url_prompt_dispatch_17700() -> String { "http://127.0.0.1:17700/api/prompt-dispatch".to_string() }
    #[inline] pub fn prompt_dispatch_endpoints() -> Vec<String> {
        vec![
            Self::url_prompt_dispatch_19890(),
            Self::url_prompt_dispatch_9099(),
            Self::url_prompt_dispatch_17700(),
        ]
    }
    #[inline] pub fn url_github_skills_categories_base() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_URL_GITHUB_SKILLS_CATEGORIES_BASE, &crate::sovereign_enclave::FP_URL_GITHUB_SKILLS_CATEGORIES_BASE) }
    #[inline] pub fn schema_skill_registry_v2() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_SCHEMA_SKILL_REGISTRY_V2, &crate::sovereign_enclave::FP_SCHEMA_SKILL_REGISTRY_V2) }
    #[inline] pub fn schema_agent_v2() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_SCHEMA_AGENT_V2, &crate::sovereign_enclave::FP_SCHEMA_AGENT_V2) }
    #[inline] pub fn model_default() -> String { crate::sovereign_enclave::unseal_verified(crate::sovereign_enclave::CIPHER_MODEL_DEFAULT, &crate::sovereign_enclave::FP_MODEL_DEFAULT) }


    #[inline] pub fn teamwork_blueprint() -> String { Self::read_system_file("teamwork_architecture_blueprint.md") }
    #[inline] pub fn teamwork_prompts_catalog() -> String { Self::read_system_file("prompts_catalog.md") }
    #[inline] pub fn prompt_solo() -> String { Self::read_system_file("promp_solo.md") }
    #[inline] pub fn prompt_solo_squad() -> String {
        let s = Self::read_system_file("promp_solo_squad.md");
        if !s.is_empty() { s } else { Self::prompt_solo_spesialis() }
    }
    #[inline] pub fn prompt_solo_spesialis() -> String { Self::read_system_file("promp_solo_spesialis.md") }
    #[inline] pub fn prompt_team() -> String { Self::read_system_file("promp_team.md") }
    #[inline] pub fn prompt_team_default() -> String {
        let s = Self::read_system_file("promp_team_default.md");
        if !s.is_empty() { s } else { Self::prompt_team() }
    }
    #[inline] pub fn prompt_team_squad() -> String {
        let s = Self::read_system_file("promp_team_squad.md");
        if !s.is_empty() { s } else { Self::prompt_team_spesialis() }
    }
    #[inline] pub fn prompt_team_spesialis() -> String { Self::read_system_file("promp_team_spesialis.md") }

    pub fn all_teamwork_files() -> Vec<(&'static str, String)> {
        vec![
            ("teamwork_architecture_blueprint.md", Self::teamwork_blueprint()),
            ("prompts_catalog.md", Self::teamwork_prompts_catalog()),
        ]
    }

    #[inline] pub fn url_duckduckgo_search() -> String { format!("{}html.duckduckgo.com/html/?q=", Self::proto_https()) }
    #[inline] pub fn url_canvas_office_3d() -> String { format!("{}/office_3d.js", Self::url_canvas_stage()) }
    #[inline] pub fn url_canvas_cdn_base() -> String { Self::url_canvas_stage() }
    #[inline] pub fn gdrive_client_id() -> String { "1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com".to_string() }

    pub fn all_category_templates() -> Vec<(String, String)> {
        crate::sealed_system::SealedSystemPrompts::all_category_templates()
    }
}
