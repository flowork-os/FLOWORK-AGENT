// [FL_INDEX: keywords="zombie process hunter, passive trigger, linux proc status, defunct processes, background tasks" | COT="Passive sensory trigger rule detecting zombie or defunct child processes in Linux /proc filesystem"]
use std::fs;
use std::process::exit;

fn main() {
    #[cfg(target_os = "linux")]
    {
        if let Ok(entries) = fs::read_dir("/proc") {
            for entry in entries.flatten() {
                let file_name = entry.file_name();
                let s = file_name.to_string_lossy();
                // Check if entry name is purely numeric (PID)
                if !s.is_empty() && s.chars().all(|c| c.is_ascii_digit()) {
                    let status_path = entry.path().join("status");
                    if let Ok(content) = fs::read_to_string(status_path) {
                        for line in content.lines() {
                            if line.starts_with("State:") {
                                if line.contains('Z') || line.to_lowercase().contains("zombie") {
                                    exit(0); // Trigger fires when a zombie process is found!
                                }
                                break;
                            }
                        }
                    }
                }
            }
        }
    }

    #[cfg(target_os = "windows")]
    {
        // On Windows, check for unresponsive/hung processes
        if let Ok(output) = std::process::Command::new("tasklist")
            .args(["/FI", "STATUS eq NOT RESPONDING", "/FO", "CSV", "/NH"])
            .output()
        {
            let text = String::from_utf8_lossy(&output.stdout);
            if text.contains("NOT RESPONDING") {
                exit(0);
            }
        }
    }

    #[cfg(target_os = "macos")]
    {
        // On macOS, check for defunct/zombie processes using ps
        if let Ok(output) = std::process::Command::new("ps")
            .args(["-A", "-o", "state"])
            .output()
        {
            let text = String::from_utf8_lossy(&output.stdout);
            if text.lines().any(|l| l.trim().starts_with('Z')) {
                exit(0);
            }
        }
    }

    exit(1);
}
