<div align="center">

# ⚡ Flowork OS — The Sovereign Autonomous Desktop Agent

**Stop babysitting AI assistants that guess, bloat tokens, and break on compiled code. Flowork OS is a polymorphic, runbook-governed engineering engine with native binary reverse engineering, 116+ Dual-Wing nano-plugs, and empirical Exit Code 0 verification.**

[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-00F5FF?style=for-the-badge&logo=linux&logoColor=white)](https://floworkos.com)
[![Architecture](https://img.shields.io/badge/Personas-7D%20Hermetic%20Triggers-FF6F00?style=for-the-badge&logo=rust&logoColor=white)](https://floworkos.com)
[![Tools](https://img.shields.io/badge/Nano--Plugs-116%2B%20Dual--Wing-00D26A?style=for-the-badge&logo=openapiinitiative&logoColor=white)](https://github.com/flowork-os/AGENT-TOOLS)
[![Disassembly](https://img.shields.io/badge/Binary%20Archaeology-Native%20%7C%20CIL%20%7C%20ASAR-8A2BE2?style=for-the-badge&logo=binary&logoColor=white)](https://floworkos.com)
[![Portability](https://img.shields.io/badge/Portability-100%25%20Zero--Dependency-FF0055?style=for-the-badge&logo=powershell&logoColor=white)](https://floworkos.com)
[![Verification](https://img.shields.io/badge/Quality-Empirical%20Exit%20Code%200-FFD700?style=for-the-badge)](https://floworkos.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

<br />

<a href="#-get-flowork-agent--zero-setup">
  <img src="https://img.shields.io/badge/%E2%9A%A1%20DOWNLOAD%20FLOWORK%20AGENT-CHOOSE%20YOUR%20OS%20%E2%86%92-FF0055?style=for-the-badge&logo=rocket&logoColor=white&labelColor=0D1117" alt="Download Flowork Agent" height="54" />
</a>

<br /><br />

<p align="center">
  <a href="#-get-flowork-agent--zero-setup">Quickstart</a> •
  <a href="#-the-developer-reality">The Problem</a> •
  <a href="#-the-sovereign-advantage">Core Advantages</a> •
  <a href="#-the-six-sovereign-superpowers">Six Superpowers</a> •
  <a href="#-honest-industry-benchmark">Benchmark Matrix</a> •
  <a href="#-official-ecosystem">Ecosystem</a>
</p>

---

</div>

## 😤 The Developer Reality (Why Typical Agents Frustrate You)

Modern AI coding assistants look impressive in scripted demos, but fall apart during real, complex software engineering workflows:

1. **Fragile, Heavyweight MCP Daemons**: Standard Model Context Protocol (MCP) servers drag gigabytes of dependencies, crash on stderr streams, and leave zombie background processes on your machine.
2. **Text-Only Blindness**: Existing tools are limited strictly to plain text source code. The moment you give them a compiled binary (`ELF`, `PE`, `Mach-O`), a `.NET` assembly, or an Electron `ASAR` bundle without source code, they surrender.
3. **Massive Context & Token Bloat**: Monolithic agents dump dozens of static tool definitions into every prompt turn, burning 3,000–8,000 tokens before you even type a word. Attention is diluted, and API costs skyrocket.
4. **The "Polite Flattery" Hallucination**: AI assistants declare tasks complete with cheerful pleasantries (*"I've fixed everything!"*), only for you to find broken code and unhandled exceptions the moment you run it.
5. **Session Amnesia & Cross-Contamination**: New chats forget previous architectural ADRs, or worse, leak system prompts across concurrent tasks.

---

## 🎯 The Sovereign Advantage

Flowork OS rejects the status quo of guessing and flattery. It is built as a **self-contained desktop intelligence engine**:

* ⚡ **Rust Micro-Kernel (`x-flow`)**: High-performance Fat LTO + stripped native kernel (~7.5 MB) with sealed prompt enclaves.
* 🎭 **Polymorphic Engineering Division**: 5 dynamic persona suites governed by 7-dimensional hermetic trigger routing.
* 🔬 **Native Binary Archaeology**: First desktop agent capable of decompilation, AST slicing, and clean-room reconstruction without source code.
* 🧩 **116+ Dual-Wing Nano-Plugs**: Agnostic modular tools with Triple-Lock error containment (100% Exit Code 0 guaranteed).
* 🧳 **100% True Portability**: Zero Docker, zero host Node/Python pre-installation. Double-click and run from any folder, secondary SSD, or USB drive.

---

## 🚀 The Six Sovereign Superpowers

### 1. 🎭 Polymorphic Personas with 7-Dimensional Hermetic Triggers
Unlike flat, one-size-fits-all agents, Flowork morphs its cognitive identity dynamically based on the exact problem you are solving:

| Persona Suite | Focus & Specialization | Slash Commands |
| :--- | :--- | :--- |
| **`coder`** | Clean Architecture, Systems Engineering, TDD, ADR Modeling | `/plan`, `/grill-me`, `/boost` |
| **`reverse-engineer`** | Binary Disassembly, ASM/High-Pcode Analysis, Clean-Room Reconstruction | `/triage`, `/decompile`, `/trace-flow`, `/cil-inspect` |
| **`tool-architect`** | OpenAPI Dual-Wing Nano-Plug Authoring, SAST Scanning, Live QC | `/audit-tools`, `/scaffold-tool` |
| **`plugin-architect`** | Canvas UI Widgets, Web Worker Hubs, Microservice Gatekeepers | `/build-plugin`, `/publish-gate` |
| **`persona-forge`** | Synthetic Persona Crafting, Runbook Extraction & SOP Calibration | `/forge-persona` |

#### 🌐 7-Dimensional Trigger Engine
Prompts are never dumped all at once. They are activated with pinpoint precision by 7 trigger dimensions:
- **`cmd`**: Triggers on exact CLI commands or slash shortcuts.
- **`tools_active` & `tool_threshold`**: Mounts specialized instructions based on active tool sets.
- **`tool_stalled` (Circuit Breaker)**: When consecutive tool failures occur, the engine halts speculation and immediately triggers deep triage and root-cause analysis runbooks.
- **`file_patterns`**: Samples workspace files dynamically (e.g., activating reverse-engineering protocols only when `*.elf`, `*.dll`, or `*.asar` are detected).
- **`turn_range`**, **`keywords`**, and **`exclude_keywords`**: Prevents trigger misfires and context bleeding.
- **Hermetic Scoping**: Zero prompt leakage across distinct session IDs.

---

### 2. 🔬 Native Binary Archaeology & Clean-Room Reconstruction
Flowork OS is the **only desktop AI agent** engineered from the ground up for deep binary reverse engineering without access to original source code:

* **Polyglot Disassembly**: Native inspection of Linux `ELF`, Windows `PE`, Apple `Mach-O`, `.NET ECMA-335 CIL` bytecode, Electron `ASAR` archives, minified web bundles, and Android `APK` packages.
* **The Epistemic Triad (Anti-Hallucination Law)**: Every technical output must be classified:
  - `[OBSERVATION]`: Empirical facts read directly from raw bytes, assembly instructions, or terminal proof.
  - `[INFERENCE]`: Deductive reasoning with an explicit confidence level (`High`, `Medium`, `Hypothetical`).
  - `[UNKNOWN]`: Explicitly mapped unresolved gaps, stripped symbols, or unreachable code branches.
* **Reconstruction Obligation Ledger**: Verifies clean-room implementations (in modern Rust, TypeScript, or Go) against original binary contracts using automated test vectors.

---

### 3. 🧩 The 116+ OpenAPI Dual-Wing Nano-Plug Ecosystem
We replaced slow, bloated MCP servers with standalone, ultra-lean **Nano-Plugs**:

* **1File1Logic**: Pure, focused ES module scripts (20–80 lines) with zero zombie background daemons.
* **Triple-Lock Error Containment**: All tools catch uncaught exceptions, traps, and errors internally, returning structured JSON with status `ERROR` and Exit Code 0—preventing process crashes.
* **Dual-Wing Keyword Routing**: Positive keywords pair with negative exclusion wings (`exclude_keywords`) to ensure tools are only mounted when mathematically relevant.
* **O(1) Crates.io Sharded Registry**: Fast sharded index (`flowork-os/AGENT-TOOLS`) allows on-demand remote searching, caching, and instant JIT installation via `search_tools`.

---

### 4. 🧪 Empirical Quality Control (Proof by Exit Code 0)
Flowork OS operates under radical honesty:
* **Zero Flattery**: No empty praise (*"Great idea!"*, *"All done!"*). Technical output is direct, data-driven, and verified.
* **Terminal Proof**: A task is never marked complete until verified by an active terminal execution with **Exit Code 0**.
* **Automatic Code & Zombie File Elimination**: Post-refactor cleanups automatically sweep dead code, temporary artifacts, and scratch directories into `.FL_BIN/` or `.flowork_spam/`.

---

### 5. 🎨 Native Live Desktop Canvas
Software engineering is inherently visual:
* **Real-Time Interactive Canvas**: Render frontends, test interactive tools, and preview audio/visual applications side-by-side with your chat.
* **Modular Extensions**: Run standalone canvas plugins without wrestling with port conflicts or orphan services.

---

### 6. 🧳 100% True Zero-Dependency Portability
* **Windows**: Single standalone directory. Double-click `flowork.bat` or run `x-flow.exe`.
* **Linux**: Standalone directory. Run `./flowork.sh` or double-click `Flowork-Agent-Installer.desktop`.
* **Zero Host Pollution**: No global node packages, no Python virtual environments, and no Docker daemon required. Extract and work from any local or external drive.

---

## ⚖️ Honest Industry Benchmark

| Architectural Dimension | Claude Code (CLI) | Cursor / Windsurf | Devin / OpenDevin | **Flowork OS** |
| :--- | :---: | :---: | :---: | :---: |
| **Execution Architecture** | Terminal CLI Text | Editor Extension | Cloud Docker VM | **Native Sovereign Desktop OS** |
| **Engine Footprint** | Heavy Node.js Runtime | Electron Bloat (~1.2 GB) | Multi-GB Cloud Image | **7.5 MB Rust Micro-Kernel** |
| **Persona Intelligence** | Single Flat Persona | Single Generalist | Monolithic Agent | **5 Polymorphic Personas (7D Triggers)** |
| **Binary Disassembly Suite** | ❌ Text Source Only | ❌ Text Source Only | ❌ Text Source Only | **✅ Native Binary (ELF / PE / Mach-O / CIL / ASAR)** |
| **Extensible Tool Standard** | Heavy MCP Daemons | Internal Closed APIs | Ad-hoc Python Scripts | **✅ 116+ Dual-Wing Nano-Plugs (O(1) Sharded)** |
| **Tool Failure Resilience** | Error dump to user | Endless Retry Loop | Hard VM Restart | **✅ Circuit Breaker (`tool_stalled` auto-triage)** |
| **Anti-Hallucination Doctrine** | Model self-confidence | Politeness & Flattery | Log heuristics | **✅ Epistemic Triad (`[OBSERVATION]` / `[INFERENCE]`)** |
| **Context Token Overhead** | Dumps full tool schemas | Injects IDE workspace | Cloud token burn | **Dynamic On-Demand (~18% leaner than Antigravity)** |
| **Verification Gate** | LLM self-claim | Manual user check | User PR review | **Automated Empirical Exit Code 0 Proof** |
| **Portability & Setup** | Requires Node / NPM | Heavy App Installer | Requires Cloud Subscription | **100% Standalone Portable (Zero Deps)** |

---

## ⚡ Get Flowork Agent (Zero Setup)

Our official installers are lightweight net-bootstrappers that stream and verify the freshest release directly from the repository.

### 📥 Official Direct Downloads:

| Platform | Installer File | How to Launch | Direct Download |
| :--- | :--- | :--- | :---: |
| 🪟 **Windows** | **`Flowork-Agent-Installer.exe`** | Place in your chosen folder and double-click | [**Download .exe**](https://github.com/flowork-os/FLOWORK-AGENT/releases/latest/download/Flowork-Agent-Installer.exe) |
| 🐧 **Linux** | **`Flowork-Agent-Installer.desktop`** | Double-click from Desktop or File Manager | [**Download .desktop**](https://github.com/flowork-os/FLOWORK-AGENT/releases/latest/download/Flowork-Agent-Installer.desktop) |

#### Terminal 1-Liner (Linux):
```bash
curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/linux/install.sh | bash
```

---

## 🌐 Official Sovereign Ecosystem

- 🛠️ **[AGENT-TOOLS](https://github.com/flowork-os/AGENT-TOOLS)**: The official sharded registry of 119+ high-performance nano-plugs and MCP contracts.
- 📚 **[FLOWORK-SKILLS](https://github.com/flowork-os/FLOWORK-SKILLS)**: Curated library of standardized runbooks and SOPs.
- 🐧 **[FLOWAGENT-LINUX-PLUGIN](https://github.com/flowork-os/FLOWAGENT-LINUX-PLUGIN)**: Linux desktop canvas extensions.
- 🪟 **[FLOWAGENT-WINDOWS-PLUGIN](https://github.com/flowork-os/FLOWAGENT-WINDOWS-PLUGIN)**: Windows desktop canvas extensions.
- 🏪 **[App Store Portal](https://plugins.floworkos.com)**: Official community web registry for plugins and extensions.

---

## 📄 License

Licensed under the **MIT License**. Built with sovereign engineering discipline by the Flowork OS Community.

Co-authored-by: Flowork OS <agent@floworkos.com>
