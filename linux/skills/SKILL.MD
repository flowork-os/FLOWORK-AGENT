---
name: sovereign_skills_nano_modular_architecture
title: Flowork OS Sovereign Skills Nano-Modular Architecture & SOP Standard
version: 4.1.0
description: Authoritative specification for nano-modular skills, 1-to-1 keyword references, on-demand modular example blueprints, GitHub tri-repo synthesis, and hard-gate kernel enforcement outside the binary kernel.
keywords: ["skill", "modular", "nano", "keywords", "references", "example", "github", "synthesis", "sovereign", "runbook", "rules", "overview", "performance", "intercept", "zero_bloat", "router", "audit", "exit_code_0", "lifecycle", "subagent"]
exclude_keywords: ["monolithic_skill", "ai_slop", "hardcoded_prompt", "prompt_bloat"]
provenance: Engineered under Sovereign Flowork OS Standard. Verified with Exit Code 0 proof.
---

# 🏛️ Flowork OS Sovereign Skills Nano-Modular Architecture Standard

## 1. Core Architecture: Micro-Kernel & The Nano-Modular Standard
The Level-0 Kernel (`x-flow`) is an immutable, compiled micro-kernel. Domain skills and Standard Operating Procedures (SOPs) live entirely outside the binary in `{engine_root}/skills/<skill_id>/`, hot-reloaded dynamically at runtime without kernel recompilation.

To eliminate prompt bloat and enforce zero-hallucination execution, skills are structured as **atomic nano-modules**:
- **Zero Monolith Doctrine:** A skill is never stored as a single giant monolithic markdown file.
- **Strict Prohibition:** Creating `SKILL.md` or `trigger.md` inside any individual skill directory (`skills/<skill_id>/`) is STRICTLY FORBIDDEN and will cause immediate audit rejection!
- **Semantic Router Model:** Skills act as high-precision semantic routers where 1 keyword maps to exactly 1 nano reference guide.

---

## 2. Standard Sovereign Skill Directory Structure
Every skill in `{engine_root}/skills/<skill_id>/` must strictly adhere to the canonical structure:

```text
skills/<skill_id>/
├── skill.json         # Manifest: metadata, semantic capability, dependencies, exact 20 keywords
├── 00_overview.md     # Domain scope, intent, and architectural pillars (strictly <= 40 lines)
├── performance.md     # Measurable quantitative KPI benchmarks & latency constraints
├── rules.md           # Domain operational invariants & mandatory rules (strictly <= 40 lines)
├── keyword.md         # 1-to-1 mapping: 1 keyword = 1 nano reference file
├── references/        # Nano-modular guides (strictly <= 1,500 characters per file)
│   ├── <topic_a>.md   # Atomic guide containing mandatory reflex to read matching example
│   └── <topic_b>.md
└── example/           # Atomic, split implementation blueprints (0 prompt injection)
    ├── <blueprint_a>  # Concrete implementation templates read on-demand via view_file
    └── <blueprint_b>
```

---

## 3. Skill Activation & Runtime JIT Keyword Interception

### A. Ambient Base Mounting (GUI / Session Activation)
When a skill is enabled via the Flowork Canvas Host or declared in `skills.json`, the Kernel injects **ONLY** the 4 core lightweight assets into the agent's turn prompt:
1. `00_overview.md`
2. `performance.md`
3. `rules.md`
4. `keyword.md`

The contents of `references/` and `example/` remain completely idle on disk (0 tokens overhead).

### B. Just-In-Time (JIT) Keyword Intercept
1. The agent inspects `keyword.md` to identify available specialized domain capability keywords.
2. When the agent uses a registered keyword in planning, reasoning, or `toolAction`, the Kernel's Tool Intercept Gate immediately injects the corresponding file from `references/<topic>.md`.
3. **Mandatory Example Blueprint Reflex:**
   Inside every file in `references/`, there is a strict mandate:
   > *"DO NOT IMPROVISE CODE BEFORE INSPECTING THE OFFICIAL BLUEPRINT! Before implementing or mutating components, you MUST inspect the specific example blueprint in `skills/<skill_id>/example/<target_file>` via `view_file`."*
4. This guarantees zero hallucination, zero prompt bloat, and exact adherence to proven code patterns.

---

## 4. Skill Authoring SOP: GitHub Tri-Repo Synthesis Pipeline
Agents must never hallucinate skills from stale training data. All skill authoring must follow this exact pipeline:

1. **Mandatory GitHub Tri-Repo Research:**
   - The agent MUST search GitHub for at least **3 distinct repositories** covering the target skill domain.
   - **Selection Hierarchy:**
     * *Priority 1:* Trending repositories in the domain.
     * *Priority 2:* Repositories with highest contributors, star count, and positive feedback.
   - **Synthesis Doctrine:** The agent must synthesize the best engineering practices and architectural patterns from all 3 repositories into the Flowork Nano-Modular standard.
2. **Fallback Manual Creation:**
   - If and only if GitHub searches yield zero credible or relevant repositories, the agent may synthesize manually.
   - The agent must state this explicitly and adhere strictly to Flowork OS Constitutions.
3. **Companion Tool Authoring:**
   - If the skill requires automated or programmatic execution, the agent MUST author a companion tool in `{engine_root}/tools/<tool_id>/` and bind it to the skill manifest (`skill.json`).

---

## 5. Hard-Gate Kernel Enforcement & Quality Control (QC)
Compliance is mechanically enforced by Kernel State-Machine Gates:

1. **Gate 1: GitHub Research Lock (Tool Blocker)**:
   Any write operation (`write_to_file`, `replace_file_content`) to `skills/` is rejected if the session has not performed verified GitHub research (minimum 3 repositories accessed via `search_web` or GitHub tools).
2. **Gate 2: Anti-Stop Circuit Breaker & Subagent Audit**:
   - The agent cannot stop or conclude the turn until an independent subagent auditor verifies:
     * `SKILL.md` and `trigger.md` are ABSENT from the skill subfolder.
     * `00_overview.md`, `performance.md`, `rules.md`, and `keyword.md` are present and valid.
     * Every file in `references/` is strictly **<= 1,500 characters** in 100% strict English.
     * `keyword.md` maintains a strict 1-to-1 mapping with `references/`.
     * `example/` contains modular, split implementation blueprints matching references.
     * `00_overview.md` + `rules.md` combined line count is <= 80 lines.
   - Any audit failure forces the agent to refactor and split until achieving **Exit Code 0**.
3. **Gate 3: Autonomous Community Swarm Push**:
   Upon verified Exit Code 0, the skill is committed with `Co-authored-by: Flowork OS <agent@floworkos.com>` and synchronized to the sovereign community repository.
