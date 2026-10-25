### 1. KERNEL GUARDIAN: MANDATORY GITHUB RESEARCH PRIOR TO CREATION
🚨 **MANDATORY STEP 0**: Prior to scaffolding or creating any app files, conduct technical research via `search_web` or `read_url_content`. Violations will trigger kernel termination with `GUARDIAN ACCESS DENIED`.

### 2. CANONICAL APP DIRECTORY TERRITORY (`apps/<app_id>/`)
All interactive Canvas applications MUST reside inside `{workspace}/apps/<app_id>/`.
- **Haram Symlink Doctrine**: Strictly forbidden to create alias symlinks (such as `app/` or `plugins/`). The canonical directory is uniquely and strictly `apps/`.
- **Naked GUI (`gui/`)**: Uncompiled plaintext HTML/CSS/JS (`gui/index.html`, `gui/style.css`, `gui/app.js`) for full DOM reactivity, Web Audio/WebGL access, and visual Canvas integration.
- **Backend Logic (`server.js` or `engine/server.mjs`)**: Scalable, fast microservice running on loopback with REST / SSE / WebSocket IPC.
- **Required Contracts**: `plugin.manifest.json`, `SKILL.md` (exact 20 keywords), and `trigger.md`.

### 3. STRICT MANIFEST CONTRACT SPECIFICATION (`plugin.manifest.json`)
The binary kernel (`x-flow`) strictly validates `plugin.manifest.json` using Rust serde typing. ANY deviation or incorrect type (e.g. using string instead of object for `entry`) causes silent deserialization failure and drops the app from the App Store.

**Mandatory Canonical Schema:**
```json
{
  "id": "my-app-id",
  "name": "My App Name",
  "version": "1.0.0",
  "author": "Flowork Sovereign Core",
  "description": "Clear English summary of application capabilities.",
  "category": "Media, Creative Writing & Journalism",
  "category_id": "CAT-010",
  "icon": "🎬",
  "entry": {
    "gui": "gui/index.html",
    "backend": "server.js"
  },
  "ipc": {
    "port_env": "FLOWORK_APP_PORT",
    "default_port": 18012
  },
  "keywords": ["keyword1", "keyword2"],
  "exclude_keywords": []
}
```
*Note: `entry` MUST be a JSON object containing `"gui"` and optionally `"backend"`. `ipc` MUST be a JSON object containing `"port_env"` and `"default_port"`. Never use `"entry": "gui/index.html"` as a plain string, and never use `"ports": {"preferred": ...}`.*

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
