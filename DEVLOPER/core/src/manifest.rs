use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginEntry {
    pub gui: Option<String>,
    pub backend: Option<String>,
}

impl Default for PluginEntry {
    fn default() -> Self {
        Self {
            gui: Some("gui/index.html".to_string()),
            backend: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginIpc {
    pub port_env: Option<String>,
    pub default_port: Option<u16>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginManifest {
    #[serde(default)]
    pub id: String,
    #[serde(default)]
    pub name: String,
    #[serde(default = "default_version")]
    pub version: String,
    pub author: Option<String>,
    pub description: Option<String>,
    pub category: Option<String>,
    pub icon: Option<String>,
    #[serde(default)]
    pub keywords: Vec<String>,
    #[serde(default)]
    pub exclude_keywords: Vec<String>,
    #[serde(default)]
    pub entry: PluginEntry,
    pub ipc: Option<PluginIpc>,
    #[serde(skip)]
    pub root_dir: PathBuf,
}

fn default_version() -> String {
    "1.0.0".to_string()
}

impl PluginManifest {
    pub fn load_from_dir(dir: &Path) -> Option<Self> {
        let manifest_path = if dir.join("app.manifest.json").exists() {
            dir.join("app.manifest.json")
        } else if dir.join("plugin.manifest.json").exists() {
            dir.join("plugin.manifest.json")
        } else if dir.join("manifest.json").exists() {
            dir.join("manifest.json")
        } else if dir.join("plugin.json").exists() {
            dir.join("plugin.json")
        } else {
            return None;
        };

        let content = std::fs::read_to_string(&manifest_path).ok()?;
        let mut manifest: PluginManifest = serde_json::from_str(&content).ok()?;
        manifest.root_dir = dir.to_path_buf();

        let dir_name = dir.file_name().and_then(|s| s.to_str()).unwrap_or("plugin").to_string();
        if manifest.id.is_empty() {
            manifest.id = dir_name.clone();
        }
        if manifest.name.is_empty() {
            manifest.name = dir_name;
        }

        // Auto-detect GUI if entry.gui is None
        if manifest.entry.gui.is_none() {
            if dir.join("gui/index.html").exists() {
                manifest.entry.gui = Some("gui/index.html".to_string());
            } else if dir.join("index.html").exists() {
                manifest.entry.gui = Some("index.html".to_string());
            }
        }

        Some(manifest)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_manifest_auto_detection_and_defaults() {
        let temp_base = std::env::temp_dir().join(format!("xflow_manifest_test_{}", std::process::id()));
        let p1 = temp_base.join("catur-pro");
        let _ = std::fs::create_dir_all(p1.join("gui"));
        let _ = std::fs::write(p1.join("gui/index.html"), "<h1>Catur</h1>");
        let _ = std::fs::write(
            p1.join("manifest.json"),
            r#"{"name": "Catur Pro", "description": "Master Chess", "keywords": ["chess", "catur"], "exclude_keywords": ["checkers"]}"#,
        );

        let m1 = PluginManifest::load_from_dir(&p1).expect("manifest.json should be auto-detected");
        assert_eq!(m1.id, "catur-pro");
        assert_eq!(m1.name, "Catur Pro");
        assert_eq!(m1.version, "1.0.0");
        assert_eq!(m1.entry.gui, Some("gui/index.html".to_string()));
        assert_eq!(m1.keywords, vec!["chess".to_string(), "catur".to_string()]);
        assert_eq!(m1.exclude_keywords, vec!["checkers".to_string()]);

        let _ = std::fs::remove_dir_all(&temp_base);
    }
}

pub type AppManifest = PluginManifest;
pub type AppEntry = PluginEntry;
pub type AppIpc = PluginIpc;
