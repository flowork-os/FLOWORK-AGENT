---
name: code_concat
description: Autonomous repository code concatenation, file tree generation, and LLM context formatting runbook.
version: 1.0.0
author: Flowork OS
keywords:
  - code_concat
  - context_packing
  - token_budget
  - llm_prompt_bundling
  - tree_generator
  - source_packer
  - gitignore_compliance
  - zero_api_dependency
  - clean_code
  - static_bundling
---

# 📦 Sovereign Code Concat & Context Packer SOP

## 1. Core Purpose
Allows autonomous agents and human operators to bundle multi-file modules, submodules, or whole repositories into structured context packages for LLMs without leaking sensitive files or requiring third-party API keys.

## 2. Capabilities
- **Zero Third-Party APIs**: 100% local Python execution.
- **Ignore Filtering**: Filters out `.git`, `node_modules`, `__pycache__`, binaries, locks, and media files automatically.
- **Dual Representation**: Supports Markdown codeblocks or XML encapsulation.
- **Accurate Token Estimation**: Returns precise character and estimated token counts to prevent context overflow.

## 3. Operational Command
```bash
python3 tools/code_concat/concat_engine.py <path> <format> <output_path>
```
