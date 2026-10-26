---
name: sovereign_canvas_plugin_architecture
title: Flowork OS Sovereign Canvas Plugin Architecture & Operational Standard
description: Authoritative SOP and engineering specification for creating interactive Flowork Canvas plugins, implementing Dual-Wing triggers, dynamic port binding, human-in-the-loop co-creation, and dedicated plugin SKILL.md runbooks.
author: "floworkos.com"
version: "2.0.0"
keywords:
  - plugins
  - canvas_ui
  - plugin_manifest
  - human_in_the_loop
  - co_creation
  - dynamic_port
  - microservice
  - rest_api
  - server_sent_events
  - websocket
  - interactive_webview
  - dual_wing_trigger
  - exclude_keywords
  - runbook_sop
  - zero_zombie
  - strict_english_ui
  - process_lifecycle
  - multi_os_portability
  - exit_code_zero
  - flowork_sovereignty
exclude_keywords:
  - internal_tool
  - cli_only
  - background_worker
---

# 🧩 SOVEREIGN CANVAS PLUGIN ARCHITECTURE (FLOWORK OS)

> **PLATFORM**: FLOWORK OS (FLOWORKOS.COM) SOVEREIGN ROOT ARCHITECTURE.  
> **CORE DOCTRINE**: HUMAN-IN-THE-LOOP CO-CREATION, DEDICATED CANVAS WORKBENCH, DUAL-WING MANIFEST CONTRACT, ZERO-ZOMBIE PROCESS MANAGEMENT, AND EMPIRICAL EXIT CODE 0 VERIFICATION.  
> **CO-AUTHORED-BY**: Flowork OS <agent@floworkos.com>

---

## 📌 1. Executive Philosophy & Fundamental Distinction: Tools vs. Plugins

Within the Flowork OS Sovereign Architecture, **Tools** and **Plugins** serve distinct functional purposes:

### 1. Internal Agent Tools (`{engine_root}/tools/`)
* **Purpose:** Instruments of autonomous execution for the AI Agent (e.g. `run_command`, `view_file`, `write_to_file`, `replace_file_content`, `search_tools`).
* **Execution Boundary:** Execute non-visually under agent discretion to inspect, analyze, edit files, and execute system commands behind the scenes.
* **Output:** Return structured data directly into the LLM conversation context or render inline visual summaries in the chat HUD.

### 2. Interactive Canvas Plugins (`{engine_root}/apps/`)
* **Purpose:** Visual, interactive workbench applications hosted on the Flowork Canvas stage.
* **Core Doctrine: Human-in-the-Loop Co-Creation:** A dedicated visual arena where human operators and AI agents collaborate in real time (e.g. Chess Arena duels, YouTube Downloader & DSP Suno Audio Studio, Video Editor, Diagram/Form Co-creators).
* **Agent Awareness:** The AI agent possesses real-time awareness of plugins opened by the user, inspects live application state via local APIs, dispatches actions, and updates the Canvas interface instantaneously.

---

## 📂 2. Standard Directory Layout: The Flow Hybrid Architecture (.flow + Naked GUI)

Every plugin implements the **Flow Hybrid Architecture**, balancing immediate UI inspectability and CSS reactivity with sealed, tamper-proof backend execution:

```text
{engine_root}/apps/<app_id>/
├── plugin.manifest.json       # [MANDATORY] Plugin contract, Dual-Wing triggers, entrypoint, IPC & permissions
├── SKILL.md                   # [MANDATORY] Plugin interaction runbook (exact 20 English keywords, API schema)
├── trigger.md                 # [MANDATORY] UNCE sensory trigger conditions
├── engine/                    # [MANDATORY] Sealed backend microservice runtime
│   ├── logic.flow             # [MANDATORY] Sealed proprietary .flow binary container (Gzip archive + SHA-256)
│   └── server.mjs             # [MANDATORY] In-memory unpacker & ephemeral runner (~50 lines, RAM execution)
└── gui/                       # [OPTIONAL] Dedicated Canvas UI webview (Naked/Plaintext)
    ├── index.html             # Entry markup (100% Strict English UI)
    ├── style.css              # Scoped stylesheet (#<app_id>-root namespace, Flowork Dark Mode tokens)
    └── app.js                 # Frontend state manager and SSE/WebSocket client
```

