# Software Company Multi-Agent SOP Operational Rules & Invariants

1. **Document-Driven Handoff:** Agents MUST NEVER pass loose conversation prompts; every phase transition requires structured markdown/JSON deliverables.
2. **Deterministic Role Specialization:** Leader creates PRD & Architecture; Backend/Frontend implement code contracts; Security audits threats; QC verifies with terminal Exit Code 0.
3. **Two-Axis Code Review:** Every code merge requires dual validation: Axis 1 (adherence to PRD & interface contracts) and Axis 2 (code health, depth, and modularity).
4. **Empirical Terminal Proof:** Speculative completion claims are strictly forbidden; all features and bug fixes require automated execution proof with Exit Code 0.
5. **Phase Barrier Enforcement:** Implementation cannot start without an approved PRD & Architecture; deployment cannot occur without passing Security and QC gates.
6. **Multi-OS Portability:** Zero absolute host paths; always resolve workspace paths dynamically via relative paths or environment APIs.
7. **Sanctity of Locks:** Never touch or override blocks guarded by `@lock` or `@frozen`.
8. **Anti-AI Slop & Zero Zombie Code:** Clean all scratch files upon completion; never leave unused imports, dummy mocks, or zombie processes.
