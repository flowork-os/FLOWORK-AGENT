---
id: binary_asset_shrouding_mandatory_skill_pin
title: Zero-Leak Binary Asset Shrouding, Mandatory 1-Skill Pin, Ephemeral Tool Lifecycle and FL_BRAIN Supremacy
created_at: 2026-10-08T11:37:00Z
category: architecture
status: resolved
keywords: [binary_shrouding, zero_leak, asset_encryption, stream_cipher, mandatory_skill_pin, ephemeral_tools, anchor_tools, skill_control, search_tools, fl_brain_supremacy, prompt_compaction_resilience, memory_recall]
---

# Sovereign Architecture Memory: Binary Asset Shrouding & Ephemeral Skill Lifecycle

## 1. Problem Statement
1. **URL Leaks in Compiled Binary**: External endpoints (`https://auth.floworkos.com`, `https://github.com/...`, `https://www.googleapis.com/...`) were leaking in plaintext within `.rodata` due to raw `include_bytes!` embedded in `asset_server.rs` and `auth_callback.rs`.
2. **Unenforced Skill Requirements & Prompt Bloat**: Operational tools were callable without an active skill pinned, causing model hallucinations and unstandardized workflows. Pinned skills and dynamic tools persisted across conversation turns, causing cumulative prompt bloat.
3. **Over-reliance on Ephemeral Chat History**: Agents relied on prompt chat history which gets compacted/truncated by LLM context windows, ignoring `.fl_brain/` as the single source of truth.

## 2. Technical Solution
### A. Zero-Leak Stream Cipher Shrouding
- Created asset shrouder encrypting all 16 Canvas web assets (`launcher.html`, `auth.html`, `callback.html`, `canvas.js`, `canvas.css`, `three.module.js`, etc.) into `.shroud/*.enc` using `CIPHER_KEY` XOR stream cipher.
- Replaced raw `include_bytes!` in `core/src/asset_server.rs` and `core/src/auth_callback.rs` with `.shroud/*.enc`.
- In-memory stream decryption via `crate::prompt_seal::unseal_bytes` decrypts assets on disk self-heal or HTTP response streaming.
- `strings x-flow | grep "https?://"` verified 0 external production URL leaks.

### B. Mandatory 1-Skill Pin & Ephemeral Lifecycle
- **Permanent Anchor Tools**: `skill_control` and `search_tools` (alongside baseline execution anchors) permanently remain in the prompt declaration and are unblockable.
- **Mandatory Pin Intercept**: Operational tools (`run_command`, `view_file`, etc.) require at least 1 pinned skill in the active session. If no skill is pinned, runtime intercepts with `MANDATORY_SKILL_REQUIRED` prompting the agent to invoke `skill_control(action: 'pin')`.
- **Auto-Pin from Turn Intercept Gate**: First tool call reason evaluates against available skills and auto-pins any matched skill.
- **Post-Loop Ephemeral Flush**: In Step D (`agent.rs`), after finalizing the turn, `self.tools.clear_pinned_skill(&session_id)` and `self.tools.reset_to_anchor_tools(&session_id)` flush ephemeral skills and dynamic tools, ensuring the next turn prompt is clean and compact.

### C. Supremacy of `.FL_BRAIN`
- Updated `SEAL_PERSISTENT_CONTEXT_HEADER` in cryptographic enclave (`gen_enclave.py`):
  1. Mandates `.fl_brain/` as the single source of truth.
  2. Warns against relying on ephemeral prompt chat history (prone to compaction/truncation).
  3. Enforces fast keyword grep recall before complex tasks.
  4. Enforces atomic crystallization of new solutions into `.fl_brain/memories/<slug>.md`.

## 3. Verification
- `cargo test --bin x-flow`: 60/60 tests passed with Exit Code 0.
- `strings target/release/x-flow | grep "https://auth.floworkos.com"`: 0 matches (Exit Code 1).
