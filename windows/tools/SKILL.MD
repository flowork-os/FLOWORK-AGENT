---
name: sovereign_tools_registry_architecture
title: Flowork OS Sovereign Tools Registry Architecture & Dual-Wing Standard
version: 3.1.0
description: Authoritative specification for modular external nano-plug tools, dynamic session mounting, 1File1Logic portability, and zero context pollution outside the binary kernel.
keywords: ["tools", "registry", "manifest", "nanoplug", "mounting", "sovereign", "intercepter", "telemetry", "modular", "automation", "schema", "sandbox", "terminal", "runbook", "portability", "lifecycle", "unce_radar", "zero_bloat", "exit_code_0", "references"]
exclude_keywords: ["monolithic_tool", "hardcoded_prompt", "global_pollution", "zombie_process"]
provenance: Engineered under Sovereign Flowork OS Standard. Verified with Exit Code 0 proof.
---

# 🛠️ Flowork OS Sovereign Tools Registry Architecture & Dual-Wing Standard

## 1. Core Architecture: The Nano-Plug Capability Gateway
The Level-0 Kernel (`x-flow`) is an immutable, compiled micro-kernel. All dynamic external tools operate outside the binary in `{engine_root}/tools/<tool_name>/` as independent nano-plugs communicating via JSON contracts and standard streams (stdin/stdout).

### Dynamic Tool Mounting & Zero Context Pollution
- **Anchor Tools (Permanent Kernel Tools):** Core operational capabilities active across all turns (`run_command`, `view_file`, `write_to_file`, `replace_file_content`, `ask_question`, `search_tools`).
- **Dynamic Session Tools (On-Demand Nano-Plugs):** Unmounted tools consume exactly 0 tokens. Tools are discovered via `search_tools(action: 'search', query: '...')` and dynamically mounted into the active session via `search_tools(action: 'mount', tools: ['...'])`.

---

## 2. Standard Sovereign Tool Directory Structure
Every tool in `{engine_root}/tools/<tool_name>/` must adhere to the canonical format:

```text
tools/<tool_name>/
├── manifest.json      # Dual-wing contract: schema, parameters, keywords, exclusions
├── main.mjs (or .py)  # 1File1Logic execution script (strictly 20–80 lines)
├── rules.md           # Tool operational invariants (strictly <= 40 lines)
├── trigger.md         # UNCE conditions: host telemetry, failure patterns, scopes
├── performance.md     # Execution latency & memory benchmarks
└── references/        # Payload samples, API schemas, integration playbooks
```

---

## 3. The 1File1Logic Doctrine & Cross-Platform Portability
- **Atomic Execution:** Single script containing 100% of execution logic (20–80 lines), adhering to strict JSON input/output schemas.
- **Multi-OS Portability:** Zero hardcoded paths (no `/root/`, `C:\`). Tools must run portably across Linux, Windows, and macOS using relative paths or environment variables.
- **Strict English Outputs:** All return payloads, errors, and diagnostic logs MUST be in strict English.

---

## 4. Chat Viewport HUD & Distinct Visual Tool Cards
While tools execute headlessly in the backend, the Flowork Chat Viewport dynamically transforms every active tool execution into an interactive visual card (HUD Card) in real-time. Each tool type features its own distinct visual archetype, icon, color accent, and collapsible execution body:

- **Inspect Archetype (`view_file` / `read_file`):** Blue-themed reader card with line-number slices, byte counters, and syntax preview.
- **Splice Archetype (`replace_file_content`):** Purple-themed surgical code-editor card showing visual diffs with additions (+) and deletions (-).
- **Forge Archetype (`write_to_file`):** Emerald-themed creator card with target path badge and payload size summary.
- **Task & Terminal Archetype (`run_command`):** Monospace cyber-console card with live status spinner, elapsed time, and Exit Code 0 badge.
- **Interactive Decision Card (`ask_question`):** Interactive prompt card with clickable single/multi-choice buttons rendered directly inline in chat.
- **Web Intelligence Archetype (`search_web` / `read_url`):** Cyan-themed reconnaissance card displaying cited search URLs and page snippet telemetry.
- **Generic Nano-Plug Card (`tools/<custom_tool>`):** Adaptive neon card with custom tool title, input parameters pill, and collapsible output payload.

---

## 5. Zero-Bloat On-Demand Routing Doctrine
- **Lightweight Operational Rules:** `rules.md` remains strictly concise (< 40 lines), detailing execution constraints and error mitigation.
- **Deep References Isolation:** Heavy API schemas, CLI argument cheat sheets, and integration examples reside in `references/`, accessed on-demand via `view_file`.

---

## 6. Quality Control & Audit Checklist
Prior to publishing or mounting any tool, verify:
1. `rules.md` line count <= 40 lines; `main.mjs` within 20–80 lines.
2. Exactly 20 lowercase English keywords declared identically in `SKILL.MD` and `manifest.json`.
3. Valid JSON I/O schema and cross-platform compatibility (Linux, Windows, macOS).
4. Strict English return payloads and error handling.
5. Independent subagent audit pass with Exit Code 0.
