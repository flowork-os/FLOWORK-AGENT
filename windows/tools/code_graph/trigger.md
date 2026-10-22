# ⚡ CODE GRAPH & REPO MAP TRIGGER SPECIFICATION

```yaml
trigger_id: tool_code_graph_trigger
target_organ: tools/code_graph
activation_mode: DUAL_WING
priority: 85
positive_keywords:
  - code_graph
  - repomap
  - repo_map
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
negative_exclusions:
  - crypto
  - forex
  - finance
  - trading
actions:
  - mount_tool: tools/code_graph
  - execute: "node tools/code_graph/main.mjs"
```
