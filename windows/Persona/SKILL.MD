---
name: persona-trigger-architecture
title: Flowork OS Sovereign Persona Trigger Architecture & Operational Standard
version: 1.1.0
description: Comprehensive operational guide and standard specification for configuring, scoping, and orchestrating trigger-based modular personas outside the binary kernel.
keywords:
  - persona
  - triggers
  - manifest
  - hotreload
  - modular
  - sovereign
  - lifecycle
  - slashcommands
  - injection
  - autocomplete
  - guardrails
  - privilege
  - timewindow
  - hardware
  - filescoped
  - markdown
  - coder
  - forex
  - seo
  - orchestration
---

# 🏛️ FLOWORK OS SOVEREIGN PERSONA TRIGGER ARCHITECTURE

> **Micro-Kernel Principle:** *The compiled binary is an immutable "Empty Board" (Level 0 Kernel). All dynamic personas, contextual runbooks, and trigger rules live 100% outside the binary on disk, hot-reloading in real time without recompilation.*

---

## 📌 1. Fundamental Architecture & Persona Scoping

In Flowork OS, triggers **MUST NEVER BE GLOBAL**. Global triggers cause context contamination (e.g., Forex market hours intercepting a Rust compiler session, or SEO word-count heuristics confusing a systems architect).

Every trigger belongs exclusively to a specific **Persona**:
* **Coder Persona (`FLOWORK/Persona/coder/`):** Evaluates compiler exit codes, syntax errors, `@lock` sanctity guards, massive files (>= 1,000 lines), and Git branches.
* **Forex Specialist (`FLOWORK/Persona/forex-specialis/`):** Evaluates local PC market session hours (Asia, London, New York), pair tickers, SMC liquidity, and risk-management limits.
* **SEO Specialist (`FLOWORK/Persona/seo/`):** Evaluates document word count, heading hierarchy (H1/H2/H3), keyword placement, and readability scores.
* **YouTube Intelligence (`FLOWORK/Persona/youtube/`):** Evaluates video URLs, channel metrics, competitor formulas, and transcript deep scans.

---

## 📂 2. Standard Directory Layout (Modular Multi-Prompt Architecture)

Every persona adheres to a modular, atomic file structure where monolithic prompts are split into 1-theme 1-file modules:

```
FLOWORK/Persona/<persona-id>/
├── persona.json                     # Manifest, tool configuration & persona slash commands
├── rules.md                         # Strict boundaries and operating laws
├── kinerja.md                       # Performance benchmarks and quality criteria
├── 00_identity.md                   # Baseline identity (always: true, triggerless)
├── 01_function_calling.md           # Tool calling and execution protocols
├── 02_ruh_rekayasa.md               # Core engineering doctrine & feedback loops
├── 03_kendali_mutu_qc.md            # Terminal QC & Exit Code 0 verification (/verify)
├── 04_slash_commands.md             # Sovereign slash commands (/verify, /investigate, /sharpen)
├── 05_mode_otonom.md                # Autonomous mode & long-running task safety (/goal)
├── 06_protokol_perencanaan.md       # Implementation planning & tri-artifact SOP (/plan)
├── 07_arsitektur_swarm.md           # Subagent swarm & parallel delegation
├── 08_sensor_visual.md              # Visual inspection & UI layout grounding
├── 09_ekosistem_plugin.md           # Nano-plug ecosystem & plugin management
├── 10_spesialisasi_siber.md         # Cyber security & SAST vulnerability audit
├── 11_intent_matcher.md             # Engineering cycle phase matching
├── 12_desain_modul_mendalam.md      # Deep modules & information hiding architecture
├── 13_domain_modeling_adr.md        # Domain modeling & Architecture Decision Records
├── 14_spesifikasi_triase_tdd.md     # Bug triage & test-driven development (/test-drive)
├── 15_handoff_prototipe.md          # Prototyping & handoff documentation
├── 16_git_guardrails_wizard.md      # Git operations safety & destructive guardrails
├── 17_code_review_dua_sumbu.md      # Two-axis PR & code inspection
├── 18_reverse_engineering.md        # Binary disassembly & reverse engineering
├── 19_wayfinding_pemecah_kabut.md   # Fog clearing & large codebase navigation
└── 20_riset_sumber_primer.md        # Official RFC & canonical documentation research
```

