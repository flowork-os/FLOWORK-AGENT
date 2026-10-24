# 🛠️ FLOWORK OS — DYNAMIC EXTERNAL TOOLS REGISTRY & DUAL-WING MANIFEST SPECIFICATION (`tools/`)

> **Flowork OS Sovereign Doctrine:** *The pure micro-kernel operates as a permanent "Tabula Rasa". All external tools operate as independent nano-plugs outside the compiled binary within the `tools/` directory, communicating strictly via Manifest JSON contracts and standard stdin/stdout, mountable dynamically on-demand.*  
> **Co-authored-by:** Flowork OS <agent@floworkos.com>

---

## 📌 1. Fundamental External Tools Architecture Principles

The `tools/` directory serves as the expansion gateway for autonomous tools outside the immutable blackbox binary:
1. **Dynamic Tool Mounting (Anchor vs. Session Tools):**
   - **Anchor Tools:** Permanent core tools always available across all sessions (`run_command`, `view_file`, `write_to_file`, `replace_file_content`, `ask_question`, `search_tools`, etc.).
   - **Dynamic Modular Tools:** All tools residing in `tools/<tool_name>/` operate on-demand. They are discovered via `search_tools(action: 'search')` and mounted to the active session via `search_tools(action: 'mount', tools: ['<tool_name>'])`.
2. **Zero Context Bloat (Anti-Bloat Prompt):**
   - Only explicitly mounted tools are injected into the LLM function declaration schema, preserving token context budgets.
3. **Nano-Plug Standard (1 Folder 1 Tool):**
   - Every tool is fully isolated in its own folder (`tools/<tool_name>/`) with its self-contained entrypoint (Node.js `.mjs`, Python `.py`, Shell `.sh`, or standalone binary).

---

## ⚙️ 2. Standard Manifest Contract Specification (`manifest.json`)

Every tool in `tools/<tool_name>/` **MUST** include an OpenAPI Object Schema-compliant `manifest.json`:

```json
{
  "name": "website_intelligence",
  "category": "osint",
  "description": "Target website intelligence extraction: monthly traffic estimation, global and country rankings, traffic channel distribution (SimilarWeb), web archive snapshot history (Wayback Machine CDX), and on-page technical SEO health (Meta tags, OpenGraph, Canonical, Headings, Robots.txt).",
  "command": "node tools/website_intelligence/main.mjs",
  "entry": "main.mjs",
  "author": "Flowork Sovereign Core",
  "version": "1.0.0",
  "keywords": [
    ".com",
    ".net",
    ".org",
    "website",
    "domain",
    "url",
    "traffic",
    "ranking",
    "seo",
    "web intelligence",
    "website_intelligence"
  ],
  "exclude_keywords": [
    "youtube.com",
    "youtube,com",
    "youtube",
    "youtu.be"
  ],
  "tags": [
    "website_intelligence",
    "osint",
    "flowork",
    "modular",
    "zero_corner",
    "nano_plug"
  ],
  "ui": {
    "css": "style.css",
    "zero_corner": true,
    "theme": "cyber_matrix"
  },
  "parameters": {
    "domain": {
      "description": "Target domain or website URL to analyze (e.g. 'apple.com', 'tokopedia.com').",
      "type": "STRING"
    },
    "keywords": {
      "description": "Mandatory on the first tool call of a turn: Comma-separated technical domain keywords in English. Used by Sovereign Skill Radar to recommend candidates for optional pinning.",
      "type": "STRING"
    },
    "reason": {
      "description": "MANDATORY ON EVERY TOOL CALL: Clear, concise technical rationale in English explaining WHY you are calling this tool right now and what specific action it performs.",
      "type": "STRING"
    }
  }
}
```

---

## 🎯 3. Dual-Wing Trigger Architecture (Positive Keywords & Negative Exclude)

To prevent **Tool Collision**, all external tool manifests enforce the **Dual-Wing Architecture**:

```
                              ┌────────────────────────────────────────┐
                              │         SEARCH INTENT / QUERY          │
                              │    (e.g., "youtube,com" / ".com")      │
                              └───────────────────┬────────────────────┘
                                                  │
                               [Case-Insensitive Substring Scan]
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
               [Negative Exclusion Wing]                         [Positive Keyword Wing]
              `query_lower.contains(&ex)`                       `query_lower.contains(&kw)`
                         │                                                 │
              Does query match exclusion?                       Does query match keyword?
              (e.g. "youtube" on web intel)                     (e.g. ".com" or "traffic")
                         │                                                 │
                 ┌───────┴───────┐                                 ┌───────┴───────┐
                 │ YES           │ NO                              │ YES           │ NO
                 ▼               ▼                                 ▼               ▼
            [DISQUALIFIED]   [Pass to Positive]                [MATCHED / FOUND]   [IGNORE]
            (Short-Circuit)  (Check Keyword Matches)           (Included in Search (Skip)
            Tool Dropped                                        Results)
```

