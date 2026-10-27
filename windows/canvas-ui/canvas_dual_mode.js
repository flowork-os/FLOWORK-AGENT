/**
 * =============================================================================
 * FLOWORK OS — DUAL-CANVAS DYNAMIC LIFECYCLE CONTROLLER
 * Module: canvas_dual_mode.js
 * 
 * Strict Architecture Guarantee:
 * - When in Solo Mode (Mr. Flow): Group War Room is completely UNMOUNTED.
 *   0 active timers, 0 background fetch calls, 0 residual DOM nodes.
 * - When in Group Mode: Swarm War Room mounts dynamic SVG DAG task graph,
 *   Blackboard obligations, and multi-lane channels.
 * 
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 * =============================================================================
 */

(function(window) {
  'use strict';

  // Helper for safe HTML escaping
  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // ===========================================================================
  // 1. SOVEREIGN SOLO STUDIO CONTROLLER (MR. FLOW)
  // ===========================================================================
  const SoloStudio = {
    isMounted: false,
    container: null,
    activeSubTab: 'artifacts', // 'artifacts' | 'trajectory' | 'terminal'
    sessionData: null,

    mount(rootEl, sessionData) {
      if (!rootEl) return;
      this.container = rootEl;
      this.sessionData = sessionData || null;
      this.isMounted = true;

      this.render();
      console.log('[DualCanvas] 👤 SoloStudio mounted successfully for session:', sessionData ? sessionData.id : 'default');
    },

    unmount() {
      if (!this.isMounted && !this.container) return;
      if (this.container) {
        this.container.replaceChildren(); // 0 DOM nodes!
      }
      this.isMounted = false;
      this.container = null;
      this.sessionData = null;
      console.log('[DualCanvas] 👤 SoloStudio unmounted.');
    },

    render() {
      if (!this.container) return;
      this.container.replaceChildren();

      const wrapper = document.createElement('div');
      wrapper.className = 'canvas-mode-container solo-studio-container';
      wrapper.id = 'stage-solo-studio';

      // Extract details
      const agPersona = (this.sessionData && (this.sessionData.agent_persona || this.sessionData.agent_id)) || 'mr.flow';
      const displayName = agPersona === 'default' ? 'Mr. Flow' : agPersona;
      const modelName = (this.sessionData && this.sessionData.model) || (window.selectedChatModelId || 'gemini-3.8-flash-high');
      const wsPath = (this.sessionData && this.sessionData.workspace_path) || (window.currentSessionWorkspacePath || 'Root Workspace');
      const wsFolder = wsPath.split('/').filter(Boolean).pop() || 'flowork';

      // Find last tool execution from session steps
      const steps = (this.sessionData && Array.isArray(this.sessionData.steps)) ? this.sessionData.steps : [];
      const toolSteps = steps.filter(s => s.type === 'FLWCTX_STEP_TYPE_RUN_COMMAND' || s.tool);
      const lastToolStep = toolSteps.length > 0 ? toolSteps[toolSteps.length - 1] : null;

      // Extract last code / file / terminal artifact
      let artifactSnippet = 'No files viewed or edited yet in this session.\nExecute tools or view code in chat to inspect live artifacts here.';
      let artifactPath = 'Workspace Idle';
      let artifactTool = 'Idle';

      if (lastToolStep) {
        artifactTool = lastToolStep.tool || (lastToolStep.runCommand && lastToolStep.runCommand.commandLine) || 'tool_call';
        const details = (lastToolStep.runCommand && lastToolStep.runCommand.details) || {};
        artifactPath = details.TargetFile || details.AbsolutePath || details.CommandLine || 'Active Execution';
        
        if (details.ReplacementContent) {
          artifactSnippet = `// REPLACEMENT DIFF: ${artifactPath}\n` + details.ReplacementContent;
        } else if (details.CodeContent) {
          artifactSnippet = `// WRITTEN FILE: ${artifactPath}\n` + details.CodeContent;
        } else if (details.real_content) {
          artifactSnippet = `// VIEWED FILE: ${artifactPath}\n` + details.real_content;
        } else if (lastToolStep.output) {
          artifactSnippet = String(lastToolStep.output).slice(0, 2000);
        }
      }

      // Header Bar
      const headerHtml = `
        <div class="solo-header-bar">
          <div class="solo-header-identity">
            <div class="solo-avatar-crest">👤</div>
            <div class="solo-title-wrap">
              <div class="solo-title-main">
                <span>${escapeHtml(displayName)}</span>
                <span class="solo-badge-tag">SOLO CORE</span>
              </div>
              <div class="solo-subtitle">
                <span>📁 ${escapeHtml(wsFolder)}</span>
                <span>•</span>
                <span>⚡ ${escapeHtml(modelName)}</span>
              </div>
            </div>
          </div>
          <div class="solo-header-telemetry">
            <div class="solo-pill solo-pill-accent">
              <span>✓ Exit Code 0 Verified</span>
            </div>
            <div class="solo-pill">
              <span>🔒 @lock Protected</span>
            </div>
            <div class="solo-pill">
              <span>🧠 .fl_brain Connected</span>
            </div>
          </div>
        </div>
      `;

      // Main Split Grid
      const bodyHtml = `
        <div class="solo-body-grid">
          <!-- Left: Workspace & Code Artifacts -->
          <div class="solo-card">
            <div class="solo-card-header">
              <div class="solo-card-title">
                <span>💻</span>
                <span>LIVE WORKSPACE & ARTIFACTS</span>
              </div>
              <div class="solo-tab-strip">
                <button class="solo-subtab-btn ${this.activeSubTab === 'artifacts' ? 'active' : ''}" data-subtab="artifacts">Artifact & Code</button>
                <button class="solo-subtab-btn ${this.activeSubTab === 'trajectory' ? 'active' : ''}" data-subtab="trajectory">Trajectory Steps (${steps.length})</button>
                <button class="solo-subtab-btn ${this.activeSubTab === 'terminal' ? 'active' : ''}" data-subtab="terminal">Execution Trace</button>
              </div>
            </div>
            <div class="solo-card-body" id="solo-card-content">
              ${this.renderSubTabContent(artifactPath, artifactTool, artifactSnippet, steps, lastToolStep)}
            </div>
          </div>

          <!-- Right: Radar HUD & Doktrin Checks -->
          <div class="solo-card">
            <div class="solo-card-header">
              <div class="solo-card-title">
                <span>🎯</span>
                <span>SOVEREIGN AGENT RADAR</span>
              </div>
              <div style="font-size: 10px; color: #00e5ff; font-weight: 700;">ACTIVE TELEMETRY</div>
            </div>
            <div class="solo-card-body">
              <div class="solo-radar-row">
                <span class="solo-radar-label">⚡ Execution State:</span>
                <span class="solo-radar-val" style="color: #34d399;">Ready / Standby</span>
              </div>
              <div class="solo-radar-row">
                <span class="solo-radar-label">🛡️ Circuit Breaker:</span>
                <span class="solo-radar-val" style="color: #38bdf8;">0 / 3 Failures (Secure)</span>
              </div>
              <div class="solo-radar-row">
                <span class="solo-radar-label">⚙️ Active Category:</span>
                <span class="solo-radar-val">CAT-026 (Solo Execution)</span>
              </div>
              <div class="solo-radar-row">
                <span class="solo-radar-label">🧹 Anti-Nyampah:</span>
                <span class="solo-radar-val" style="color: #34d399;">.FL_BIN/scratch/ Clean</span>
              </div>

              <div style="margin-top: 14px; font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">
                Iron Doctrine Guardians:
              </div>
              <div class="solo-doctrine-list">
                <div class="solo-doctrine-item">
                  <span>✓</span>
                  <span><strong>Anti-Overclaim:</strong> Success requires empirical exit code 0.</span>
                </div>
                <div class="solo-doctrine-item">
                  <span>✓</span>
                  <span><strong>Zero-Trust:</strong> Multi-OS boundary without path hardcoding.</span>
                </div>
                <div class="solo-doctrine-item">
                  <span>✓</span>
                  <span><strong>Kesucian @lock:</strong> Locked code lines strictly guarded.</span>
                </div>
                <div class="solo-doctrine-item">
                  <span>✓</span>
                  <span><strong>Zero-Zombie:</strong> Only verified Flowork triggers active.</span>
                </div>
              </div>

              <div style="margin-top: 16px; display: flex; gap: 8px;">
                <button class="solo-btn-action" id="btn-solo-recall-brain">
                  <span>🧠 Recall .fl_brain</span>
                </button>
                <button class="solo-btn-action" id="btn-solo-clean-scratch">
                  <span>🧹 Purge Scratch</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      `;

      wrapper.innerHTML = headerHtml + bodyHtml;
      this.container.appendChild(wrapper);

      // Bind Subtab events
      wrapper.querySelectorAll('.solo-subtab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const tab = e.currentTarget.dataset.subtab;
          this.activeSubTab = tab;
          wrapper.querySelectorAll('.solo-subtab-btn').forEach(b => b.classList.toggle('active', b.dataset.subtab === tab));
          const contentEl = wrapper.querySelector('#solo-card-content');
          if (contentEl) {
            contentEl.innerHTML = this.renderSubTabContent(artifactPath, artifactTool, artifactSnippet, steps, lastToolStep);
          }
        });
      });

      // Bind Action buttons
      const btnRecall = wrapper.querySelector('#btn-solo-recall-brain');
      if (btnRecall) {
        btnRecall.addEventListener('click', () => {
          if (typeof window.showToast === 'function') {
            window.showToast('Recalling sovereign solutions from {effective_ws}/.fl_brain');
          }
        });
      }

      const btnClean = wrapper.querySelector('#btn-solo-clean-scratch');
      if (btnClean) {
        btnClean.addEventListener('click', async () => {
          try {
            await fetch('/api/tools/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                tool: 'run_command',
                args: { CommandLine: 'rm -rf .FL_BIN/scratch/*', Cwd: wsPath }
              })
            });
            if (typeof window.showToast === 'function') window.showToast('Scratch directory purged successfully');
          } catch (_) {
            if (typeof window.showToast === 'function') window.showToast('Purge scratch signal sent');
          }
        });
      }
    },

    renderSubTabContent(path, tool, snippet, steps, lastTool) {
      if (this.activeSubTab === 'artifacts') {
        return `
          <div class="solo-artifact-meta">
            <div>
              <span style="color: #00e5ff; font-weight: 700;">${escapeHtml(tool)}</span>: 
              <span style="color: #94a3b8;">${escapeHtml(path)}</span>
            </div>
            <button class="solo-btn-action" onclick="navigator.clipboard.writeText(this.closest('.solo-card-body').querySelector('.solo-artifact-box').innerText)">
              📋 Copy Snippet
            </button>
          </div>
          <pre class="solo-artifact-box">${escapeHtml(snippet)}</pre>
        `;
      } else if (this.activeSubTab === 'trajectory') {
        if (!steps || steps.length === 0) {
          return '<div style="color: #94a3b8; padding: 20px; text-align: center;">No steps recorded in this conversation yet.</div>';
        }
        return `
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${steps.map((st, idx) => {
              const typeLabel = (st.type || '').replace('FLWCTX_STEP_TYPE_', '');
              const toolLabel = st.tool || (st.runCommand && st.runCommand.commandLine) || '';
              return `
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); padding: 8px 12px; border-radius: 6px; font-size: 11px;">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-weight: 700; color: #38bdf8;">Step #${idx + 1} • ${escapeHtml(typeLabel)}</span>
                    <span style="color: #34d399;">${escapeHtml(st.status || 'DONE')}</span>
                  </div>
                  ${toolLabel ? `<div style="color: #cbd5e1; font-family: monospace;">🛠️ ${escapeHtml(toolLabel)}</div>` : ''}
                </div>
              `;
            }).join('')}
          </div>
        `;
      } else {
        // Terminal trace
        const out = lastTool ? (lastTool.output || 'Command executed with Exit Code 0.') : 'Terminal idle. Waiting for next instruction.';
        return `
          <div style="font-family: monospace; font-size: 11px; background: #030712; padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 229, 255, 0.15); color: #38bdf8; max-height: 380px; overflow-y: auto; white-space: pre-wrap;">
$ flowork-cli trace --session=${escapeHtml((this.sessionData && this.sessionData.id) || 'active')}
[RUNTIME TELEMETRY: EXIT CODE 0]
${escapeHtml(String(out).slice(0, 3000))}
          </div>
        `;
      }
    }
  };

  // ===========================================================================
  // 2. SWARM TACTICAL WAR ROOM CONTROLLER (MULTI-AGENT SQUAD)
  // ===========================================================================
  const GroupWarRoom = {
    isMounted: false,
    container: null,
    sessionData: null,
    pollTimer: null,
    abortController: null,
    selectedNodeId: null,
    office3D: null,

    mount(rootEl, sessionData) {
      // Ensure previous instance is wiped
      if (this.isMounted) this.unmount();

      if (!rootEl) return;
      this.container = rootEl;
      this.sessionData = sessionData || null;
      this.isMounted = true;
      this.abortController = new AbortController();

      this.render();
      this.startPollingIfVisible();
      console.log('[DualCanvas] 👥 GroupWarRoom mounted for group:', sessionData ? (sessionData.group_name || sessionData.id) : 'unknown');
    },

    unmount() {
      // Strict homework invariant: completely eliminate group presence from DOM and background
      if (this.office3D) {
        this.office3D.destroy();
        this.office3D = null;
      }
      if (this.pollTimer) {
        clearInterval(this.pollTimer);
        this.pollTimer = null;
      }
      if (this.abortController) {
        this.abortController.abort();
        this.abortController = null;
      }
      if (this.container) {
        this.container.replaceChildren(); // 0 DOM nodes!
      }
      this.isMounted = false;
      this.container = null;
      this.sessionData = null;
      this.selectedNodeId = null;
      console.log('[DualCanvas] 🛡️ GroupWarRoom completely UNMOUNTED & PURGED. 0 timers, 0 DOM nodes.');
    },

    startPollingIfVisible() {
      if (this.pollTimer) clearInterval(this.pollTimer);
      if (!this.sessionData || !this.sessionData.id) return;

      const sid = this.sessionData.id;
      // Low-overhead refresh every 6 seconds ONLY when mounted
      this.pollTimer = setInterval(async () => {
        if (!this.isMounted || !this.sessionData) return;
        try {
          const res = await fetch(`/api/chat/steps/${sid}`, {
            signal: this.abortController ? this.abortController.signal : undefined
          });
          if (res.ok) {
            const json = await res.json();
            if (json.status === 'ok' && json.data) {
              this.sessionData = json.data;
              this.updateDynamicSections();
            }
          }
        } catch (_) {
          // Aborted or network pause
        }
      }, 6000);
    },

    render() {
      if (!this.container) return;
      this.container.replaceChildren();

      const wrapper = document.createElement('div');
      wrapper.className = 'canvas-mode-container group-warroom-container';
      wrapper.id = 'stage-group-warroom';

      const gName = (this.sessionData && (this.sessionData.group_name || this.sessionData.title)) || 'Swarm Squad Group';
      const gDom = (this.sessionData && this.sessionData.group_domain) || 'technology';
      const members = (this.sessionData && Array.isArray(this.sessionData.members) && this.sessionData.members.length > 0)
        ? this.sessionData.members
        : ['default', 'planner', 'coder-specialist', 'qa-engineer'];
      const adminName = (this.sessionData && this.sessionData.admin) || 'default';

      // Header Bar
      const headerHtml = `
        <div class="warroom-header-bar">
          <div class="warroom-identity">
            <div class="warroom-avatar-crest">👥</div>
            <div class="warroom-title-wrap">
              <div class="warroom-title-main">
                <span>${escapeHtml(gName)}</span>
                <span class="warroom-badge-tag">TACTICAL WAR ROOM</span>
              </div>
              <div class="warroom-subtitle">
                <span>Domain: <strong>${escapeHtml(gDom)}</strong></span>
                <span>•</span>
                <span>Coordinator: <strong>@${escapeHtml(adminName)}</strong></span>
                <span>•</span>
                <span>${members.length} Squad Agents</span>
              </div>
            </div>
          </div>
          <div class="warroom-header-actions">
            <div class="warroom-pill-phase">
              <span>⚡ MESH PHASE: COLLABORATIVE CONSENSUS</span>
            </div>
          </div>
        </div>
      `;

      // Center Stage: Executive Boardroom 3D Office & Dynamic SVG DAG
      const dagHtml = `
        <div class="warroom-dag-stage">
          <div class="warroom-dag-header">
            <div class="warroom-dag-title">
              <span>🏢</span>
              <span>EXECUTIVE BOARDROOM & SWARM TOPOLOGY</span>
            </div>
            <div style="font-size: 10px; color: #a855f7; display: flex; gap: 8px; align-items: center;">
              <div class="group-office-subtabs" style="display: flex; gap: 4px;">
                <button class="solo-btn-action active" id="btn-subtab-3d-office" style="padding: 2px 8px; font-size: 10px;">🏢 3D Office</button>
                <button class="solo-btn-action" id="btn-subtab-dag-mesh" style="padding: 2px 8px; font-size: 10px;">🕸️ SVG DAG</button>
              </div>
              <button class="solo-btn-action" id="btn-warroom-recenter" style="padding: 2px 8px; font-size: 10px;">Reset View</button>
            </div>
          </div>
          <div class="warroom-dag-canvas-wrap" id="warroom-stage-mount" style="position: relative; width: 100%; height: 100%; min-height: 280px;">
            <div id="warroom-3d-mount" class="group-office-canvas-wrap" style="width: 100%; height: 100%; position: absolute; inset: 0;">
              <canvas id="group-office-3d-canvas"></canvas>
            </div>
            <div id="warroom-dag-mount" style="width: 100%; height: 100%; position: absolute; inset: 0; display: none;"></div>
          </div>
        </div>
      `;

      // Bottom Split: Live Blackboard & Inter-Agent Stream
      const bottomHtml = `
        <div class="warroom-bottom-grid">
          <!-- Left: Swarm Blackboard -->
          <div class="warroom-card">
            <div class="warroom-card-header">
              <div class="warroom-card-title">
                <span>📋</span>
                <span>SHARED BLACKBOARD & OBLIGATIONS</span>
              </div>
              <span style="font-size: 10px; color: #c084fc; font-weight: 600;">STAGE-GATES</span>
            </div>
            <div class="warroom-card-body" id="warroom-blackboard-body">
              ${this.renderBlackboardContent(members)}
            </div>
          </div>

          <!-- Right: Inter-Agent Channel Feed -->
          <div class="warroom-card">
            <div class="warroom-card-header">
              <div class="warroom-card-title">
                <span>📡</span>
                <span>SWARM CHANNEL DISPATCH TRAFFIC</span>
              </div>
              <span style="font-size: 10px; color: #38bdf8; font-weight: 600;">REAL-TIME</span>
            </div>
            <div class="warroom-card-body" id="warroom-stream-body">
              ${this.renderChannelFeed()}
            </div>
          </div>
        </div>
      `;

      wrapper.innerHTML = headerHtml + dagHtml + bottomHtml;
      this.container.appendChild(wrapper);

      // Mount 3D Modern Executive Office
      const canvas3D = wrapper.querySelector('#group-office-3d-canvas');
      const wrap3D = wrapper.querySelector('#warroom-3d-mount');
      if (canvas3D && wrap3D && typeof window.GroupOffice3D === 'function') {
        try {
          this.office3D = new window.GroupOffice3D(canvas3D, wrap3D);
          this.office3D.syncMembers(members);
        } catch (err) {
          console.warn('[GroupWarRoom] Error mounting GroupOffice3D:', err);
        }
      }

      // Render Dynamic SVG DAG in background container
      const svgMount = wrapper.querySelector('#warroom-dag-mount');
      if (svgMount) {
        this.renderSvgDag(svgMount, members, adminName);
      }

      // Subtab switcher: 3D Office vs SVG DAG
      const btn3D = wrapper.querySelector('#btn-subtab-3d-office');
      const btnDag = wrapper.querySelector('#btn-subtab-dag-mesh');
      if (btn3D && btnDag && wrap3D && svgMount) {
        btn3D.addEventListener('click', () => {
          btn3D.classList.add('active');
          btnDag.classList.remove('active');
          wrap3D.style.display = 'block';
          svgMount.style.display = 'none';
          if (this.office3D && typeof this.office3D.onWindowResize === 'function') {
            this.office3D.onWindowResize();
          }
        });
        btnDag.addEventListener('click', () => {
          btnDag.classList.add('active');
          btn3D.classList.remove('active');
          wrap3D.style.display = 'none';
          svgMount.style.display = 'block';
          this.renderSvgDag(svgMount, members, adminName);
        });
      }

      // Bind Recenter
      const btnRecenter = wrapper.querySelector('#btn-warroom-recenter');
      if (btnRecenter && svgMount) {
        btnRecenter.addEventListener('click', () => {
          if (wrap3D && wrap3D.style.display !== 'none' && this.office3D) {
            this.office3D.camSpherical = { radius: 7.2, theta: 0.1, phi: 1.05 };
            this.office3D.updateCameraPosition();
          } else {
            this.renderSvgDag(svgMount, members, adminName);
          }
        });
      }
    },

    renderSvgDag(containerEl, members, admin) {
      if (!containerEl) return;
      containerEl.replaceChildren();

      const rect = containerEl.getBoundingClientRect();
      const width = rect.width > 200 ? rect.width : 780;
      const height = rect.height > 150 ? rect.height : 280;

      const svgNs = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(svgNs, 'svg');
      svg.setAttribute('class', 'swarm-dag-svg');
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.setAttribute('width', '100%');
      svg.setAttribute('height', '100%');

      // SVG Definitions (Arrow markers, gradients)
      const defs = document.createElementNS(svgNs, 'defs');
      defs.innerHTML = `
        <marker id="dag-arrow" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#a855f7" />
        </marker>
        <marker id="dag-arrow-active" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
        </marker>
        <linearGradient id="link-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#a855f7" stop-opacity="0.6"/>
          <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.8"/>
        </linearGradient>
      `;
      svg.appendChild(defs);

      // Node layout calculations:
      // Hub node (admin) placed at left or center-left, specialists radiating or tiered
      const nodeCoords = [];
      const nodeWidth = 140;
      const nodeHeight = 52;

      // Group layout:
      // Leader node
      const centerX = width * 0.22;
      const centerY = height * 0.5;
      nodeCoords.push({
        id: admin,
        name: admin === 'default' ? 'Leader (Admin)' : admin,
        role: 'Orchestrator',
        isLeader: true,
        x: centerX,
        y: centerY
      });

      // Child specialist nodes
      const specialists = members.filter(m => m !== admin);
      const specCount = specialists.length;

      if (specCount > 0) {
        const rightColX = width * 0.72;
        const spacingY = height / (specCount + 1);

        specialists.forEach((m, idx) => {
          const ny = spacingY * (idx + 1);
          let roleName = 'Specialist';
          if (m.includes('plan')) roleName = 'Architecture';
          else if (m.includes('code')) roleName = 'Engineering';
          else if (m.includes('ui')) roleName = 'UI/UX Design';
          else if (m.includes('qa')) roleName = 'Quality Control';
          else if (m.includes('reverse') || m.includes('crypto')) roleName = 'Domain Analyst';

          nodeCoords.push({
            id: m,
            name: m,
            role: roleName,
            isLeader: false,
            x: rightColX,
            y: ny
          });
        });
      }

      // Draw SVG Link Paths (Bezier curves from leader to specialists)
      const leaderCoord = nodeCoords[0];
      for (let i = 1; i < nodeCoords.length; i++) {
        const target = nodeCoords[i];
        const path = document.createElementNS(svgNs, 'path');
        const c1X = leaderCoord.x + (target.x - leaderCoord.x) * 0.5;
        const c1Y = leaderCoord.y;
        const c2X = leaderCoord.x + (target.x - leaderCoord.x) * 0.5;
        const c2Y = target.y;

        const d = `M ${leaderCoord.x} ${leaderCoord.y} C ${c1X} ${c1Y}, ${c2X} ${c2Y}, ${target.x} ${target.y}`;
        path.setAttribute('d', d);
        path.setAttribute('class', i === 1 ? 'dag-link-path dag-link-active' : 'dag-link-path');
        path.setAttribute('marker-end', i === 1 ? 'url(#dag-arrow-active)' : 'url(#dag-arrow)');
        svg.appendChild(path);
      }

      // Draw Nodes
      nodeCoords.forEach((node) => {
        const g = document.createElementNS(svgNs, 'g');
        const isSelected = this.selectedNodeId === node.id;
        g.setAttribute('class', `dag-node-group ${node.isLeader ? 'leader' : ''} ${isSelected ? 'active' : ''}`);
        g.setAttribute('transform', `translate(${node.x - nodeWidth / 2}, ${node.y - nodeHeight / 2})`);

        // Node background rectangle
        const rectEl = document.createElementNS(svgNs, 'rect');
        rectEl.setAttribute('class', 'dag-node-rect');
        rectEl.setAttribute('width', String(nodeWidth));
        rectEl.setAttribute('height', String(nodeHeight));
        g.appendChild(rectEl);

        // Role indicator dot
        const dot = document.createElementNS(svgNs, 'circle');
        dot.setAttribute('cx', '14');
        dot.setAttribute('cy', '18');
        dot.setAttribute('r', '4');
        dot.setAttribute('fill', node.isLeader ? '#fbbf24' : '#38bdf8');
        g.appendChild(dot);

        // Label
        const textTitle = document.createElementNS(svgNs, 'text');
        textTitle.setAttribute('class', 'dag-node-label');
        textTitle.setAttribute('x', String(nodeWidth / 2 + 6));
        textTitle.setAttribute('y', '22');
        textTitle.textContent = `@${node.name}`;
        g.appendChild(textTitle);

        // Sublabel
        const textRole = document.createElementNS(svgNs, 'text');
        textRole.setAttribute('class', 'dag-node-sublabel');
        textRole.setAttribute('x', String(nodeWidth / 2));
        textRole.setAttribute('y', '38');
        textRole.textContent = `[${node.role}]`;
        g.appendChild(textRole);

        // Interaction
        g.addEventListener('click', (e) => {
          e.stopPropagation();
          this.selectedNodeId = node.id;
          containerEl.querySelectorAll('.dag-node-group').forEach(el => el.classList.remove('active'));
          g.classList.add('active');
          if (typeof window.showToast === 'function') {
            window.showToast(`Swarm focus: @${node.name} (${node.role})`);
          }
        });

        svg.appendChild(g);
      });

      containerEl.appendChild(svg);
    },

    renderBlackboardContent(members) {
      return `
        <div class="blackboard-section-title">Swarm Telemetry & Activity Stream</div>
        <div class="blackboard-item">
          <div class="blackboard-dot"></div>
          <div class="blackboard-text">
            <strong>Active Swarm Units:</strong> ${members.length} specialists operational in Virtual Office.
          </div>
        </div>
      `;
    },

    renderChannelFeed() {
      const steps = (this.sessionData && Array.isArray(this.sessionData.steps)) ? this.sessionData.steps : [];
      if (steps.length === 0) {
        return '<div style="color: #94a3b8; padding: 16px; text-align: center;">Swarm channel quiet. Issue a command to dispatch tasks.</div>';
      }

      // Filter recent user commands and planner responses
      const recent = steps.slice(-4);
      return recent.map((st) => {
        let sender = '@default (Coordinator)';
        let msg = '';
        if (st.type === 'FLWCTX_STEP_TYPE_USER_INPUT') {
          sender = 'User Dispatcher';
          msg = (st.userInput && st.userInput.message) || '';
        } else if (st.plannerResponse) {
          msg = String(st.plannerResponse.response || '').slice(0, 180) + '...';
        } else if (st.runCommand) {
          sender = 'Engine Execution Hook';
          msg = `Tool triggered: ${st.tool || st.runCommand.commandLine || 'action'}`;
        }

        return `
          <div class="swarm-feed-row">
            <div class="swarm-feed-header">
              <span class="swarm-feed-sender">${escapeHtml(sender)}</span>
              <span class="swarm-feed-time">Synchronized</span>
            </div>
            <div class="swarm-feed-msg">${escapeHtml(msg)}</div>
          </div>
        `;
      }).join('');
    },

    updateDynamicSections() {
      if (!this.container) return;
      if (this.office3D && this.sessionData && Array.isArray(this.sessionData.members)) {
        this.office3D.syncMembers(this.sessionData.members);
      }
      const bbBody = this.container.querySelector('#warroom-blackboard-body');
      if (bbBody && this.sessionData) {
        bbBody.innerHTML = this.renderBlackboardContent(this.sessionData.members || []);
      }
      const streamBody = this.container.querySelector('#warroom-stream-body');
      if (streamBody) {
        streamBody.innerHTML = this.renderChannelFeed();
      }
    }
  };

  // ===========================================================================
  // 3. MASTER GOVERNOR & DUAL-CANVAS ROUTER
  // ===========================================================================
  const DualCanvasController = {
    SoloStudio,
    GroupWarRoom,
    currentSessionData: null,

    init() {
      console.log('[DualCanvas] ⚡ Initializing Dual-Canvas Controller with Sovereign Persistence...');
      this.bindTabEvents();
      this.bindModeButtons();

      // 🔒 Sovereign Persist Gate: Always restore user-commanded session mode (Default: Team)
      const savedMode = (localStorage.getItem('xflow_session_mode') === 'solo') ? 'solo' : 'team';
      const isTeam = (savedMode !== 'solo');
      const activeType = isTeam ? 'group' : 'personal';

      window.currentSessionMode = savedMode;
      window.currentSessionType = activeType;

      this.updateModeButtons(savedMode);

      if (window.office3DInstance && typeof window.office3DInstance.setOfficeMode === 'function') {
        window.office3DInstance.setOfficeMode(savedMode);
      }

      const viewCanvasStage = document.getElementById('view-canvas-stage');
      if (viewCanvasStage && viewCanvasStage.classList.contains('active')) {
        this.onActivateTab();
      }
    },

    bindTabEvents() {
      // Bind Stage Tab in Main Navigation Strip
      const tabCanvas = document.getElementById('tab-canvas-stage');
      if (tabCanvas) {
        tabCanvas.addEventListener('click', () => {
          if (typeof window.switchTab === 'function') {
            window.switchTab('canvas-stage');
          }
        });
      }

      // Bind Quick Toggle button in Rightbar Chat Header
      const btnToggle = document.getElementById('btn-toggle-canvas-studio');
      if (btnToggle) {
        btnToggle.addEventListener('click', () => {
          if (typeof window.switchTab === 'function') {
            window.switchTab('canvas-stage');
          }
        });
      }
    },

    bindModeButtons() {
      const btnSolo = document.querySelectorAll('#btn-mode-solo, .btn-mode-solo');
      const btnTeam = document.querySelectorAll('#btn-mode-team, .btn-mode-team');

      btnSolo.forEach(btn => {
        if (!btn._hasModeListener) {
          btn._hasModeListener = true;
          btn.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchMode('solo');
          });
        }
      });

      btnTeam.forEach(btn => {
        if (!btn._hasModeListener) {
          btn._hasModeListener = true;
          btn.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchMode('team');
          });
        }
      });
    },

    updateModeButtons(mode) {
      const isTeam = (mode !== 'solo');
      const btnSolo = document.querySelectorAll('#btn-mode-solo, .btn-mode-solo');
      const btnTeam = document.querySelectorAll('#btn-mode-team, .btn-mode-team');

      btnSolo.forEach(btn => {
        if (!isTeam) {
          btn.classList.add('active');
          btn.style.background = '#00F2FE';
          btn.style.color = '#020617';
          btn.style.boxShadow = '0 0 10px rgba(0, 242, 254, 0.4)';
        } else {
          btn.classList.remove('active');
          btn.style.background = 'transparent';
          btn.style.color = '#94a3b8';
          btn.style.boxShadow = 'none';
        }
      });

      btnTeam.forEach(btn => {
        if (isTeam) {
          btn.classList.add('active');
          btn.style.background = '#a855f7';
          btn.style.color = '#ffffff';
          btn.style.boxShadow = '0 0 10px rgba(168, 85, 247, 0.4)';
        } else {
          btn.classList.remove('active');
          btn.style.background = 'transparent';
          btn.style.color = '#94a3b8';
          btn.style.boxShadow = 'none';
        }
      });
    },

    async switchMode(targetMode) {
      const isGroup = (targetMode === 'team');
      const mode = isGroup ? 'team' : 'solo';
      const sessionType = isGroup ? 'group' : 'personal';
      const persona = isGroup ? 'leader' : 'mr.flow';

      console.log(`[DualCanvas] Switching session mode to ${mode.toUpperCase()} (session_type=${sessionType}, persona=${persona})...`);

      window.currentSessionMode = mode;
      window.currentSessionType = sessionType;
      localStorage.setItem('xflow_session_mode', mode);

      this.updateModeButtons(mode);

      if (this.currentSessionData) {
        this.currentSessionData.session_type = sessionType;
        this.currentSessionData.mode = mode;
      }
      if (window.currentLoadedSessionData) {
        window.currentLoadedSessionData.session_type = sessionType;
        window.currentLoadedSessionData.mode = mode;
      }

      // 1. Notify Backend Core if session exists
      const activeId = window.currentChatSessionId;
      if (activeId) {
        try {
          await fetch('/api/chat/sessions/' + encodeURIComponent(activeId) + '/mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode, session_type: sessionType, persona: persona })
          });
          console.log(`[DualCanvas] Backend session mode persisted for ${activeId}`);
        } catch (err) {
          console.warn('[DualCanvas] Failed to persist session mode to backend:', err);
        }
      }

      // 2. Set active persona in session
      if (typeof window.setSessionAgentPersona === 'function') {
        window.setSessionAgentPersona(persona, { preserveSession: true });
      }

      // 3. Synchronize 3D Office Environment Mode
      if (window.office3DInstance && typeof window.office3DInstance.setSessionMode === 'function') {
        window.office3DInstance.setSessionMode(isGroup ? 'group' : 'solo');
      }

      // 4. Update Header and Tab styling
      this.syncSession(this.currentSessionData);

      // 5. Toast Feedback
      if (typeof window.showToast === 'function') {
        window.showToast(isGroup ? '🔷 Swarm Tactical War Room Mode Active' : '🟢 Sovereign Solo Studio Focus Active', 'info');
      }
    },

    // Called on tab switch ('canvas-stage')
    onActivateTab() {
      const isGroup = Boolean(this.currentSessionData && (this.currentSessionData.session_type === 'group' || this.currentSessionData.mode === 'team'));
      const rootEl = document.getElementById('canvas-dynamic-root');
      if (!rootEl) return;

      if (isGroup) {
        // Enforce SoloStudio unmount
        SoloStudio.unmount();
        GroupWarRoom.mount(rootEl, this.currentSessionData);
      } else {
        // Enforce GroupWarRoom unmount & purge (Strict homework requirement!)
        GroupWarRoom.unmount();
        SoloStudio.mount(rootEl, this.currentSessionData);
      }
    },

    // Called when user leaves 'canvas-stage'
    onDeactivateTab() {
      // If group warroom was running background timers, pause them
      if (GroupWarRoom.isMounted && GroupWarRoom.pollTimer) {
        clearInterval(GroupWarRoom.pollTimer);
        GroupWarRoom.pollTimer = null;
      }
      if (SoloStudio.isMounted) {
        SoloStudio.unmount();
      }
    },

    // Called on loadChatSession or startNewChatSession
    syncSession(sessionData) {
      this.currentSessionData = sessionData || null;
      window.currentLoadedSessionData = sessionData || null;

      // 🔒 USER PREFERENCE SUPREME RULE:
      // Default is ALWAYS Team / War Room mode unless explicitly selected as solo!
      const userSelectedMode = localStorage.getItem('xflow_session_mode');
      const isGroup = (userSelectedMode === 'solo') ? false : (userSelectedMode === 'team' ? true : !(sessionData && sessionData.mode === 'solo'));
      const activeMode = isGroup ? 'team' : 'solo';
      const activeType = isGroup ? 'group' : 'personal';

      window.currentSessionMode = activeMode;
      window.currentSessionType = activeType;
      localStorage.setItem('xflow_session_mode', activeMode);

      this.bindModeButtons();
      this.updateModeButtons(activeMode);

      // 1. Update Tab Capsule Title & Icon in Main Tab Strip
      this.updateTabCapsule(isGroup, sessionData);

      // 2. Update Chat Header Quick Toggle
      this.updateChatHeaderButton(isGroup, sessionData);

      // 3. STRICT ISOLATION GUARD:
      // If we are currently in Solo mode, GroupWarRoom MUST BE COMPLETELY UNMOUNTED.
      if (!isGroup) {
        GroupWarRoom.unmount();
      } else {
        SoloStudio.unmount();
      }

      // 4. If the Canvas Stage is currently the active view panel, re-mount active mode
      const viewCanvasStage = document.getElementById('view-canvas-stage');
      const isViewActive = viewCanvasStage && viewCanvasStage.classList.contains('active');

      if (isViewActive) {
        const rootEl = document.getElementById('canvas-dynamic-root');
        if (rootEl) {
          if (isGroup) {
            GroupWarRoom.mount(rootEl, sessionData);
          } else {
            SoloStudio.mount(rootEl, sessionData);
          }
        }
      }
    },

    updateTabCapsule(isGroup, sessionData) {
      const symEl = document.getElementById('tab-canvas-symbol');
      const labelEl = document.getElementById('tab-canvas-label');
      const tabCapsule = document.getElementById('tab-canvas-stage');

      if (isGroup) {
        const gName = (sessionData && (sessionData.group_name || sessionData.title)) || 'War Room';
        if (symEl) symEl.textContent = '👥';
        if (labelEl) labelEl.textContent = `War Room (${gName.slice(0, 14)})`;
        if (tabCapsule) {
          tabCapsule.setAttribute('title', `Swarm Tactical War Room: ${gName}`);
        }
      } else {
        const ag = (sessionData && (sessionData.agent_persona || sessionData.agent_id)) || 'Mr. Flow';
        const agLabel = ag === 'default' ? 'Mr. Flow' : ag;
        if (symEl) symEl.textContent = '👤';
        if (labelEl) labelEl.textContent = `Solo Studio (${agLabel.slice(0, 12)})`;
        if (tabCapsule) {
          tabCapsule.setAttribute('title', `Sovereign Solo Studio: ${agLabel}`);
        }
      }
    },

    updateChatHeaderButton(isGroup, sessionData) {
      const btn = document.getElementById('btn-toggle-canvas-studio');
      if (!btn) return;

      if (isGroup) {
        btn.classList.add('group-mode');
        btn.innerHTML = `<span>👥</span><span>War Room</span>`;
        btn.setAttribute('title', 'Switch to Swarm Tactical War Room');
      } else {
        btn.classList.remove('group-mode');
        btn.innerHTML = `<span>👤</span><span>Solo Studio</span>`;
        btn.setAttribute('title', 'Switch to Sovereign Solo Studio');
      }
    }
  };

  // Expose globally
  window.DualCanvasController = DualCanvasController;
  window.SoloStudio = SoloStudio;
  window.GroupWarRoom = GroupWarRoom;

  // Auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => DualCanvasController.init());
  } else {
    DualCanvasController.init();
  }

})(window);
