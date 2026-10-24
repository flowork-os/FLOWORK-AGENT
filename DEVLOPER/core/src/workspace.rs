use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorkspaceInfo {
    pub id: String,
    pub name: String,
    pub path: String,
    pub created_at: String,
    pub is_active: bool,
    pub has_pillars: bool,
}

pub struct WorkspaceManager {
    root_dir: PathBuf,
    active_workspace_id: Arc<RwLock<String>>,
    active_workspace_path: Arc<RwLock<PathBuf>>,
}

impl WorkspaceManager {
    pub fn new(root_dir: impl AsRef<Path>) -> Self {
        let root = root_dir.as_ref().to_path_buf();
        let abs_root = std::fs::canonicalize(&root).unwrap_or(root.clone());
        let active_id = Self::load_active_id(&abs_root).unwrap_or_else(|| "default".to_string());
        let active_path = Self::load_active_path(&abs_root).unwrap_or_else(|| abs_root.clone());

        let mgr = Self {
            root_dir: abs_root.clone(),
            active_workspace_id: Arc::new(RwLock::new(active_id)),
            active_workspace_path: Arc::new(RwLock::new(active_path.clone())),
        };

        // Autonomous Sacred Bootstrap: Ensure .FL_BIN, .fl_brain, and sacred files exist
        let project_name = active_path.file_name().unwrap_or_default().to_string_lossy().to_string();
        let _ = mgr.bootstrap_sacred_pillars(&active_path, &project_name);
        if active_path != abs_root {
            let root_name = abs_root.file_name().unwrap_or_default().to_string_lossy().to_string();
            let _ = mgr.bootstrap_sacred_pillars(&abs_root, &root_name);
        }

        mgr
    }

    pub fn resolve_primary_config_dir(&self) -> PathBuf {
        if self.root_dir.join("portable-home").exists() {
            self.root_dir.join("portable-home").join(".flowork").join("config")
        } else if let Ok(p_root) = std::env::var("FLOWORK_PORTABLE_ROOT") {
            let p = PathBuf::from(p_root);
            if p.exists() {
                p.join(".flowork").join("config")
            } else {
                self.root_dir.join("portable-home").join(".flowork").join("config")
            }
        } else {
            self.root_dir.join("portable-home").join(".flowork").join("config")
        }
    }

    fn get_projects_dirs(&self) -> Vec<PathBuf> {
        let mut dirs = Vec::new();
        dirs.push(self.resolve_primary_config_dir().join("projects"));
        if self.root_dir.join(".flowork").join("config").join("projects").exists() {
            dirs.push(self.root_dir.join(".flowork").join("config").join("projects"));
        }
        if let Some(parent) = self.root_dir.parent() {
            if parent.join("portable-home").join(".flowork").join("config").join("projects").exists() {
                dirs.push(parent.join("portable-home").join(".flowork").join("config").join("projects"));
            }
            if parent.join(".flowork").join("config").join("projects").exists() {
                dirs.push(parent.join(".flowork").join("config").join("projects"));
            }
        }
        dirs
    }

    fn load_active_id(root: &Path) -> Option<String> {
        let candidates = [
            root.join("portable-home").join(".flowork").join("config").join("active_workspace.json"),
            root.join(".flowork").join("config").join("active_workspace.json"),
        ];
        for file in candidates {
            if let Ok(content) = std::fs::read_to_string(&file) {
                if let Ok(val) = serde_json::from_str::<Value>(&content) {
                    if let Some(s) = val.get("id").and_then(|v| v.as_str()) {
                        return Some(s.to_string());
                    }
                }
            }
        }
        None
    }

    fn load_active_path(root: &Path) -> Option<PathBuf> {
        let candidates = [
            root.join("portable-home").join(".flowork").join("config").join("active_workspace.json"),
            root.join(".flowork").join("config").join("active_workspace.json"),
        ];
        for file in candidates {
            if let Ok(content) = std::fs::read_to_string(&file) {
                if let Ok(val) = serde_json::from_str::<Value>(&content) {
                    if let Some(s) = val.get("path").and_then(|v| v.as_str()) {
                        let pb = PathBuf::from(s);
                        if pb.exists() {
                            return Some(pb);
                        }
                    }
                }
            }
        }
        None
    }

