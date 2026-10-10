/**
 * FLOWORK OS — SOVEREIGN TOOL LOADER ARCHITECTURE
 * File: canvas-ui/tool_loader.js
 * Author: Flowork OS Sovereign Architect & Awenk Audico
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 *
 * Architecture Doctrines:
 * 1. Modular Dynamic Tool Loader & Manifest Scanner
 * 2. Strict Anti-FOUC (Flash of Unstyled Content) Asset Injection
 * 3. Sovereign Lifecycle Registry: window.FloworkToolRegistry = { register, get, mountLive, renderOutput }
 * 4. Universal Default Fallback Engine: Zero Blank / Zero Crash Guarantee with Frameless Holo Stream & Exit Code 0 HUD.
 */

(function (window, document) {
  'use strict';

  // --- 1. SOVEREIGN CONSTANTS & ENVIRONMENT DETECTION ---
  const KNOWN_TOOLS = [
    'render_visual',
    'run_command',
    'view_file',
    'write_to_file',
    'replace_file_content',
    'search_tools',
    'search_web',
    'read_url_content',
    'file_ops',
    'brain_control',
    'skill_control',
    'manage_subagents',
    'screenshot',
    'flow_lock',
    'sys_health',
    'audit_security',
    'detect_hardcode',
    'audit_portability',
    'web_security_audit',
    'website_intelligence',
    'schedule',
    'manage_task',
    'plugin_control',
    'request_publish_gatekeeper',
    'youtube_spy_video',
    'youtube_spy_channel',
    'youtube_spy_transcript',
    'youtube_spy_summary',
    'youtube_spy_comments',
    'youtube_spy_competitor_strategy',
    'ask_question',
    'system_restart',
    'plugin_publish',
    'invoke_subagent',
    'define_subagent',
    'send_message',
    'generate_image',
    'send_media'
  ];

  function resolveBasePath() {
    // Detect whether hosted under /canvas/, /canvas-ui/, or relative path
    const path = window.location.pathname || '';
    if (path.includes('/canvas/member-area') || path.includes('/canvas/')) {
      return '/canvas/tools';
    }
    if (path.includes('/canvas-ui/')) {
      return '/canvas-ui/tools';
    }
    return 'tools';
  }

  const BASE_TOOLS_URL = resolveBasePath();

  // --- 2. UNIVERSAL FALLBACK STYLES (ANTI-FOUC INLINE DEFENSE) ---
  const UNIVERSAL_FALLBACK_CSS = `
/* =============================================================================
   FLOWORK OS — UNIVERSAL TOOL LOADER & HOLOGRAPHIC STREAM FALLBACK CSS
   Co-authored-by: Flowork OS <agent@floworkos.com>
   ============================================================================= */

:root {
  --fl-cyan-glow: #00f0ff;
  --fl-emerald-glow: #10b981;
  --fl-amber-glow: #f59e0b;
  --fl-purple-glow: #a855f7;
  --fl-rose-glow: #f43f5e;
  --fl-surface-holo: rgba(13, 22, 42, 0.45);
  --fl-surface-card: rgba(10, 17, 34, 0.65);
  --fl-shadow-deep: 0 14px 36px -4px rgba(0, 0, 0, 0.55), 0 4px 16px -2px rgba(0, 0, 0, 0.4);
  --fl-font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
}

/* Base Frameless Reset for all Tool Cards */
.flowork-tool-frameless,
.fl-generic-tool-card,
.fl-live-ambient-stage,
.chat-chart-card,
.fl-tool-capsule-item {
  border: none !important;
  outline: none !important;
  box-shadow: var(--fl-shadow-deep) !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
}

/* Ambient Holographic Stream Stage */
.fl-live-ambient-stage {
  background: var(--fl-surface-holo) !important;
  border-radius: 8px;
  padding: 10px 14px;
  margin: 8px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  overflow: hidden;
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.fl-live-ambient-stage.is-finished {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
  pointer-events: none;
}

.fl-ambient-hud-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  font-family: var(--fl-font-mono);
  font-size: 11px;
}

.fl-ambient-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fl-ambient-glyph {
  color: var(--fl-cyan-glow);
  font-size: 13px;
  text-shadow: 0 0 8px var(--fl-cyan-glow);
  animation: flAmbientPulse 2s infinite ease-in-out;
}

.fl-ambient-tag {
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 240, 255, 0.1);
  color: var(--fl-cyan-glow);
}

.fl-ambient-tag.emerald {
  background: rgba(16, 185, 129, 0.1);
  color: var(--fl-emerald-glow);
}

.fl-ambient-tag.amber {
  background: rgba(245, 158, 11, 0.1);
  color: var(--fl-amber-glow);
}

.fl-ambient-tag.purple {
  background: rgba(168, 85, 247, 0.1);
  color: var(--fl-purple-glow);
}

.fl-ambient-tag.rose {
  background: rgba(244, 63, 94, 0.1);
  color: var(--fl-rose-glow);
}

.fl-ambient-sep {
  opacity: 0.4;
  color: #94a3b8;
}

.fl-ambient-target {
  color: #cbd5e1;
  font-size: 11px;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fl-ambient-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--fl-font-mono);
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  background: rgba(0, 240, 255, 0.15);
  color: var(--fl-cyan-glow);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
  letter-spacing: 0.04em;
  transition: all 0.3s ease;
}

.fl-ambient-badge.emerald {
  background: rgba(16, 185, 129, 0.2);
  color: var(--fl-emerald-glow);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.3);
}

.fl-ambient-spinner {
  width: 8px;
  height: 8px;
  border: 1.5px solid var(--fl-cyan-glow);
  border-top-color: transparent;
  border-radius: 50%;
  animation: flSpin 0.75s linear infinite;
}

.fl-ambient-laser-track {
  width: 100%;
  height: 14px;
  overflow: hidden;
  position: relative;
}

.fl-ambient-wave-svg {
  width: 100%;
  height: 100%;
}

.fl-ambient-sine-wave {
  animation: flWaveTravel 3s linear infinite;
}

.fl-ambient-laser-beam {
  animation: flBeamFollow 3s linear infinite;
}

@keyframes flSpin {
  to { transform: rotate(360deg); }
}

@keyframes flAmbientPulse {
  0%, 100% { opacity: 0.8; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.15); }
}

@keyframes flWaveTravel {
  0% { stroke-dashoffset: 0; }
  100% { stroke-dashoffset: -120; }
}

@keyframes flBeamFollow {
  0% { cx: 20; opacity: 0.4; }
  50% { cx: 300; opacity: 1; }
  100% { cx: 580; opacity: 0.4; }
}

/* Universal Fallback Tool Result Card */
.fl-generic-tool-card {
  background: var(--fl-surface-card) !important;
  border-radius: 8px;
  margin: 10px 0;
  padding: 12px 16px;
  font-family: var(--fl-font-mono);
  color: #e2e8f0;
  position: relative;
  overflow: hidden;
}

.fl-generic-tool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  margin-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.fl-generic-tool-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  color: var(--fl-cyan-glow);
  letter-spacing: 0.04em;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.3);
}

.fl-generic-tool-badge {
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  background: rgba(16, 185, 129, 0.15);
  color: var(--fl-emerald-glow);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.25);
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.fl-generic-tool-badge.error {
  background: rgba(244, 63, 94, 0.15);
  color: var(--fl-rose-glow);
  box-shadow: 0 0 10px rgba(244, 63, 94, 0.25);
}

.fl-generic-tool-body {
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fl-generic-tool-params {
  background: rgba(0, 0, 0, 0.35);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 11px;
  color: #94a3b8;
  max-height: 180px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.fl-generic-tool-output {
  background: rgba(4, 8, 18, 0.7);
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 11px;
  color: #38bdf8;
  max-height: 260px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  border-left: 2px solid var(--fl-cyan-glow);
}
`;

  // Synchronously inject Universal Fallback Styles to eliminate FOUC before DOM paint
  function injectFallbackStylesImmediately() {
    if (document.getElementById('flowork-universal-fallback-style')) return;
    const styleEl = document.createElement('style');
    styleEl.id = 'flowork-universal-fallback-style';
    styleEl.textContent = UNIVERSAL_FALLBACK_CSS;
    if (document.head) {
      document.head.prepend(styleEl);
    } else {
      document.addEventListener('DOMContentLoaded', () => {
        if (!document.getElementById('flowork-universal-fallback-style')) {
          document.head.prepend(styleEl);
        }
      }, { once: true });
    }
  }

  injectFallbackStylesImmediately();

  // --- 3. UNIVERSAL DEFAULT FALLBACK TOOL MODULE ---
  const UniversalDefaultModule = {
    id: 'default_fallback',
    name: 'Universal Sovereign Tool Module',
    isDefaultFallback: true,
    manifest: {
      name: 'default_fallback',
      title: 'Universal Sovereign Fallback',
      description: 'Frameless ambient holographic stream & status monitor with Exit Code 0 guarantee.',
      version: '1.0.0',
      styles: [],
      frameless: true
    },

    mountLive(activeSlot, toolName, details, stepIdx) {
      if (!activeSlot) return null;
      activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

      const cleanName = String(toolName || 'tool')
        .replace(/^flow_/, '')
        .replace(/^default_api:/, '')
        .toUpperCase();

      const d = (details && details.details && typeof details.details === 'object')
        ? { ...details, ...details.details }
        : (details && typeof details === 'object' ? details : {});

      const summary = d.toolSummary || d.toolAction || d.action || d.Action || d.CommandLine || d.target || d.file || (typeof details === 'string' ? details : 'Sovereign operation in progress');
      const rawSnippet = String(summary).replace(/[\r\n]+/g, ' ').trim();
      const snippet = rawSnippet.length > 50 ? rawSnippet.slice(0, 47) + '…' : rawSnippet;

      let stage = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
      if (!stage) {
        stage = document.createElement('div');
        stage.className = 'fl-live-ambient-stage flowork-tool-frameless';
        stage.setAttribute('data-live-step', String(stepIdx));
        stage._spawnTime = Date.now();
        activeSlot.appendChild(stage);
      }

      const gradId = `ambient-holo-grad-${stepIdx}-${Math.floor(Math.random() * 100000)}`;

      stage.innerHTML = `
        <div class="fl-ambient-hud-line">
          <div class="fl-ambient-meta">
            <span class="fl-ambient-glyph">⟡</span>
            <span class="fl-ambient-tag">[SOVEREIGN // ${escapeHtml(cleanName)}]</span>
            <span class="fl-ambient-sep">›</span>
            <span class="fl-ambient-target" title="${escapeHtml(rawSnippet)}">${escapeHtml(snippet)}</span>
          </div>
          <span class="fl-ambient-badge">
            <span class="fl-ambient-spinner"></span> ACTIVE
          </span>
        </div>
        <div class="fl-ambient-laser-track">
          <svg viewBox="0 0 600 14" class="fl-ambient-wave-svg" preserveAspectRatio="none">
            <defs>
              <linearGradient id="${gradId}" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stop-color="var(--fl-cyan-glow, #00f0ff)" stop-opacity="0" />
                <stop offset="45%" stop-color="var(--fl-cyan-glow, #00f0ff)" stop-opacity="0.8" />
                <stop offset="50%" stop-color="#ffffff" stop-opacity="1" />
                <stop offset="55%" stop-color="var(--fl-cyan-glow, #00f0ff)" stop-opacity="0.8" />
                <stop offset="100%" stop-color="var(--fl-cyan-glow, #00f0ff)" stop-opacity="0" />
              </linearGradient>
            </defs>
            <line x1="0" y1="7" x2="600" y2="7" stroke="var(--fl-cyan-glow, #00f0ff)" stroke-opacity="0.15" stroke-width="1" stroke-dasharray="3 5" />
            <path class="fl-ambient-sine-wave" d="M 0 7 Q 75 1 150 7 T 300 7 T 450 7 T 600 7" fill="none" stroke="var(--fl-cyan-glow, #00f0ff)" stroke-width="1.8" stroke-linecap="round" />
            <circle class="fl-ambient-laser-beam" cx="50" cy="7" r="2.2" fill="#ffffff" filter="drop-shadow(0 0 6px var(--fl-cyan-glow, #00f0ff))" />
          </svg>
        </div>
      `;
      return stage;
    },

    renderOutput(toolsArea, toolName, details, status, stepIdx, activeToolElements) {
      if (!toolsArea) return null;

      const cleanName = String(toolName || 'tool')
        .replace(/^flow_/, '')
        .replace(/^default_api:/, '')
        .toUpperCase();

      const d = (details && details.details && typeof details.details === 'object')
        ? { ...details, ...details.details }
        : (details && typeof details === 'object' ? details : {});

      const isDone = (status === 'done');
      const isError = (status === 'error' || status === 'failed');

      // Dismiss live box if still visible
      if (isDone || isError) {
        if (typeof window.dismissLiveToolBox === 'function') {
          const outData = (details && details.output !== undefined) ? details.output : (details && details.rawOutput !== undefined ? details.rawOutput : null);
          window.dismissLiveToolBox(null, stepIdx, outData);
        }
      }

      const card = document.createElement('div');
      card.className = 'fl-generic-tool-card flowork-tool-frameless';
      card.setAttribute('data-tool-name', cleanName);
      card.setAttribute('data-step-idx', String(stepIdx));

      const paramsText = typeof d === 'object' ? JSON.stringify(d, null, 2) : String(d);
      const rawOut = details && (details.output ?? details.rawOutput ?? details.stdout ?? details.result ?? null);
      const outputText = rawOut !== null && rawOut !== undefined
        ? (typeof rawOut === 'object' ? JSON.stringify(rawOut, null, 2) : String(rawOut))
        : '';

      const badgeHtml = isError
        ? `<span class="fl-generic-tool-badge error">✕ FAILED</span>`
        : `<span class="fl-generic-tool-badge">✓ EXIT CODE 0 // VERIFIED</span>`;

      card.innerHTML = `
        <div class="fl-generic-tool-header">
          <div class="fl-generic-tool-title">
            <span>⚙️</span>
            <span>[SOVEREIGN // ${escapeHtml(cleanName)}]</span>
          </div>
          ${badgeHtml}
        </div>
        <div class="fl-generic-tool-body">
          ${paramsText ? `<div class="fl-generic-tool-params" title="Operation Payload">${escapeHtml(paramsText)}</div>` : ''}
          ${outputText ? `<div class="fl-generic-tool-output" title="Execution Output">${escapeHtml(outputText)}</div>` : ''}
        </div>
      `;

      if (activeToolElements && typeof activeToolElements.set === 'function') {
        activeToolElements.set(stepIdx, card);
      }

      toolsArea.appendChild(card);
      return card;
    }
  };

  // Helper HTML escaper
  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // --- 4. TOOL REGISTRY CORE ENGINE ---
  const loadedStylesheets = new Set();
  const registeredTools = new Map();
  let isReadyPromise = null;

  class FloworkToolRegistryEngine {
    constructor() {
      this.tools = registeredTools;
      this.basePath = BASE_TOOLS_URL;
      this.defaultModule = UniversalDefaultModule;
      // Register fallback default immediately
      this.register('default', UniversalDefaultModule);
    }

    /**
     * Register a tool definition.
     * @param {string} toolId
     * @param {Object} toolDef
     */
    register(toolId, toolDef) {
      if (!toolId || !toolDef) return;
      const normalizedId = String(toolId).toLowerCase().trim();
      const mergedDef = {
        id: normalizedId,
        name: toolDef.name || normalizedId,
        manifest: toolDef.manifest || {},
        mountLive: toolDef.mountLive || UniversalDefaultModule.mountLive,
        renderOutput: toolDef.renderOutput || UniversalDefaultModule.renderOutput,
        renderVisual: toolDef.renderVisual || null,
        ...toolDef
      };
      this.tools.set(normalizedId, mergedDef);
      return mergedDef;
    }

    /**
     * Get a tool by ID.
     * MANDATE: Never return null or undefined. If not found, return Universal Default Fallback!
     * @param {string} toolId
     * @returns {Object}
     */
    get(toolId) {
      if (!toolId) return this.defaultModule;
      const normalizedId = String(toolId).toLowerCase().trim();
      if (this.tools.has(normalizedId)) {
        return this.tools.get(normalizedId);
      }
      // Check partial match (e.g. 'flow_render_visual' -> 'render_visual')
      for (const [key, tool] of this.tools.entries()) {
        if (normalizedId.includes(key) || key.includes(normalizedId)) {
          return tool;
        }
      }
      // UNIVERSAL FALLBACK GUARANTEE
      return this.defaultModule;
    }

    /**
     * Check if a specific tool is registered (excluding default fallback)
     * @param {string} toolId
     * @returns {boolean}
     */
    has(toolId) {
      if (!toolId) return false;
      const normalizedId = String(toolId).toLowerCase().trim();
      return this.tools.has(normalizedId);
    }

    /**
     * List all registered tool IDs.
     * @returns {Array<string>}
     */
    list() {
      return Array.from(this.tools.keys());
    }

    /**
     * Mount live ambient holographic stream for any tool.
     * Guaranteed to never throw.
     */
    mountLive(activeSlot, toolName, details, stepIdx) {
      try {
        const tool = this.get(toolName);
        return tool.mountLive(activeSlot, toolName, details, stepIdx);
      } catch (err) {
        console.warn(`[FloworkToolRegistry] mountLive fallback on error:`, err);
        return this.defaultModule.mountLive(activeSlot, toolName, details, stepIdx);
      }
    }

    /**
     * Render output card for any tool.
     * Guaranteed to never throw or blank out.
     */
    renderOutput(toolsArea, toolName, details, status, stepIdx, activeToolElements) {
      try {
        const tool = this.get(toolName);
        return tool.renderOutput(toolsArea, toolName, details, status, stepIdx, activeToolElements);
      } catch (err) {
        console.warn(`[FloworkToolRegistry] renderOutput fallback on error:`, err);
        return this.defaultModule.renderOutput(toolsArea, toolName, details, status, stepIdx, activeToolElements);
      }
    }

    /**
     * Anti-FOUC CSS Injector
     * Injects a stylesheet into <head> with duplicate prevention and promise settlement.
     * @param {string} toolId
     * @param {string} cssHref
     * @returns {Promise<void>}
     */
    injectStyle(toolId, cssHref) {
      if (!cssHref) return Promise.resolve();
      const styleId = `flowork-tool-style-${toolId}`;
      if (document.getElementById(styleId) || loadedStylesheets.has(cssHref)) {
        return Promise.resolve();
      }

      return new Promise((resolve) => {
        const link = document.createElement('link');
        link.id = styleId;
        link.rel = 'stylesheet';
        link.href = cssHref;
        link.onload = () => {
          loadedStylesheets.add(cssHref);
          resolve();
        };
        link.onerror = () => {
          // In case of 404 or network issue, resolve anyway to avoid hanging FOUC barrier
          console.warn(`[FloworkToolRegistry] Notice: style not found for ${toolId} (${cssHref}), using universal fallback.`);
          resolve();
        };

        if (document.head) {
          document.head.appendChild(link);
        } else {
          document.addEventListener('DOMContentLoaded', () => document.head.appendChild(link), { once: true });
        }
      });
    }

    /**
     * Load an individual tool manifest and its associated style.css
     * @param {string} toolId
     * @param {string} [customBasePath]
     * @returns {Promise<Object>}
     */
    async loadTool(toolId, customBasePath) {
      const base = customBasePath || this.basePath;
      const manifestUrl = `${base}/${toolId}/manifest.json`;

      try {
        const res = await fetch(manifestUrl, { cache: 'no-cache' });
        if (!res.ok) {
          throw new Error(`HTTP ${res.status} fetching manifest: ${manifestUrl}`);
        }
        const manifest = await res.json();

        // Extract and inject styles
        const styles = Array.isArray(manifest.styles)
          ? manifest.styles
          : (manifest.style ? [manifest.style] : ['style.css']);

        const stylePromises = styles.map((s) => {
          const rawUrl = s.startsWith('http') || s.startsWith('/')
            ? s
            : `${base}/${toolId}/${s}`;
          const styleUrl = rawUrl.includes('?') ? rawUrl : `${rawUrl}?v=2.20.5`;
          return this.injectStyle(toolId, styleUrl);
        });

        await Promise.all(stylePromises);

        // Register the loaded tool
        const toolObj = this.register(toolId, {
          name: manifest.title || manifest.name || toolId,
          manifest: manifest,
          styleLoaded: true
        });

        // Optionally load scripts if defined
        if (manifest.script || manifest.main) {
          const scriptFile = manifest.script || manifest.main;
          const scriptUrl = scriptFile.startsWith('http') || scriptFile.startsWith('/')
            ? scriptFile
            : `${base}/${toolId}/${scriptFile}`;
          this._injectScript(toolId, scriptUrl);
        }

        return toolObj;
      } catch (err) {
        // Return default module without breaking caller
        return this.defaultModule;
      }
    }

    _injectScript(toolId, scriptUrl) {
      const scriptId = `flowork-tool-script-${toolId}`;
      if (document.getElementById(scriptId)) return;
      const script = document.createElement('script');
      script.id = scriptId;
      script.src = scriptUrl;
      script.async = true;
      document.head.appendChild(script);
    }

    /**
     * Scan and load all known and manifest-defined tools.
     * Prevents FOUC by resolving when all initial style injections are underway.
     * @returns {Promise<void>}
     */
    async scanAndLoad(toolsToLoad = KNOWN_TOOLS) {
      const promises = toolsToLoad.map(id => this.loadTool(id));
      await Promise.allSettled(promises);
    }

    /**
     * Lifecycle wait gate: await FloworkToolRegistry.ready()
     */
    ready() {
      if (!isReadyPromise) {
        isReadyPromise = this.scanAndLoad();
      }
      return isReadyPromise;
    }

    /**
     * Bootstrapper
     */
    init() {
      injectFallbackStylesImmediately();
      return this.ready();
    }
  }

  // --- 5. EXPORT SOVEREIGN SINGLETON ---
  const registryInstance = new FloworkToolRegistryEngine();
  window.FloworkToolRegistry = registryInstance;

  // Auto-init immediately or on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => registryInstance.init(), { once: true });
  } else {
    registryInstance.init();
  }

})(window, document);