### A. Substring Contains Matching Principle
The tool catalog search engine (`core/src/tools.rs` -> `execute_flow_search_tools`) uses **case-insensitive substring contains**:
* **URL & Full Domain Matching:** An input like `https://example.com/api` triggers tools with keyword `.com` or `domain`.
* **Typo Tolerance:** Inputs like `youtube,com` (with comma) still match keyword `youtube` while actively excluding generic tools like `website_intelligence`.
* **Deep URL Paths:** Segments like `watch?v=` or `channel/` are matched without fragile regular expressions.

### B. Short-Circuit Exclusion Evaluation
Negative exclusions are evaluated **BEFORE** keyword text matching:
```rust
// 0. EXCLUSION CHECK (Short-circuit): Substring matching
// If query contains any of tool's exclude_keywords, disqualify immediately!
if !query_lower.is_empty() {
    if let Some(ex_arr) = t.get("exclude_keywords").or_else(|| t.get("exclude")).and_then(|v| v.as_array()) {
        for ex in ex_arr {
            if let Some(ex_str) = ex.as_str() {
                let ex_clean = ex_str.trim().to_lowercase();
                if !ex_clean.is_empty() && query_lower.contains(&ex_clean) {
                    return false; // Tool dropped immediately!
                }
            }
        }
    }
}
```

### C. Collision Avoidance Matrix Example:
* **Web Recon (`website_intelligence`) vs. YouTube Spy (`youtube_spy_video`):**
  - `website_intelligence` keywords: `[".com", ".net", ".org", "website", "domain", "traffic", "ranking"]`.
  - `website_intelligence` excludes: `["youtube.com", "youtube,com", "youtube", "youtu.be"]`.
  - `youtube_spy_video` keywords: `["youtube", "youtu.be", "youtube.com", "youtube,com", "video deepscan"]`.
  - **Evaluation Outcomes:**
    | Query Input | `website_intelligence` | `youtube_spy_video` | Recommended Tool |
    | :--- | :--- | :--- | :--- |
    | `"check traffic for example.com"` | ✅ Matched (`.com`) | ❌ Unmatched | **`website_intelligence`** |
    | `"open url https://youtube.com/watch?v=123"` | 🛑 **Excluded** | ✅ Matched (`youtube`) | **`youtube_spy_video`** |
    | `"analyze this youtube,com channel"` | 🛑 **Excluded** | ✅ Matched (`youtube`) | **`youtube_spy_video`** |

---

## 🔒 4. Mandatory Intercept Gate Schema (`reason` & `keywords`)

Every external tool resolved by Flowork OS is automatically injected with the Intercept Gate parameters:
1. **`reason` (MANDATORY ON EVERY CALL):** Concise technical rationale in English explaining WHY this tool is being invoked and what specific action it performs.
2. **`keywords` (MANDATORY ON FIRST CALL OF TURN):** Technical English domain keywords used by the *Sovereign Skill Radar* to recommend relevant skills.

---

## 🔍 5. Discovery, Mounting & Unmounting Workflow (`search_tools`)

```bash
# 1. Search tool catalog by keywords:
search_tools(action: "search", query: "traffic .com")

# 2. Mount tool to active session (available on subsequent turns):
search_tools(action: "mount", tools: ["website_intelligence", "web_security_audit"])

# 3. Unmount tool after task completion to conserve token budget:
search_tools(action: "unmount", tools: ["website_intelligence"])

# 4. Search remote tools in official Flowork OS registry (flowork-os/AGENT-TOOLS):
search_tools(action: "search_remote", query: "docker")
```

---

## 🛡️ 6. Quality Standards & Preflight Gatekeeper Audit

Before an external tool is approved or released:
1. **Strict English Mandate (100%):** All `description`, parameter explanations, `keywords`, and `exclude_keywords` MUST be in formal English.
2. **Authoritative Runbook `SKILL.md`:** If accompanied by a `SKILL.md`, both frontmatter and body text must be 100% formal English (Zero Indonesian Markers).
3. **Multi-OS Portability (`detect_hardcode`):**
   - Must contain zero absolute host paths (`/home/...`, `C:\...`, `/root/...`).
   - Must pass `detect_hardcode(target_dir: "tools/<tool_name>")` with **Exit Code 0**.

---

## 🚀 7. Mandatory Contribution to Official GitHub Registry (`flowork-os/AGENT-TOOLS`)

Whenever an agent engineers or refactors an external tool:
1. **Empirical Verification (Exit Code 0):** The tool must be verified via terminal CLI and return valid JSON (Exit Code 0).
2. **Mandatory Upload to Official Registry:** Publish verified tools to `flowork-os/AGENT-TOOLS`:
   ```bash
   search_tools(action: "publish", tool_id: "<tool_name>", notes: "feat: add <tool_name> modular nano-plug")
   ```
3. **Attestation Guard Fortress (Hash Integrity):** Kernel validates SHA-256 binary and core UI hashes against GitHub `release_checksums.json`. Tampered hashes immediately abort uploads.

---

## 🔄 8. Autonomous Kernel Self-Healing

This specification guide (`tools/README.md`) is protected within the **Cryptographic Bytecode Enclave** of the `x-flow` kernel binary:
* **Fresh Installations:** The binary reconstitutes `tools/README.md` when the `tools/` directory is initialized.
* **Accidental Deletions:** If removed by users or external processes, the `x-flow` kernel detects the absence during turn evaluation and reconstitutes the file instantly from the enclave.
