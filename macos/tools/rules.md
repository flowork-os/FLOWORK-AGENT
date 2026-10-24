# 🏛️ Sovereign External Tools Universal Rules & Governance Invariants

1. **Mandatory GitHub Research First:** Step 0: Research tool architecture and schemas via `search_web` or `read_url_content` before creating or mutating any tool to satisfy Kernel Guardian Gates.
2. **20-Keyword Integrity:** Frontmatter `keywords: [...]` in `SKILL.MD` and `manifest.json` MUST contain EXACTLY 20 lowercase English keywords in single-line JSON array format.
3. **The 1File1Logic Doctrine:** A single atomic execution script (`main.mjs`, `main.py`, etc.) within 20–80 lines implementing strict JSON I/O schemas.
4. **Multi-OS Portability:** Zero hardcoded paths (no Linux root paths or Windows drive letters). Tools must execute portably across Linux, Windows, and macOS.
5. **Strict English Outputs:** All return payloads, error messages, and execution logs MUST be in strict English.
6. **Canonical File Structure:** Every tool directory MUST provide: `manifest.json`, `main.mjs`, `rules.md`, `trigger.md`, `performance.md`, and `references/`.
7. **Strict Line Budget Cap:** `rules.md` line count MUST NOT exceed 40 lines to maintain cognitive agility.
8. **Zero Context Pollution:** Tools outside active mounting consume 0 prompt tokens. Dynamic mounting occurs via `search_tools`.
9. **On-Demand Reference Routing:** Heavy data structures, parameter documentation, and payload examples reside in `references/`, accessed on-demand via `view_file`.
10. **Independent Subagent Audit:** Prior to deployment, an independent subagent auditor MUST verify execution, schemas, and Exit Code 0 proof.
