---
id: preflight-security-and-user-io-gatekeeper
title: Sovereign Gatekeeper Architecture, Sandboxed Jailing, and HMAC Authentication
created_at: 2026-10-08T18:07:00Z
category: registry-security-gatekeeper
status: resolved
keywords:
  - preflight-gatekeeper
  - separation-of-duties
  - sandboxed-path-jailing
  - sovereign-hmac-sha256
  - zero-client-token
  - cloudflare-edge-gateway
  - anti-debug-ptrace
  - multi-os-portability
  - user-io-sovereignty
  - secret-leak-scanner
  - fail-closed-security
  - exit-code-zero
---

# Sovereign Gatekeeper Architecture, Sandboxed Jailing, and HMAC Authentication

## 1. Problem Statement & Threat Vector Analysis
Publishing plugins, skills, and tools to shared public registries introduces four critical vulnerability vectors:
1. **Repository Infrastructure Pollution**: Accidental or malicious overwriting of release binaries (`*.exe`, `*.deb`, `releases/`, `.github/workflows/`, root `README.md`).
2. **Client Credential Exposure**: Client-side GitHub Personal Access Tokens (PAT) risking privilege abuse if leaked.
3. **Agent Self-Remediation Bias**: Allowing the same agent doing the work to bypass security checks or try to "work around" failed audits without true fixes.
4. **Endpoint Spoofing & Reverse Engineering**: External attackers directly hitting edge endpoints (`plugins.floworkos.com`) or extracting static API tokens from client binaries via Ghidra/GDB.

## 2. Implemented Defense-in-Depth Solution

### A. Separation of Duties (SoD) & Gatekeeper Subagent Enforcement
- The primary agent has **no direct upload authority**.
- When publishing is triggered (`search_tools`, `plugin_publish`, `skill_control`, or `request_publish_gatekeeper`), the engine delegates inspection to an isolated **Security Gatekeeper & Publisher** subagent.
- **Strict Doctrine**: If ANY violation is detected:
  - The Gatekeeper is **FORBIDDEN** from modifying, editing, or remediating files.
  - The audit fails closed with **Exit Code 1**, returning structured findings.
  - The **Primary Agent MUST inspect the findings and fix the files in the workspace**.
  - Only when all violations are 100% resolved can publication succeed.

### B. Sandboxed Path Jailing (Cloudflare Worker)
- Enforced on edge (`flowork-plugin-hub`):
  - Tools are jailed strictly to `tools/<tool_id>/...` and `index/tools/`.
  - Plugins are jailed strictly to `plugins/<plugin_id>/...` and `index/plugins/`.
  - Skills are jailed strictly to `skills/<skill_id>/...` and `index/skills/`.
  - Any attempt to access protected paths (`.github/`, `releases/`, `bin/`, `*.exe`, `*.deb`, root `README.md`, `LICENSE`, directory traversal `..`) is rejected with **403 Forbidden: Sandbox Escape Attempt**.

### C. Zero-Client Token Architecture
- Client binaries hold **NO GitHub token**.
- The token is managed securely within Cloudflare Worker secrets (`env.GITHUB_TOKEN`).
- Cloudflare acts as an authenticated gatekeeper executing Git commits after verifying signatures and running edge SAST scans.

### D. Cryptographic HMAC-SHA256 & Anti-Replay Authentication
- Requests to `plugins.floworkos.com` require three headers:
  - `X-Flowork-Signature`: `HMAC-SHA256(secret_seed, timestamp + ":" + nonce + ":" + sha256(body))`
  - `X-Flowork-Timestamp`: Epoch milliseconds (strictly validated with max 60s clock drift against replay attacks).
  - `X-Flowork-Nonce`: UUID v4 nonce.
- Secret seed is XOR-masked at compile-time on the stack, preventing string extraction via `strings` or disassembly.

### E. Anti-Debug & Anti-Tamper Protection (Rust Engine)
- Linux: `libc::ptrace(libc::PTRACE_TRACEME)` detects active debuggers (GDB/strace/Frida) and blocks signature generation.
- Windows: `IsDebuggerPresent()` detects debuggers and locks cryptographic signing.

## 3. Empirical Verification (Exit Code 0)
- Full 66-test suite passed in `xflow-core` (`cargo test --bin x-flow`).
- Linux release binary (`x-flow`, 7.0 MB) and Windows cross-compiled release binary (`x-flow.exe`, 6.8 MB via `cargo-zigbuild`).
- Active daemon `./x-flow` verified running on `http://127.0.0.1:19890`.
- Synchronized across `flowork-os/generator` (commit `1d27abb`) and `flowork-os/FLOWORK-AGENT` (commit `44da98e`).
- Cloudflare Worker `flowork-plugin-hub` live on edge (`deployment_id: 9eece13c17a6433cb831d89cee0148fa`).
