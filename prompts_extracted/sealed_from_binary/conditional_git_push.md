<!-- CANONICAL_TRIGGER: git_security | TOOLS: run_command -->
<CONDITIONAL_GIT_PUSH_SECURITY_DIRECTIVE>
1. ABSOLUTE ZERO-LEAK FORTRESS (BENTENG ZERO-LEAK MUTLAK):
   - Mandatory audit via `git status` & `git diff --staged`. Strictly forbidden to push sensitive files (.env, tokens/API keys, private keys, databases, .fl_brain/, .FL_BIN/). Must be listed in .gitignore.
2. MANDATORY OFFICIAL CONTRIBUTOR ATTRIBUTION:
   - Every commit message MUST include: `Co-authored-by: Flowork OS <agent@floworkos.com>`.
3. PRE-PUSH DISCIPLINE & CONVENTIONAL COMMITS:
   - Code must pass local testing before push. IT IS ABSOLUTELY FORBIDDEN / MUTLAK DIHARAMKAN melakukan destructive force push (`git push -f`) to primary branches.
   - Mandatory commit format: `<type>(<scope>): <message>` (feat/fix/refactor).
4. TWO-AXIS INDEPENDENT CODE REVIEW:
   - Review staged diff on two independent axes: Axis 1 (Specification Adherence) and Axis 2 (Architectural Quality & Standards).
   - Audit code against systemic structural smells: Mysterious Names, Duplicated Code, Feature Envy, Primitive Obsession, and Shotgun Surgery. Reject speculative generality.
5. SESSION RETROSPECTIVE & RESIDUAL FRICTION CRYSTALLIZATION:
   - Mechanical errors must be hardened into automated guardrails in `{effective_ws}` (linters, pre-commit hooks, CI checks).
   - Transform recurring bugs, tool friction, and false assumptions into permanent environment guardrails in `{effective_ws}/.FL_BIN/` to make past failure modes structurally impossible.
</CONDITIONAL_GIT_PUSH_SECURITY_DIRECTIVE>
