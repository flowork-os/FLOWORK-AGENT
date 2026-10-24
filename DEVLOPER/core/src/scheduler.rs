use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::{broadcast, oneshot, Mutex, RwLock};
use tokio::time::{sleep, Duration};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduledJob {
    pub id: String,
    pub session_id: String, // Bound strictly to chat session ID
    pub job_type: String, // "timer" | "cron"
    pub prompt: String,
    pub condition: String, // "never", "any", or specific sender/task ID
    pub duration_seconds: Option<u64>,
    pub cron_expression: Option<String>,
    pub max_iterations: Option<usize>,
    pub iteration_count: usize,
    pub is_daemon: bool,
    pub status: String, // "active", "completed", "cancelled"
    pub created_at: String,
    pub last_fired_at: Option<String>,
}

#[derive(Clone)]
pub struct SchedulerManager {
    jobs: Arc<RwLock<HashMap<String, ScheduledJob>>>,
    cancel_handles: Arc<Mutex<HashMap<String, oneshot::Sender<()>>>>,
    event_tx: broadcast::Sender<Value>,
    storage_path: Arc<Option<PathBuf>>,
}

impl SchedulerManager {
    pub fn new() -> Self {
        let cwd = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        Self::new_with_root(&cwd)
    }

    pub fn new_with_root(root: impl AsRef<Path>) -> Self {
        let (event_tx, _) = broadcast::channel(128);
        let storage_file = resolve_storage_path(root.as_ref());
        let loaded_jobs = load_persisted_jobs(&storage_file);
        if !loaded_jobs.is_empty() {
            println!("[Scheduler] 📦 Loaded {} persisted job(s) from {:?}", loaded_jobs.len(), storage_file);
        }

        Self {
            jobs: Arc::new(RwLock::new(loaded_jobs)),
            cancel_handles: Arc::new(Mutex::new(HashMap::new())),
            event_tx,
            storage_path: Arc::new(Some(storage_file)),
        }
    }

    #[allow(dead_code)]
    pub fn subscribe_events(&self) -> broadcast::Receiver<Value> {
        self.event_tx.subscribe()
    }

    #[allow(dead_code)]
    pub fn get_event_sender(&self) -> broadcast::Sender<Value> {
        self.event_tx.clone()
    }

    pub async fn list_jobs(&self) -> Vec<ScheduledJob> {
        let guard = self.jobs.read().await;
        let mut list: Vec<ScheduledJob> = guard.values().cloned().collect();
        list.sort_by(|a, b| b.created_at.cmp(&a.created_at));
        list
    }

    #[allow(dead_code)]
    pub async fn list_jobs_by_session(&self, session_id: &str) -> Vec<ScheduledJob> {
        let guard = self.jobs.read().await;
        let mut list: Vec<ScheduledJob> = guard.values().filter(|j| j.session_id == session_id).cloned().collect();
        list.sort_by(|a, b| b.created_at.cmp(&a.created_at));
        list
    }

    #[allow(dead_code)]
    pub async fn get_job(&self, id: &str) -> Option<ScheduledJob> {
        let guard = self.jobs.read().await;
        guard.get(id).cloned()
    }

    pub async fn cancel_job(&self, id: &str) -> Result<(), String> {
        // Trigger cancel signal to spawned async task
        {
            let mut cancel_guard = self.cancel_handles.lock().await;
            if let Some(tx) = cancel_guard.remove(id) {
                let _ = tx.send(());
            }
        }

        // Update status in jobs map and persist to disk
        let mut guard = self.jobs.write().await;
        if let Some(job) = guard.get_mut(id) {
            job.status = "cancelled".to_string();
            Self::persist_jobs_internal(&self.storage_path, &guard).await;
            Ok(())
        } else {
            Err(format!("Scheduled job '{id}' not found"))
        }
    }

