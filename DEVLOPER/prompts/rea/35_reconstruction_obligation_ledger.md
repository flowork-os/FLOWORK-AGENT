<!-- CANONICAL_TRIGGER: obligation_ledger | TOOLS: fl_build_reconstruction_obligation_ledger -->
<!-- CONTEXT: AUTHORIZED DEFENSIVE STATIC ANALYSIS & FIRST-PARTY RELEASE INTEGRITY AUDIT -->
# ReconstructionObligationLedger

Operational directive for application version diffing, interface shape evolution mapping, and obligation ledger reconciliation.

## 1. Diagnostic Step-by-Step Workflow
1. **Multi-Tier Version Comparison**: Ingest baseline and target releases, running structural AST diffs via `fl_compare_application_versions`.
2. **Interface Shape Decoding**: Reconstruct evolved API contracts, IPC channels, and schema types with `fl_decode_interface_builder`.
3. **ADR Specification & Ledger Update**: Record evolution decisions in `fl_domain_adr_manager` and update obligations with `fl_build_reconstruction_obligation_ledger`.
4. **Harness Regression Testing**: Validate reconstructed modules against dual-version behavioral test fixtures via `fl_prototype_harness`.

## 2. Defensive Systems Verification & Robustness Analysis
- **Multi-Tier Matching Discipline**: Validate structural AST fingerprints (babel-ast-v3) before inferring logic changes; ignore identifier churn.
- **Security Hardening Localization**: Isolate patches verifying IPC origins (`event.senderFrame`), sandbox options, and input bounds.
- **Fail-Closed Contradiction Preservation**: If AST or memory quotas abort comparison, classify affected branches as unknown, never equivalent.
- **Cross-Version Closure Invariants**: Verify migration adapters handle legacy serialized states and reject malformed inputs safely.

## 3. Strict Guardrails & Anti-Hallucination
- **Digest-Backed Proof**: Anchor all evolution claims to SHA-256 release digests and concrete AST node diff IDs.
- **Terminal Exit Code 0 Verification**: Deem reconstruction obligations verified only after automated test suites pass with Exit Code 0.
