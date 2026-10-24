//! [FLOWORKOS:AGENTS_ENGINE]
//! Sovereign Subagent Squad Engine and Role Resolution Registry
//! Co-authored-by: Flowork OS <agent@floworkos.com>

use std::path::{Path, PathBuf};
use serde_json::Value;

pub use crate::persona::ToolRunStats;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum AgentCategory {
    Healthcare,
    Psychology,
    Legal,
    Education,
    Technology,
    Finance,
    Business,
    Marketing,
    Advertising,
    MediaCreative,
    Design,
    HumanResources,
    ScienceResearch,
    AutomationAdmin,
    Core,
    ArtsMusicPoetry,
    MetaphysicsFengShui,
    ArchitectureSpatial,
    CulinaryGastronomy,
    SportsAthletics,
    AgricultureEcology,
    DiplomacyNegotiation,
    CybersecurityForensics,
    HospitalityTourism,
    MaritimeLogistics,
    System,
}

impl AgentCategory {
    pub fn all() -> &'static [AgentCategory] {
        &[
            AgentCategory::Healthcare,
            AgentCategory::Psychology,
            AgentCategory::Legal,
            AgentCategory::Education,
            AgentCategory::Technology,
            AgentCategory::Finance,
            AgentCategory::Business,
            AgentCategory::Marketing,
            AgentCategory::Advertising,
            AgentCategory::MediaCreative,
            AgentCategory::Design,
            AgentCategory::HumanResources,
            AgentCategory::ScienceResearch,
            AgentCategory::AutomationAdmin,
            AgentCategory::Core,
            AgentCategory::ArtsMusicPoetry,
            AgentCategory::MetaphysicsFengShui,
            AgentCategory::ArchitectureSpatial,
            AgentCategory::CulinaryGastronomy,
            AgentCategory::SportsAthletics,
            AgentCategory::AgricultureEcology,
            AgentCategory::DiplomacyNegotiation,
            AgentCategory::CybersecurityForensics,
            AgentCategory::HospitalityTourism,
            AgentCategory::MaritimeLogistics,
            AgentCategory::System,
        ]
    }

    pub fn id(&self) -> &'static str {
        match self {
            AgentCategory::Healthcare => "CAT-001",
            AgentCategory::Psychology => "CAT-002",
            AgentCategory::Legal => "CAT-003",
            AgentCategory::Education => "CAT-004",
            AgentCategory::Technology => "CAT-005",
            AgentCategory::Finance => "CAT-006",
            AgentCategory::Business => "CAT-007",
            AgentCategory::Marketing => "CAT-008",
            AgentCategory::Advertising => "CAT-009",
            AgentCategory::MediaCreative => "CAT-010",
            AgentCategory::Design => "CAT-011",
            AgentCategory::HumanResources => "CAT-012",
            AgentCategory::ScienceResearch => "CAT-013",
            AgentCategory::AutomationAdmin => "CAT-014",
            AgentCategory::Core => "CAT-015",
            AgentCategory::ArtsMusicPoetry => "CAT-016",
            AgentCategory::MetaphysicsFengShui => "CAT-017",
            AgentCategory::ArchitectureSpatial => "CAT-018",
            AgentCategory::CulinaryGastronomy => "CAT-019",
            AgentCategory::SportsAthletics => "CAT-020",
            AgentCategory::AgricultureEcology => "CAT-021",
            AgentCategory::DiplomacyNegotiation => "CAT-022",
            AgentCategory::CybersecurityForensics => "CAT-023",
            AgentCategory::HospitalityTourism => "CAT-024",
            AgentCategory::MaritimeLogistics => "CAT-025",
            AgentCategory::System => "CAT-026",
        }
    }

    pub fn slug(&self) -> &'static str {
        match self {
            AgentCategory::Healthcare => "healthcare",
            AgentCategory::Psychology => "psychology",
            AgentCategory::Legal => "legal",
            AgentCategory::Education => "education",
            AgentCategory::Technology => "technology",
            AgentCategory::Finance => "finance",
            AgentCategory::Business => "business",
            AgentCategory::Marketing => "marketing",
            AgentCategory::Advertising => "advertising",
            AgentCategory::MediaCreative => "media_creative",
            AgentCategory::Design => "design",
            AgentCategory::HumanResources => "human_resources",
            AgentCategory::ScienceResearch => "science_research",
            AgentCategory::AutomationAdmin => "automation_admin",
            AgentCategory::Core => "core",
            AgentCategory::ArtsMusicPoetry => "arts_music_poetry",
            AgentCategory::MetaphysicsFengShui => "metaphysics_fengshui",
            AgentCategory::ArchitectureSpatial => "architecture_spatial",
            AgentCategory::CulinaryGastronomy => "culinary_gastronomy",
            AgentCategory::SportsAthletics => "sports_athletics",
            AgentCategory::AgricultureEcology => "agriculture_ecology",
            AgentCategory::DiplomacyNegotiation => "diplomacy_negotiation",
            AgentCategory::CybersecurityForensics => "cybersecurity_forensics",
            AgentCategory::HospitalityTourism => "hospitality_tourism",
            AgentCategory::MaritimeLogistics => "maritime_logistics",
            AgentCategory::System => "system",
        }
    }

    pub fn title(&self) -> &'static str {
        match self {
            AgentCategory::Healthcare => "Healthcare & Medicine",
            AgentCategory::Psychology => "Psychology & Counseling",
            AgentCategory::Legal => "Legal & Contracts",
            AgentCategory::Education => "Education & Learning",
            AgentCategory::Technology => "Technology & Software Engineering",
            AgentCategory::Finance => "Finance & Accounting",
            AgentCategory::Business => "Business & Strategy",
            AgentCategory::Marketing => "Marketing & Growth",
            AgentCategory::Advertising => "Advertising & Media Buying",
            AgentCategory::MediaCreative => "Media & Content Creation",
            AgentCategory::Design => "Design & User Interface",
            AgentCategory::HumanResources => "Human Resources & Recruitment",
            AgentCategory::ScienceResearch => "Science & Research",
            AgentCategory::AutomationAdmin => "Automation & Operations",
            AgentCategory::Core => "Core Universal System",
            AgentCategory::ArtsMusicPoetry => "Arts, Music & Poetry",
            AgentCategory::MetaphysicsFengShui => "Metaphysics & Feng Shui",
            AgentCategory::ArchitectureSpatial => "Architecture & Spatial Design",
            AgentCategory::CulinaryGastronomy => "Culinary Arts & Gastronomy",
            AgentCategory::SportsAthletics => "Sports & Athletics",
            AgentCategory::AgricultureEcology => "Agriculture & Ecology",
            AgentCategory::DiplomacyNegotiation => "Diplomacy & Negotiation",
            AgentCategory::CybersecurityForensics => "Cybersecurity & Digital Forensics",
            AgentCategory::HospitalityTourism => "Hospitality & Tourism",
            AgentCategory::MaritimeLogistics => "Maritime & Global Logistics",
            AgentCategory::System => "System Administration & Infrastructure",
        }
    }

    pub fn from_str_loose(s: &str) -> AgentCategory {
        let clean = s.to_lowercase().trim().to_string();
        for &cat in Self::all() {
            if clean == cat.id().to_lowercase() || clean == cat.slug() || clean == cat.title().to_lowercase() {
                return cat;
            }
        }
        if clean.contains("coder") || clean.contains("developer") || clean.contains("programmer") {
            return AgentCategory::Technology;
        }
        match clean.as_str() {
            "technology" | "tech" | "coding" | "coder" | "coder-specialist" | "software" | "backend" | "frontend" => AgentCategory::Technology,
            "design" | "ui" | "ux" => AgentCategory::Design,
            "marketing" => AgentCategory::Marketing,
            "finance" => AgentCategory::Finance,
            "business" => AgentCategory::Business,
            "legal" => AgentCategory::Legal,
            "healthcare" | "health" => AgentCategory::Healthcare,
            "education" => AgentCategory::Education,
            "cybersecurity" | "security" => AgentCategory::CybersecurityForensics,
            "system" => AgentCategory::System,
            _ => AgentCategory::Core,
        }
    }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct GuardianFilesystemPolicy {
    pub allowed_extensions: Option<Vec<String>>,
    pub prohibited_extensions: Option<Vec<String>>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct GuardianRule {
    #[serde(default)]
    pub allow: Vec<String>,
    #[serde(default)]
    pub deny: Vec<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct GuardianPolicy {
    pub filesystem: Option<GuardianFilesystemPolicy>,
    pub tools: Option<GuardianRule>,
    pub dispatch: Option<Vec<String>>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct AgentMatchResult {
    pub agent_id: String,
    pub persona_name: String,
    pub target_type: String,
    pub doc_id: String,
    pub priority: u32,
    pub match_reasons: Vec<String>,
    pub body_markdown: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct AgentManifest {
    pub id: String,
    pub name: Option<String>,
    pub category: Option<String>,
    #[serde(default)]
    pub allowed_tools: Vec<String>,
    #[serde(default)]
    pub default_tools: Vec<String>,
    #[serde(default)]
    pub locked_tools: Vec<String>,
    pub guardian: Option<GuardianPolicy>,
}

impl AgentManifest {
    pub fn is_tool_locked(&self, tool: &str) -> bool {
        self.locked_tools.iter().any(|t| t.to_lowercase() == tool.to_lowercase())
    }

    pub fn is_tool_allowed_by_guardian(&self, tool: &str) -> Option<bool> {
        if self.is_tool_locked(tool) {
            return Some(false);
        }
        if let Some(guardian) = &self.guardian {
            if let Some(tools_rule) = &guardian.tools {
                let tool_lower = tool.to_lowercase();
                if tools_rule.deny.iter().any(|d| d == "*" || tool_lower.contains(&d.to_lowercase())) {
                    return Some(false);
                }
                if !tools_rule.allow.is_empty() && !tools_rule.allow.iter().any(|a| a == "*" || tool_lower.contains(&a.to_lowercase())) {
                    return Some(false);
                }
            }
        }
        None
    }

    pub fn is_command_allowed(&self, cmd: &str) -> Result<(), String> {
        if let Some(guardian) = &self.guardian {
            if let Some(tools_rule) = &guardian.tools {
                let cmd_lower = cmd.to_lowercase();
                for deny in &tools_rule.deny {
                    if !deny.is_empty() && (deny == "*" || cmd_lower.contains(&deny.to_lowercase())) {
                        return Err(format!("Command prohibited by guardian deny pattern: '{}'", deny));
                    }
                }
            }
        }
        Ok(())
    }

    pub fn is_file_access_allowed(&self, path: &str) -> Result<(), String> {
        if let Some(guardian) = &self.guardian {
            if let Some(fs) = &guardian.filesystem {
                let path_lower = path.to_lowercase();
                if let Some(prohibited) = &fs.prohibited_extensions {
                    for ext in prohibited {
                        if path_lower.ends_with(&ext.to_lowercase()) {
                            return Err(format!("Extension '{}' is prohibited by guardian policy", ext));
                        }
                    }
                }
                if let Some(allowed) = &fs.allowed_extensions {
                    if !allowed.iter().any(|ext| path_lower.ends_with(&ext.to_lowercase())) {
                        return Err(format!("File extension for '{}' is not in allowed extensions: {:?}", path, allowed));
                    }
                }
            }
        }
        Ok(())
    }
}

pub struct SovereignAgentsEngine;

impl SovereignAgentsEngine {
    pub fn resolve_agent_roots(workspace: &Path, engine_root: &Path) -> Vec<PathBuf> {
        let mut roots = crate::persona::SovereignPersonaEngine::resolve_persona_roots(workspace, engine_root);
        let candidates = [
            engine_root.join("system").join("subagent"),
            workspace.join("system").join("subagent"),
            engine_root.join("portable-home").join(".flowork").join("subagents"),
        ];
        for sub in &candidates {
            if sub.exists() && !roots.contains(sub) {
                roots.push(sub.clone());
            }
        }
        roots
    }

    pub fn resolve_agent_metadata(agent_roots: &[PathBuf], agent_id: &str) -> (Option<Value>, String) {
        let clean_id = agent_id.trim().trim_start_matches("group-").to_lowercase();
        for root in agent_roots {
            let candidate = root.join(&clean_id);
            if candidate.exists() {
                let manifest_path = candidate.join("agent.json");
                if manifest_path.exists() {
                    if let Ok(c) = std::fs::read_to_string(&manifest_path) {
                        if let Ok(v) = serde_json::from_str::<Value>(&c) {
                            let cat = v.get("category").and_then(|x| x.as_str()).unwrap_or("general").to_string();
                            return (Some(v), cat);
                        }
                    }
                }
            }
        }
        (None, "general".to_string())
    }

    pub fn load_agent_manifest(agent_roots: &[PathBuf], agent_id: &str) -> Option<AgentManifest> {
        let clean_id = agent_id.trim().trim_start_matches("group-").to_lowercase();
        for root in agent_roots {
            let candidate = root.join(&clean_id);
            if candidate.exists() {
                let manifest_path = candidate.join("agent.json");
                if manifest_path.exists() {
                    if let Ok(c) = std::fs::read_to_string(&manifest_path) {
                        if let Ok(m) = serde_json::from_str::<AgentManifest>(&c) {
                            return Some(m);
                        }
                    }
                }
            }
        }
        None
    }

    pub fn compose_top_single_agent_block(matches: &[AgentMatchResult]) -> String {
        let p_matches: Vec<crate::persona::PersonaMatchResult> = matches.iter().map(|m| crate::persona::PersonaMatchResult {
            persona_name: m.persona_name.clone(),
            target_type: m.target_type.clone(),
            doc_id: m.doc_id.clone(),
            priority: m.priority,
            match_reasons: m.match_reasons.clone(),
            body_markdown: m.body_markdown.clone(),
        }).collect();
        crate::persona::SovereignPersonaEngine::compose_top_single_persona_block(&p_matches)
    }
}