    /// Deletes a scheduled job permanently from memory and disk storage
    pub async fn delete_job(&self, id: &str) -> Result<(), String> {
        // Trigger cancel signal to stop spawned async task if running
        {
            let mut cancel_guard = self.cancel_handles.lock().await;
            if let Some(tx) = cancel_guard.remove(id) {
                let _ = tx.send(());
            }
        }

        // Remove completely from jobs map and update disk
        let mut guard = self.jobs.write().await;
        if guard.remove(id).is_some() {
            Self::persist_jobs_internal(&self.storage_path, &guard).await;
            Ok(())
        } else {
            Err(format!("Scheduled job '{id}' not found"))
        }
    }

    /// Updates an existing scheduled job's prompt and/or recurrence/timing, restarting its worker
    pub async fn update_job(
        &self,
        id: &str,
        prompt: Option<&str>,
        duration_seconds: Option<u64>,
        cron_expression: Option<&str>,
    ) -> Result<ScheduledJob, String> {
        // Cancel existing running worker
        {
            let mut cancel_guard = self.cancel_handles.lock().await;
            if let Some(tx) = cancel_guard.remove(id) {
                let _ = tx.send(());
            }
        }

        let mut guard = self.jobs.write().await;
        if let Some(job) = guard.get_mut(id) {
            if let Some(p) = prompt {
                let clean_p = p.trim();
                if !clean_p.is_empty() {
                    job.prompt = clean_p.to_string();
                }
            }

            if let Some(cron) = cron_expression {
                let clean_cron = cron.trim();
                if !clean_cron.is_empty() {
                    job.job_type = "cron".to_string();
                    job.cron_expression = Some(clean_cron.to_string());
                    job.duration_seconds = None;
                }
            } else if let Some(secs) = duration_seconds {
                if secs > 0 {
                    job.job_type = "timer".to_string();
                    job.duration_seconds = Some(secs);
                    job.cron_expression = None;
                    job.created_at = get_timestamp_iso(); // Reset timer reference
                }
            }

            job.status = "active".to_string();
            let updated_job = job.clone();
            Self::persist_jobs_internal(&self.storage_path, &guard).await;

            drop(guard);
            self.spawn_job_worker(&updated_job).await;

            Ok(updated_job)
        } else {
            Err(format!("Scheduled job '{id}' not found"))
        }
    }

    /// Cascading cleanup: Cancel and purge all active scheduled tasks bound to a deleted chat session
    pub async fn cancel_jobs_by_session(&self, session_id: &str) -> usize {
        let target_ids: Vec<String> = {
            let guard = self.jobs.read().await;
            guard.values()
                .filter(|j| j.session_id == session_id && j.status == "active")
                .map(|j| j.id.clone())
                .collect()
        };

        let count = target_ids.len();
        for id in &target_ids {
            let _ = self.cancel_job(id).await;
        }
        count
    }

    /// Early-terminates one-shot timers bound strictly to a specific chat session if their condition matches an incoming event/sender
    pub async fn notify_session_event(&self, session_id: &str, sender_id: Option<&str>) -> Vec<String> {
        let to_cancel: Vec<String> = {
            let guard = self.jobs.read().await;
            guard.values()
                .filter(|j| {
                    j.session_id == session_id
                        && j.status == "active"
                        && j.job_type == "timer"
                        && (
                            j.condition.eq_ignore_ascii_case("any")
                                || sender_id.map(|s| j.condition.eq_ignore_ascii_case(s)).unwrap_or(false)
                        )
                })
                .map(|j| j.id.clone())
                .collect()
        };

        let mut cancelled_ids = Vec::new();
        for id in to_cancel {
            if self.cancel_job(&id).await.is_ok() {
                cancelled_ids.push(id);
            }
        }
        cancelled_ids
    }