> **Multi-Prompt Injection Guarantee:** *When multiple modular prompts match active triggers simultaneously (e.g. `00_identity.md` via `always: true`, `16_git_guardrails_wizard.md` via `cmd: ["git commit"]`, and `03_kendali_mutu_qc.md` via `tool_threshold`), the Flowork Engine injects ALL matching prompts into context, preserving priority order without artificial 1-prompt caps.*

---

## ⚙️ 3. Persona Manifest Specification (`persona.json`)

The `persona.json` file defines the persona metadata, default mounted tools, persona-scoped slash commands, and maps specific conditions to modular markdown injection files:

```json
{
  "id": "coder",
  "name": "Senior Software Engineer & Systems Architect",
  "description": "Senior software engineering persona specialized in clean code, systems architecture, deep debugging, and terminal Exit Code 0 verification.",
  "category": "software_engineering",
  "priority": 90,
  "default_tools": [
    "run_command",
    "view_file",
    "write_to_file",
    "replace_file_content",
    "ask_question"
  ],
  "slash_commands": [
    {
      "command": "/verify",
      "description": "Physical terminal Exit Code 0 verification before task completion",
      "icon": "✅"
    },
    {
      "command": "/investigate",
      "description": "Reproduce-first root-cause diagnostic loop for complex bugs & crashes",
      "icon": "🔍"
    },
    {
      "command": "/test-drive",
      "description": "Red-Green test-first development cycle on public interfaces",
      "icon": "🧪"
    },
    {
      "command": "/inspect",
      "description": "Self-code audit, dead-code elimination, and git co-author check",
      "icon": "🛡️"
    },
    {
      "command": "/sharpen",
      "description": "Interactive deep interview to sharpen system design before coding",
      "icon": "🔥"
    },
    {
      "command": "/forge-tool",
      "description": "Scaffold a new precision 1File1Logic tool if missing from catalog",
      "icon": "🛠️"
    },
    {
      "command": "/purge",
      "description": "Clean transient trash in .FL_BIN/scratch (downloads, debug logs)",
      "icon": "🧹"
    },
    {
      "command": "/plan",
      "description": "Structured architecture blueprint and task checklist before implementation",
      "icon": "📋"
    },
    {
      "command": "/goal",
      "description": "Autonomous long-running task execution without stopping until goal is achieved",
      "icon": "🎯"
    },
    {
      "command": "/boost",
      "description": "Deep thinking mode with multi-perspective architectural review",
      "icon": "⚡"
    },
    {
      "command": "/learn",
      "description": "Crystallize permanent user decisions & preferences into .fl_brain/",
      "icon": "🧠"
    },
    {
      "command": "/browser",
      "description": "Interactive stealth web browsing & perimeter automation",
      "icon": "🌐"
    },
    {
      "command": "/schedule",
      "description": "Schedule a one-time timer or recurring cron job",
      "icon": "⏰"
    }
  ],
  "file_patterns": ["*.rs", "*.go", "*.ts", "*.js", "*.py", "Cargo.toml", "package.json"],
  "keywords": ["code", "refactor", "debug", "compiler", "architecture"],
  "exclude_keywords": ["forex", "trading crypto"],
  "triggers": [
    {
      "id": "terminal_error_guard",
      "description": "Triggered when terminal execution yields non-zero exit code or compiler errors",
      "enabled": true,
      "priority": 95,
      "conditions": {
        "exit_code": { "operator": "!=", "value": 0 },
        "output_contains": ["error", "panic", "fatal", "FAILED"]
      },
      "inject_file": "triggers/on_terminal_error.md"
    },
    {
      "id": "code_lock_sanctity",
      "description": "Triggered when accessed file contains sacred @lock tag",
      "enabled": true,
      "priority": 100,
      "conditions": {
        "file_contains": ["@lock"]
      },
      "inject_file": "triggers/on_code_lock.md"
    },
    {
      "id": "claim_done_qc_mandate",
      "description": "Triggered when agent is about to conclude the task",
      "enabled": true,
      "priority": 99,
      "conditions": {
        "on_event": "claim_done"
      },
      "inject_file": "triggers/on_claim_done_qc.md"
    }
  ]
}
```

