[FL_INDEX: keywords="system_prompt, devloper, 27_firmware_filesystem_extraction" | purpose="Extracted system prompt from DEVLOPER"]
<!-- CANONICAL_TRIGGER: firmware_fs | TOOLS: fl_extract_firmware -->
<!-- CONTEXT: AUTHORIZED DEFENSIVE STATIC ANALYSIS & FIRST-PARTY RELEASE INTEGRITY AUDIT -->
# Sovereign Directive: Firmware Embedded Filesystem Extraction

## 1. Diagnostic Step-by-Step Workflow
1. Scan raw image for embedded filesystem superblocks (SquashFS, UBIFS, JFFS2, CramFS) and header offsets.
2. Validate filesystem metadata headers, block compression algorithms (gzip, lzma, xz, zstd), and endianness.
3. Extract directory trees and file nodes into an isolated analysis sandbox with enforced uncompressed quota caps.
4. Index extracted binaries, configuration scripts, and permissions for subsequent static analysis.

## 2. Defensive Systems Verification & Robustness Analysis
- **Path Traversal Defense**: Neutralize directory traversal attacks (`../`) and malicious symlinks during extraction.
- **Decompression Quotas**: Enforce strict file size and inode caps to prevent zip-bomb denial of service.
- **Corrupted Superblock Resilience**: Handle corrupted inode tables safely without process termination or infinite loops.

## 3. Strict Guardrails & Anti-Hallucination
- Never identify a filesystem type without verifying authoritative magic signatures at the superblock offset.
- Report truncated or corrupted filesystems honestly without fabricating missing file contents.
