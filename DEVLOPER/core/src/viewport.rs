use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ActiveViewport {
    pub tab: String,
    pub title: String,
    pub kind: String, // "system", "app_store", "plugin"
    pub port: Option<u16>,
    pub updated_at: String,
}

impl Default for ActiveViewport {
    fn default() -> Self {
        Self {
            tab: "home".to_string(),
            title: "Home Workbench".to_string(),
            kind: "system".to_string(),
            port: None,
            updated_at: Self::get_timestamp(),
        }
    }
}

impl ActiveViewport {
    pub fn get_timestamp() -> String {
        let now = std::time::SystemTime::now();
        let d = now.duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
        format!("{}", d.as_secs())
    }
}

pub struct ViewportManager {
    current: Arc<RwLock<ActiveViewport>>,
    root_dir: PathBuf,
}

impl ViewportManager {
    pub fn new(root_dir: impl AsRef<Path>) -> Self {
        let root = root_dir.as_ref().to_path_buf();
        let initial = Self::load_from_disk(&root).unwrap_or_default();
        Self {
            current: Arc::new(RwLock::new(initial)),
            root_dir: root,
        }
    }

    fn load_from_disk(root: &Path) -> Option<ActiveViewport> {
        let candidates = [
            root.join("portable-home").join(".flowork").join("active_viewport.json"),
            root.join(".flowork").join("active_viewport.json"),
        ];
        for path in candidates {
            if let Ok(content) = std::fs::read_to_string(&path) {
                if let Ok(vp) = serde_json::from_str(&content) {
                    return Some(vp);
                }
            }
        }
        None
    }

    pub async fn get_current(&self) -> ActiveViewport {
        self.current.read().await.clone()
    }

    pub fn get_current_sync(&self) -> ActiveViewport {
        if let Ok(guard) = self.current.try_read() {
            guard.clone()
        } else {
            Self::load_from_disk(&self.root_dir).unwrap_or_default()
        }
    }

    pub async fn set_active(&self, tab: String, title: String, kind: String, port: Option<u16>) -> ActiveViewport {
        let new_vp = ActiveViewport {
            tab,
            title,
            kind,
            port,
            updated_at: ActiveViewport::get_timestamp(),
        };

        {
            let mut guard = self.current.write().await;
            *guard = new_vp.clone();
        }

        // Persist to portable-home/.flowork/active_viewport.json for cross-process & IDE awareness
        let target_dir = if self.root_dir.join("portable-home").exists() {
            self.root_dir.join("portable-home").join(".flowork")
        } else if let Ok(p_root) = std::env::var("FLOWORK_PORTABLE_ROOT") {
            let p = PathBuf::from(p_root);
            if p.exists() {
                p.join(".flowork")
            } else {
                self.root_dir.join("portable-home").join(".flowork")
            }
        } else {
            self.root_dir.join("portable-home").join(".flowork")
        };

        let _ = std::fs::create_dir_all(&target_dir);
        let path = target_dir.join("active_viewport.json");
        if let Ok(json_str) = serde_json::to_string_pretty(&new_vp) {
            let _ = std::fs::write(path, json_str);
        }

        new_vp
    }
}