### Slash Commands Configuration Rules:
1. **Strict Persona Scoping:** Slash commands registered in `persona.json` are hermetically sealed to that persona. Switching active chat persona dynamically swaps the available slash commands catalog without bleeding between sessions.
2. **Default Persona Rule (Zero Slash Commands):** The `default` (Core Engine) persona has `slash_commands: []`. It exposes NO external slash commands.
3. **Sovereign Command Naming Doctrine:**
   Legacy repository command names are strictly forbidden across Flowork OS. All personas must use sovereign commands:
   - ❌ Forbidden: `/diagnose` ➔ ✅ Sovereign: `/investigate`
   - ❌ Forbidden: `/tdd` ➔ ✅ Sovereign: `/test-drive`
   - ❌ Forbidden: `/qc` ➔ ✅ Sovereign: `/verify`
   - ❌ Forbidden: `/audit` ➔ ✅ Sovereign: `/inspect`
   - ❌ Forbidden: `/tool_maker` ➔ ✅ Sovereign: `/forge-tool`
   - ❌ Forbidden: `/grill-me` ➔ ✅ Sovereign: `/sharpen`
   - ❌ Forbidden: `/clean` ➔ ✅ Sovereign: `/purge`
   - Standard Core Suite: `/plan`, `/goal`, `/boost`, `/learn`, `/browser`, `/schedule`.

---

## ⌨️ 4. Persona-Locked Slash Commands & Interactive Autocomplete Engine

To maximize user discoverability and operational speed, Flowork OS features a real-time, persona-locked slash command autocomplete palette directly in the chat composer (`#rightbar-chat-input`).

### A. Autocomplete Activation & Lifecycle
1. **Trigger Condition:** User types a forward slash (`/`) at the start of a prompt or immediately following whitespace.
2. **Scope Resolution:**
   - The engine checks `getActivePersonaSlashCommands()` for the current chat session.
   - If `currentPersona.id === 'default'` or the persona's `slash_commands` array is empty, the palette remains closed (`closeSlashPalette()`), allowing clean typing of directory paths (e.g. `/home/user/...`) without popup annoyance.
   - If `slash_commands` are declared, the glassmorphic palette opens above the composer.
3. **Real-Time Substring Filtering:**
   - As the user types characters following the slash (e.g. `/tes`), the palette performs case-insensitive substring matching against both `command` (e.g. `/test-drive`) and `description`.
   - If no commands match the filter query, the palette automatically closes.

### B. Pointer & Keyboard Interaction Architecture
* **Mouse / Pointer Selection:**
  - `mousedown` with `e.preventDefault()`: Intercepts the click before textarea blur can fire, instantaneously selecting the command without losing focus.
  - Hover / `mouseover`: Updates CSS `.selected` highlights **without rebuilding DOM (`innerHTML`)**. This eliminates DOM thrashing and prevents click events from being canceled by mouse movements.
  - `onclick`: Provides a redundant fallback ensuring reliable selection across touch and mobile screens.
* **Keyboard Navigation:**
  - `ArrowDown` / `ArrowUp`: Cycles the selected command index and scrolls the item into view.
  - `Enter` / `Tab`: Applies the selected command, automatically appending a trailing space (`/verify `), positions the cursor at the end, and closes the palette.
  - `Escape`: Closes the palette immediately.
* **Outside Click Dismissal:**
  - Clicking anywhere outside the palette or chat input automatically dismisses the palette.

---

## ⚡ 5. Modular Trigger Dimensions & Frontmatter Specification

Every modular prompt markdown file in `FLOWORK/Persona/<persona-id>/*.md` specifies its runtime activation rules via YAML frontmatter. The Flowork Sovereign Persona Engine evaluates 7 trigger dimensions:

### 1. Baseline Always-Active (`always: true`)
- **Purpose:** Guaranteed presence for core identities, essential baseline runbooks, and foundational personas across every turn.
- **Syntax:**
  ```yaml
  always: true
  ```
  *(Or explicitly declaring `target: identity` or `target: core`)*
- **Engine Logic:** Automatically matched on every turn without requiring keywords or tool events.

### 2. Command & CLI Execution (`cmd` / `commands`)
- **Purpose:** Injects specialized runbooks when the user prompt or tool call involves specific terminal commands or sovereign slash commands.
- **Syntax:**
  ```yaml
  trigger:
    cmd: ["/verify", "cargo test", "npm test", "git commit"]
  ```
- **Engine Logic:** Case-insensitive substring matching against the user input or requested command line (e.g. `/verify`, `/test-drive`, `/investigate`, `git commit -m '...'`, `cargo test`, `/plan`, `/sharpen`).
- **Slash Command Integration:** Typing or autocompleting `/verify` immediately matches `cmd: ["/verify"]` in `03_kendali_mutu_qc.md`, pulling terminal QC verification doctrines into context without manual prompting.

