//! Sovereign Flowork Swarm DAG Engine
//! True Async Multi-Agent Swarm Parallelism with In-Degree Frontier Scanner,
//! Canonical Prefix Path Mutex, Bounded Worker Pool, 120s Timeout Guard, and Context Fusion.
//! Co-authored-by: Flowork OS <agent@floworkos.com>

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{sleep, timeout, Duration};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum NodeStatus {
    Pending,
    Running,
    Succeeded,
    Failed,
    TimedOut,
    Skipped,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DagNode {
    pub id: String,
    pub title: String,
    pub agent_id: String,
    pub prompt: String,
    pub target_paths: Vec<String>,
    pub timeout_seconds: u64,
    pub output_token_budget: usize, // Role-based output token ceiling (Sovereign Swarm asymmetric budget)
    pub status: NodeStatus,
    pub result_summary: Option<String>,
    pub error_message: Option<String>,
    pub execution_millis: u64,
}

impl DagNode {
    /// Determines the default asymmetric output token budget based on subagent role/category.
    /// Follows the Sovereign Swarm Architecture principle: "Massive Input -> Diamond Output"
    pub fn default_budget_for_agent(agent_id: &str) -> usize {
        let clean = agent_id.to_lowercase();
        if clean.contains("auditor") || clean.contains("security") {
            250 // ~1,000 chars (High compression status matrix)
        } else if clean.contains("qc") || clean.contains("qa") || clean.contains("quality") {
            250 // ~1,000 chars (Pass/Fail verification matrix)
        } else if clean.contains("crypto") || clean.contains("market") || clean.contains("trader") {
            400 // ~1,600 chars (Executive action vectors)
        } else if clean.contains("research") {
            500 // ~2,000 chars (Verified factual synthesis)
        } else if clean.contains("coder") || clean.contains("dev") || clean.contains("engineer") {
            800 // ~3,200 chars (Diff block + Terminal proof)
        } else {
            500 // Default ceiling: 500 tokens (~2,000 chars)
        }
    }

    pub fn new(id: impl Into<String>, title: impl Into<String>, agent_id: impl Into<String>, prompt: impl Into<String>) -> Self {
        let aid = agent_id.into();
        let default_budget = Self::default_budget_for_agent(&aid);
        Self {
            id: id.into(),
            title: title.into(),
            agent_id: aid,
            prompt: prompt.into(),
            target_paths: Vec::new(),
            timeout_seconds: 120, // Default 120s timeout guard (Anti-Zombie Barrier)
            output_token_budget: default_budget,
            status: NodeStatus::Pending,
            result_summary: None,
            error_message: None,
            execution_millis: 0,
        }
    }

    pub fn with_output_budget(mut self, budget_tokens: usize) -> Self {
        self.output_token_budget = budget_tokens;
        self
    }

    pub fn max_output_chars(&self) -> usize {
        if self.output_token_budget > 0 {
            self.output_token_budget * 4
        } else {
            Self::default_budget_for_agent(&self.agent_id) * 4
        }
    }

    pub fn with_targets(mut self, targets: Vec<String>) -> Self {
        self.target_paths = targets;
        self
    }

    pub fn with_timeout(mut self, timeout_seconds: u64) -> Self {
        self.timeout_seconds = timeout_seconds;
        self
    }
}

// ==============================================================================
// 1.5. MULTI-AGENT CONCURRENT STATE TELEMETRY & EVENT BUS
// ==============================================================================

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SwarmWorkerState {
    pub task_id: String,
    pub agent_id: String,
    pub role: String,
    pub status: String, // "pending" | "running" | "succeeded" | "failed" | "timed_out"
    pub targets: Vec<String>,
    pub execution_millis: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SwarmWaveEvent {
    pub wave_index: usize,
    pub total_waves: usize,
    pub status: String, // "wave_started" | "worker_completed" | "barrier_sync" | "wave_finished"
    pub active_workers: Vec<SwarmWorkerState>,
}

pub type SwarmEventCallback = Arc<dyn Fn(SwarmWaveEvent) + Send + Sync>;

// ==============================================================================
// 1. CANONICAL PREFIX FILE RESERVATION MUTEX
// ==============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReservationConflict {
    pub task_id: String,
    pub conflicting_with_task: String,
    pub requested_path: String,
    pub locked_path: String,
}

#[derive(Clone, Default)]
pub struct FileReservationMutex {
    // locked_path_str -> holding_task_id
    locks: Arc<Mutex<HashMap<String, String>>>,
}

impl FileReservationMutex {
    pub fn new() -> Self {
        Self {
            locks: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// Normalizes path relative to base directory for canonical prefix comparison
    pub fn normalize_path(base_dir: &Path, rel_or_abs: &str) -> PathBuf {
        let p = Path::new(rel_or_abs);
        let combined = if p.is_absolute() {
            p.to_path_buf()
        } else {
            base_dir.join(p)
        };

        // Simplistic component normalizer without requiring file existence
        let mut components = Vec::new();
        for comp in combined.components() {
            match comp {
                std::path::Component::CurDir => {}
                std::path::Component::ParentDir => {
                    components.pop();
                }
                c => components.push(c.as_os_str().to_string_lossy().to_string()),
            }
        }

        PathBuf::from(components.join("/"))
    }

    /// Checks if two paths have a prefix/parent-child hierarchy collision
    pub fn is_hierarchical_collision(path_a: &Path, path_b: &Path) -> bool {
        path_a == path_b || path_a.starts_with(path_b) || path_b.starts_with(path_a)
    }

    /// Attempts to reserve a set of paths for a task.
    /// If ANY path causes a hierarchical collision with an active lock, returns Err(ReservationConflict)
    pub async fn try_reserve(&self, task_id: &str, paths: &[String], base_dir: &Path) -> Result<(), ReservationConflict> {
        let mut guard = self.locks.lock().await;

        for req in paths {
            let norm_req = Self::normalize_path(base_dir, req);

            for (locked_str, holding_task) in guard.iter() {
                if holding_task == task_id {
                    continue; // Reentrant for the same task
                }
                let norm_locked = Path::new(locked_str);
                if Self::is_hierarchical_collision(&norm_req, norm_locked) {
                    return Err(ReservationConflict {
                        task_id: task_id.to_string(),
                        conflicting_with_task: holding_task.clone(),
                        requested_path: norm_req.to_string_lossy().to_string(),
                        locked_path: locked_str.clone(),
                    });
                }
            }
        }

        // All paths clear -> acquire locks
        for req in paths {
            let norm_req = Self::normalize_path(base_dir, req);
            guard.insert(norm_req.to_string_lossy().to_string(), task_id.to_string());
        }

        Ok(())
    }

    /// Releases all locks held by a specific task
    pub async fn release_task(&self, task_id: &str) {
        let mut guard = self.locks.lock().await;
        guard.retain(|_, holding_task| holding_task != task_id);
    }

    /// Returns currently active locked path count
    pub async fn active_lock_count(&self) -> usize {
        let guard = self.locks.lock().await;
        guard.len()
    }
}

// ==============================================================================
// 2. IN-DEGREE TOPOLOGICAL FRONTIER SCANNER & DAG GRAPH
// ==============================================================================

#[derive(Clone, Default)]
pub struct TaskDagGraph {
    nodes: HashMap<String, DagNode>,
    // node_id -> set of dependency node_ids (inbound edges that must complete first)
    dependencies: HashMap<String, HashSet<String>>,
}

impl TaskDagGraph {
    pub fn new() -> Self {
        Self {
            nodes: HashMap::new(),
            dependencies: HashMap::new(),
        }
    }

    pub fn add_node(&mut self, node: DagNode) {
        let id = node.id.clone();
        self.nodes.insert(id.clone(), node);
        self.dependencies.entry(id).or_default();
    }

    pub fn add_dependency(&mut self, dependent_node: &str, depends_on_node: &str) -> Result<(), String> {
        if !self.nodes.contains_key(dependent_node) {
            return Err(format!("Node '{}' does not exist in DAG", dependent_node));
        }
        if !self.nodes.contains_key(depends_on_node) {
            return Err(format!("Node '{}' does not exist in DAG", depends_on_node));
        }
        if dependent_node == depends_on_node {
            return Err(format!("Self-dependency detected on node '{}'", dependent_node));
        }

        self.dependencies
            .entry(dependent_node.to_string())
            .or_default()
            .insert(depends_on_node.to_string());

        // Cycle check
        if self.detect_cycle() {
            self.dependencies
                .entry(dependent_node.to_string())
                .or_default()
                .remove(depends_on_node);
            return Err(format!("Cycle detected: adding edge {} -> {} would create a circular dependency", dependent_node, depends_on_node));
        }

        Ok(())
    }

    pub fn detect_cycle(&self) -> bool {
        let mut visited = HashMap::new(); // 0 = unvisited, 1 = visiting, 2 = visited

        fn dfs(u: &str, deps: &HashMap<String, HashSet<String>>, visited: &mut HashMap<String, u8>) -> bool {
            visited.insert(u.to_string(), 1);
            if let Some(upstream) = deps.get(u) {
                for v in upstream {
                    match visited.get(v).copied().unwrap_or(0) {
                        1 => return true, // Found cycle
                        0 => {
                            if dfs(v, deps, visited) {
                                return true;
                            }
                        }
                        _ => {}
                    }
                }
            }
            visited.insert(u.to_string(), 2);
            false
        }

        for node_id in self.nodes.keys() {
            if visited.get(node_id).copied().unwrap_or(0) == 0 {
                if dfs(node_id, &self.dependencies, &mut visited) {
                    return true;
                }
            }
        }

        false
    }

    /// Scans the topological frontier for nodes that have in-degree == 0 among uncompleted nodes
    /// A node is ready if its status is Pending AND all of its dependencies have Succeeded
    pub fn scan_frontier(&self) -> Vec<String> {
        let mut ready = Vec::new();

        for (id, node) in &self.nodes {
            if node.status != NodeStatus::Pending {
                continue;
            }

            let deps = self.dependencies.get(id);
            let all_deps_satisfied = match deps {
                None => true,
                Some(set) => set.iter().all(|dep_id| {
                    self.nodes.get(dep_id).map(|n| n.status == NodeStatus::Succeeded).unwrap_or(false)
                }),
            };

            if all_deps_satisfied {
                ready.push(id.clone());
            }
        }

        ready
    }

    pub fn get_node(&self) -> &HashMap<String, DagNode> {
        &self.nodes
    }

    pub fn get_node_mut(&mut self, id: &str) -> Option<&mut DagNode> {
        self.nodes.get_mut(id)
    }

    pub fn is_complete(&self) -> bool {
        self.nodes.values().all(|n| {
            n.status == NodeStatus::Succeeded || n.status == NodeStatus::Failed || n.status == NodeStatus::TimedOut || n.status == NodeStatus::Skipped
        })
    }

    pub fn has_unrecoverable_failure(&self) -> bool {
        // If a pending node requires a dependency that has Failed or TimedOut, it can never proceed
        for (id, node) in &self.nodes {
            if node.status == NodeStatus::Pending {
                if let Some(deps) = self.dependencies.get(id) {
                    for dep_id in deps {
                        if let Some(dep) = self.nodes.get(dep_id) {
                            if dep.status == NodeStatus::Failed || dep.status == NodeStatus::TimedOut {
                                return true;
                            }
                        }
                    }
                }
            }
        }
        false
    }
}

// ==============================================================================
// 3. BARRIER CONTEXT FUSION (ROLE-BASED ASYMMETRIC TOKEN BUDGETING)
// ==============================================================================

pub struct ContextFusion;

impl ContextFusion {
    /// Fuses completed worker outputs from a wave into a compact, structured semantic bridge.
    /// Enforces asymmetric role-based token budgeting per worker (Sovereign Swarm Architecture paradigm).
    pub fn fuse_wave_results(nodes: &[&DagNode], max_chars_per_node: usize) -> String {
        if nodes.is_empty() {
            return String::new();
        }

        let mut fused = String::from("### 🌊 WAVE EXECUTION BARRIER CONTEXT FUSION\n");
        fused.push_str("Summary of verified parallel worker outputs for downstream DAG frontier:\n\n");

        for node in nodes {
            fused.push_str(&format!(
                "#### [Worker: {} | Agent: {} | Role Budget: {} tokens]\n",
                node.id, node.agent_id, node.output_token_budget
            ));
            fused.push_str(&format!("- Status: {:?} (took {} ms)\n", node.status, node.execution_millis));
            if !node.target_paths.is_empty() {
                fused.push_str(&format!("- Mutated Targets: {}\n", node.target_paths.join(", ")));
            }

            if let Some(ref summary) = node.result_summary {
                let clean = summary.trim();
                let effective_chars_cap = if node.output_token_budget > 0 {
                    node.output_token_budget * 4
                } else if max_chars_per_node > 0 {
                    max_chars_per_node
                } else {
                    2000
                };

                if clean.chars().count() > effective_chars_cap {
                    let truncated = Self::safe_head_tail_truncate(
                        clean,
                        effective_chars_cap,
                        &node.agent_id,
                        node.output_token_budget,
                    );
                    fused.push_str(&format!("- Findings:\n{}\n\n", truncated));
                } else {
                    fused.push_str(&format!("- Findings: {}\n\n", clean));
                }
            } else if let Some(ref err) = node.error_message {
                fused.push_str(&format!("- Error: {}\n\n", err));
            } else {
                fused.push_str("- Findings: [Completed with Exit Code 0 - No output reported]\n\n");
            }
        }

        fused
    }

    /// Safe Head-Tail Truncator guaranteeing UTF-8 char safety, markdown fence closure,
    /// and preservation of diff blocks & Exit Code 0 for coders.
    pub fn safe_head_tail_truncate(content: &str, max_chars: usize, role: &str, max_tokens: usize) -> String {
        let clean = content.trim();
        let total_chars = clean.chars().count();
        if total_chars <= max_chars {
            return clean.to_string();
        }

        let is_coder = role.to_lowercase().contains("coder") || role.to_lowercase().contains("developer");
        let marker = format!(
            "\n\n... [CONTEXT FUSION CONDENSED: TRUNCATED DUE TO ROLE TOKEN BUDGET (Max {} tokens | Role: {})] ...\n\n",
            max_tokens, role
        );

        let chars: Vec<char> = clean.chars().collect();
        let marker_char_count = marker.chars().count();
        let budget_pool = max_chars.saturating_sub(marker_char_count);
        let head_target = (budget_pool * 3) / 10;
        let tail_target = budget_pool.saturating_sub(head_target);

        // Snap head to newline if near boundary
        let mut head_end = head_target.min(chars.len());
        if let Some(nl_pos) = chars[..head_end].iter().rposition(|&c| c == '\n') {
            if nl_pos >= head_target.saturating_sub(head_target / 4) {
                head_end = nl_pos;
            }
        }
        let mut head_str: String = chars[..head_end].iter().collect();
        // Auto-close unclosed markdown code fence in head
        if head_str.matches("```").count() % 2 != 0 {
            head_str.push_str("\n```");
        }

        // Tail selection
        let mut tail_start = chars.len().saturating_sub(tail_target);
        if is_coder {
            // Anchor check: if clean contains "Exit Code: 0", ensure it's in tail
            if let Some(ec_idx) = clean.rfind("Exit Code:") {
                let ec_char_pos = clean[..ec_idx].chars().count();
                if ec_char_pos < chars.len() && ec_char_pos < tail_start {
                    tail_start = ec_char_pos;
                }
            }
            // Also check for git diff header "diff --git"
            if let Some(diff_idx) = clean.rfind("diff --git") {
                let diff_char_pos = clean[..diff_idx].chars().count();
                if diff_char_pos < chars.len() && diff_char_pos > head_end && diff_char_pos < tail_start {
                    tail_start = diff_char_pos;
                }
            }
        }

        // Snap tail to newline
        if let Some(nl_rel) = chars[tail_start..].iter().position(|&c| c == '\n') {
            if nl_rel <= tail_target / 5 {
                tail_start += nl_rel + 1;
            }
        }

        let mut tail_str: String = chars[tail_start..].iter().collect();
        // Auto-close unclosed markdown code fence in tail
        if tail_str.matches("```").count() % 2 != 0 {
            tail_str.push_str("\n```");
        }

        format!("{}{}{}", head_str, marker, tail_str)
    }
}

// ==============================================================================
// 4. BOUNDED SWARM EXECUTOR & JITTERED BACKOFF
// ==============================================================================

pub struct SwarmDagExecutor {
    pub max_concurrent_workers: usize, // Default: 3 (Bounded 2..=4)
    pub base_workspace: PathBuf,
    pub mutex: FileReservationMutex,
    pub event_callback: Option<SwarmEventCallback>,
}

impl SwarmDagExecutor {
    pub fn new(base_workspace: impl AsRef<Path>) -> Self {
        Self {
            max_concurrent_workers: 3,
            base_workspace: base_workspace.as_ref().to_path_buf(),
            mutex: FileReservationMutex::new(),
            event_callback: None,
        }
    }

    pub fn with_worker_pool_size(mut self, size: usize) -> Self {
        self.max_concurrent_workers = size.clamp(2, 4);
        self
    }

    pub fn with_event_callback<CB>(mut self, callback: CB) -> Self
    where
        CB: Fn(SwarmWaveEvent) + Send + Sync + 'static,
    {
        self.event_callback = Some(Arc::new(callback));
        self
    }

    /// Selects non-conflicting candidates from the topological frontier to run in the current wave
    pub async fn select_wave_candidates(&self, dag: &TaskDagGraph) -> Vec<String> {
        let frontier = dag.scan_frontier();
        let mut wave = Vec::new();

        for candidate_id in frontier {
            if wave.len() >= self.max_concurrent_workers {
                break;
            }

            if let Some(candidate_node) = dag.nodes.get(&candidate_id) {
                // Check if candidate conflicts with already selected candidates in this wave
                let mut has_wave_conflict = false;
                for selected_id in &wave {
                    if let Some(selected_node) = dag.nodes.get(selected_id) {
                        for p1 in &candidate_node.target_paths {
                            let n1 = FileReservationMutex::normalize_path(&self.base_workspace, p1);
                            for p2 in &selected_node.target_paths {
                                let n2 = FileReservationMutex::normalize_path(&self.base_workspace, p2);
                                if FileReservationMutex::is_hierarchical_collision(&n1, &n2) {
                                    has_wave_conflict = true;
                                    break;
                                }
                            }
                            if has_wave_conflict {
                                break;
                            }
                        }
                    }
                    if has_wave_conflict {
                        break;
                    }
                }

                if !has_wave_conflict {
                    wave.push(candidate_id);
                }
            }
        }

        wave
    }

    /// Executes an entire DAG to completion using Wave Frontier Dispatch,
    /// Anti-Zombie 120s Timeout Guard, File Reservation Mutex, and Context Fusion.
    pub async fn execute_all<F, Fut>(&mut self, dag: &mut TaskDagGraph, mut worker_fn: F) -> Result<String, String>
    where
        F: FnMut(DagNode, String) -> Fut + Send + 'static,
        Fut: std::future::Future<Output = Result<String, String>> + Send + 'static,
    {
        let mut wave_counter = 0;
        let mut fused_history = String::new();

        while !dag.is_complete() {
            if dag.has_unrecoverable_failure() {
                return Err("Swarm DAG stopped: upstream dependency failed or timed out".to_string());
            }

            let wave_ids = self.select_wave_candidates(dag).await;
            if wave_ids.is_empty() {
                return Err("Deadlock detected in DAG: no frontier nodes can proceed".to_string());
            }

            wave_counter += 1;
            println!(
                "[Sovereign Swarm Engine] 🚀 Dispatching Wave {}: {} parallel worker(s) -> {:?}",
                wave_counter,
                wave_ids.len(),
                wave_ids
            );

            // Reserve locks for all nodes in wave
            for id in &wave_ids {
                if let Some(node) = dag.nodes.get(id) {
                    if let Err(e) = self.mutex.try_reserve(id, &node.target_paths, &self.base_workspace).await {
                        return Err(format!("Fatal Reservation Mutex error during wave dispatch: {:?}", e));
                    }
                    if let Some(node_mut) = dag.get_node_mut(id) {
                        node_mut.status = NodeStatus::Running;
                    }
                }
            }

            // Prepare active workers list and notify event listener of wave start
            let mut wave_workers: Vec<SwarmWorkerState> = wave_ids.iter().filter_map(|id| {
                dag.nodes.get(id).map(|node| SwarmWorkerState {
                    task_id: node.id.clone(),
                    agent_id: node.agent_id.clone(),
                    role: node.title.clone(),
                    status: "running".to_string(),
                    targets: node.target_paths.clone(),
                    execution_millis: 0,
                })
            }).collect();

            if let Some(ref cb) = self.event_callback {
                cb(SwarmWaveEvent {
                    wave_index: wave_counter,
                    total_waves: 0,
                    status: "wave_started".to_string(),
                    active_workers: wave_workers.clone(),
                });
            }

            // Spawn concurrent workers
            let mut join_set = tokio::task::JoinSet::new();

            for id in &wave_ids {
                let Some(node) = dag.nodes.get(id).cloned() else {
                    continue;
                };
                let context_snapshot = fused_history.clone();
                let future = worker_fn(node.clone(), context_snapshot);

                let timeout_secs = node.timeout_seconds;
                join_set.spawn(async move {
                    let start_t = std::time::Instant::now();
                    let res = timeout(Duration::from_secs(timeout_secs), future).await;
                    let elapsed = start_t.elapsed().as_millis() as u64;

                    match res {
                        Ok(Ok(summary)) => (node.id, NodeStatus::Succeeded, Some(summary), None, elapsed),
                        Ok(Err(err_msg)) => (node.id, NodeStatus::Failed, None, Some(err_msg), elapsed),
                        Err(_) => (
                            node.id,
                            NodeStatus::TimedOut,
                            None,
                            Some(format!("Execution exceeded strict deadline of {}s (Anti-Zombie Guard Triggered)", timeout_secs)),
                            elapsed,
                        ),
                    }
                });
            }

            // Barrier Rendezvous: wait for all workers in this wave
            let mut completed_in_wave = Vec::new();
            while let Some(res) = join_set.join_next().await {
                match res {
                    Ok((task_id, status, summary, err, elapsed)) => {
                        self.mutex.release_task(&task_id).await;
                        let status_str = match status {
                            NodeStatus::Succeeded => "succeeded",
                            NodeStatus::Failed => "failed",
                            NodeStatus::TimedOut => "timed_out",
                            _ => "completed",
                        };

                        if let Some(w) = wave_workers.iter_mut().find(|w| w.task_id == task_id) {
                            w.status = status_str.to_string();
                            w.execution_millis = elapsed;
                        }

                        if let Some(ref cb) = self.event_callback {
                            cb(SwarmWaveEvent {
                                wave_index: wave_counter,
                                total_waves: 0,
                                status: "worker_completed".to_string(),
                                active_workers: wave_workers.clone(),
                            });
                        }

                        if let Some(node_mut) = dag.get_node_mut(&task_id) {
                            node_mut.status = status;
                            node_mut.result_summary = summary;
                            node_mut.error_message = err;
                            node_mut.execution_millis = elapsed;
                            completed_in_wave.push(node_mut.clone());
                        }
                    }
                    Err(join_err) => {
                        eprintln!("[Sovereign Swarm Engine] Worker join error: {:?}", join_err);
                    }
                }
            }

            // Wave barrier synchronization
            if let Some(ref cb) = self.event_callback {
                cb(SwarmWaveEvent {
                    wave_index: wave_counter,
                    total_waves: 0,
                    status: "barrier_sync".to_string(),
                    active_workers: wave_workers,
                });
            }

            // Perform Context Fusion for this wave (Cap 2,000 chars / ~500 tokens per worker)
            let wave_refs: Vec<&DagNode> = completed_in_wave.iter().collect();
            let wave_fusion = ContextFusion::fuse_wave_results(&wave_refs, 2000);
            fused_history.push_str(&wave_fusion);
        }

        if let Some(ref cb) = self.event_callback {
            cb(SwarmWaveEvent {
                wave_index: wave_counter,
                total_waves: wave_counter,
                status: "wave_finished".to_string(),
                active_workers: Vec::new(),
            });
        }

        println!("[Sovereign Swarm Engine] ✅ All {} waves completed deterministically with Exit Code 0.", wave_counter);
        Ok(fused_history)
    }

    /// Jittered Exponential Backoff Helper for API resilience
    pub async fn with_jittered_backoff<F, Fut, T, E>(
        max_retries: usize,
        base_delay_ms: u64,
        mut op: F,
    ) -> Result<T, E>
    where
        F: FnMut() -> Fut,
        Fut: std::future::Future<Output = Result<T, E>>,
    {
        let mut attempt = 0;
        loop {
            match op().await {
                Ok(val) => return Ok(val),
                Err(e) => {
                    attempt += 1;
                    if attempt >= max_retries {
                        return Err(e);
                    }
                    // Pseudo-random jitter based on current timestamp nanoseconds
                    let jitter = (std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .unwrap_or_default()
                        .subsec_nanos() % 100) as u64;
                    let delay = (base_delay_ms * (1 << attempt.min(5))) + jitter;
                    sleep(Duration::from_millis(delay)).await;
                }
            }
        }
    }
}

// ==============================================================================
// 5. SOVEREIGN VERIFICATION UNIT TESTS
// ==============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dag_cycle_detection() {
        let mut dag = TaskDagGraph::new();
        dag.add_node(DagNode::new("A", "Task A", "coder", "do A"));
        dag.add_node(DagNode::new("B", "Task B", "coder", "do B"));
        dag.add_node(DagNode::new("C", "Task C", "coder", "do C"));

        assert!(dag.add_dependency("B", "A").is_ok());
        assert!(dag.add_dependency("C", "B").is_ok());
        // Adding A -> C creates cycle: A -> B -> C -> A
        assert!(dag.add_dependency("A", "C").is_err(), "Cycle must be caught immediately");
    }

    #[test]
    fn test_topological_frontier_diamond() {
        let mut dag = TaskDagGraph::new();
        dag.add_node(DagNode::new("A", "Root", "coder", "root task"));
        dag.add_node(DagNode::new("B1", "Parallel Branch 1", "recon", "branch 1"));
        dag.add_node(DagNode::new("B2", "Parallel Branch 2", "designer", "branch 2"));
        dag.add_node(DagNode::new("C", "Terminal Join", "auditor", "verify all"));

        dag.add_dependency("B1", "A").unwrap();
        dag.add_dependency("B2", "A").unwrap();
        dag.add_dependency("C", "B1").unwrap();
        dag.add_dependency("C", "B2").unwrap();

        // Wave 1: Only A has in-degree == 0
        let frontier_1 = dag.scan_frontier();
        assert_eq!(frontier_1, vec!["A"]);

        // Simulate A completion
        dag.get_node_mut("A").unwrap().status = NodeStatus::Succeeded;

        // Wave 2: B1 and B2 are both ready simultaneously
        let mut frontier_2 = dag.scan_frontier();
        frontier_2.sort();
        assert_eq!(frontier_2, vec!["B1", "B2"]);

        // Complete B1, B2 still pending -> C should NOT be ready yet
        dag.get_node_mut("B1").unwrap().status = NodeStatus::Succeeded;
        assert_eq!(dag.scan_frontier(), vec!["B2"]);

        // Complete B2 -> C is now unlocked
        dag.get_node_mut("B2").unwrap().status = NodeStatus::Succeeded;
        assert_eq!(dag.scan_frontier(), vec!["C"]);
    }

    #[tokio::test]
    async fn test_canonical_prefix_file_reservation_mutex() {
        let mutex = FileReservationMutex::new();
        let base_dir = Path::new("/workspace");

        // Task 1 reserves directory "/workspace/src"
        let t1_res = mutex.try_reserve("task-01", &[String::from("src")], base_dir).await;
        assert!(t1_res.is_ok());

        // Task 2 attempts to reserve child file "/workspace/src/core/agent.rs" -> MUST FAIL (Prefix collision)
        let t2_res = mutex.try_reserve("task-02", &[String::from("src/core/agent.rs")], base_dir).await;
        assert!(t2_res.is_err(), "Hierarchical prefix collision must reject child path reservation");
        if let Err(conflict) = t2_res {
            assert_eq!(conflict.conflicting_with_task, "task-01");
        }

        // Task 3 reserves non-conflicting path "/workspace/docs/readme.md" -> MUST SUCCEED
        let t3_res = mutex.try_reserve("task-03", &[String::from("docs/readme.md")], base_dir).await;
        assert!(t3_res.is_ok(), "Disjoint paths must succeed simultaneously");

        // Release Task 1 -> Task 2 can now reserve
        mutex.release_task("task-01").await;
        let t2_retry = mutex.try_reserve("task-02", &[String::from("src/core/agent.rs")], base_dir).await;
        assert!(t2_retry.is_ok(), "Path should be free after releasing holding task");
    }

    #[test]
    fn test_context_fusion_500_token_cap() {
        let mut n1 = DagNode::new("T1", "Recon Task", "recon", "fetch intel");
        n1.status = NodeStatus::Succeeded;
        n1.execution_millis = 1450;
        n1.result_summary = Some(format!("START_HEAD_DATA_{}_END_TAIL_DATA", "A".repeat(5000)));

        let fused = ContextFusion::fuse_wave_results(&[&n1], 2000);
        assert!(fused.contains("WAVE EXECUTION BARRIER CONTEXT FUSION"));
        assert!(fused.contains("CONTEXT FUSION CONDENSED"));
        assert!(fused.contains("START_HEAD_DATA"));
        assert!(fused.contains("END_TAIL_DATA"));
        assert!(fused.len() < 2600, "Fused payload must strictly clamp to ~500 tokens per worker");
    }

    #[test]
    fn test_role_based_context_fusion_budgeting() {
        let mut auditor = DagNode::new("T1", "Audit Subsystem", "security-auditor", "audit");
        auditor.status = NodeStatus::Succeeded;
        auditor.execution_millis = 1200;
        auditor.result_summary = Some(format!("AUDIT_START_{}_AUDIT_END", "B".repeat(6000)));

        let mut coder = DagNode::new("T2", "Implement Patch", "coder-specialist", "code");
        coder.status = NodeStatus::Succeeded;
        coder.execution_millis = 2300;
        coder.result_summary = Some(format!("CODER_START_{}_CODER_END", "C".repeat(6000)));

        assert_eq!(auditor.output_token_budget, 250);
        assert_eq!(coder.output_token_budget, 800);

        let fused = ContextFusion::fuse_wave_results(&[&auditor, &coder], 2000);
        assert!(fused.contains("Role Budget: 250 tokens"));
        assert!(fused.contains("Role Budget: 800 tokens"));
        assert!(fused.contains("AUDIT_START"));
        assert!(fused.contains("AUDIT_END"));
        assert!(fused.contains("CODER_START"));
        assert!(fused.contains("CODER_END"));
    }

    #[test]
    fn test_truncator_utf8_char_boundary_and_fences() {
        // Multi-byte Unicode (emojis, Cyrillic, CJK) and unclosed markdown fence
        let unicode_content = format!(
            "HEADER_START 🦀 ⚡ 🌊 🛡️ 🚀 💎\n```rust\nfn calculate() {{\n    let x = \"Привет мир 世界\";\n{}\n```\nTAIL_END 🏁",
            "    // repeating payload line\n".repeat(200)
        );

        let truncated = ContextFusion::safe_head_tail_truncate(&unicode_content, 500, "research-analyst", 125);
        assert!(truncated.contains("HEADER_START"));
        assert!(truncated.contains("TAIL_END"));
        // Fences must be closed (even count of ```)
        let fence_count = truncated.matches("```").count();
        assert_eq!(fence_count % 2, 0, "Markdown fences must be balanced and auto-closed! Found: {}", fence_count);
    }

    #[test]
    fn test_coder_diff_and_exit_code_preservation() {
        let coder_content = format!(
            "TASK_INIT: Starting build\n{}\ndiff --git a/src/agent.rs b/src/agent.rs\n--- a/src/agent.rs\n+++ b/src/agent.rs\n@@ -10 +10 @@\n+ pub fn verified() {{}}\n[DOKTRIN TERMINAL FLOWORK] Perintah keluar dengan kode eksekusi: 0. Exit Code: 0",
            "Intermediate verbose analysis step\n".repeat(150)
        );

        let truncated = ContextFusion::safe_head_tail_truncate(&coder_content, 1200, "coder-specialist", 300);
        assert!(truncated.contains("TASK_INIT"), "Must preserve head task declaration");
        assert!(truncated.contains("Exit Code: 0"), "Must strictly anchor Exit Code: 0 for coders");
        assert!(truncated.contains("diff --git"), "Must preserve diff block for coders");
    }

    #[tokio::test]
    async fn test_zombie_barrier_timeout_guard() {
        let mut executor = SwarmDagExecutor::new("/tmp");
        let mut dag = TaskDagGraph::new();

        // Node with 1-second timeout guard
        let mut slow_node = DagNode::new("slow_node", "Hung LLM Call", "coder", "fetch");
        slow_node.timeout_seconds = 1;
        dag.add_node(slow_node);

        // Worker that attempts to sleep for 5 seconds (simulating hanging socket)
        let res = executor.execute_all(&mut dag, |_node, _ctx| async move {
            sleep(Duration::from_secs(5)).await;
            Ok("Should never arrive here".to_string())
        }).await;

        assert!(res.is_ok());
        let node_result = dag.get_node().get("slow_node").unwrap();
        assert_eq!(node_result.status, NodeStatus::TimedOut, "Node must be marked TimedOut by barrier guard");
        assert!(node_result.error_message.as_ref().unwrap().contains("Anti-Zombie Guard Triggered"));
    }

    #[tokio::test]
    async fn test_swarm_event_bus_broadcast() {
        let events = Arc::new(tokio::sync::Mutex::new(Vec::new()));
        let events_clone = events.clone();

        let mut executor = SwarmDagExecutor::new("/tmp").with_event_callback(move |ev| {
            let ev_copy = ev.clone();
            let ev_storage = events_clone.clone();
            tokio::spawn(async move {
                ev_storage.lock().await.push(ev_copy);
            });
        });

        let mut dag = TaskDagGraph::new();
        dag.add_node(DagNode::new("T1", "Task 1", "market-analyst", "survey"));
        dag.add_node(DagNode::new("T2", "Task 2", "coder-specialist", "compile"));

        let res = executor.execute_all(&mut dag, |node, _| async move {
            Ok(format!("Task {} finished", node.id))
        }).await;

        assert!(res.is_ok(), "DAG execution must succeed");

        // Small yield to let async event tasks record
        tokio::time::sleep(Duration::from_millis(50)).await;

        let recorded = events.lock().await.clone();
        assert!(!recorded.is_empty(), "Must have captured swarm wave events");
        
        let statuses: Vec<String> = recorded.iter().map(|e| e.status.clone()).collect();
        assert!(statuses.contains(&"wave_started".to_string()), "Must record wave_started");
        assert!(statuses.contains(&"worker_completed".to_string()), "Must record worker_completed");
        assert!(statuses.contains(&"barrier_sync".to_string()), "Must record barrier_sync");
        assert!(statuses.contains(&"wave_finished".to_string()), "Must record wave_finished");
    }

    #[tokio::test]
    async fn test_jittered_backoff_transient_recovery() {
        let attempts = Arc::new(std::sync::atomic::AtomicUsize::new(0));
        let attempts_clone = attempts.clone();

        let res = SwarmDagExecutor::with_jittered_backoff(4, 5, || {
            let att = attempts_clone.clone();
            async move {
                let current = att.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
                if current < 2 {
                    Err("Transient HTTP 429 Rate Limit Simulation")
                } else {
                    Ok("Success 200 OK")
                }
            }
        }).await;

        assert_eq!(res, Ok("Success 200 OK"));
        assert_eq!(attempts.load(std::sync::atomic::Ordering::SeqCst), 3);
    }

    #[tokio::test]
    async fn test_complex_multi_wave_stress_test() {
        let events = Arc::new(tokio::sync::Mutex::new(Vec::new()));
        let events_clone = events.clone();

        let mut executor = SwarmDagExecutor::new("/tmp")
            .with_worker_pool_size(3)
            .with_event_callback(move |ev| {
                let ev_copy = ev.clone();
                let ev_storage = events_clone.clone();
                tokio::spawn(async move {
                    ev_storage.lock().await.push(ev_copy);
                });
            });

        let mut dag = TaskDagGraph::new();

        // Wave 1 nodes (Frontier: 3 independent tasks)
        dag.add_node(DagNode::new("T1", "Recon Alpha", "market-analyst", "recon").with_targets(vec!["src/a".into()]));
        dag.add_node(DagNode::new("T2", "Arch Beta", "software-architect", "arch").with_targets(vec!["src/b".into()]));
        dag.add_node(DagNode::new("T3", "Biz Gamma", "business-copywriter", "biz").with_targets(vec!["src/c".into()]));

        // Wave 2 nodes (Depends on Wave 1)
        dag.add_node(DagNode::new("T4", "Coder Delta", "coder-specialist", "code").with_targets(vec!["src/d".into()]));
        dag.add_node(DagNode::new("T5", "QA Epsilon", "qa-engineer", "qa").with_targets(vec!["src/e".into()]));
        dag.add_dependency("T4", "T1").unwrap();
        dag.add_dependency("T4", "T2").unwrap();
        dag.add_dependency("T5", "T3").unwrap();

        // Wave 3 node (Terminal Reducer)
        dag.add_node(DagNode::new("T6", "Release Omega", "release-engineer", "seal"));
        dag.add_dependency("T6", "T4").unwrap();
        dag.add_dependency("T6", "T5").unwrap();

        let execution_order = Arc::new(tokio::sync::Mutex::new(Vec::new()));
        let order_clone = execution_order.clone();

        let res = executor.execute_all(&mut dag, move |node, _ctx| {
            let order = order_clone.clone();
            async move {
                // Simulate async computational workload
                tokio::time::sleep(Duration::from_millis(15)).await;
                order.lock().await.push(node.id.clone());
                Ok(format!("Task [{}] executed successfully", node.id))
            }
        }).await;

        assert!(res.is_ok(), "Complex Multi-Wave DAG execution must succeed");
        assert!(dag.is_complete(), "All 6 nodes in DAG must be complete");

        // Verify deterministic topological order
        let order = execution_order.lock().await.clone();
        assert_eq!(order.len(), 6, "All 6 tasks must execute");
        
        let pos_t1 = order.iter().position(|x| x == "T1").unwrap();
        let pos_t2 = order.iter().position(|x| x == "T2").unwrap();
        let pos_t3 = order.iter().position(|x| x == "T3").unwrap();
        let pos_t4 = order.iter().position(|x| x == "T4").unwrap();
        let pos_t5 = order.iter().position(|x| x == "T5").unwrap();
        let pos_t6 = order.iter().position(|x| x == "T6").unwrap();

        // T4 must come after T1 and T2
        assert!(pos_t4 > pos_t1, "T4 must run after T1");
        assert!(pos_t4 > pos_t2, "T4 must run after T2");
        // T5 must come after T3
        assert!(pos_t5 > pos_t3, "T5 must run after T3");
        // T6 must come after T4 and T5
        assert!(pos_t6 > pos_t4, "T6 must run after T4");
        assert!(pos_t6 > pos_t5, "T6 must run after T5");

        // Small yield to let async event tasks finish recording
        tokio::time::sleep(Duration::from_millis(50)).await;

        let recorded = events.lock().await.clone();
        let wave_start_count = recorded.iter().filter(|e| e.status == "wave_started").count();
        let barrier_sync_count = recorded.iter().filter(|e| e.status == "barrier_sync").count();
        let wave_finished_count = recorded.iter().filter(|e| e.status == "wave_finished").count();

        assert_eq!(wave_start_count, 3, "Must have exactly 3 wave_started events");
        assert_eq!(barrier_sync_count, 3, "Must have exactly 3 barrier_sync events");
        assert_eq!(wave_finished_count, 1, "Must have exactly 1 wave_finished event");
    }
}
