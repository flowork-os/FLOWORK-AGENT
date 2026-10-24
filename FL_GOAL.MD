# 🎯 FL_GOAL.MD — ACTIVE MISSION DIRECTIVE

1. **Eliminate Plaintext Connection Leak**:
   - Strip all plaintext `connection/` directories from local release assets (`flowork/connection`).
   - Patch `upload_github.sh` to forbid copying `connection/` into release trees (`linux/`, `windows/`, `macos/`).
   - Enforce cryptographic sealing via `core/src/connector_enclave.rs` and standalone native compilation.
2. **Build Sovereign Multi-OS Binaries**:
   - Compile Linux x86_64 ELF (`flowork` / `x-flow`).
   - Compile Windows x86_64 PE (`flowork.exe`).
   - Compile macOS Mach-O Universal (`flowork-darwin-x86_64` & `flowork-darwin-arm64`).
   - Compile native standalone connector binaries (`flowork-connector`, `flowork-connector.exe`).
   - Audit binaries with `.rodata` deep string inspection (Exit Code 0).
3. **Purge Remote GitHub Leaks ("Hapus Bersih di Atas")**:
   - Delete legacy GitHub Release `v1.0.0` and remote tag `v1.0.0`.
   - Purge entire git history on remote `origin/main` by force-pushing a clean orphan commit free of any plaintext `connection/` leaks.
4. **Publish Verified Sovereign Release v1.0.0**:
   - Bundle clean multi-OS distribution archives (`.tar.gz` and `.zip`).
   - Upload verified release assets with synchronized cryptographic SHA-256 checksums to GitHub Releases.