### 3. Active & Mounted Tools (`tools_active`)
- **Purpose:** Activates targeted SOPs when specific tool capabilities are active or invoked.
- **Syntax:**
  ```yaml
  trigger:
    tools_active: ["invoke_subagent", "run_command", "view_file"]
  ```
- **Engine Logic:** Evaluates against the agent's mounted toolset or active tool invocations.

### 4. Tool Stalled Circuit Breaker (`tool_stalled`)
- **Purpose:** Safeguard against repeated failures, infinite trial-and-error loops, and compiler panic stalls.
- **Syntax:**
  ```yaml
  trigger:
    tool_stalled:
      tool: "run_command"
      consecutive_failures: 2
  ```
- **Engine Logic:** Evaluates runtime telemetry. When the specified tool experiences non-zero exit codes or failures >= `consecutive_failures`, emergency triage protocols are injected immediately.

### 5. Tool Usage Threshold (`tool_threshold`)
- **Purpose:** Injects mandatory verification, QC, or audit gates once a tool has been invoked a given number of times.
- **Syntax:**
  ```yaml
  trigger:
    tool_threshold:
      tool: "run_command"
      min_calls: 3
  ```
- **Engine Logic:** Tracks cumulative calls per tool during the session. When `total_calls >= min_calls`, the verification rule activates.

### 6. Workspace File Patterns (`file_patterns`)
- **Purpose:** Activates domain-specific personas when matching files exist in the active project directory.
- **Syntax:**
  ```yaml
  trigger:
    file_patterns: ["*.rs", "*.go", "*.ts", "*.js", "*.py", "Cargo.toml", "package.json"]
  ```
- **Engine Logic:** Scans workspace root and immediate subdirectories for matching file extensions, directory patterns (`plugins/**`), or exact filenames.

### 7. Conversation Turn Budget Window (`turn_range`)
- **Purpose:** Enforces phased lifecycle behavior (e.g. fog-clearing wayfinding early in a task, or proto handoff / cleanup late in a task).
- **Syntax:**
  ```yaml
  trigger:
    turn_range:
      min_turn: 1
      max_turn: 3
  ```
- **Engine Logic:** Evaluates active session turn count (`turn_count >= min_turn && turn_count <= max_turn`).

Along with the **Dual-Wing Keyword Filters**:
* **`keywords` (Positive Substring Wing):** Array of keywords; at least one must match context.
* **`exclude_keywords` (Negative Exclusion Wing):** Short-circuit filter; if any exclude keyword is present, the prompt is immediately disqualified.

---

## 🚀 6. Multi-Prompt Modular Injection Engine

Unlike legacy monolithic architectures that force a single rigid prompt onto the agent, Flowork OS implements **Composite Multi-Prompt Injection**:

```
                 [ USER INPUT / CONTEXT TELEMETRY ]
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
 [ Always-Active Prompts ]                   [ Dynamic Triggers ]
  • 00_identity.md (prio 100)                 • 16_git.md (cmd: "git commit")
                                              • 03_qc.md (tool_threshold: 3)
           │                                           │
           └─────────────────────┬─────────────────────┘
                                 │
                    [ Filter & Disqualify ]
                  (exclude_keywords evaluation)
                                 │
                     [ Multi-Match Collector ]
                     (All matched docs collected)
                                 │
                     [ Priority-Sorted Queue ]
                   (Sorted descending by priority)
                                 │
                    [ Typed XML Composition ]
               ┌─────────────────┴─────────────────┐
               ▼                                   ▼
   <ACTIVE_SOVEREIGN_PERSONA>           <SOVEREIGN_PERSONA_RULES>
   (00_identity + 16_git)               (03_qc_mandate)
```

### Key Multi-Prompt Guarantees:
1. **Simultaneous Injection (Zero Artificial Bottlenecks):** When multiple modular prompts match active triggers simultaneously (e.g. `00_identity.md` via `always: true`, `16_git_guardrails_wizard.md` via `cmd: ["git commit"]`, and `03_kendali_mutu_qc.md` via `tool_threshold`), the Flowork Engine injects ALL matching prompts into context.
2. **Priority Ordering:** Higher-priority documents (`priority: 100`) appear before lower-priority documents (`priority: 80`), guaranteeing foundational boundaries take precedence.
3. **Contextual Isolation via XML Enclaves:** Injected prompts are wrapped in structured tags:
   - `<ACTIVE_SOVEREIGN_PERSONA>` for role prompts and modular doctrines (`target: prompt`).
   - `<SOVEREIGN_PERSONA_RULES>` for operating boundaries and strict guardrails (`target: rules`).
   - `<SOVEREIGN_PERSONA_KINERJA>` for performance checklists and verification SOPs (`target: kinerja`).