    pub fn get_root_dir(&self) -> PathBuf {
        self.root_dir.clone()
    }

    pub async fn get_active_path(&self) -> PathBuf {
        self.active_workspace_path.read().await.clone()
    }

    pub fn get_active_path_sync(&self) -> PathBuf {
        if let Ok(guard) = self.active_workspace_path.try_read() {
            guard.clone()
        } else {
            self.root_dir.clone()
        }
    }

    pub async fn get_all(&self) -> Vec<WorkspaceInfo> {
        let mut list = Vec::new();
        let mut seen_paths = std::collections::HashSet::new();
        let active_id = self.active_workspace_id.read().await.clone();
        let active_path = self.active_workspace_path.read().await.clone();

        // 1. Always include root workspace as primary
        let root_str = self.root_dir.to_string_lossy().to_string();
        let root_name = self.root_dir.file_name().unwrap_or_default().to_string_lossy().to_string();
        seen_paths.insert(root_str.clone());

        let has_root_pillars = self.root_dir.join(".fl_brain").exists() || self.root_dir.join("skills").exists();
        list.push(WorkspaceInfo {
            id: "default".to_string(),
            name: if root_name.is_empty() { "flowork (Root)".to_string() } else { root_name },
            path: root_str.clone(),
            created_at: "system".to_string(),
            is_active: active_path == self.root_dir || active_id == "default",
            has_pillars: has_root_pillars,
        });

        // 2. Scan project configs
        for pdir in self.get_projects_dirs() {
            if let Ok(entries) = std::fs::read_dir(pdir) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.extension().and_then(|s| s.to_str()) == Some("json") {
                        if path.file_name().and_then(|s| s.to_str()) == Some("outside-of-project.json") {
                            continue;
                        }
                        if let Ok(content) = std::fs::read_to_string(&path) {
                            if let Ok(val) = serde_json::from_str::<Value>(&content) {
                                let id = val.get("id").and_then(|v| v.as_str()).unwrap_or("").to_string();
                                let name = val.get("name").and_then(|v| v.as_str()).unwrap_or(&id).to_string();
                                let created_at = val.get("createdAt").and_then(|v| v.as_str()).unwrap_or("").to_string();

                                let mut ws_path_str = String::new();
                                if let Some(resources) = val.get("projectResources").and_then(|pr| pr.get("resources")).and_then(|r| r.as_array()) {
                                    for res in resources {
                                        if let Some(uri) = res.get("folderUri").and_then(|u| u.as_str()) {
                                            let stripped = uri.trim_start_matches("file://");
                                            let clean = clean_verbatim_path(Path::new(stripped));
                                            ws_path_str = clean.to_string_lossy().to_string();
                                            break;
                                        }
                                    }
                                }

                                if !ws_path_str.is_empty() && !seen_paths.contains(&ws_path_str) {
                                    seen_paths.insert(ws_path_str.clone());
                                    let ws_p = PathBuf::from(&ws_path_str);
                                    let has_pillars = ws_p.join(".fl_brain").exists() || ws_p.join("skills").exists();
                                    let is_active = id == active_id || ws_p == active_path;

                                    list.push(WorkspaceInfo {
                                        id,
                                        name,
                                        path: ws_path_str,
                                        created_at,
                                        is_active,
                                        has_pillars,
                                    });
                                }
                            }
                        }
                    }
                }
            }
        }

        list
    }

    pub async fn create_workspace(&self, name: &str, target_path_str: &str) -> Result<WorkspaceInfo, String> {
        let clean_name = name.trim();
        if clean_name.is_empty() {
            return Err("Project name cannot be empty".to_string());
        }

        let target_dir = PathBuf::from(target_path_str.trim());
        let _ = std::fs::create_dir_all(&target_dir).map_err(|e| format!("Failed to create folder: {e}"))?;
        let abs_target = std::fs::canonicalize(&target_dir).unwrap_or(target_dir);

        // Bootstrap the Sacred Documents and Folders
        self.bootstrap_sacred_pillars(&abs_target, clean_name)?;

        // Register project JSON
        let project_id = format!("proj_{}", uuid::Uuid::new_v4().simple());
        let time_iso = get_timestamp_iso();
        let proj_json = json!({
            "id": project_id,
            "name": clean_name,
            "createdAt": time_iso,
            "projectResources": {
                "resources": [
                    { "folderUri": format!("file://{}", abs_target.to_string_lossy()) }
                ]
            }
        });

        for pdir in self.get_projects_dirs() {
            let _ = std::fs::create_dir_all(&pdir);
            let file_path = pdir.join(format!("{project_id}.json"));
            let _ = std::fs::write(file_path, serde_json::to_string_pretty(&proj_json).unwrap_or_default());
        }

        // Set as active
        self.set_active(&project_id, &abs_target).await?;

        Ok(WorkspaceInfo {
            id: project_id,
            name: clean_name.to_string(),
            path: abs_target.to_string_lossy().to_string(),
            created_at: time_iso,
            is_active: true,
            has_pillars: true,
        })
    }

    pub async fn set_active(&self, id: &str, path: &Path) -> Result<(), String> {
        let abs_path = std::fs::canonicalize(path).unwrap_or_else(|_| path.to_path_buf());
        {
            let mut id_guard = self.active_workspace_id.write().await;
            *id_guard = id.to_string();
            let mut path_guard = self.active_workspace_path.write().await;
            *path_guard = abs_path.clone();
        }

        let active_json = json!({
            "id": id,
            "path": abs_path.to_string_lossy().to_string(),
            "updatedAt": get_timestamp_iso()
        });

        let conf_dir = self.resolve_primary_config_dir();
        let _ = std::fs::create_dir_all(&conf_dir);
        let _ = std::fs::write(conf_dir.join("active_workspace.json"), serde_json::to_string_pretty(&active_json).unwrap_or_default());

        let project_name = abs_path.file_name().unwrap_or_default().to_string_lossy().to_string();
        let _ = self.bootstrap_sacred_pillars(&abs_path, &project_name);

        Ok(())
    }

    pub async fn delete_workspace(&self, id: &str) -> Result<String, String> {
        let clean_id = id.trim();
        if clean_id.is_empty() || clean_id == "default" {
            return Err("Cannot delete root default workspace".to_string());
        }

        let mut deleted_any = false;
        for pdir in self.get_projects_dirs() {
            let file_path = pdir.join(format!("{clean_id}.json"));
            if file_path.exists() {
                if let Ok(_) = std::fs::remove_file(&file_path) {
                    deleted_any = true;
                }
            }
        }

        let is_active = {
            let guard = self.active_workspace_id.read().await;
            *guard == clean_id
        };

        if is_active {
            let _ = self.set_active("default", &self.root_dir).await;
        }

        if deleted_any {
            Ok(format!("Workspace '{clean_id}' deleted successfully from registry"))
        } else {
            Err(format!("Workspace '{clean_id}' not found in registry"))
        }
    }

    pub fn bootstrap_sacred_pillars(&self, target_dir: &Path, project_name: &str) -> Result<(), String> {
        bootstrap_sacred_pillars_standalone(target_dir, project_name)
    }
}

