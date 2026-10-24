use crate::sync_drive::SyncDriveManager;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{sleep, Duration};

pub struct SyncWatcher {
    manager: Arc<SyncDriveManager>,
    pending_sizes: Mutex<HashMap<PathBuf, (u64, u64)>>,
    failed_cooldown: Mutex<HashMap<PathBuf, (u64, u32)>>, // (cooldown_until_epoch_secs, attempt_count)
}

impl SyncWatcher {
    pub fn new(manager: Arc<SyncDriveManager>) -> Self {
        Self {
            manager,
            pending_sizes: Mutex::new(HashMap::new()),
            failed_cooldown: Mutex::new(HashMap::new()),
        }
    }

    pub fn start_worker(self: Arc<Self>) {
        tokio::spawn(async move {
            println!("[Sync Drive] Cloud Offload Watcher service started.");
            loop {
                sleep(Duration::from_secs(6)).await;
                self.scan_cycle().await;
            }
        });
    }

    fn collect_files_recursive(dir: &Path, list: &mut Vec<PathBuf>) {
        let entries = match std::fs::read_dir(dir) {
            Ok(e) => e,
            Err(_) => return,
        };

        for entry in entries.flatten() {
            let path = entry.path();
            let name = match path.file_name().and_then(|f| f.to_str()) {
                Some(n) => n,
                None => continue,
            };

            // Ignore hidden, git, cache, and build directories
            if name.starts_with('.')
                || name == "node_modules"
                || name == "target"
                || name == ".git"
                || name == ".flowork"
            {
                continue;
            }

            if path.is_dir() {
                Self::collect_files_recursive(&path, list);
            } else if path.is_file() {
                // Safety filter: Ignore shortcuts, hidden files, temporary files
                if name.ends_with(".desktop")
                    || name.ends_with(".url")
                    || name.ends_with(".xflow-stub")
                    || name.ends_with(".tmp")
                    || name.ends_with(".crdownload")
                    || name.ends_with(".part")
                    || name.ends_with('~')
                {
                    continue;
                }
                list.push(path);
            }
        }
    }

    pub async fn scan_cycle(&self) {
        let folders = {
            let lock = self.manager.state.read().await;
            lock.backup_folders.clone()
        };

        if folders.is_empty() {
            return;
        }

        let mut candidate_files = Vec::new();
        for folder_str in folders {
            let folder = Path::new(&folder_str);
            if folder.exists() && folder.is_dir() {
                Self::collect_files_recursive(folder, &mut candidate_files);
            }
        }

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        // Prune deleted files from failed_cooldown
        {
            let mut cooldowns = self.failed_cooldown.lock().await;
            cooldowns.retain(|p, _| p.exists());
        }

        for path in candidate_files {
            // Check failure cooldown backoff to prevent tight retry loops
            {
                let cooldowns = self.failed_cooldown.lock().await;
                if let Some(&(cooldown_until, _)) = cooldowns.get(&path) {
                    if now < cooldown_until {
                        continue;
                    }
                }
            }

            let meta = match std::fs::metadata(&path) {
                Ok(m) => m,
                Err(_) => continue,
            };
            let current_size = meta.len();

            let mut pending = self.pending_sizes.lock().await;
            if let Some((prev_size, first_seen)) = pending.get(&path) {
                if *prev_size == current_size && (now - first_seen) >= 3 {
                    // File size is stable, trigger upload & offload
                    pending.remove(&path);
                    drop(pending);

                    println!("[Sync Drive] Detected stable file for cloud offload: {}", path.display());
                    match self.manager.upload_and_offload(&path).await {
                        Ok(offloaded) => {
                            println!(
                                "[Sync Drive] SUCCESS: Offloaded {} to {} (ID: {}). Shortcut created, physical file deleted from PC.",
                                offloaded.file_name, offloaded.account_email, offloaded.gdrive_file_id
                            );
                            let mut cooldowns = self.failed_cooldown.lock().await;
                            cooldowns.remove(&path);
                        }
                        Err(e) => {
                            let (backoff_secs, attempt) = {
                                let mut cooldowns = self.failed_cooldown.lock().await;
                                let entry = cooldowns.entry(path.clone()).or_insert((0, 0));
                                entry.1 += 1;
                                let backoff = (300 * entry.1 as u64).min(3600); // 5m, 10m, 15m... max 1hr
                                entry.0 = now + backoff;
                                (backoff, entry.1)
                            };
                            eprintln!(
                                "[Sync Drive] Offload failed for {} (attempt {}): {e}. Retrying after {}s cooldown.",
                                path.display(), attempt, backoff_secs
                            );
                        }
                    }
                } else if *prev_size != current_size {
                    pending.insert(path, (current_size, now));
                }
            } else {
                pending.insert(path, (current_size, now));
            }
        }
    }
}
