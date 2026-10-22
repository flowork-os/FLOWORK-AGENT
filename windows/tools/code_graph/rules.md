# 📜 CODE GRAPH & REPO MAP RULES & OPERATIONAL INVARIANTS

1. **Strict Sub-Ceiling Budget Cap:** Injected repo map token count MUST strictly satisfy `actual_tokens <= max_tokens`. Downward-only truncation; `abs()` overrun formulas are strictly forbidden.
2. **Secret Shield & Zero-Leak AST:** Files matching `*.env*`, `*.secret*`, `*.key*`, `*.pem*`, `*.cert*`, or containing substrings `token`, `password`, or `credential` are unconditionally excluded from the code graph.
3. **RAM Ceiling & Streaming Windowing:** Peak RSS must remain under 200 MB. Repositories exceeding 500 files must be processed via streaming windowing; monolithic in-memory graphs are strictly forbidden.
4. **Multi-OS Separator Independence:** All internal paths must use `path.relative` and normalized POSIX separators (`/`) for cross-platform compatibility across Linux ELF, macOS Mach-O, and Windows PE.
5. **Fail-Soft Circuit Breaker:** In the event of graph ranking OOM or memory pressure, the tool must gracefully degrade to a flat directory hierarchy outline without throwing unhandled exceptions.
6. **Strict English Telemetry:** All output JSON envelopes, status reports, and error messages MUST be formatted in industry-standard English.