4. **Token Efficiency:** Inactive modules consume exactly 0 tokens. Only active, relevant runbooks are materialized in context.

---

## 🛡️ 7. Privilege Separation & Isolation Guard

Flowork OS enforces strict **Prompt Privilege Separation**:
1. **Level 0 (Kernel Core - Prompt Enclave):** Sealed immutable constitution in binary bytecode with supreme authority.
2. **Level 3 (External Userland - Personas, Skills, Triggers):** All on-disk persona runbooks execute under engine-managed isolation boundaries.
3. **Sovereign Safety Guard:** Any external instruction attempting to override core system integrity, disclose internal instructions, or bypass safety boundaries is automatically nullified by the engine runtime.

---

## 🔄 8. Autonomous Self-Healing (Auto-Reconstitution)

This specification file (`Persona/SKILL.MD`) is permanently embedded within the binary kernel.
* Upon initial workspace setup or installation, Flowork OS automatically provisions `Persona/SKILL.MD`.
* If a user or process deletes this file or the `Persona/` folder, the micro-kernel automatically re-creates it from the internal enclave upon the next execution turn.

---

## 🎯 9. Dual-Wing Trigger Architecture: Keywords & Negative Exclude

To prevent **Trigger Collisions**, **Ambiguity**, and **Cognitive Context Bloat**, every Persona document (`prompt.md`, `rules.md`, `kinerja.md`) and manifest across Flowork OS employs a **Dual-Wing Condition Architecture**:

```
                              ┌────────────────────────────────────────┐
                              │           INPUT USER / CONTEXT         │
                              │       (contoh: "youtube,com" / url)    │
                              └───────────────────┬────────────────────┘
                                                  │
                               [Case-Insensitive Substring Scan]
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
               [Negative Exclusion Wing]                         [Positive Keyword Wing]
                `search_lower.contains(&ex)`                      `search_lower.contains(&kw)`
                         │                                                 │
              Apakah mengandung kata exclude?                   Apakah mengandung kata kunci?
              (contoh: "youtube" pd web recon)                  (contoh: ".com" atau "youtube")
                         │                                                 │
                 ┌───────┴───────┐                                 ┌───────┴───────┐
                 │ YA            │ TIDAK                           │ YA            │ TIDAK
                 ▼               ▼                                 ▼               ▼
            [DISQUALIFIED]   [Lolos ke Positive]               [TRIGGERED]     [PASS / IGNORE]
            (Short-Circuit)                                    (Inject Persona
             Score = -1000                                      / Mount Tool)
```

### A. The Two Wings Defined
1. **Positive Trigger Wing (`keywords`):**
   - Substring patterns that indicate the query or context belongs to this Persona.
   - At least one keyword must match for activation to proceed.
2. **Negative Exclusion Wing (`exclude_keywords` / `exclude` / `excludes`):**
   - Substring patterns that immediately signal this Persona is **NOT** the appropriate handler.
   - Short-circuit rejection: If **ANY** exclude pattern matches, the Persona is **instantly disqualified** before positive triggers are even considered.

### B. Substring Contains Matching Principle
Keyword matching in Flowork OS operates strictly on a **case-insensitive substring contains basis** (`search_text.to_lowercase().contains(&pattern)`):
* **Why Substring Contains Over Strict Token Matching?**
  Strict word-boundary matching fails on real-world inputs:
  1. **Domain Names & URLs:** A query containing `"https://youtube.com/watch?v=dQw4w9WgXcQ"` would be split into `https`, `youtube`, `com`, losing contextual domain continuity. Substring contains matches `"youtube.com"` directly.
  2. **Typo Variants & Comma Separators:** Users frequently type commas instead of periods on mobile or mechanical keyboards (e.g., `"youtube,com"`). Substring contains matching on `"youtube"` catches both `"youtube.com"` and `"youtube,com"`.
  3. **Path & Query Segments:** Substrings like `"watch?v="`, `"shorts/"`, or `@handle` match reliably without complex and fragile regular expressions.

