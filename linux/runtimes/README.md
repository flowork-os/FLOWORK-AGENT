<!-- [FL_INDEX: portable_runtimes, zero_dependency, plug_and_play, node_embed, python_embed | purpose="Architecture specification and bootstrap documentation for Flowork OS portable runtimes layer"] -->
# ⚡ Flowork OS — Portable Runtimes & Zero-Dependency Enclave

This directory provides isolated, portable runtime environments for Flowork OS to guarantee **100% Plug-and-Play execution across Windows and Linux** without requiring system-wide dependencies.

## 🏛️ Architecture Matrix

| Component | Target Role | Mechanism |
| :--- | :--- | :--- |
| **Glibc Baseline** (Linux) | Core Engine | Built against `glibc 2.17` (Runs on Ubuntu 18.04+, Debian 10+, CentOS, RHEL, Alpine). |
| **Static CRT** (Windows) | Core Engine | Built with `-C target-feature=+crt-static` (Zero VC++ Redistributable or UCRT dependency). |
| **Node.js Runtime** (Windows/Linux) | Tool Engine & MCP Bridge | Isolated standalone Node executable in `runtimes/node/`. |
| **Python 3 Runtime** (Windows/Linux) | Passive Watchers & Scripts | Windows Embeddable Python in `runtimes/python/` (bypasses Windows Store alias trap). |
| **curl & SSL Certificates** | Downloads & APIs | Windows native Schannel / PowerShell + Linux native bundled root certificates. |

## 🚀 Bootstrap Scripts

- **Windows Autonomous Provisioner**: `windows/setup_runtimes.ps1`
- **Linux Autonomous Provisioner**: `linux/setup_runtimes.sh`

Both scripts automatically detect if host runtimes exist; if missing, they pull lightweight, official portable standalone versions into `runtimes/` without requiring administrator privileges or installer wizards.
