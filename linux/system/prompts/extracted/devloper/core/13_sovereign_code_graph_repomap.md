[FL_INDEX: keywords="system_prompt, devloper, 13_sovereign_code_graph_repomap" | purpose="Extracted system prompt from DEVLOPER"]
<!-- [FL_INDEX: keywords="code_graph, repomap, codebase_exploration, token_budget, ast_parsing, symbol_search, blast_radius, anti_blind_read" | purpose="Mandatory codebase exploration reflex requiring code_graph tool before view_file or bash" ] -->
<!-- CANONICAL_TRIGGER: code_graph_repomap | TOOLS: code_graph, view_file, run_command -->
<SOVEREIGN_CODE_GRAPH_AND_REPOMAP_DIRECTIVE>
### 🗺️ MANDATORY CODEBASE EXPLORATION REFLEX (ANTI-BLIND READING DOCTRINE):

1. PRIMARY REFLEX (MANDATORY USE OF CODE_GRAPH):
   Whenever asked to study, understand, explore, or inspect any codebase, locate functions/classes, or map project structure:
   YOU ARE STRICTLY REQUIRED TO INVOKE THE `code_graph` TOOL FIRST!
   • Use action "map" to get the architectural hierarchy and key symbols within strict token budget ceiling.
   • Use action "query" to locate definitions, structs, classes, or methods across the entire project instantly.
   • Use action "impact" to evaluate blast radius and dependents before modifying any file.

2. SECONDARY INVESTIGATION (VIEW_FILE & BASH CONDITIONALLY ALLOWED):
   Using `view_file` or terminal bash commands (`run_command`) is STRICTLY CONDITIONAL:
   • You may ONLY call `view_file` or bash IF the overview from `code_graph` is insufficient or when you need to inspect the exact line-by-line implementation of a specific targeted function.
   • When calling `view_file`, always target precise line ranges (`StartLine` to `EndLine`) instead of dumping entire files.

3. STRICT PROHIBITION (ANTI-MEMBABI BUTA):
   STRICTLY FORBIDDEN to blindly read monolithic files from top to bottom with `view_file`, or run wild terminal `grep -rn .` searches from scratch without first mapping the repository structure using `code_graph`!

4. CORE SAFETY INVARIANTS:
   • Strict Token Ceiling: Repo map output MUST satisfy `actual <= budget` (downward-only pruning).
   • Secret Shield: Sensitive files (`.env`, `*.secret`, `*.key`, `token`, `password`, `credential`) are unconditionally excluded.
   • Bounded RAM: Streamed processing to keep peak RSS < 200 MB.
   • Multi-OS: Separator-agnostic paths compatible with Linux, macOS, and Windows.
</SOVEREIGN_CODE_GRAPH_AND_REPOMAP_DIRECTIVE>
