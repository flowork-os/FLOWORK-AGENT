use std::path::PathBuf;

/// Dynamic Root Anchor & runtime configuration
#[derive(Debug, Clone)]
pub struct AppConfig {
    #[allow(dead_code)]
    pub root_dir: PathBuf,
    pub plugins_dir: PathBuf,
    pub skills_dir: PathBuf,
    pub canvas_dir: PathBuf,
    pub host: String,
    pub port: u16,
}

impl AppConfig {
    pub fn new() -> Self {
        let root = Self::find_project_root();
        let plugins_dir = if root.join("apps").exists() {
            root.join("apps")
        } else {
            root.join("plugins")
        };
        let skills_dir = root.join("skills");
        let canvas_dir = if root.join("canvas-ui").exists() {
            root.join("canvas-ui")
        } else if root.join("canvas").exists() {
            root.join("canvas")
        } else {
            root.join("canvas-ui")
        };

        let _ = std::fs::create_dir_all(&plugins_dir);
        let _ = std::fs::create_dir_all(&skills_dir);
        let _ = std::fs::create_dir_all(&canvas_dir);

        Self {
            root_dir: root,
            plugins_dir,
            skills_dir,
            canvas_dir,
            host: "127.0.0.1".to_string(),
            port: 19890,
        }
    }

    fn find_project_root() -> PathBuf {
        // Priority 1: Current Executable location (Rock-solid Multi-OS dynamic portability)
        if let Ok(exe_path) = std::env::current_exe() {
            if let Ok(canon) = exe_path.canonicalize() {
                if let Some(parent) = canon.parent() {
                    if parent.join("canvas-ui").exists() || parent.join("canvas").exists() || parent.join("apps").exists() || parent.join("plugins").exists() {
                        return parent.to_path_buf();
                    }
                    if let Some(grandparent) = parent.parent() {
                        if grandparent.join("canvas-ui").exists() || grandparent.join("canvas").exists() || grandparent.join("apps").exists() || grandparent.join("plugins").exists() {
                            return grandparent.to_path_buf();
                        }
                    }
                }
            }
        }

        // Priority 2: Current working directory
        if let Ok(cwd) = std::env::current_dir() {
            if cwd.join("canvas-ui").exists() || cwd.join("canvas").exists() || cwd.join("apps").exists() || cwd.join("plugins").exists() {
                return cwd;
            }
            if cwd.join("xflow").join("canvas-ui").exists() || cwd.join("xflow").join("canvas").exists() {
                return cwd.join("xflow");
            }
            if let Some(parent) = cwd.parent() {
                if parent.join("canvas-ui").exists() || parent.join("canvas").exists() || parent.join("apps").exists() || parent.join("plugins").exists() {
                    return parent.to_path_buf();
                }
                if parent.join("xflow").join("canvas-ui").exists() || parent.join("xflow").join("canvas").exists() {
                    return parent.join("xflow");
                }
            }
        }

        std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.to_path_buf()))
            .unwrap_or_else(|| PathBuf::from("."))
    }
}