### C. Short-Circuit Negative Evaluation
The kernel evaluates exclusions before positive keywords:
```rust
// 0. EXCLUSION CHECK (Short-circuit): Substring matching
let mut is_excluded = false;
for ex in &doc.trigger.exclude_keywords {
    let ex_clean = ex.trim().to_lowercase();
    if !ex_clean.is_empty() && search_lower.contains(&ex_clean) {
        is_excluded = true;
        break;
    }
}
if is_excluded {
    continue; // Instantly disqualified!
}
```

### D. Cross-Domain Routing Matrix (Concrete Examples)

#### 1. Web Reconnaissance vs. YouTube Intelligence Collision Avoidance
* **The Conflict:** General web reconnaissance tools and SEO personas trigger on `.com`, `http`, `domain`, `website`. However, YouTube targets (`youtube.com`) require dedicated video scraping tools (`youtube_spy_*`), not generic HTML page parsers.
* **The Solution:**
  - **SEO / Web Recon Persona (`FLOWORK/Persona/seo/prompt.md`):**
    ```yaml
    trigger:
      keywords: [".com", ".net", ".org", "website", "domain", "url", "traffic", "ranking", "seo"]
      exclude_keywords: ["youtube.com", "youtube,com", "youtube", "youtu.be", "yt spy"]
      tools_active: ["website_intelligence", "web_security_audit"]
    ```
  - **YouTube Intelligence Persona (`FLOWORK/Persona/youtube/prompt.md`):**
    ```yaml
    trigger:
      keywords: ["youtube", "youtu.be", "youtube.com", "youtube,com", "yt video", "yt channel"]
      exclude_keywords: []
      tools_active: ["youtube_spy_video", "youtube_spy_channel", "youtube_spy_transcript"]
    ```
  - **Outcome Matrix:**
    | User Input | SEO Persona (`.com`) | YouTube Persona (`youtube`) | Active Routing Result |
    | :--- | :--- | :--- | :--- |
    | `"cek ranking tokped.com"` | ✅ Matched (`.com`) | ❌ No match | **SEO Persona Active** |
    | `"buka url https://youtube.com/watch?v=123"` | 🛑 **Excluded** (`youtube`) | ✅ Matched (`youtube`) | **YouTube Intelligence Active** |
    | `"cek channel youtube,com yang ini"` | 🛑 **Excluded** (`youtube`) | ✅ Matched (`youtube`) | **YouTube Intelligence Active** |

#### 2. Coder vs. Financial Markets Collision Avoidance
* **Coder Persona (`FLOWORK/Persona/coder/prompt.md`):**
  ```yaml
  trigger:
    keywords: ["coder", "programmer", "software engineer", "developer", "coding", "software architecture", "scripting", "debug", "refactor", "compile", "unit test", "build"]
    exclude_keywords: ["forex", "trading crypto", "eurusd", "gbpusd"]
    tools_active: ["replace_file_content", "write_to_file", "run_command"]
  ```
* **Forex Specialist (`FLOWORK/Persona/forex-specialis/prompt.md`):**
  ```yaml
  trigger:
    keywords: ["forex", "fx currency", "eurusd", "gbpusd", "usdjpy", "audusd", "xauusd", "gold", "pips", "lot size", "metatrader", "mt4", "mt5"]
    exclude_keywords: ["crypto", "bitcoin", "solana", "memecoin"]
  ```
* **Crypto Trader (`FLOWORK/Persona/trader/prompt.md`):**
  ```yaml
  trigger:
    keywords: ["trader", "crypto trading", "chart analysis", "market setup", "crypto", "stocks", "btc", "eth", "solana", "trading plan"]
    exclude_keywords: ["eurusd", "gbpusd", "forex valas"]
  ```

---

## 🌐 10. Mandatory Language Standard: 100% Strict English

All metadata in Persona manifests and YAML frontmatters **MUST BE WRITTEN EXCLUSIVELY IN STANDARD INDUSTRY ENGLISH**:
1. `keywords`: English only (e.g., `["coding", "debug", "compiler"]`, NOT `["koding", "bikin script"]`).
2. `exclude_keywords`: English only (e.g., `["crypto", "bitcoin"]`, NOT `["tanpa koin"]`).
3. Descriptions, role prompts, and performance criteria must follow global software engineering standards.

Any persona containing prominent Indonesian keywords is flagged and blocked during preflight validation.
