<div align="center">

# ⚡ Flowork OS — Sovereign AI Agent & Canvas Host

**Autonomous Multi-OS Desktop Environment, Sovereign AI Agent Switchboard & Canvas Host**

[![Platform](https://img.shields.io/badge/Platform-Linux%20x86__64%20%7C%20Windows%2010%2F11-00F5FF?style=for-the-badge)](https://floworkos.com)
[![Architecture](https://img.shields.io/badge/Architecture-Sovereign%20Multi--OS-FF6F00?style=for-the-badge)](https://floworkos.com)
[![Installer](https://img.shields.io/badge/Installer-Eternal%20Net--Bootstrapper-00D26A?style=for-the-badge)](https://floworkos.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](https://github.com/flowork-os/FLOWORK-AGENT/pulls)

<br />

<a href="#-official-eternal-installers">
  <img src="https://img.shields.io/badge/%E2%9A%A1%20DOWNLOAD%20OFFICIAL%20INSTALLERS-CHOOSE%20YOUR%20OS%20%E2%86%92-FF0055?style=for-the-badge&logo=rocket&logoColor=white&labelColor=0D1117" alt="Download Installers" height="54" />
</a>

<br /><br />

<p align="center">
  <a href="#-official-eternal-installers">Installers</a> •
  <a href="#-quick-start--terminal">Quick Start</a> •
  <a href="#-repository-structure">Structure</a> •
  <a href="#-key-capabilities">Capabilities</a> •
  <a href="#-extensions--ecosystem">Ecosystem</a>
</p>

---

</div>

## 📦 Official Eternal Installers

Our official installers are engineered as **Eternal Net-Bootstrappers**:
- 🌐 **Zero Stale Bundles**: The installer binaries do not bundle heavy static payloads.
- ⚡ **Always Fresh**: Whenever executed, they automatically stream and unpack the latest verified release directly from the `main` branch.
- 🔒 **One-Click Autonomous Setup**: Creates desktop shortcuts and configures environment permissions automatically.

### 📥 Download Installer for Your OS:

| Platform | Installer File | How to Install | Direct Download |
| :--- | :--- | :--- | :---: |
| 🪟 **Windows** | **`Flowork-Agent-Installer.exe`** | Double-click the `.exe` file to download latest release & launch | [**Download .exe**](https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/windows/Flowork-Agent-Installer.exe) |
| 🐧 **Linux** | **`Flowork-Agent-Installer.desktop`** | Double-click the `.desktop` file on Desktop or File Manager | [**Download .desktop**](https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/linux/Flowork-Agent-Installer.desktop) |

---

## 🚀 Quick Start (Terminal Alternative)

### 🐧 Linux (x86_64, AArch64)

#### 1. One-Liner Terminal Installer
```bash
curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/linux/install.sh | bash
```

#### 2. Manual Launch
```bash
cd linux
chmod +x flowork.sh x-flow
./flowork.sh
```

---

### 🪟 Windows (10, 11, Server)

#### 1. Standalone Batch Launcher
Download the repository, open `windows/`, and double-click **`flowork.bat`**.

#### 2. PowerShell Command Line
```powershell
cd windows
.\flowork.bat
```

---

## 🏛️ Repository Structure

This repository is strictly partitioned into dedicated, clean multi-OS trees:

```
FLOWORK-AGENT/
├── Flowork-Agent-Installer.desktop # 🐧 Universal 1-Click Linux Desktop Installer
├── linux/                          # 🐧 Pure Linux Agent Distribution
│   ├── Flowork-Agent-Installer.desktop
│   ├── x-flow                      # Native Linux compiled core engine
│   ├── flowork.sh                  # Interactive shell launcher & auto-updater
│   ├── run.sh                      # Direct runner
│   ├── install.sh                  # Autonomous Linux system installer
│   ├── X-Flow.desktop              # Desktop application entry
│   ├── flowork/                    # Daemon binary runner & mock runtime
│   ├── hooks/                      # Shell hooks (.sh, .cjs)
│   ├── canvas-ui/                  # Member area & interactive webview
│   ├── connection/                 # Gateway & model resolver bridge
│   ├── mcp/                        # Model Context Protocol runtime
│   ├── plugins/                    # Local plugin mount point
│   ├── skills/                     # Local skill mount point
│   └── tools/                      # Local micro-tool mount point
│
├── windows/                        # 🪟 Pure Windows Agent Distribution
│   ├── Flowork-Agent-Installer.exe # 🪟 Standalone Windows Net-Installer
│   ├── x-flow.exe                  # Native Windows compiled core engine
│   ├── flowork.bat                 # Interactive batch launcher & auto-updater
│   ├── run.bat                     # Batch runner
│   ├── run.ps1                     # PowerShell runner
│   ├── flowork/                    # Daemon binary runner & mock runtime
│   ├── hooks/                      # Windows hooks (.bat, .ps1, .cjs)
│   ├── canvas-ui/                  # Member area & interactive webview
│   ├── connection/                 # Gateway & model resolver bridge
│   ├── mcp/                        # Model Context Protocol runtime
│   ├── plugins/                    # Local plugin mount point
│   ├── skills/                     # Local skill mount point
│   └── tools/                      # Local micro-tool mount point
│
├── .gitignore
└── README.md
```

---

## 🌟 Key Capabilities

- 🎨 **Sovereign Canvas Host**: Dual-process interactive webview host running locally on isolated loopback ports (`127.0.0.1:9099`).
- ⚡ **Zero-Prompt Bloat**: 8 anchor core tools with Just-In-Time (JIT) dynamic mounting for ephemeral extensions.
- 🧠 **Sovereign Brain (`.fl_brain`)**: Long-term memory storage preserving verified operational solutions across runs.
- 🛡️ **Zero-Zombie Process Supervision**: Deterministic termination signals prevent orphaned background processes across both Linux and Windows.
- 🔌 **Plug & Play Multi-OS Extensibility**: Fully compatible with the official Flowork OS registries:
  - [FLOWAGENT-LINUX-PLUGIN](https://github.com/flowork-os/FLOWAGENT-LINUX-PLUGIN)
  - [FLOWAGENT-WINDOWS-PLUGIN](https://github.com/flowork-os/FLOWAGENT-WINDOWS-PLUGIN)
  - [AGENT-TOOLS](https://github.com/flowork-os/AGENT-TOOLS)
  - [FLOWORK-SKILLS](https://github.com/flowork-os/FLOWORK-SKILLS)

---

## 🌐 Extensions & Ecosystem

Discover verified plugins, micro-tools, and runbooks directly on the official app store:
👉 **[https://plugins.floworkos.com](https://plugins.floworkos.com)**

---

## 📄 License & Sovereignty

Licensed under the **MIT License**. Engineered with sovereign pride by Flowork OS.

Co-authored-by: Flowork OS <agent@floworkos.com>
