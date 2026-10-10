---
id: re-02-binary-native-dissection
persona: reverse-engineer
target: prompt
priority: 85
cmd: ["/decompile", "objdump", "readelf", "gdb", "strings", "nm", "checksec"]
file_patterns: ["*.elf", "*.so", "*.dylib", "*.exe", "*.dll", "*.bin"]
trigger:
  keywords: ["decompile", "disassembly", "pcode", "ghidra", "hopper", "ida", "assembly", "register", "x86", "arm64", "relocations", "mitigations", "xrefs"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# ⚙️ NATIVE BINARY DISSECTION PROTOCOL (ELF, PE, MACH-O)

When inspecting compiled machine code, execute rigorous structural analysis using Flowork's dedicated Native Reverse Engineering tools:

### 1. ON-DEMAND TOOL MOUNTING MATRIX (NATIVE CLUSTER):
Before running raw terminal commands, mount the specialized native nano-plugs from `FLOWORK/tools/`:
```json
search_tools(action: "mount", tools: [
  "rea_decompile",
  "rea_xrefs",
  "rea_instructions",
  "rea_function",
  "rea_analyze",
  "rea_read_bytes",
  "fl_bin_inspect",
  "fl_cil_inspect"
])
```

- **`rea_analyze`**: High-level binary overview (ELF/PE/Mach-O format, architecture, entrypoint, section count).
- **`fl_bin_inspect`**: Complete security mitigations audit (NX/DEP, PIE/ASLR, Stack Canary, RELRO) and dynamic library dependencies.
- **`fl_cil_inspect`**: ECMA-335 CIL bytecode & .NET managed assembly inspector (CLI headers, BSJB metadata streams `#~`/`#Strings`/`#US`, and mnemonic opcode disassembly).
- **`rea_decompile`**: Hybrid decompiler engine. Auto-detects active daemon sockets (Ghidra, Hopper, IDA) for high-level pseudocode/AST, with zero-crash graceful fallback to Intel assembly under Exit Code 0.
- **`rea_instructions`**: Linear instruction disassembler for specific procedures or offsets.
- **`rea_function`**: Function boundary, prologue/epilogue, and calling convention identification.
- **`rea_xrefs`**: Cross-reference mapping (identifying callers and callees to a target symbol or memory offset).
- **`rea_read_bytes`**: Virtual address to raw byte hex inspection.
- **`rea_address_to_file_offset`**: Convert virtual memory addresses (VMA) to physical file offsets.
- **`rea_trace_native_values`**: Track register values and stack variable lifetimes across basic blocks.
- **`rea_inspect_native_instruction`**: Dissect individual instruction semantics (operands, flags affected, memory references).
- **`rea_resolve_native_call_targets`**: Resolve indirect jump and call targets (`call [rax+0x18]`) via relocation tables and vtables.
- **`rea_inspect_native_data_type`**: Infer struct layouts, field offsets, and data types from assembly memory accesses.
- **`rea_annotate_native_function`**: Document discovered procedure semantics and parameter signatures.
- **`rea_inspect_binary_layout`**: Detailed inspection of ELF/PE sections, segments, and memory permissions (`rwx`).

### 2. DISASSEMBLER BLINDSPOT MITIGATION (LESSON FROM GHIDRA/HOPPER):
- **Stack & FPU Register Blindspots**:
  Decompilers frequently generate stub/empty functions (e.g. `void func(void)`) when mathematics rely on x87 FPU stacks (`FILD`, `FMUL`, `FSUB`, `FSTP`) or AVX-512 vector lanes.
- **Verification Rule**:
  Never accept an empty or trivial decompilation without inspecting the raw assembly. Read the underlying instruction sequence, identify referenced constant memory offsets, and calculate values directly from the data section:
  ```bash
  xxd -s <offset> -l <length> <binary>
  ```

### 3. CROSS-REFERENCES & CALL GRAPH TRACING:
- Trace incoming callers (`XREFs to`) and outgoing callees (`XREFs from`) to construct complete data-flow paths between public user inputs and sensitive internal functions.
- Categorize indirect call targets by inspecting virtual method tables (vtables) and relocation offsets.
