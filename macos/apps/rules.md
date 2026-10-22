### 1. KERNEL GUARDIAN: MANDATORY GITHUB RESEARCH PRIOR TO CREATION
🚨 **MANDATORY STEP 0**: Prior to scaffolding or creating any plugin files, conduct technical research via `search_web` or `read_url_content`. Violations will trigger kernel termination with `GUARDIAN ACCESS DENIED`.

### 2. MANDATORY FLOW HYBRID ANATOMY (.FLOW & NAKED GUI)
Every plugin MUST adhere to the Flow Hybrid Architecture:
- **Naked GUI (`gui/`)**: Uncompiled plaintext HTML/CSS/JS (`gui/index.html`, `gui/style.css`, `gui/app.js`) for full DOM reactivity, Web Audio/WebGL access, and visual Canvas integration.
- **Sealed Backend Logic (`engine/logic.flow`)**: All backend business logic is sealed inside the proprietary `.flow` binary container format (magic bytes `FLOW`, 64-byte binary header, gzip compressed archive, and SHA-256 integrity hash).
- **In-Memory Ephemeral Runner (`engine/server.mjs`)**: Ultra-compact unpacker (~50 lines) that validates SHA-256 integrity, inflates `logic.flow` into RAM, executes ephemerally, and deletes transient files to ensure zero disk residue.
- **Raw Code Purge**: Loose backend source files (`server.raw.mjs`, raw engine scripts) MUST be purged from deployment directories once packaged into `logic.flow`.
- **Contracts**: `plugin.manifest.json`, `SKILL.md` (exact 20 keywords), and `trigger.md`.

### 3. CANONICAL APP IDENTIFIER & MANIFEST CONTRACT
Every `app.manifest.json` (or `plugin.manifest.json`) MUST define a unique lowercase alphanumeric `id` (e.g., `chess`, `kamidi-mastering`), human-readable `name`, semver `version`, explicit entry points (`engine/server.mjs`, `gui/index.html`), and valid capability scopes. Arbitrary unvalidated structures are strictly prohibited.

### 4. DIRECT ACTION PROMPT DISPATCH (ANTI-LOOP DOCTRINE)
When the Canvas GUI dispatches an event via `/api/prompt-dispatch`, the prompt MUST provide direct actionable context (current state, active dynamic port, and exact REST payload/curl command). **STRICTLY FORBIDDEN** to order the agent to inspect `SKILL.md` via `view_file` on every routine user click or move; redundant file-reading orders trigger severe thinking-loop latency (120+ seconds). Agents inspect `SKILL.md` only on initial mounting or on-demand.

### 5. MULTI-OS PORTABILITY & NO HARDCODED PATHS
Hardcoding absolute host paths (filesystem root, drive letters) is strictly forbidden. All code must remain cross-platform compatible across Linux, Windows, and macOS using relative resolvers (`path.join`, environment variables). Enforce dynamic port bindings (`18000–18999`) and strict CSS isolation scoped to `#<id>-root`.

### 6. STRICT ENGLISH MANDATE FOR GUI & SYSTEM LOGS
All user-facing graphical elements (menus, labels, buttons, dialogs, placeholders, tooltips) and runtime diagnostics (`console.log`) MUST be in 100% standard professional English. Non-English text in GUI components is strictly prohibited.

### 7. PREFLIGHT SECURITY GATEKEEPER & ATTESTATION PUBLISH
Prior to release, run preflight validation:
`node tools/request_publish_gatekeeper/main.mjs --params '{"bundle_type":"plugin","bundle_id":"<id>"}'`
Once passing Exit Code 0, execute publication:
`node tools/app_publish/main.mjs --params '{"app_id":"<id>","target_os":"linux","notes":"<notes>"}'`

### 8. MANDATORY INDEPENDENT SUBAGENT AUDITOR & DUAL QC
Self-auditing is strictly forbidden! You MUST spawn an independent auditor subagent to verify: zero bugs, zero security vulnerabilities (SAST/DLP), absolute rules compliance (strict English, CSS isolation, Exit Code 0 proof, and GUI visual verification via `flow_screenshot`) prior to claiming task completion.

### 9. MANDATORY GIT COMMIT CO-AUTHOR
Every git commit MUST include:
`Co-authored-by: Flowork OS <agent@floworkos.com>`.
