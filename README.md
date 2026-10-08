<div align="center">

# ⚡ Flowork OS — Sovereign AI Agent & Canvas Host

**Autonomous Multi-OS Desktop Environment, Sovereign AI Agent Switchboard & Canvas Host**

[![Platform](https://img.shields.io/badge/Platform-Linux%20x86__64%20%7C%20Windows%2010%2F11-00F5FF?style=for-the-badge)](https://floworkos.com)
[![Architecture](https://img.shields.io/badge/Architecture-Sovereign%20Multi--OS-FF6F00?style=for-the-badge)](https://floworkos.com)
[![Runtime](https://img.shields.io/badge/Core-Rust%20%7C%20Node.js%20%7C%20WASM-339933?style=for-the-badge)](https://floworkos.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](https://github.com/flowork-os/FLOWORK-AGENT/pulls)

<br />

<a href="#-quick-start--installation">
  <img src="https://img.shields.io/badge/%E2%9A%A1%20GET%20STARTED%20NOW-CHOOSE%20YOUR%20OS%20%E2%86%92-FF0055?style=for-the-badge&logo=rocket&logoColor=white&labelColor=0D1117" alt="Get Started Now" height="54" />
</a>

<br /><br />

<p align="center">
  <a href="#-quick-start--installation">Installation</a> •
  <a href="#-repository-structure">Structure</a> •
  <a href="#-key-capabilities">Capabilities</a> •
  <a href="#-extensions--ecosystem">Ecosystem</a> •
  <a href="#-license">License</a>
</p>

---

</div>

## 🚀 Quick Start & Installation

### 🐧 Linux (x86_64, AArch64)

#### 1. One-Liner Autonomous Installer
Run directly in your Linux terminal:
```bash
curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/linux/install.sh | bash
```

#### 2. Manual Launch
Navigate into the `linux/` directory and run:
```bash
chmod +x flowork.sh x-flow
./flowork.sh
```

---

### 🪟 Windows (10, 11, Server)

#### 1. Quick Launch
1. Download or clone this repository.
2. Open the `windows/` folder.
3. Double-click **`flowork.bat`** (or right-click `run.ps1` and select *Run with PowerShell*).

#### 2. Command Line / PowerShell
```powershell
cd windows
.\flowork.bat
```

---

## 🏛️ Repository Structure

This repository is strictly partitioned into dedicated, clean multi-OS trees:

```
FLOWORK-AGENT/
├── linux/                        # 🐧 Pure Linux Agent Distribution
│   ├── x-flow                    # Native Linux compiled core engine
│   ├── flowork.sh                # Interactive shell launcher
│   ├── run.sh                    # Direct runner
│   ├── install.sh                # Autonomous Linux system installer
│   ├── X-Flow.desktop            # Desktop application entry
│   ├── flowork/                  # Daemon binary runner & mock runtime
│   ├── hooks/                    # Shell hooks (.sh, .cjs)
│   ├── canvas-ui/                # Member area & interactive webview
│   ├── connection/               # Gateway & model resolver bridge
│   ├── mcp/                      # Model Context Protocol runtime
│   ├── plugins/                  # Local plugin mount point
│   ├── skills/                   # Local skill mount point
│   └── tools/                    # Local micro-tool mount point
│
├── windows/                      # 🪟 Pure Windows Agent Distribution
│   ├── x-flow.exe                # Native Windows compiled core engine
│   ├── flowork.bat               # Interactive batch launcher
│   ├── run.bat                   # Batch runner
│   ├── run.ps1                   # PowerShell runner
│   ├── flowork/                  # Daemon binary runner & mock runtime
│   ├── hooks/                    # Windows hooks (.bat, .ps1, .cjs)
│   ├── canvas-ui/                # Member area & interactive webview
│   ├── connection/               # Gateway & model resolver bridge
│   ├── mcp/                      # Model Context Protocol runtime
│   ├── plugins/                  # Local plugin mount point
│   ├── skills/                   # Local skill mount point
│   └── tools/                    # Local micro-tool mount point
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