### 🧩 The 4 Pillars of Flow Hybrid Architecture:
1. **Naked GUI (`gui/`):** HTML, CSS, and client-side JavaScript remain unbundled and uncompiled, enabling instant browser rendering, DOM inspection, Web Audio/WebGL hardware access, and seamless Flowork token inheritance.
2. **Sealed Logic Container (`engine/logic.flow`):** All backend Node.js business logic, dependencies, and algorithms are securely sealed inside the `.flow` binary container (`FLOW` magic header, gzip compression, and SHA-256 checksum).
3. **In-Memory Ephemeral Runner (`engine/server.mjs`):** An ultra-lean loader that reads `logic.flow`, verifies SHA-256 cryptographic integrity, uncompresses the module into RAM, executes the entrypoint, and cleans up temporary files with zero disk pollution.
4. **Raw Code Purge:** Loose unsealed backend code (`server.raw.mjs`, source scripts) MUST be purged from deployment directories once compiled into `logic.flow`. Source code is preserved in Git repositories.

---

## ⚙️ 3. Standard Manifest Contract Specification (`plugin.manifest.json`)

Every plugin **MUST** provide an authoritative `plugin.manifest.json` defining its identity, capabilities, entrypoints, and Dual-Wing triggers:

```json
{
  "$schema": "https://floworkos.com/schemas/plugin.manifest.json",
  "id": "chess",
  "name": "Sovereign Chess Arena",
  "version": "1.0.0",
  "author": "Flowork OS",
  "description": "Interactive dual-sovereignty chess arena for live Human vs Agent matches on Flowork Canvas.",
  "category_id": "CAT-020",
  "category": "Sports Science & Athletics Performance",
  "icon": "♟️",
  "keywords": [
    "chess",
    "chessboard",
    "chess_engine",
    "stockfish",
    "grandmaster",
    "fen",
    "pgn",
    "board_game"
  ],
  "exclude_keywords": [
    "chinese_chess",
    "xiangqi",
    "checkers"
  ],
  "entry": {
    "gui": "gui/index.html",
    "backend": "engine/server.mjs"
  },
  "skill": "SKILL.md",
  "ipc": {
    "port_env": "FLOWORK_APP_PORT",
    "default_port": 17820
  },
  "permissions": {
    "network": true,
    "filesystem_read": ["."]
  }
}
```

### Standard Manifest Fields:
| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `id` | String | Yes | Unique plugin identifier matching directory name (`plugins/<id>/`). |
| `name` | String | Yes | Human-readable title displayed on Canvas tabs. |
| `version` | String | Yes | Semantic version string (`1.0.0`). |
| `author` | String | Yes | Creator attribution or team handle. |
| `description` | String | Yes | Comprehensive overview of features and collaborative workflows. |
| `category_id` | String | Yes | **Mandatory** Official Flowork Category ID (`CAT-001` through `CAT-026`). Enforced by Gatekeeper. |
| `category` | String | Yes | Canonical domain category matching `category_id` taxonomy. |
| `icon` | String | Yes | Unicode emoji or SVG asset identifier. |
| `keywords` | Array<String> | Yes | Positive substring trigger patterns for automatic recommendation. |
| `exclude_keywords` | Array<String> | Yes | Negative exclusion patterns for collision avoidance. |
| `entry.gui` | String | No | Path to webview markup entrypoint (`gui/index.html`). |
| `entry.backend` | String | Yes | Path to microservice script or binary (`engine/server.mjs`). |
| `ipc.port_env` | String | Yes | Environment variable name injecting the assigned port (`FLOWORK_APP_PORT`). |
| `ipc.default_port`| Integer | Yes | Fallback port if unmanaged (`17820`). |
| `permissions` | Object | No | Declared sandboxing permissions (`network`, `filesystem_read`). |

---

## 🎯 4. Dual-Wing Trigger Architecture on Canvas Plugins

To prevent **Plugin Activation Ambiguity and Collisions**, all plugin manifests enforce the **Dual-Wing Condition Architecture**:

