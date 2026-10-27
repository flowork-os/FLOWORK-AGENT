use crate::manifest::PluginManifest;
use notify::{RecursiveMode, Watcher};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::{broadcast, RwLock};

#[derive(Debug, Clone, serde::Serialize)]
pub enum CatalogEvent {
    #[allow(dead_code)]
    PluginAttached(Box<PluginManifest>),
    PluginDetached(String),
    PromptDispatched(String),
    PluginCommand { action: String, plugin_id: String },
    SkillsUpdated,
    SystemRestarting { session_id: String, reason: String, resume_prompt: String },
    SystemRestarted { session_id: String },
    AgentActivity { agent_id: String, state: String },
    SwarmWaveState(crate::swarm_dag::SwarmWaveEvent),
}

pub struct PluginDiscovery {
    plugins: Arc<RwLock<HashMap<String, PluginManifest>>>,
    tx: broadcast::Sender<CatalogEvent>,
    plugins_dir: PathBuf,
    skills_dir: PathBuf,
}

impl PluginDiscovery {
    pub fn new(plugins_dir: PathBuf, skills_dir: PathBuf) -> (Self, broadcast::Receiver<CatalogEvent>) {
        let (tx, rx) = broadcast::channel(100);
        (Self { plugins: Arc::new(RwLock::new(HashMap::new())), tx, plugins_dir, skills_dir }, rx)
    }

    pub fn plugins_dir(&self) -> &Path {
        &self.plugins_dir
    }

    pub fn skills_dir(&self) -> &Path {
        &self.skills_dir
    }

    pub fn broadcast_skills_updated(&self) {
        let _ = self.tx.send(CatalogEvent::SkillsUpdated);
    }

    /// Pure disk-driven: ensures plugins/ directory exists without auto-reconstituting files from memory.
    pub fn ensure_plugin_skill(plugins_dir: &Path) {
        let _ = std::fs::create_dir_all(plugins_dir);
    }

    pub async fn scan_all(&self) {
        Self::ensure_plugin_skill(&self.plugins_dir);
        let mut list = HashMap::new();
        Self::scan_folder(&self.plugins_dir, &mut list);
        let mut guard = self.plugins.write().await;
        *guard = list;
    }

    fn scan_folder(folder: &Path, list: &mut HashMap<String, PluginManifest>) {
        if let Ok(entries) = std::fs::read_dir(folder) {
            for entry in entries.flatten() {
                let p = entry.path();
                if p.is_dir() {
                    if let Some(m) = PluginManifest::load_from_dir(&p) { list.insert(m.id.clone(), m); }
                }
            }
        }
    }

    pub async fn get_all(&self) -> Vec<PluginManifest> {
        self.plugins.read().await.values().cloned().collect()
    }

    pub async fn get(&self, id: &str) -> Option<PluginManifest> {
        self.plugins.read().await.get(id).cloned()
    }

    pub fn subscribe(&self) -> broadcast::Receiver<CatalogEvent> {
        self.tx.subscribe()
    }

    pub fn broadcast_prompt(&self, prompt: &str) {
        let _ = self.tx.send(CatalogEvent::PromptDispatched(prompt.to_string()));
    }

    pub fn broadcast_plugin_command(&self, action: &str, plugin_id: &str) {
        let _ = self.tx.send(CatalogEvent::PluginCommand {
            action: action.to_string(),
            plugin_id: plugin_id.to_string(),
        });
    }

    pub fn broadcast_system_restarting(&self, session_id: &str, reason: &str, resume_prompt: &str) {
        let _ = self.tx.send(CatalogEvent::SystemRestarting {
            session_id: session_id.to_string(),
            reason: reason.to_string(),
            resume_prompt: resume_prompt.to_string(),
        });
    }

    pub fn broadcast_system_restarted(&self, session_id: &str) {
        let _ = self.tx.send(CatalogEvent::SystemRestarted {
            session_id: session_id.to_string(),
        });
    }

    pub fn broadcast_agent_activity(&self, agent_id: &str, state: &str) {
        let _ = self.tx.send(CatalogEvent::AgentActivity {
            agent_id: agent_id.to_string(),
            state: state.to_string(),
        });
    }

    pub fn broadcast_swarm_wave(&self, event: crate::swarm_dag::SwarmWaveEvent) {
        let _ = self.tx.send(CatalogEvent::SwarmWaveState(event));
    }

