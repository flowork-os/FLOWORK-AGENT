---
name: "Reverse Engineer Anything"
description: "Sovereign runbook for multi-target reverse engineering, decompilation, binary inspection, and clean-room reconstruction across native binaries, Electron/ASAR, APK, and managed code"
keywords: ["reverse engineering","decompilation","binary analysis","disassembly","ghidra","hopper","ida pro","jadx","electron asar","static analysis","dynamic analysis","call graph","clean room design","ast parsing","firmware extraction","evidence graph","pe elf macho","apk analysis","symbol recovery","pseudocode"]
---

# ⚙️ SKILL: Reverse Engineer Anything

## 1. Intent & Trigger Boundaries
Defensive, multi-target reverse engineering SOP for extracting underlying architectures, logic flows, state models, and algorithmic patterns from shipped artifacts (native binaries, Electron/ASAR bundles, Android APKs, managed .NET/Java assemblies, and firmware images).

### Trigger Boundaries:
- User requests extracting or understanding a feature from a binary executable, closed application, or compiled package without available source code.
- Decompiling, disassembling, and inspecting PE (Windows), ELF (Linux), Mach-O (macOS), APK (Android), or ASAR (Electron) files.
- Bridging REA (`morluto/rea`) tools via CLI or integrating native reverse engineering engines (Ghidra, Hopper, IDA Pro, JADX, Binwalk).
- Reconstructing closed-source functionality into clean-room, unencumbered implementation code adhering to sovereign specifications.

## 2. Standard Operating Procedures

### Phase 1: Target Ingestion & Triage
1. **Target Identification & Format Routing:**
   - **Electron / JavaScript / ASAR**: Route directly to sovereign Chromium Pickle parser:
     ```bash
     node tools/fl_asar/main.mjs --target_path /path/to/app.asar
     ```
   - **Native Binary (ELF / PE / Mach-O)**: Inspect file architecture, mitigations & headers:
     ```bash
     node tools/fl_bin_inspect/main.mjs --target_path /path/to/binary
     ```
   - **Managed Assembly (.NET / CIL / CLR)**: Inspect metadata streams and disassemble CIL bytecode:
     ```bash
     node tools/fl_cil_inspect/main.mjs --target_path /path/to/assembly.dll
     ```
   - **Android APK**: Inspect package manifest, DEX pools, and export topologies:
     ```bash
     node tools/rea_inspect_android_package/main.mjs --target_path /path/to/app.apk
     ```
   - **Firmware Blob**: Perform entropy calculation and partition carving via `rea_extract_firmware`.

### Phase 2: Engine Selection & Hybrid Decompilation
1. **Engine Selection Protocol:**
   - For native binaries (Linux/Windows/macOS): Route to `rea_decompile` featuring Hybrid Socket Bridge detection with graceful POSIX fallback:
     ```bash
     node tools/rea_decompile/main.mjs --target_path /path/to/binary --symbol main
     ```
   - If local Ghidra / Hopper / IDA socket bridge is active, `rea_decompile` queries high-level pseudocode.
   - If daemons are offline, it falls back seamlessly to Intel disassembly under Exit Code 0.
2. **Deterministic Binary Decomposition:**
   - Extract symbol tables, exported functions, and imported dynamic link libraries:
     ```bash
     nm -D /path/to/binary
     objdump -T /path/to/binary
     strings -a -n 8 /path/to/binary | grep -E "https?://|API|auth|secret"
     ```
   - Trace control flow graphs (CFG) and identify high-value target routines (entry points, cryptography routines, IPC handlers).

### Phase 3: Evidence Graph Construction & Analysis
1. Extract inline Evidence records:
   - Identify observed facts (addresses, signatures, string literals, call hierarchy).
   - Differentiate strictly between verified facts, decompiler inferences, and unknown boundary conditions.
2. Synthesize API & state transition models:
   - Document payload serialization schemas, request headers, IPC protocol channels, and cryptographic primitives.

### Phase 4: Clean-Room Reconstruction
1. Build an unencumbered sovereign specification document containing:
   - Inputs, outputs, data formats, validation rules, state machine transitions, and error behaviors.
2. Implement native code (Rust, TypeScript, Python) strictly against the specification, ensuring zero proprietary code leakage and full independent implementation.

## 3. Strict Prohibitions & Edge Cases
- **Absolute Portability**: Never hardcode host absolute paths (`/home/...`, `C:\...`). Always use relative or dynamic path resolution.
- **Zero Vibe Reversing**: Never hallucinate API schemas or crypto keys; every claim must be backed by concrete disk strings, disassembler offsets, or decompiler pseudocode.
- **Session Isolation**: Never pollute the workspace root with decompiler database dumps or temporary projects. Isolate all caches, dumps, and extractions to `.FL_BIN/`.

## 4. Verification & Exit Code 0 Proof
1. Verify static parsing output or CLI tool invocation:
   ```bash
   npx -y rea-agents@latest doctor --json
   ```
2. For extracted code or clean-room implementation, execute test suite and confirm Exit Code 0 across all verification steps.
