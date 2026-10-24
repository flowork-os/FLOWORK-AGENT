# 📚 FLOWORK OS — SOVEREIGN SKILLS REGISTRY & DUAL-WING SKILL RADAR ARCHITECTURE (`skills/`)

> **Flowork OS Sovereign Doctrine:** *The pure micro-kernel operates as a permanent "Tabula Rasa". All specialized domain expertise, SOPs, and operational runbooks reside 100% outside the compiled binary in the `skills/` directory in a modular, hot-reloadable, and zero-bloat architecture.*  
> **Co-authored-by:** Flowork OS <agent@floworkos.com>

---

## 📌 1. Fundamental Skills Architecture Principles

The `skills/` directory is the authoritative repository of on-demand specialized domain expertise (*Runbooks / SOPs*) across the Flowork OS ecosystem.
Whenever an agent receives a complex domain task (e.g. Reverse Engineering, Web Traffic SEO, Security Auditing, Portability Enforcement):
1. **Mandatory Inspection Reflex (`view_file`):** The agent MUST read `skills/<skill_name>/SKILL.md` using `view_file` prior to executing technical actions.
2. **Anti-Hallucination & Zero Trial-Error:** Agents are strictly forbidden from guessing complex workflows; execution must adhere to official runbooks.
3. **Mandatory Pinned Skill (Tier 1-4):** Agents must mount (*pin*) the relevant skill into the active session via `skill_control(action: "pin", skill_id: "...")` before executing specialized tasks.

---

## 🎯 2. Standard YAML Frontmatter Specification: Exact 20 English Keywords

Every `SKILL.md` file MUST feature a strict YAML Frontmatter block at the very top:

```yaml
---
name: "Web Traffic & SEO Specialist"
description: "Standard operating procedure for web traffic analysis, technical SEO auditing, search engine indexation footprinting, backlink discovery, and Core Web Vitals profiling."
keywords: ["seo","traffic","backlinks","ranking","indexing","analytics","sitemap","robots","serp","keywords","performance","lighthouse","crawling","canonical","open_graph","schema_org","json_ld","ttfb","core_web_vitals","pageviews"]
exclude_keywords: ["youtube.com", "youtube,com", "youtube", "youtu.be", "yt spy"]
provenance: "Engineered under 4-Tier Sovereign Acquisition Hierarchy. Verified with Exit Code 0 proof."
---
```

### Sovereign Standards & Authoring Rules:
1. **MANDATORY EXACT 20 ENGLISH KEYWORDS (`keywords`):**
   - The `keywords` field MUST contain **EXACTLY 20 KEYWORDS** in formal English.
   - Any skill with fewer than 20 or more than 20 keywords is considered **DEFECTIVE (INVALID)** and will be rejected by the *Preflight Gatekeeper*, `skill_control`, and the *Runtime Skill Radar*!
2. **MANDATORY ENGLISH FOR KEYWORDS & EXCLUSIONS:**
   - All keywords (`keywords`), exclusion keywords (`exclude_keywords`), name (`name`), and description (`description`) must be 100% formal English. Non-English terms are strictly banned.
3. **MANDATORY STRICT ENGLISH BODY CONTENT:**
   - **Iron Law of Skill Creation:** Both the frontmatter keywords and all content/body text of `SKILL.md` MUST be 100% strict English.
   - All sections (Overview, Standard Execution Flow, Edge Cases & Recovery, Empirical QC Exit Code 0), operational instructions, and command examples in `SKILL.md` MUST have Zero Indonesian Markers.
   - Flowork OS demands global portability without regional language bias so modules can be executed universally by any model and runtime worldwide.

---

## ⚡ 3. Dual-Wing Skill Radar Architecture (Keywords & Negative Exclude)

To prevent **Skill Collision** and **Context Bloat**, the *Sovereign Skill Radar* (`core/src/trigger.rs`) evaluates incoming intent through a **Dual-Wing Architecture**:

```
                              ┌────────────────────────────────────────┐
                              │       INTENT / QUERY KEYWORDS          │
                              │    (e.g., "youtube,com" / "seo")       │
                              └───────────────────┬────────────────────┘
                                                  │
                               [Case-Insensitive Substring Scan]
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
               [Negative Exclusion Wing]                         [Positive Keyword Wing]
                `query_lower.contains(&ex)`                       `query_lower.contains(&kw)`
                         │                                                 │
              Does query contain exclude?                       Does query contain keyword?
              (e.g., "youtube" on SEO skill)                    (e.g., "traffic" or "ranking")
                         │                                                 │
                 ┌───────┴───────┐                                 ┌───────┴───────┐
                 │ YES           │ NO                              │ YES           │ NO
                 ▼               ▼                                 ▼               ▼
            [DISQUALIFIED]   [Pass to Positive]                [RECOMMENDED]   [PASS / IGNORE]
             Score = -1000   (Calculate Score)                 (Top-3 Radar    (Score 0 / Skip)
            (Short-Circuit)                                     Banner HUD)
```

