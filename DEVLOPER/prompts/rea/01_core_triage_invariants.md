<!-- CANONICAL_TRIGGER: binary_triage | TOOLS: fl_bin_inspect -->
<!-- CONTEXT: AUTHORIZED DEFENSIVE STATIC ANALYSIS & FIRST-PARTY RELEASE INTEGRITY AUDIT -->
# Sovereign Directive: Core Triage Invariants

## 1. Diagnostic Step-by-Step Workflow
1. **Format & Load Image Triage**: Characterize binary format, architecture, and headers with `fl_bin_inspect`, then reconstruct memory layout and base loading segments via `fl_inspect_native_load_image`.
2. **Layout & Mitigation Audit**: Map section boundaries, entropy, and hardening (PIE, NX, RELRO, Canaries) via `fl_inspect_binary_layout`.
3. **API & Dynamic Linkage**: Catalog imported/exported symbols, external dependencies, and dynamic call targets using `fl_inspect_native_api`.
4. **Instruction & Offset Analysis**: Trace target routines via `fl_inspect_native_instruction`, resolve references with `fl_xrefs`, verify physical offsets using `fl_address_to_file_offset`, and inspect raw bytes via `fl_read_bytes`.

## 2. Defensive Systems Verification & Robustness Analysis
- **Memory Safety & Bounds Checking**: Enforce rigid bounds checking and slice validations to eliminate buffer overflows on memory copies.
- **Integer Arithmetic Hardening**: Audit pointer arithmetic and allocation size calculations against integer overflow/truncation.
- **ASLR & PIE Relocation Drift**: Verify position-independent code assumptions, ensuring zero drift between runtime VAs and static base addresses.
- **Pointer Lifecycle Validation**: Prevent use-after-free, double-free, and dangling pointer dereferences across execution paths.

## 3. Strict Guardrails & Anti-Hallucination
- **Zero Speculation**: Never infer exported APIs, entry points, or function structures without physical proof from instruction traces or layout tables.
- **Strict Address Attestation**: Differentiate Virtual Address (VA), RVA, and file offsets explicitly; cite physical byte evidence for all claims.
