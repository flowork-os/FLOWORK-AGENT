---
name: code_concat
description: High-performance repository and directory packer for LLMs. Concatenates code, computes token counts, respects gitignore, and structures context with XML/Markdown formatting without third-party APIs.
version: 1.0.0
keywords:
  - code_concat
  - context_packer
  - token_counter
  - llm_context
  - repository_tree
  - gitignore_filter
  - markdown_context
  - xml_context
  - prompt_engineering
  - zero_third_party_api
---

# Code Concat Tool Specification (Flowork OS)

## Overview
Adopted natively from jub0t/concat. Concatenates codebases into clean LLM-ready bundles with estimated token counts and file tree hierarchies, executing 100% locally with zero external API dependencies.

## Usage
Run via Python entrypoint:
`python3 tools/code_concat/concat_engine.py <target_path> [markdown|xml] [output_file]`