### A. Substring Contains Matching Principle
Keyword matching operates via **case-insensitive substring contains** (`query.to_lowercase().contains(&kw)`):
* **Why Substring?**
  - **URLs & TLDs:** Domain queries like `example.com` match keyword `.com` or `domain`.
  - **Typo Tolerance:** Inputs like `youtube,com` (comma instead of period) are matched accurately by substring `youtube`.
  - **Sub-paths:** `watch?v=`, `shorts/`, or `@handle` match instantly without fragile regex.

### B. Short-Circuit Negative Rejection
Exclusion checks are evaluated **FIRST** before positive scores are calculated:
```rust
// 0. EXCLUSION CHECK (Short-circuit): Substring matching
let exclude_vals = skill.get("exclude_keywords")
    .or_else(|| skill.get("exclude"))
    .or_else(|| skill.get("excludes"));
if let Some(arr) = exclude_vals.and_then(|v| v.as_array()) {
    for ex in arr {
        if let Some(ex_str) = ex.as_str() {
            let ex_clean = ex_str.trim().to_lowercase();
            if !ex_clean.is_empty() && query_lower.contains(&ex_clean) {
                return -1000; // IMMEDIATE DISQUALIFICATION!
            }
        }
    }
}
```
If an exclusion matches, the score drops immediately to `-1000`, disqualifying the skill.

### C. Collision Avoidance Matrix Example:
* **Web Traffic SEO vs. YouTube Intelligence:**
  - `web_traffic_seo_auditor`: Contains keywords `seo`, `traffic`, `ranking`, `domain`. Adds `exclude_keywords: ["youtube.com", "youtube,com", "youtube", "youtu.be"]`.
  - When user requests traffic analysis for `example.com`: SEO skill is recommended.
  - When user requests `youtube.com/watch?v=123` or `youtube,com`: SEO skill is **INSTANTLY DISQUALIFIED**, yielding to specialized YouTube tools (`youtube_spy_*`).

---

## 📂 4. Canonical Modular Skill Folder Structure

Each skill resides inside its dedicated directory:

```text
skills/
└── <skill-name>/
    ├── SKILL.md       # (Mandatory) 20 keywords YAML frontmatter + complete SOP
    ├── scripts/       # (Optional) Helper scripts / automation tooling
    ├── templates/     # (Optional) Code templates or schema files
    └── resources/     # (Optional) Reference data, offline databases, dictionaries
```

---

## 🏛️ 5. 4-Tier Sovereign Acquisition Hierarchy & Pinned Skill Lifecycle

1. **Tier 1 (Local Workspace / Installed Skills):** Highest priority. Radar scans the local `skills/` directory first.
2. **Tier 2 (Official Flowork OS Registry):** Scans official catalog `flowork-os/FLOWORK-SKILLS` if local matches are fewer than 3.
3. **Tier 3 (Model Context Protocol / Community):** Adapts external MCP skills.
4. **Tier 4 (Zero-Precedent Sovereign Crafting):** If no matching skill exists, the agent authors a new skill from scratch with exact 20 English keywords via `skill_control(action: 'create')`.

### Pinned Skill Lifecycle Rules:
* Agents inspect skills via `view_file` prior to pinning.
* Mount active skills via `skill_control(action: "pin", skill_id: "<id>")`.
* Once pinned, the skill SOP is dynamically injected into `<PINNED_ACTIVE_SKILL>` on subsequent turns.
* Upon completion, agents unpin the skill via `skill_control(action: "unpin")`.

---

## 🚀 6. Mandatory Contribution to Official GitHub Registry (Exit Code 0)

Whenever an agent creates or refactors a new skill:
1. **Empirical Verification (Exit Code 0):** Agents must execute and verify all scripts, SOPs, and commands to prove Exit Code 0 success.
2. **Mandatory Upload to Official Registry:** Publish verified skills to `flowork-os/FLOWORK-SKILLS`:
   ```bash
   skill_control(action: "publish", skill_id: "<skill_name>", notes: "feat: add <skill_name> sovereign runbook")
   ```
3. **Sovereign Community Growth:** Flowork OS is an evolving global operating system. Hoarding tested modules violates sovereign growth.
4. **Attestation Guard Fortress (Hash Integrity):** Kernel validates SHA-256 hashes against `release_checksums.json`. Tampered or invalid hashes abort uploads immediately.

---

## 🔄 7. Autonomous Kernel Self-Healing

This governance document (`skills/README.md`) is protected within the **Cryptographic Bytecode Enclave** of the `x-flow` kernel binary:
* **Fresh Installations:** The binary reconstitutes `skills/README.md` if the `skills/` folder lacks it.
* **Accidental Deletions:** If removed by users or external processes, the `x-flow` kernel detects the absence during turn evaluation and reconstitutes the file instantly from the enclave without restarts or downloads.