    /// Spawns the async execution worker for a scheduled job (handles timer countdown & cron routines)
    async fn spawn_job_worker(&self, job: &ScheduledJob) {
        if job.status != "active" {
            return;
        }

        let (cancel_tx, mut cancel_rx) = oneshot::channel();
        {
            let mut cancel_guard = self.cancel_handles.lock().await;
            cancel_guard.insert(job.id.clone(), cancel_tx);
        }

        let jobs_arc = Arc::clone(&self.jobs);
        let cancel_handles_arc = Arc::clone(&self.cancel_handles);
        let event_tx_clone = self.event_tx.clone();
        let storage_path_clone = Arc::clone(&self.storage_path);
        let spawned_job_id = job.id.clone();
        let spawned_session_id = job.session_id.clone();
        let prompt_clone = job.prompt.clone();
        let job_type = job.job_type.clone();

        if job_type == "timer" {
            let duration_seconds = job.duration_seconds.unwrap_or(60);
            let created_at_secs = job.created_at.parse::<u64>().unwrap_or_else(|_| get_timestamp_secs());
            let target_secs = created_at_secs + duration_seconds;
            let now_secs = get_timestamp_secs();
            let remaining_secs = if target_secs > now_secs {
                target_secs - now_secs
            } else {
                0
            };

            tokio::spawn(async move {
                tokio::select! {
                    _ = sleep(Duration::from_secs(remaining_secs)) => {
                        let now_fired = get_timestamp_iso();
                        {
                            let mut guard = jobs_arc.write().await;
                            if let Some(j) = guard.get_mut(&spawned_job_id) {
                                j.status = "completed".to_string();
                                j.iteration_count = 1;
                                j.last_fired_at = Some(now_fired.clone());
                            }
                            Self::persist_jobs_internal(&storage_path_clone, &guard).await;
                        }
                        {
                            let mut cancel_guard = cancel_handles_arc.lock().await;
                            cancel_guard.remove(&spawned_job_id);
                        }
                        // Broadcast event to listeners with session_id
                        let payload = json!({
                            "event": "schedule_fired",
                            "job_id": spawned_job_id,
                            "session_id": spawned_session_id,
                            "job_type": "timer",
                            "prompt": prompt_clone,
                            "fired_at": now_fired,
                        });
                        let _ = event_tx_clone.send(payload);
                    }
                    _ = &mut cancel_rx => {
                        // Cancelled early by user/event
                    }
                }
            });
        } else if job_type == "cron" {
            let clean_cron = job.cron_expression.clone().unwrap_or_else(|| "*/5 * * * *".to_string());
            let max_iterations = job.max_iterations;
            let mut iter_count = job.iteration_count;

            tokio::spawn(async move {
                let interval_secs = parse_cron_to_interval_secs(&clean_cron);

                loop {
                    tokio::select! {
                        _ = sleep(Duration::from_secs(interval_secs)) => {
                            iter_count += 1;
                            let now_fired = get_timestamp_iso();
                            let is_finished = if let Some(max_i) = max_iterations {
                                iter_count >= max_i
                            } else {
                                false
                            };

                            {
                                let mut guard = jobs_arc.write().await;
                                if let Some(j) = guard.get_mut(&spawned_job_id) {
                                    j.iteration_count = iter_count;
                                    j.last_fired_at = Some(now_fired.clone());
                                    if is_finished {
                                        j.status = "completed".to_string();
                                    }
                                }
                                Self::persist_jobs_internal(&storage_path_clone, &guard).await;
                            }

                            let payload = json!({
                                "event": "schedule_fired",
                                "job_id": spawned_job_id,
                                "session_id": spawned_session_id,
                                "job_type": "cron",
                                "prompt": prompt_clone,
                                "iteration": iter_count,
                                "fired_at": now_fired,
                                "is_finished": is_finished,
                            });
                            let _ = event_tx_clone.send(payload);

                            if is_finished {
                                let mut cancel_guard = cancel_handles_arc.lock().await;
                                cancel_guard.remove(&spawned_job_id);
                                break;
                            }
                        }
                        _ = &mut cancel_rx => {
                            break;
                        }
                    }
                }
            });
        }
    }