```
                              ┌────────────────────────────────────────┐
                              │         USER INTENT / CHAT QUERY       │
                              │    (e.g., "start chess match with me") │
                              └───────────────────┬────────────────────┘
                                                  │
                               [Case-Insensitive Substring Scan]
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
               [Negative Exclusion Wing]                         [Positive Keyword Wing]
             `query_lower.contains(&ex)`                       `query_lower.contains(&kw)`
                         │                                                 │
            Does query contain exclude term?                  Does query contain keyword?
            (e.g., "checkers" in chess rule)                  (e.g., "chess" or "chessboard")
                         │                                                 │
                 ┌───────┴───────┐                                 ┌───────┴───────┐
                 │ YES           │ NO                              │ YES           │ NO
                 ▼               ▼                                 ▼               ▼
            [DISQUALIFIED]   [Pass to Positive]                [MATCHED / RECOMMEND] [IGNORE]
            (Short-Circuit)  (Evaluate Keywords)               (Launch Plugin Canvas (Skip)
             Plugin Rejected                                    / Bind Host Tab)
```

### Concrete Collision Avoidance Matrix:
* **Chess Arena (`chess`) vs. Checkers & Board Games:**
  - Plugin `chess` specifies positive keywords: `["chess", "chessboard", "chess_engine", "grandmaster", "fen", "pgn"]`.
  - Plugin `chess` specifies exclusions: `["chinese_chess", "xiangqi", "checkers"]`.
  - **Evaluation Outcomes:**
    | Input Query | `chess` Match | Exclusion Status | Active Result |
    | :--- | :--- | :--- | :--- |
    | `"Play a game of chess with me on canvas"` | ✅ Matched (`chess`) | 🟢 Not excluded | **Launch Sovereign Chess Arena** |
    | `"Let's play checkers on board"` | ❌ No match | 🛑 **Excluded (`checkers`)** | **Ignore Chess Plugin** |
    | `"Analyze this FEN string on chessboard"` | ✅ Matched (`fen`) | 🟢 Not excluded | **Launch Sovereign Chess Arena** |

---

## ⚡ 5. Dynamic Port Allocation & Zero-Zombie Process Lifecycle

### 1. Dynamic Port Injection (`$FLOWORK_APP_PORT`)
* Hardcoding static network ports is strictly prohibited to prevent fatal `EADDRINUSE` socket conflicts when multiple instances run simultaneously.
* The X-Flow runtime supervisor allocates an available high-range port and injects it via environment variable:

```javascript
// Node.js implementation: engine/server.mjs
import http from 'http';

const PORT = parseInt(process.env.FLOWORK_APP_PORT || process.env.PORT || '17820', 10);
const server = http.createServer((req, res) => {
  // Application routing
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[Plugin:chess] Microservice listening on http://127.0.0.1:${PORT}`);
});
```

```python
# Python implementation: engine/server.py
import os
from aiohttp import web

PORT = int(os.environ.get("FLOWORK_APP_PORT", os.environ.get("PORT", 17820)))
app = web.Application()
web.run_app(app, host="127.0.0.1", port=PORT)
```

### 2. Zero-Zombie Process Lifecycle
* **PID Registration:** When X-Flow launches a plugin backend microservice, it tracks its OS Process ID (PID).
* **Graceful Termination:** When a plugin tab is closed, the session is cleared, or the host restarts, the supervisor dispatches `SIGTERM` followed by `SIGKILL` if unclosed within 3 seconds.
* **Process Cleanup Hook:**
  ```javascript
  const cleanup = () => {
    console.log('[Plugin:chess] Gracefully shutting down microservice...');
    server.close(() => process.exit(0));
  };
  process.on('SIGTERM', cleanup);
  process.on('SIGINT', cleanup);
  ```

---

## 📡 6. Real-Time Communication Protocols (SSE & REST API)

Plugins interact with both the Canvas UI webview and the AI agent using lightweight, zero-latency protocols:

### 1. Server-Sent Events (SSE) for Real-Time State Broadcast
The microservice exposes an SSE stream (`GET /api/events`) enabling the webview to update instantly when the AI agent executes actions behind the scenes:
```javascript
// Server-side event broadcast (engine/server.mjs)
const clients = new Set();

export function handleSSE(req, res) {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Access-Control-Allow-Origin': '*'
  });
  clients.add(res);
  req.on('close', () => clients.delete(res));
}

