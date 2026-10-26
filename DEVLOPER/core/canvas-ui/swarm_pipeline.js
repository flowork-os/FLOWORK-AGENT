/**
 * ============================================================================
 * ⚡ FLOWORK OS — SWARM PIPELINE CANVAS ENGINE
 * Focus: Agent & Trigger (Left Bar), Infinite Canvas (No Right Bar),
 * Dual-Output Ports, 4-Way Cable Deletion, and Full Popup Prompt Editor (Task & Rules).
 * Module: swarm_pipeline.js (100% Standalone, Zero-Global-Pollution)
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 * ============================================================================
 */

(function (window, document) {
  'use strict';

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // =========================================================================
  // 🏛️ CONSTANT CATALOGS: ANTIGRAVITY MODELS, TOOLS, FILE ACTIONS, SKILLS
  // =========================================================================

  const ANTIGRAVITY_MODELS = [
    { id: 'gemini-3.8-flash-high', name: 'Gemini 3.8 Flash (High) [RECOMMENDED]', tier: 'Flagship Deep Thinking', latency: '0.8s (Ultra-fast)', context: '1,000,000 tokens', desc: 'Flagship high-speed reasoning model with multi-step reflection and code synthesis.' },
    { id: 'gemini-3.8-flash-medium', name: 'Gemini 3.8 Flash (Medium) [THINKING]', tier: 'Balanced Thinking', latency: '0.5s (Fast)', context: '1,000,000 tokens', desc: 'Balanced high-performance thinking for complex technical workflows.' },
    { id: 'gemini-3.8-flash-low', name: 'Gemini 3.8 Flash (Low) [FAST]', tier: 'Lightweight Fast', latency: '0.2s (Instant)', context: '1,000,000 tokens', desc: 'Ultra-low latency model for high-frequency sub-task evaluation.' }
  ];

  const PROMPT_TRIGGER_TOOLS = new Set([
    'detect_hardcode',
    'audit_security',
    'audit_portability',
    'website_intelligence',
    'web_security_audit',
    'youtube_spy_video',
    'youtube_spy_transcript',
    'youtube_spy_summary',
    'youtube_spy_channel',
    'youtube_spy_comments',
    'youtube_spy_competitor_strategy',
    'youtube_audio_mixer'
  ]);

  function isPromptOrEnclaveTriggeredTool(toolId) {
    if (!toolId) return false;
    if (typeof toolId === 'string' && toolId.startsWith('fl_')) return true;
    return PROMPT_TRIGGER_TOOLS.has(toolId);
  }

  const SOVEREIGN_LOCAL_TOOLS = [
  {
    "id": "ask_question",
    "name": "ask_question",
    "category": "General",
    "desc": "Curved zero-corner decision dome and stadium choice pills for structured multiple-choice user questions.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "brain_control",
    "name": "brain_control",
    "category": "cognitive",
    "desc": "Frameless transparent neural memory synapse recall HUD and .fl_brain atomic solution vault controller.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "crypto_scanner",
    "name": "crypto_scanner",
    "category": "finance",
    "desc": "Scans cryptocurrency market metrics, 24h trading volume, price volatility, and liquidity depth for major spot and perpetual pairs.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false,
    "keywords": [
      "crypto_scanner",
      "crypto",
      "bitcoin",
      "ethereum",
      "solana",
      "trading volume",
      "volatility",
      "orderbook",
      "perpetuals"
    ],
    "tags": [
      "crypto",
      "trading",
      "volume",
      "liquidity",
      "volatility",
      "market",
      "bitcoin",
      "ethereum",
      "solana",
      "binance",
      "telemetry",
      "scanner"
    ]
  },
  {
    "id": "file_ops",
    "name": "file_ops",
    "category": "filesystem",
    "desc": "Frameless modular file operations suite featuring holographic file scanning, code forging, streaming synthesis, and visual diffs for Flowork Canvas UI.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "flow_lock",
    "name": "flow_lock",
    "category": "security",
    "desc": "Frameless octagonal cryo-vault with clamping cyber-shackle and live SHA-256 line-range telemetry for flow_lock.",
    "risk": "HIGH",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "generate_image",
    "name": "generate_image",
    "category": "visual",
    "desc": "Generate an image or edit existing images based on a text prompt. The resulting image will be saved as an artifact for use. You can use this tool to generate user interfaces and iterate on a design with the USER for an application or website that you are building. When creating UI designs, generate only the interface itself without surrounding device frames (laptops, phones, tablets, etc.) unless the user explicitly requests them. You can also use this tool to generate assets for use in an application or website.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false,
    "keywords": [
      "generate_image",
      "image generation",
      "ui mockup",
      "visual asset",
      "canvas image",
      "text to image"
    ],
    "tags": [
      "generate_image",
      "visual",
      "flowork",
      "modular",
      "zero_corner",
      "nano_plug"
    ]
  },
  {
    "id": "manage_task",
    "name": "manage_task",
    "category": "General",
    "desc": "Server blade daemon rack with 4-slot task telemetry bus (ACTION, TASK ID, STATE, STREAM) and live background task output.",
    "risk": "MODERATE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "plugin_control",
    "name": "plugin_control",
    "category": "General",
    "desc": "Notched cartridge bay HUD for managing Canvas UI plugins (list, open, close, search_remote, install) with real-time IPC and catalog telemetry.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "plugin_publish",
    "name": "plugin_publish",
    "category": "publishing",
    "desc": "Authoritatively audit, compute SHA-256 cryptographic attestation, package, and publish a Flowork Canvas plugin to the official repository and registries (plugins/plugins.json). Enforces strict preflight gatekeeper checks including mandatory category_id (CAT-001 through CAT-026).",
    "risk": "HIGH",
    "hasCss": true,
    "hasGui": false,
    "keywords": [
      "plugin_publish",
      "publish plugin",
      "plugin upload",
      "plugin registry",
      "plugin sha256"
    ],
    "tags": [
      "plugin_publish",
      "publishing",
      "flowork",
      "modular",
      "zero_corner",
      "nano_plug"
    ]
  },
  {
    "id": "read_url_content",
    "name": "read_url_content",
    "category": "network",
    "desc": "Angled parallelogram cyber data tunnel streaming HTTP TLS headers, byte size, and extracted Markdown lines for read_url_content.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "render_visual",
    "name": "render_visual",
    "category": "visual",
    "desc": "Render interactive visual widgets, charts, system pipelines, architecture diagrams, data tables, and KPI dashboards directly into the sovereign chat interface. Use this tool whenever presenting data visualizations, financial trading candles, portfolio donuts, server telemetry, system architectures, interactive tables, process logs, or multi-stage pipelines.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false,
    "keywords": [
      "render_visual",
      "data visualization",
      "charts",
      "dashboards",
      "canvas ui",
      "diagrams",
      "tables"
    ],
    "tags": [
      "render_visual",
      "visual",
      "flowork",
      "modular",
      "zero_corner",
      "nano_plug"
    ]
  },
  {
    "id": "replace_file_content",
    "name": "replace_file_content",
    "category": "filesystem",
    "desc": "Frameless dual-capsule surgical diff splicer showing real-time deletion and insertion ribbons for replace_file_content.",
    "risk": "HIGH",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "request_publish_gatekeeper",
    "name": "request_publish_gatekeeper",
    "category": "gatekeeper",
    "desc": "Trigger dedicated Security Gatekeeper Subagent to inspect and publish a tool, plugin, or skill to official Flowork registries. By doctrine, if violations exist, the Gatekeeper is FORBIDDEN from remediating files and will return a blocking Exit Code 1 report for the primary agent to fix.",
    "risk": "HIGH",
    "hasCss": true,
    "hasGui": false,
    "keywords": [
      "request_publish_gatekeeper",
      "plugin publish",
      "tool publish",
      "gatekeeper audit",
      "registry publish"
    ],
    "tags": [
      "request_publish_gatekeeper",
      "gatekeeper",
      "flowork",
      "modular",
      "zero_corner",
      "nano_plug"
    ]
  },
  {
    "id": "run_command",
    "name": "run_command",
    "category": "terminal",
    "desc": "Frameless modular terminal shell executor, command streaming telemetry, and tactical HUD bash interface for Flowork Canvas UI.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "schedule",
    "name": "schedule",
    "category": "General",
    "desc": "Octagonal chrono-reactor pod with spinning temporal dial, 5-field cron/timer matrix, and live schedule telemetry.",
    "risk": "MODERATE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "screenshot",
    "name": "screenshot",
    "category": "General",
    "desc": "Frameless optical camera viewfinder with corner brackets, laser reticle sweep, shutter flash, and real image file telemetry.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "search_tools",
    "name": "search_tools",
    "category": "registry",
    "desc": "Frameless sonar arc and high-speed horizontal chip roulette for search_tools dynamic registry discovery.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "search_web",
    "name": "search_web",
    "category": "network",
    "desc": "Frameless OSINT crosshair and live packet sniffer extracting real web citations and domains for search_web.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "send_media",
    "name": "send_media",
    "category": "General",
    "desc": "Curved zero-corner vinyl/lens orb and rounded waveform pill bars for media streaming.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "skill_control",
    "name": "skill_control",
    "category": "runtime",
    "desc": "Frameless transparent runtime SOP skill mounting HUD, tactical skill engagement card, and on-demand runbook controller.",
    "risk": "CRITICAL",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "sys_health",
    "name": "sys_health",
    "category": "diagnostics",
    "desc": "Inspect host system health, hardware resources, and runtime status. Reports platform, CPU architecture and load, RAM consumption, root disk space, and active listening ports natively with zero external shell dependencies.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false,
    "keywords": [
      "sys_health",
      "system health",
      "cpu load",
      "ram usage",
      "disk space",
      "hardware telemetry"
    ],
    "tags": [
      "sys_health",
      "diagnostics",
      "flowork",
      "modular",
      "zero_corner",
      "nano_plug"
    ]
  },
  {
    "id": "system_restart",
    "name": "system_restart",
    "category": "lifecycle",
    "desc": "Autonomously restart the Flowork engine binary to apply self-evolution changes, code fixes, binary updates, or configuration reloads. Preserves chat session state and auto-resume prompts, then gracefully restarts.",
    "risk": "CRITICAL",
    "hasCss": true,
    "hasGui": false,
    "keywords": [
      "system_restart",
      "restart",
      "reboot",
      "reload",
      "lifecycle",
      "binary update"
    ],
    "tags": [
      "system_restart",
      "lifecycle",
      "flowork",
      "modular",
      "zero_corner",
      "nano_plug"
    ]
  },
  {
    "id": "view_file",
    "name": "view_file",
    "category": "filesystem",
    "desc": "Nano-modular chat-merged inline laser file scanner and hyper-speed ghost code line streamer for view_file.",
    "risk": "SAFE",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "write_to_file",
    "name": "write_to_file",
    "category": "filesystem",
    "desc": "Nano-modular blueprint prism pod with vertical byte-fill pillar and live code materializer stream for write_to_file.",
    "risk": "HIGH",
    "hasCss": true,
    "hasGui": false
  },
  {
    "id": "team_dispatch",
    "name": "team_dispatch",
    "category": "orchestration",
    "desc": "Autonomous swarm team delegation and task dispatch across pipeline DAG cables to specialist subordinate agents.",
    "risk": "MODERATE",
    "hasCss": true,
    "hasGui": false
  }
];

  const STANDARD_TOOLS = SOVEREIGN_LOCAL_TOOLS;

  const GUARDIAN_ARCHETYPES = {
    NETWORK: 'network',
    FILESYSTEM: 'filesystem',
    TERMINAL: 'terminal',
    SUBAGENT: 'subagent',
    REVERSING: 'reversing',
    GENERAL: 'general'
  };

  function getToolArchetype(tool) {
    const tid = (tool.id || '').toLowerCase();
    const cat = (tool.category || '').toLowerCase();
    const desc = (tool.desc || '').toLowerCase();
    const combined = `${tid} ${cat} ${desc}`;

    // 1. Explicit Network / Web
    if (tid === 'read_url_content' || tid === 'search_web' || cat.includes('web') || cat.includes('recon') || cat.includes('net') || tid.includes('url') || tid.includes('http') || tid.includes('fetch') || tid.includes('domain') || tid.includes('dns') || tid.includes('browse')) {
      return GUARDIAN_ARCHETYPES.NETWORK;
    }

    // 2. Explicit Terminal / CLI
    if (tid === 'run_command' || cat.includes('terminal') || cat.includes('cli') || tid.includes('exec') || tid.includes('bash') || tid.includes('command') || tid.includes('shell')) {
      return GUARDIAN_ARCHETYPES.TERMINAL;
    }

    // 3. Auditor Council / Quality Control
    if (tid === 'team_audit' || (cat.includes('audit') && !cat.includes('security'))) {
      return GUARDIAN_ARCHETYPES.GENERAL;
    }

    // 4. Reverse Engineering / Binary Analysis
    if (cat.includes('reverse') || cat.includes('binary') || cat.includes('disasm') || cat.includes('decompile') || cat.includes('elf') || cat.includes('pe') || cat.includes('gadget') || cat.includes('rop') || cat.includes('hex')) {
      return GUARDIAN_ARCHETYPES.REVERSING;
    }

    // 5. Filesystem / Storage
    if (tid === 'view_file' || tid === 'write_to_file' || tid === 'replace_file_content' || cat.includes('filesystem') || cat.includes('file') || cat.includes('disk') || tid.includes('file') || tid.includes('dir') || tid.includes('path') || combined.includes('file content') || combined.includes('workspace file')) {
      return GUARDIAN_ARCHETYPES.FILESYSTEM;
    }

    // 6. General
    return GUARDIAN_ARCHETYPES.GENERAL;
  }

  function getDefaultGuardianForTool(tool, isLeader = false) {
    const arch = getToolArchetype(tool);
    switch (arch) {
      case GUARDIAN_ARCHETYPES.NETWORK:
        return {
          archetype: 'network',
          allowedDomains: '*',
          deniedDomains: 'localhost, 127.0.0.1, internal.lan',
          allowedProtocols: 'https, http',
          maxPayloadBytes: 10485760
        };
      case GUARDIAN_ARCHETYPES.FILESYSTEM:
        return {
          archetype: 'filesystem',
          allowedExtensions: '.js, .ts, .json, .html, .css, .md, .py, .mjs, .yaml, .txt',
          prohibitedExtensions: '.lock, .env, .pem, .key, .sh, .bash, .bin, .exe, .so',
          enforceLockAnnotations: true,
          maxFileSizeKb: 5120,
          restrictedPaths: '.git/, .flowork_brain/, /etc/'
        };
      case GUARDIAN_ARCHETYPES.TERMINAL:
        return {
          archetype: 'terminal',
          allowedCommandsPattern: '.*',
          prohibitedCommandsPattern: 'rm\\s+-rf\\s+[/~]|:\\(\\)\\s*\\{|mkfs|dd\\s+if=|shutdown|reboot',
          timeoutSeconds: 60,
          restrictedCwd: '.'
        };
      case GUARDIAN_ARCHETYPES.SUBAGENT:
        return {
          archetype: 'subagent',
          maxConcurrentSubagents: isLeader ? 10 : 3,
          allowedSubagentTypes: 'research, specialist, auditor, coder',
          maxRecursionDepth: isLeader ? 3 : 1
        };
      case GUARDIAN_ARCHETYPES.REVERSING:
        return {
          archetype: 'reversing',
          allowedBinaryFormats: 'ELF, PE, Mach-O, RAW',
          readOnlyAnalysis: true,
          symbolFilters: 'main, _start, sym.*',
          maxBinarySizeMb: 50
        };
      case GUARDIAN_ARCHETYPES.GENERAL:
      default:
        return {
          archetype: 'general',
          requireHumanConfirmation: false,
          auditTrailLogging: true,
          operationBudgetLimit: 100
        };
    }
  }

  function getNodeToolGuardian(node, tool) {
    if (!node.toolGovernance) {
      node.toolGovernance = {
        allowAll: true,
        allowedTools: SOVEREIGN_LOCAL_TOOLS.map(t => t.id),
        deniedTools: [],
        toolGuardians: {}
      };
    }
    if (!node.toolGovernance.toolGuardians) {
      node.toolGovernance.toolGuardians = {};
    }
    if (!node.toolGovernance.toolGuardians[tool.id]) {
      node.toolGovernance.toolGuardians[tool.id] = getDefaultGuardianForTool(tool, !!node.isLocked);
    }
    return node.toolGovernance.toolGuardians[tool.id];
  }

  function renderGuardianDrawerHtml(tool, guardian, node, allNodes = []) {
    const arch = guardian.archetype || getToolArchetype(tool);
    const otherNodes = (allNodes || []).filter(n => n.id !== node.id);
    const cloneOptionsHtml = otherNodes.map(n => `<option value="${n.id}">${n.role || n.id}</option>`).join('');

    let formFieldsHtml = '';

    if (arch === 'network') {
      formFieldsHtml = `
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>✓ Allowed Domains Whitelist (Comma-separated, '*' for all)</label>
            <input type="text" class="guardian-input" data-tool-id="${tool.id}" data-field="allowedDomains" value="${guardian.allowedDomains ?? '*'}" placeholder="e.g. floworkos.com, github.com, api.openai.com" />
            <div class="guardian-hint">Only HTTP/HTTPS network traffic to whitelisted hostnames will be permitted for ${node.role || node.id}.</div>
          </div>
          <div class="guardian-field">
            <label style="color:#f43f5e;">✕ Prohibited Domains Blacklist (Comma-separated)</label>
            <input type="text" class="guardian-input danger" data-tool-id="${tool.id}" data-field="deniedDomains" value="${guardian.deniedDomains ?? 'localhost, 127.0.0.1, internal.lan'}" placeholder="e.g. localhost, 127.0.0.1, internal.lan" />
            <div class="guardian-hint">Strictly blocks outbound network requests and SSRF attack vectors.</div>
          </div>
        </div>
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>Permissible Protocols</label>
            <input type="text" class="guardian-input" data-tool-id="${tool.id}" data-field="allowedProtocols" value="${guardian.allowedProtocols ?? 'https, http'}" placeholder="https, http" />
          </div>
          <div class="guardian-field">
            <label>Max Payload Ingress / Egress (Bytes)</label>
            <input type="number" class="guardian-input" data-tool-id="${tool.id}" data-field="maxPayloadBytes" value="${guardian.maxPayloadBytes ?? 10485760}" min="1024" max="104857600" />
          </div>
        </div>
      `;
    } else if (arch === 'filesystem') {
      formFieldsHtml = `
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>✓ Permissible File Extensions</label>
            <input type="text" class="guardian-input" data-tool-id="${tool.id}" data-field="allowedExtensions" value="${guardian.allowedExtensions ?? '.js, .ts, .json, .html, .css, .md, .py, .mjs, .yaml, .txt'}" />
            <div class="guardian-hint">File extension scope permitted for file modifications by ${node.role || node.id}.</div>
          </div>
          <div class="guardian-field">
            <label style="color:#f43f5e;">✕ Quarantined File Extensions</label>
            <input type="text" class="guardian-input danger" data-tool-id="${tool.id}" data-field="prohibitedExtensions" value="${guardian.prohibitedExtensions ?? '.lock, .env, .pem, .key, .sh, .bash, .bin, .exe, .so'}" />
            <div class="guardian-hint">Modifications to quarantined file formats will immediately trip the circuit breaker.</div>
          </div>
        </div>
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>Restricted Directory Paths (Prefix Quarantine)</label>
            <input type="text" class="guardian-input" data-tool-id="${tool.id}" data-field="restrictedPaths" value="${guardian.restrictedPaths ?? '.git/, .flowork_brain/, /etc/'}" />
          </div>
          <div class="guardian-field">
            <label>Max File Payload Size (KB)</label>
            <input type="number" class="guardian-input" data-tool-id="${tool.id}" data-field="maxFileSizeKb" value="${guardian.maxFileSizeKb ?? 5120}" min="10" max="500000" />
          </div>
        </div>
        <div class="guardian-checkbox-row">
          <label class="pipeline-switch" style="transform: scale(0.8); margin:0;">
            <input type="checkbox" class="guardian-switch-input" data-tool-id="${tool.id}" data-field="enforceLockAnnotations" ${guardian.enforceLockAnnotations !== false ? 'checked' : ''} />
            <span class="pipeline-slider"></span>
          </label>
          <span style="font-size:11px; font-weight:700; color:#cbd5e1;">🔒 Strictly Enforce Sanctity of @lock and @freez source code comments</span>
        </div>
      `;
    } else if (arch === 'terminal') {
      formFieldsHtml = `
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>✓ Permissible Command Regex Pattern</label>
            <input type="text" class="guardian-input" data-tool-id="${tool.id}" data-field="allowedCommandsPattern" value="${guardian.allowedCommandsPattern ?? '.*'}" placeholder=".*" />
            <div class="guardian-hint">Regex pattern validating terminal commands before execution.</div>
          </div>
          <div class="guardian-field">
            <label style="color:#f43f5e;">✕ Prohibited Dangerous Command Pattern (Regex)</label>
            <input type="text" class="guardian-input danger" data-tool-id="${tool.id}" data-field="prohibitedCommandsPattern" value="${guardian.prohibitedCommandsPattern ?? 'rm\\s+-rf\\s+[/~]|:\\(\\)\\s*\\{|mkfs|dd\\s+if=|shutdown|reboot'}" />
            <div class="guardian-hint">Destructive shell patterns blocked immediately with execution refusal.</div>
          </div>
        </div>
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>Command SLA Timeout (Seconds)</label>
            <input type="number" class="guardian-input" data-tool-id="${tool.id}" data-field="timeoutSeconds" value="${guardian.timeoutSeconds ?? 60}" min="5" max="3600" />
          </div>
          <div class="guardian-field">
            <label>Restricted Working Directory (CWD Sandbox)</label>
            <input type="text" class="guardian-input" data-tool-id="${tool.id}" data-field="restrictedCwd" value="${guardian.restrictedCwd ?? './'}" />
          </div>
        </div>
      `;
    } else if (arch === 'subagent') {
      formFieldsHtml = `
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>Max Concurrent Subagents</label>
            <input type="number" class="guardian-input" data-tool-id="${tool.id}" data-field="maxConcurrentSubagents" value="${guardian.maxConcurrentSubagents ?? (node.isLocked ? 10 : 3)}" min="1" max="50" />
            <div class="guardian-hint">Controls fan-out concurrency to prevent runaway token usage.</div>
          </div>
          <div class="guardian-field">
            <label>Permissible Subagent Types (Comma-separated)</label>
            <input type="text" class="guardian-input" data-tool-id="${tool.id}" data-field="allowedSubagentTypes" value="${guardian.allowedSubagentTypes ?? 'research, specialist, auditor, coder'}" />
            <div class="guardian-hint">Subagent persona archetypes this agent is authorized to spawn.</div>
          </div>
        </div>
        <div class="guardian-field">
          <label>Max Subagent Recursion Depth</label>
          <input type="number" class="guardian-input" data-tool-id="${tool.id}" data-field="maxRecursionDepth" value="${guardian.maxRecursionDepth ?? (node.isLocked ? 3 : 1)}" min="1" max="5" style="max-width:300px;" />
        </div>
      `;
    } else if (arch === 'reversing') {
      formFieldsHtml = `
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>Allowed Binary Architectures / Formats</label>
            <input type="text" class="guardian-input" data-tool-id="${tool.id}" data-field="allowedBinaryFormats" value="${guardian.allowedBinaryFormats ?? 'ELF, PE, Mach-O, RAW'}" />
          </div>
          <div class="guardian-field">
            <label>Symbol / Function Filter Patterns</label>
            <input type="text" class="guardian-input" data-tool-id="${tool.id}" data-field="symbolFilters" value="${guardian.symbolFilters ?? 'main, _start, sym.*'}" />
          </div>
        </div>
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>Max Binary Target Size (MB)</label>
            <input type="number" class="guardian-input" data-tool-id="${tool.id}" data-field="maxBinarySizeMb" value="${guardian.maxBinarySizeMb ?? 50}" min="1" max="1000" />
          </div>
          <div class="guardian-field" style="justify-content:center;">
            <div class="guardian-checkbox-row">
              <label class="pipeline-switch" style="transform: scale(0.8); margin:0;">
                <input type="checkbox" class="guardian-switch-input" data-tool-id="${tool.id}" data-field="readOnlyAnalysis" ${guardian.readOnlyAnalysis !== false ? 'checked' : ''} />
                <span class="pipeline-slider"></span>
              </label>
              <span style="font-size:11px; font-weight:700; color:#cbd5e1;">Strict Read-Only Analysis</span>
            </div>
          </div>
        </div>
      `;
    } else {
      // General / Intelligence / Finance
      formFieldsHtml = `
        <div class="guardian-field-row">
          <div class="guardian-field">
            <label>Max Operations Budget Limit (Per Session)</label>
            <input type="number" class="guardian-input" data-tool-id="${tool.id}" data-field="operationBudgetLimit" value="${guardian.operationBudgetLimit ?? 100}" min="1" max="10000" />
            <div class="guardian-hint">Upper limit of consecutive operations allowed before mandatory validation.</div>
          </div>
          <div class="guardian-field" style="display:flex; flex-direction:column; justify-content:center; gap:8px;">
            <div class="guardian-checkbox-row">
              <label class="pipeline-switch" style="transform: scale(0.8); margin:0;">
                <input type="checkbox" class="guardian-switch-input" data-tool-id="${tool.id}" data-field="requireHumanConfirmation" ${guardian.requireHumanConfirmation ? 'checked' : ''} />
                <span class="pipeline-slider"></span>
              </label>
              <span style="font-size:11px; font-weight:700; color:#cbd5e1;">Require Super Admin Human Confirmation</span>
            </div>
            <div class="guardian-checkbox-row">
              <label class="pipeline-switch" style="transform: scale(0.8); margin:0;">
                <input type="checkbox" class="guardian-switch-input" data-tool-id="${tool.id}" data-field="auditTrailLogging" ${guardian.auditTrailLogging !== false ? 'checked' : ''} />
                <span class="pipeline-slider"></span>
              </label>
              <span style="font-size:11px; font-weight:700; color:#cbd5e1;">Enable Full Audit Trail Telemetry</span>
            </div>
          </div>
        </div>
      `;
    }

    return `
      <tr class="pipeline-guardian-drawer-row collapsed" id="guardian-drawer-${tool.id}" data-tool-id="${tool.id}">
        <td colspan="5">
          <div class="pipeline-guardian-drawer-content">
            <div class="guardian-drawer-header">
              <div class="guardian-drawer-title">
                <span>🛡️</span>
                <span>Guardian Sandbox Policy for <code style="color:#00f2fe; font-size:11.5px;">${tool.id}</code></span>
                <span class="guardian-arch-pill">${arch.toUpperCase()} ARCHETYPE</span>
                <span style="font-size:10px; color:#10b981; font-weight:700; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); padding:1px 6px; border-radius:4px;">
                  Agent ID: ${node.id} (${node.role || 'Agent'})
                </span>
              </div>
              <div class="guardian-drawer-actions">
                <button type="button" class="guardian-mini-btn btn-reset-guardian" data-tool-id="${tool.id}" title="Reset to standard default policy">↺ Reset Default</button>
                ${otherNodes.length > 0 ? `
                  <select class="guardian-mini-btn sel-clone-guardian" data-tool-id="${tool.id}" style="cursor:pointer; background:rgba(15,23,42,0.9); outline:none;">
                    <option value="">📋 Clone Policy from...</option>
                    ${cloneOptionsHtml}
                  </select>
                ` : ''}
              </div>
            </div>
            <div class="guardian-form-grid">
              ${formFieldsHtml}
            </div>
          </div>
        </td>
      </tr>
    `;
  }


  const DEFAULT_LOCAL_SKILLS = [
    { id: 'ui_ux_pro_max', name: 'UI / UX Pro Max', origin: 'Local Skills', category: 'Frontend & Design', desc: 'Pixel-perfect UI design, responsive layouts, WCAG compliance, and modern CSS/JS polish.' },
    { id: 'antigravity_guide', name: 'Antigravity Guide & Reference', origin: 'Local Skills', category: 'Antigravity Core', desc: 'Complete architectural reference, CLI commands, SDK integration, and runtime configs.' },
    { id: 'agy_customizations', name: 'Antigravity Customizations', origin: 'Local Skills', category: 'Antigravity Core', desc: 'Extensibility reference for skills, rules, hooks, sidecars, and MCP server management.' },
    { id: 'generative_ui', name: 'Generative UI & Widgets', origin: 'Local Skills', category: 'Visualization', desc: 'Inline interactive HTML widgets, visual artifacts, dynamic dashboards, and charts.' },
    { id: 'permissioned_github', name: 'Permissioned GitHub Ops', origin: 'Local Skills', category: 'DevOps & Git', desc: 'Automated GitHub branch isolation, pull request creation, and co-author compliance.' },
    { id: 'migrate_workflows', name: 'Migrate Workflows', origin: 'Local Skills', category: 'Migration', desc: 'Scan legacy workflow scripts and migrate them into modular SKILL.md packages.' },
    { id: 'automation', name: 'End-to-End Automation', origin: 'Local Skills', category: 'Automation', desc: 'Headless automation scripts, recurring pipelines, and event-driven swarm jobs.' },
    { id: 'plugin', name: 'Nano-Plug Architecture', origin: 'Local Skills', category: 'Extensibility', desc: '1-file 1-logic modular nano-plugins with manifest contracts and multi-OS portability.' }
  ];

  let DYNAMIC_LOCAL_SKILLS = [...DEFAULT_LOCAL_SKILLS];

  const SOVEREIGN_MULTIDOMAIN_TRIGGERS = [
    {
      id: 'market_tick_sensor',
      name: 'Forex / Crypto Market Sensor',
      domain: 'Forex / Quant Finance',
      icon: '📈',
      description: 'Real-time FX & Crypto volatility, price breakout, spread spikes, and technical indicator sensor.',
      triggerConfig: {
        ingressType: 'market_tick',
        channel: 'EURUSD, XAUUSD, BTCUSDT',
        symbol: 'EURUSD, XAUUSD, BTCUSDT',
        threshold: 'Spread <= 1.2 pips && RSI < 30',
        conditionExpr: 'payload.spread <= 1.2 && payload.rsi < 30',
        samplePayload: JSON.stringify({
          symbol: "EURUSD",
          bid: 1.0848,
          ask: 1.0850,
          spread: 0.2,
          rsi: 28.4,
          volatility: "HIGH",
          timeframe: "M15",
          signal: "OVERSOLD_REVERSAL"
        }, null, 2)
      }
    },
    {
      id: 'webhook_ingress',
      name: 'Webhook Ingress Gateway',
      domain: 'Universal / API Ingress',
      icon: '⚡',
      description: 'HTTP POST listener (:19890/api/webhook) for TradingView alerts, Stripe events, GitHub, and Telegram.',
      triggerConfig: {
        ingressType: 'webhook',
        channel: '/api/webhook/pipeline',
        method: 'POST',
        authMode: 'bearer_token',
        conditionExpr: 'payload.event != null',
        samplePayload: JSON.stringify({
          event: "ORDER_SIGNAL",
          pair: "EURUSD",
          signal: "BUY",
          price: 1.0845,
          tp: 1.0920,
          sl: 1.0810,
          confidence: 0.94
        }, null, 2)
      }
    },
    {
      id: 'file_watcher',
      name: 'Document & File Observer',
      domain: 'Corporate Law / Data / Research',
      icon: '📁',
      description: 'Watches incoming contracts, CSVs, PDF briefs, or financial tick data in local directory.',
      triggerConfig: {
        ingressType: 'file_watcher',
        channel: 'vault/incoming/',
        watchPath: 'vault/incoming/',
        patterns: '*.pdf, *.docx, *.csv',
        conditionExpr: 'payload.file_size_kb > 0 && !payload.file_name.startsWith(".")',
        samplePayload: JSON.stringify({
          event: "FILE_CREATED",
          file_name: "Master_Service_Agreement_2026.pdf",
          path: "vault/incoming/Master_Service_Agreement_2026.pdf",
          mime: "application/pdf",
          file_size_kb: 412,
          jurisdiction: "International Commercial Law"
        }, null, 2)
      }
    },
    {
      id: 'chat_ingress',
      name: 'Client Consultation Intake',
      domain: 'Psychology / Advisory / Support',
      icon: '💬',
      description: 'Listens for inbound client messages, intake consultation forms, patient notes, or priority triage tickets.',
      triggerConfig: {
        ingressType: 'chat_ingress',
        channel: 'web_portal_intake',
        source: 'web_portal',
        category: 'intake_consultation',
        conditionExpr: 'payload.urgency >= 3 || payload.sentiment === "distressed"',
        samplePayload: JSON.stringify({
          client_id: "CL-908",
          intake_form: "Initial Clinical Assessment",
          urgency: 4,
          primary_concern: "acute cognitive fatigue & burnout",
          session_type: "CBT",
          preferred_specialist: "Psychologist Agent"
        }, null, 2)
      }
    },
    {
      id: 'cron_scheduler',
      name: 'Autonomous Chrono Scheduler',
      domain: 'Universal / Timing',
      icon: '⏰',
      description: 'Scheduled recurring cron ticks (1m, 5m, 1h, daily audits, market opening Bell).',
      triggerConfig: {
        ingressType: 'cron',
        channel: '*/5 * * * * (every 5 minutes)',
        interval: '5m',
        cronExpr: '*/5 * * * *',
        conditionExpr: 'payload.is_active === true',
        samplePayload: JSON.stringify({
          tick_id: "cron-0042",
          timestamp: new Date().toISOString(),
          interval: "5m",
          is_active: true,
          target: "periodic_market_and_compliance_audit"
        }, null, 2)
      }
    },
    {
      id: 'security_sentinel',
      name: 'System Sentinel & Safety Guard',
      domain: 'Engineering / Infrastructure',
      icon: '🛡️',
      description: 'Monitors system health, memory anomalies, circuit breaker trips, and error threshold spikes.',
      triggerConfig: {
        ingressType: 'system_sentinel',
        channel: 'system_resource_guard',
        metrics: 'memory_rss, api_error_rate',
        conditionExpr: 'payload.error_rate > 0.05 || payload.memory_percent > 85',
        samplePayload: JSON.stringify({
          alert_level: "WARNING",
          metric: "memory_rss",
          memory_percent: 88,
          error_rate: 0.01,
          source: "worker_cluster_0"
        }, null, 2)
      }
    }
  ];

  const DEFAULT_SWARM_PRESETS = {
    default: {
      id: 'default',
      name: 'Default Sovereign Swarm',
      icon: '⚡',
      domain: 'Core Orchestration',
      description: 'Pristine sovereign foundation with Mr. Flow at executive command.',
      panX: 40,
      panY: 40,
      scale: 1.0,
      nodes: [
        {
          id: 'node-mrflow',
          agentId: 'mr.flow',
          name: 'Mr. Flow',
          role: 'Grand Chief AI Overseer & Executive Architect',
          icon: '⚡',
          type: 'agent',
          x: 450,
          y: 240,
          taskPrompt: 'Executive architecture, system supervision, and autonomous orchestration.',
          rulePrompt: 'Enforce zero-trust and empirical proof (Exit Code 0).',
          modelConfig: {
            accountMode: 'combo',
            modelId: 'gemini-3.8-flash-high',
            modelName: 'Gemini 3.8 Flash (High)',
            provider: 'google',
            temperature: 0.2
          },
          toolGovernance: {
            allowAll: true,
            allowedTools: [],
            deniedTools: []
          }
        }
      ],
      connections: []
    }  };

  class SwarmPipelineEngine {
    constructor() {
      this.container = null;
      this.boardEl = null;
      this.svgLayer = null;
      this.nodesLayer = null;
      this.inspectorEl = null; // Right bar removed per instruction

      // Persistence, Presets & Dynamic Discovery
      this.STORAGE_KEY = 'flowork_swarm_pipeline_dag_v1';
      this.PRESETS_STORAGE_KEY = 'flowork_swarm_presets_v1';
      this.ACTIVE_PRESET_KEY = 'flowork_swarm_active_preset_id';
      this._saveTimer = null;
      this.activePresetId = 'default';
      this.presets = {};
      this.dynamicAgents = [];
      this.dynamicTriggers = [];

      this.nodes = [];
      this.connections = [];
      this.selectedNodeId = null;
      this.availableTools = SOVEREIGN_LOCAL_TOOLS;
      this.dockFilter = 'all';
      this.dockSearchQuery = '';
      this.selectedConnId = null;
      this.activeSubtab = 'boardroom';
      this.activeModalNode = null;

      // Pan & Zoom
      this.panX = 40;
      this.panY = 40;
      this.scale = 1.0;
      this.isPanning = false;
      this.panStartX = 0;
      this.panStartY = 0;

      // Node Dragging
      this.draggedNode = null;
      this.dragOffsetX = 0;
      this.dragOffsetY = 0;

      // Wire Drawing
      this.isWiring = false;
      this.wireStartNodeId = null;
      this.wireStartPort = 'out-1';
      this.activeWireEl = null;

      // Real-Time Discovery Caching & Timers
      this._lastAgentsHash = null;
      this._triggersRendered = false;
      this._rosterPollTimer = null;
      this._boundBeforeUnload = null;
      this._boundWindowFocus = null;

      // Global bounds
      this._boundOnMouseMove = this._onMouseMove.bind(this);
      this._boundOnMouseUp = this._onMouseUp.bind(this);
      this._boundOnKeyDown = this._onKeyDown.bind(this);
    }

    /**
     * Mounts the pipeline inside the specified container
     */
    mount(container) {
      if (!container) return;
      this.container = container;
      this.container.innerHTML = '';

      // Chat is strictly forbidden in Swarm Pipeline (exclusive to 3D Studio)
      const rightbar = document.getElementById('rightbar-chat');
      if (rightbar) rightbar.style.setProperty('display', 'none', 'important');
      const resizer = document.getElementById('resizer-right');
      if (resizer) resizer.style.setProperty('display', 'none', 'important');
      document.querySelector('.canvas-layout')?.classList.add('pipeline-active');

      this._buildLayout();
      this._initDefaultNodes();
      this._bindGlobalEvents();
      this.render();
      this.loadDynamicRoster(); // Real-time discovery of Triggers and Agents only
      this.syncServerDag();

      // Auto-poll subagents every 2.5s to detect additions or deletions on disk dynamically!
      if (this._rosterPollTimer) clearInterval(this._rosterPollTimer);
      this._rosterPollTimer = setInterval(() => {
        if (!document.hidden) {
          this.loadDynamicRoster(true);
        }
      }, 2500);

      console.log('[SwarmPipeline] ⚡ Flowork Swarm Pipeline Engine mounted (Dynamic Disk Roster & Zero Hardcoding).');
    }

    unmount() {
      if (this._rosterPollTimer) {
        clearInterval(this._rosterPollTimer);
        this._rosterPollTimer = null;
      }
      this.saveState();
    }

    /**
     * Builds the Cockpit HTML layout:
     * - Left Bar: Only Agent and Trigger
     * - Center: Canvas Board (Full Width, Toolbar Removed per user directive)
     * - Right Bar: REMOVED COMPLETELY
     */
    _buildLayout() {
      this.container.classList.add('swarm-pipeline-container', 'group-subview-pane');

      // 1. Left Zone: Palette Sidebar (Triggers & Agents only)
      const palette = document.createElement('aside');
      palette.className = 'pipeline-palette-sidebar';
      palette.innerHTML = `
        <div class="palette-header">
          <h3>⚡ Swarm Palette</h3>
          <div style="display:flex; align-items:center; gap:6px;">
            <button type="button" class="palette-refresh-btn" id="btn-palette-refresh-all" title="Refresh Triggers & Agents from disk">🔄</button>
            <span style="font-size:10px; color:#64748b;">Plug & Play</span>
          </div>
        </div>
        <div class="palette-scroll-content">
          <!-- 1. Triggers First (Ingress Gateway) -->
          <div style="margin-bottom:16px;">
            <div class="palette-category-title" style="display:flex; justify-content:space-between; align-items:center;">
              <span>⚡ Triggers (Ingress)</span>
              <span id="palette-trigger-count" style="font-size:9.5px; color:#00f2fe; font-weight:700;"></span>
            </div>
            <div class="palette-items-grid" id="palette-triggers-list">
              <div style="color:#64748b; font-size:10px; padding:8px 4px;">Loading triggers...</div>
            </div>
          </div>

          <!-- 2. Agents (Specialists & Executives) -->
          <div>
            <div class="palette-category-title" style="display:flex; justify-content:space-between; align-items:center;">
              <span>🤖 Agents & Specialists</span>
              <span id="palette-agent-count" style="font-size:9.5px; color:#38bdf8; font-weight:700;"></span>
            </div>
            <div class="palette-items-grid" id="palette-agents-list">
              <div style="color:#64748b; font-size:10px; padding:8px 4px;">Loading agents...</div>
            </div>
          </div>
        </div>
      `;

      // 2. Center Zone: Infinite DAG Canvas Board (Full Width, Clean Canvas without Toolbar Clutter)
      const board = document.createElement('main');
      board.className = 'pipeline-canvas-board pipeline-board';
      board.innerHTML = `
        <div class="pipeline-floating-status">
          <span class="pipeline-status-badge" id="pipeline-active-preset-badge">📈 Forex & Quant Trading</span>
          <span class="pipeline-save-indicator" id="pipeline-save-indicator">💾 Auto-Saved</span>
        </div>

        <svg class="pipeline-svg-layer" id="pipeline-svg-layer">
          <defs>
            <filter id="glow-emerald" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>
        </svg>
        <div class="pipeline-nodes-layer" id="pipeline-nodes-layer"></div>

        <div class="pipeline-floating-hud">
          <div class="pipeline-hud-preset-group">
            <select class="pipeline-hud-select" id="pipeline-preset-selector" title="Switch Domain Preset">
            </select>
            <button type="button" class="pipeline-hud-btn" id="btn-pipe-save-preset" title="Save Preset Snapshot">💾 Save</button>
            <button type="button" class="pipeline-hud-btn" id="btn-pipe-new-preset" title="Create New Custom Preset">➕ New</button>
          </div>
          <div style="width: 1px; height: 18px; background: rgba(255,255,255,0.15); margin: 0 4px;"></div>
          <button type="button" class="pipeline-hud-btn" id="btn-pipe-auto-layout" title="Auto-Arrange DAG (Clean Non-Overlapping Layout)">✨ Auto Arrange</button>
          <button type="button" class="pipeline-hud-btn" id="btn-pipe-reset-squad" title="Reset Preset to Pristine Squad">🔄 Reset Squad</button>
          <button type="button" class="pipeline-hud-btn" id="btn-pipe-center" title="Center Canvas View">🎯 Center</button>
          <button type="button" class="pipeline-hud-btn danger" id="btn-pipe-clear-all" title="Clear All Nodes from Canvas">🗑️ Clear All</button>
          <button type="button" class="pipeline-hud-btn primary" id="btn-pipe-run" title="Execute Active Swarm Signal Flow">⚡ Run Pipeline</button>
        </div>
      `;

      this.container.appendChild(palette);
      this.container.appendChild(board);
      // Right bar is completely removed per user instruction!

      this.boardEl = board;
      this.svgLayer = board.querySelector('#pipeline-svg-layer');
      this.nodesLayer = board.querySelector('#pipeline-nodes-layer');
      this.inspectorEl = null;

      palette.querySelector('#btn-palette-refresh-all')?.addEventListener('click', () => {
        this.loadDynamicRoster();
      });

      this._bindToolbarEvents(board);
      this._bindBoardCanvasEvents(board);
    }

    /**
     * Initializes default nodes or restores from localStorage
     */
    _initDefaultNodes() {
      this.initPresets();

      if (this.loadSavedState()) {
        this.populatePresetDropdown();
        this.updateStatusBadge();
        return;
      }

      // If no saved state, load the active preset (default: default)
      this.loadPreset(this.activePresetId, false);
      this.populatePresetDropdown();
      this.updateStatusBadge();
    }

    /**
     * Initializes default and custom presets
     */
    initPresets() {
      // 1. Start with pristine default presets
      this.presets = JSON.parse(JSON.stringify(DEFAULT_SWARM_PRESETS));

      // 2. Load stored presets if any
      try {
        const raw = localStorage.getItem(this.PRESETS_STORAGE_KEY);
        if (raw) {
          const stored = JSON.parse(raw);
          if (stored && typeof stored === 'object') {
            for (const [id, preset] of Object.entries(stored)) {
              if (preset && preset.nodes) {
                this.presets[id] = preset;
              }
            }
          }
        }
      } catch (err) {
        console.warn('[SwarmPipeline] Error reading presets storage:', err);
      }

      // 3. Determine active preset ID
      try {
        const savedActive = localStorage.getItem(this.ACTIVE_PRESET_KEY);
        if (savedActive && this.presets[savedActive]) {
          this.activePresetId = savedActive;
        } else if (!this.presets[this.activePresetId]) {
          this.activePresetId = 'default';
        }
      } catch (e) {
        this.activePresetId = 'default';
      }

      return this.presets;
    }

    /**
     * Populates the Floating HUD Preset Dropdown
     */
    populatePresetDropdown() {
      const select = this.boardEl?.querySelector('#pipeline-preset-selector');
      if (!select) return;

      select.innerHTML = '';
      for (const preset of Object.values(this.presets)) {
        const opt = document.createElement('option');
        opt.value = preset.id;
        opt.textContent = `${preset.icon || '📦'} ${preset.name || preset.id}`;
        if (preset.id === this.activePresetId) {
          opt.selected = true;
        }
        select.appendChild(opt);
      }
    }

    /**
     * Updates Floating Status Badge with active domain information
     */
    updateStatusBadge(customText = null) {
      const badge = this.boardEl?.querySelector('#pipeline-active-preset-badge');
      if (!badge) return;

      if (customText) {
        badge.textContent = customText;
        return;
      }

      const active = this.presets[this.activePresetId] || DEFAULT_SWARM_PRESETS[this.activePresetId];
      if (active) {
        badge.textContent = `${active.icon || '📦'} ${active.name || this.activePresetId}`;
      } else {
        badge.textContent = `⚡ ${this.activePresetId}`;
      }
    }

    /**
     * Loads a specific preset into the DAG canvas
     */
    loadPreset(presetId, autoSave = true) {
      if (!this.presets[presetId] && DEFAULT_SWARM_PRESETS[presetId]) {
        this.presets[presetId] = JSON.parse(JSON.stringify(DEFAULT_SWARM_PRESETS[presetId]));
      }

      const target = this.presets[presetId];
      if (!target) return false;

      this.activePresetId = presetId;
      this.selectedNodeId = null;
      this.selectedConnId = null;

      this.nodes = JSON.parse(JSON.stringify(target.nodes || []));
      this.connections = JSON.parse(JSON.stringify(target.connections || []));
      this.connections.forEach(c => {
        if (c.guardianEnabled === undefined) c.guardianEnabled = true;
      });

      if (target.panX !== undefined) this.panX = target.panX;
      if (target.panY !== undefined) this.panY = target.panY;
      if (target.scale !== undefined) this.scale = target.scale;

      this.nodes.forEach(n => this._ensureNodeStructures(n));

      this.populatePresetDropdown();
      this.updateStatusBadge();
      this.render();

      if (autoSave) {
        this.saveState(true);
      }

      // Notify 3D Office and system listeners that active squad has changed
      try {
        window.dispatchEvent(new CustomEvent('flowork:preset-changed', {
          detail: { presetId, preset: target }
        }));
        window.dispatchEvent(new CustomEvent('flowork:swarm-dag-updated', {
          detail: { nodes: target.nodes }
        }));
        fetch('/api/swarmflow/active', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ activePresetId: presetId })
        }).catch(() => {});
      } catch (_) {}

      return true;
    }

    /**
     * Switches to another preset, auto-saving outgoing canvas first
     */
    switchPreset(presetId) {
      if (!presetId) return;
      if (presetId === this.activePresetId && this.nodes && this.nodes.length > 0) return;

      // 1. Snapshot outgoing active preset state
      if (this.presets[this.activePresetId]) {
        this.presets[this.activePresetId].nodes = JSON.parse(JSON.stringify(this.nodes));
        this.presets[this.activePresetId].connections = JSON.parse(JSON.stringify(this.connections));
        this.presets[this.activePresetId].panX = this.panX;
        this.presets[this.activePresetId].panY = this.panY;
        this.presets[this.activePresetId].scale = this.scale;
        this.presets[this.activePresetId].updatedAt = Date.now();
      }

      // 2. Load incoming preset
      this.loadPreset(presetId, true);

      // 3. Visual notification indicator
      const indicator = this.boardEl?.querySelector('#pipeline-save-indicator');
      if (indicator) {
        const curr = this.presets[presetId];
        indicator.textContent = `⚡ Switched to ${curr?.name || presetId}`;
        indicator.classList.remove('save-indicator-flash');
        void indicator.offsetWidth;
        indicator.classList.add('save-indicator-flash');
      }
    }

    /**
     * Explicitly saves current preset modifications
     */
    saveCurrentPreset() {
      if (this.presets[this.activePresetId]) {
        this.presets[this.activePresetId].nodes = JSON.parse(JSON.stringify(this.nodes));
        this.presets[this.activePresetId].connections = JSON.parse(JSON.stringify(this.connections));
        this.presets[this.activePresetId].panX = this.panX;
        this.presets[this.activePresetId].panY = this.panY;
        this.presets[this.activePresetId].scale = this.scale;
        this.presets[this.activePresetId].updatedAt = Date.now();
      }

      this.saveState(true);

      const indicator = this.boardEl?.querySelector('#pipeline-save-indicator');
      if (indicator) {
        const curr = this.presets[this.activePresetId];
        indicator.textContent = `💾 Preset Saved [${curr?.name || this.activePresetId}]`;
        indicator.classList.remove('save-indicator-flash');
        void indicator.offsetWidth;
        indicator.classList.add('save-indicator-flash');
      }
    }

    /**
     * Creates a new custom preset cloned from the current canvas
     */
    createNewPreset() {
      const name = window.prompt('Enter a title for the new preset (e.g. Crypto Arbitrage, SEO Content Engine):');
      if (!name || !name.trim()) return;

      const cleanName = name.trim();
      const id = 'custom_' + cleanName.toLowerCase().replace(/[^a-z0-9]+/g, '_') + '_' + Date.now().toString(36);

      const newPreset = {
        id,
        name: cleanName,
        icon: '✨',
        domain: 'Custom Swarm Domain',
        description: `Custom sovereign pipeline preset: ${cleanName}`,
        panX: this.panX,
        panY: this.panY,
        scale: this.scale,
        nodes: JSON.parse(JSON.stringify(this.nodes)),
        connections: JSON.parse(JSON.stringify(this.connections)),
        createdAt: Date.now(),
        updatedAt: Date.now()
      };

      this.presets[id] = newPreset;
      this.activePresetId = id;
      this.populatePresetDropdown();
      this.updateStatusBadge();
      this.saveState(true);

      const indicator = this.boardEl?.querySelector('#pipeline-save-indicator');
      if (indicator) {
        indicator.textContent = `✨ Created Preset [${cleanName}]`;
        indicator.classList.remove('save-indicator-flash');
        void indicator.offsetWidth;
        indicator.classList.add('save-indicator-flash');
      }
    }

    /**
     * Auto-Save DAG State to Persistent Storage
     */
    saveState(syncToServer = true) {
      try {
        // 1. Always keep current preset in sync in memory
        if (this.presets && this.activePresetId && this.presets[this.activePresetId]) {
          this.presets[this.activePresetId].nodes = JSON.parse(JSON.stringify(this.nodes));
          this.presets[this.activePresetId].connections = JSON.parse(JSON.stringify(this.connections));
          this.presets[this.activePresetId].panX = this.panX;
          this.presets[this.activePresetId].panY = this.panY;
          this.presets[this.activePresetId].scale = this.scale;
          this.presets[this.activePresetId].updatedAt = Date.now();
        }

        const state = {
          version: '2026.10.18.clean',
          timestamp: Date.now(),
          activePresetId: this.activePresetId,
          presets: this.presets,
          panX: this.panX,
          panY: this.panY,
          scale: this.scale,
          nodes: this.nodes,
          connections: this.connections
        };

        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(state));
        localStorage.setItem(this.PRESETS_STORAGE_KEY, JSON.stringify(this.presets));
        localStorage.setItem(this.ACTIVE_PRESET_KEY, this.activePresetId);

        if (syncToServer) {
          // Sync DAG & Cable Guardian switches directly to disk via backend API
          fetch('/api/pipeline/dag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state)
          }).catch(() => {});
        }

        const indicator = this.boardEl?.querySelector('#pipeline-save-indicator');
        if (indicator) {
          const curr = this.presets?.[this.activePresetId];
          const presetLabel = curr?.name ? ` [${curr.name}]` : '';
          indicator.textContent = `💾 Auto-Saved${presetLabel} ${new Date().toLocaleTimeString('en-US')}`;
          indicator.classList.remove('save-indicator-flash');
          void indicator.offsetWidth;
          indicator.classList.add('save-indicator-flash');
        }

        try {
          window.dispatchEvent(new CustomEvent('flowork:swarm-dag-updated', {
            detail: { nodes: this.nodes }
          }));
        } catch (_) {}
      } catch (err) {
        console.error('[SwarmPipeline] Auto-Save error:', err);
      }
    }

    debouncedSave(delay = 400) {
      if (this._saveTimer) clearTimeout(this._saveTimer);
      this._saveTimer = setTimeout(() => {
        this.saveState();
      }, delay);
    }

    loadSavedState() {
      try {
        const raw = localStorage.getItem(this.STORAGE_KEY);
        if (!raw) return false;
        const data = JSON.parse(raw);
        if (!data || !Array.isArray(data.nodes)) return false;

        if (data.presets && typeof data.presets === 'object') {
          Object.assign(this.presets, data.presets);
        }

        if (data.activePresetId && this.presets[data.activePresetId]) {
          this.activePresetId = data.activePresetId;
        }

        this.nodes = data.nodes;
        this.connections = Array.isArray(data.connections) ? data.connections : [];
        this.connections.forEach(c => {
          if (c.guardianEnabled === undefined) c.guardianEnabled = true;
        });
        if (data.panX !== undefined) this.panX = data.panX;
        if (data.panY !== undefined) this.panY = data.panY;
        if (data.scale !== undefined) this.scale = data.scale;

        this.nodes.forEach(n => {
          this._ensureNodeStructures(n);
        });

        // Sync from server if local connections are empty
        if (this.connections.length === 0) {
          fetch('/api/pipeline/dag')
            .then(r => r.json())
            .then(res => {
              if (res && res.dag && Array.isArray(res.dag.connections) && res.dag.connections.length > 0) {
                this.connections = res.dag.connections;
                this.render();
              }
            }).catch(() => {});
        }

        console.log(`[SwarmPipeline] 💾 Restored ${this.nodes.length} nodes & ${this.connections.length} connections for preset [${this.activePresetId}].`);
        return true;
      } catch (err) {
        console.warn('[SwarmPipeline] Failed to parse saved DAG:', err);
        return false;
      }
    }

    /**
     * Synchronizes DAG with server disk configuration (system/pipeline_dag.json)
     */
    async syncServerDag() {
      try {
        const res = await fetch('/api/pipeline/dag');
        const json = await res.json();
        if (json && json.status === 'ok' && json.dag && Array.isArray(json.dag.nodes) && json.dag.nodes.length > 0) {
          if (json.dag.presets && typeof json.dag.presets === 'object') {
            Object.assign(this.presets, json.dag.presets);
          }
          if (json.dag.activePresetId && this.presets[json.dag.activePresetId]) {
            this.activePresetId = json.dag.activePresetId;
          }
          this.nodes = json.dag.nodes;
          this.connections = Array.isArray(json.dag.connections) ? json.dag.connections : [];
          this.connections.forEach(c => {
            if (c.guardianEnabled === undefined) c.guardianEnabled = true;
          });
          if (json.dag.panX !== undefined) this.panX = json.dag.panX;
          if (json.dag.panY !== undefined) this.panY = json.dag.panY;
          if (json.dag.scale !== undefined) this.scale = json.dag.scale;
          this.nodes.forEach(n => this._ensureNodeStructures(n));
          this.populatePresetDropdown();
          this.updateStatusBadge();
          this.render();
          console.log(`[SwarmPipeline] 🚀 Synchronized ${this.nodes.length} nodes & ${this.connections.length} connections with server DAG.`);
        }
      } catch (err) {
        console.warn('[SwarmPipeline] Failed to sync server DAG:', err);
      }
    }

    /**
     * Plug & Play: Dynamically populates Triggers and Agents in the sidebar
     */
    async loadDynamicRoster(isBackgroundPoll = false) {
      const triggerListEl = this.container.querySelector('#palette-triggers-list');
      const agentListEl = this.container.querySelector('#palette-agents-list');
      const triggerCountEl = this.container.querySelector('#palette-trigger-count');
      const agentCountEl = this.container.querySelector('#palette-agent-count');

      // 1. Fetch Dynamic Triggers
      try {
        let triggers = [];
        try {
          const res = await fetch('/api/triggers/list?session_id=default');
          if (res.ok) {
            const data = await res.json();
            if (data && Array.isArray(data.triggers)) triggers = data.triggers;
            if (data && Array.isArray(data.external_triggers)) triggers = triggers.concat(data.external_triggers);
            if (data && Array.isArray(data.chrono_jobs)) triggers = triggers.concat(data.chrono_jobs);
          }
        } catch (e) {
          console.warn('[SwarmPipeline] Backend triggers fetch note:', e);
        }

        // Merge sovereign multi-domain triggers (preserves any backend triggers)
        SOVEREIGN_MULTIDOMAIN_TRIGGERS.forEach(sTrig => {
          if (!triggers.some(t => (t.id || t.trigger_id) === sTrig.id)) {
            triggers.push(sTrig);
          }
        });

        this.dynamicTriggers = triggers;
        if (triggerCountEl) triggerCountEl.textContent = `(${triggers.length})`;
        if (triggerListEl) {
          triggerListEl.innerHTML = '';

          triggers.forEach(t => {
            const item = document.createElement('div');
            item.className = 'palette-card-item';
            item.setAttribute('data-type', 'trigger');
            item.setAttribute('data-trigger-id', t.id || t.trigger_id);
            item.setAttribute('draggable', 'true');
            item.style.cursor = 'grab';
            item.title = `Drag to canvas or click to add ${t.name || t.id}`;
            item.innerHTML = `
              <div class="palette-card-icon" style="color:#00f2fe;">${t.icon || '⚡'}</div>
              <div class="palette-card-info" style="min-width:0; flex:1;">
                <div class="palette-card-name" style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${t.name || t.id}</div>
                ${t.domain ? `<div style="margin-top:2px;"><span style="font-size:8.5px; color:#38bdf8; background:rgba(56,189,248,0.12); padding:1px 5px; border-radius:3px; font-weight:700;">${t.domain}</span></div>` : ''}
                <div class="palette-card-desc" style="margin-top:2px;">${t.description || 'System Trigger'}</div>
              </div>
            `;

            // HTML5 Drag & Drop from Sidebar to Canvas
            item.addEventListener('dragstart', (e) => {
              const payload = {
                type: 'trigger',
                triggerId: t.id || t.trigger_id,
                name: t.name || t.id,
                role: t.name || t.id,
                icon: t.icon || '⚡',
                domain: t.domain || 'Sovereign Sensor',
                description: t.description || 'System Trigger',
                triggerConfig: t.triggerConfig ? JSON.parse(JSON.stringify(t.triggerConfig)) : null
              };
              e.dataTransfer.setData('application/json', JSON.stringify(payload));
              e.dataTransfer.setData('text/plain', JSON.stringify(payload));
              e.dataTransfer.effectAllowed = 'copy';
              item.classList.add('is-dragging');
            });
            item.addEventListener('dragend', () => {
              item.classList.remove('is-dragging');
            });

            item.addEventListener('click', () => {
              this.spawnFromPalette({
                type: 'trigger',
                triggerId: t.id || t.trigger_id,
                name: t.name || t.id,
                role: t.name || t.id,
                icon: t.icon || '⚡',
                domain: t.domain || 'Sovereign Sensor',
                description: t.description || 'System Trigger',
                triggerConfig: t.triggerConfig ? JSON.parse(JSON.stringify(t.triggerConfig)) : null
              });
            });
            triggerListEl.appendChild(item);
          });
        }
      } catch (err) {
        console.warn('[SwarmPipeline] Dynamic trigger discovery notice:', err);
      }

      // 2. Fetch Dynamic Agents from Disk via /api/subagents (Zero Hardcoding!)
      try {
        let agents = [];
        // Priority 1: Query backend dynamic subagents (scans system/subagent/ on disk)
        let res = await fetch('/api/subagents');
        if (res.ok) {
          const data = await res.json();
          if (data && Array.isArray(data.subagents)) {
            agents = data.subagents;
          }
        }

        // Fallback to legacy routes if needed
        if (!agents.length) {
          let legacyRes = await fetch('/api/agents');
          if (!legacyRes.ok) legacyRes = await fetch('/api/personas');
          if (legacyRes.ok) {
            const data = await legacyRes.json();
            agents = data && Array.isArray(data.agents) ? data.agents : (Array.isArray(data.personas) ? data.personas : []);
          } else if (window.AVAILABLE_PERSONAS && Array.isArray(window.AVAILABLE_PERSONAS)) {
            agents = window.AVAILABLE_PERSONAS;
          }
        }

        // Khusus Mr. Flow: Dikeluarkan dari list Swarm Palette karena Mr. Flow adalah Agen Solo!
        const spawnableAgents = agents.filter(a => a && a.id && a.id !== 'default' && a.id !== 'mr.flow' && !a.id.toLowerCase().includes('mr.flow'));
        this.dynamicAgents = spawnableAgents;

        // Compare hash for background polling to prevent unnecessary DOM recreation
        const currentHash = JSON.stringify(spawnableAgents.map(a => `${a.id}:${a.name}:${a.role}:${a.icon}`));
        if (isBackgroundPoll && this._lastAgentsHash === currentHash) {
          return; // No change on disk, skip DOM rebuild
        }
        this._lastAgentsHash = currentHash;

        if (agentCountEl) agentCountEl.textContent = `(${spawnableAgents.length} Agents)`;
        if (agentListEl) {
          agentListEl.innerHTML = '';
          spawnableAgents.forEach(a => {
            const item = document.createElement('div');
            item.className = 'palette-card-item';
            item.setAttribute('data-type', 'agent');
            item.setAttribute('data-agent-id', a.id);
            item.setAttribute('draggable', 'true');
            item.style.cursor = 'grab';
            item.title = `Drag to canvas or click to add ${a.name || a.id}`;
            item.innerHTML = `
              <div class="palette-card-icon" style="color:${a.id === 'leader' ? '#f59e0b' : '#38bdf8'};">${a.icon || (a.id === 'leader' ? '👑' : '🤖')}</div>
              <div class="palette-card-info">
                <div class="palette-card-name" style="display:flex; align-items:center; gap:6px;">
                  <span>${a.name || a.id}</span>
                  ${a.id === 'leader' ? '<span class="pipeline-chip-tag" style="color:#f59e0b; border-color:rgba(245,158,11,0.3); font-size:8.5px; padding:0 3px;">LEADER</span>' : ''}
                </div>
                <div class="palette-card-desc">${a.role || a.description || 'Autonomous Agent'}</div>
              </div>
            `;

            // HTML5 Drag & Drop from Sidebar to Canvas
            item.addEventListener('dragstart', (e) => {
              const payload = {
                type: a.id === 'leader' ? 'leader' : 'agent',
                agentId: a.id,
                name: a.name || a.id,
                role: a.name || a.id,
                icon: a.icon || (a.id === 'leader' ? '👑' : '🤖'),
                description: a.description || a.role
              };
              e.dataTransfer.setData('application/json', JSON.stringify(payload));
              e.dataTransfer.setData('text/plain', JSON.stringify(payload));
              e.dataTransfer.effectAllowed = 'copy';
              item.classList.add('is-dragging');
            });
            item.addEventListener('dragend', () => {
              item.classList.remove('is-dragging');
            });

            item.addEventListener('click', () => {
              this.spawnFromPalette({
                type: a.id === 'leader' ? 'leader' : 'agent',
                agentId: a.id,
                name: a.name || a.id,
                role: a.name || a.id,
                icon: a.icon || (a.id === 'leader' ? '👑' : '🤖'),
                description: a.description || a.role
              });
            });

            agentListEl.appendChild(item);
          });
        }
      } catch (err) {
        console.warn('[SwarmPipeline] Dynamic agent discovery notice:', err);
      }

      // 3. Fetch Local Skills from Disk via /api/skills (Strictly local skills/ folder, zero remote repo)
      try {
        const skillsRes = await fetch('/api/skills');
        if (skillsRes.ok) {
          const sData = await skillsRes.json();
          if (sData && Array.isArray(sData.skills) && sData.skills.length > 0) {
            DYNAMIC_LOCAL_SKILLS = sData.skills.map(s => ({
              id: s.id,
              name: s.name || s.id,
              origin: 'Local Skills',
              category: s.category || 'Specialized SOP',
              desc: s.description || `Local skill from skills/${s.id}`
            }));
          }
        }
      } catch (err) {
        console.warn('[SwarmPipeline] Dynamic local skills discovery notice:', err);
      }
    }

    /**
     * Spawns an agent or trigger node from the palette onto the canvas
     */
    spawnFromPalette(data) {
      let spawnX = 100;
      let spawnY = 180;
      if (this.nodes && this.nodes.length > 0) {
        let maxNode = this.nodes[0];
        for (const n of this.nodes) {
          if ((n.x || 0) > (maxNode.x || 0)) {
            maxNode = n;
          }
        }
        spawnX = (maxNode.x || 100) + 340;
        spawnY = maxNode.y || 180;
        if (spawnX > 2200) {
          spawnX = 100;
          spawnY += 240;
        }
      }
      return this.addNode({
        type: data.type || 'agent',
        agentId: data.agentId || data.id,
        name: data.name,
        role: data.role || (data.type === 'trigger' ? 'Trigger Endpoint' : 'Specialist Agent'),
        icon: data.icon || (data.type === 'trigger' ? '⚡' : '🤖'),
        description: data.description || '',
        x: Math.round(spawnX),
        y: Math.round(spawnY),
        taskPrompt: data.taskPrompt || '',
        rulePrompt: data.rulePrompt || '',
        promptFile: data.promptFile || '',
        triggerEvents: data.triggerEvents,
        concreteTools: data.concreteTools,
        triggerConditions: data.triggerConditions
      });
    }

    /**
     * Toolbar actions & Floating Canvas HUD
     */
    _bindToolbarEvents(board) {
      const presetSelector = board.querySelector('#pipeline-preset-selector');
      const btnSavePreset = board.querySelector('#btn-pipe-save-preset');
      const btnNewPreset = board.querySelector('#btn-pipe-new-preset');
      const btnAutoLayout = board.querySelector('#btn-pipe-auto-layout');
      const btnResetSquad = board.querySelector('#btn-pipe-reset-squad');
      const btnCenter = board.querySelector('#btn-pipe-center');
      const btnClearAll = board.querySelector('#btn-pipe-clear-all') || board.querySelector('#btn-pipe-clear');
      const btnRun = board.querySelector('#btn-pipe-run');

      if (presetSelector) {
        presetSelector.addEventListener('change', (e) => {
          this.switchPreset(e.target.value);
        });
      }

      if (btnSavePreset) {
        btnSavePreset.addEventListener('click', () => {
          this.saveCurrentPreset();
        });
      }

      if (btnNewPreset) {
        btnNewPreset.addEventListener('click', () => {
          this.createNewPreset();
        });
      }

      if (btnAutoLayout) {
        btnAutoLayout.addEventListener('click', () => {
          this.autoArrangeNodes();
        });
      }

      if (btnResetSquad) {
        btnResetSquad.addEventListener('click', () => {
          this.resetToDefaultSquad();
        });
      }

      if (btnCenter) {
        btnCenter.addEventListener('click', () => {
          this.panX = 40;
          this.panY = 40;
          this.scale = 1.0;
          this.render();
          this.debouncedSave();
        });
      }

      if (btnClearAll) {
        btnClearAll.addEventListener('click', () => {
          this.clearAllNodes();
        });
      }

      if (btnRun) {
        btnRun.addEventListener('click', () => {
          this.executePipelineSimulation();
        });
      }
    }

    /**
     * Topologically arranges triggers -> leaders -> specialists in a clean horizontal grid
     */
    autoArrangeNodes() {
      if (!this.nodes || this.nodes.length === 0) return;

      const triggers = this.nodes.filter(n => n.type === 'trigger');
      const leaders = this.nodes.filter(n => (n.type === 'leader' || n.agentId === 'leader') && n.type !== 'trigger');
      const specialists = this.nodes.filter(n => !triggers.includes(n) && !leaders.includes(n));

      const connMap = new Map();
      const inDegree = new Map();
      this.nodes.forEach(n => {
        connMap.set(n.id, []);
        inDegree.set(n.id, 0);
      });
      (this.connections || []).forEach(c => {
        if (connMap.has(c.from) && inDegree.has(c.to)) {
          connMap.get(c.from).push(c.to);
          inDegree.set(c.to, (inDegree.get(c.to) || 0) + 1);
        }
      });

      const depth = new Map();
      triggers.forEach(n => depth.set(n.id, 0));
      const leaderBaseDepth = triggers.length > 0 ? 1 : 0;
      leaders.forEach(n => depth.set(n.id, leaderBaseDepth));

      const queue = [...triggers, ...leaders];
      specialists.forEach(n => {
        if ((inDegree.get(n.id) || 0) === 0 && !depth.has(n.id)) {
          depth.set(n.id, leaderBaseDepth + (leaders.length > 0 ? 1 : 0));
          queue.push(n);
        }
      });

      while (queue.length > 0) {
        const curr = queue.shift();
        const currDepth = depth.get(curr.id) || 0;
        const nexts = connMap.get(curr.id) || [];
        for (const nextId of nexts) {
          const nextNode = this.nodes.find(n => n.id === nextId);
          const existingDepth = depth.get(nextId);
          if (existingDepth === undefined || existingDepth < currDepth + 1) {
            depth.set(nextId, currDepth + 1);
            if (nextNode && !queue.includes(nextNode)) {
              queue.push(nextNode);
            }
          }
        }
      }

      let maxCol = 0;
      depth.forEach(d => { if (d > maxCol) maxCol = d; });
      let fallbackCol = maxCol + 1;
      this.nodes.forEach(n => {
        if (!depth.has(n.id)) {
          depth.set(n.id, fallbackCol++);
        }
      });

      const colGroups = new Map();
      this.nodes.forEach(n => {
        const col = depth.get(n.id) || 0;
        if (!colGroups.has(col)) colGroups.set(col, []);
        colGroups.get(col).push(n);
      });

      const sortedCols = Array.from(colGroups.keys()).sort((a, b) => a - b);
      sortedCols.forEach((colKey, colIdx) => {
        const group = colGroups.get(colKey);
        group.forEach((node, rowIdx) => {
          node.x = 100 + colIdx * 340;
          node.y = 180 + rowIdx * 240;
        });
      });

      this.panX = 40;
      this.panY = 40;
      this.scale = 1.0;
      this.render();
      this.saveState();
    }

    /**
     * Resets canvas to the pristine squad definition of current preset
     */
    resetToDefaultSquad() {
      this.selectedNodeId = null;
      this.selectedConnId = null;

      if (DEFAULT_SWARM_PRESETS[this.activePresetId]) {
        const pristine = DEFAULT_SWARM_PRESETS[this.activePresetId];
        this.nodes = JSON.parse(JSON.stringify(pristine.nodes));
        this.connections = JSON.parse(JSON.stringify(pristine.connections));
        this.panX = pristine.panX !== undefined ? pristine.panX : 40;
        this.panY = pristine.panY !== undefined ? pristine.panY : 40;
        this.scale = pristine.scale !== undefined ? pristine.scale : 1.0;
      } else {
        this.nodes = [
          {
            id: 'node-0-leader',
            agentId: 'leader',
            type: 'leader',
            name: 'Swarm Leader',
            role: 'Swarm Leader',
            icon: '👑',
            x: 100,
            y: 180,
            isLocked: true,
            taskPrompt: 'Coordinate mission delegation across subordinate swarm agents.',
            rulePrompt: 'Ensure all subordinates adhere to leadership SOP and strict SLA targets.',
            toolGovernance: {
              allowAll: true,
              allowedTools: SOVEREIGN_LOCAL_TOOLS.map(t => t.id),
              deniedTools: []
            }
          },
          {
            id: 'node-1-backend',
            agentId: 'backend-engineer',
            type: 'agent',
            name: 'Backend Engineer',
            role: 'Backend & Systems Specialist',
            icon: '⚙️',
            x: 440,
            y: 180,
            isLocked: false,
            taskPrompt: 'Implement backend services, database schemas, and IPC routing.',
            rulePrompt: 'Zero hardcoded paths. Strict multi-OS support. Sanctity of @lock.'
          },
          {
            id: 'node-2-frontend',
            agentId: 'frontend-engineer',
            type: 'agent',
            name: 'Frontend Engineer',
            role: 'UI/UX & Client Specialist',
            icon: '🎨',
            x: 780,
            y: 180,
            isLocked: false,
            taskPrompt: 'Construct client user interfaces, Canvas components, and interactive styles.',
            rulePrompt: 'Strict Global English. Visual screenshot verification before dispatch. Sanctity of @lock.'
          },
          {
            id: 'node-3-security',
            agentId: 'security-auditor',
            type: 'agent',
            name: 'Security Auditor',
            role: 'Security & Reverse Engineering Specialist',
            icon: '🛡️',
            x: 1120,
            y: 180,
            isLocked: false,
            taskPrompt: 'Perform security audit, threat modeling, and secret scan.',
            rulePrompt: 'Zero unvetted secrets or credentials. Scrutinize reverse engineering and attack surfaces. Sanctity of @lock.'
          },
          {
            id: 'node-4-qc',
            agentId: 'quality-control',
            type: 'agent',
            name: 'Quality Control',
            role: 'Quality Control & Release Gatekeeper',
            icon: '🧪',
            x: 1460,
            y: 180,
            isLocked: false,
            taskPrompt: 'Execute automated test suites, linting, visual verification, and seal release certification.',
            rulePrompt: 'Strict Exit Code 0 empirical proof. Visual screenshot verification. Anti-zombie code hygiene.'
          }
        ];

        this.connections = [
          {
            id: 'conn-0-1',
            from: 'node-0-leader',
            fromPort: 'out-1',
            to: 'node-1-backend',
            toPort: 'input',
            type: 'normal',
            guardianEnabled: true
          },
          {
            id: 'conn-1-2',
            from: 'node-1-backend',
            fromPort: 'out-1',
            to: 'node-2-frontend',
            toPort: 'input',
            type: 'normal',
            guardianEnabled: true
          },
          {
            id: 'conn-2-3',
            from: 'node-2-frontend',
            fromPort: 'out-1',
            to: 'node-3-security',
            toPort: 'input',
            type: 'normal',
            guardianEnabled: true
          },
          {
            id: 'conn-3-4',
            from: 'node-3-security',
            fromPort: 'out-1',
            to: 'node-4-qc',
            toPort: 'input',
            type: 'normal',
            guardianEnabled: true
          }
        ];
        this.panX = 40;
        this.panY = 40;
        this.scale = 1.0;
      }

      this.nodes.forEach(n => this._ensureNodeStructures(n));
      this.render();
      this.saveState(true);

      const indicator = this.boardEl?.querySelector('#pipeline-save-indicator');
      if (indicator) {
        const curr = this.presets?.[this.activePresetId];
        indicator.textContent = `🔄 Reset [${curr?.name || this.activePresetId}] to Pristine Squad`;
        indicator.classList.remove('save-indicator-flash');
        void indicator.offsetWidth;
        indicator.classList.add('save-indicator-flash');
      }
    }

    /**
     * Clears all nodes and connections from canvas immediately
     */
    clearAllNodes() {
      this.nodes = [];
      this.connections = [];
      this.selectedNodeId = null;
      this.selectedConnId = null;
      this.render();
      this.saveState(true);
    }

    /**
     * Canvas Board pan & zoom
     */
    _bindBoardCanvasEvents(board) {
      board.addEventListener('mousedown', (e) => {
        this.closeContextMenu();
        if (e.target === board || e.target === this.svgLayer || e.target === this.nodesLayer) {
          this.isPanning = true;
          this.panStartX = e.clientX - this.panX;
          this.panStartY = e.clientY - this.panY;
          board.style.cursor = 'grabbing';
          this.selectedNodeId = null;
          this.selectedConnId = null;
          this.render();
        }
      });

      board.addEventListener('wheel', (e) => {
        e.preventDefault();
        const zoomDelta = e.deltaY > 0 ? -0.08 : 0.08;
        const newScale = Math.min(Math.max(0.4, this.scale + zoomDelta), 1.8);
        this.scale = newScale;
        this.render();
        this.debouncedSave(300);
      }, { passive: false });

      // HTML5 Drag and Drop Ingress: Drop nodes anywhere on canvas
      board.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
      });

      board.addEventListener('dragenter', (e) => {
        e.preventDefault();
      });

      board.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        let data = null;
        try {
          const raw = e.dataTransfer.getData('application/json') || e.dataTransfer.getData('text/plain');
          if (raw) data = JSON.parse(raw);
        } catch (_) {}

        if (data) {
          const boardRect = this.boardEl.getBoundingClientRect();
          const mouseCanvasX = (e.clientX - boardRect.left - this.panX) / this.scale;
          const mouseCanvasY = (e.clientY - boardRect.top - this.panY) / this.scale;

          this.addNode({
            type: data.type || 'agent',
            agentId: data.agentId || data.id,
            name: data.name,
            role: data.role || (data.type === 'trigger' ? 'Trigger Endpoint' : 'Specialist Agent'),
            icon: data.icon || (data.type === 'trigger' ? '⚡' : '🤖'),
            description: data.description || '',
            x: Math.max(40, Math.round(mouseCanvasX - 125)),
            y: Math.max(40, Math.round(mouseCanvasY - 40)),
            taskPrompt: data.taskPrompt || '',
            rulePrompt: data.rulePrompt || ''
          });
          this.render();
          this.saveState(true);
        }
      });
    }

    _bindGlobalEvents() {
      window.removeEventListener('mousemove', this._boundOnMouseMove);
      window.removeEventListener('mouseup', this._boundOnMouseUp);
      window.removeEventListener('keydown', this._boundOnKeyDown);

      window.addEventListener('mousemove', this._boundOnMouseMove);
      window.addEventListener('mouseup', this._boundOnMouseUp);
      window.addEventListener('keydown', this._boundOnKeyDown);

      if (!this._boundBeforeUnload) {
        this._boundBeforeUnload = () => this.saveState(false);
        window.addEventListener('beforeunload', this._boundBeforeUnload);
      }
      if (!this._boundWindowFocus) {
        this._boundWindowFocus = () => this.loadDynamicRoster(true);
        window.addEventListener('focus', this._boundWindowFocus);
      }
    }

    _onKeyDown(e) {
      if (e.key === 'Escape') {
        this.closeContextMenu();
      }
      const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
      if (activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select' || document.activeElement?.isContentEditable) return;

      // 1. Delete selected cable via Delete or Backspace
      if ((e.key === 'Delete' || e.key === 'Backspace') && this.selectedConnId) {
        e.preventDefault();
        this.deleteConnection(this.selectedConnId);
        return;
      }

      // 2. Delete selected node via Delete or Backspace
      if ((e.key === 'Delete' || e.key === 'Backspace') && this.selectedNodeId) {
        const node = this.nodes.find(n => n.id === this.selectedNodeId);
        if (node) {
          e.preventDefault();
          this.deleteNode(node.id);
        }
      }
    }

    _onMouseMove(e) {
      if (this.isPanning && this.boardEl) {
        this.panX = e.clientX - this.panStartX;
        this.panY = e.clientY - this.panStartY;
        this.render();
        return;
      }

      if (this.draggedNode && this.boardEl) {
        const boardRect = this.boardEl.getBoundingClientRect();
        const mouseCanvasX = (e.clientX - boardRect.left - this.panX) / this.scale;
        const mouseCanvasY = (e.clientY - boardRect.top - this.panY) / this.scale;

        this.draggedNode.x = Math.round(mouseCanvasX - this.dragOffsetX);
        this.draggedNode.y = Math.round(mouseCanvasY - this.dragOffsetY);

        const nodeEl = this.nodesLayer.querySelector(`#dag-node-${this.draggedNode.id}`);
        if (nodeEl) {
          nodeEl.style.left = `${this.draggedNode.x}px`;
          nodeEl.style.top = `${this.draggedNode.y}px`;
        }
        this._renderConnectionsOnly();
        this.debouncedSave(400);
        return;
      }

      if (this.isWiring && this.activeWireEl && this.boardEl) {
        const fromNode = this.nodes.find(n => n.id === this.wireStartNodeId);
        if (!fromNode) return;

        const x1 = fromNode.x + 250;
        const y1 = fromNode.y + (this.wireStartPort === 'out-2' ? 118 : 59);

        const boardRect = this.boardEl.getBoundingClientRect();
        const mouseCanvasX = (e.clientX - boardRect.left - this.panX) / this.scale;
        const mouseCanvasY = (e.clientY - boardRect.top - this.panY) / this.scale;

        const pathData = this._calculateBezier(x1, y1, mouseCanvasX, mouseCanvasY);
        this.activeWireEl.setAttribute('d', pathData);
      }
    }

    _onMouseUp(e) {
      if (this.isPanning) {
        this.isPanning = false;
        if (this.boardEl) this.boardEl.style.cursor = 'grab';
        this.debouncedSave(200);
      }

      if (this.draggedNode) {
        this.draggedNode = null;
        this.debouncedSave(200);
      }

      if (this.isWiring) {
        const targetPort = e.target.closest('.dag-port-input');
        if (targetPort) {
          const targetNodeId = targetPort.getAttribute('data-node-id');
          if (targetNodeId && targetNodeId !== this.wireStartNodeId) {
            this.connectNodes(this.wireStartNodeId, targetNodeId, this.wireStartPort);
          }
        }

        if (this.activeWireEl && this.activeWireEl.parentNode) {
          this.activeWireEl.parentNode.removeChild(this.activeWireEl);
        }
        this.activeWireEl = null;
        this.isWiring = false;
        this.wireStartNodeId = null;
        this.wireStartPort = 'out-1';
      }
    }

    _ensureNodeStructures(n) {
      if (!n) return;
      if (!n.personaData) {
        n.personaData = {
          role: n.role || 'Agent',
          systemPrompt: n.isLocked
            ? 'You are the Sovereign Swarm Leader. You oversee, coordinate, and orchestrate all delegated missions across subordinate agents.'
            : (n.type === 'trigger'
              ? 'System Ingress Trigger. Listens for external telemetry/events and dispatches payload to swarm.'
              : 'You are an autonomous specialist agent. You execute delegated assignments with rigorous precision and zero hallucination.'),
          tone: 'Professional & Technical',
          priority: n.isLocked ? 'Critical' : 'High',
          timeoutSeconds: 120
        };
      }
      if (!n.rulesData) {
        n.rulesData = {
          prompt: n.rulePrompt || 'Adhere strictly to standard SOP, zero credential leaks, and SLA targets.',
          gateValidation: 'strict',
          passPort: 'out-1',
          failPort: 'out-2',
          failoverAction: 'circuit_break'
        };
      }
      if (!n.taskData) {
        n.taskData = {
          prompt: n.taskPrompt || 'Execute assigned operations and return validated deliverables with Exit Code 0.',
          acceptanceCriteria: 'Output must satisfy functional specifications and achieve Exit Code 0.',
          contextIngestion: 'blackboard_and_payload',
          slaSeconds: 300
        };
      }
      if (!n.modelConfig) {
        n.modelConfig = {
          provider: 'google',
          modelId: 'gemini-3.8-flash-high',
          modelName: 'Gemini 3.8 Flash (High)',
          accountMode: 'combo', // 'combo' (DEFAULT) or specific account
          temperature: 0.2
        };
      }
      if (!n.toolGovernance) {
        n.toolGovernance = {
          allowAll: true,
          allowedTools: SOVEREIGN_LOCAL_TOOLS.map(t => t.id),
          deniedTools: [],
          toolGuardians: {}
        };
      }
      if (!n.toolGovernance.toolGuardians) {
        n.toolGovernance.toolGuardians = {};
      }
      if (!n.guardianConfig) {
        n.guardianConfig = {
          allowRead: true,
          allowEdit: true,
          allowWrite: true,
          allowDelete: false,
          allowedExtensions: ['.js', '.ts', '.json', '.html', '.css', '.md', '.py', '.mjs', '.yaml', '.txt'],
          prohibitedExtensions: ['.lock', '.env', '.pem', '.key', '.sh', '.bash', '.bin', '.exe', '.so'],
          enforceLockAnnotations: true,
          restrictedPaths: ['.git/', '.flowork_brain/']
        };
      }
      if (!n.skillsConfig) {
        n.skillsConfig = {
          activeSkills: ['ui_ux_pro_max', 'antigravity_guide', 'code-review', 'implement-spec']
        };
      }
      if (!n.triggerConfig) {
        // Find matching predefined trigger config if available
        const matched = SOVEREIGN_MULTIDOMAIN_TRIGGERS.find(t => 
          t.id === n.triggerId || 
          t.id === n.id || 
          t.name === n.role || 
          (n.role && n.role.includes(t.name)) ||
          (n.name && n.name.includes(t.name))
        );
        if (matched) {
          n.triggerConfig = JSON.parse(JSON.stringify(matched.triggerConfig));
          if (!n.domain) n.domain = matched.domain;
        } else {
          n.triggerConfig = {
            enabled: n.type === 'trigger',
            ingressType: 'webhook',
            channel: '/api/webhook/pipeline',
            method: 'POST',
            conditionExpr: 'payload.event != null',
            samplePayload: JSON.stringify({ event: 'INGRESS_SIGNAL', timestamp: new Date().toISOString() }, null, 2),
            daemonActive: true,
            events: n.triggerEvents || ['ingress_signal'],
            exitCodeFilter: 'Port 1 (Match) / Port 2 (Else)',
            triggerPrompt: '',
            promptFile: n.promptFile || ''
          };
        }
      }
    }

    /**
     * Adds a new node to the DAG (Structured across 6 tabs)
     */
    addNode(nodeData) {
      const type = nodeData.type || 'agent';
      const newNode = {
        id: nodeData.id || `node-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 5)}`,
        type: type,
        triggerId: nodeData.triggerId,
        domain: nodeData.domain || '',
        triggerConfig: nodeData.triggerConfig,
        agentId: nodeData.agentId || (type === 'leader' ? 'leader' : (nodeData.id?.includes('leader') ? 'leader' : 'mr.flow')),
        name: nodeData.name || '',
        role: nodeData.role || (type === 'trigger' ? 'Trigger Endpoint' : 'Specialist Agent'),
        icon: nodeData.icon || (type === 'trigger' ? '⚡' : '🤖'),
        description: nodeData.description || '',
        x: nodeData.x || 300,
        y: nodeData.y || 200,
        isLocked: !!nodeData.isLocked,
        taskPrompt: nodeData.taskPrompt || nodeData.prompt || '',
        rulePrompt: nodeData.rulePrompt || '',
        promptFile: nodeData.promptFile || '',
        triggerEvents: nodeData.triggerEvents,
        concreteTools: nodeData.concreteTools,
        triggerConditions: nodeData.triggerConditions
      };

      this._ensureNodeStructures(newNode);

      this.nodes.push(newNode);
      this.selectNode(newNode.id);
      this.debouncedSave();
      return newNode;
    }

    /**
     * Connects two nodes with a directional cable (Out 1 or Out 2)
     */
    addConnection(fromId, toId, fromPort = 'out-1', type = 'normal') {
      return this.connectNodes(fromId, toId, fromPort, type);
    }

    connectNodes(fromId, toId, fromPort = 'out-1', type = 'normal') {
      if (fromId === toId) return null;
      const exists = this.connections.some(c => c.from === fromId && (c.fromPort || 'out-1') === fromPort && c.to === toId);
      if (exists) return null;

      const newConn = {
        id: `conn-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`,
        from: fromId,
        fromPort: fromPort,
        to: toId,
        toPort: 'input',
        type: type
      };

      this.connections.push(newConn);
      this.selectConnection(newConn.id);
      this.debouncedSave();
      return newConn;
    }

    selectConnection(connId) {
      this.selectedConnId = connId;
      this.selectedNodeId = null;
      this.render();
    }

    selectNode(nodeId) {
      this.selectedNodeId = nodeId;
      this.selectedConnId = null;
      this.render();
    }

    deleteConnection(connId) {
      this.connections = this.connections.filter(c => c.id !== connId);
      if (this.selectedConnId === connId) {
        this.selectedConnId = null;
      }
      this.render();
      this.saveState();
    }

    deleteNode(nodeId) {
      const node = this.nodes.find(n => n.id === nodeId);
      if (!node) return;

      this.nodes = this.nodes.filter(n => n.id !== nodeId);
      this.connections = this.connections.filter(c => c.from !== nodeId && c.to !== nodeId);
      if (this.selectedNodeId === nodeId) {
        this.selectedNodeId = null;
      }
      this.closeContextMenu();
      this.render();
      this.saveState();
    }

    closeContextMenu() {
      const existing = document.getElementById('pipeline-node-contextmenu');
      if (existing) {
        existing.remove();
      }
    }

    showNodeContextMenu(node, clientX, clientY) {
      this.closeContextMenu();

      const menu = document.createElement('div');
      menu.id = 'pipeline-node-contextmenu';
      menu.className = 'pipeline-custom-contextmenu';
      menu.style.left = `${clientX}px`;
      menu.style.top = `${clientY}px`;

      const isTriggerNode = (node.type === 'trigger') || (node.id && node.id.startsWith('trg-'));
      const roleText = node.role || node.id || 'Node';

      menu.innerHTML = `
        <div class="contextmenu-header">
          <span>${node.icon || (isTriggerNode ? '⚡' : '🤖')}</span>
          <strong style="color:#f8fafc; font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:140px;">${roleText}</strong>
        </div>
        <div class="contextmenu-divider"></div>
        <button type="button" class="contextmenu-item" id="ctx-btn-configure">
          <span style="font-size:13px;">⚙️</span>
          <span>Configure Cockpit</span>
        </button>
        <button type="button" class="contextmenu-item danger" id="ctx-btn-delete">
          <span style="font-size:13px;">🗑️</span>
          <span>Delete Node</span>
        </button>
      `;

      document.body.appendChild(menu);

      // Adjust if menu overflows viewport
      const rect = menu.getBoundingClientRect();
      if (rect.right > window.innerWidth) {
        menu.style.left = `${Math.max(10, window.innerWidth - rect.width - 15)}px`;
      }
      if (rect.bottom > window.innerHeight) {
        menu.style.top = `${Math.max(10, window.innerHeight - rect.height - 15)}px`;
      }

      // Configure button click
      menu.querySelector('#ctx-btn-configure')?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.closeContextMenu();
        if (isTriggerNode) {
          this.openTriggerCockpitModal(node);
        } else {
          this.openFullPromptModal(node, null, null);
        }
      });

      // Delete button click
      menu.querySelector('#ctx-btn-delete')?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.closeContextMenu();
        this.deleteNode(node.id);
      });

      // Auto close on document click or contextmenu elsewhere
      const onDocDismiss = (e) => {
        if (!menu.contains(e.target)) {
          this.closeContextMenu();
          document.removeEventListener('click', onDocDismiss);
          document.removeEventListener('contextmenu', onDocDismiss);
        }
      };
      setTimeout(() => {
        document.addEventListener('click', onDocDismiss);
        document.addEventListener('contextmenu', onDocDismiss);
      }, 50);
    }

    renderInspector() {
      // Safe no-op: Right bar is removed per instruction
    }

    /**
     * Renders all nodes (with dual outputs) and SVG connections
     */
    render() {
      if (!this.nodesLayer || !this.svgLayer) return;

      this.nodesLayer.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.scale})`;
      this.svgLayer.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.scale})`;

      // 1. Render Connections (SVG Bezier Cables)
      let svgHtml = `
        <defs>
          <filter id="glow-emerald" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
      `;

      this.connections.forEach(conn => {
        const fromNode = this.nodes.find(n => n.id === conn.from);
        const toNode = this.nodes.find(n => n.id === conn.to);
        if (!fromNode || !toNode) return;

        const fromPort = conn.fromPort || 'out-1';
        const x1 = fromNode.x + 250;
        const y1 = fromNode.y + (fromPort === 'out-2' ? 118 : 59);
        const x2 = toNode.x;
        const y2 = toNode.y + 82;

        const pathData = this._calculateBezier(x1, y1, x2, y2);
        const isTrigger = fromNode.type === 'trigger';
        const isSelected = this.selectedConnId === conn.id;

        let cableClass = isTrigger ? 'pipeline-cable trigger-cable' : 'pipeline-cable';
        if (fromPort === 'out-2') cableClass += ' cable-route-2';
        if (isSelected) cableClass += ' cable-selected';
        if (conn.guardianEnabled === false) cableClass += ' cable-guardian-bypassed';

        svgHtml += `
          <g class="pipeline-cable-group ${isSelected ? 'selected' : ''}" data-conn-id="${conn.id}">
            <path d="${pathData}" class="${cableClass}" />
            <path d="${pathData}" class="pipeline-photon-stream ${fromPort === 'out-2' ? 'photon-route-2' : ''} ${conn.guardianEnabled === false ? 'photon-bypassed' : ''}" />
          </g>
        `;
      });

      this.svgLayer.innerHTML = svgHtml;

      // Bind SVG cable click & right-click handlers
      const cableGroups = this.svgLayer.querySelectorAll('.pipeline-cable-group');
      cableGroups.forEach(cg => {
        cg.addEventListener('click', (e) => {
          e.stopPropagation();
          const connId = cg.getAttribute('data-conn-id');
          this.selectConnection(connId);
        });

        cg.addEventListener('contextmenu', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const connId = cg.getAttribute('data-conn-id');
          if (confirm('Delete this connection cable?')) {
            this.deleteConnection(connId);
          }
        });
      });

      // 2. Render Node Elements & Midpoint Delete Badges
      this.nodesLayer.innerHTML = '';

      // Midpoint Badges with Quick ✕ Delete Button
      this.connections.forEach(conn => {
        const fromNode = this.nodes.find(n => n.id === conn.from);
        const toNode = this.nodes.find(n => n.id === conn.to);
        if (!fromNode || !toNode) return;

        const fromPort = conn.fromPort || 'out-1';
        const x1 = fromNode.x + 250;
        const y1 = fromNode.y + (fromPort === 'out-2' ? 118 : 59);
        const x2 = toNode.x;
        const y2 = toNode.y + 82;
        const midX = Math.round((x1 + x2) / 2);
        const midY = Math.round((y1 + y2) / 2);

        const isSelected = this.selectedConnId === conn.id;
        const portText = fromPort === 'out-2' ? 'Out 2 (Fail)' : 'Out 1 (Pass)';
        const isGuardianOn = conn.guardianEnabled !== false;

        const badgeEl = document.createElement('div');
        badgeEl.className = `pipeline-gate-badge ${isSelected ? 'selected' : ''} ${fromPort === 'out-2' ? 'badge-route-2' : ''} ${isGuardianOn ? 'guardian-active' : 'guardian-bypassed'}`;
        badgeEl.id = `gate-badge-${conn.id}`;
        badgeEl.style.left = `${midX}px`;
        badgeEl.style.top = `${midY}px`;
        badgeEl.innerHTML = `
          <button class="gate-guardian-toggle-btn ${isGuardianOn ? 'active' : 'bypassed'}" title="Toggle Guardian Inspection on this Cable (Currently: ${isGuardianOn ? 'GUARDIAN ON' : 'GUARDIAN OFF / TRIAL'})" data-conn-id="${conn.id}">
            <span class="guardian-shield-icon">${isGuardianOn ? '🛡️' : '⚪'}</span>
            <span class="guardian-label-text">${isGuardianOn ? 'GUARD ON' : 'GUARD OFF'}</span>
          </button>
          <span style="font-size:9px; font-weight:800; margin-right:4px;">[${portText}]</span>
          <button class="gate-delete-quick-btn" title="Delete Cable" data-conn-id="${conn.id}">✕</button>
        `;

        badgeEl.addEventListener('click', (e) => {
          if (e.target.closest('.gate-delete-quick-btn') || e.target.closest('.gate-guardian-toggle-btn')) return;
          e.stopPropagation();
          this.selectConnection(conn.id);
        });

        const btnToggleGuardian = badgeEl.querySelector('.gate-guardian-toggle-btn');
        if (btnToggleGuardian) {
          btnToggleGuardian.addEventListener('click', (e) => {
            e.stopPropagation();
            conn.guardianEnabled = conn.guardianEnabled === false ? true : false;
            this.saveState();
            this.render();
          });
        }

        const btnDel = badgeEl.querySelector('.gate-delete-quick-btn');
        if (btnDel) {
          btnDel.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteConnection(conn.id);
          });
        }

        this.nodesLayer.appendChild(badgeEl);
      });

      // Render Nodes
      this.nodes.forEach(node => {
        const nodeEl = document.createElement('div');

        let badgeClass = 'badge-specialist';
        let badgeText = 'AGENT';

        if (node.isLocked) {
          badgeClass = 'badge-leader';
          badgeText = 'LEADER';
        } else if (node.type === 'trigger') {
          badgeClass = 'badge-trigger';
          badgeText = 'TRIGGER';
        } else if (node.type === 'task') {
          badgeClass = 'badge-task';
          badgeText = 'TASK';
        } else if (node.type === 'rule') {
          badgeClass = 'badge-rule';
          badgeText = 'RULE';
        }

        const isTriggerNode = node.type === 'trigger';
        const taskSnippet = node.taskPrompt ? node.taskPrompt.substring(0, 32) + '...' : '<span style="color:#64748b; font-style:italic;">Not configured</span>';
        const ruleSnippet = node.rulePrompt ? node.rulePrompt.substring(0, 32) + '...' : '<span style="color:#64748b; font-style:italic;">Not configured</span>';
        const triggerEventsSnippet = node.triggerConfig?.events?.length ? node.triggerConfig.events.join(', ') : 'terminal_execution';

        nodeEl.className = `dag-node ${isTriggerNode ? 'node-trigger' : ''} ${node.isLocked ? 'node-locked' : ''} ${this.selectedNodeId === node.id ? 'selected' : ''}`;
        nodeEl.id = `dag-node-${node.id}`;
        nodeEl.style.left = `${node.x}px`;
        nodeEl.style.top = `${node.y}px`;

        const tc = node.triggerConfig || {};
        const sensorType = tc.ingressType || 'webhook';
        const channelDisplay = tc.channel || tc.symbol || tc.watchPath || tc.interval || '/api/webhook/pipeline';
        const trigRuleSnippet = tc.conditionExpr ? (tc.conditionExpr.length > 28 ? tc.conditionExpr.substring(0, 26) + '...' : tc.conditionExpr) : 'All Ingress Fired';
        const domainTag = node.domain || 'Sovereign Sensor';

        const bodyContent = isTriggerNode ? `
            <div style="font-size:10px; display:flex; flex-direction:column; gap:4px;">
              <div><strong style="color:#00f2fe;">📡 Sensor Channel:</strong> <span style="font-size:9.5px; color:#38bdf8; font-family:monospace; word-break:break-all;">${channelDisplay}</span></div>
              <div><strong style="color:#a855f7;">⚖️ Port 1 Rule:</strong> <span style="font-size:9.5px; color:#e2e8f0; font-family:monospace;">${trigRuleSnippet}</span></div>
            </div>
            <div style="margin-top:6px; font-size:9.5px; color:#34d399; background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25); border-radius:4px; padding:3px 6px; display:flex; align-items:center; justify-content:space-between;">
              <span style="color:#10b981; font-weight:700;">🟢 Port 1: Match</span>
              <span style="color:#f59e0b; font-weight:700;">🟠 Port 2: Else</span>
            </div>
            <button class="dag-node-prompt-btn" style="margin-top:6px; width:100%; font-size:10px; font-weight:800; background:linear-gradient(135deg, rgba(0,242,254,0.18), rgba(6,182,212,0.25)); border:1px solid rgba(0,242,254,0.45); color:#00f2fe; border-radius:5px; padding:5px; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:5px; transition:all 0.2s ease;">
              ⚡ Configure & Test Ingress
            </button>
        ` : `
            <div style="font-size:10px; display:flex; flex-direction:column; gap:3px;">
              <div><strong style="color:#818cf8;">📋 Task:</strong> <span style="font-size:9.5px;">${taskSnippet}</span></div>
              <div><strong style="color:#fb7185;">🛡️ Rules:</strong> <span style="font-size:9.5px;">${ruleSnippet}</span></div>
            </div>
            <div style="margin-top:6px; font-size:9.5px; color:#38bdf8; background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.25); border-radius:4px; padding:3px 6px; display:flex; align-items:center; justify-content:space-between;">
              <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:120px;">🧠 ${node.modelConfig?.modelName ? node.modelConfig.modelName.split('[')[0].trim() : 'Gemini 3.8 Flash'}</span>
              <span style="color:#f59e0b; font-weight:800; font-size:9px;">⚡ ${node.modelConfig?.accountMode === 'combo' ? 'Combo' : 'Direct'}</span>
            </div>
            <button class="dag-node-prompt-btn" style="margin-top:6px; width:100%; font-size:10px; font-weight:800; background:rgba(56,189,248,0.2); border:1px solid rgba(56,189,248,0.45); color:#7dd3fc; border-radius:5px; padding:5px; cursor:pointer;">
              ⚙️ Configure Cockpit (6 Tabs)
            </button>
        `;

        nodeEl.innerHTML = `
          <!-- Input Port -->
          <div class="dag-port dag-port-input" data-node-id="${node.id}" data-port="input" title="Input Port"></div>

          <!-- Header -->
          <div class="dag-node-header">
            <div class="dag-node-title">
              <span>${node.icon || (isTriggerNode ? '⚡' : '🤖')}</span>
              <span>${node.role}</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
              <span class="dag-node-status-indicator" style="display:none;"></span>
              <span class="dag-node-type-badge ${badgeClass}">${badgeText}</span>
              <button type="button" class="dag-node-delete-btn" data-node-id="${node.id}" title="Delete node from canvas">✕</button>
            </div>
          </div>

          <!-- Body -->
          <div class="dag-node-body" title="Click to open full cockpit configuration">
            ${bodyContent}
          </div>

          <!-- Mandatory 2 Output Ports -->
          <div class="dag-port dag-port-out-1" data-node-id="${node.id}" data-port-id="out-1" title="Output 1 (${isTriggerNode ? 'Condition Match / Primary Signal' : 'Pass / Primary Route'})">1</div>
          <div class="dag-port dag-port-out-2" data-node-id="${node.id}" data-port-id="out-2" title="Output 2 (${isTriggerNode ? 'Else / Fallback Route' : 'Fail / Fallback Route'})">2</div>
        `;

        // Node delete button
        const delBtn = nodeEl.querySelector('.dag-node-delete-btn');
        if (delBtn) {
          delBtn.addEventListener('mousedown', (e) => e.stopPropagation());
          delBtn.addEventListener('pointerdown', (e) => e.stopPropagation());
          delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            this.deleteNode(node.id);
          });
        }

        // Right click (contextmenu) on node -> Custom Context Menu (Configure / Delete)
        nodeEl.addEventListener('contextmenu', (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.selectNode(node.id);
          this.showNodeContextMenu(node, e.clientX, e.clientY);
        });

        // Select Node & Dragging
        const header = nodeEl.querySelector('.dag-node-header');
        header.addEventListener('mousedown', (e) => {
          e.stopPropagation();
          this.selectNode(node.id);
          this.draggedNode = node;

          const boardRect = this.boardEl.getBoundingClientRect();
          const mouseCanvasX = (e.clientX - boardRect.left - this.panX) / this.scale;
          const mouseCanvasY = (e.clientY - boardRect.top - this.panY) / this.scale;

          this.dragOffsetX = mouseCanvasX - node.x;
          this.dragOffsetY = mouseCanvasY - node.y;
        });

        // Double click header -> Open Full Popup Prompt Editor or Trigger Cockpit
        header.addEventListener('dblclick', (e) => {
          e.stopPropagation();
          if (isTriggerNode) {
            this.openTriggerCockpitModal(node);
          } else {
            this.openFullPromptModal(node, null, null);
          }
        });

        // Clicking body -> Selects node AND Opens Full Popup Prompt Editor or Trigger Cockpit
        nodeEl.querySelector('.dag-node-body')?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.selectNode(node.id);
          if (isTriggerNode) {
            this.openTriggerCockpitModal(node);
          } else {
            this.openFullPromptModal(node, null, null);
          }
        });

        // Prompt button explicit click
        nodeEl.querySelector('.dag-node-prompt-btn')?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.selectNode(node.id);
          if (isTriggerNode) {
            this.openTriggerCockpitModal(node);
          } else {
            this.openFullPromptModal(node, null, null);
          }
        });

        // Mandatory 2 Output Ports Wiring
        const outPorts = nodeEl.querySelectorAll('.dag-port-out-1, .dag-port-out-2');
        outPorts.forEach(outPort => {
          outPort.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            this.isWiring = true;
            this.wireStartNodeId = node.id;
            this.wireStartPort = outPort.getAttribute('data-port-id') || 'out-1';

            const strokeColor = this.wireStartPort === 'out-2' ? '#f43f5e' : '#10b981';
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('class', 'pipeline-cable');
            path.setAttribute('style', `stroke: ${strokeColor}; stroke-dasharray: 4 4; stroke-width: 2.5px;`);
            this.svgLayer.appendChild(path);
            this.activeWireEl = path;
          });
        });

        this.nodesLayer.appendChild(nodeEl);
      });
    }

    _renderConnectionsOnly() {
      const paths = this.svgLayer.querySelectorAll('.pipeline-cable-group');
      paths.forEach(g => {
        const connId = g.getAttribute('data-conn-id');
        const conn = this.connections.find(c => c.id === connId);
        if (!conn) return;

        const fromNode = this.nodes.find(n => n.id === conn.from);
        const toNode = this.nodes.find(n => n.id === conn.to);
        if (!fromNode || !toNode) return;

        const fromPort = conn.fromPort || 'out-1';
        const x1 = fromNode.x + 250;
        const y1 = fromNode.y + (fromPort === 'out-2' ? 118 : 59);
        const x2 = toNode.x;
        const y2 = toNode.y + 82;
        const pathData = this._calculateBezier(x1, y1, x2, y2);

        const cables = g.querySelectorAll('path');
        cables.forEach(c => c.setAttribute('d', pathData));

        const badge = this.nodesLayer.querySelector(`#gate-badge-${conn.id}`);
        if (badge) {
          badge.style.left = `${Math.round((x1 + x2) / 2)}px`;
          badge.style.top = `${Math.round((y1 + y2) / 2)}px`;
        }
      });
    }

    _calculateBezier(x1, y1, x2, y2) {
      const dx = Math.abs(x2 - x1) * 0.55;
      const cp1x = x1 + Math.max(dx, 40);
      const cp1y = y1;
      const cp2x = x2 - Math.max(dx, 40);
      const cp2y = y2;
      return `M ${x1} ${y1} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${y2}`;
    }

    // =========================================================================
    // ⚡ FULL POPUP MODAL FOR TASK & RULES PROMPT CONFIGURATION
    // =========================================================================

    /**
     * Opens the Full Popup Modal for editing Promp Task & Promp Rules
     */

    // Bottom tools dock removed per sovereign user directive
    renderBottomToolsDock() {}

    openFullPromptModal(node, focusedToolId = null, initialTab = null) {
      if (!node) return;
      if (node.type === 'trigger' || (node.id && node.id.startsWith('trg-'))) {
        this.openTriggerCockpitModal(node);
        return;
      }
      this._ensureNodeStructures(node);
      this.selectedNodeId = node.id;
      this.activeModalNode = node;

      let overlay = document.getElementById('pipeline-prompt-modal-overlay');
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'pipeline-prompt-modal-overlay';
        overlay.className = 'pipeline-prompt-modal-overlay';
        overlay.innerHTML = `
          <div class="pipeline-prompt-modal-box" id="pipeline-prompt-modal-box"></div>
        `;
        document.body.appendChild(overlay);

        overlay.addEventListener('click', (e) => {
          if (e.target === overlay) {
            this.closeFullPromptModal();
          }
        });

        window.addEventListener('keydown', (e) => {
          if (e.key === 'Escape' && overlay.classList.contains('active')) {
            this.closeFullPromptModal();
          } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && overlay.classList.contains('active')) {
            e.preventDefault();
            this.saveAndCloseModal();
          }
        });
      }

      const box = overlay.querySelector('#pipeline-prompt-modal-box');
      if (!box) return;

      // Extract current values locked to agent identity
      const effectiveAgentId = node.agentId || (node.type === 'leader' || (node.id && node.id.includes('leader')) ? 'leader' : 'mr.flow');
      node.agentId = effectiveAgentId;

      const personaName = node.name || node.personaData?.name || (effectiveAgentId === 'leader' ? 'Swarm Leader' : 'Mr. Flow');
      const personaRole = node.role || node.personaData?.role || (effectiveAgentId === 'leader' ? 'Swarm Leader' : 'Sovereign Solo Executive Agent');
      const personaIcon = node.icon || node.personaData?.icon || (effectiveAgentId === 'leader' ? '👑' : '⚡');
      const personaDesc = node.description || node.personaData?.description || (effectiveAgentId === 'leader' ? 'Commander for group mode and primary user interface orchestrator.' : 'Autonomous multi-disciplinary agent equipped with unrestricted access to sovereign tools.');

      const taskPromptVal = node.taskPrompt || node.taskData?.prompt || node.taskData?.objective || '';
      const rulePromptVal = node.rulePrompt || node.rulesData?.prompt || '';

      // Live connections for Port 1 and Port 2
      const out1Conn = this.connections.find(c => c.from === node.id && (c.fromPort || 'out-1') === 'out-1');
      const out2Conn = this.connections.find(c => c.from === node.id && c.fromPort === 'out-2');
      const target1 = out1Conn ? (this.nodes.find(n => n.id === out1Conn.to)?.role || out1Conn.to) : '<span style="color:#64748b; font-style:italic;">Not connected (Wire from Port 1)</span>';
      const target2 = out2Conn ? (this.nodes.find(n => n.id === out2Conn.to)?.role || out2Conn.to) : '<span style="color:#64748b; font-style:italic;">Not connected (Wire from Port 2)</span>';

      // 1. Models Table Rows Generator
      const activeModelId = node.modelConfig?.modelId || 'gemini-3.8-flash-high';
      const renderCockpitModelRows = (modelsList, currentActiveId) => {
        const list = Array.isArray(modelsList) && modelsList.length > 0 ? modelsList : ANTIGRAVITY_MODELS;
        return list.map(m => {
          const isSelected = m.id === currentActiveId;
          const tier = m.tier || m.badge || (m.provider === 'ollama' ? 'Local LLM' : (m.provider === '9router' ? 'Proxy Router' : 'Flagship Thinking'));
          const latency = m.latency || (m.provider === 'ollama' ? '0.1s (Local GPU)' : (m.provider === '9router' ? 'Routed' : '0.8s (Fast)'));
          const context = m.context || '1,000,000 tokens';
          const badgeText = m.provider === 'ollama' ? 'ACTIVE OLLAMA' : (m.provider === '9router' ? 'ACTIVE 9ROUTER' : 'ACTIVE GOOGLE');
          const badgeClass = m.provider === 'ollama' ? 'pipeline-badge-safe' : (m.provider === '9router' ? 'pipeline-badge-high' : 'pipeline-badge-safe');
          return `
            <tr class="pipeline-model-row ${isSelected ? 'selected' : ''}" data-model-id="${m.id}" data-model-name="${m.name}" data-provider="${m.provider || 'gravity'}" style="cursor:pointer;">
              <td style="text-align:center;">
                <input type="radio" name="cockpit-model-radio" value="${m.id}" ${isSelected ? 'checked' : ''} style="cursor:pointer; accent-color:#00f2fe;" />
              </td>
              <td>
                <strong style="color:${isSelected ? '#00f2fe' : '#f1f5f9'}; font-size:12.5px;">${m.name}</strong>
                <div style="font-size:10px; color:#64748b; font-family:monospace;">${m.id}</div>
              </td>
              <td><span class="pipeline-chip-tag" style="color:#7dd3fc;">${tier}</span></td>
              <td style="color:#10b981; font-weight:700; font-size:11px;">${latency}</td>
              <td style="color:#cbd5e1; font-size:11px;">${context}</td>
              <td><span class="${badgeClass}">${badgeText}</span></td>
            </tr>
          `;
        }).join('');
      };
      const modelsRowsHtml = renderCockpitModelRows(ANTIGRAVITY_MODELS, activeModelId);

      // 2. Tools Governance Rows
      const isMasterAllowAll = node.toolGovernance?.allowAll !== false;
      const allowedTools = (node.toolGovernance?.allowedTools || []).filter(id => !isPromptOrEnclaveTriggeredTool(id));
      const deniedTools = (node.toolGovernance?.deniedTools || []).filter(id => !isPromptOrEnclaveTriggeredTool(id));
      const rawToolsList = this.availableTools || SOVEREIGN_LOCAL_TOOLS;
      const toolsList = rawToolsList.filter(t => !isPromptOrEnclaveTriggeredTool(t.id));
      const rulesCount = toolsList.filter(t => t.risk && t.risk !== 'SAFE' && t.risk !== 'LOW').length;
      const safeCount = toolsList.length - rulesCount;
      const toolsRowsHtml = toolsList.map(t => {
        const isAllowed = isMasterAllowAll ? true : (allowedTools.includes(t.id) && !deniedTools.includes(t.id));
        let badgeClass = 'pipeline-badge-safe';
        if (t.risk === 'CRITICAL') badgeClass = 'pipeline-badge-critical';
        else if (t.risk === 'HIGH') badgeClass = 'pipeline-badge-high';
        else if (t.risk === 'MODERATE') badgeClass = 'pipeline-badge-moderate';

        const isSafe = !t.risk || t.risk === 'SAFE' || t.risk === 'LOW';
        const guardianBtnHtml = isSafe
          ? `<span class="pipeline-chip-tag" style="color:#10b981; font-size:10px; border-color:rgba(16,185,129,0.25);">🟢 Safe &bull; Auto</span>`
          : `<button type="button" class="pipeline-guardian-expand-btn" data-tool-id="${t.id}" title="Configure Rules Policy for ${node.role || node.id}">
               🛡️ Rules Policy
             </button>`;

        const guardian = !isSafe ? getNodeToolGuardian(node, t) : null;
        const drawerHtml = !isSafe ? renderGuardianDrawerHtml(t, guardian, node, this.nodes) : '';
        const rulesCategoryTag = !isSafe
          ? `<span class="pipeline-chip-tag" style="color:#f59e0b; border-color:rgba(245,158,11,0.4); font-weight:700; font-size:10px; margin-right:4px;">🛡️ Has Rules</span>`
          : '';

        return `
          <tr class="pipeline-tool-row" data-tool-id="${t.id}" data-has-rules="${!isSafe ? 'true' : 'false'}">
            <td><code style="color:#38bdf8; font-weight:700; font-size:11.5px;">${t.id}</code></td>
            <td>${rulesCategoryTag}<span class="pipeline-chip-tag">${t.category}</span></td>
            <td style="font-size:11.5px; color:#cbd5e1;">${t.desc || ''}</td>
            <td><span class="${badgeClass}">${t.risk}</span></td>
            <td style="text-align:center;">
              <div style="display:flex; align-items:center; justify-content:center; gap:8px;">
                ${guardianBtnHtml}
                <label class="pipeline-switch" style="margin:0;">
                  <input type="checkbox" class="tool-switch" data-tool-id="${t.id}" ${isAllowed ? 'checked' : ''} />
                  <span class="pipeline-slider"></span>
                </label>
              </div>
            </td>
          </tr>
          ${drawerHtml}
        `;
      }).join('');

      // 3. Skills Catalog Rows
      const activeSkillsList = node.skillsConfig?.activeSkills || [];
      const skillsRowsHtml = DYNAMIC_LOCAL_SKILLS.map(s => {
        const isSkillActive = activeSkillsList.includes(s.id);
        const originBadge = '<span class="pipeline-chip-tag" style="color:#38bdf8; border-color:rgba(56,189,248,0.3);">Local Skills</span>';

        return `
          <tr class="pipeline-skill-row" data-skill-id="${s.id}">
            <td>
              <strong style="color:${isSkillActive ? '#00f2fe' : '#f1f5f9'}; font-size:12px;">${s.name}</strong>
              <div style="font-size:10px; color:#64748b; font-family:monospace;">${s.id}</div>
            </td>
            <td>${originBadge}</td>
            <td><span style="font-size:11px; color:#94a3b8;">${s.category}</span></td>
            <td style="font-size:11.5px; color:#cbd5e1;">${s.desc}</td>
            <td style="text-align:center;">
              <label class="pipeline-switch">
                <input type="checkbox" class="skill-switch" data-skill-id="${s.id}" ${isSkillActive ? 'checked' : ''} />
                <span class="pipeline-slider"></span>
              </label>
            </td>
          </tr>
        `;
      }).join('');

      // Build full cockpit HTML with 7 tabs
      box.innerHTML = `
        <!-- Cockpit Header -->
        <div class="pipeline-modal-header">
          <div class="pipeline-modal-title-wrap">
            <span class="pipeline-modal-icon" id="modal-header-icon-disp">${personaIcon}</span>
            <div>
              <div class="pipeline-modal-title" id="modal-node-title-disp">Cockpit Configuration: ${personaRole}</div>
              <div style="font-size:10px; display:flex; gap:8px; align-items:center;">
                <span style="color:#38bdf8; font-weight:700;">NODE ID: ${node.id}</span>
                <span style="color:#64748b;">•</span>
                <span style="color:#94a3b8; font-weight:700;">TYPE: ${(node.type || 'agent').toUpperCase()}</span>
                ${node.isLocked ? '<span class="pipeline-badge-critical" style="margin-left:4px;">IMMUTABLE ROOT 0 (@lock)</span>' : ''}
              </div>
            </div>
            <div style="margin-left: 18px;">
              <select class="cockpit-agent-select" id="cockpit-agent-select" title="Switch Agent Studio Target">
                ${(this.nodes || []).map(n => `<option value="${n.id}" ${n.id === node.id ? 'selected' : ''}>${n.icon || '🤖'} ${n.role || n.name || n.id}</option>`).join('')}
              </select>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-size:11px; color:#10b981; font-weight:700;">● Live Swarm Synchronized</div>
            <button class="pipeline-modal-close-btn" id="btn-close-modal" title="Close (Esc)">✕</button>
          </div>
        </div>

        <!-- 7 Cockpit Tabs Bar (Style, Persona, Rules, Task, Model, Tools, Skills) -->
        <div class="pipeline-cockpit-tabs-bar" id="pipeline-cockpit-tabs-bar">
          <button type="button" class="pipeline-cockpit-tab-btn active" data-tab="style">
            <span>🎨</span> Style & Outfit <span class="tab-badge">3D Wardrobe</span>
          </button>
          <button type="button" class="pipeline-cockpit-tab-btn" data-tab="persona">
            <span>👤</span> Persona <span class="tab-badge">Identity</span>
          </button>
          <button type="button" class="pipeline-cockpit-tab-btn" data-tab="rules">
            <span>🛡️</span> Rules <span class="tab-badge">2 Ports</span>
          </button>
          <button type="button" class="pipeline-cockpit-tab-btn" data-tab="task">
            <span>📋</span> Task <span class="tab-badge">SLA</span>
          </button>
          <button type="button" class="pipeline-cockpit-tab-btn" data-tab="model">
            <span>🧠</span> Model Selection <span class="tab-badge">Antigravity</span>
          </button>
          <button type="button" class="pipeline-cockpit-tab-btn" data-tab="tools">
            <span>🔧</span> Tools & Guardians <span class="tab-badge">${toolsList.length} Tools</span>
          </button>
          <button type="button" class="pipeline-cockpit-tab-btn" data-tab="skills">
            <span>⚡</span> Skills Catalog <span class="tab-badge" id="tab-skills-count">${activeSkillsList.length} Active</span>
          </button>
        </div>

        <!-- Cockpit Panes Body -->
        <div class="pipeline-cockpit-panes-body">

          <!-- 1. Style & Outfit Pane (Character Studio - Before Persona) -->
          <div class="pipeline-cockpit-pane active" id="cockpit-pane-style">
            <div class="pipeline-table-card">
              <div class="pipeline-table-header-row">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span style="font-size:16px;">🎨</span>
                  <h4 style="margin:0; font-size:13px; font-weight:700; color:#f8fafc;">3D Agent Wardrobe & Character Studio</h4>
                  <span class="pipeline-chip-tag" style="color:#00f2fe; font-family:monospace; font-size:11px;">system/subagent/${effectiveAgentId}/style.json</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                  <span id="style-sync-indicator" style="font-size:11px; color:#10b981; font-weight:600;">● Synced to Disk</span>
                  <button type="button" id="btn-save-agent-style" class="pipeline-modal-btn primary" style="padding:4px 12px; font-size:11px; height:28px;">
                    💾 Save Style
                  </button>
                </div>
              </div>

              <!-- Quick Presets Carousel -->
              <div class="pipeline-style-presets-bar">
                <span style="font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px;">Quick Presets:</span>
                <div class="pipeline-preset-pills" id="style-preset-pills">
                  <button type="button" class="pipeline-preset-pill active" data-preset="cyber_neon">⚡ Cyber Neon</button>
                  <button type="button" class="pipeline-preset-pill" data-preset="imperial_gold">👑 Imperial Gold</button>
                  <button type="button" class="pipeline-preset-pill" data-preset="executive_tuxedo">💼 Executive Tuxedo</button>
                  <button type="button" class="pipeline-preset-pill" data-preset="tactical_sentinel">🛡️ Tactical Sentinel</button>
                  <button type="button" class="pipeline-preset-pill" data-preset="quantum_lab">🥼 Quantum Lab</button>
                  <button type="button" class="pipeline-preset-pill" data-preset="stealth_shadow">🥷 Stealth Shadow</button>
                </div>
              </div>

              <!-- 2-Column Split: Interactive 3D Character Turntable + Outfit Customizer -->
              <div class="pipeline-style-grid-container">
                <!-- Left: 3D Live Character Turntable & Identity Badge -->
                <div class="pipeline-style-preview-col">
                  <div class="pipeline-style-canvas-wrap">
                    <canvas id="agent-style-turntable-canvas" width="340" height="340"></canvas>
                    <div class="pipeline-style-turntable-badge">
                      <span id="preview-preset-badge">⚡ Cyber Neon</span>
                      <span style="font-size:9.5px; color:#64748b;">(Drag to rotate 360°)</span>
                    </div>
                  </div>
                  <div class="pipeline-style-head-notice">
                    <span>🔒 Head Lock Rule</span>: Chibi Cyber Helmet shape is sacred. Visor & Eye luminescence adapt to outfit color.
                  </div>
                </div>

                <!-- Right: Customizer Form Controls -->
                <div class="pipeline-style-controls-col">
                  <div class="pipeline-modal-grid-2">
                    <div class="pipeline-modal-form-row">
                      <label class="pipeline-modal-label">Suit Cut & Cutout</label>
                      <select class="pipeline-modal-select" id="style-suit-cut">
                        <option value="cyber_suit" selected>⚡ Cyber Jumpsuit (Core Chassis)</option>
                        <option value="executive_blazer">💼 Executive Blazer & Silk Tie</option>
                        <option value="tactical_vest">🛡️ Tactical Combat Vest & Plates</option>
                        <option value="lab_coat">🥼 Quantum Lab Coat (Long Flaps)</option>
                        <option value="stealth_hoodie">🥷 Stealth Urban Tech Hoodie</option>
                      </select>
                    </div>
                    <div class="pipeline-modal-form-row">
                      <label class="pipeline-modal-label">Chest Reactor / Crest</label>
                      <select class="pipeline-modal-select" id="style-chest-reactor">
                        <option value="arc_reactor" selected>⚡ Arc Reactor Core (Luminescent)</option>
                        <option value="flowork_f">👑 Flowork 'F' Gold Crest</option>
                        <option value="minimal_badge">🔘 Minimalist Titanium Plate</option>
                        <option value="none">🚫 Stealth Seamless (No Core)</option>
                      </select>
                    </div>
                  </div>

                  <!-- Color Pickers Row 1 -->
                  <div class="pipeline-modal-grid-2">
                    <div class="pipeline-modal-form-row">
                      <label class="pipeline-modal-label">Primary Suit Color (Baju Utama)</label>
                      <div class="pipeline-color-picker-wrap">
                        <input type="color" id="style-primary-color" value="#00f2fe" class="pipeline-color-input" />
                        <input type="text" id="style-primary-hex" value="#00f2fe" class="pipeline-modal-input" style="font-family:monospace; text-transform:uppercase;" />
                      </div>
                      <div class="pipeline-swatches-row" data-target="primary">
                        <span class="swatch" data-color="#00f2fe" style="background:#00f2fe;" title="Cyan"></span>
                        <span class="swatch" data-color="#f59e0b" style="background:#f59e0b;" title="Gold"></span>
                        <span class="swatch" data-color="#a855f7" style="background:#a855f7;" title="Purple"></span>
                        <span class="swatch" data-color="#10b981" style="background:#10b981;" title="Emerald"></span>
                        <span class="swatch" data-color="#ef4444" style="background:#ef4444;" title="Red"></span>
                        <span class="swatch" data-color="#f1f5f9" style="background:#f1f5f9;" title="Platinum"></span>
                        <span class="swatch" data-color="#09090b" style="background:#09090b;" title="Obsidian"></span>
                      </div>
                    </div>

                    <div class="pipeline-modal-form-row">
                      <label class="pipeline-modal-label">Secondary / Trim Accent (Lis & Kerah)</label>
                      <div class="pipeline-color-picker-wrap">
                        <input type="color" id="style-secondary-color" value="#7f00ff" class="pipeline-color-input" />
                        <input type="text" id="style-secondary-hex" value="#7f00ff" class="pipeline-modal-input" style="font-family:monospace; text-transform:uppercase;" />
                      </div>
                      <div class="pipeline-swatches-row" data-target="secondary">
                        <span class="swatch" data-color="#7f00ff" style="background:#7f00ff;" title="Violet"></span>
                        <span class="swatch" data-color="#00f2fe" style="background:#00f2fe;" title="Cyan"></span>
                        <span class="swatch" data-color="#f59e0b" style="background:#f59e0b;" title="Gold"></span>
                        <span class="swatch" data-color="#09090b" style="background:#09090b;" title="Obsidian"></span>
                        <span class="swatch" data-color="#38bdf8" style="background:#38bdf8;" title="Sky"></span>
                        <span class="swatch" data-color="#ec4899" style="background:#ec4899;" title="Pink"></span>
                      </div>
                    </div>
                  </div>

                  <!-- Color Pickers Row 2 -->
                  <div class="pipeline-modal-grid-2">
                    <div class="pipeline-modal-form-row">
                      <label class="pipeline-modal-label">Visor & Eye Luminescence</label>
                      <div class="pipeline-color-picker-wrap">
                        <input type="color" id="style-visor-glow" value="#00f2fe" class="pipeline-color-input" />
                        <input type="text" id="style-visor-hex" value="#00f2fe" class="pipeline-modal-input" style="font-family:monospace; text-transform:uppercase;" />
                      </div>
                    </div>

                    <div class="pipeline-modal-form-row">
                      <label class="pipeline-modal-label">Thruster Ion Flame (Hover/Flight)</label>
                      <div class="pipeline-color-picker-wrap">
                        <input type="color" id="style-thruster-color" value="#00f2fe" class="pipeline-color-input" />
                        <input type="text" id="style-thruster-hex" value="#00f2fe" class="pipeline-modal-input" style="font-family:monospace; text-transform:uppercase;" />
                      </div>
                    </div>
                  </div>

                  <!-- Accessories Row -->
                  <div class="pipeline-modal-grid-2">
                    <div class="pipeline-modal-form-row">
                      <label class="pipeline-modal-label">Shoulder Epaulets & Pads</label>
                      <select class="pipeline-modal-select" id="style-shoulders">
                        <option value="smooth" selected>Smooth Ergonomic Shoulders</option>
                        <option value="epaulets">👑 Gold Imperial Epaulets</option>
                        <option value="armor_plates">🛡️ Armored Composite Pauldrons</option>
                      </select>
                    </div>
                    <div class="pipeline-modal-form-row">
                      <label class="pipeline-modal-label">Cape / Cloak</label>
                      <select class="pipeline-modal-select" id="style-cape">
                        <option value="false" selected>No Cape (Aero Dynamics)</option>
                        <option value="true">👑 Imperial Royal Cape</option>
                      </select>
                    </div>
                  </div>

                  <!-- Tool Visual Theme Selector & Live Widget Preview -->
                  <div class="pipeline-tool-style-section">
                    <div class="pipeline-tool-style-header">
                      <h5><span>🛠️</span> Tool Card Output Style (Chat & Telemetry)</h5>
                      <span class="pipeline-chip-tag" style="color:#00f2fe; font-size:10px;">Select Visual Preset</span>
                    </div>

                    <div class="pipeline-tool-theme-grid" id="tool-theme-options">
                      <div class="pipeline-tool-theme-option active" data-theme="cyber_neon">
                        <div class="theme-title">⚡ Cyber Neon</div>
                        <div class="theme-desc">Holo cyberpunk glow with cyan & purple accents.</div>
                      </div>
                      <div class="pipeline-tool-theme-option" data-theme="executive_glass">
                        <div class="theme-title">💼 Executive Glass</div>
                        <div class="theme-desc">Frosted translucent blur, luxury slate & gold.</div>
                      </div>
                      <div class="pipeline-tool-theme-option" data-theme="retro_crt">
                        <div class="theme-title">📟 Retro CRT</div>
                        <div class="theme-desc">Monospace UNIX terminal with phosphor scanlines.</div>
                      </div>
                      <div class="pipeline-tool-theme-option" data-theme="minimalist">
                        <div class="theme-title">📄 Minimalist</div>
                        <div class="theme-desc">Compact flat dark slate, ultra-low visual noise.</div>
                      </div>
                    </div>

                    <!-- Live Tool Card Preview Box -->
                    <div class="pipeline-tool-preview-container">
                      <div class="pipeline-tool-preview-badge">
                        <span>LIVE CHAT WIDGET PREVIEW</span>
                        <span id="preview-tool-theme-label" style="color:#00f2fe; font-family:monospace;">Theme: cyber_neon</span>
                      </div>
                      <div class="pipeline-sample-tool-card fl-tool-theme-card" id="sample-tool-preview-card" data-tool-theme="cyber_neon">
                        <div class="pipeline-sample-tool-card-header">
                          <span class="tool-title">⚡ RUN_COMMAND &bull; <code>cargo build --release</code></span>
                          <span style="font-size:9.5px; opacity:0.8;">Exit Code 0 &bull; 2.4s</span>
                        </div>
                        <div class="pipeline-sample-tool-card-body">
                          <div style="opacity:0.9;">Compiling core v1.0.0 (/flowork/core)...</div>
                          <div style="color:var(--tool-accent, #00f2fe); font-weight:600; margin-top:2px;">Finished release [optimized] target(s) in 2.38s</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Toggle Raw JSON -->
                  <div style="margin-top:10px;">
                    <button type="button" class="pipeline-mini-btn" id="btn-toggle-raw-style-json">👁️ Inspect Raw style.json</button>
                    <div id="raw-style-json-box" style="display:none; margin-top:8px;">
                      <textarea class="pipeline-modal-textarea" id="txt-raw-style-json" rows="6" style="font-family:monospace; font-size:11px;"></textarea>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 2. Persona Pane -->
          <div class="pipeline-cockpit-pane" id="cockpit-pane-persona">
            <div class="pipeline-table-card">
              <div class="pipeline-table-header-row">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span style="font-size:16px;">👤</span>
                  <h4 style="margin:0; font-size:13px; font-weight:700; color:#f8fafc;">Persona Soul Directives</h4>
                  <span class="pipeline-chip-tag" style="color:#38bdf8; font-family:monospace; font-size:11px;">system/subagent/${effectiveAgentId}/persona.md</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                  <span id="persona-sync-indicator" style="font-size:11px; color:#10b981; font-weight:600;">● Synced to Disk</span>
                  <button type="button" id="btn-save-agent-persona" class="pipeline-modal-btn primary" style="padding:4px 12px; font-size:11px; height:28px;">
                    💾 Save Persona
                  </button>
                </div>
              </div>
              <div style="padding:16px 20px; display:flex; flex-direction:column; gap:8px;">
                <textarea class="pipeline-modal-textarea" id="modal-persona-system-prompt" rows="18" style="font-family:monospace; font-size:12.5px; line-height:1.55; width:100%; min-height:360px;" placeholder="Enter persona soul directives without identity fluff...">${node.personaData.systemPrompt || ''}</textarea>
              </div>
            </div>
          </div>

          <!-- 2. Rules Pane (Clean 1-Column Prompt) -->
          <div class="pipeline-cockpit-pane" id="cockpit-pane-rules">
            <div class="pipeline-table-card">
              <div class="pipeline-table-header-row">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span style="font-size:16px;">🛡️</span>
                  <h4 style="margin:0; font-size:13px; font-weight:700; color:#f8fafc;">Rules & Operational Guardrails</h4>
                  <span class="pipeline-chip-tag" style="color:#fb7185; font-family:monospace; font-size:11px;">system/subagent/${effectiveAgentId}/rules.md</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                  <span id="rules-sync-indicator" style="font-size:11px; color:#10b981; font-weight:600;">● Synced to Disk</span>
                  <button type="button" id="btn-save-agent-rules" class="pipeline-modal-btn primary" style="padding:4px 12px; font-size:11px; height:28px;">
                    💾 Save Rules
                  </button>
                </div>
              </div>
              <div style="padding:16px 20px; display:flex; flex-direction:column; gap:14px;">
                <div class="pipeline-modal-form-row">
                  <textarea class="pipeline-modal-textarea" id="modal-rule-prompt" rows="18" style="min-height: 380px; font-family:'JetBrains Mono', monospace; font-size:12px; line-height:1.6;" placeholder="Define operational rules and guardrails...">${rulePromptVal}</textarea>
                </div>
              </div>
            </div>
          </div>

          <!-- 3. Task Pane (Clean 1-Column Prompt) -->
          <div class="pipeline-cockpit-pane" id="cockpit-pane-task">
            <div class="pipeline-table-card">
              <div class="pipeline-table-header-row">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span style="font-size:16px;">📋</span>
                  <h4 style="margin:0; font-size:13px; font-weight:700; color:#f8fafc;">Task Scope & Mission Instructions</h4>
                  <span class="pipeline-chip-tag" style="color:#818cf8; font-family:monospace; font-size:11px;">system/subagent/${effectiveAgentId}/task.md</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                  <span id="task-sync-indicator" style="font-size:11px; color:#10b981; font-weight:600;">● Synced to Disk</span>
                  <button type="button" id="btn-save-agent-task" class="pipeline-modal-btn primary" style="padding:4px 12px; font-size:11px; height:28px;">
                    💾 Save Task
                  </button>
                </div>
              </div>
              <div style="padding:16px 20px; display:flex; flex-direction:column; gap:14px;">
                <div class="pipeline-modal-form-row">
                  <textarea class="pipeline-modal-textarea" id="modal-task-prompt" rows="18" style="min-height: 380px; font-family:'JetBrains Mono', monospace; font-size:12px; line-height:1.6;" placeholder="Define task scope and mission instructions...">${taskPromptVal}</textarea>
                </div>
              </div>
            </div>
          </div>

          <!-- 4. Model Selection Pane (Antigravity Models + Combo Auto-Balancer) -->
          <div class="pipeline-cockpit-pane" id="cockpit-pane-model">
            <div class="pipeline-table-card">
              <div class="pipeline-table-header-row">
                <h4><span>⚡</span> Connection Target & Account Load Balancer</h4>
                <span class="pipeline-chip-tag" style="color:#f59e0b;">Multi-Account Balancing</span>
              </div>
              <div style="padding:16px 20px; display:flex; flex-direction:column; gap:12px;">
                <div style="font-size:11.5px; color:#94a3b8;">
                  Select the account binding logic for this node. The <strong style="color:#f59e0b;">Combo (Auto-Balancer)</strong> mode distributes API requests across all available authenticated accounts to optimize throughput and bypass rate limits.
                </div>
                <div class="pipeline-modal-grid-2">
                  <div class="pipeline-modal-form-row">
                    <label class="pipeline-modal-label">Account Binding Mode</label>
                    <select class="pipeline-modal-select" id="modal-model-account-mode">
                      <option value="combo" ${node.modelConfig.accountMode === 'combo' ? 'selected' : ''}>⚡ Combo (Auto-Balancer) [DEFAULT - Recommended]</option>
                      <option value="account_slot_1" ${node.modelConfig.accountMode === 'account_slot_1' ? 'selected' : ''}>Direct Account Slot 1 (Primary)</option>
                      <option value="account_slot_2" ${node.modelConfig.accountMode === 'account_slot_2' ? 'selected' : ''}>Direct Account Slot 2 (Secondary)</option>
                      <option value="account_slot_3" ${node.modelConfig.accountMode === 'account_slot_3' ? 'selected' : ''}>Direct Account Slot 3 (Tertiary)</option>
                    </select>
                  </div>
                  <div class="pipeline-modal-form-row">
                    <label class="pipeline-modal-label">
                      <span>Model Temperature (Creativity vs Determinism)</span>
                      <span id="disp-temp-val" style="color:#38bdf8; font-weight:800;">${node.modelConfig.temperature || 0.2}</span>
                    </label>
                    <input type="range" class="pipeline-modal-range" id="modal-model-temperature" min="0.0" max="1.0" step="0.05" value="${node.modelConfig.temperature || 0.2}" style="width:100%; accent-color:#38bdf8; cursor:pointer;" />
                  </div>
                </div>
              </div>
            </div>

            <div class="pipeline-table-card">
              <div class="pipeline-table-header-row" style="flex-wrap:wrap; gap:10px;">
                <div style="display:flex; align-items:center; gap:12px;">
                  <h4><span>🧠</span> Models Catalog (Official Dropdown Match)</h4>
                  <div class="pipeline-model-provider-tabs" id="cockpit-model-provider-tabs" style="display:flex; gap:6px;">
                    <button type="button" class="pipeline-mini-btn active" data-provider="gravity" id="btn-cockpit-prov-gravity">⚡ Gravity</button>
                    <button type="button" class="pipeline-mini-btn" data-provider="ollama" id="btn-cockpit-prov-ollama">🦙 Ollama</button>
                    <button type="button" class="pipeline-mini-btn" data-provider="9router" id="btn-cockpit-prov-9router">🔀 9Router</button>
                  </div>
                </div>
                <span class="pipeline-chip-tag" id="cockpit-models-active-tag" style="color:#38bdf8;">Tab 5 of 7</span>
              </div>
              <table class="pipeline-data-table" id="table-models-list">
                <thead>
                  <tr>
                    <th style="width:6%; text-align:center;">Select</th>
                    <th style="width:30%;">Model Name & ID</th>
                    <th style="width:20%;">Specialization Tier</th>
                    <th style="width:14%;">Latency Profile</th>
                    <th style="width:14%;">Context Window</th>
                    <th style="width:16%;">Engine Status</th>
                  </tr>
                </thead>
                <tbody id="tbody-cockpit-models-list">
                  ${modelsRowsHtml}
                </tbody>
              </table>
            </div>
          </div>

          <!-- 5. Tool Governance Pane (${toolsList.length} Local Tools • Zero Cloudflare) -->
          <div class="pipeline-cockpit-pane" id="cockpit-pane-tools">
            <div class="pipeline-table-card">
              <div class="pipeline-table-header-row">
                <h4><span>🔧</span> Universal Tool Governance & Execution Sandbox (${toolsList.length} Local Tools)</h4>
                <span class="pipeline-chip-tag" style="color:#10b981;">Tab 5 of 6</span>
                <div class="pipeline-table-actions">
                  <button type="button" class="pipeline-mini-btn" id="btn-tools-filter-rules" style="color:#f59e0b; border-color:rgba(245,158,11,0.4); font-weight:700;">🛡️ With Rules Only (${rulesCount})</button>
                  <button type="button" class="pipeline-mini-btn primary" id="btn-tools-allow-all">✓ Allow All (${toolsList.length})</button>
                  <button type="button" class="pipeline-mini-btn" id="btn-tools-safe-preset">🛡️ Safe Preset</button>
                  <button type="button" class="pipeline-mini-btn danger" id="btn-tools-deny-all">✕ Deny All</button>
                </div>
              </div>

              <!-- Role-Based Tool Presets (Coder, DevOps, Security, Researcher, Full Sovereign) -->
              <div style="padding:10px 20px; background:rgba(15,23,42,0.7); border-bottom:1px solid rgba(255,255,255,0.08); display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                  <span style="font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px;">Role Presets:</span>
                  <div style="display:flex; gap:6px; flex-wrap:wrap;" id="tools-role-presets">
                    <button type="button" class="pipeline-preset-pill" data-role-pack="coder">💻 Coder / Architect</button>
                    <button type="button" class="pipeline-preset-pill" data-role-pack="devops">🛡️ DevOps / SRE</button>
                    <button type="button" class="pipeline-preset-pill" data-role-pack="security">🔍 Security & Pentest</button>
                    <button type="button" class="pipeline-preset-pill" data-role-pack="researcher">🌐 Researcher</button>
                    <button type="button" class="pipeline-preset-pill active" data-role-pack="full">👑 Full Sovereign (${toolsList.length})</button>
                  </div>
                </div>
                <div style="font-size:10.5px; color:#64748b; display:flex; gap:10px; align-items:center;">
                  <span>🟢 Safe (Auto-Allowed)</span>
                  <span>🛡️ Active (Rules Policy)</span>
                </div>
              </div>
              <div style="padding:12px 20px; background:rgba(10,15,30,0.6); border-bottom:1px solid rgba(255,255,255,0.06); display:flex; align-items:center; justify-content:space-between;">
                <div>
                  <strong style="font-size:12px; color:#f1f5f9;">Master Governance Switch: Allow All Tools</strong>
                  <div style="font-size:10.5px; color:#94a3b8;">When active, all ${toolsList.length} local tools are automatically authorized without individual restrictions. Served 100% locally from host daemon.</div>
                </div>
                <label class="pipeline-switch">
                  <input type="checkbox" id="modal-tool-master-allow-all" ${isMasterAllowAll ? 'checked' : ''} />
                  <span class="pipeline-slider"></span>
                </label>
              </div>

              <!-- Search and Filter Bar for ${toolsList.length} Tools -->
              <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 20px; background:rgba(15,23,42,0.4); border-bottom:1px solid rgba(255,255,255,0.06); gap:12px; flex-wrap:wrap;">
                <input type="text" id="inp-modal-tools-search" class="pipeline-dock-search" placeholder="Search ${toolsList.length} local tools by name, tag, or category..." style="width:300px; padding:6px 10px;" />
                <div style="display:flex; gap:6px; flex-wrap:wrap;" id="modal-tools-filter-pills">
                  <button type="button" class="pipeline-dock-pill active" data-filter="all">All (${toolsList.length})</button>
                  <button type="button" class="pipeline-dock-pill" data-filter="rules" style="color:#f59e0b; border-color:rgba(245,158,11,0.5); font-weight:700; background:rgba(245,158,11,0.12);">🛡️ With Rules (${rulesCount})</button>
                  <button type="button" class="pipeline-dock-pill" data-filter="safe" style="color:#10b981; border-color:rgba(16,185,129,0.3);">🟢 Safe Tools (${safeCount})</button>
                  <button type="button" class="pipeline-dock-pill" data-filter="filesystem">Filesystem</button>
                  <button type="button" class="pipeline-dock-pill" data-filter="terminal">Terminal</button>
                  <button type="button" class="pipeline-dock-pill" data-filter="network">Network</button>
                  <button type="button" class="pipeline-dock-pill" data-filter="visual">Visual</button>
                  <button type="button" class="pipeline-dock-pill" data-filter="general">General</button>
                </div>
              </div>

              <table class="pipeline-data-table" id="table-tools-governance">
                <thead>
                  <tr>
                    <th style="width:18%;">Tool Identifier</th>
                    <th style="width:13%;">Category</th>
                    <th style="width:38%;">Capability Scope & Description</th>
                    <th style="width:11%;">Risk Rating</th>
                    <th style="width:20%; text-align:center;">Authorization & Guardian</th>
                  </tr>
                </thead>
                <tbody id="tbody-tools-governance">
                  ${toolsRowsHtml}
                </tbody>
              </table>
            </div>
          </div>

          <!-- 6. Skills Catalog Pane -->
          <div class="pipeline-cockpit-pane" id="cockpit-pane-skills">
            <div class="pipeline-table-card">
              <div class="pipeline-table-header-row">
                <h4><span>⚡</span> Local Sovereign Skills Catalog (skills/)</h4>
                <span class="pipeline-chip-tag" style="color:#a855f7;">Tab 6 of 6</span>
                <div class="pipeline-table-actions">
                  <button type="button" class="pipeline-mini-btn primary" id="btn-skills-enable-all">✓ Enable All Skills</button>
                  <button type="button" class="pipeline-mini-btn" id="btn-skills-sovereign-preset">👑 Default Sovereign Skills</button>
                  <button type="button" class="pipeline-mini-btn danger" id="btn-skills-disable-all">✕ Disable All</button>
                </div>
              </div>
              <div style="padding:10px 20px; background:rgba(10,15,30,0.6); border-bottom:1px solid rgba(255,255,255,0.06); font-size:11px; color:#94a3b8;">
                Discovered specialized skills strictly from local <code>skills/</code> directory. Toggle skills to attach them to this node.
              </div>
              <table class="pipeline-data-table" id="table-skills-catalog">
                <thead>
                  <tr>
                    <th style="width:20%;">Skill Name & ID</th>
                    <th style="width:14%;">Origin Source</th>
                    <th style="width:16%;">Specialization</th>
                    <th style="width:40%;">Operational Scope & Description</th>
                    <th style="width:10%; text-align:center;">Active</th>
                  </tr>
                </thead>
                <tbody>
                  ${skillsRowsHtml}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      `;

      // 0. Agent Switcher inside Cockpit
      const agentSelect = box.querySelector('#cockpit-agent-select');
      if (agentSelect) {
        agentSelect.addEventListener('change', (e) => {
          const selId = e.target.value;
          const nextNode = (this.nodes || []).find(n => n.id === selId);
          if (nextNode) {
            this.openFullPromptModal(nextNode);
          }
        });
      }

      // 1. Tab Switching
      const tabBtns = box.querySelectorAll('.pipeline-cockpit-tab-btn');
      const panes = box.querySelectorAll('.pipeline-cockpit-pane');
      tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const tabId = btn.getAttribute('data-tab');
          tabBtns.forEach(b => b.classList.remove('active'));
          panes.forEach(p => p.classList.remove('active'));
          btn.classList.add('active');
          const targetPane = box.querySelector(`#cockpit-pane-${tabId}`);
          if (targetPane) targetPane.classList.add('active');
        });
      });

      // 1. Style & 3D Wardrobe Tab Bindings (Locked to Subagent ID)
      const paneStyle = box.querySelector('#cockpit-pane-style');
      if (paneStyle && effectiveAgentId) {
        const selSuitCut = paneStyle.querySelector('#style-suit-cut');
        const selChestReactor = paneStyle.querySelector('#style-chest-reactor');
        const selShoulders = paneStyle.querySelector('#style-shoulders');
        const selCape = paneStyle.querySelector('#style-cape');

        const inpPrimaryColor = paneStyle.querySelector('#style-primary-color');
        const inpPrimaryHex = paneStyle.querySelector('#style-primary-hex');
        const inpSecondaryColor = paneStyle.querySelector('#style-secondary-color');
        const inpSecondaryHex = paneStyle.querySelector('#style-secondary-hex');
        const inpVisorGlow = paneStyle.querySelector('#style-visor-glow');
        const inpVisorHex = paneStyle.querySelector('#style-visor-hex');
        const inpThrusterColor = paneStyle.querySelector('#style-thruster-color');
        const inpThrusterHex = paneStyle.querySelector('#style-thruster-hex');

        const btnSaveStyle = paneStyle.querySelector('#btn-save-agent-style');
        const styleSyncIndicator = paneStyle.querySelector('#style-sync-indicator');
        const previewBadge = paneStyle.querySelector('#preview-preset-badge');
        const presetPills = paneStyle.querySelectorAll('.pipeline-preset-pill');

        const btnToggleRawJson = paneStyle.querySelector('#btn-toggle-raw-style-json');
        const rawJsonBox = paneStyle.querySelector('#raw-style-json-box');
        const txtRawJson = paneStyle.querySelector('#txt-raw-style-json');

        const turntableCanvas = paneStyle.querySelector('#agent-style-turntable-canvas');
        let turntableRotation = 0;
        let isDraggingTurntable = false;
        let lastDragX = 0;

        let currentStyle = {
          version: "1.0.0",
          agent_id: effectiveAgentId,
          preset_name: effectiveAgentId === 'leader' ? "Imperial Gold" : "Cyber Neon",
          tool_style: {
            theme: effectiveAgentId === 'leader' ? "executive_glass" : "cyber_neon",
            density: "comfortable"
          },
          head: {
            locked_mesh: "default_chibi_helmet",
            visor_glow_color: effectiveAgentId === 'leader' ? "#f59e0b" : "#00f2fe",
            eye_emissive_color: effectiveAgentId === 'leader' ? "#f59e0b" : "#00f2fe"
          },
          suit: {
            style: effectiveAgentId === 'leader' ? "executive_blazer" : "cyber_suit",
            primary_color: effectiveAgentId === 'leader' ? "#f59e0b" : "#00f2fe",
            secondary_color: effectiveAgentId === 'leader' ? "#09090b" : "#7f00ff",
            accent_neon: effectiveAgentId === 'leader' ? "#f59e0b" : "#00f2fe",
            material: { roughness: 0.28, metalness: 0.55 }
          },
          accessories: {
            chest_badge: effectiveAgentId === 'leader' ? "flowork_f" : "arc_reactor",
            cape: effectiveAgentId === 'leader',
            shoulders: effectiveAgentId === 'leader' ? "epaulets" : "smooth"
          },
          limbs: {
            pants_color: "#09090b",
            boots_color: "#111827",
            thruster_plasma_color: effectiveAgentId === 'leader' ? "#f59e0b" : "#00f2fe"
          }
        };

        const STYLE_PRESETS = {
          cyber_neon: {
            preset_name: "Cyber Neon",
            suit_cut: "cyber_suit",
            chest_reactor: "arc_reactor",
            shoulders: "smooth",
            cape: "false",
            primary: "#00f2fe",
            secondary: "#7f00ff",
            visor: "#00f2fe",
            thruster: "#00f2fe",
            tool_theme: "cyber_neon"
          },
          imperial_gold: {
            preset_name: "Imperial Gold",
            suit_cut: "executive_blazer",
            chest_reactor: "flowork_f",
            shoulders: "epaulets",
            cape: "true",
            primary: "#f59e0b",
            secondary: "#09090b",
            visor: "#f59e0b",
            thruster: "#f59e0b",
            tool_theme: "executive_glass"
          },
          executive_tuxedo: {
            preset_name: "Executive Tuxedo",
            suit_cut: "executive_blazer",
            chest_reactor: "minimal_badge",
            shoulders: "smooth",
            cape: "false",
            primary: "#0f172a",
            secondary: "#f1f5f9",
            visor: "#38bdf8",
            thruster: "#38bdf8",
            tool_theme: "executive_glass"
          },
          tactical_sentinel: {
            preset_name: "Tactical Sentinel",
            suit_cut: "tactical_vest",
            chest_reactor: "arc_reactor",
            shoulders: "armor_plates",
            cape: "false",
            primary: "#14532d",
            secondary: "#22c55e",
            visor: "#22c55e",
            thruster: "#10b981",
            tool_theme: "retro_crt"
          },
          quantum_lab: {
            preset_name: "Quantum Lab",
            suit_cut: "lab_coat",
            chest_reactor: "arc_reactor",
            shoulders: "smooth",
            cape: "false",
            primary: "#f8fafc",
            secondary: "#0284c7",
            visor: "#00f2fe",
            thruster: "#00f2fe",
            tool_theme: "cyber_neon"
          },
          stealth_shadow: {
            preset_name: "Stealth Shadow",
            suit_cut: "stealth_hoodie",
            chest_reactor: "none",
            shoulders: "smooth",
            cape: "false",
            primary: "#09090b",
            secondary: "#ef4444",
            visor: "#ef4444",
            thruster: "#ef4444",
            tool_theme: "minimalist"
          }
        };

        const toolThemeOptions = paneStyle.querySelectorAll('.pipeline-tool-theme-option');
        const sampleToolPreviewCard = paneStyle.querySelector('#sample-tool-preview-card');
        const previewToolThemeLabel = paneStyle.querySelector('#preview-tool-theme-label');

        const updateToolThemeUI = (themeName) => {
          if (!themeName) themeName = 'cyber_neon';
          toolThemeOptions.forEach(opt => {
            if (opt.getAttribute('data-theme') === themeName) {
              opt.classList.add('active');
            } else {
              opt.classList.remove('active');
            }
          });
          if (sampleToolPreviewCard) {
            sampleToolPreviewCard.setAttribute('data-tool-theme', themeName);
          }
          if (previewToolThemeLabel) {
            previewToolThemeLabel.textContent = `Theme: ${themeName}`;
          }
        };

        toolThemeOptions.forEach(opt => {
          opt.addEventListener('click', () => {
            const themeKey = opt.getAttribute('data-theme');
            if (!currentStyle.tool_style) currentStyle.tool_style = { density: 'comfortable' };
            currentStyle.tool_style.theme = themeKey;
            updateToolThemeUI(themeKey);
            if (styleSyncIndicator) {
              styleSyncIndicator.textContent = '○ Unsaved Changes';
              styleSyncIndicator.style.color = '#f59e0b';
            }
            if (txtRawJson) txtRawJson.value = JSON.stringify(currentStyle, null, 2);
          });
        });

        const syncInputsFromState = () => {
          if (selSuitCut) selSuitCut.value = currentStyle.suit?.style || "cyber_suit";
          if (selChestReactor) selChestReactor.value = currentStyle.accessories?.chest_badge || "arc_reactor";
          if (selShoulders) selShoulders.value = currentStyle.accessories?.shoulders || "smooth";
          if (selCape) selCape.value = currentStyle.accessories?.cape ? "true" : "false";

          const pCol = currentStyle.suit?.primary_color || "#00f2fe";
          if (inpPrimaryColor) inpPrimaryColor.value = pCol;
          if (inpPrimaryHex) inpPrimaryHex.value = pCol;

          const sCol = currentStyle.suit?.secondary_color || "#7f00ff";
          if (inpSecondaryColor) inpSecondaryColor.value = sCol;
          if (inpSecondaryHex) inpSecondaryHex.value = sCol;

          const vCol = currentStyle.head?.visor_glow_color || pCol;
          if (inpVisorGlow) inpVisorGlow.value = vCol;
          if (inpVisorHex) inpVisorHex.value = vCol;

          const tCol = currentStyle.limbs?.thruster_plasma_color || pCol;
          if (inpThrusterColor) inpThrusterColor.value = tCol;
          if (inpThrusterHex) inpThrusterHex.value = tCol;

          const tTheme = currentStyle.tool_style?.theme || (effectiveAgentId === 'leader' ? 'executive_glass' : 'cyber_neon');
          updateToolThemeUI(tTheme);

          if (previewBadge) previewBadge.textContent = `⚡ ${currentStyle.preset_name || 'Custom Outfit'}`;
          if (txtRawJson) txtRawJson.value = JSON.stringify(currentStyle, null, 2);
          renderTurntablePreview();
        };

        const syncStateFromInputs = () => {
          currentStyle.suit.style = selSuitCut?.value || "cyber_suit";
          currentStyle.suit.primary_color = inpPrimaryColor?.value || "#00f2fe";
          currentStyle.suit.secondary_color = inpSecondaryColor?.value || "#7f00ff";
          currentStyle.suit.accent_neon = inpPrimaryColor?.value || "#00f2fe";

          currentStyle.head.visor_glow_color = inpVisorGlow?.value || "#00f2fe";
          currentStyle.head.eye_emissive_color = inpVisorGlow?.value || "#00f2fe";

          currentStyle.accessories.chest_badge = selChestReactor?.value || "arc_reactor";
          currentStyle.accessories.shoulders = selShoulders?.value || "smooth";
          currentStyle.accessories.cape = selCape?.value === "true";

          currentStyle.limbs.thruster_plasma_color = inpThrusterColor?.value || "#00f2fe";
          node.styleData = currentStyle;

          if (styleSyncIndicator) {
            styleSyncIndicator.textContent = '○ Unsaved Changes';
            styleSyncIndicator.style.color = '#f59e0b';
          }
          if (txtRawJson) txtRawJson.value = JSON.stringify(currentStyle, null, 2);
          renderTurntablePreview();
        };

        // Fetch style from disk
        fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/style`)
          .then(r => r.json())
          .then(data => {
            if (data && data.status === 'ok' && data.style_data) {
              currentStyle = Object.assign(currentStyle, data.style_data);
              syncInputsFromState();
            }
          })
          .catch(e => console.warn('[SwarmPipeline] Style fetch note:', e));

        [selSuitCut, selChestReactor, selShoulders, selCape].forEach(sel => {
          sel?.addEventListener('change', syncStateFromInputs);
        });

        const bindColorPair = (colorInp, hexInp) => {
          colorInp?.addEventListener('input', (e) => {
            if (hexInp) hexInp.value = e.target.value.toUpperCase();
            syncStateFromInputs();
          });
          hexInp?.addEventListener('change', (e) => {
            let v = e.target.value.trim();
            if (!v.startsWith('#')) v = '#' + v;
            if (/^#[0-9A-Fa-f]{6}$/.test(v)) {
              if (colorInp) colorInp.value = v;
              syncStateFromInputs();
            }
          });
        };
        bindColorPair(inpPrimaryColor, inpPrimaryHex);
        bindColorPair(inpSecondaryColor, inpSecondaryHex);
        bindColorPair(inpVisorGlow, inpVisorHex);
        bindColorPair(inpThrusterColor, inpThrusterHex);

        paneStyle.querySelectorAll('.pipeline-swatches-row').forEach(row => {
          const target = row.getAttribute('data-target');
          row.querySelectorAll('.swatch').forEach(sw => {
            sw.addEventListener('click', () => {
              const col = sw.getAttribute('data-color');
              if (target === 'primary') {
                if (inpPrimaryColor) inpPrimaryColor.value = col;
                if (inpPrimaryHex) inpPrimaryHex.value = col;
              } else if (target === 'secondary') {
                if (inpSecondaryColor) inpSecondaryColor.value = col;
                if (inpSecondaryHex) inpSecondaryHex.value = col;
              }
              syncStateFromInputs();
            });
          });
        });

        presetPills.forEach(pill => {
          pill.addEventListener('click', () => {
            const pKey = pill.getAttribute('data-preset');
            const pCfg = STYLE_PRESETS[pKey];
            if (!pCfg) return;

            presetPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            currentStyle.preset_name = pCfg.preset_name;
            currentStyle.suit.style = pCfg.suit_cut;
            currentStyle.suit.primary_color = pCfg.primary;
            currentStyle.suit.secondary_color = pCfg.secondary;
            currentStyle.head.visor_glow_color = pCfg.visor;
            currentStyle.head.eye_emissive_color = pCfg.visor;
            currentStyle.accessories.chest_badge = pCfg.chest_reactor;
            currentStyle.accessories.shoulders = pCfg.shoulders;
            currentStyle.accessories.cape = pCfg.cape === 'true';
            currentStyle.limbs.thruster_plasma_color = pCfg.thruster;

            if (pCfg.tool_theme) {
              if (!currentStyle.tool_style) currentStyle.tool_style = { density: 'comfortable' };
              currentStyle.tool_style.theme = pCfg.tool_theme;
              updateToolThemeUI(pCfg.tool_theme);
            }

            node.styleData = currentStyle;
            syncInputsFromState();
            if (styleSyncIndicator) {
              styleSyncIndicator.textContent = '○ Unsaved Changes';
              styleSyncIndicator.style.color = '#f59e0b';
            }
          });
        });

        btnToggleRawJson?.addEventListener('click', () => {
          const isHidden = rawJsonBox.style.display === 'none';
          rawJsonBox.style.display = isHidden ? 'block' : 'none';
          btnToggleRawJson.textContent = isHidden ? '✕ Close JSON' : '👁️ Inspect Raw style.json';
        });

        btnSaveStyle?.addEventListener('click', async () => {
          btnSaveStyle.textContent = '⏳ Saving...';
          btnSaveStyle.disabled = true;

          try {
            const res = await fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/style`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ style_data: currentStyle })
            });
            const data = await res.json();
            if (res.ok && data.status === 'ok') {
              btnSaveStyle.textContent = '✓ Saved!';
              btnSaveStyle.style.background = 'rgba(16,185,129,0.2)';
              btnSaveStyle.style.borderColor = '#10b981';
              btnSaveStyle.style.color = '#10b981';
              if (styleSyncIndicator) {
                styleSyncIndicator.textContent = '● Synced to Disk';
                styleSyncIndicator.style.color = '#10b981';
              }
              node.styleData = currentStyle;

              if (currentStyle.tool_style && currentStyle.tool_style.theme) {
                localStorage.setItem('xflow_tool_theme', currentStyle.tool_style.theme);
                window.currentActiveToolTheme = currentStyle.tool_style.theme;
                document.querySelectorAll('.fl-cmd-item, .fl-commands-group, .tool-hud-container, .pipeline-sample-tool-card').forEach(el => {
                  el.setAttribute('data-tool-theme', currentStyle.tool_style.theme);
                });
              }

              if (window.office3DInstance && typeof window.office3DInstance.updateAgentStyle === 'function') {
                window.office3DInstance.updateAgentStyle(effectiveAgentId, currentStyle);
              }
              setTimeout(() => {
                btnSaveStyle.textContent = '💾 Save Style';
                btnSaveStyle.style.background = '';
                btnSaveStyle.style.borderColor = '';
                btnSaveStyle.style.color = '';
                btnSaveStyle.disabled = false;
              }, 1200);
            } else {
              alert('Save style failed: ' + (data.message || 'Unknown error'));
              btnSaveStyle.textContent = '💾 Save Style';
              btnSaveStyle.disabled = false;
            }
          } catch (err) {
            alert('Network error saving style: ' + err.message);
            btnSaveStyle.textContent = '💾 Save Style';
            btnSaveStyle.disabled = false;
          }
        });

        // 3D Turntable Renderer on HTML5 Canvas
        const renderTurntablePreview = () => {
          if (!turntableCanvas) return;
          const ctx = turntableCanvas.getContext('2d');
          const w = turntableCanvas.width;
          const h = turntableCanvas.height;
          ctx.clearRect(0, 0, w, h);

          const centerX = w / 2;
          const centerY = h / 2 - 15;
          const rot = turntableRotation;

          // Pedestal Ring
          ctx.save();
          ctx.translate(centerX, centerY + 130);
          ctx.scale(1, 0.35);
          ctx.beginPath();
          ctx.arc(0, 0, 75, 0, Math.PI * 2);
          const pedGrd = ctx.createRadialGradient(0, 0, 10, 0, 0, 75);
          pedGrd.addColorStop(0, 'rgba(0, 242, 254, 0.4)');
          pedGrd.addColorStop(0.7, 'rgba(0, 242, 254, 0.15)');
          pedGrd.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = pedGrd;
          ctx.fill();
          ctx.restore();

          const pCol = currentStyle.suit?.primary_color || '#00f2fe';
          const sCol = currentStyle.suit?.secondary_color || '#7f00ff';
          const vCol = currentStyle.head?.visor_glow_color || pCol;
          const tCol = currentStyle.limbs?.thruster_plasma_color || pCol;
          const hasCape = currentStyle.accessories?.cape === true;
          const hasEpaulets = currentStyle.accessories?.shoulders === 'epaulets';

          const cosR = Math.cos(rot);
          const sinR = Math.sin(rot);

          // Cape
          if (hasCape && cosR > -0.2) {
            ctx.save();
            ctx.translate(centerX - sinR * 12, centerY + 25);
            ctx.fillStyle = '#451a03';
            ctx.strokeStyle = '#b45309';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(-35, 0);
            ctx.lineTo(35, 0);
            ctx.lineTo(44, 90);
            ctx.lineTo(-44, 90);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            ctx.restore();
          }

          // Legs & Boots
          [-22, 22].forEach(legX => {
            ctx.save();
            ctx.translate(centerX + legX * cosR, centerY + 78);
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(-7, 0, 14, 25);
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(-9, 25, 18, 15);
            ctx.fillStyle = vCol;
            ctx.fillRect(-8, 40, 16, 4);
            const flameGrd = ctx.createLinearGradient(0, 44, 0, 62);
            flameGrd.addColorStop(0, tCol);
            flameGrd.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = flameGrd;
            ctx.beginPath();
            ctx.moveTo(-7, 44);
            ctx.lineTo(7, 44);
            ctx.lineTo(0, 62);
            ctx.closePath();
            ctx.fill();
            ctx.restore();
          });

          // Torso / Suit
          ctx.save();
          ctx.translate(centerX, centerY + 35);
          const suitGrd = ctx.createLinearGradient(-32, 0, 32, 0);
          suitGrd.addColorStop(0, pCol);
          suitGrd.addColorStop(0.5, '#f8fafc');
          suitGrd.addColorStop(1, pCol);
          ctx.fillStyle = suitGrd;
          ctx.beginPath();
          ctx.roundRect(-30, -15, 60, 50, 10);
          ctx.fill();
          ctx.strokeStyle = sCol;
          ctx.lineWidth = 2.5;
          ctx.stroke();

          // Chest Badge
          const badgeType = currentStyle.accessories?.chest_badge || 'arc_reactor';
          if (badgeType === 'arc_reactor') {
            ctx.beginPath();
            ctx.arc(sinR * 8, 8, 11, 0, Math.PI * 2);
            ctx.fillStyle = vCol;
            ctx.shadowColor = vCol;
            ctx.shadowBlur = 12;
            ctx.fill();
            ctx.shadowBlur = 0;
            ctx.strokeStyle = '#09090b';
            ctx.lineWidth = 2;
            ctx.stroke();
          } else if (badgeType === 'flowork_f') {
            ctx.fillStyle = '#f59e0b';
            ctx.font = 'bold 15px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('F', sinR * 8, 14);
          }

          // Suit Cut Details
          const cut = currentStyle.suit?.style || 'cyber_suit';
          if (cut === 'executive_blazer') {
            ctx.strokeStyle = sCol;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(-16, -15);
            ctx.lineTo(0, 16);
            ctx.lineTo(16, -15);
            ctx.stroke();
          } else if (cut === 'tactical_vest') {
            ctx.strokeStyle = 'rgba(0,0,0,0.4)';
            ctx.lineWidth = 3;
            ctx.strokeRect(-24, -8, 48, 12);
          }
          ctx.restore();

          // Arms
          [-38, 38].forEach((armX) => {
            ctx.save();
            ctx.translate(centerX + armX, centerY + 28);
            ctx.fillStyle = hasEpaulets ? '#f59e0b' : sCol;
            ctx.beginPath();
            ctx.arc(0, 0, 10, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = pCol;
            ctx.fillRect(-6, 8, 12, 28);
            ctx.fillStyle = '#1e293b';
            ctx.beginPath();
            ctx.arc(0, 42, 8, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
          });

          // Head & Helmet (Sacred Locked Mesh)
          ctx.save();
          ctx.translate(centerX, centerY - 38);
          ctx.fillStyle = effectiveAgentId === 'leader' ? '#09090b' : '#111827';
          ctx.beginPath();
          ctx.arc(0, 0, 42, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = 'rgba(255,255,255,0.15)';
          ctx.lineWidth = 2;
          ctx.stroke();

          // Visor Plate
          ctx.save();
          ctx.beginPath();
          ctx.ellipse(sinR * 6, 2, 34, 26, 0, 0, Math.PI * 2);
          ctx.clip();
          const visorGrd = ctx.createLinearGradient(0, -20, 0, 20);
          visorGrd.addColorStop(0, '#030814');
          visorGrd.addColorStop(0.6, '#0f172a');
          visorGrd.addColorStop(1, '#020617');
          ctx.fillStyle = visorGrd;
          ctx.fillRect(-45, -30, 90, 60);

          // Visor Rim
          ctx.strokeStyle = vCol;
          ctx.shadowColor = vCol;
          ctx.shadowBlur = 10;
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.arc(sinR * 6, 2, 26, 0.2, Math.PI - 0.2);
          ctx.stroke();

          // Eyes
          ctx.fillStyle = vCol;
          const eyeOff = sinR * 10;
          ctx.beginPath();
          ctx.arc(-12 + eyeOff, 0, 3.5, 0, Math.PI * 2);
          ctx.arc(12 + eyeOff, 0, 3.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
          ctx.restore();

          // Crown for leader
          if (effectiveAgentId === 'leader') {
            ctx.fillStyle = '#f59e0b';
            ctx.strokeStyle = '#78350f';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(-22, -36);
            ctx.lineTo(-20, -52);
            ctx.lineTo(-10, -42);
            ctx.lineTo(0, -56);
            ctx.lineTo(10, -42);
            ctx.lineTo(20, -52);
            ctx.lineTo(22, -36);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
          }

          // Antennae
          ctx.strokeStyle = '#64748b';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(-36, -10);
          ctx.lineTo(-48, -26);
          ctx.moveTo(36, -10);
          ctx.lineTo(48, -26);
          ctx.stroke();
          ctx.fillStyle = vCol;
          ctx.beginPath();
          ctx.arc(-48, -26, 3.5, 0, Math.PI * 2);
          ctx.arc(48, -26, 3.5, 0, Math.PI * 2);
          ctx.fill();

          ctx.restore();
        };

        turntableCanvas?.addEventListener('mousedown', (e) => {
          isDraggingTurntable = true;
          lastDragX = e.clientX;
        });

        window.addEventListener('mousemove', (e) => {
          if (!isDraggingTurntable) return;
          const deltaX = e.clientX - lastDragX;
          lastDragX = e.clientX;
          turntableRotation += deltaX * 0.018;
          renderTurntablePreview();
        });

        window.addEventListener('mouseup', () => {
          isDraggingTurntable = false;
        });

        turntableCanvas?.addEventListener('touchstart', (e) => {
          if (e.touches.length > 0) {
            isDraggingTurntable = true;
            lastDragX = e.touches[0].clientX;
          }
        });
        window.addEventListener('touchmove', (e) => {
          if (!isDraggingTurntable || e.touches.length === 0) return;
          const deltaX = e.touches[0].clientX - lastDragX;
          lastDragX = e.touches[0].clientX;
          turntableRotation += deltaX * 0.018;
          renderTurntablePreview();
        });
        window.addEventListener('touchend', () => {
          isDraggingTurntable = false;
        });

        renderTurntablePreview();
      }

      // 2. Persona Tab Bindings (Locked to Subagent ID)
      const inpSysPrompt = box.querySelector('#modal-persona-system-prompt');
      const btnSavePersona = box.querySelector('#btn-save-agent-persona');
      const syncIndicator = box.querySelector('#persona-sync-indicator');

      // Auto-load subagent persona from disk
      if (effectiveAgentId) {
        fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/persona`)
          .then(r => r.json())
          .then(data => {
            if (data && data.status === 'ok') {
              if (data.persona_content && inpSysPrompt && !inpSysPrompt.dataset.dirty) {
                inpSysPrompt.value = data.persona_content;
                node.personaData.systemPrompt = data.persona_content;
              }
            }
          })
          .catch(e => console.warn('[SwarmPipeline] Subagent persona load notice:', e));
      }

      if (inpSysPrompt) {
        inpSysPrompt.addEventListener('input', (e) => {
          inpSysPrompt.dataset.dirty = 'true';
          node.personaData.systemPrompt = e.target.value;
          if (syncIndicator) {
            syncIndicator.textContent = '○ Unsaved Changes';
            syncIndicator.style.color = '#f59e0b';
          }
          this.debouncedSave();
        });
      }

      if (btnSavePersona) {
        btnSavePersona.addEventListener('click', async () => {
          const savePayload = {
            persona_content: inpSysPrompt ? inpSysPrompt.value : (node.personaData.systemPrompt || '')
          };
          btnSavePersona.textContent = '⏳ Saving...';
          btnSavePersona.disabled = true;
          try {
            const res = await fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/persona`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(savePayload)
            });
            const data = await res.json();
            if (res.ok && data.status === 'ok') {
              btnSavePersona.textContent = '✓ Saved!';
              btnSavePersona.style.background = 'rgba(16,185,129,0.2)';
              btnSavePersona.style.borderColor = '#10b981';
              btnSavePersona.style.color = '#10b981';
              if (syncIndicator) {
                syncIndicator.textContent = '● Synced to Disk';
                syncIndicator.style.color = '#10b981';
              }
              delete inpSysPrompt.dataset.dirty;
              setTimeout(() => {
                btnSavePersona.textContent = '💾 Save Persona';
                btnSavePersona.style.background = '';
                btnSavePersona.style.borderColor = '';
                btnSavePersona.style.color = '';
                btnSavePersona.disabled = false;
              }, 2000);
            } else {
              alert('Save failed: ' + (data.message || 'Unknown error'));
              btnSavePersona.textContent = '💾 Save Persona';
              btnSavePersona.disabled = false;
            }
          } catch (err) {
            alert('Failed to communicate with subagent persona API: ' + err.message);
            btnSavePersona.textContent = '💾 Save Persona';
            btnSavePersona.disabled = false;
          }
        });
      }

      // 2. Rules Tab Bindings (Locked to Subagent ID)
      const inpRulePrompt = box.querySelector('#modal-rule-prompt');
      const btnSaveRules = box.querySelector('#btn-save-agent-rules');
      const rulesSyncIndicator = box.querySelector('#rules-sync-indicator');

      if (effectiveAgentId) {
        fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/rules`)
          .then(r => r.json())
          .then(data => {
            if (data && data.status === 'ok') {
              if (data.rules_content && inpRulePrompt && !inpRulePrompt.dataset.dirty) {
                inpRulePrompt.value = data.rules_content;
                node.rulePrompt = data.rules_content;
                node.rulesData.prompt = data.rules_content;
              }
            }
          })
          .catch(e => console.warn('[SwarmPipeline] Subagent rules load notice:', e));
      }

      if (inpRulePrompt) {
        inpRulePrompt.addEventListener('input', (e) => {
          inpRulePrompt.dataset.dirty = 'true';
          node.rulePrompt = e.target.value;
          node.rulesData.prompt = e.target.value;
          if (rulesSyncIndicator) {
            rulesSyncIndicator.textContent = '○ Unsaved Changes';
            rulesSyncIndicator.style.color = '#f59e0b';
          }
          this.debouncedSave();
        });
      }

      if (btnSaveRules) {
        btnSaveRules.addEventListener('click', async () => {
          const savePayload = {
            rules_content: inpRulePrompt ? inpRulePrompt.value : (node.rulePrompt || '')
          };
          btnSaveRules.textContent = '⏳ Saving...';
          btnSaveRules.disabled = true;
          try {
            const res = await fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/rules`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(savePayload)
            });
            const data = await res.json();
            if (res.ok && data.status === 'ok') {
              btnSaveRules.textContent = '✓ Saved!';
              btnSaveRules.style.background = 'rgba(16,185,129,0.2)';
              btnSaveRules.style.borderColor = '#10b981';
              btnSaveRules.style.color = '#10b981';
              if (rulesSyncIndicator) {
                rulesSyncIndicator.textContent = '● Synced to Disk';
                rulesSyncIndicator.style.color = '#10b981';
              }
              delete inpRulePrompt.dataset.dirty;
              setTimeout(() => {
                btnSaveRules.textContent = '💾 Save Rules';
                btnSaveRules.style.background = '';
                btnSaveRules.style.borderColor = '';
                btnSaveRules.style.color = '';
                btnSaveRules.disabled = false;
              }, 2000);
            } else {
              alert('Save failed: ' + (data.message || 'Unknown error'));
              btnSaveRules.textContent = '💾 Save Rules';
              btnSaveRules.disabled = false;
            }
          } catch (err) {
            alert('Failed to communicate with subagent rules API: ' + err.message);
            btnSaveRules.textContent = '💾 Save Rules';
            btnSaveRules.disabled = false;
          }
        });
      }

      // 3. Task Tab Bindings (Locked to Subagent ID)
      const inpTaskPrompt = box.querySelector('#modal-task-prompt');
      const btnSaveTask = box.querySelector('#btn-save-agent-task');
      const taskSyncIndicator = box.querySelector('#task-sync-indicator');

      if (effectiveAgentId) {
        fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/task`)
          .then(r => r.json())
          .then(data => {
            if (data && data.status === 'ok') {
              if (data.task_content && inpTaskPrompt && !inpTaskPrompt.dataset.dirty) {
                inpTaskPrompt.value = data.task_content;
                node.taskPrompt = data.task_content;
                node.taskData.prompt = data.task_content;
              }
            }
          })
          .catch(e => console.warn('[SwarmPipeline] Subagent task load notice:', e));
      }

      if (inpTaskPrompt) {
        inpTaskPrompt.addEventListener('input', (e) => {
          inpTaskPrompt.dataset.dirty = 'true';
          node.taskPrompt = e.target.value;
          node.taskData.prompt = e.target.value;
          node.taskData.objective = e.target.value;
          if (taskSyncIndicator) {
            taskSyncIndicator.textContent = '○ Unsaved Changes';
            taskSyncIndicator.style.color = '#f59e0b';
          }
          this.debouncedSave();
        });
      }

      if (btnSaveTask) {
        btnSaveTask.addEventListener('click', async () => {
          const savePayload = {
            task_content: inpTaskPrompt ? inpTaskPrompt.value : (node.taskPrompt || '')
          };
          btnSaveTask.textContent = '⏳ Saving...';
          btnSaveTask.disabled = true;
          try {
            const res = await fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/task`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(savePayload)
            });
            const data = await res.json();
            if (res.ok && data.status === 'ok') {
              btnSaveTask.textContent = '✓ Saved!';
              btnSaveTask.style.background = 'rgba(16,185,129,0.2)';
              btnSaveTask.style.borderColor = '#10b981';
              btnSaveTask.style.color = '#10b981';
              if (taskSyncIndicator) {
                taskSyncIndicator.textContent = '● Synced to Disk';
                taskSyncIndicator.style.color = '#10b981';
              }
              delete inpTaskPrompt.dataset.dirty;
              setTimeout(() => {
                btnSaveTask.textContent = '💾 Save Task';
                btnSaveTask.style.background = '';
                btnSaveTask.style.borderColor = '';
                btnSaveTask.style.color = '';
                btnSaveTask.disabled = false;
              }, 2000);
            } else {
              alert('Save failed: ' + (data.message || 'Unknown error'));
              btnSaveTask.textContent = '💾 Save Task';
              btnSaveTask.disabled = false;
            }
          } catch (err) {
            alert('Failed to communicate with subagent task API: ' + err.message);
            btnSaveTask.textContent = '💾 Save Task';
            btnSaveTask.disabled = false;
          }
        });
      }

      // 4. Model Selection Tab Bindings
      const selAccountMode = box.querySelector('#modal-model-account-mode');
      const footerAccountDisp = box.querySelector('#footer-active-account-disp');
      selAccountMode.addEventListener('change', (e) => {
        node.modelConfig.accountMode = e.target.value;
        if (footerAccountDisp) {
          footerAccountDisp.textContent = `⚡ Account: ${e.target.value === 'combo' ? 'Combo (Auto-Balancer)' : e.target.value}`;
        }
        this.render();
        this.debouncedSave();
      });

      const inpTemp = box.querySelector('#modal-model-temperature');
      const dispTempVal = box.querySelector('#disp-temp-val');
      inpTemp.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        node.modelConfig.temperature = val;
        if (dispTempVal) dispTempVal.textContent = val.toFixed(2);
        this.debouncedSave();
      });

      // 4. Model Selection Tab Bindings & Dynamic Provider Switching
      const tbodyModels = box.querySelector('#tbody-cockpit-models-list');
      const footerModelDisp = box.querySelector('#footer-active-model-disp');

      const bindModelRowsEvents = () => {
        const modelRows = box.querySelectorAll('.pipeline-model-row');
        modelRows.forEach(row => {
          row.addEventListener('click', async () => {
            const mId = row.getAttribute('data-model-id');
            const mName = row.getAttribute('data-model-name');
            const mProv = row.getAttribute('data-provider') || 'gravity';
            node.modelConfig.modelId = mId;
            node.modelConfig.modelName = mName;
            node.modelConfig.provider = mProv;

            modelRows.forEach(r => {
              r.classList.remove('selected');
              const radio = r.querySelector('input[type="radio"]');
              if (radio) radio.checked = (r === row);
            });
            row.classList.add('selected');

            if (footerModelDisp) {
              footerModelDisp.textContent = `🧠 Model: ${mName.split('[')[0].trim()}`;
            }
            try {
              localStorage.setItem('xflow_chat_model', mId);
              localStorage.setItem('xflow_agent_model_' + node.id, mId);
              if (typeof window.switchFloworkCoreModel === 'function') {
                await window.switchFloworkCoreModel(mId);
              }
              const routerPort = (typeof _getFloworkRouterPort === 'function') ? _getFloworkRouterPort() : 9099;
              await fetch(`http://127.0.0.1:${routerPort}/auth/router/active-provider`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: mProv })
              }).catch(() => {});
            } catch (_) {}
            this.render();
            this.debouncedSave();
          });
        });
      };
      bindModelRowsEvents();

      // Provider tabs click handlers in Cockpit modal
      const provTabs = box.querySelectorAll('#cockpit-model-provider-tabs .pipeline-mini-btn');
      provTabs.forEach(tabBtn => {
        tabBtn.addEventListener('click', async () => {
          const targetProv = tabBtn.getAttribute('data-provider');
          provTabs.forEach(b => b.classList.remove('active'));
          tabBtn.classList.add('active');

          if (tbodyModels) {
            tbodyModels.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:16px; color:#94a3b8; font-size:12px;">🔄 Fetching live ${targetProv.toUpperCase()} models...</td></tr>`;
          }

          try {
            const routerPort = (typeof _getFloworkRouterPort === 'function') ? _getFloworkRouterPort() : 9099;
            const res = await fetch(`http://127.0.0.1:${routerPort}/auth/router/models?provider=${targetProv}`);
            if (res.ok) {
              const data = await res.json();
              if (data && Array.isArray(data.models)) {
                const mappedModels = data.models.map(m => ({
                  id: m.id,
                  name: m.name,
                  tier: m.badge || (targetProv === 'ollama' ? 'Local LLM' : (targetProv === '9router' ? 'Proxy Router' : 'Flagship Thinking')),
                  latency: (targetProv === 'ollama' ? '0.1s (Local GPU)' : (targetProv === '9router' ? 'Routed' : '0.8s (Fast)')),
                  context: m.context || '1,000,000 tokens',
                  desc: m.desc || '',
                  provider: targetProv
                }));
                if (tbodyModels) {
                  tbodyModels.innerHTML = renderCockpitModelRows(mappedModels, node.modelConfig?.modelId);
                  bindModelRowsEvents();
                }
                return;
              }
            }
          } catch (_) {}

          if (tbodyModels) {
            tbodyModels.innerHTML = renderCockpitModelRows(ANTIGRAVITY_MODELS, node.modelConfig?.modelId);
            bindModelRowsEvents();
          }
        });
      });

      // Auto-load live models immediately when opening Cockpit
      setTimeout(async () => {
        try {
          const routerPort = (typeof _getFloworkRouterPort === 'function') ? _getFloworkRouterPort() : 9099;
          const res = await fetch(`http://127.0.0.1:${routerPort}/auth/router/models`);
          if (res.ok) {
            const data = await res.json();
            if (data && Array.isArray(data.models) && tbodyModels) {
              const activeProv = data.provider || 'gravity';
              provTabs.forEach(b => {
                b.classList.toggle('active', b.getAttribute('data-provider') === activeProv);
              });
              const mapped = data.models.map(m => ({
                id: m.id,
                name: m.name,
                tier: m.badge || (activeProv === 'ollama' ? 'Local LLM' : (activeProv === '9router' ? 'Proxy Router' : 'Flagship Thinking')),
                latency: (activeProv === 'ollama' ? '0.1s (Local GPU)' : (activeProv === '9router' ? 'Routed' : '0.8s (Fast)')),
                context: m.context || '1,000,000 tokens',
                desc: m.desc || '',
                provider: activeProv
              }));
              tbodyModels.innerHTML = renderCockpitModelRows(mapped, node.modelConfig?.modelId);
              bindModelRowsEvents();
            }
          }
        } catch (_) {}
      }, 50);

      // 5. Tool Governance Tab Bindings
      const masterToolSwitch = box.querySelector('#modal-tool-master-allow-all');
      let toolSwitches = box.querySelectorAll('.tool-switch');
      const modalToolsSearch = box.querySelector('#inp-modal-tools-search');
      const modalPillsContainer = box.querySelector('#modal-tools-filter-pills');

      let currentModalFilter = 'all';
      let currentModalSearch = '';

      const filterModalToolRows = () => {
        const rows = box.querySelectorAll('#tbody-tools-governance .pipeline-tool-row');
        rows.forEach(r => {
          const tid = (r.getAttribute('data-tool-id') || '').toLowerCase();
          const cat = (r.children[1]?.textContent || '').toLowerCase();
          const desc = (r.children[2]?.textContent || '').toLowerCase();

          let matchFilter = true;
          if (currentModalFilter === 'rules') matchFilter = r.getAttribute('data-has-rules') === 'true';
          else if (currentModalFilter === 'safe') matchFilter = r.getAttribute('data-has-rules') === 'false';
          else if (currentModalFilter === 'filesystem') matchFilter = cat.includes('filesystem');
          else if (currentModalFilter === 'terminal') matchFilter = cat.includes('terminal');
          else if (currentModalFilter === 'network') matchFilter = cat.includes('network');
          else if (currentModalFilter === 'visual') matchFilter = cat.includes('visual');
          else if (currentModalFilter === 'general') matchFilter = cat.includes('general');

          let matchSearch = true;
          if (currentModalSearch) {
            matchSearch = tid.includes(currentModalSearch) || cat.includes(currentModalSearch) || desc.includes(currentModalSearch);
          }

          const shouldShow = matchFilter && matchSearch;
          r.style.display = shouldShow ? '' : 'none';
          const drawer = box.querySelector(`#guardian-drawer-${tid}`);
          if (drawer) {
            if (!shouldShow) drawer.style.display = 'none';
            else drawer.style.display = '';
          }
        });
      };

      modalToolsSearch?.addEventListener('input', (e) => {
        currentModalSearch = (e.target.value || '').trim().toLowerCase();
        filterModalToolRows();
      });

      modalPillsContainer?.addEventListener('click', (e) => {
        const pill = e.target.closest('.pipeline-dock-pill');
        if (!pill) return;
        modalPillsContainer.querySelectorAll('.pipeline-dock-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        currentModalFilter = pill.getAttribute('data-filter') || 'all';
        filterModalToolRows();
      });

      // Expand/Collapse Guardian Drawer per tool row
      box.querySelectorAll('.pipeline-guardian-expand-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const tid = btn.getAttribute('data-tool-id');
          const drawer = box.querySelector(`#guardian-drawer-${tid}`);
          if (drawer) {
            const isCollapsed = drawer.classList.contains('collapsed');
            drawer.classList.toggle('collapsed');
            btn.classList.toggle('active', isCollapsed);
            if (isCollapsed) {
              drawer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
          }
        });
      });

      // Bind all inputs inside drawers (inputs, checkboxes, reset, clone)
      const bindAllDrawerInputs = (rootEl) => {
        rootEl.querySelectorAll('.guardian-input').forEach(inp => {
          inp.addEventListener('input', () => {
            const tid = inp.getAttribute('data-tool-id');
            const field = inp.getAttribute('data-field');
            const val = inp.type === 'number' ? (Number(inp.value) || 0) : inp.value;
            const g = getNodeToolGuardian(node, { id: tid });
            g[field] = val;
            this.debouncedSave();
          });
        });

        rootEl.querySelectorAll('.guardian-switch-input').forEach(sw => {
          sw.addEventListener('change', () => {
            const tid = sw.getAttribute('data-tool-id');
            const field = sw.getAttribute('data-field');
            const g = getNodeToolGuardian(node, { id: tid });
            g[field] = sw.checked;
            this.debouncedSave();
          });
        });

        rootEl.querySelectorAll('.btn-reset-guardian').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const tid = btn.getAttribute('data-tool-id');
            const t = (this.availableTools || SOVEREIGN_LOCAL_TOOLS).find(tool => tool.id === tid) || { id: tid };
            node.toolGovernance.toolGuardians[tid] = getDefaultGuardianForTool(t, !!node.isLocked);
            this.saveState();

            const drawer = box.querySelector(`#guardian-drawer-${tid}`);
            if (drawer) {
              const temp = document.createElement('tbody');
              temp.innerHTML = renderGuardianDrawerHtml(t, node.toolGovernance.toolGuardians[tid], node, this.nodes);
              const newDrawer = temp.firstElementChild;
              if (newDrawer) {
                newDrawer.classList.remove('collapsed');
                drawer.replaceWith(newDrawer);
                bindAllDrawerInputs(newDrawer);
              }
            }
          });
        });

        rootEl.querySelectorAll('.sel-clone-guardian').forEach(sel => {
          sel.addEventListener('change', () => {
            const srcNodeId = sel.value;
            if (!srcNodeId) return;
            const tid = sel.getAttribute('data-tool-id');
            const srcNode = this.nodes.find(n => n.id === srcNodeId);
            if (srcNode && srcNode.toolGovernance?.toolGuardians?.[tid]) {
              node.toolGovernance.toolGuardians[tid] = JSON.parse(JSON.stringify(srcNode.toolGovernance.toolGuardians[tid]));
              this.saveState();
              const t = (this.availableTools || SOVEREIGN_LOCAL_TOOLS).find(tool => tool.id === tid) || { id: tid };
              const drawer = box.querySelector(`#guardian-drawer-${tid}`);
              if (drawer) {
                const temp = document.createElement('tbody');
                temp.innerHTML = renderGuardianDrawerHtml(t, node.toolGovernance.toolGuardians[tid], node, this.nodes);
                const newDrawer = temp.firstElementChild;
                if (newDrawer) {
                  newDrawer.classList.remove('collapsed');
                  drawer.replaceWith(newDrawer);
                  bindAllDrawerInputs(newDrawer);
                }
              }
            }
            sel.value = '';
          });
        });
      };

      bindAllDrawerInputs(box);

      const syncToolGovernanceFromSwitches = () => {
        const allowed = [];
        const denied = [];
        toolSwitches.forEach(sw => {
          const tid = sw.getAttribute('data-tool-id');
          if (sw.checked) allowed.push(tid);
          else denied.push(tid);
        });
        node.toolGovernance.allowedTools = allowed;
        node.toolGovernance.deniedTools = denied;
        node.toolGovernance.allowAll = (denied.length === 0);
        if (masterToolSwitch) masterToolSwitch.checked = (denied.length === 0);
        this.debouncedSave();
      };

      masterToolSwitch.addEventListener('change', (e) => {
        const isChecked = e.target.checked;
        node.toolGovernance.allowAll = isChecked;
        toolSwitches.forEach(sw => { sw.checked = isChecked; });
        const allToolIds = (this.availableTools || SOVEREIGN_LOCAL_TOOLS).filter(t => !isPromptOrEnclaveTriggeredTool(t.id)).map(t => t.id);
        if (isChecked) {
          node.toolGovernance.allowedTools = allToolIds;
          node.toolGovernance.deniedTools = [];
        } else {
          node.toolGovernance.allowedTools = [];
          node.toolGovernance.deniedTools = allToolIds;
        }
        this.debouncedSave();
      });

      toolSwitches.forEach(sw => {
        sw.addEventListener('change', () => {
          syncToolGovernanceFromSwitches();
        });
      });

      box.querySelector('#btn-tools-filter-rules')?.addEventListener('click', () => {
        const rulesPill = box.querySelector('#modal-tools-filter-pills [data-filter="rules"]');
        if (rulesPill) rulesPill.click();
      });

      box.querySelector('#btn-tools-allow-all')?.addEventListener('click', () => {
        if (masterToolSwitch) {
          masterToolSwitch.checked = true;
          masterToolSwitch.dispatchEvent(new Event('change'));
        }
      });

      box.querySelector('#btn-tools-deny-all')?.addEventListener('click', () => {
        if (masterToolSwitch) {
          masterToolSwitch.checked = false;
          masterToolSwitch.dispatchEvent(new Event('change'));
        }
      });

      box.querySelector('#btn-tools-safe-preset')?.addEventListener('click', () => {
        const tools = (this.availableTools || SOVEREIGN_LOCAL_TOOLS).filter(t => !isPromptOrEnclaveTriggeredTool(t.id));
        const safeIds = tools.filter(t => t.risk === 'SAFE').map(t => t.id);
        if (masterToolSwitch) masterToolSwitch.checked = false;
        node.toolGovernance.allowAll = false;
        toolSwitches.forEach(sw => {
          const tid = sw.getAttribute('data-tool-id');
          sw.checked = safeIds.includes(tid);
        });
        syncToolGovernanceFromSwitches();
      });

      // Role-Based Tool Presets Binding
      const rolePackBtns = box.querySelectorAll('#tools-role-presets .pipeline-preset-pill');
      rolePackBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          rolePackBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const pack = btn.getAttribute('data-role-pack');
          const allTools = (this.availableTools || SOVEREIGN_LOCAL_TOOLS).filter(t => !isPromptOrEnclaveTriggeredTool(t.id));

          if (pack === 'full') {
            if (masterToolSwitch) {
              masterToolSwitch.checked = true;
              masterToolSwitch.dispatchEvent(new Event('change'));
            }
            return;
          }

          if (masterToolSwitch) masterToolSwitch.checked = false;
          node.toolGovernance.allowAll = false;

          let targetIds = [];
          if (pack === 'coder') {
            targetIds = allTools.filter(t => 
              t.category === 'filesystem' || t.category === 'code' || t.id.includes('file') || t.id.includes('code') || t.id.includes('git') || t.id.includes('test')
            ).map(t => t.id);
          } else if (pack === 'devops') {
            targetIds = allTools.filter(t => 
              t.category === 'general' || t.category === 'filesystem' || t.id.includes('command') || t.id.includes('task') || t.id.includes('process') || t.id.includes('port')
            ).map(t => t.id);
          } else if (pack === 'security') {
            targetIds = allTools.filter(t => 
              t.category === 'security' || t.category === 'reverse' || t.id.includes('crypto') || t.id.includes('bin') || t.id.includes('audit') || t.id.includes('inspect')
            ).map(t => t.id);
          } else if (pack === 'researcher') {
            targetIds = allTools.filter(t => 
              t.category === 'web' || t.category === 'intelligence' || t.id.includes('search') || t.id.includes('url') || t.id.includes('question') || t.id.includes('read')
            ).map(t => t.id);
          }

          // Always add safe baseline tools
          const safeIds = allTools.filter(t => t.risk === 'SAFE').map(t => t.id);
          const combined = new Set([...targetIds, ...safeIds]);

          toolSwitches.forEach(sw => {
            const tid = sw.getAttribute('data-tool-id');
            sw.checked = combined.has(tid);
          });
          syncToolGovernanceFromSwitches();
        });
      });

      // 6. Skills Catalog Tab Bindings
      const skillSwitches = box.querySelectorAll('.skill-switch');
      const skillsCountBadge = box.querySelector('#tab-skills-count');

      const syncSkillsFromSwitches = () => {
        const active = [];
        skillSwitches.forEach(sw => {
          if (sw.checked) active.push(sw.getAttribute('data-skill-id'));
        });
        node.skillsConfig.activeSkills = active;
        if (skillsCountBadge) skillsCountBadge.textContent = `${active.length} Active`;
        this.debouncedSave();
      };

      skillSwitches.forEach(sw => {
        sw.addEventListener('change', () => {
          syncSkillsFromSwitches();
        });
      });

      box.querySelector('#btn-skills-enable-all')?.addEventListener('click', () => {
        skillSwitches.forEach(sw => { sw.checked = true; });
        syncSkillsFromSwitches();
      });

      box.querySelector('#btn-skills-disable-all')?.addEventListener('click', () => {
        skillSwitches.forEach(sw => { sw.checked = false; });
        syncSkillsFromSwitches();
      });

      box.querySelector('#btn-skills-sovereign-preset')?.addEventListener('click', () => {
        const sovSkills = ['ui_ux_pro_max', 'antigravity_guide', 'code-review', 'implement-spec'];
        skillSwitches.forEach(sw => {
          sw.checked = sovSkills.includes(sw.getAttribute('data-skill-id'));
        });
        syncSkillsFromSwitches();
      });

      // 9. Close Modal Handler
      box.querySelector('#btn-close-modal')?.addEventListener('click', () => this.closeFullPromptModal());

      // Show overlay
      requestAnimationFrame(() => {
        overlay.classList.add('active');
      });

      // If initial tab requested, activate it directly
      if (initialTab) {
        tabBtns.forEach(b => b.classList.remove('active'));
        panes.forEach(p => p.classList.remove('active'));
        const targetTabBtn = box.querySelector(`.pipeline-cockpit-tab-btn[data-tab="${initialTab}"]`);
        const targetPane = box.querySelector(`#cockpit-pane-${initialTab}`);
        if (targetTabBtn && targetPane) {
          targetTabBtn.classList.add('active');
          targetPane.classList.add('active');
        }
      }

      // If a specific tool was requested, auto-switch to tools tab and reveal its guardian drawer
      if (focusedToolId) {
        tabBtns.forEach(b => b.classList.remove('active'));
        panes.forEach(p => p.classList.remove('active'));
        const toolsTabBtn = box.querySelector('.pipeline-cockpit-tab-btn[data-tab="tools"]');
        const toolsPane = box.querySelector('#cockpit-pane-tools');
        if (toolsTabBtn && toolsPane) {
          toolsTabBtn.classList.add('active');
          toolsPane.classList.add('active');
        }
        setTimeout(() => {
          const drawer = box.querySelector(`#guardian-drawer-${focusedToolId}`);
          const expandBtn = box.querySelector(`.pipeline-guardian-expand-btn[data-tool-id="${focusedToolId}"]`);
          if (drawer) {
            drawer.classList.remove('collapsed');
            if (expandBtn) expandBtn.classList.add('active');
            drawer.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }, 120);
      }
    }

    closeFullPromptModal() {
      const overlay = document.getElementById('pipeline-prompt-modal-overlay');
      if (overlay) {
        overlay.classList.remove('active');
      }
      this.activeModalNode = null;
    }

    async saveAndCloseModal() {
      const box = document.getElementById('pipeline-prompt-modal-box');
      if (box && this.activeModalNode) {
        const node = this.activeModalNode;
        const effectiveAgentId = node.agentId || (node.type === 'leader' || (node.id && node.id.includes('leader')) ? 'leader' : 'mr.flow');
        const inpSysPrompt = box.querySelector('#modal-persona-system-prompt');
        const inpRulePrompt = box.querySelector('#modal-rule-prompt');
        const inpTaskPrompt = box.querySelector('#modal-task-prompt');

        const promises = [];
        if (inpSysPrompt && (inpSysPrompt.dataset.dirty || inpSysPrompt.value)) {
          node.personaData.systemPrompt = inpSysPrompt.value;
          promises.push(fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/persona`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ persona_content: inpSysPrompt.value })
          }));
        }
        if (inpRulePrompt && (inpRulePrompt.dataset.dirty || inpRulePrompt.value)) {
          node.rulePrompt = inpRulePrompt.value;
          node.rulesData.prompt = inpRulePrompt.value;
          promises.push(fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/rules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rules_content: inpRulePrompt.value })
          }));
        }
        if (inpTaskPrompt && (inpTaskPrompt.dataset.dirty || inpTaskPrompt.value)) {
          node.taskPrompt = inpTaskPrompt.value;
          node.taskData.prompt = inpTaskPrompt.value;
          promises.push(fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/task`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_content: inpTaskPrompt.value })
          }));
        }
        if (node.styleData) {
          promises.push(fetch(`/api/subagents/${encodeURIComponent(effectiveAgentId)}/style`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ style_data: node.styleData })
          }));
          if (window.office3DInstance && typeof window.office3DInstance.updateAgentStyle === 'function') {
            window.office3DInstance.updateAgentStyle(effectiveAgentId, node.styleData);
          }
        }

        if (promises.length > 0) {
          try {
            await Promise.all(promises);
          } catch (e) {
            console.warn('[SwarmPipeline] Batch prompt save notice:', e);
          }
        }
      }

      this.saveState();
      this.render();
      this.closeFullPromptModal();
    }

    /**
     * Opens the Sovereign Multi-Domain Trigger Cockpit & Test Bed Modal
     */
    openTriggerCockpitModal(node) {
      if (!node) return;
      this._ensureNodeStructures(node);
      this.selectedNodeId = node.id;
      this.activeModalNode = node;

      let overlay = document.getElementById('pipeline-trigger-modal-overlay');
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'pipeline-trigger-modal-overlay';
        overlay.className = 'pipeline-prompt-modal-overlay';
        overlay.innerHTML = `<div class="pipeline-trigger-modal-box" id="pipeline-trigger-modal-box"></div>`;
        document.body.appendChild(overlay);

        overlay.addEventListener('click', (e) => {
          if (e.target === overlay) this.closeTriggerCockpitModal();
        });

        window.addEventListener('keydown', (e) => {
          if (e.key === 'Escape' && overlay.classList.contains('active')) {
            this.closeTriggerCockpitModal();
          }
        });
      }

      const box = overlay.querySelector('#pipeline-trigger-modal-box');
      if (!box) return;

      const tc = node.triggerConfig || {};
      const ingressType = tc.ingressType || 'webhook';
      const channelVal = tc.channel || tc.symbol || tc.watchPath || tc.interval || '/api/webhook/pipeline';
      const condVal = tc.conditionExpr || 'payload.event != null';
      const samplePayloadVal = tc.samplePayload || JSON.stringify({
        event: "SIGNAL",
        symbol: "EURUSD",
        rsi: 28.4,
        spread: 0.2
      }, null, 2);

      // Get downstream targets for Port 1 and Port 2
      const out1Conn = this.connections.find(c => c.from === node.id && (c.fromPort || 'out-1') === 'out-1');
      const out2Conn = this.connections.find(c => c.from === node.id && c.fromPort === 'out-2');
      const target1Node = out1Conn ? this.nodes.find(n => n.id === out1Conn.to) : null;
      const target2Node = out2Conn ? this.nodes.find(n => n.id === out2Conn.to) : null;
      const target1Text = target1Node 
        ? `➡️ Connected to: <strong style="color:#00f2fe;">${target1Node.icon || '🤖'} ${target1Node.role || target1Node.name}</strong>` 
        : `<span style="color:#64748b; font-style:italic;">No agent connected to Port 1 (Drag cable from Port 1)</span>`;
      const target2Text = target2Node 
        ? `➡️ Connected to: <strong style="color:#f59e0b;">${target2Node.icon || '🤖'} ${target2Node.role || target2Node.name}</strong>` 
        : `<span style="color:#64748b; font-style:italic;">No agent connected to Port 2 (Drag cable from Port 2)</span>`;

      box.innerHTML = `
        <!-- Header -->
        <div class="prompt-modal-header" style="padding:16px 20px; border-bottom:1px solid rgba(255,255,255,0.08); display:flex; justify-content:space-between; align-items:center;">
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-size:26px; line-height:1; padding:8px; background:rgba(0,242,254,0.12); border:1px solid rgba(0,242,254,0.3); border-radius:8px;">${node.icon || '⚡'}</div>
            <div>
              <div style="display:flex; align-items:center; gap:8px;">
                <h3 style="margin:0; font-size:16px; color:#f8fafc; font-weight:700;">${node.role || node.name || 'Trigger Ingress Sensor'}</h3>
                <span style="font-size:10px; background:rgba(0,242,254,0.15); border:1px solid rgba(0,242,254,0.3); color:#00f2fe; padding:2px 8px; border-radius:12px; font-weight:700;">${node.domain || 'Sovereign Sensor'}</span>
              </div>
              <div style="font-size:11px; color:#94a3b8; margin-top:2px;">Sovereign Multi-Domain Ingress Cockpit • Universal Signal & Event Router</div>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="display:flex; align-items:center; gap:6px; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); padding:4px 10px; border-radius:20px; font-size:11px; color:#34d399; font-weight:600;">
              <span style="width:7px; height:7px; border-radius:50%; background:#10b981; display:inline-block; box-shadow:0 0 6px #10b981;"></span>
              <span>LISTENING</span>
            </div>
            <button type="button" class="prompt-modal-close" id="btn-close-trigger-modal" style="background:none; border:none; color:#94a3b8; font-size:18px; cursor:pointer; padding:4px 8px;">✕</button>
          </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="prompt-modal-tabs" style="display:flex; gap:4px; padding:0 20px; background:rgba(15,23,42,0.4); border-bottom:1px solid rgba(255,255,255,0.08);">
          <button type="button" class="prompt-tab-btn active" data-trig-tab="protocol" style="padding:10px 16px; font-size:12px; font-weight:600; color:#00f2fe; background:none; border:none; border-bottom:2px solid #00f2fe; cursor:pointer;">📡 Protocol & Source</button>
          <button type="button" class="prompt-tab-btn" data-trig-tab="rules" style="padding:10px 16px; font-size:12px; font-weight:600; color:#94a3b8; background:none; border:none; border-bottom:2px solid transparent; cursor:pointer;">⚖️ Rules & Port Routing</button>
          <button type="button" class="prompt-tab-btn" data-trig-tab="simulation" style="padding:10px 16px; font-size:12px; font-weight:600; color:#94a3b8; background:none; border:none; border-bottom:2px solid transparent; cursor:pointer;">🧪 Live Test Bed & Signal Flow</button>
        </div>

        <!-- Tab Bodies -->
        <div class="prompt-modal-content" style="flex:1; overflow-y:auto; padding:20px;">
          <!-- TAB 1: Protocol & Source -->
          <div class="trig-tab-pane active" id="trig-pane-protocol" style="display:flex; flex-direction:column; gap:16px;">
            <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:14px;">
              <label style="display:block; font-size:12px; font-weight:700; color:#e2e8f0; margin-bottom:6px;">Ingress Sensor Type</label>
              <select id="trig-cfg-type" style="width:100%; padding:8px 12px; background:#0f172a; border:1px solid rgba(255,255,255,0.15); border-radius:6px; color:#f8fafc; font-size:12.5px;">
                <option value="market_tick" ${ingressType === 'market_tick' ? 'selected' : ''}>📈 Forex / Crypto Market Tick Sensor (Price / Volatility / Spread)</option>
                <option value="webhook" ${ingressType === 'webhook' ? 'selected' : ''}>⚡ HTTP Webhook Ingress (TradingView / Stripe / Telegram / GitHub)</option>
                <option value="file_watcher" ${ingressType === 'file_watcher' ? 'selected' : ''}>📁 Directory & Document Observer (Contracts / CSVs / Tick Data)</option>
                <option value="chat_ingress" ${ingressType === 'chat_ingress' ? 'selected' : ''}>💬 Client Consultation & Message Intake (Psychology / Support / Inquiries)</option>
                <option value="cron" ${ingressType === 'cron' ? 'selected' : ''}>⏰ Chrono / Cron Recurring Scheduler (Periodic Audit / Time Ticker)</option>
                <option value="system_sentinel" ${ingressType === 'system_sentinel' ? 'selected' : ''}>🛡️ System Sentinel & Safety Guard (Telemetry / Resource Health)</option>
              </select>
            </div>

            <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:14px;">
              <label style="display:block; font-size:12px; font-weight:700; color:#e2e8f0; margin-bottom:6px;">Channel / Target / Endpoint Identifier</label>
              <input type="text" id="trig-cfg-channel" value="${escapeHtml(channelVal)}" placeholder="e.g. EURUSD, XAUUSD or /api/webhook/pipeline or vault/incoming/" style="width:100%; padding:8px 12px; background:#0f172a; border:1px solid rgba(255,255,255,0.15); border-radius:6px; color:#38bdf8; font-family:monospace; font-size:12.5px;" />
              <div style="font-size:11px; color:#64748b; margin-top:6px;">Specify target asset pair(s), HTTP endpoint path, local directory, or cron interval.</div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
              <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:12px;">
                <label style="display:block; font-size:11.5px; font-weight:700; color:#e2e8f0; margin-bottom:4px;">Authentication / Ingress Policy</label>
                <select id="trig-cfg-auth" style="width:100%; padding:6px 10px; background:#0f172a; border:1px solid rgba(255,255,255,0.15); border-radius:6px; color:#f8fafc; font-size:11.5px;">
                  <option value="open">Open Ingress (Local / Internal Signal)</option>
                  <option value="bearer">Bearer Secret Token Validation</option>
                  <option value="hmac">HMAC SHA-256 Webhook Signature</option>
                </select>
              </div>
              <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:12px;">
                <label style="display:block; font-size:11.5px; font-weight:700; color:#e2e8f0; margin-bottom:4px;">Execution Architecture</label>
                <div style="font-size:11px; color:#94a3b8; display:flex; align-items:center; gap:8px; margin-top:6px;">
                  <span style="color:#10b981; font-weight:700;">⚡ Real-time Asynchronous Ingress</span>
                  <span>(Zero Thread Blocking)</span>
                </div>
              </div>
            </div>
          </div>

          <!-- TAB 2: Rules & Port Routing -->
          <div class="trig-tab-pane" id="trig-pane-rules" style="display:none; flex-direction:column; gap:16px;">
            <!-- Port 1 Rule -->
            <div style="background:rgba(16,185,129,0.04); border:1px solid rgba(16,185,129,0.25); border-radius:8px; padding:14px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span style="background:#10b981; color:#060911; font-weight:800; font-size:11px; width:20px; height:20px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;">1</span>
                  <strong style="color:#34d399; font-size:13px;">Port 1: Primary Route (Condition Satisfied / Signal Fired)</strong>
                </div>
                <span style="font-size:10px; color:#10b981; font-weight:700; background:rgba(16,185,129,0.15); padding:2px 8px; border-radius:10px;">PRIMARY EMISSION</span>
              </div>
              <div style="font-size:11px; color:#94a3b8; margin-bottom:8px;">When incoming payload satisfies this condition, signal flows through Port 1 to downstream agent:</div>
              <input type="text" id="trig-cfg-rule-1" value="${escapeHtml(condVal)}" placeholder="e.g. payload.spread <= 1.2 && payload.rsi < 30" style="width:100%; padding:8px 12px; background:#0b1322; border:1px solid rgba(16,185,129,0.3); border-radius:6px; color:#6ee7b7; font-family:monospace; font-size:12px;" />
              <div style="margin-top:8px; font-size:11px; color:#cbd5e1; background:rgba(0,0,0,0.3); padding:8px 12px; border-radius:6px;">
                ${target1Text}
              </div>
            </div>

            <!-- Port 2 Rule -->
            <div style="background:rgba(245,158,11,0.04); border:1px solid rgba(245,158,11,0.25); border-radius:8px; padding:14px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span style="background:#f59e0b; color:#060911; font-weight:800; font-size:11px; width:20px; height:20px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;">2</span>
                  <strong style="color:#fbbf24; font-size:13px;">Port 2: Fallback Route (Condition Unmet / Risk Escalation / Else)</strong>
                </div>
                <span style="font-size:10px; color:#f59e0b; font-weight:700; background:rgba(245,158,11,0.15); padding:2px 8px; border-radius:10px;">FALLBACK / NOISE FILTER</span>
              </div>
              <div style="font-size:11px; color:#94a3b8; margin-bottom:8px;">If condition is FALSE or signal is rejected/filtered, routes through Port 2:</div>
              <div style="margin-top:8px; font-size:11px; color:#cbd5e1; background:rgba(0,0,0,0.3); padding:8px 12px; border-radius:6px;">
                ${target2Text}
              </div>
            </div>
          </div>

          <!-- TAB 3: Live Test Bed & Simulation -->
          <div class="trig-tab-pane" id="trig-pane-simulation" style="display:none; flex-direction:column; gap:14px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
              <label style="font-size:12px; font-weight:700; color:#e2e8f0;">Mock Ingress Payload (JSON)</label>
              <div style="display:flex; gap:6px; flex-wrap:wrap;">
                <button type="button" class="trig-preset-btn" data-preset="forex" style="font-size:10px; padding:3px 8px; background:rgba(0,242,254,0.1); border:1px solid rgba(0,242,254,0.3); color:#00f2fe; border-radius:4px; cursor:pointer;">📈 Forex Breakout</button>
                <button type="button" class="trig-preset-btn" data-preset="legal" style="font-size:10px; padding:3px 8px; background:rgba(168,85,247,0.1); border:1px solid rgba(168,85,247,0.3); color:#c084fc; border-radius:4px; cursor:pointer;">📁 Legal Contract</button>
                <button type="button" class="trig-preset-btn" data-preset="psychology" style="font-size:10px; padding:3px 8px; background:rgba(236,72,153,0.1); border:1px solid rgba(236,72,153,0.3); color:#f472b6; border-radius:4px; cursor:pointer;">💬 Client Intake</button>
                <button type="button" class="trig-preset-btn" data-preset="webhook" style="font-size:10px; padding:3px 8px; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#34d399; border-radius:4px; cursor:pointer;">⚡ Webhook POST</button>
              </div>
            </div>

            <textarea id="trig-cfg-payload" rows="8" style="width:100%; padding:10px 14px; background:#070d19; border:1px solid rgba(0,242,254,0.3); border-radius:6px; color:#e2e8f0; font-family:monospace; font-size:12px; line-height:1.5; resize:vertical;">${escapeHtml(samplePayloadVal)}</textarea>

            <button type="button" id="btn-trig-test-fire" style="padding:12px 20px; font-size:13px; font-weight:800; background:linear-gradient(135deg, #00f2fe 0%, #0284c7 100%); border:none; border-radius:6px; color:#060911; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px; box-shadow:0 0 20px rgba(0,242,254,0.4); transition:all 0.2s cubic-bezier(0.4, 0, 0.2, 1);">
              <span>⚡ Test Fire Trigger & Trace Live Signal Flow</span>
            </button>

            <!-- Live Ingress Execution Console -->
            <div>
              <div style="font-size:11px; font-weight:700; color:#94a3b8; margin-bottom:4px; display:flex; justify-content:space-between;">
                <span>Live Ingress Telemetry Console</span>
                <span id="trig-sim-eval-badge" style="font-size:10px; font-weight:700; color:#38bdf8;">Idle</span>
              </div>
              <pre id="trig-sim-console" style="margin:0; padding:10px 14px; background:#030712; border:1px solid rgba(255,255,255,0.08); border-radius:6px; color:#34d399; font-family:monospace; font-size:11px; height:120px; overflow-y:auto; line-height:1.4;">[SYSTEM] Sovereign Ingress Engine initialized. Ready for incoming signal event...</pre>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="prompt-modal-footer" style="padding:14px 20px; border-top:1px solid rgba(255,255,255,0.08); display:flex; justify-content:space-between; align-items:center; background:rgba(15,23,42,0.4);">
          <div style="font-size:11px; color:#64748b;">Changes are automatically synchronized to persistent DAG storage.</div>
          <div style="display:flex; gap:10px;">
            <button type="button" class="btn-cancel" id="btn-cancel-trig-modal" style="padding:8px 16px; font-size:12px; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); color:#cbd5e1; border-radius:6px; cursor:pointer;">Cancel</button>
            <button type="button" class="btn-save" id="btn-save-trig-modal" style="padding:8px 18px; font-size:12px; font-weight:700; background:#00f2fe; border:none; color:#060911; border-radius:6px; cursor:pointer; box-shadow:0 0 12px rgba(0,242,254,0.3);">Save & Apply</button>
          </div>
        </div>
      `;

      overlay.classList.add('active');

      // Bind Tabs
      const tabBtns = box.querySelectorAll('.prompt-tab-btn');
      tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          tabBtns.forEach(b => {
            b.classList.remove('active');
            b.style.color = '#94a3b8';
            b.style.borderBottomColor = 'transparent';
          });
          btn.classList.add('active');
          btn.style.color = '#00f2fe';
          btn.style.borderBottomColor = '#00f2fe';

          const targetTab = btn.getAttribute('data-trig-tab');
          box.querySelectorAll('.trig-tab-pane').forEach(p => p.style.display = 'none');
          const targetPane = box.querySelector(`#trig-pane-${targetTab}`);
          if (targetPane) targetPane.style.display = 'flex';
        });
      });

      // Bind Presets
      const presetBtns = box.querySelectorAll('.trig-preset-btn');
      presetBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const p = btn.getAttribute('data-preset');
          const txtPayload = box.querySelector('#trig-cfg-payload');
          const inpRule = box.querySelector('#trig-cfg-rule-1');
          const inpChannel = box.querySelector('#trig-cfg-channel');
          const simConsole = box.querySelector('#trig-sim-console');

          if (p === 'forex') {
            if (txtPayload) txtPayload.value = JSON.stringify({
              symbol: "EURUSD",
              bid: 1.0848,
              ask: 1.0850,
              spread: 0.2,
              rsi: 28.4,
              timeframe: "M15",
              volatility: "HIGH"
            }, null, 2);
            if (inpRule) inpRule.value = 'payload.spread <= 1.2 && payload.rsi < 30';
            if (inpChannel) inpChannel.value = 'EURUSD, XAUUSD';
            if (simConsole) simConsole.textContent += `\n[PRESET] Loaded Forex Breakout Sensor preset.`;
          } else if (p === 'legal') {
            if (txtPayload) txtPayload.value = JSON.stringify({
              event: "FILE_CREATED",
              file_name: "Master_Service_Agreement_2026.pdf",
              path: "vault/incoming/Master_Service_Agreement_2026.pdf",
              mime: "application/pdf",
              file_size_kb: 412,
              jurisdiction: "International Commercial Law"
            }, null, 2);
            if (inpRule) inpRule.value = 'payload.file_size_kb > 0 && !payload.file_name.startsWith(".")';
            if (inpChannel) inpChannel.value = 'vault/incoming/';
            if (simConsole) simConsole.textContent += `\n[PRESET] Loaded Legal Document Observer preset.`;
          } else if (p === 'psychology') {
            if (txtPayload) txtPayload.value = JSON.stringify({
              client_id: "CL-908",
              intake_form: "Initial Clinical Assessment",
              urgency: 4,
              primary_concern: "acute cognitive fatigue & burnout",
              session_type: "CBT"
            }, null, 2);
            if (inpRule) inpRule.value = 'payload.urgency >= 3 || payload.sentiment === "distressed"';
            if (inpChannel) inpChannel.value = 'web_portal_intake';
            if (simConsole) simConsole.textContent += `\n[PRESET] Loaded Client Consultation Intake preset.`;
          } else if (p === 'webhook') {
            if (txtPayload) txtPayload.value = JSON.stringify({
              event: "ORDER_SIGNAL",
              pair: "EURUSD",
              signal: "BUY",
              price: 1.0845,
              tp: 1.0920,
              sl: 1.0810,
              confidence: 0.94
            }, null, 2);
            if (inpRule) inpRule.value = 'payload.event != null';
            if (inpChannel) inpChannel.value = '/api/webhook/pipeline';
            if (simConsole) simConsole.textContent += `\n[PRESET] Loaded HTTP Webhook Gateway preset.`;
          }
        });
      });

      // Bind Test Fire Button
      box.querySelector('#btn-trig-test-fire')?.addEventListener('click', async () => {
        const txtPayload = box.querySelector('#trig-cfg-payload');
        const inpRule = box.querySelector('#trig-cfg-rule-1');
        const simConsole = box.querySelector('#trig-sim-console');
        const evalBadge = box.querySelector('#trig-sim-eval-badge');

        let payloadObj = {};
        try {
          payloadObj = JSON.parse(txtPayload ? txtPayload.value : '{}');
        } catch (e) {
          if (simConsole) simConsole.textContent += `\n[ERROR] Invalid JSON payload: ${e.message}`;
          return;
        }

        const condExpr = inpRule ? inpRule.value.trim() : '';
        let passes = true;
        if (condExpr) {
          try {
            const evalFn = new Function('payload', `try { return Boolean(${condExpr}); } catch(e) { return false; }`);
            passes = evalFn(payloadObj);
          } catch (e) {
            passes = true;
          }
        }

        if (evalBadge) {
          evalBadge.textContent = passes ? '🟢 Port 1 Emitted' : '🟠 Port 2 Fallback';
          evalBadge.style.color = passes ? '#10b981' : '#f59e0b';
        }

        if (simConsole) {
          simConsole.textContent += `\n[EVAL] Rule: "${condExpr || 'ANY'}" -> Result: ${passes ? 'TRUE (Port 1 Fired)' : 'FALSE (Port 2 Fallback)'}`;
          simConsole.textContent += `\n[DISPATCH] ⚡ Signal packet travelling along canvas cables...`;
          simConsole.scrollTop = simConsole.scrollHeight;
        }

        // Trigger real flow on canvas!
        this.runPipelineFlow(node.id, payloadObj);
      });

      // Bind Close and Save buttons
      box.querySelector('#btn-close-trigger-modal')?.addEventListener('click', () => this.closeTriggerCockpitModal());
      box.querySelector('#btn-cancel-trig-modal')?.addEventListener('click', () => this.closeTriggerCockpitModal());
      box.querySelector('#btn-save-trig-modal')?.addEventListener('click', () => this.saveAndCloseTriggerModal());
    }

    closeTriggerCockpitModal() {
      const overlay = document.getElementById('pipeline-trigger-modal-overlay');
      if (overlay) overlay.classList.remove('active');
      this.activeModalNode = null;
    }

    saveAndCloseTriggerModal() {
      const box = document.getElementById('pipeline-trigger-modal-box');
      if (box && this.activeModalNode) {
        const node = this.activeModalNode;
        const selType = box.querySelector('#trig-cfg-type');
        const inpChannel = box.querySelector('#trig-cfg-channel');
        const selAuth = box.querySelector('#trig-cfg-auth');
        const inpRule1 = box.querySelector('#trig-cfg-rule-1');
        const txtPayload = box.querySelector('#trig-cfg-payload');

        if (!node.triggerConfig) node.triggerConfig = {};
        if (selType) node.triggerConfig.ingressType = selType.value;
        if (inpChannel) {
          node.triggerConfig.channel = inpChannel.value.trim();
          node.triggerConfig.symbol = inpChannel.value.trim();
          node.triggerConfig.watchPath = inpChannel.value.trim();
          node.triggerConfig.interval = inpChannel.value.trim();
        }
        if (selAuth) node.triggerConfig.authMode = selAuth.value;
        if (inpRule1) node.triggerConfig.conditionExpr = inpRule1.value.trim();
        if (txtPayload) node.triggerConfig.samplePayload = txtPayload.value.trim();

        this.saveState();
        this.render();
      }
      this.closeTriggerCockpitModal();
    }

    /**
     * Autonomous Sovereign Multi-Domain Pipeline Workflow Execution Engine
     */
    async runPipelineFlow(startTriggerId = null, customPayload = null) {
      console.log('[SwarmPipeline] 🚀 Initiating sovereign multi-domain pipeline execution...');

      const statusBadge = this.boardEl?.querySelector('.pipeline-status-badge');
      const updateStatus = (text, color = '#00f2fe', bg = 'rgba(0,242,254,0.15)') => {
        if (statusBadge) {
          statusBadge.textContent = text;
          statusBadge.style.color = color;
          statusBadge.style.borderColor = color;
          statusBadge.style.background = bg;
        }
      };

      // 1. Identify Entry / Ingress Trigger Node(s)
      let startingNodes = [];
      if (startTriggerId) {
        const trg = this.nodes.find(n => n.id === startTriggerId);
        if (trg) startingNodes.push(trg);
      } else {
        startingNodes = this.nodes.filter(n => n.type === 'trigger' || (n.id && n.id.startsWith('trg-')) || (n.id && n.id.includes('ingress')));
        if (startingNodes.length === 0) {
          const leader = this.nodes.find(n => n.type === 'leader' || (n.id && n.id.includes('leader')));
          if (leader) startingNodes.push(leader);
          else if (this.nodes.length > 0) startingNodes.push(this.nodes[0]);
        }
      }

      if (startingNodes.length === 0) {
        updateStatus('⚠️ Empty DAG Canvas (Add nodes to run)', '#f59e0b', 'rgba(245,158,11,0.15)');
        return;
      }

      // Reset previous visual execution states
      this.boardEl?.querySelectorAll('.dag-node').forEach(el => el.classList.remove('node-firing', 'node-processing', 'node-success'));
      this.svgLayer?.querySelectorAll('.pipeline-photon-stream').forEach(el => el.classList.remove('active-flow-1', 'active-flow-2'));

      const log = (msg) => {
        const time = new Date().toLocaleTimeString();
        const line = `[${time}] ${msg}`;
        console.log(`[SwarmPipeline] ${line}`);
        const simConsole = document.getElementById('trig-sim-console');
        if (simConsole) {
          simConsole.textContent += `\n${line}`;
          simConsole.scrollTop = simConsole.scrollHeight;
        }
      };

      // 2. Cascade Execution
      for (const startNode of startingNodes) {
        const isTrigger = startNode.type === 'trigger' || (startNode.id && startNode.id.includes('ingress'));
        const nodeEl = document.getElementById(`dag-node-${startNode.id}`);

        if (isTrigger) {
          updateStatus(`⚡ Ingress Firing: ${startNode.role || startNode.name}...`, '#00f2fe');
          if (nodeEl) nodeEl.classList.add('node-firing');

          // Parse Payload
          let payload = customPayload;
          if (!payload && startNode.triggerConfig?.samplePayload) {
            try {
              payload = JSON.parse(startNode.triggerConfig.samplePayload);
            } catch (e) {
              payload = { raw: startNode.triggerConfig.samplePayload };
            }
          }
          if (!payload) payload = { event: 'TRIGGER_DISPATCH', timestamp: new Date().toISOString() };

          log(`⚡ Ingress Trigger [${startNode.role || startNode.name}] activated.`);

          // Evaluate condition
          const condExpr = startNode.triggerConfig?.conditionExpr || '';
          let conditionPassed = true;
          if (condExpr && condExpr.trim() !== '') {
            try {
              const evalFn = new Function('payload', `try { return Boolean(${condExpr}); } catch(e) { return false; }`);
              conditionPassed = evalFn(payload);
            } catch (err) {
              conditionPassed = true;
            }
          }

          const activePort = conditionPassed ? 'out-1' : 'out-2';
          log(`⚖️ Condition [${condExpr || 'ANY'}]: ${conditionPassed ? 'MATCHED (Port 1)' : 'UNMET (Port 2)'}`);

          await new Promise(r => setTimeout(r, 600));

          // Find Outgoing Connection for activePort
          const outgoingConns = this.connections.filter(c => c.from === startNode.id && (c.fromPort || 'out-1') === activePort);
          if (outgoingConns.length > 0) {
            for (const conn of outgoingConns) {
              const connGroup = this.svgLayer?.querySelector(`[data-conn-id="${conn.id}"]`);
              const photon = connGroup?.querySelector('.pipeline-photon-stream');
              if (photon) {
                photon.classList.add(activePort === 'out-1' ? 'active-flow-1' : 'active-flow-2');
              }

              const targetNode = this.nodes.find(n => n.id === conn.to);
              if (targetNode) {
                log(`🌐 Dispatched packet via ${activePort === 'out-1' ? 'Port 1 (Primary)' : 'Port 2 (Fallback)'} -> [${targetNode.role || targetNode.name}]`);
                await new Promise(r => setTimeout(r, 700));

                await this._cascadeExecuteNode(targetNode, payload, log, updateStatus);
              }
            }
          } else {
            log(`ℹ️ Ingress fired, but no cable wired from ${activePort}. Standing by.`);
          }

          if (nodeEl) {
            nodeEl.classList.remove('node-firing');
            nodeEl.classList.add('node-success');
          }
        } else {
          await this._cascadeExecuteNode(startNode, { initial: true }, log, updateStatus);
        }
      }

      // 3. Execution Finished
      updateStatus('✓ Multi-Domain Consensus Reached (Goal Met & Approved)', '#10b981', 'rgba(16,185,129,0.15)');
      log('🎯 Sovereign Swarm Flow execution completed successfully.');

      setTimeout(() => {
        this.svgLayer?.querySelectorAll('.pipeline-photon-stream').forEach(el => el.classList.remove('active-flow-1', 'active-flow-2'));
        this.boardEl?.querySelectorAll('.dag-node').forEach(el => el.classList.remove('node-firing', 'node-processing', 'node-success'));
      }, 3500);
    }

    async _cascadeExecuteNode(node, incomingData, log, updateStatus) {
      const nodeEl = document.getElementById(`dag-node-${node.id}`);
      if (nodeEl) nodeEl.classList.add('node-processing');

      updateStatus(`🤖 ${node.role || node.name}: Processing Ingress...`, '#38bdf8');
      log(`🤖 Agent [${node.role || node.name}] ingesting data packet...`);

      await new Promise(r => setTimeout(r, 650));

      log(`✓ [${node.role || node.name}] task completed with Consensus Verified.`);
      if (nodeEl) {
        nodeEl.classList.remove('node-processing');
        nodeEl.classList.add('node-success');
      }

      // Propagate down Port 1 (Primary Route)
      const outConns = this.connections.filter(c => c.from === node.id && (c.fromPort || 'out-1') === 'out-1');
      for (const conn of outConns) {
        const connGroup = this.svgLayer?.querySelector(`[data-conn-id="${conn.id}"]`);
        const photon = connGroup?.querySelector('.pipeline-photon-stream');
        if (photon) photon.classList.add('active-flow-1');

        const next = this.nodes.find(n => n.id === conn.to);
        if (next) {
          log(`➡️ [${node.role || node.name}] handed off signal -> [${next.role || next.name}]`);
          await new Promise(r => setTimeout(r, 650));
          await this._cascadeExecuteNode(next, incomingData, log, updateStatus);
        }
      }
    }

    /**
     * Retrieves the currently active preset object
     */
    getActivePreset() {
      if (this.presets && this.activePresetId && this.presets[this.activePresetId]) {
        return this.presets[this.activePresetId];
      }
      return {
        id: this.activePresetId || 'coding',
        name: this.activePresetId || 'Coding',
        nodes: this.nodes || [],
        connections: this.connections || []
      };
    }

    /**
     * Dynamically lights up agent node and connected cables based on real-time task execution.
     * @param {string} agentId - The agent ID, role, or name
     * @param {string} state - 'working' | 'processing' | 'done' | 'idle' | 'firing'
     */
    setAgentActivityState(agentId, state, options = {}) {
      if (!agentId || !this.nodes || this.nodes.length === 0) return;

      const cleanId = String(agentId).toLowerCase().replace(/^(agent-|session-)/, '');
      const isWorking = (state === 'working' || state === 'processing' || state === 'busy');
      const isDone = (state === 'done' || state === 'success' || state === 'completed');

      const matchedNodes = this.nodes.filter(n => {
        const nAgent = String(n.agentId || '').toLowerCase();
        const nId = String(n.id || '').toLowerCase();
        const nRole = String(n.role || '').toLowerCase();
        const nName = String(n.name || '').toLowerCase();
        return nAgent === cleanId ||
               nId === cleanId ||
               nId.includes(cleanId) ||
               cleanId.includes(nId) ||
               nRole.includes(cleanId) ||
               cleanId.includes(nRole) ||
               nName.includes(cleanId) ||
               cleanId.includes(nName) ||
               (cleanId === 'leader' && n.type === 'leader') ||
               (cleanId.includes('backend') && (nId.includes('backend') || nRole.includes('backend'))) ||
               (cleanId.includes('frontend') && (nId.includes('frontend') || nRole.includes('frontend'))) ||
               (cleanId.includes('security') && (nId.includes('security') || nRole.includes('security'))) ||
               (cleanId.includes('qc') && (nId.includes('qc') || nRole.includes('qc') || nRole.includes('quality')));
      });

      if (matchedNodes.length === 0) return;

      matchedNodes.forEach(node => {
        const nodeEl = document.getElementById(`dag-node-${node.id}`);
        const statusEl = nodeEl?.querySelector('.dag-node-status-indicator');
        const connectedConns = this.connections.filter(c => c.from === node.id || c.to === node.id);

        if (isWorking) {
          if (nodeEl) {
            nodeEl.classList.remove('node-success');
            nodeEl.classList.add('node-processing');
          }
          if (statusEl) {
            statusEl.textContent = '⚡ RUNNING';
            statusEl.style.display = 'inline-flex';
          }
          connectedConns.forEach(conn => {
            const connGroup = this.svgLayer?.querySelector(`[data-conn-id="${conn.id}"]`);
            const cable = connGroup?.querySelector('.pipeline-cable');
            const photon = connGroup?.querySelector('.pipeline-photon-stream');
            if (cable) cable.classList.add('cable-active');
            if (photon) photon.classList.add('active-flow-1');
          });
        } else if (isDone) {
          if (nodeEl) {
            nodeEl.classList.remove('node-processing');
            nodeEl.classList.add('node-success');
          }
          if (statusEl) {
            statusEl.textContent = '✓ DONE';
            statusEl.style.display = 'inline-flex';
          }
          setTimeout(() => {
            if (nodeEl) nodeEl.classList.remove('node-success');
            if (statusEl) statusEl.style.display = 'none';
            connectedConns.forEach(conn => {
              const connGroup = this.svgLayer?.querySelector(`[data-conn-id="${conn.id}"]`);
              const cable = connGroup?.querySelector('.pipeline-cable');
              const photon = connGroup?.querySelector('.pipeline-photon-stream');
              if (cable) cable.classList.remove('cable-active');
              if (photon) photon.classList.remove('active-flow-1', 'active-flow-2');
            });
          }, 2500);
        } else {
          // Idle
          if (nodeEl) nodeEl.classList.remove('node-processing', 'node-success', 'node-firing');
          if (statusEl) statusEl.style.display = 'none';
          connectedConns.forEach(conn => {
            const connGroup = this.svgLayer?.querySelector(`[data-conn-id="${conn.id}"]`);
            const cable = connGroup?.querySelector('.pipeline-cable');
            const photon = connGroup?.querySelector('.pipeline-photon-stream');
            if (cable) cable.classList.remove('cable-active');
            if (photon) photon.classList.remove('active-flow-1', 'active-flow-2');
          });
        }
      });
    }

    /**
     * Executes pipeline cyber photon simulation (Universal Entry Point)
     */
    executePipelineSimulation() {
      return this.runPipelineFlow();
    }
  }

  // Expose to window
  window.SwarmPipelineEngine = SwarmPipelineEngine;
  window.swarmPipelineInstance = new SwarmPipelineEngine();
  window.swarmPipelineEngine = window.swarmPipelineInstance;
  window.swarmPipeline = window.swarmPipelineInstance;

  // Universal Sovereign Agent Studio Opener
  window.openAgentStudio = function(agentIdOrData) {
    if (!window.swarmPipelineInstance) {
      window.swarmPipelineInstance = new SwarmPipelineEngine();
    }
    const engine = window.swarmPipelineInstance;
    if (!engine.nodes || engine.nodes.length === 0) {
      engine._initDefaultNodes();
    }
    if (typeof engine.loadDynamicRoster === 'function') {
      engine.loadDynamicRoster();
    }

    let targetNode = null;
    const rawId = (typeof agentIdOrData === 'string') 
      ? agentIdOrData 
      : (agentIdOrData?.id || agentIdOrData?.persona || agentIdOrData?.agentId || 'mr.flow');
    
    const cleanId = String(rawId).toLowerCase().replace(/^(agent-|session-)/, '');

    if (engine.nodes && engine.nodes.length > 0) {
      targetNode = engine.nodes.find(n => {
        const nAgent = String(n.agentId || '').toLowerCase();
        const nId = String(n.id || '').toLowerCase();
        const nRole = String(n.role || '').toLowerCase();
        const nName = String(n.name || '').toLowerCase();
        return nAgent === cleanId || 
               nId === cleanId || 
               nId.includes(cleanId) || 
               nRole.includes(cleanId) || 
               nName.includes(cleanId) ||
               (cleanId === 'leader' && n.type === 'leader');
      });
    }

    if (!targetNode && engine.nodes && engine.nodes.length > 0) {
      targetNode = engine.nodes[0];
    }

    if (targetNode) {
      engine.openFullPromptModal(targetNode);
    }
  };

})(window, document);
