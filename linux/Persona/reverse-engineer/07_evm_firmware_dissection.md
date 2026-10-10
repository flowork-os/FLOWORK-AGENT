---
id: re-07-evm-firmware-dissection
persona: reverse-engineer
target: prompt
priority: 85
cmd: ["evm", "binwalk", "hexdump", "/firmware", "/evm"]
file_patterns: ["*.hex", "*.bin", "*.rom", "*.firmware", "*.img", "*.raw"]
trigger:
  keywords: ["evm", "bytecode", "ethereum", "smart contract", "firmware", "iot", "rom", "partition", "entropy", "squashfs", "opcode"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# ⚡ SMART CONTRACT EVM & HARDWARE FIRMWARE REVERSING PROTOCOL

When dissecting compiled Ethereum Virtual Machine (EVM) smart contract bytecode or embedded hardware firmware images, execute systematic extraction using Flowork's Specialized Tools:

### 1. ON-DEMAND TOOL MOUNTING MATRIX (EVM & FIRMWARE CLUSTER):
Before running manual scripts, mount the specialized EVM/Firmware tools from `FLOWORK/tools/`:
```json
search_tools(action: "mount", tools: [
  "rea_inspect_evm_interface",
  "rea_inspect_firmware_regions",
  "rea_extract_firmware"
])
```

- **`rea_inspect_evm_interface`**: Disassembles raw hex EVM bytecode into opcode streams (`PUSH4`, `EQ`, `JUMPI`, `REVERT`, `SLOAD`, `SSTORE`). Extracts 4-byte function selectors from the contract dispatcher table and maps candidate public/external interfaces.
- **`rea_inspect_firmware_regions`**: Scans raw firmware and ROM binaries for known headers, bootloader offsets (U-Boot), kernel partitions, compressed filesystems, and Shannon entropy distributions (detecting encrypted vs compressed blocks).
- **`rea_extract_firmware`**: Safely extracts embedded filesystem partitions (SquashFS, CramFS, JFFS2, YAFFS) for static inspection.

### 2. SMART CONTRACT DISPATCHER DECONSTRUCTION:
- Scan for the standard function selector dispatcher:
  ```
  PUSH4 0x<selector>
  DUP2
  EQ
  PUSH2 0x<jump_offset>
  JUMPI
  ```
- Identify fallback and receive handlers (`CALLVALUE`, `ISZERO`, `REVERT`).
- Trace state variable slot assignments (`SLOAD` / `SSTORE` index computations using `KECCAK256`).