export function broadcastState(data) {
  const payload = `data: ${JSON.stringify(data)}\n\n`;
  for (const client of clients) client.write(payload);
}
```

```javascript
// Client-side stream listener (gui/app.js)
const eventSource = new EventSource('/api/events');
eventSource.onmessage = (event) => {
  const state = JSON.parse(event.data);
  updateCanvasView(state);
};
```

---

## 🧠 7. Session Telemetry & Runtime `<CALLER_CONTEXT>` Awareness

The Level 0 micro-kernel automatically injects live Canvas telemetry into the system prompt's `<CALLER_CONTEXT>` enclave on every turn:
```xml
<CALLER_CONTEXT>
- Active Chat ID: session-coder-99
- Open Plugins: chess (port: 17820), yt-downloader (port: 17895)
</CALLER_CONTEXT>
```

### Agent Awareness Protocol:
* When a plugin is listed under `Open Plugins`, the AI agent immediately recognizes that the user has that visual workbench open on their screen.
* The agent can query application state, calculate next moves, process media, or trigger updates by executing HTTP requests to `http://127.0.0.1:<PORT>/...`.

### 🔄 Bi-Directional Co-Creation & Direct Action Prompt Injection:
Plugins are not static displays; they are living collaborative arenas between humans and agents:
1. **Active Prompt Injection via `/api/prompt-dispatch`:**
   When an operator performs an action on the Canvas UI (e.g. moves a piece in Chess Arena, clicks "Ask AI", or triggers a workflow), the frontend webview (`gui/app.js`) dispatches a direct actionable prompt directly to the open chat session:
   ```javascript
   // Example: Direct Action Prompt Injection (as implemented in apps/chess/gui/app.js)
   fetch('/api/prompt-dispatch', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       toAgent: 'mr.flow',         // Optional: Target specific specialist agent
       triggerId: 'chess',         // Optional: Identifier for audit logging
       prompt: `[PLUGIN: ${pluginId.toUpperCase()}] Operator ${userProfile.name} executed action: ${action}\n` +
               `Live State: ${JSON.stringify(state)}\n` +
               `Active Port: ${port}\n\n` +
               `DIRECT ACTION COMMAND: Execute the counter-action immediately via:\n` +
               `curl -s -X POST http://127.0.0.1:${port}/api/action -H "Content-Type: application/json" -d '${JSON.stringify(actionPayload)}'\n\n` +
               `Reply to ${userProfile.name} in chat with friendly banter!`,
       eventPayload: { action, state }
     })
   });
   ```
2. **Immediate 1-Step Execution (Anti-Loop Doctrine):**
   The Flowork Kernel routes this event to the active chat session, waking up the agent. Because the prompt already provides the actionable endpoint, port, and payload contract, the agent executes the counter-action **immediately in 1 single step** via `run_command` without redundant `view_file` calls!
3. **Skill Reading on Initial Mount Only:**
   `SKILL.md` is inspected once upon initial plugin mounting or session bootstrap. Redundant orders to re-read `SKILL.md` on every routine user click or move are strictly forbidden to prevent cognitive loop latency.
4. **Real-Time Visual Sync (SSE):**
   The backend microservice processes the agent's request and broadcasts the updated state over SSE (`/api/events`) to `gui/app.js`, instantly updating the Canvas UI!

---

## 📖 8. Mandatory Dedicated Plugin Runbook (`{engine_root}/apps/<app_id>/SKILL.md`)

> 🚨 **INVARIANT OPERATIONAL LAW: ZERO GUESSWORK**  
> **AGENTS ARE STRICTLY FORBIDDEN FROM GUESSING PLUGIN API ENDPOINTS, QUERY PARAMETERS, OR JSON PAYLOAD SCHEMAS.**

Whenever an agent interacts with a newly mounted Canvas plugin:
1. **Initial Inspection (`view_file`):** Open and read `{engine_root}/apps/<app_id>/SKILL.md` once upon mounting using `view_file`.
2. **Review Official Contracts:** Inspect the declared REST API endpoints (`GET /api/state`, `POST /api/action`), header requirements, and expected response payloads.
3. **Precision Execution:** Invoke endpoints via `run_command` (using `curl` or Node.js) with verified arguments.

### Standard Plugin `SKILL.md` Template:
```markdown
# ♟️ SOVEREIGN CHESS ARENA — OPERATIONAL RUNBOOK

## 1. Role & Identity
- Player White: Human Operator
- Player Black: Flowork AI Agent

## 2. Dynamic Port & Endpoint Resolution
- Active port is provided in <CALLER_CONTEXT> (e.g. port 17820).

## 3. REST API Contract & Execution

### A. Inspect Board State & Legal Moves
\`\`\`bash
curl -s http://127.0.0.1:<PORT>/api/state
\`\`\`

### B. Execute Move
\`\`\`bash
curl -s -X POST http://127.0.0.1:<PORT>/api/move \
  -H "Content-Type: application/json" \
  -d '{"from": "e7", "to": "e5", "comment": "Countering center pawn structure!"}'
\`\`\`
```