    /// Automatically resumes all persisted active scheduled jobs upon service startup
    pub async fn start_persisted_workers(&self) {
        let active_jobs: Vec<ScheduledJob> = {
            let guard = self.jobs.read().await;
            guard.values().filter(|j| j.status == "active").cloned().collect()
        };

        if !active_jobs.is_empty() {
            println!("[Scheduler] 🔄 Resuming {} active scheduled routine(s)...", active_jobs.len());
            for job in active_jobs {
                self.spawn_job_worker(&job).await;
            }
        }
    }

    pub async fn schedule_timer(
        &self,
        session_id: &str,
        duration_seconds: u64,
        prompt: &str,
        condition: Option<&str>,
    ) -> Result<ScheduledJob, String> {
        if duration_seconds == 0 {
            return Err("DurationSeconds must be greater than 0".to_string());
        }

        let job_id = format!("sched_timer_{:x}", uuid::Uuid::new_v4().simple());
        let condition_str = condition.unwrap_or("never").to_string();
        let now_str = get_timestamp_iso();
        let sid = if session_id.trim().is_empty() { "default".to_string() } else { session_id.trim().to_string() };

        let job = ScheduledJob {
            id: job_id.clone(),
            session_id: sid.clone(),
            job_type: "timer".to_string(),
            prompt: prompt.to_string(),
            condition: condition_str.clone(),
            duration_seconds: Some(duration_seconds),
            cron_expression: None,
            max_iterations: Some(1),
            iteration_count: 0,
            is_daemon: false,
            status: "active".to_string(),
            created_at: now_str,
            last_fired_at: None,
        };

        {
            let mut guard = self.jobs.write().await;
            guard.insert(job_id.clone(), job.clone());
            Self::persist_jobs_internal(&self.storage_path, &guard).await;
        }

        self.spawn_job_worker(&job).await;

        Ok(job)
    }

    pub async fn schedule_cron(
        &self,
        session_id: &str,
        cron_expression: &str,
        prompt: &str,
        max_iterations: Option<usize>,
        is_daemon: bool,
    ) -> Result<ScheduledJob, String> {
        let clean_cron = cron_expression.trim();
        if clean_cron.is_empty() {
            return Err("CronExpression cannot be empty".to_string());
        }

        // Validate cron fields (5 fields: min hour day month day-of-week)
        let parts: Vec<&str> = clean_cron.split_whitespace().collect();
        if parts.len() != 5 {
            return Err("CronExpression must contain exactly 5 space-separated fields (minute hour dom month dow)".to_string());
        }

        let job_id = format!("sched_cron_{:x}", uuid::Uuid::new_v4().simple());
        let now_str = get_timestamp_iso();
        let sid = if session_id.trim().is_empty() { "default".to_string() } else { session_id.trim().to_string() };

        let job = ScheduledJob {
            id: job_id.clone(),
            session_id: sid.clone(),
            job_type: "cron".to_string(),
            prompt: prompt.to_string(),
            condition: "never".to_string(),
            duration_seconds: None,
            cron_expression: Some(clean_cron.to_string()),
            max_iterations,
            iteration_count: 0,
            is_daemon,
            status: "active".to_string(),
            created_at: now_str,
            last_fired_at: None,
        };

        {
            let mut guard = self.jobs.write().await;
            guard.insert(job_id.clone(), job.clone());
            Self::persist_jobs_internal(&self.storage_path, &guard).await;
        }

        self.spawn_job_worker(&job).await;

        Ok(job)
    }

    async fn persist_jobs_internal(storage_path: &Option<PathBuf>, guard: &HashMap<String, ScheduledJob>) {
        if let Some(ref path) = storage_path {
            let mut list: Vec<&ScheduledJob> = guard.values().collect();
            list.sort_by(|a, b| b.created_at.cmp(&a.created_at));
            if let Ok(bytes) = serde_json::to_vec_pretty(&list) {
                let parent = path.parent().unwrap_or_else(|| Path::new("."));
                let _ = tokio::fs::create_dir_all(parent).await;
                let tmp_path = path.with_extension(format!("tmp.{}", rand_val()));
                if tokio::fs::write(&tmp_path, &bytes).await.is_ok() {
                    let _ = tokio::fs::rename(&tmp_path, path).await;
                }
            }
        }
    }
}

