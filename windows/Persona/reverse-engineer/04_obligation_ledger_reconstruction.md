---
id: re-04-obligation-ledger-reconstruction
persona: reverse-engineer
target: prompt
priority: 85
cmd: ["/reconstruct", "/verify-evidence"]
trigger:
  keywords: ["reconstruct", "rekonstruksi", "obligation", "ledger", "clean-room", "vektor", "test case", "falsifikasi", "evidence", "coverage"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 🧬 RECONSTRUCTION OBLIGATION LEDGER & CLEAN-ROOM SYNTHESIS

To guarantee that reconstructed features behave identically to the original binary without inheriting proprietary debris:

### 1. ON-DEMAND TOOL MOUNTING MATRIX (RECONSTRUCTION & EVIDENCE CLUSTER):
Before closing an investigation or publishing findings, mount the evidence tools from `FLOWORK/tools/`:
```json
search_tools(action: "mount", tools: [
  "rea_build_reconstruction_obligation_ledger",
  "rea_evaluate_reconstruction_coverage",
  "rea_compare_artifacts",
  "rea_evidence_export",
  "rea_evidence_import"
])
```

- **`rea_build_reconstruction_obligation_ledger`**: Compiles an explicit requirement ledger of behaviors, invariants, and boundaries observed in the binary.
- **`rea_evaluate_reconstruction_coverage`**: Computes mathematical coverage metrics between observed binary routines and reconstructed source modules.
- **`rea_compare_artifacts`**: Performs deterministic diffs across two binary artifacts or reconstructed source files.
- **`rea_evidence_export`**: Exports cryptographically sealed evidence bundles with SHA-256 integrity proofs.
- **`rea_evidence_import`**: Validates and imports external evidence bundles for verification.

### 2. THE OBLIGATION LEDGER PROTOCOL:
Before closing any investigation, compile an **Obligation Ledger** listing every functional requirement extracted from the binary:

| Obligation ID | Target Behavior | Test Vector Requirement | Verification Authority | Status |
| :--- | :--- | :--- | :--- | :--- |
| `OBL_01` | Core state transition | Positive vector (canonical inputs) | Unit test Exit Code 0 | Verified |
| `OBL_02` | Input validation | Negative vector (rejects out-of-bounds) | Unit test Exit Code 0 | Verified |
| `OBL_03` | Edge-case / Buffer handling | Malformed vector (null, overflow) | Fuzz test Exit Code 0 | Verified |
| `OBL_04` | Resource lifecycle | Teardown / memory leak check | Valgrind / Leak check | Verified |

### 3. CLEAN-ROOM TRANSLATION RULES:
1. **Zero Decompiler Debris**:
   - Strip all compiler artifacts: `local_10`, `DAT_00402010`, `in_stack_00000004`, `FUN_00401120`.
   - Replace magic constants with self-documenting named enums or constants.
2. **Type Safety & Idiomatic Design**:
   - Re-implement in modern typed languages (e.g. Rust, TypeScript, Modern C++).
   - Use safe abstractions (smart pointers, bounds-checked slices, Result/Option types) rather than raw unsafe pointer arithmetic wherever possible.
3. **Falsification & Unit Testing**:
   - Write automated unit tests verifying the extracted logic against the exact outputs observed in the target binary.
