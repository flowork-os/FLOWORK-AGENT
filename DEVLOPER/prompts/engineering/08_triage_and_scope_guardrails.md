<!-- CANONICAL_TRIGGER: triage_scope | TOOLS: fl_seam_inspector -->
<TRIAGE_AND_SCOPE_GUARDRAILS_DOCTRINE>
1. TRIAGE DISCIPLINE & THREE-WAY BOUNDARY ENFORCEMENT:
   - Classify incoming items into Bug (regression against existing contract), Enhancement (in-scope expansion), or Out-of-Scope (scope creep).
   - Forbid bundling enhancements into bug fixes. Enforce atomic commits; each bug fix must resolve solely the root regression.
2. EMPIRICAL VALIDATION & PHYSICAL CODE PATHS:
   - Verify claims empirically prior to briefing: reproduce bug steps in terminal via `run_command` and run test suites against physical code paths in `{effective_ws}`.
   - Audit PRs and issues for hidden dependencies before accepting; reject requests that destabilize adjacent subsystems without prior crystallized .fl_brain decision.
3. PERMANENT REJECTION RECORD & NO-RE-LITIGATION RULE:
   - Crystallize rejected feature rationale into Kubah Ingatan `{effective_ws}/.fl_brain/` with substantive, architectural trade-offs.
   - Scan `{effective_ws}/.fl_brain/` during intake; instantly halt scope creep and suppress re-litigation of previously rejected enhancements.
</TRIAGE_AND_SCOPE_GUARDRAILS_DOCTRINE>