fn resolve_storage_path(root: &Path) -> PathBuf {
    let abs_root = std::fs::canonicalize(root).unwrap_or_else(|_| root.to_path_buf());
    let portable_home = if abs_root.join("portable-home").exists() {
        abs_root.join("portable-home")
    } else if let Some(parent) = abs_root.parent() {
        if parent != Path::new("/") && parent != Path::new("/tmp") && parent.join("portable-home").exists() {
            parent.join("portable-home")
        } else {
            abs_root.join("portable-home")
        }
    } else {
        abs_root.join("portable-home")
    };
    let config_dir = portable_home.join(".flowork").join("config");
    let _ = std::fs::create_dir_all(&config_dir);
    config_dir.join("scheduled_jobs.json")
}

fn load_persisted_jobs(path: &Path) -> HashMap<String, ScheduledJob> {
    let mut map = HashMap::new();
    if path.exists() {
        if let Ok(content) = std::fs::read_to_string(path) {
            if let Ok(list) = serde_json::from_str::<Vec<ScheduledJob>>(&content) {
                for job in list {
                    map.insert(job.id.clone(), job);
                }
            }
        }
    }
    map
}

/// Fallback interval parser for standard cron patterns:
/// - "*/N * * * *" -> N minutes
/// - "0 * * * *" -> 60 minutes
/// - "0 0 * * *" -> 24 hours
/// - Defaults to 60 seconds if unspecified
fn parse_cron_to_interval_secs(cron: &str) -> u64 {
    let parts: Vec<&str> = cron.split_whitespace().collect();
    if parts.len() != 5 {
        return 60;
    }

    let min_part = parts[0];
    if min_part.starts_with("*/") {
        if let Ok(n) = min_part[2..].parse::<u64>() {
            return (n.max(1)) * 60;
        }
    } else if min_part == "*" {
        return 60;
    } else if parts[1].starts_with("*/") {
        if let Ok(n) = parts[1][2..].parse::<u64>() {
            return (n.max(1)) * 3600;
        }
    } else if parts[1] == "*" {
        return 3600;
    }

    60
}

fn get_timestamp_secs() -> u64 {
    let now = std::time::SystemTime::now();
    now.duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs()
}

fn get_timestamp_iso() -> String {
    format!("{}", get_timestamp_secs())
}

