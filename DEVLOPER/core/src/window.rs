use std::process::Command;
use std::sync::atomic::{AtomicU32, Ordering};
use tokio::sync::oneshot;

static WINDOW_PID: AtomicU32 = AtomicU32::new(0);

pub struct WindowManager;

impl WindowManager {
    pub fn open_desktop_window(url: &str) -> Option<oneshot::Receiver<()>> {
        let app_flag = format!("--app={url}");
        let profile_dir = if let Ok(fl_home) = std::env::var("FLOWORK_HOME") {
            std::path::PathBuf::from(fl_home).join("browser-profile")
        } else if let Ok(port_home) = std::env::var("PORTABLE_HOME") {
            std::path::PathBuf::from(port_home).join(".flowork").join("browser-profile")
        } else if std::path::Path::new("portable-home/.flowork").exists() {
            std::path::PathBuf::from("portable-home/.flowork/browser-profile")
        } else if let Ok(cwd) = std::env::current_dir() {
            if cwd.join("portable-home/.flowork").exists() {
                cwd.join("portable-home/.flowork/browser-profile")
            } else {
                std::env::temp_dir().join("xflow-canvas-profile")
            }
        } else {
            std::env::temp_dir().join("xflow-canvas-profile")
        };
        let _ = std::fs::create_dir_all(&profile_dir);
        let user_data = format!("--user-data-dir={}", profile_dir.display());

        let flags = [
            app_flag.as_str(),
            "--new-window",
            user_data.as_str(),
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-sync",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-component-update",
            "--password-store=basic",
            "--ignore-gpu-blocklist",
            "--enable-webgl",
            "--enable-accelerated-2d-canvas",
            "--enable-gpu-rasterization",
            "--disable-popup-blocking",
            "--autoplay-policy=no-user-gesture-required",
            "--allow-running-insecure-content",
            "--disable-features=BlockInsecurePrivateNetworkRequests",
            "--class=flowork-os",
            "--app-id=flowork-os",
        ];

        #[cfg(target_os = "linux")]
        let candidates: &[&str] = &[
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "brave-browser",
            "microsoft-edge",
        ];

        #[cfg(target_os = "windows")]
        let mut candidates_vec: Vec<String> = vec![
            "chrome.exe".to_string(),
            "msedge.exe".to_string(),
            "brave.exe".to_string(),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe".to_string(),
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe".to_string(),
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe".to_string(),
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe".to_string(),
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe".to_string(),
        ];

        #[cfg(target_os = "windows")]
        if let Ok(local_app) = std::env::var("LOCALAPPDATA") {
            let p = std::path::PathBuf::from(local_app);
            candidates_vec.push(p.join("Google").join("Chrome").join("Application").join("chrome.exe").to_string_lossy().to_string());
            candidates_vec.push(p.join("Microsoft").join("Edge").join("Application").join("msedge.exe").to_string_lossy().to_string());
            candidates_vec.push(p.join("BraveSoftware").join("Brave-Browser").join("Application").join("brave.exe").to_string_lossy().to_string());
        }

        #[cfg(target_os = "windows")]
        let candidates: Vec<&str> = candidates_vec.iter().map(|s| s.as_str()).collect();

        #[cfg(target_os = "macos")]
        let candidates: &[&str] = &[
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ];

        let (tx, rx) = oneshot::channel();

        for bin in candidates {
            if let Ok(mut child) = Command::new(bin).args(flags).spawn() {
                WINDOW_PID.store(child.id(), Ordering::SeqCst);
                std::thread::spawn(move || {
                    let _ = child.wait();
                    WINDOW_PID.store(0, Ordering::SeqCst);
                    let _ = tx.send(());
                });
                return Some(rx);
            }
        }

        // Platform-specific fallback to default system browser
        #[cfg(target_os = "linux")]
        let fallback = Command::new("xdg-open").arg(url).spawn();
        #[cfg(target_os = "windows")]
        let fallback = Command::new("cmd").args(["/C", "start", "", url]).spawn();
        #[cfg(target_os = "macos")]
        let fallback = Command::new("open").arg(url).spawn();

        if let Ok(mut child) = fallback {
            WINDOW_PID.store(child.id(), Ordering::SeqCst);
            std::thread::spawn(move || {
                let _ = child.wait();
                WINDOW_PID.store(0, Ordering::SeqCst);
                let _ = tx.send(());
            });
            return Some(rx);
        }

        None
    }

    pub fn close_desktop_window() {
        let pid = WINDOW_PID.swap(0, Ordering::SeqCst);
        let my_pid = std::process::id();
        if pid > 100 && pid != my_pid {
            #[cfg(unix)]
            let _ = Command::new("kill").args(["-TERM", &pid.to_string()]).status();
            #[cfg(windows)]
            let _ = Command::new("taskkill").args(["/PID", &pid.to_string(), "/F", "/T"]).status();
        }
    }
}
