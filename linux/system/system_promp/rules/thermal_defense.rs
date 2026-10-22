use std::fs;
use std::process::exit;

fn main() {
    // 1. Linux /sys/class/thermal
    #[cfg(target_os = "linux")]
    {
        if let Ok(entries) = fs::read_dir("/sys/class/thermal") {
            for entry in entries.flatten() {
                let path = entry.path().join("temp");
                if path.is_file() {
                    if let Ok(c) = fs::read_to_string(&path) {
                        if let Ok(milli_celsius) = c.trim().parse::<i64>() {
                            // 75°C threshold
                            if milli_celsius >= 75_000 {
                                exit(0);
                            }
                        }
                    }
                }
            }
        }
    }

    // 2. Windows CPU High Load Defense (Overheating threshold ~90% load)
    #[cfg(target_os = "windows")]
    {
        if let Ok(output) = std::process::Command::new("wmic")
            .args(["cpu", "get", "loadpercentage", "/Value"])
            .output()
        {
            let text = String::from_utf8_lossy(&output.stdout);
            for line in text.lines() {
                if let Some(val_str) = line.trim().strip_prefix("LoadPercentage=") {
                    if let Ok(pct) = val_str.trim().parse::<u32>() {
                        if pct >= 90 {
                            exit(0);
                        }
                    }
                }
            }
        }
    }

    // 3. macOS Thermal level
    #[cfg(target_os = "macos")]
    {
        if let Ok(output) = std::process::Command::new("sysctl")
            .args(["-n", "machdep.xcpm.cpu_thermal_level"])
            .output()
        {
            let text = String::from_utf8_lossy(&output.stdout);
            if let Ok(level) = text.trim().parse::<i32>() {
                if level >= 2 {
                    exit(0);
                }
            }
        }
    }

    exit(1);
}
