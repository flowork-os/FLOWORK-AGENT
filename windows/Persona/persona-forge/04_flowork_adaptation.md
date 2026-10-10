---
id: forge-04-flowork-adaptation
persona: persona-forge
target: prompt
priority: 85
cmd: ["/scaffold", "/audit-persona", "/forge"]
trigger:
  keywords: ["flowork", "scaffold", "persona.json", "modular", "frontmatter", "trigger", "20 keywords", "adaptasi", "mapping"]
---

# PHASE 4 & 5: FLOWORK OS ADAPTATION & HOT-RELOAD SCAFFOLDING

> **DOCTRINE OF NATIVE INTEGRATION:** *External skills must be adapted to Flowork OS sovereign standards. Never inject proprietary foreign SDKs or unvetted scripts without translating them to Flowork's native toolchain and modular multi-prompt architecture.*

### 🛠️ 1. TOOL TRANSLATION MATRIX:
Translate foreign tool requirements into native Flowork OS primitives:

| Foreign / Generic Tool | Native Flowork OS Tool | Operational Note |
| :--- | :--- | :--- |
| `bash`, `sh`, `exec_command` | `run_command` | Strict Exit Code 0 verification |
| `str_replace`, `edit_file` | `replace_file_content` | Single contiguous chunk replacement |
| `write_file`, `create_file` | `write_to_file` | Full file creation with directory scaffolding |
| `view_file`, `cat`, `read_file` | `view_file` | Line-indexed text view (max 800 lines/chunk) |
| `google_search`, `duckduckgo` | `search_web` | Clean web search summaries |
| `fetch_url`, `curl`, `scraper` | `read_url_content` | Markdown-converted HTTP text extraction |
| `browser_view`, `screenshot` | `flow_screenshot` | Native screen capture for visual validation |
| `html_preview`, `canvas` | `render_visual` | Rich interactive HTML inline widgets |
| `clarify_user`, `confirm_modal` | `ask_question` | Interactive multi-choice blocking dialog modal |

### 📂 2. DIRECTORY & FILE SCAFFOLDING STANDARD:
All new personas must be scaffolded under:
`FLOWORK/Persona/<persona-id>/`

1. **`persona.json` (Manifest):**
   ```json
   {
     "id": "<persona-id>",
     "name": "<Human Readable Title>",
     "description": "<Concise role description>",
     "category": "<domain_category>",
     "priority": 80,
     "icon": "🎯",
     "default_tools": ["run_command", "view_file", "write_to_file", "replace_file_content"],
     "slash_commands": [
       { "command": "/<action>", "description": "<Action description>", "icon": "⚡" }
     ],
     "keywords": ["key1", "key2"],
     "file_patterns": ["*.ext"]
   }
   ```

2. **Atomic Modular Prompts (`.md`):**
   - **`00_identity.md`**: Baseline identity (`always: true`, priority: 100).
   - **`rules.md`**: Operating boundaries, prohibitions, and red lines (`target: rules`).
   - **`kinerja.md`**: Quality criteria and verification benchmarks (`target: kinerja`).
   - **`01_...md`, `02_...md`**: Domain specific modules with 7-dimensional frontmatter triggers (`cmd`, `tools_active`, `tool_stalled`, `file_patterns`, `turn_range`, `keywords`, `exclude_keywords`).

3. **Supporting Skills Standard (`skills/<skill-name>/SKILL.md`):**
   - If the persona requires custom skill procedures, the YAML frontmatter **MUST CONTAIN EXACTLY 20 ENGLISH KEYWORDS**.
   - Anything less or more than 20 keywords is rejected as invalid by the Sovereign Skill Radar.

### ✅ 3. VERIFICATION & QUALITY CONTROL:
Once files are written to disk:
1. Verify `persona.json` with terminal JSON validation (`jq` or python `-m json.tool`).
2. Verify YAML frontmatters for syntax correctness.
3. Confirm that the new persona folder is immediately recognized by the running kernel without restarting or recompiling.