fn rand_val() -> u32 {
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default();
    (now.as_nanos() % 100_000_000) as u32
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_scheduler() -> SchedulerManager {
        let test_dir = std::env::temp_dir().join(format!("test_sched_{}", rand_val()));
        let _ = std::fs::create_dir_all(&test_dir);
        SchedulerManager::new_with_root(&test_dir)
    }

    #[tokio::test]
    async fn test_scheduler_timer_execution() {
        let mgr = create_test_scheduler();
        let mut rx = mgr.subscribe_events();

        let job = mgr.schedule_timer("sess_test_1", 1, "Wakeup agent and inspect memory", Some("never")).await.unwrap();
        assert_eq!(job.status, "active");
        assert_eq!(job.job_type, "timer");
        assert_eq!(job.session_id, "sess_test_1");

        // Wait for event fired
        let fired = tokio::time::timeout(Duration::from_secs(3), rx.recv()).await;
        assert!(fired.is_ok());
        let event_val = fired.unwrap().unwrap();
        assert_eq!(event_val["event"], "schedule_fired");
        assert_eq!(event_val["job_id"], job.id);
        assert_eq!(event_val["session_id"], "sess_test_1");

        let finished_job = mgr.get_job(&job.id).await.unwrap();
        assert_eq!(finished_job.status, "completed");
        assert_eq!(finished_job.iteration_count, 1);
    }

    #[tokio::test]
    async fn test_scheduler_cancel_timer() {
        let mgr = create_test_scheduler();
        let job = mgr.schedule_timer("sess_test_2", 10, "Pending long reminder", None).await.unwrap();
        assert_eq!(job.status, "active");

        let cancel_res = mgr.cancel_job(&job.id).await;
        assert!(cancel_res.is_ok());

        let cancelled_job = mgr.get_job(&job.id).await.unwrap();
        assert_eq!(cancelled_job.status, "cancelled");
    }

    #[tokio::test]
    async fn test_scheduler_list_jobs() {
        let mgr = create_test_scheduler();
        let _ = mgr.schedule_timer("sess_test_3", 5, "Task A", None).await.unwrap();
        let _ = mgr.schedule_timer("sess_test_3", 10, "Task B", None).await.unwrap();

        let list = mgr.list_jobs().await;
        assert!(list.len() >= 2);
    }

    #[tokio::test]
    async fn test_scheduler_cancel_jobs_by_session() {
        let mgr = create_test_scheduler();
        let _ = mgr.schedule_timer("sess_target_delete", 30, "Target 1", None).await.unwrap();
        let _ = mgr.schedule_timer("sess_target_delete", 45, "Target 2", None).await.unwrap();
        let _ = mgr.schedule_timer("sess_keep_alive", 60, "Keep alive", None).await.unwrap();

        let cancelled_count = mgr.cancel_jobs_by_session("sess_target_delete").await;
        assert_eq!(cancelled_count, 2);

        let remaining_active = mgr.list_jobs().await.into_iter().filter(|j| j.status == "active").collect::<Vec<_>>();
        assert_eq!(remaining_active.len(), 1);
        assert_eq!(remaining_active[0].session_id, "sess_keep_alive");
    }

    #[tokio::test]
    async fn test_scheduler_disk_persistence_and_reload() {
        let test_dir = std::env::temp_dir().join(format!("test_sched_persist_{}", rand_val()));
        let _ = std::fs::create_dir_all(&test_dir);

        let mgr1 = SchedulerManager::new_with_root(&test_dir);
        let job = mgr1.schedule_cron("sess_persistent", "*/15 * * * *", "Routine audit", None, false).await.unwrap();
        assert_eq!(job.status, "active");

        // Simulate application restart: instantiate a new manager pointing to the same root
        let mgr2 = SchedulerManager::new_with_root(&test_dir);
        let loaded = mgr2.get_job(&job.id).await;
        assert!(loaded.is_some(), "Job must persist across application restarts");
        let loaded_job = loaded.unwrap();
        assert_eq!(loaded_job.id, job.id);
        assert_eq!(loaded_job.status, "active");
        assert_eq!(loaded_job.cron_expression.as_deref(), Some("*/15 * * * *"));
    }

    #[tokio::test]
    async fn test_scheduler_conditional_early_termination_by_session() {
        let mgr = create_test_scheduler();

        // 1. Session A: timer with condition "any"
        let job_a_any = mgr.schedule_timer("sess_alpha", 300, "Wait any update", Some("any")).await.unwrap();
        // 2. Session A: timer with condition "subagent_123"
        let job_a_specific = mgr.schedule_timer("sess_alpha", 300, "Wait specific subagent", Some("subagent_123")).await.unwrap();
        // 3. Session B: timer with condition "any" (MUST NOT be cancelled when session A fires!)
        let job_b_any = mgr.schedule_timer("sess_beta", 300, "Session B timer", Some("any")).await.unwrap();

        // Trigger event in Session A from subagent_123: both "any" and "subagent_123" in Session A should cancel
        let cancelled = mgr.notify_session_event("sess_alpha", Some("subagent_123")).await;
        assert_eq!(cancelled.len(), 2);
        assert!(cancelled.contains(&job_a_any.id));
        assert!(cancelled.contains(&job_a_specific.id));

        // Session B timer must remain completely active (Zero leakage across session IDs!)
        let check_b = mgr.get_job(&job_b_any.id).await.unwrap();
        assert_eq!(check_b.status, "active", "Session B timer must NOT be affected by Session A event!");
    }
}

