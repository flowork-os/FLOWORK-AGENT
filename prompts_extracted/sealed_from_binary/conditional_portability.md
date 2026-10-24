<!-- CANONICAL_TRIGGER: portability | TOOLS: audit_security, flow_lock -->
<CONDITIONAL_PORTABILITY_AND_NANO_MODULAR_DIRECTIVE>
1. ANTI-HARDCODED PATH & MULTI-OS PORTABILITY:
   - Absolute host paths (`/home/...`, `C:\...`, `/Users/...`, usernames) are strictly forbidden. Use dynamic relative APIs (PathBuf, path.join, process.cwd, PWD) and dynamic path separators with UTF-8 LF (`\n`). Verify zero hardcodes via `audit_security`.
2. 4 PILAR NANO-MODULAR FLOWORK OS:
   - Pillar 1 (Agnostic Manifest): Governed strictly by manifest contracts (`manifest.json`, `agent.json`, `SKILL.md`).
   - Pillar 2 (Plug & Play): Loose coupling; mount/unmount safely without engine disruption.
   - Pillar 3 (1 File 1 Logic & 20-80 LOC): Highly focused, ideal 20-80 lines (max 120 lines). Zero monolithic god-files.
   - Pillar 4 (Zero Residue Sandbox): All temporary files/scratches MUST reside in `{effective_ws}/.FL_BIN/scratch/` and be cleaned up.
3. ENGINEERING HYGIENE & SHALLOW STACKS:
   - Boy Scout Principle: Leave code cleaner than found. Eliminate zombie code, trivial echo comments, and decorative banners. Comments explain non-obvious *why*, not *what* (max 1-2 lines).
   - Shallow indirection: Max 3 layers of indirection for business logic. Forbid circular dependencies.
   - Deep modules: Maximize capability behind minimal interface surface.
4. MANDATORY FL_INDEX TAGGING:
   - Every created or modified file MUST embed a top-level semantic tag: `[FL_INDEX: keywords="..." | purpose="..."]` with at least 3-5 technical keywords.
</CONDITIONAL_PORTABILITY_AND_NANO_MODULAR_DIRECTIVE>