---

## 🛡️ 9. Quality Standards & Preflight Gatekeeper Audit

Before publishing or finalizing any new Canvas plugin:
1. **Mandatory Dual Runbook & Trigger Consultation:**
   - Prior to designing, implementing, or scaffolding any Canvas plugin, the agent MUST read both `{engine_root}/apps/SKILL.MD` AND `{engine_root}/apps/trigger.md` via `view_file`.
2. **Mandatory Category Taxonomy Binding (`category_id` CAT-001 .. CAT-026):**
   - The plugin manifest MUST declare an official `category_id` from the 26 Flowork OS professional jurisdictions (`CAT-001` through `CAT-026`). Plugins with missing or unrecognized categories are rejected by the Gatekeeper with Exit Code 1.
3. **Plugin Trigger Specification (`{engine_root}/apps/<app_id>/trigger.md`):**
   - Every plugin MUST provide its ambient trigger specification in `{engine_root}/apps/<app_id>/trigger.md` (or within `plugin.manifest.json`).
   - Must declare valid `scopes`, `events`, and bind to an official category (`CAT-001` through `CAT-026`, or `all`).
   - If declaring UNCE conditions (`local.port_open`, `time.market_session`, `env.is_headless`, `hw.cpu_load_percent`), all operators MUST conform strictly to standard UNCE comparison syntax.
4. **Multi-OS Portability Audit:** Verify zero absolute host paths (`detect_hardcode`). Use relative paths and OS-agnostic path resolvers (`path.join`).
5. **Dynamic Port Proof:** Verify backend microservice honors `process.env.FLOWORK_APP_PORT`.
6. **100% Strict English UI & Logs:** Ensure all buttons, labels, tooltips, and console log outputs are written exclusively in formal industry English.
7. **Scoped CSS Isolation:** Ensure all GUI styling is enclosed within `#<app_id>-root` or custom scoped container classes.
8. **Mandatory Dedicated Runbook (`SKILL.md`):** Verify `{engine_root}/apps/<app_id>/SKILL.md` provides complete, copy-paste runnable `curl` examples and schema docs.
9. **Exit Code 0 Terminal Proof:** Verify backend tests and build suites terminate cleanly with exit code 0.
10. **Visual GUI Inspection via Screenshot:** Take a screenshot via `flow_screenshot` / `screenshot` of the running GUI window to verify layout, rendering, DOM state, and responsive styling. It is strictly forbidden to claim completion without visual screenshot evidence.
11. **Mandatory Subagent Audit Verification (Pilar 5: Trigger Verification):**
   - The independent auditor subagent spawned during preflight verification MUST verify `{engine_root}/apps/<app_id>/trigger.md` against `{engine_root}/apps/trigger.md`.
   - Any hallucinated trigger keys, invalid category bindings, or syntax errors will cause the auditor to reject the plugin immediately.

---

## 🚀 10. Mandatory Contribution & Publication Pipeline

Whenever an agent engineers, upgrades, or releases a Canvas plugin:
1. **Preflight Security Gatekeeper Audit:**
   Execute the dedicated preflight auditor tool to inspect manifest, category ID, triggers, dynamic port compliance, and DLP cleanliness:
   ```bash
   node tools/request_publish_gatekeeper/main.mjs --params '{"bundle_type": "plugin", "bundle_id": "<app_id>"}'
   ```
   *Gatekeeper returns Exit Code 0 on clean pass, or Exit Code 1 with blocking violation list.*

2. **Attestation Guard & Publication Tool (`app_publish`):**
   Once cleared by the gatekeeper, publish the plugin to official local/remote registries (`plugins/plugins.json` and `.registry_cache_linux.json`) with recursive SHA-256 integrity hashing:
   ```bash
   node tools/app_publish/main.mjs --params '{"app_id": "<app_id>", "target_os": "linux", "notes": "feat: release <app_id> canvas app"}'
   ```
   Or invoke via kernel tool call:
   ```bash
   app_publish(app_id: "<app_id>", target_os: "linux", notes: "feat: add <app_id> canvas app")
   ```
3. **Attestation Guard (Cryptographic Hash Integrity):** The kernel validates local binary and core UI SHA-256 hashes against `release_checksums.json` on GitHub. Any tampered or unauthorized build is immediately blocked from remote publication.

