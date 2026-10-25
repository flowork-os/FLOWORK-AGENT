//! Sovereign Flowork OS Sandbox Engine
//! Kernel-Enforced Boundaries for Autonomous Agent Execution
//! Co-authored-by: Flowork OS <agent@floworkos.com>

pub mod landlock;

pub use landlock::{LandlockSandbox, SandboxConfig, SandboxStatus};
use std::path::Path;

/// Applies pre-execution sandboxing to a Tokio Command before spawning.
/// On Linux, this attaches a `pre_exec` closure that invokes Landlock LSM
/// confinement directly in the child process after fork, before exec.
pub fn apply_sandbox_to_command(
    cmd: &mut tokio::process::Command,
    workspace_root: &Path,
    bypass_if_dev_mode: bool,
) -> bool {
    if bypass_if_dev_mode && crate::attestation::is_dev_mode_authenticated(workspace_root) {
        // Developer mode active: unconstrained execution permitted
        return false;
    }

    #[cfg(target_os = "linux")]
    {
        if !LandlockSandbox::is_supported() {
            return false;
        }

        let config = SandboxConfig::new(workspace_root);
        unsafe {
            cmd.pre_exec(move || {
                match LandlockSandbox::enforce(&config) {
                    Ok(_) => Ok(()),
                    Err(e) => {
                        eprintln!("[FLOWORK_SANDBOX:CRITICAL] Landlock enforcement failed: {}", e);
                        Err(std::io::Error::new(std::io::ErrorKind::PermissionDenied, e))
                    }
                }
            });
        }
        true
    }
    #[cfg(not(target_os = "linux"))]
    {
        let _ = cmd;
        let _ = workspace_root;
        false
    }
}
