---
name: code-graph
description: Standard Operating Procedure for sovereign token-budgeted code graph extraction, AST symbol definition indexing, PageRank repository mapping, and blast radius analysis.
keywords:
  - code_graph
  - repomap
  - token_budget
  - ast_parsing
  - pagerank
  - blast_radius
  - call_hierarchy
  - dependency_graph
  - llm_context
  - memory_bounded
  - secret_shield
  - multi_os
  - cross_reference
  - symbol_table
  - tree_sitter
  - code_intelligence
  - impact_analysis
  - outline_extraction
  - zero_leak
  - reverse_engineering
---

<!-- [FL_INDEX: keywords="code_graph, repomap, ast_parsing, token_budget, pagerank, blast_radius, call_hierarchy, dependency_graph, llm_context, memory_bounded, secret_shield, multi_os, cross_reference, symbol_table, tree_sitter, code_intelligence, impact_analysis, outline_extraction, zero_leak, reverse_engineering" | purpose="SOP and technical documentation for sovereign token-budgeted code graph & repo map engine" ] -->

# 🗺️ CODE GRAPH & REPO MAP ENGINE — OPERATIONAL RUNBOOK (SOP)

## 1. PURPOSE & CAPABILITY
The `code_graph` tool performs token-budgeted static code intelligence, AST symbol extraction, dependency graph construction, and PageRank file ranking across any repository. It allows language models to maintain global architectural awareness within strict context limits.

### Supported Actions:
1. `map` (default): Extracts high-priority files and symbol signatures within strict token budget ceiling.
2. `query`: Searches definitions, classes, functions, and interfaces across the whole graph.
3. `impact`: Calculates blast radius and direct dependents for a file or symbol before modification.
4. `overview`: Fast hierarchical directory overview.

---

## 2. DETERMINISTIC WORKFLOW & EXAMPLES

### CLI Invocation:
```bash
node tools/code_graph/main.mjs map <target_dir> <max_tokens>
```

### JSON Parameters:
```json
{
  "action": "map",
  "target_dir": ".",
  "max_tokens": 1024,
  "depth": 4
}
```

---

## 3. ARCHITECTURAL INVARIANTS
1. **Strict Token Ceiling**: Output actual tokens will NEVER exceed `max_tokens` (`actual <= budget`).
2. **Secret Shield**: Credentials, `.env`, tokens, private keys, and build artifacts are automatically skipped.
3. **RAM Ceiling**: Peak RSS bounded < 50 MB via incremental scanning and size-bounded parsing.
4. **Multi-OS**: Fully path-agnostic with UTF-8 and POSIX path normalization.

---

## 4. CONCRETE VERIFICATION LEDGER
- Validated with exit code 0 across multi-directory trees.
- Zero SAST/SCA security findings (100/100).
- Fully registered in `ANCHOR_TOOLS` and `tool_virtualizer.js`.