    pub fn start_watcher(self: Arc<Self>) {
        let p_dir = self.plugins_dir.clone();
        let s_dir = self.skills_dir.clone();
        let (notify_tx, notify_rx) = std::sync::mpsc::channel();
        let (trigger_tx, mut trigger_rx) = tokio::sync::mpsc::channel::<()>(32);

        std::thread::spawn(move || {
            let mut watcher = match notify::recommended_watcher(notify_tx) {
                Ok(w) => w,
                Err(e) => {
                    eprintln!("[Discovery] Failed to initialize recommended watcher: {e}");
                    return;
                }
            };

            if let Err(e) = watcher.watch(&p_dir, RecursiveMode::Recursive) {
                eprintln!("[Discovery] Failed to watch {}: {e}", p_dir.display());
            }
            if s_dir.exists() {
                if let Err(e) = watcher.watch(&s_dir, RecursiveMode::Recursive) {
                    eprintln!("[Discovery] Failed to watch {}: {e}", s_dir.display());
                }
            }

            while let Ok(res) = notify_rx.recv() {
                match res {
                    Ok(event) => {
                        let is_noisy = event.paths.iter().any(|path| {
                            let path_str = path.to_string_lossy();
                            path_str.contains(".git")
                                || path_str.contains("node_modules")
                                || path_str.contains("__pycache__")
                                || path_str.contains(".venv")
                                || path_str.contains(".FL_BIN")
                                || path_str.ends_with(".log")
                                || path_str.ends_with(".tmp")
                        });
                        if !is_noisy {
                            let _ = trigger_tx.try_send(());
                        }
                    }
                    Err(e) => {
                        eprintln!("[Discovery] Non-fatal notify event error: {e}");
                    }
                }
            }
        });

        tokio::spawn(async move {
            while trigger_rx.recv().await.is_some() {
                // Debounce 1000ms: wait for any rapid filesystem activity to settle
                tokio::time::sleep(tokio::time::Duration::from_millis(1000)).await;
                while trigger_rx.try_recv().is_ok() {}

                self.scan_all().await;
                let _ = self.tx.send(CatalogEvent::PluginDetached("sync".into()));
                let _ = self.tx.send(CatalogEvent::SkillsUpdated);
            }
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_plugin_skill_markdown_english_and_twenty_keywords() {
        let home_dir = std::env::var("HOME").unwrap_or_default();
        let candidates = [
            std::path::PathBuf::from("flowork/plugins/SKILL.MD"),
            std::path::PathBuf::from("../flowork/plugins/SKILL.MD"),
            std::path::PathBuf::from("../../flowork/plugins/SKILL.MD"),
            std::path::PathBuf::from("../../../flowork/plugins/SKILL.MD"),
            std::path::PathBuf::from("../../../../flowork/plugins/SKILL.MD"),
            std::path::PathBuf::from("plugins/SKILL.MD"),
            std::path::PathBuf::from("../flowork/apps/SKILL.MD"),
            std::path::PathBuf::from("../../flowork/apps/SKILL.MD"),
            std::path::PathBuf::from("../../../flowork/apps/SKILL.MD"),
            std::path::PathBuf::from("../../../../flowork/apps/SKILL.MD"),
            std::path::PathBuf::from("flowork/apps/SKILL.MD"),
            std::path::PathBuf::from("apps/SKILL.MD"),
            std::path::PathBuf::from(&home_dir).join("flowork/apps/SKILL.MD"),
            std::path::PathBuf::from("/home/mrflow/flowork/apps/SKILL.MD"),
        ];
        let content = candidates.iter()
            .find_map(|p| std::fs::read_to_string(p).ok())
            .expect("Must read flowork/plugins/SKILL.MD from disk");
        assert!(!content.is_empty(), "Plugin SKILL.md must not be empty");
        assert!(content.contains("name: sovereign_canvas_plugin_architecture"));
        assert!(content.contains("author: \"floworkos.com\""));
        assert!(content.contains("SOVEREIGN CANVAS PLUGIN ARCHITECTURE"));
        assert!(content.contains("HUMAN-IN-THE-LOOP CO-CREATION"));
        assert!(content.contains("plugin.manifest.json"));
        assert!(content.contains("ZERO-ZOMBIE"));

        // Verify exactly 20 English keywords
        let kw_start = content.find("keywords:").expect("Must contain keywords frontmatter");
        let kw_end = content[kw_start..].find("exclude_keywords:")
            .map(|idx| kw_start + idx)
            .unwrap_or_else(|| {
                content[kw_start..].find("---").map(|idx| kw_start + idx).unwrap_or(content.len())
            });
        let kw_block = &content[kw_start..kw_end];
        let keywords_count = kw_block.lines().filter(|l| l.trim().starts_with('-')).count();
        assert_eq!(keywords_count, 20, "Embedded SKILL.md MUST contain EXACTLY 20 keywords! Found: {keywords_count}");
    }

    #[test]
    fn test_auto_reconstitution_of_plugin_skill_when_deleted() {
        let temp_dir = std::env::temp_dir().join(format!("xflow_plugin_skill_test_{}", std::process::id()));
        let plugins_dir = temp_dir.join("plugins");

        // 1. Initially plugins directory does NOT exist
        assert!(!plugins_dir.exists());

        // 2. Call ensure_plugin_skill - directory is created, but SKILL.MD is NOT auto-written (pure disk-driven)
        PluginDiscovery::ensure_plugin_skill(&plugins_dir);
        assert!(plugins_dir.exists(), "plugins/ directory must be automatically created");
        let skill_file = plugins_dir.join("SKILL.MD");
        assert!(!skill_file.exists(), "plugins/SKILL.MD must NOT be auto-generated from binary (pure disk-driven)");

        // 3. User places SKILL.MD on disk
        let disk_skill = "---\nname: sovereign_canvas_plugin_architecture\ndescription: Master SOP\nkeywords: [a,b,c]\n---\n# Plugin\nplugin.manifest.json\n";
        std::fs::write(&skill_file, disk_skill).expect("Write SKILL.MD");
        assert!(skill_file.exists());

        // 4. User deletes the entire plugins folder
        let _ = std::fs::remove_dir_all(&plugins_dir);
        assert!(!plugins_dir.exists());

        // 5. Calling ensure_plugin_skill creates directory but does NOT auto-reconstitute deleted SKILL.MD
        PluginDiscovery::ensure_plugin_skill(&plugins_dir);
        assert!(plugins_dir.exists());
        assert!(!plugins_dir.join("SKILL.MD").exists(), "plugins/SKILL.MD must NOT be auto-reconstituted by binary");

        let _ = std::fs::remove_dir_all(&temp_dir);
    }
}

pub type AppDiscovery = PluginDiscovery;