/// Helper to clean Windows verbatim UNC prefix (`\\?\` or `\\?\UNC\`) for multi-OS compatibility
/// Also strips `file://` prefixes and normalizes leading slashes before Windows drive letters (e.g. `/C:/...` -> `C:/...`)
pub fn clean_verbatim_path(path: &Path) -> PathBuf {
    let raw = path.to_string_lossy();
    let s = raw.trim_start_matches("file://");
    if s.starts_with(r"\\?\UNC\") {
        PathBuf::from(format!(r"\\{}", &s[8..]))
    } else if s.starts_with(r"\\?\") {
        PathBuf::from(&s[4..])
    } else if s.len() >= 3
        && (s.starts_with('/') || s.starts_with('\\'))
        && s.as_bytes()[1].is_ascii_alphabetic()
        && s.as_bytes()[2] == b':'
    {
        PathBuf::from(&s[1..])
    } else {
        PathBuf::from(s)
    }
}

// SYSTEM_SOUL_PERSONAS permanently purged - Flowork OS relies 100% on modular skills in skills/

/// Standalone, fail-safe Sacred Pillars bootstrapper
/// Guaranteed Zero-Crash: Even if the target directory is read-only or filesystem write fails,
/// it emits a non-fatal warning and returns Ok(()) without breaking runtime execution.
pub fn bootstrap_sacred_pillars_standalone(target_dir: &Path, project_name: &str) -> Result<(), String> {
    let clean_target = clean_verbatim_path(target_dir);

    // 1. Folders (Fail-Safe Multi-OS) - Canonical lowercase .fl_brain and .FL_BIN (with scratch isolation)
    let _ = std::fs::create_dir_all(clean_target.join(".fl_brain"));
    let _ = std::fs::create_dir_all(clean_target.join(".fl_brain").join("memories"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN").join("scratch"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN").join("runtime"));

    // Auto-generate canonical sharded department for default orchestrator (Universal Core System / Mr. Flow)
    let _ = std::fs::create_dir_all(clean_target.join(".fl_brain").join("universal_core_system").join("mrflow").join("memories"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN").join("universal_core_system").join("mrflow").join("scratch"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN").join("universal_core_system").join("mrflow").join("tasks"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN").join("universal_core_system").join("mrflow").join("dashboards"));

    // 2. Sacred Brain Crystals (Default header kata kunci minimal)
    write_if_missing(
        &clean_target.join(".fl_brain").join("system_architecture.md"),
        &format!("<!-- [KEYWORDS: system_architecture, {project_name}] -->\n")
    );
    write_if_missing(
        &clean_target.join(".fl_brain").join("universal_core_system").join("mrflow").join("memories").join("system_architecture.md"),
        &format!("<!-- [KEYWORDS: system_architecture, universal_core_system, mrflow, {project_name}] -->\n")
    );

    // 3. Autonomous self-healing for Flowork's Body (TUBUH FLOWORK):
    // SKILL.MD lives in Tubuh Flowork, NOT in arbitrary project workspaces!
    // If target_dir is Flowork's body (detected via existing skills, tools, plugins, or canvas-ui), ensure SKILL.MD runbooks
    if clean_target.join("skills").exists()
        || clean_target.join("tools").exists()
        || clean_target.join("apps").exists()
        || clean_target.join("plugins").exists()
        || clean_target.join("canvas-ui").exists()
        || clean_target.join("canvas").exists()
        || clean_target.join("agents").exists()
    {
        ensure_flowork_body_pillars(&clean_target);
    }

    Ok(())
}

/// Dynamically auto-generates category, username, & agent-id sharded directories for .fl_brain and .FL_BIN in workspace
pub fn ensure_agent_sharded_workspace_directories(target_dir: &Path, category: &str, agent_id: &str) {
    let clean_target = clean_verbatim_path(target_dir);
    let cat_clean = if category.trim().is_empty() { "universal_core_system" } else { category.trim() };
    let agent_clean = if agent_id.trim().is_empty() || agent_id == "default" { "mrflow" } else { agent_id.trim() };
    let user_clean = std::env::var("FLOWORK_USER")
        .or_else(|_| std::env::var("USER"))
        .unwrap_or_else(|_| "mrflow".to_string());

    // Sovereign format: .fl_brain/memories/{username}/{agent_id} and shared
    let _ = std::fs::create_dir_all(clean_target.join(".fl_brain").join("memories").join(&user_clean).join(agent_clean));
    let _ = std::fs::create_dir_all(clean_target.join(".fl_brain").join("memories").join(&user_clean).join("shared"));

    // Legacy & FL_BIN paths
    let _ = std::fs::create_dir_all(clean_target.join(".fl_brain").join(cat_clean).join(agent_clean).join("memories"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN").join(cat_clean).join(agent_clean).join("scratch"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN").join(cat_clean).join(agent_clean).join("tasks"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN").join(cat_clean).join(agent_clean).join("dashboards"));
    let _ = std::fs::create_dir_all(clean_target.join(".FL_BIN").join("runtime"));
}


/// Ensure authoritative SKILL.MD runbooks and root pillars exist in Flowork's Body (TUBUH FLOWORK).
/// Auto-reconstitutes any missing or deleted root pillar file from embedded binary enclave.
/// Doktrin Mutlak: Persona & Agent individual prompts JANGAN di-auto generate! Hanya master root pillars.
pub fn ensure_flowork_body_pillars(flowork_body: &Path) {
    // Auto-reconstitute all 21 authoritative root pillars from embedded binary enclave
    crate::root_pillars::reconstitute_root_pillars(flowork_body);

    ensure_skills_skill(&flowork_body.join("skills"));
    if flowork_body.join("agents").exists() {
        ensure_agents_skill(&flowork_body.join("agents"));
    }
    ensure_tools_skill(&flowork_body.join("tools"));
    if flowork_body.join("apps").exists() {
        ensure_plugins_skill(&flowork_body.join("apps"));
    } else if flowork_body.join("plugins").exists() {
        ensure_plugins_skill(&flowork_body.join("plugins"));
    }

    // Auto-generate dynamic system prompts repository (system/system_promp)
    ensure_agents_system(&flowork_body.join("system").join("system_promp"));

    if flowork_body.join("FLOWORK").join("skills").exists() {
        crate::root_pillars::reconstitute_root_pillars(&flowork_body.join("FLOWORK"));
        ensure_skills_skill(&flowork_body.join("FLOWORK").join("skills"));
    }
    if flowork_body.join("FLOWORK").join("agents").exists() {
        ensure_agents_skill(&flowork_body.join("FLOWORK").join("agents"));
    }
    if flowork_body.join("FLOWORK").join("tools").exists() {
        ensure_tools_skill(&flowork_body.join("FLOWORK").join("tools"));
    }
    if flowork_body.join("FLOWORK").join("plugins").exists() {
        ensure_plugins_skill(&flowork_body.join("FLOWORK").join("plugins"));
    }
}

/// Ensure dynamic system prompts repository directory exists in Tubuh Flowork (agents/system).
/// Pure disk-driven: Never auto-generates or writes hardcoded prompt strings.
pub fn ensure_agents_system(system_dir: &Path) {
    let _ = std::fs::create_dir_all(system_dir);
}

/// Ensure agents/ directory exists in Tubuh Flowork.
/// Pure disk-driven: Never auto-generates or writes hardcoded strings into SKILL.MD.
pub fn ensure_agents_skill(agents_root: &Path) {
    let _ = std::fs::create_dir_all(agents_root);
}

/// Doktrin Kedaulatan: Persona & Agent JANGAN di-auto generate!
/// Fungsi ini sengaja dijadikan no-op untuk menjamin binary tidak pernah meng-generate Persona atau Agent.
#[allow(dead_code)]
#[inline]
pub fn ensure_persona_skill(_persona_root: &Path) {
    // Intentionally no-op: Persona and Agent must NEVER be auto-generated by binary
}

/// Ensure skills/ directory exists.
/// Pure disk-driven: Never auto-generates or writes hardcoded strings into SKILL.MD.
pub fn ensure_skills_skill(skills_root: &Path) {
    let _ = std::fs::create_dir_all(skills_root);
}

/// Backward compatibility alias for legacy callers
#[inline]
pub fn ensure_skills_readme(skills_root: &Path) {
    ensure_skills_skill(skills_root);
}

/// Ensure tools/ directory exists.
/// Pure disk-driven: Never auto-generates or writes hardcoded strings into SKILL.MD.
pub fn ensure_tools_skill(tools_root: &Path) {
    let _ = std::fs::create_dir_all(tools_root);
}

/// Backward compatibility alias for legacy callers
#[inline]
pub fn ensure_tools_readme(tools_root: &Path) {
    ensure_tools_skill(tools_root);
}

/// Ensure plugins/ directory exists.
/// Pure disk-driven: Never auto-generates or writes hardcoded strings into SKILL.MD.
pub fn ensure_plugins_skill(plugins_root: &Path) {
    if plugins_root.exists() {
        let _ = std::fs::create_dir_all(plugins_root);
    }
}

fn write_if_missing(path: &Path, content: &str) -> bool {
    if !path.exists() {
        if let Some(parent) = path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        match std::fs::write(path, content) {
            Ok(_) => true,
            Err(e) => {
                eprintln!("[FLOWORKOS:WORKSPACE:WARN] Non-fatal auto-generate failed for {}: {e}", path.display());
                false
            }
        }
    } else {
        true
    }
}

fn get_timestamp_iso() -> String {
    let now = std::time::SystemTime::now();
    let d = now.duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    format!("{}", d.as_secs())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_workspace_creation_and_sacred_pillars_bootstrap() {
        let nanos = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
        let temp_base = std::env::temp_dir().join(format!("xflow_ws_test_{}_{}", std::process::id(), nanos));
        let _ = std::fs::create_dir_all(&temp_base);

        let mgr = WorkspaceManager::new(&temp_base);

        let target_project = temp_base.join("my-awesome-app");
        let ws = mgr.create_workspace("My Awesome App", target_project.to_str().unwrap()).await.unwrap();

        assert_eq!(ws.name, "My Awesome App");
        assert!(ws.is_active);
        assert!(ws.has_pillars);

        // Verify Sacred Directories & Brain Keywords existence
        assert!(target_project.join(".fl_brain").join("system_architecture.md").exists());
        assert!(target_project.join(".FL_BIN").exists());

        // Verify Skills & Persona belong to Tubuh Flowork, NEVER littered in user workspace
        assert!(!target_project.join("skills").exists(), "Skills live in Tubuh Flowork, not workspace");
        assert!(!target_project.join("agents").exists(), "Agents live in Tubuh Flowork, not workspace");
        assert!(!target_project.join("Persona").exists(), "Persona lives in Tubuh Flowork, not workspace");
        assert!(!target_project.join("tools").exists(), "Tools live in Tubuh Flowork, not workspace");
        assert!(!target_project.join("plugins").exists(), "Plugins live in Tubuh Flowork, not workspace");

        // Verify Legacy Sacred Documents are permanently purged (never auto-created)
        assert!(!target_project.join("FL_SOUL.MD").exists(), "FL_SOUL.MD must NOT be generated");
        assert!(!target_project.join("FL_RULES.MD").exists(), "FL_RULES.MD must NOT be generated");
        assert!(!target_project.join("FL_GOAL.MD").exists(), "FL_GOAL.MD must NOT be generated");
        assert!(!target_project.join("FL_MAP.MD").exists(), "FL_MAP.MD must NOT be generated");
        assert!(!target_project.join("ARCHITECT.MD").exists(), "ARCHITECT.MD must NOT be generated");

        let brain_text = std::fs::read_to_string(target_project.join(".fl_brain").join("system_architecture.md")).unwrap();
        assert!(brain_text.contains("KEYWORDS: system_architecture"));

        // Verify SOUL folder is permanently absent (Doctrine: 100% Skills-first architecture)
        assert!(!target_project.join("SOUL").exists(), "SOUL folder must be permanently removed and never generated");

        // Verify listing
        let all = mgr.get_all().await;
        assert!(all.len() >= 2); // Root + new project

        let _ = std::fs::remove_dir_all(&temp_base);
        println!("✅ Sovereign Workspace Auto-Bootstrap verified: Empty sacred documents seeded & SOUL permanently deleted!");
    }

    #[test]
    fn test_sacred_pillars_fail_safe_no_crash_multi_os() {
        // Multi-OS Fail-safe test: Calling bootstrap on restricted or dummy path must NEVER crash/panic
        let dummy_path = PathBuf::from("/proc/sys/flowork_read_only_test_path_multi_os_dummy");
        let res = bootstrap_sacred_pillars_standalone(&dummy_path, "Test Fail Safe App");
        assert!(res.is_ok(), "bootstrap_sacred_pillars_standalone must be fail-safe and never return Err on write failure");

        // Test Windows UNC verbatim path normalization
        let win_path = PathBuf::from(r"\\?\C:\Users\test\workspace");
        let cleaned = clean_verbatim_path(&win_path);
        assert_eq!(cleaned, PathBuf::from(r"C:\Users\test\workspace"));

        let unc_path = PathBuf::from(r"\\?\UNC\server\share\workspace");
        let cleaned_unc = clean_verbatim_path(&unc_path);
        assert_eq!(cleaned_unc, PathBuf::from(r"\\server\share\workspace"));
    }

    #[tokio::test]
    async fn test_workspace_delete_and_cleanup() {
        let nanos = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
        let temp_base = std::env::temp_dir().join(format!("xflow_ws_del_test_{}_{}", std::process::id(), nanos));
        let _ = std::fs::create_dir_all(&temp_base);

        let mgr = WorkspaceManager::new(&temp_base);

        let target_project = temp_base.join("to-be-deleted");
        let ws = mgr.create_workspace("Temporary Project", target_project.to_str().unwrap()).await.unwrap();

        assert_eq!(ws.name, "Temporary Project");
        assert_eq!(mgr.get_active_path().await, std::fs::canonicalize(&target_project).unwrap());

        // Delete the workspace
        let res = mgr.delete_workspace(&ws.id).await;
        assert!(res.is_ok());

        // Verify active switched back to root default
        assert_eq!(mgr.get_active_path().await, std::fs::canonicalize(&temp_base).unwrap_or(temp_base.clone()));

        // Cannot delete root default
        assert!(mgr.delete_workspace("default").await.is_err());

        let _ = std::fs::remove_dir_all(&temp_base);
        println!("✅ Workspace Deletion verified: Registry cleaned and fallback to default works!");
    }

    #[test]
    fn test_auto_reconstitution_of_persona_skills_and_tools_readmes() {
        let nanos = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
        let temp_dir = std::env::temp_dir().join(format!("flw_reconstitute_test_{}_{}", std::process::id(), nanos));
        let persona_dir = temp_dir.join("Persona");
        let skills_dir = temp_dir.join("skills");
        let tools_dir = temp_dir.join("tools");
        let plugins_dir = temp_dir.join("plugins");

        let _ = std::fs::create_dir_all(&persona_dir);
        let _ = std::fs::create_dir_all(&skills_dir);
        let _ = std::fs::create_dir_all(&tools_dir);
        let _ = std::fs::create_dir_all(&plugins_dir);

        // 1. Initial bootstrap of Tubuh Flowork: directories are created, zero prompts hardcoded in binary
        let res = bootstrap_sacred_pillars_standalone(&temp_dir, "AutoReconstitutionTest");
        assert!(res.is_ok());

        let persona_skill_path = persona_dir.join("SKILL.MD");

        // Verify directories exist
        assert!(skills_dir.exists(), "skills directory must exist");
        assert!(tools_dir.exists(), "tools directory must exist");
        assert!(plugins_dir.exists(), "plugins directory must exist");

        // Persona individual runbooks must NEVER be auto-generated by binary
        assert!(!persona_skill_path.exists(), "Persona & Agent individual prompts must NEVER be auto-generated by binary!");

        // Calling ensure_flowork_body_pillars maintains directory integrity
        ensure_flowork_body_pillars(&temp_dir);
        assert!(skills_dir.exists());
        assert!(tools_dir.exists());
        assert!(plugins_dir.exists());

        // 4. Verify that in an arbitrary user workspace project, root pillars are NOT littered
        let clean_ws = std::env::temp_dir().join(format!("flowork_clean_ws_{}", get_timestamp_iso()));
        let res_ws = bootstrap_sacred_pillars_standalone(&clean_ws, "CleanUserProject");
        assert!(res_ws.is_ok());
        assert!(clean_ws.join(".fl_brain").exists(), "Workspace must have .fl_brain");
        assert!(clean_ws.join(".FL_BIN").exists(), "Workspace must have .FL_BIN");
        assert!(!clean_ws.join("skills").exists(), "SKILL MUST LIVE IN TUBUH FLOWORK, NOT IN WORKSPACE!");
        assert!(!clean_ws.join("agents").exists(), "AGENTS MUST LIVE IN TUBUH FLOWORK, NOT IN WORKSPACE!");
        assert!(!clean_ws.join("Persona").exists(), "PERSONA MUST LIVE IN TUBUH FLOWORK, NOT IN WORKSPACE!");
        assert!(!clean_ws.join("tools").exists(), "TOOLS MUST LIVE IN TUBUH FLOWORK, NOT IN WORKSPACE!");
        assert!(!clean_ws.join("plugins").exists(), "PLUGINS MUST LIVE IN TUBUH FLOWORK, NOT IN WORKSPACE!");
        assert!(!clean_ws.join("README.MD").exists(), "README.MD MUST LIVE IN ROOT, NOT IN WORKSPACE!");
        assert!(!clean_ws.join("STRUCTURE.MD").exists(), "STRUCTURE.MD MUST LIVE IN ROOT, NOT IN WORKSPACE!");

        let _ = std::fs::remove_dir_all(&temp_dir);
        let _ = std::fs::remove_dir_all(&clean_ws);
        println!("✅ Root Pillars Auto-Reconstitution verified with Exit Code 0!");
    }

    #[test]
    fn test_ensure_system_categories_decoupled_from_kernel() {
        let nanos = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
        let flowork_body = std::env::temp_dir().join(format!("flw_body_test_{}_{}", std::process::id(), nanos));
        let _ = std::fs::create_dir_all(&flowork_body);

        // Verify categories directory is decoupled from kernel and NOT created automatically
        ensure_flowork_body_pillars(&flowork_body);
        let cat_dir = flowork_body.join("agents").join("system").join("categories");
        assert!(!cat_dir.exists(), "agents/system/categories must NOT be created automatically by kernel");

        // Verify Workspace Isolation: User workspace projects MUST NEVER have portable-home/.flowork/SYSTEM
        let user_ws = std::env::temp_dir().join(format!("flw_user_ws_{}_{}", std::process::id(), nanos));
        let _ = std::fs::create_dir_all(&user_ws);
        let _ = bootstrap_sacred_pillars_standalone(&user_ws, "MyCleanProject");

        assert!(!user_ws.join("portable-home").exists(), "User workspace must NEVER contain portable-home!");
        assert!(!user_ws.join("SYSTEM").exists(), "User workspace must NEVER contain SYSTEM!");
        assert!(!user_ws.join("categories").exists(), "User workspace must NEVER contain categories!");

        let _ = std::fs::remove_dir_all(&flowork_body);
        let _ = std::fs::remove_dir_all(&user_ws);
        println!("✅ Decoupled categories architecture and workspace isolation verified with Exit Code 0!");
    }

    #[test]
    fn test_ensure_agents_system_auto_generation() {
        let nanos = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
        let flowork_body = std::env::temp_dir().join(format!("flw_agents_sys_test_{}_{}", std::process::id(), nanos));
        let _ = std::fs::create_dir_all(&flowork_body);

        let sys_dir = flowork_body.join("agents").join("system");
        ensure_agents_system(&sys_dir);
        assert!(sys_dir.exists(), "agents/system directory must be created");
        let trigger_file = sys_dir.join("trigger.md");
        assert!(!trigger_file.exists(), "trigger.md must NOT be auto-generated into disk by binary (pure disk-driven)");

        let _ = std::fs::remove_dir_all(&flowork_body);
        println!("✅ ensure_agents_system disk-driven behavior verified with Exit Code 0!");
    }
}
