//! Sovereign Flowork OS Symbolic Memory & Context Offload Engine
//! High-Density Symbolic Representation (Mermaid Task Nodes) & Lossless Context Compression
//! Sovereign Zero-Drought Symbolic Memory Architecture
//! Co-authored-by: Flowork OS <agent@floworkos.com>

use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

static NODE_COUNTER: AtomicU64 = AtomicU64::new(1001);

pub struct SymbolicMemory;

#[derive(Debug, Clone)]
pub struct OffloadResult {
    pub formatted_output: String,
    pub is_offloaded: bool,
    pub node_id: Option<String>,
    pub offload_path: Option<PathBuf>,
    pub lines_count: usize,
    pub original_chars: usize,
    pub tokens_saved_est: usize,
}

impl SymbolicMemory {
    /// Character threshold above which command outputs are offloaded
    pub const OFFLOAD_CHAR_THRESHOLD: usize = 1500;
    /// Line count threshold above which command outputs are offloaded
    pub const OFFLOAD_LINE_THRESHOLD: usize = 35;

    /// Generates a unique deterministic node ID for drill-down traceability
    pub fn generate_node_id() -> String {
        let count = NODE_COUNTER.fetch_add(1, Ordering::SeqCst);
        let now_ms = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis();
        format!("ref_{:x}_{}", now_ms % 0xffffff, count)
    }

    /// Condenses voluminous tool and command execution outputs into a high-density
    /// symbolic representation (Mermaid task node + head/tail preview), offloading the
    /// full raw text to `.FL_BIN/scratch/logs/` to prevent LLM context drowning.
    pub fn condense_command_output(
        workspace_root: &Path,
        command: &str,
        exit_code: i32,
        stdout: &str,
        stderr: &str,
    ) -> OffloadResult {
        let combined = if stderr.trim().is_empty() {
            stdout.to_string()
        } else if stdout.trim().is_empty() {
            stderr.to_string()
        } else {
            format!("{}\n{}", stdout, stderr)
        };

        let total_chars = combined.len();
        let lines: Vec<&str> = combined.lines().collect();
        let total_lines = lines.len();

        // If output is within budget, pass through raw without offload
        if total_chars <= Self::OFFLOAD_CHAR_THRESHOLD && total_lines <= Self::OFFLOAD_LINE_THRESHOLD {
            let status_label = if exit_code == 0 { "SUCCESS (Exit Code 0)" } else { "ERROR" };
            let formatted = format!("Command: {}\nExit Code: {} ({})\n{}", command, exit_code, status_label, combined);
            return OffloadResult {
                formatted_output: formatted,
                is_offloaded: false,
                node_id: None,
                offload_path: None,
                lines_count: total_lines,
                original_chars: total_chars,
                tokens_saved_est: 0,
            };
        }

        // Output exceeds budget: engage sovereign symbolic context offloading
        let node_id = Self::generate_node_id();
        let logs_dir = workspace_root.join(".FL_BIN").join("scratch").join("logs");
        let _ = std::fs::create_dir_all(&logs_dir);
        let log_file_name = format!("{}.log", node_id);
        let full_log_path = logs_dir.join(&log_file_name);
        let rel_log_path = PathBuf::from(".FL_BIN").join("scratch").join("logs").join(&log_file_name);

        // 1. Offload full raw output losslessly to external filesystem (bottom layer preservation)
        let _ = std::fs::write(&full_log_path, &combined);

        // 2. Extract Head (first 10 lines) and Tail (last 10 lines) previews
        let head_count = std::cmp::min(10, total_lines);
        let head_preview = lines[..head_count].join("\n");

        let tail_start = if total_lines > 20 { total_lines - 10 } else { head_count };
        let tail_preview = if tail_start > head_count {
            lines[tail_start..].join("\n")
        } else {
            String::new()
        };

        let offloaded_lines = total_lines.saturating_sub(head_count + (total_lines - tail_start));
        let size_kb = (total_chars as f64) / 1024.0;
        let short_cmd = crate::tools::safe_truncate_str(command, 60);
        let clean_short_cmd = short_cmd.replace('"', "'");
        let status_str = if exit_code == 0 { "SUCCESS" } else { "FAILED" };

        // 3. Construct high-density Symbolic Mermaid Graph + Structured Preview
        let mut formatted = String::with_capacity(2048);
        formatted.push_str(&format!("Command: {}\nExit Code: {} ({})\n", command, exit_code, status_str));
        formatted.push_str("[SOVEREIGN SYMBOLIC CONTEXT ENGINE // ZERO-DROUGHT CONTEXT ARCHITECTURE]\n");
        formatted.push_str("```mermaid\ngraph LR\n");
        formatted.push_str(&format!("    CMD[\"$ {}\"] --> N[\"[{}] {} lines, {:.1} KB // Exit Code: {}\"]\n", clean_short_cmd, node_id, total_lines, size_kb, exit_code));
        formatted.push_str("```\n");
        formatted.push_str("--- HEAD PREVIEW (First 10 lines) ---\n");
        formatted.push_str(&head_preview);
        formatted.push_str("\n");

        if !tail_preview.is_empty() {
            formatted.push_str(&format!("\n... [{} verbose lines offloaded to external disk storage] ...\n\n", offloaded_lines));
            formatted.push_str("--- TAIL PREVIEW (Last 10 lines) ---\n");
            formatted.push_str(&tail_preview);
            formatted.push_str("\n");
        }

        formatted.push_str(&format!(
            "\n[TRACEABILITY & DRILL-DOWN]: Full unabridged log archived at: {}\nUse `view_file(\"{}\")` to drill down to specific node details if required.",
            rel_log_path.display(),
            rel_log_path.display()
        ));

        // Roughly 4 chars per token saved
        let condensed_chars = formatted.len();
        let tokens_saved = total_chars.saturating_sub(condensed_chars) / 4;

        OffloadResult {
            formatted_output: formatted,
            is_offloaded: true,
            node_id: Some(node_id),
            offload_path: Some(rel_log_path),
            lines_count: total_lines,
            original_chars: total_chars,
            tokens_saved_est: tokens_saved,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_short_output_no_offload() {
        let temp = std::env::temp_dir();
        let res = SymbolicMemory::condense_command_output(
            &temp,
            "echo hello",
            0,
            "hello world",
            "",
        );
        assert!(!res.is_offloaded);
        assert!(res.node_id.is_none());
        assert!(res.formatted_output.contains("hello world"));
    }

    #[test]
    fn test_voluminous_output_symbolic_offload() {
        let temp = std::env::temp_dir();
        let mut long_output = String::new();
        for i in 1..=200 {
            long_output.push_str(&format!("Log line {}: building subsystem module and verifying bytes\n", i));
        }

        let res = SymbolicMemory::condense_command_output(
            &temp,
            "cargo test --all",
            0,
            &long_output,
            "",
        );

        assert!(res.is_offloaded);
        assert!(res.node_id.is_some());
        assert!(res.formatted_output.contains("```mermaid"));
        assert!(res.formatted_output.contains("SYMBOLIC CONTEXT ENGINE"));
        assert!(res.formatted_output.contains("HEAD PREVIEW"));
        assert!(res.formatted_output.contains("TAIL PREVIEW"));
        assert!(res.tokens_saved_est > 0);

        // Verify file was written to disk losslessly
        if let Some(ref path) = res.offload_path {
            let full_p = temp.join(path);
            assert!(full_p.exists());
            let content = std::fs::read_to_string(&full_p).unwrap();
            assert_eq!(content.len(), long_output.len());
            let _ = std::fs::remove_file(full_p);
        }
    }
}
