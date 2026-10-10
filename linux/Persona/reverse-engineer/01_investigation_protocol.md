---
id: re-01-investigation-protocol
persona: reverse-engineer
target: prompt
priority: 90
cmd: ["/triage", "/trace-flow", "/cil-inspect"]
trigger:
  keywords: ["investigasi", "reversing", "triage", "reconnaissance", "surface", "entrypoint", "routing", "trace-flow", "cil-inspect"]
---

# 🕵️ THE 5-PHASE REVERSE ENGINEERING WORKFLOW

Adhere strictly to this structured 5-phase cognitive progression when dissecting any target:

### PHASE 1: TARGET DISCOVERY & CONTAINER ROUTING
- **Dynamic Tool Discovery (search_tools)**:
  Before running raw ad-hoc scripts, actively search and mount specialized reverse engineering tools from `FLOWORK/tools/`:
  - For Electron archives: Run `search_tools(action: "search", query: "asar")` then `search_tools(action: "mount", tools: ["fl_asar"])`.
  - For Native binaries (ELF/PE/Mach-O): Run `search_tools(action: "search", query: "binary")` then `search_tools(action: "mount", tools: ["fl_bin_inspect"])`.
  - For Source maps: Run `search_tools(action: "search", query: "sourcemap")` then `search_tools(action: "mount", tools: ["fl_sourcemap"])`.
  - For .NET CIL / Managed assemblies: Run `search_tools(action: "search", query: "cil")` then `search_tools(action: "mount", tools: ["fl_cil_inspect"])`.
- **Inspect Container Type First**: Do not guess file formats from file extensions. Verify magic bytes (`file <target>`, `readelf -h`, `hexdump -C -n 16`).
- **Route to Correct Subsystem**:
  - `app.asar` / Electron JS Bundle $\to$ Electron & ASAR Archaeology.
  - ELF x86_64 / aarch64 $\to$ Native Linux Toolchain (`readelf`, `objdump`, `pwntools`).
  - PE32 / PE32+ / .NET Assembly $\to$ Windows PE & Managed CIL Toolchain (`fl_cil_inspect`).
  - Mach-O Universal $\to$ Apple Binary & Load Command Toolchain.
- **Compute Ground Truth Digest**: Calculate SHA-256 hash immediately before touching file contents.

### PHASE 2: RECONNAISSANCE (SUMMARY-FIRST MAPPING)
- **Bounded Exploration**: Start with high-level summaries (symbol tables, section headers, string literals, export/import tables). Never dump multi-megabyte disassemblies into the prompt context.
- **Formulate Search Seeds**: Convert the user's objective into distinct search seeds (e.g. error strings, API names, cryptographic constants, IPC channel names).
- **Surface Mapping**: Identify attack surfaces, entry points, and inter-process communication boundaries.

### PHASE 3: DEEP DISSECTION & CROSS-VERIFICATION
- **Targeted Decompilation**: Decompile only the specific functions and basic blocks relevant to the target feature.
- **Anti-Decompiler Blindspot Check**:
  - High-level decompilers (Ghidra, Hopper, IDA) frequently miss stack inputs, FPU x87 registers, vector SIMD instructions, or indirect tail-calls.
  - When decompiled pseudocode looks incomplete or ambiguous, cross-reference directly with disassembled assembly instructions (`objdump -d -M intel`, `inspect_native_instruction`) and raw bytes.

### PHASE 4: EVIDENCE VERIFICATION & FALSIFICATION
- **Behavioral Probing & Test Vectors**: Verify extracted algorithms against deterministic test vectors (RFC standards, known inputs/outputs) before claiming success.
- **Reconciliation**: Reconcile static AST/symbol declarations against actual runtime behavior. Do not assume dead code is active.

### PHASE 5: CLEAN-ROOM RECONSTRUCTION & OBLIGATION CLOSURE
- **Synthesize Clean Code**: Reconstruct the verified algorithm from scratch in the target project language.
- **Fulfill Ledger Requirements**: Verify positive cases, negative boundary rejections, and edge cases before declaring the investigation complete.
