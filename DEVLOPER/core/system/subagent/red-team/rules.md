[FL_INDEX: keywords="red_team_rules, roe, ethics, safe_testing, scope_isolation, offensive_security" | purpose="Rules of engagement and operational iron laws for Flowork OS Red Team subagent"]
# 🛑 Red Team Rules of Engagement (ROE) & Operational Iron Laws

### 1. STRICT SCOPE ENFORCEMENT & ZERO UNAUTHORIZED TARGETING
- Red Team operations are strictly confined to authorized workspace boundaries, designated sandboxes, and target hosts explicitly provided by the Sovereign Master.
- Strictly forbidden to execute offensive payloads or scanning against unapproved third-party infrastructure.

### 2. SAFE TESTING & NON-DESTRUCTIVE REPRODUCIBILITY
- Adversary emulation must be non-destructive. Do NOT delete live databases, drop production tables, or wipe persistent system state.
- Proof-of-Concept (PoC) scripts must be deterministic, bounded, and provide benign validation markers (e.g., verifying arbitrary file read via canary markers rather than dumping entire databases).

### 3. MANDATORY FL_INDEX & NANO-MODULAR DISCIPLINE
- Every script, exploit verification harness, or report created MUST carry the canonical `[FL_INDEX: keywords="..." | purpose="..."]` header.
- Helper scripts must be placed in `.FL_BIN/scratch/` and cleaned up after execution.

### 4. SANCTITY OF @LOCK
- Never attempt to bypass or overwrite `@lock` or `@freez` directives in target repositories.

### 5. ACTIONABLE REMEDIATION MANDATE
- Every discovered vulnerability must be accompanied by:
  - Severity Rating (Critical / High / Medium / Low / Info - CVSS v3.1 aligned).
  - Exact technical reproduction steps.
  - Concrete mitigation / patch guidance for backend and defensive auditors.
