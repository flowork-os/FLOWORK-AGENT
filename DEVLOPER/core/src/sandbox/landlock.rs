//! Sovereign Flowork OS Landlock LSM Kernel Sandbox
//! Direct Kernel-level Filesystem Isolation for AI Agents & Tool Execution
//! Inspired by NVIDIA OpenShell Kernel-Enforcement Architecture
//! Co-authored-by: Flowork OS <agent@floworkos.com>

use std::path::{Path, PathBuf};

#[derive(Debug, Clone)]
pub struct SandboxConfig {
    pub workspace_root: PathBuf,
    pub allow_temp: bool,
    pub additional_read_write: Vec<PathBuf>,
    pub additional_read_only: Vec<PathBuf>,
}

impl SandboxConfig {
    pub fn new(workspace_root: &Path) -> Self {
        Self {
            workspace_root: workspace_root.to_path_buf(),
            allow_temp: true,
            additional_read_write: Vec::new(),
            additional_read_only: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SandboxStatus {
    Enforced { abi_version: i32 },
    UnsupportedKernel,
    DisabledByDevMode,
    NonLinuxHost,
}

#[cfg(target_os = "linux")]
pub mod sys {
    use std::ffi::CString;
    use std::os::unix::ffi::OsStrExt;
    use std::path::Path;

    pub const SYS_LANDLOCK_CREATE_RULESET: i64 = 444;
    pub const SYS_LANDLOCK_ADD_RULE: i64 = 445;
    pub const SYS_LANDLOCK_RESTRICT_SELF: i64 = 446;

    pub const LANDLOCK_CREATE_RULESET_VERSION: u32 = 1 << 0;
    pub const LANDLOCK_RULE_PATH_BENEATH: u32 = 1;
    pub const PR_SET_NO_NEW_PRIVS: i32 = 38;

    pub const O_PATH: i32 = 0o10000000;
    pub const O_CLOEXEC: i32 = 0o2000000;

    // Landlock ABI v1 Access Flags
    pub const ACCESS_FS_EXECUTE: u64 = 1 << 0;
    pub const ACCESS_FS_WRITE_FILE: u64 = 1 << 1;
    pub const ACCESS_FS_READ_FILE: u64 = 1 << 2;
    pub const ACCESS_FS_READ_DIR: u64 = 1 << 3;
    pub const ACCESS_FS_REMOVE_DIR: u64 = 1 << 4;
    pub const ACCESS_FS_REMOVE_FILE: u64 = 1 << 5;
    pub const ACCESS_FS_MAKE_CHAR: u64 = 1 << 6;
    pub const ACCESS_FS_MAKE_DIR: u64 = 1 << 7;
    pub const ACCESS_FS_MAKE_REG: u64 = 1 << 8;
    pub const ACCESS_FS_MAKE_SOCK: u64 = 1 << 9;
    pub const ACCESS_FS_MAKE_FIFO: u64 = 1 << 10;
    pub const ACCESS_FS_MAKE_BLOCK: u64 = 1 << 11;
    pub const ACCESS_FS_MAKE_SYM: u64 = 1 << 12;

    // Landlock ABI v2 Access Flags
    pub const ACCESS_FS_REFER: u64 = 1 << 13;

    // Landlock ABI v3 Access Flags
    pub const ACCESS_FS_TRUNCATE: u64 = 1 << 14;

    #[repr(C)]
    pub struct LandlockRulesetAttr {
        pub handled_access_fs: u64,
    }

    #[repr(C)]
    pub struct LandlockPathBeneathAttr {
        pub allowed_access: u64,
        pub parent_fd: i32,
    }

    extern "C" {
        pub fn syscall(number: i64, ...) -> i64;
        pub fn prctl(option: i32, arg2: u64, arg3: u64, arg4: u64, arg5: u64) -> i32;
        pub fn open(path: *const libc::c_char, flags: i32, ...) -> i32;
        pub fn close(fd: i32) -> i32;
    }

    pub fn query_abi_version() -> i32 {
        unsafe {
            let res = syscall(
                SYS_LANDLOCK_CREATE_RULESET,
                std::ptr::null::<LandlockRulesetAttr>(),
                0,
                LANDLOCK_CREATE_RULESET_VERSION,
            );
            res as i32
        }
    }

    pub fn get_handled_mask(abi_version: i32) -> (u64, u64) {
        let mut full_rw = ACCESS_FS_EXECUTE
            | ACCESS_FS_WRITE_FILE
            | ACCESS_FS_READ_FILE
            | ACCESS_FS_READ_DIR
            | ACCESS_FS_REMOVE_DIR
            | ACCESS_FS_REMOVE_FILE
            | ACCESS_FS_MAKE_CHAR
            | ACCESS_FS_MAKE_DIR
            | ACCESS_FS_MAKE_REG
            | ACCESS_FS_MAKE_SOCK
            | ACCESS_FS_MAKE_FIFO
            | ACCESS_FS_MAKE_BLOCK
            | ACCESS_FS_MAKE_SYM;

        if abi_version >= 2 {
            full_rw |= ACCESS_FS_REFER;
        }
        if abi_version >= 3 {
            full_rw |= ACCESS_FS_TRUNCATE;
        }

        let ro = ACCESS_FS_EXECUTE | ACCESS_FS_READ_FILE | ACCESS_FS_READ_DIR;
        (full_rw, ro)
    }

    pub fn add_path_rule(ruleset_fd: i32, path: &Path, access_mask: u64) -> bool {
        if !path.exists() {
            return false;
        }
        let c_str = match CString::new(path.as_os_str().as_bytes()) {
            Ok(c) => c,
            Err(_) => return false,
        };

        unsafe {
            let fd = open(c_str.as_ptr(), O_PATH | O_CLOEXEC);
            if fd < 0 {
                return false;
            }
            let attr = LandlockPathBeneathAttr {
                allowed_access: access_mask,
                parent_fd: fd,
            };
            let ret = syscall(SYS_LANDLOCK_ADD_RULE, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, &attr, 0);
            close(fd);
            ret == 0
        }
    }
}

pub struct LandlockSandbox;

impl LandlockSandbox {
    /// Detects if Landlock LSM is supported by the host Linux kernel
    pub fn is_supported() -> bool {
        #[cfg(target_os = "linux")]
        {
            sys::query_abi_version() > 0
        }
        #[cfg(not(target_os = "linux"))]
        {
            false
        }
    }

    /// Gets active Landlock ABI version
    pub fn abi_version() -> i32 {
        #[cfg(target_os = "linux")]
        {
            sys::query_abi_version()
        }
        #[cfg(not(target_os = "linux"))]
        {
            -1
        }
    }

    /// Enforces Landlock sandbox confinement onto current process.
    /// This is strictly unprivileged (no root required) and irreversible.
    /// All subsequent file accesses outside allowed directories will return EACCES.
    pub fn enforce(config: &SandboxConfig) -> Result<SandboxStatus, String> {
        #[cfg(target_os = "linux")]
        {
            let abi = sys::query_abi_version();
            if abi <= 0 {
                return Ok(SandboxStatus::UnsupportedKernel);
            }

            let (full_rw, ro) = sys::get_handled_mask(abi);
            let attr = sys::LandlockRulesetAttr {
                handled_access_fs: full_rw,
            };

            unsafe {
                let ruleset_fd = sys::syscall(
                    sys::SYS_LANDLOCK_CREATE_RULESET,
                    &attr,
                    std::mem::size_of::<sys::LandlockRulesetAttr>(),
                    0,
                ) as i32;

                if ruleset_fd < 0 {
                    return Err(format!("Failed to create Landlock ruleset (fd={ruleset_fd})"));
                }

                // 1. Allow Workspace Root (Read-Write-Execute)
                sys::add_path_rule(ruleset_fd, &config.workspace_root, full_rw);

                // 2. Allow Temp directories if enabled
                if config.allow_temp {
                    for tmp in &["/tmp", "/var/tmp"] {
                        sys::add_path_rule(ruleset_fd, Path::new(tmp), full_rw);
                    }
                }

                // 3. Allow Additional Read-Write paths (e.g. scratch directories)
                for p in &config.additional_read_write {
                    sys::add_path_rule(ruleset_fd, p, full_rw);
                }

                // 4. Allow Standard Operating System Binaries and Dynamic Libraries (Read-Only + Execute)
                let ro_system_paths = [
                    "/usr",
                    "/lib",
                    "/lib64",
                    "/bin",
                    "/sbin",
                    "/etc/resolv.conf",
                    "/etc/hosts",
                    "/etc/ssl",
                    "/etc/pki",
                    "/etc/ca-certificates",
                    "/etc/alternatives",
                    "/dev/null",
                    "/dev/urandom",
                    "/dev/zero",
                    "/dev/ptmx",
                    "/dev/pts",
                    "/proc",
                ];
                for ro_path in &ro_system_paths {
                    sys::add_path_rule(ruleset_fd, Path::new(ro_path), ro);
                }

                // 5. Allow Additional Read-Only paths
                for p in &config.additional_read_only {
                    sys::add_path_rule(ruleset_fd, p, ro);
                }

                // 6. Set PR_SET_NO_NEW_PRIVS (mandatory before Landlock restrict)
                if sys::prctl(sys::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 {
                    sys::close(ruleset_fd);
                    return Err("Failed to set PR_SET_NO_NEW_PRIVS on child process".to_string());
                }

                // 7. Restrict process to ruleset
                let ret = sys::syscall(sys::SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0);
                sys::close(ruleset_fd);

                if ret != 0 {
                    return Err(format!("Failed to apply SYS_LANDLOCK_RESTRICT_SELF (ret={ret})"));
                }

                Ok(SandboxStatus::Enforced { abi_version: abi })
            }
        }
        #[cfg(not(target_os = "linux"))]
        {
            let _ = config;
            Ok(SandboxStatus::NonLinuxHost)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_landlock_detection_and_abi() {
        if LandlockSandbox::is_supported() {
            let abi = LandlockSandbox::abi_version();
            assert!(abi >= 1, "Landlock ABI version must be at least 1");
            println!("Test verified Landlock ABI: {}", abi);
        } else {
            println!("Landlock not supported on this host, gracefully handled.");
        }
    }
}
