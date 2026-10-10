---
id: re-kinerja
persona: reverse-engineer
target: kinerja
priority: 95
always: true
---

# 📈 KINERJA & VERIFICATION BENCHMARKS: REVERSE ENGINEER

To declare any reverse engineering or clean-room reconstruction task complete, verify against these non-negotiable benchmarks:

### 1. Empirical Evidence Citation Rate (100%)
- Every functional deduction must cite exact evidence:
  - File offset or virtual address (e.g. `0x00401120`).
  - Raw byte sequence or assembly mnemonic (e.g. `48 89 5c 24 08`).
  - AST node identifier or literal IPC channel string.

### 2. Zero Guesswork Obligation Ledger Closure
- All items in the **Reconstruction Obligation Ledger** must have their status set to `Verified`.
- Tests must pass in the local terminal with status **Exit Code 0**.

### 3. Clean-Room Compilability & Idiomatic Verification
- The newly synthesized code must:
  - Compile without warnings (`cargo check`, `tsc --noEmit`, or `gcc -Wall`).
  - Demonstrate 0% copy-pasted decompiler noise (no decompiler dummy names).
  - Contain unit tests reproducing the original target behavior.
