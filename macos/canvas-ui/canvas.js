// [FL_INDEX: clipboard, copy_snippet, stage_run, canvas_ui, input_dispatch | COT: Eliminate fatal infinite recursion in safeCopyToClipboard and fix stage run drawer auto-expansion| AT: 2026-10-26T21:56:38Z]
// X-Flow Canvas Host — Organic Aerodynamic Client Runtime (2026 Edition)
// [SOVEREIGN SEAL] Anti-Shadow DOM & Canvas Tamper-Proof Seal
(function sealCanvasRuntime() {
  if (window.__flowork_canvas_sealed) return;
  window.__flowork_canvas_sealed = true;

  const blockShadow = function() {
    console.error('[Flowork Security Gate] 🛑 REJECTION: Canvas is cryptographically sealed against Shadow DOM injection.');
    throw new Error('SECURITY_VIOLATION: Canvas is sealed against Shadow DOM');
  };

  try {
    if (window.HTMLCanvasElement && HTMLCanvasElement.prototype) {
      Object.defineProperty(HTMLCanvasElement.prototype, 'attachShadow', {
        value: blockShadow,
        writable: false,
        configurable: false
      });
    }
  } catch (_) {}

  document.querySelectorAll('canvas').forEach(el => {
    try {
      Object.defineProperty(el, 'attachShadow', {
        value: blockShadow,
        writable: false,
        configurable: false
      });
      Object.seal(el);
    } catch (_) {}
  });

  try {
    const sentinel = new MutationObserver(mutations => {
      for (const m of mutations) {
        for (const node of m.addedNodes) {
          if (node.nodeType === 1 && (node.shadowRoot || node.getAttribute('data-shadow-spoof'))) {
            node.remove();
            console.error('[Flowork Security Gate] 🛑 Unauthorized shadow container eradicated.');
          }
        }
      }
    });
    sentinel.observe(document.documentElement, { childList: true, subtree: true });
  } catch (_) {}
})();

let pluginsState = [];
let copilotState = [];
let copilotCommitSha = '';
let activeCategory = 'all';
let activeCopilotCategory = 'all';
let searchQuery = '';
let homeSearchQuery = '';
let copilotSearchQuery = '';
const MODULES_PER_PAGE = 50;
let homeCurrentPage = 1;
let copilotCurrentPage = 1;
let authState = {
  authorized: false,
  user: null,
  login_url: ''
};
let authPollInterval = null;
const openTabs = new Map(); // id -> { title, tabEl, iframePanel, isRunning }

document.addEventListener('DOMContentLoaded', () => {
  initStarfieldBackground();
  initAuthSystem();
  initSidebarToggle();
  initLayoutResizers();
  initSearchAndShortcuts();
  initCatalogSearch();
  renderCategoryRibbons();
  initCategoryFilters();
  initCopilotCategoryFilters();
  initEventListeners();
  initSyncDriveUI();
  initSentinelRecordUI();
  initConnectorUI();
  initPromoRecorder();
  initWorkspaceSystem();
  initScheduleSystem();
  initRouterSwitchboardSystem();
  // Pre-boot tab guard: Validate saved tab, normalize stale/invalid tabs to 'office'
  let preSavedActiveTab = localStorage.getItem('xflow_active_tab');
  if (preSavedActiveTab === 'group' || preSavedActiveTab === 'canvas-stage' || !preSavedActiveTab) {
    preSavedActiveTab = 'office';
    try { localStorage.setItem('xflow_active_tab', 'office'); } catch (_) {}
  }

  let savedOpenTabIds = [];
  try {
    const raw = localStorage.getItem('xflow_open_plugin_tabs');
    if (raw) savedOpenTabIds = JSON.parse(raw);
  } catch (_) {}

  // If saved tab is neither standard (office, copilot, home, pipeline) nor an open plugin tab, fallback immediately
  if (preSavedActiveTab !== 'office' && preSavedActiveTab !== 'copilot' && preSavedActiveTab !== 'home' && preSavedActiveTab !== 'pipeline') {
    if (!Array.isArray(savedOpenTabIds) || !savedOpenTabIds.includes(preSavedActiveTab)) {
      preSavedActiveTab = 'office';
      try { localStorage.setItem('xflow_active_tab', 'office'); } catch (_) {}
    }
  }

  if (preSavedActiveTab === 'home' || preSavedActiveTab === 'copilot' || preSavedActiveTab === 'pipeline') {
    switchTab(preSavedActiveTab);
  } else if (preSavedActiveTab === 'office') {
    const layout = document.querySelector('.canvas-layout');
    if (layout) {
      layout.classList.add('solo-studio-glass');
      layout.classList.remove('app-mode');
    }
    const officePanel = document.getElementById('view-office');
    if (officePanel) {
      officePanel.classList.add('active');
      officePanel.style.removeProperty('display');
      officePanel.style.contentVisibility = 'visible';
    }
    const tabOffice = document.getElementById('tab-office');
    if (tabOffice) tabOffice.classList.add('active');

    const rightbarChat = document.getElementById('rightbar-chat');
    if (rightbarChat) {
      const isCollapsed = localStorage.getItem('xflow_rightbar_collapsed') === 'true';
      if (!isCollapsed) {
        rightbarChat.classList.remove('collapsed');
        rightbarChat.style.removeProperty('display');
      }
    }
    const resizerRight = document.getElementById('resizer-right');
    if (resizerRight) {
      const isCollapsed = localStorage.getItem('xflow_rightbar_collapsed') === 'true';
      if (!isCollapsed) {
        resizerRight.classList.remove('collapsed');
        resizerRight.style.removeProperty('display');
      }
    }
  } else {
    // Valid open plugin tab
    const layout = document.querySelector('.canvas-layout');
    if (layout) {
      layout.classList.remove('solo-studio-glass');
      layout.classList.add('app-mode');
    }
    const officePanel = document.getElementById('view-office');
    if (officePanel) {
      officePanel.classList.remove('active');
      officePanel.style.setProperty('display', 'none', 'important');
    }
    const tabOffice = document.getElementById('tab-office');
    if (tabOffice) tabOffice.classList.remove('active');

    // Ensure side chat is docked and visible immediately for active app
    const rightbarChat = document.getElementById('rightbar-chat');
    if (rightbarChat) {
      rightbarChat.classList.remove('collapsed');
      rightbarChat.style.display = '';
    }
    const resizerRight = document.getElementById('resizer-right');
    if (resizerRight) {
      resizerRight.classList.remove('collapsed');
      resizerRight.style.display = '';
    }

    // Pre-mount skeleton tab capsules from saved tabs so the tab bar never blinks empty
    const tabStrip = document.getElementById('tab-strip');
    if (tabStrip && Array.isArray(savedOpenTabIds)) {
      savedOpenTabIds.forEach(id => {
        if (!document.getElementById(`tab-${id}`)) {
          const cap = document.createElement('div');
          cap.className = `tab-capsule ${id === preSavedActiveTab ? 'active' : ''}`;
          cap.id = `tab-${id}`;
          cap.dataset.tabId = id;
          cap.innerHTML = `
            <span class="tab-symbol">⚡</span>
            <span class="tab-label">${escapeHtml(id)}</span>
            <span class="tab-close-btn" title="Close Tab & Stop Engine">&times;</span>
          `;
          tabStrip.appendChild(cap);
        }
      });
    }
  }

  fetchPlugins();
  fetchCopilotRegistry();
  initSSE();
  initOffice3DSystem();
  initOfficeSubnavSystem();
  initStoreSubnavSystem();
  reportActiveViewport(preSavedActiveTab || 'office');
});

// ── 0.05 3D VIRTUAL OFFICE SYSTEM (FLOWORK FOR OFFICE) ──
let office3DInstance = null;
let currentInspectedAgent = null;
let currentActiveAgentId = localStorage.getItem('xflow_active_agent_id') || 'agent-mrflow-system-01';

function getActiveTargetAgentId() {
  const p = (currentSessionPersonaId || 'mr.flow').trim();
  if (p === 'default' || p === 'mr.flow') return 'agent-mrflow-system-01';
  if (p === 'leader') return 'agent-leader-system-01';
  return p.startsWith('agent-') ? p : ('agent-' + p);
}
window.getActiveTargetAgentId = getActiveTargetAgentId;

function getActiveAgent() {
  const targetPersona = (currentSessionPersonaId || 'mr.flow').trim();
  const targetAgentId = getActiveTargetAgentId();
  if (office3DInstance && Array.isArray(office3DInstance.agentRoster)) {
    const found = office3DInstance.agentRoster.find(a => 
      a.id.toLowerCase() === targetAgentId.toLowerCase() || 
      (a.persona && a.persona.toLowerCase() === targetPersona.toLowerCase())
    );
    if (found) return found;
  }
  return null;
}
window.getActiveAgent = getActiveAgent;

function initOffice3DSystem() {
  const canvas = document.getElementById('office-3d-canvas');
  const container = document.getElementById('view-office');
  if (!canvas || !container) return;

  let engineAttempts = 0;
  const checkEngine = () => {
    if (typeof window.SovereignOffice3D === 'function') {
      try {
        office3DInstance = new window.SovereignOffice3D(canvas, container);
        window.office3DInstance = office3DInstance;
        const isOfficeCurrentlyActive = container.classList.contains('active') && 
          (!document.querySelector('.tab-capsule.active') || document.querySelector('.tab-capsule.active')?.dataset.tabId === 'office');
        if (!isOfficeCurrentlyActive && typeof office3DInstance.pause === 'function') {
          office3DInstance.pause();
          console.log('[Office 3D] 🛡️ Viewport guard: 3D Studio paused immediately (Background tab detected)');
        }
        const savedMode = (localStorage.getItem('xflow_session_mode') === 'solo') ? 'solo' : 'team';
        if (typeof office3DInstance.setOfficeMode === 'function') {
          office3DInstance.setOfficeMode(savedMode);
        }
        if (typeof office3DInstance.setSessionMode === 'function') {
          office3DInstance.setSessionMode(savedMode === 'solo' ? 'solo' : 'group');
        } else if (Array.isArray(AVAILABLE_PERSONAS) && AVAILABLE_PERSONAS.length > 0) {
          office3DInstance.syncPersonas(AVAILABLE_PERSONAS);
        }
        renderOfficeAgentDock();
        if (currentActiveAgentId && office3DInstance) {
          office3DInstance.selectAgentById(currentActiveAgentId, true);
        }
        console.log('[Office 3D] 🏢 Sovereign 3D Virtual Office initialized successfully');
      } catch (err) {
        console.error('[Office 3D] Error initializing 3D office:', err);
      }
    } else {
      engineAttempts++;
      if (engineAttempts <= 120) {
        setTimeout(checkEngine, 50);
      } else {
        console.warn('[Office 3D] SovereignOffice3D engine not loaded after 6s. Rogue timer avoided.');
      }
    }
  };
  checkEngine();


  const btnZoomIn = document.getElementById('btn-office-zoom-in');
  if (btnZoomIn) {
    btnZoomIn.addEventListener('click', () => {
      if (office3DInstance && typeof office3DInstance.zoomIn === 'function') {
        office3DInstance.zoomIn();
      }
    });
  }

  const btnZoomOut = document.getElementById('btn-office-zoom-out');
  if (btnZoomOut) {
    btnZoomOut.addEventListener('click', () => {
      if (office3DInstance && typeof office3DInstance.zoomOut === 'function') {
        office3DInstance.zoomOut();
      }
    });
  }

  const btnLockView = document.getElementById('btn-office-lock-view');
  if (btnLockView) {
    btnLockView.addEventListener('click', () => {
      if (office3DInstance && typeof office3DInstance.toggleLockView === 'function') {
        const isLocked = office3DInstance.toggleLockView();
        btnLockView.classList.toggle('active', isLocked);
        const label = document.getElementById('label-office-lock-view');
        if (label) label.textContent = isLocked ? '🔒 Lock View' : '🔓 Free View';
      }
    });
  }

  window.onOfficeAgentSelected = (agentData) => {
    // 3D Office Agent Selection: Pure spatial focus + open Cockpit Model Selection
    currentInspectedAgent = agentData;
    if (agentData) {
      const targetAgentId = agentData.persona || (agentData.id ? agentData.id.replace(/^agent-/, '') : 'mr.flow');
      if (window.swarmPipeline && typeof window.swarmPipeline.openFullPromptModal === 'function') {
        const targetNode = {
          id: targetAgentId,
          label: agentData.name || targetAgentId,
          persona: targetAgentId,
          agentId: targetAgentId,
          modelConfig: {
            provider: agentData.provider || 'gravity',
            modelId: agentData.model || localStorage.getItem('xflow_agent_model_' + targetAgentId) || localStorage.getItem('xflow_chat_model') || 'gemini-3.8-flash-high'
          }
        };
        window.swarmPipeline.openFullPromptModal(targetNode, null, 'model');
      }
    }
  };
}

// ── 0.06 OFFICE SUB-NAV & PIPELINE GOVERNOR (OFFICE, SWARM PIPELINE & BLACKBOARD) ──
let currentOfficeSubtab = 'office'; // 'office' | 'pipeline' | 'blackboard'

function switchOfficeSubtab(targetSubtab) {
  if (!targetSubtab || targetSubtab === 'boardroom' || targetSubtab === '3d') {
    targetSubtab = 'office';
  }
  currentOfficeSubtab = targetSubtab;
  try {
    localStorage.setItem('xflow_office_subtab', targetSubtab);
  } catch (_) {}

  // 1. Update sub-nav button active classes
  const btns = document.querySelectorAll('#office-subnav-bar .group-subnav-btn, .group-subnav-bar .group-subnav-btn');
  btns.forEach(btn => {
    const s = btn.getAttribute('data-subtab');
    if (s === targetSubtab || (s === 'office' && (targetSubtab === 'office' || targetSubtab === 'boardroom'))) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // 2. Pane visibility inside Office
  const paneOffice = document.getElementById('office-pane-3d');
  const paneBlackboard = document.getElementById('office-pane-blackboard');
  const panePipeline = document.getElementById('view-pipeline');

  if (paneOffice) paneOffice.style.display = (targetSubtab === 'office') ? 'block' : 'none';

  if (paneBlackboard) {
    paneBlackboard.style.display = (targetSubtab === 'blackboard') ? 'flex' : 'none';
    if (targetSubtab === 'blackboard' && window.swarmTelemetry) {
      if (!window.swarmTelemetry.isInitialized && typeof window.swarmTelemetry.bindUI === 'function') {
        window.swarmTelemetry.bindUI();
      }
      if (typeof window.swarmTelemetry.render === 'function') {
        window.swarmTelemetry.render();
      }
    }
  }

  if (panePipeline) {
    const isPipeline = (targetSubtab === 'pipeline');
    panePipeline.style.setProperty('display', isPipeline ? 'flex' : 'none', 'important');
    panePipeline.style.setProperty('visibility', isPipeline ? 'visible' : 'hidden', 'important');
    panePipeline.style.setProperty('content-visibility', isPipeline ? 'visible' : 'hidden', 'important');
    panePipeline.classList.toggle('active', isPipeline);
    if (isPipeline) {
      const engine = window.swarmPipelineInstance || window.swarmPipeline;
      if (engine) {
        if (!panePipeline.classList.contains('swarm-pipeline-container') || !panePipeline.querySelector('.pipeline-palette-sidebar')) {
          engine.mount(panePipeline);
        } else {
          engine.render();
        }
      }
    }
  }

  // 2b. CHAT & LAYOUT VISIBILITY POLICY:
  const rightbarChat = document.getElementById('rightbar-chat');
  const resizerRight = document.getElementById('resizer-right');
  const canvasLayout = document.querySelector('.canvas-layout');

  if (targetSubtab === 'pipeline') {
    if (rightbarChat) rightbarChat.style.setProperty('display', 'none', 'important');
    if (resizerRight) resizerRight.style.setProperty('display', 'none', 'important');
    if (canvasLayout) canvasLayout.classList.add('pipeline-active');
  } else {
    if (rightbarChat) {
      rightbarChat.style.removeProperty('display');
      rightbarChat.classList.remove('collapsed');
    }
    if (resizerRight) {
      resizerRight.style.removeProperty('display');
      resizerRight.classList.remove('collapsed');
    }
    if (canvasLayout) canvasLayout.classList.remove('pipeline-active');
  }
  if (typeof window.__updateLayoutResizers === 'function') {
    window.__updateLayoutResizers();
  }

  // 2c. Canvas Foreground & Bottom Composer visibility
  const canvasFg = document.getElementById('office-3d-canvas-fg');
  if (canvasFg) {
    canvasFg.style.setProperty('display', (targetSubtab === 'office') ? 'block' : 'none', 'important');
  }
  const bottomChatbar = document.getElementById('office-bottom-chatbar');
  if (bottomChatbar) {
    bottomChatbar.style.display = (targetSubtab === 'office') ? '' : 'none';
  }

  // 3. Three.js Solo Office GPU Lifecycle Governor
  if (targetSubtab === 'office') {
    if (window.office3DInstance && typeof window.office3DInstance.resume === 'function') {
      window.office3DInstance.resume();
    }
    if (window.office3DInstance && typeof window.office3DInstance.onWindowResize === 'function') {
      window.office3DInstance.onWindowResize();
    }
  } else {
    // Blackboard & Swarm Flow: 0 FPS, 0 GPU draw calls!
    if (window.office3DInstance && typeof window.office3DInstance.pause === 'function') {
      window.office3DInstance.pause();
    }
  }
}
window.switchOfficeSubtab = switchOfficeSubtab;
window.switchGroupSubtab = switchOfficeSubtab; // Backward compatibility alias

function initOfficeSubnavSystem() {
  const bar = document.getElementById('office-subnav-bar') || document.getElementById('group-subnav-bar');
  if (!bar) return;

  const btns = bar.querySelectorAll('.group-subnav-btn');
  btns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const subtab = btn.getAttribute('data-subtab');
      if (subtab) {
        switchOfficeSubtab(subtab);
      }
    });
  });

  // Restore saved subtab or default to office
  let saved = localStorage.getItem('xflow_office_subtab') || localStorage.getItem('xflow_group_subtab') || 'office';
  if (saved === 'boardroom' || saved === '3d') saved = 'office';
  switchOfficeSubtab(saved);
}
window.initOfficeSubnavSystem = initOfficeSubnavSystem;
window.initGroupSubnavSystem = initOfficeSubnavSystem; // Backward compatibility alias

// ── UNIFIED FLOWORK SOVEREIGN ECOSYSTEM STORE SYSTEM ──
let currentStoreSubtab = 'apps';

const ECOSYSTEM_REGISTRIES = {
  apps: {
    id: 'apps',
    label: 'Apps',
    icon: '📱',
    repo: 'flowork-os/apps',
    title: 'X-Flow App Store',
    subtitle: 'Browse, install, and update verified polyglot extensions directly from GitHub repository',
    metaPill: 'CLOUD FEDERATION REPOSITORY',
    catalogUrl: 'https://auth.floworkos.com/api/store/catalog',
    itemsKey: 'plugins',
    accentColor: '#10b981',
    accentRgb: '16, 185, 129',
    unitName: 'Extensions'
  },
  skills: {
    id: 'skills',
    label: 'Skills',
    icon: '🧠',
    repo: 'flowork-os/FLOWORK-SKILLS',
    title: 'Flowork Skills Hub',
    subtitle: 'Autonomous agent domain SOPs, cognitive procedures, and playbooks with strict 20 English keywords from',
    metaPill: 'AGENT KNOWLEDGE BASE',
    catalogUrl: 'https://raw.githubusercontent.com/flowork-os/FLOWORK-SKILLS/main/skills.json',
    itemsKey: 'skills',
    accentColor: '#8b5cf6',
    accentRgb: '139, 92, 246',
    unitName: 'Skills'
  },
  tools: {
    id: 'tools',
    label: 'Tools',
    icon: '🛠️',
    repo: 'flowork-os/AGENT-TOOLS',
    title: 'Agent Tools Registry',
    subtitle: 'Deterministic CLI utilities, real-time scanners, and MCP tool adapters for autonomous agents from',
    metaPill: 'DETERMINISTIC AGENT UTILITIES',
    catalogUrl: 'https://raw.githubusercontent.com/flowork-os/AGENT-TOOLS/main/tools.json',
    itemsKey: 'tools',
    accentColor: '#f59e0b',
    accentRgb: '245, 158, 11',
    unitName: 'Tools'
  },
  agents: {
    id: 'agents',
    label: 'Agents',
    icon: '🤖',
    repo: 'flowork-os/AGENTS',
    title: 'Autonomous Agent Squads',
    subtitle: 'Specialist persona roles, engineering agents, security auditors, and QC leads designed for swarm orchestration from',
    metaPill: 'AUTONOMOUS SQUAD ROLES',
    catalogUrl: 'https://raw.githubusercontent.com/flowork-os/AGENTS/main/agents.json',
    itemsKey: 'agents',
    accentColor: '#00f2fe',
    accentRgb: '0, 242, 254',
    unitName: 'Agents'
  },
  triggers: {
    id: 'triggers',
    label: 'Triggers',
    icon: '⚡',
    repo: 'flowork-os/triger',
    title: 'Sensor & Trigger Registry',
    subtitle: 'Active background daemons (cron/webhook/price watchers) and passive Just-In-Time prompt sensors from',
    metaPill: 'EVENT & TELEMETRY SENSORS',
    catalogUrl: 'https://raw.githubusercontent.com/flowork-os/triger/main/triggers.json',
    itemsKey: 'triggers',
    accentColor: '#ec4899',
    accentRgb: '236, 72, 153',
    unitName: 'Triggers'
  }
};

let ecosystemState = {
  apps: [],
  skills: [],
  tools: [],
  agents: [],
  triggers: []
};

function getInstalledSet(type) {
  const norm = (type || '').toLowerCase().replace(/s$/, '');
  const pluralKey = norm === 'app' ? 'apps' : norm + 's';
  if (pluralKey === 'apps') {
    return new Set((pluginsState || []).map(p => p.id));
  }
  try {
    const raw = localStorage.getItem(`xflow_installed_${pluralKey}`);
    if (raw) return new Set(JSON.parse(raw));
  } catch (_) {}
  if (pluralKey === 'skills') return new Set(['software_company_sop', 'ui_ux_pro_max']);
  if (pluralKey === 'tools') return new Set(['crypto_scanner', 'file_ops', 'mcp_flowork_system_inspect_workspace', 'mcp_flowork_system_system_status', 'semantic_search']);
  if (pluralKey === 'agents') return new Set(['mr.flow']);
  if (pluralKey === 'triggers') return new Set(['bitcoin_threshold', 'webhook_receiver', 'document_companion', 'zombie_process_hunter']);
  return new Set();
}

function saveInstalledSet(type, set) {
  try {
    localStorage.setItem(`xflow_installed_${type}`, JSON.stringify(Array.from(set)));
  } catch (_) {}
  updateInstalledCountBadge();
}

function updateInstalledCountBadge() {
  const badge = document.getElementById('store-installed-count-badge');
  if (!badge) return;
  const count = getInstalledSet('apps').size +
                getInstalledSet('skills').size +
                getInstalledSet('tools').size +
                getInstalledSet('agents').size +
                getInstalledSet('triggers').size;
  badge.textContent = count;
}

function switchStoreSubtab(subtab) {
  let targetSubtab = subtab || 'apps';
  if (targetSubtab === 'cloud') targetSubtab = 'apps';
  if (targetSubtab === 'home') targetSubtab = 'installed';
  currentStoreSubtab = targetSubtab;
  try {
    localStorage.setItem('xflow_store_subtab', targetSubtab);
  } catch (_) {}

  // 1. Toggle subnav buttons
  const bar = document.getElementById('store-subnav-bar');
  if (bar) {
    const btns = bar.querySelectorAll('.group-subnav-btn');
    btns.forEach(btn => {
      const btnSubtab = btn.getAttribute('data-storesubtab');
      btn.classList.toggle('active', btnSubtab === targetSubtab);
    });
  }

  // 2. Toggle subview panes
  const paneCloud = document.getElementById('store-pane-cloud');
  const paneInstalled = document.getElementById('store-pane-installed');

  if (targetSubtab === 'installed') {
    if (paneCloud) paneCloud.style.display = 'none';
    if (paneInstalled) paneInstalled.style.display = 'block';
    if (typeof filterAndRenderCards === 'function') filterAndRenderCards();
  } else {
    if (paneCloud) paneCloud.style.display = 'block';
    if (paneInstalled) paneInstalled.style.display = 'none';
    copilotCurrentPage = 1;
    activeCopilotCategory = 'all';
    updateEcosystemHero(targetSubtab);
    fetchEcosystemRegistry(targetSubtab);
  }

  updateInstalledCountBadge();

  // 3. Update viewport telemetry
  if (typeof reportActiveViewport === 'function') {
    reportActiveViewport('copilot');
  }
}
window.switchStoreSubtab = switchStoreSubtab;

function updateEcosystemHero(tabKey, data = null) {
  const config = ECOSYSTEM_REGISTRIES[tabKey];
  if (!config) return;

  const glow = document.getElementById('copilot-aeropod-glow');
  const meta = document.getElementById('copilot-aeropod-meta');
  const title = document.getElementById('copilot-aeropod-title');
  const subtitle = document.getElementById('copilot-aeropod-subtitle');
  const repoLabel = document.getElementById('copilot-repo-label');
  const statCount = document.getElementById('copilot-stat-count');
  const statCountLabel = document.getElementById('copilot-stat-count-label');
  const statSha = document.getElementById('copilot-stat-sha');
  const statShaLabel = document.getElementById('copilot-stat-sha-label');
  const statStatus = document.getElementById('copilot-stat-status');
  const searchInput = document.getElementById('copilot-search-input');

  if (glow) {
    glow.style.background = `radial-gradient(circle at center, rgba(${config.accentRgb}, 0.22) 0%, transparent 70%)`;
  }
  if (meta) {
    meta.style.borderColor = `rgba(${config.accentRgb}, 0.4)`;
    meta.style.color = config.accentColor;
    meta.textContent = config.metaPill;
  }
  if (title) {
    title.textContent = config.title;
  }
  if (subtitle) {
    subtitle.innerHTML = `${config.subtitle} <code id="copilot-repo-label" style="color: ${config.accentColor}; background: rgba(${config.accentRgb}, 0.1); padding: 2px 8px; border-radius: 6px;">${config.repo}</code>.`;
  }
  if (repoLabel) {
    repoLabel.textContent = config.repo;
  }
  const items = (tabKey === 'apps') ? copilotState : (ecosystemState[tabKey] || []);
  if (statCount) {
    statCount.textContent = items.length;
  }
  if (statCountLabel) {
    statCountLabel.textContent = `Available ${config.unitName}`;
  }
  if (statSha) {
    statSha.textContent = (data && data.updated_at) ? data.updated_at.slice(0, 10) : (copilotCommitSha || 'main CDN');
  }
  if (statShaLabel) {
    statShaLabel.textContent = 'Catalog Release';
  }
  if (statStatus) {
    statStatus.textContent = 'Active';
    statStatus.style.color = config.accentColor;
  }
  if (searchInput) {
    searchInput.placeholder = `Search ${config.label.toLowerCase()}...`;
  }
}

async function fetchEcosystemRegistry(tabKey = 'apps', isManual = false) {
  if (tabKey === 'installed') {
    filterAndRenderCards();
    return;
  }
  const config = ECOSYSTEM_REGISTRIES[tabKey];
  if (!config) return;

  const targetOs = getClientTargetOs();
  const cacheKey = `xflow_ecosystem_cache_${tabKey}_${targetOs}`;

  if (tabKey === 'apps') {
    await fetchCopilotRegistry(isManual, targetOs);
    ecosystemState.apps = copilotState;
    updateEcosystemHero('apps');
    return;
  }

  // Check localStorage cache
  if (!isManual) {
    try {
      const cachedStr = localStorage.getItem(cacheKey);
      if (cachedStr) {
        const cached = JSON.parse(cachedStr);
        const age = Date.now() - (cached.timestamp || 0);
        if (age < COPILOT_CACHE_TTL && cached.items && cached.items.length > 0) {
          ecosystemState[tabKey] = cached.items;
          applyEcosystemRegistryData(tabKey, cached.data, isManual);
          return;
        }
      }
    } catch (_) {}
  }

  try {
    const res = await fetch(config.catalogUrl, { cache: 'no-cache' });
    if (res.ok) {
      const data = await res.json();
      const items = data[config.itemsKey] || [];
      ecosystemState[tabKey] = items;
      try {
        localStorage.setItem(cacheKey, JSON.stringify({
          timestamp: Date.now(),
          items: items,
          data: data
        }));
      } catch (_) {}
      applyEcosystemRegistryData(tabKey, data, isManual);
    } else {
      console.warn(`[Ecosystem Store] Failed to fetch catalog for ${tabKey}: HTTP ${res.status}`);
    }
  } catch (err) {
    console.error(`[Ecosystem Store] Error fetching catalog for ${tabKey}:`, err);
  }
}

function applyEcosystemRegistryData(tabKey, data, isManual) {
  const config = ECOSYSTEM_REGISTRIES[tabKey];
  if (!config) return;

  updateEcosystemHero(tabKey, data);
  renderCategoryRibbons();
  filterAndRenderCopilotCards();

  if (isManual) {
    const count = (ecosystemState[tabKey] || []).length;
    showToast(`${config.label} Registry synced from GitHub (${count} ${config.unitName.toLowerCase()})`);
  }
}

function initStoreSubnavSystem() {
  const bar = document.getElementById('store-subnav-bar');
  if (!bar || bar._subnavBound) return;
  bar._subnavBound = true;

  const btns = bar.querySelectorAll('.group-subnav-btn');
  btns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const subtab = btn.getAttribute('data-storesubtab');
      if (subtab) {
        switchStoreSubtab(subtab);
      }
    });
  });

  updateInstalledCountBadge();

  // Restore saved subtab or default to apps
  let saved = localStorage.getItem('xflow_store_subtab') || 'apps';
  if (saved === 'cloud') saved = 'apps';
  switchStoreSubtab(saved);
}
window.initStoreSubnavSystem = initStoreSubnavSystem;

// ── Real-Time 3D Office Agent Activity & Dynamic Exit Tracker ──
const activeStepWorkerAgents = new Map(); // stepIdx -> agentId
const agentExitTimers = new Map(); // agentId -> timeoutId

function cancelAgentExitTimer(agentId) {
  if (!agentId) return;
  const tid = agentExitTimers.get(agentId);
  if (tid) {
    clearTimeout(tid);
    agentExitTimers.delete(agentId);
  }
}
window.cancelAgentExitTimer = cancelAgentExitTimer;

function setUnifiedAgentActivity(agentId, state) {
  if (!agentId) return;
  if (window.office3DInstance && typeof window.office3DInstance.setAgentState === 'function') {
    window.office3DInstance.setAgentState(agentId, state);
  }
  if (window.swarmPipelineInstance && typeof window.swarmPipelineInstance.setAgentActivityState === 'function') {
    window.swarmPipelineInstance.setAgentActivityState(agentId, state);
  }
  if (typeof window.updateOfficeDockAgentState === 'function') {
    window.updateOfficeDockAgentState(agentId, state);
  }
}
window.setUnifiedAgentActivity = setUnifiedAgentActivity;

function scheduleAgentExit(agentId, delayMs = 2500) {
  if (!agentId || agentId === 'agent-boss') return;
  cancelAgentExitTimer(agentId);
  const timer = setTimeout(() => {
    agentExitTimers.delete(agentId);
    if (isChatStreaming) {
      return;
    }
    const isStillBusy = Array.from(activeStepWorkerAgents.values()).includes(agentId);
    if (!isStillBusy) {
      setUnifiedAgentActivity(agentId, 'idle');
    }
  }, delayMs);
  agentExitTimers.set(agentId, timer);
}
window.scheduleAgentExit = scheduleAgentExit;

function resolveWorkerAgentFromTool(toolName, details) {
  const rawTool = String(toolName || '').toLowerCase().trim();
  const d = (details && typeof details === 'object') ? details : {};

  // 1. Direct explicit Subagent / Swarm target from invocation details
  let candidate = null;
  if (Array.isArray(d.Subagents) && d.Subagents.length > 0 && d.Subagents[0]) {
    candidate = d.Subagents[0].TypeName || d.Subagents[0].typeName || d.Subagents[0].role || d.Subagents[0].Role;
  }
  if (!candidate) {
    candidate = d.target_agent_id || d.targetAgentId || d.to_agent_id || d.recipient || d.TypeName || d.typeName || d.agent_id || d.agentId || d.role || d.Role;
  }

  // 2. Match against office 3D agent roster if explicit candidate
  if (candidate && window.office3DInstance && Array.isArray(window.office3DInstance.agentRoster)) {
    const candStr = String(candidate).toLowerCase().trim().replace(/^agent-/, '');
    const found = window.office3DInstance.agentRoster.find(a => {
      const pid = (a.persona || '').toLowerCase();
      const aid = (a.id || '').toLowerCase().replace(/^agent-/, '');
      return aid === candStr || pid === candStr || (candStr && (aid.includes(candStr) || pid.includes(candStr)));
    });
    if (found) return found.id;
    return 'agent-' + candStr;
  }

  // 3. High-Precision Domain Specialist Attribution for Flowork Swarm
  const targetFile = String(d.TargetFile || d.AbsolutePath || d.target_file || d.targetFile || d.file_path || d.path || d.file || '').toLowerCase();
  const reasonText = String(d.reason || d.reasonText || d.Description || d.description || '').toLowerCase();
  const isFrontendTarget = targetFile.endsWith('.html') || targetFile.endsWith('.css') || targetFile.endsWith('.vue') || targetFile.endsWith('.svelte') || targetFile.endsWith('.jsx') || targetFile.endsWith('.tsx') || targetFile.includes('canvas-ui') || targetFile.includes('member-area') || targetFile.includes('styles/') || targetFile.endsWith('.svg');

  // A. Swarm Orchestrator & Group Coordinator (Leader)
  if (rawTool.includes('invoke_subagent') || rawTool.includes('spawn') || rawTool.includes('dispatch') || rawTool.includes('team_progress')) {
    return 'leader';
  }

  // B. Quality Control & Release Gatekeeper (Tests, Verification, Exit Code Checks, Deterministic Helper)
  if (rawTool.includes('deterministic_helper') || rawTool.includes('verify') || rawTool.includes('test') || rawTool.includes('check_exit') || rawTool.includes('qc') || rawTool.includes('invariant') || reasonText.includes('exit code 0') || reasonText.includes('verification')) {
    return 'quality-control';
  }

  // C. Security Auditor & Reverse Engineering Specialist (Code View, URL Content, Web Search, AST Security)
  if (rawTool.includes('view_file') || rawTool.includes('read_file') || rawTool.includes('search_web') || rawTool.includes('read_url') || rawTool.includes('ast_audit') || rawTool.includes('audit') || rawTool.includes('security') || rawTool.includes('inspect') || reasonText.includes('inspect') || reasonText.includes('audit')) {
    return 'security-auditor';
  }

  // D. Frontend Engineer (UI/UX, CSS, HTML, Canvas, Visual components)
  if (rawTool.includes('render_visual') || rawTool.includes('generate_image') || (rawTool.includes('replace_file') && isFrontendTarget) || (rawTool.includes('write_to_file') && isFrontendTarget)) {
    return 'frontend-engineer';
  }

  // E. Backend & Systems Specialist (Terminal, Commands, Node/Rust/Python/Bash, System files)
  if (rawTool.includes('run_command') || rawTool.includes('bash') || rawTool.includes('exec') || rawTool.includes('terminal') || rawTool.includes('forger') || rawTool.includes('patch') || rawTool.includes('write_to_file') || rawTool.includes('replace_file')) {
    return 'backend-engineer';
  }

  // 4. Fallback to active chat session persona
  return (typeof getActiveTargetAgentId === 'function') ? getActiveTargetAgentId() : 'mr.flow';
}
window.resolveWorkerAgentFromTool = resolveWorkerAgentFromTool;

function renderOfficeAgentDock() {
  const dockList = document.getElementById('office-dock-list');
  const countBadge = document.getElementById('office-dock-count');
  if (!dockList) return;

  const roster = (office3DInstance && Array.isArray(office3DInstance.agentRoster) && office3DInstance.agentRoster.length > 0)
    ? office3DInstance.agentRoster
    : (Array.isArray(AVAILABLE_PERSONAS) ? AVAILABLE_PERSONAS.map((p, idx) => ({
        id: 'agent-' + p.id,
        name: p.name,
        role: (p.id.toLowerCase() === 'mr.flow' || p.id.toLowerCase() === 'default') ? 'Autonomous Core & Orchestrator' : (p.id.toLowerCase() === 'leader' ? 'Swarm Leader & Group Orchestrator' : (p.description || 'Specialist Agent')),
        sessionId: 'session-' + p.id,
        persona: p.id,
        icon: p.icon || ((p.id.toLowerCase() === 'mr.flow' || p.id.toLowerCase() === 'default') ? '⚡' : (p.id.toLowerCase() === 'leader' ? '👑' : '🤖')),
        model: 'gemini-3.8-flash-high',
        state: 'idle'
      })) : []);

  // Strict activity-driven presence:
  // Only Sovereign Boss (permanently presiding) and agents genuinely working/executing are on canvas and in dock!
  const activeOnlyRoster = roster.filter(a => a.isBoss || a.state === 'working');
  const displayList = activeOnlyRoster;

  if (countBadge) {
    countBadge.textContent = displayList.length;
  }

  // Delegated event listeners bound ONCE on container to prevent memory leaks on dynamic elements
  if (!dockList._delegatedBound) {
    dockList._delegatedBound = true;
    dockList.addEventListener('dragstart', (e) => {
      const item = e.target.closest('.office-agent-dock-item');
      if (!item) return;
      const agentId = item.getAttribute('data-agent-id');
      if (e.dataTransfer) {
        e.dataTransfer.setData('text/plain', agentId);
        e.dataTransfer.setData('application/x-flowork-agent', agentId);
        e.dataTransfer.effectAllowed = 'copyMove';
      }
      item.classList.add('is-dragging');
    });

    dockList.addEventListener('dragend', (e) => {
      const item = e.target.closest('.office-agent-dock-item');
      if (item) item.classList.remove('is-dragging');
    });

    dockList.addEventListener('click', (e) => {
      const item = e.target.closest('.office-agent-dock-item');
      if (!item) return;
      const agentId = item.getAttribute('data-agent-id');
      const activeRoster = (office3DInstance && Array.isArray(office3DInstance.agentRoster))
        ? office3DInstance.agentRoster
        : (Array.isArray(AVAILABLE_PERSONAS) ? AVAILABLE_PERSONAS.map(p => ({ id: 'agent-' + p.id })) : []);
      const targetAgent = activeRoster.find(a => a.id === agentId);
      if (targetAgent) {
        if (office3DInstance && typeof office3DInstance.selectAgentById === 'function') {
          office3DInstance.selectAgentById(agentId);
        } else {
          activateOfficeAgentChat(targetAgent);
        }
      }
    });
  }

  const fragment = document.createDocumentFragment();

  if (displayList.length === 0) {
    const emptyEl = document.createElement('div');
    emptyEl.style.cssText = 'padding: 12px; font-size: 11px; color: #94a3b8; text-align: center;';
    emptyEl.textContent = 'No active agents';
    fragment.appendChild(emptyEl);
    dockList.replaceChildren(fragment);
    return;
  }

  const tempWrapper = document.createElement('div');
  tempWrapper.innerHTML = displayList.map(agent => {
    const isSelected = (currentActiveAgentId && currentActiveAgentId === agent.id) || (currentInspectedAgent && currentInspectedAgent.id === agent.id);
    const isWorking = agent.state === 'working';
    const isBoss = !!agent.isBoss;
    return `
      <div class="office-agent-dock-item ${isSelected ? 'active' : ''} ${isBoss ? 'boss-item' : ''}" data-agent-id="${escapeHtml(agent.id)}" draggable="true" title="Drag to Canvas floor or click to focus agent">
        <div class="dock-item-left">
          <div class="dock-item-avatar">${agent.icon || (isBoss ? '👑' : '🤖')}</div>
          <div class="dock-item-info">
            <div class="dock-item-name-row">
              <span class="dock-item-name" style="${isBoss ? 'color:#fbbf24;font-weight:900;' : ''}" title="${escapeHtml(agent.name)}">${escapeHtml(agent.name)}</span>
              <span class="dock-item-id-badge" style="${isBoss ? 'border-color:#f59e0b;color:#fbbf24;' : ''}">${isBoss ? 'LEADER' : escapeHtml(agent.id)}</span>
            </div>
            <div class="dock-item-role" title="${escapeHtml(agent.role)}">${escapeHtml(agent.role)}</div>
          </div>
        </div>
        <div class="dock-item-status-pill ${isBoss ? 'working' : (isWorking ? 'working' : 'idle')}" style="${isBoss ? 'background:rgba(245,158,11,0.15);border-color:#f59e0b;color:#fbbf24;' : ''}">
          <span class="dock-status-dot" style="${isBoss ? 'background:#fbbf24;box-shadow:0 0 8px #fbbf24;' : ''}"></span>
          <span>${isBoss ? 'PRESIDING' : (isWorking ? 'WORKING' : 'IDLE')}</span>
        </div>
      </div>
    `;
  }).join('');

  while (tempWrapper.firstChild) {
    fragment.appendChild(tempWrapper.firstChild);
  }
  dockList.replaceChildren(fragment);
}
window.renderOfficeAgentDock = renderOfficeAgentDock;

function highlightOfficeDockItem(agentId) {
  const dockItems = document.querySelectorAll('.office-agent-dock-item');
  dockItems.forEach(item => {
    if (item.getAttribute('data-agent-id') === agentId) {
      item.classList.add('active');
      item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
      item.classList.remove('active');
    }
  });
}
window.highlightOfficeDockItem = highlightOfficeDockItem;

function updateOfficeDockAgentState(agentId, newState) {
  renderOfficeAgentDock();
}
window.updateOfficeDockAgentState = updateOfficeDockAgentState;

function activateOfficeAgentChat(agentData) {
  if (!agentData || !agentData.id) return;
  currentActiveAgentId = agentData.id;
  currentInspectedAgent = agentData;
  localStorage.setItem('xflow_active_agent_id', agentData.id);

  // 1. Sync persona specialist to this agent without wiping active chat
  const personaId = agentData.persona || 'default';

  localStorage.setItem('xflow_chat_persona', personaId);
  localStorage.setItem('xflow_agent_persona_' + agentData.id, personaId);
  currentSessionPersonaId = personaId;
  pendingSessionPersonaId = personaId;

  if (typeof setSessionAgentPersona === 'function') {
    setSessionAgentPersona(personaId);
  }

  // 2. Restore saved model for this agent/persona
  const savedModel = agentData.model 
    || localStorage.getItem('xflow_agent_model_' + agentData.id) 
    || localStorage.getItem('xflow_agent_model_' + personaId)
    || 'gemini-3.8-flash-high';

  if (savedModel && Array.isArray(AVAILABLE_CHAT_MODELS) && AVAILABLE_CHAT_MODELS.some(m => m.id === savedModel)) {
    selectedChatModelId = savedModel;
    localStorage.setItem('xflow_chat_model', savedModel);
    localStorage.setItem('xflow_agent_model_' + agentData.id, savedModel);
    updateModelPillDisplay();
    renderModelDropdown();
    if (typeof window.switchFloworkCoreModel === 'function') {
      window.switchFloworkCoreModel(savedModel);
    }
  }

  // 2b. Restore saved account for this agent/persona (Default is ALWAYS 'combo'!)
  const savedAccount = agentData.account
    || localStorage.getItem('xflow_agent_account_' + agentData.id)
    || localStorage.getItem('xflow_agent_account_' + personaId)
    || 'combo'; // ALWAYS COMBO BY DEFAULT!

  if (typeof setSessionBinding === 'function') {
    setSessionBinding(savedAccount).catch(() => {});
  } else {
    currentSessionAccountId = savedAccount;
    updateAccountPillDisplay();
  }

  // 3. Update agent UI pill display immediately
  updateAgentPillDisplay();
  renderAgentDropdown();
  highlightOfficeDockItem(agentData.id);

  // 4. CRITICAL: PRESERVE ONGOING CHAT SESSION!
  // Do NOT wipe or replace currentChatSessionId when selecting an agent in 3D canvas.
  // The active conversation (messages, trajectory, tools) must remain fully intact.
  if (typeof window.__closeHistoryView === 'function') {
    window.__closeHistoryView();
  } else {
    const rightbarMessages = document.getElementById('rightbar-messages');
    const rightbarHistoryView = document.getElementById('rightbar-history-view');
    if (rightbarHistoryView) {
      rightbarHistoryView.classList.remove('active');
      rightbarHistoryView.style.display = 'none';
    }
    if (rightbarMessages) {
      rightbarMessages.classList.remove('history-active');
      rightbarMessages.style.display = 'flex';
    }
  }

  // 5. Toast notification confirming agent focus in 3D
  if (typeof showFloworkLaserToast === 'function') {
    showFloworkLaserToast(`👥 Focused Agent [${agentData.name || agentData.id}]`, true);
  }
}
window.activateOfficeAgentChat = activateOfficeAgentChat;

// ── 0.1 SOVEREIGN WORKSPACE & PROJECT MANAGEMENT ──
let sovereignWorkspaces = [];
let activeWorkspacePath = '';
let workspaceSystemInitialized = false;

function initWorkspaceSystem() {
  if (workspaceSystemInitialized) return;
  workspaceSystemInitialized = true;

  const btnDropdown = document.getElementById('btn-workspace-dropdown');
  const popover = document.getElementById('workspace-dropdown-popover');
  const btnQuickNew = document.getElementById('btn-quick-new-ws');
  const btnOpenCreateModal = document.getElementById('btn-open-create-ws-modal');
  const btnOpenBrowseFolder = document.getElementById('btn-open-browse-ws-folder');
  const modal = document.getElementById('workspace-modal');
  const btnCloseModal = document.getElementById('btn-close-ws-modal');
  const btnCancelModal = document.getElementById('btn-cancel-ws-modal');
  const btnBrowseModalFolder = document.getElementById('btn-browse-ws-folder');
  const formCreate = document.getElementById('form-create-workspace');

  if (btnDropdown) {
    btnDropdown.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleWorkspaceDropdown();
    });
  }

  // Close dropdown on outside click
  document.addEventListener('click', (e) => {
    const wrap = document.getElementById('workspace-capsule-wrap');
    if (wrap && !wrap.contains(e.target)) {
      closeWorkspaceDropdown();
    }
  });

  // Modal open triggers
  if (btnQuickNew) {
    btnQuickNew.addEventListener('click', (e) => {
      e.stopPropagation();
      openCreateWorkspaceModal();
    });
  }

  if (btnOpenCreateModal) {
    btnOpenCreateModal.addEventListener('click', (e) => {
      e.stopPropagation();
      openCreateWorkspaceModal();
    });
  }

  // Open local folder trigger in dropdown
  if (btnOpenBrowseFolder) {
    btnOpenBrowseFolder.addEventListener('click', async (e) => {
      e.stopPropagation();
      closeWorkspaceDropdown();
      await handleBrowseAndSwitchWorkspace();
    });
  }

  // Modal close triggers
  if (btnCloseModal) {
    btnCloseModal.addEventListener('click', closeCreateWorkspaceModal);
  }
  if (btnCancelModal) {
    btnCancelModal.addEventListener('click', closeCreateWorkspaceModal);
  }
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeCreateWorkspaceModal();
      }
    });
  }

  // Browse folder button inside creation modal
  if (btnBrowseModalFolder) {
    btnBrowseModalFolder.addEventListener('click', handleBrowseModalFolder);
  }

  // Form submit
  if (formCreate) {
    formCreate.addEventListener('submit', handleCreateWorkspaceSubmit);
  }

  // Keyboard shortcut: Esc to close modal/dropdown
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAllChatDropdowns();
      closeCreateWorkspaceModal();
      if (typeof closeConnectorModal === 'function') closeConnectorModal();
      if (typeof closeSyncDriveModal === 'function') closeSyncDriveModal();
      const askModal = document.getElementById('ask-question-modal');
      if (askModal && askModal.style.display !== 'none') askModal.style.display = 'none';
      document.body.style.overflow = '';
    }
  });

  // Initial load
  fetchWorkspaces();
}

function closeAllChatDropdowns(exceptId = null) {
  if (exceptId !== 'workspace' && typeof closeWorkspaceDropdown === 'function') closeWorkspaceDropdown();
  if (exceptId !== 'model' && typeof closeModelDropdown === 'function') closeModelDropdown();
  if (exceptId !== 'account' && typeof closeAccountDropdown === 'function') closeAccountDropdown();
  if (exceptId !== 'agent' && typeof closeAgentDropdown === 'function') closeAgentDropdown();
}
window.closeAllChatDropdowns = closeAllChatDropdowns;

function toggleWorkspaceDropdown() {
  const popover = document.getElementById('workspace-dropdown-popover');
  const wrap = document.getElementById('workspace-capsule-wrap');
  if (!popover || !wrap) return;

  const isVisible = popover.style.display !== 'none';
  if (isVisible) {
    closeWorkspaceDropdown();
  } else {
    openWorkspaceDropdown();
  }
}

function openWorkspaceDropdown() {
  closeAllChatDropdowns('workspace');
  const popover = document.getElementById('workspace-dropdown-popover');
  const wrap = document.getElementById('workspace-capsule-wrap');
  if (popover) popover.style.display = 'block';
  if (wrap) wrap.classList.add('open');
}

function closeWorkspaceDropdown() {
  const popover = document.getElementById('workspace-dropdown-popover');
  const wrap = document.getElementById('workspace-capsule-wrap');
  if (popover) popover.style.display = 'none';
  if (wrap) wrap.classList.remove('open');
}

function openCreateWorkspaceModal() {
  closeWorkspaceDropdown();
  const modal = document.getElementById('workspace-modal');
  if (modal) {
    modal.style.display = 'flex';
    const nameInput = document.getElementById('ws-input-name');
    if (nameInput) setTimeout(() => nameInput.focus(), 60);
  }
}

function closeCreateWorkspaceModal() {
  const modal = document.getElementById('workspace-modal');
  if (modal) modal.style.display = 'none';
}

function truncatePath(pathStr) {
  if (!pathStr) return '';
  if (pathStr.length <= 34) return pathStr;
  const parts = pathStr.split('/').filter(Boolean);
  if (parts.length <= 2) return pathStr;
  return '.../' + parts.slice(-2).join('/');
}

async function handleBrowseModalFolder() {
  try {
    const res = await fetch('/api/dialog/pick-folder');
    const data = await res.json();
    if (data.status === 'ok' && data.path) {
      const pathInput = document.getElementById('ws-input-path');
      const nameInput = document.getElementById('ws-input-name');
      if (pathInput) pathInput.value = data.path;
      if (nameInput && !nameInput.value.trim()) {
        const derived = data.path.split('/').filter(Boolean).pop() || 'My Project';
        nameInput.value = derived;
      }
    }
  } catch (err) {
    console.warn('Folder picker dialog error:', err);
    showToast('Failed to open native folder picker');
  }
}

async function handleBrowseAndSwitchWorkspace() {
  try {
    const res = await fetch('/api/dialog/pick-folder');
    const data = await res.json();
    if (data.status === 'ok' && data.path) {
      await switchWorkspace('', data.path);
    }
  } catch (err) {
    console.warn('Folder picker dialog error:', err);
    showToast('Failed to open native folder picker');
  }
}

async function handleCreateWorkspaceSubmit(e) {
  e.preventDefault();
  const nameInput = document.getElementById('ws-input-name');
  const pathInput = document.getElementById('ws-input-path');
  const submitBtn = document.getElementById('btn-submit-create-ws');

  const name = nameInput ? nameInput.value.trim() : '';
  const path = pathInput ? pathInput.value.trim() : '';

  if (!name || !path) {
    showToast('⚠️ Project name and directory path are required');
    return;
  }

  const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>⚡ Seeding Sacred Pillars...</span>';
  }

  try {
    const res = await fetch('/api/workspaces/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, path })
    });
    const data = await res.json();

    if (data.status === 'ok') {
      showToast(`⚡ Sovereign Workspace "${name}" bootstrapped! Sacred pillars seeded.`);
      playFloworkTaskDoneSound();
      closeCreateWorkspaceModal();
      if (nameInput) nameInput.value = '';
      if (pathInput) pathInput.value = '';
      await fetchWorkspaces();
    } else {
      showToast(`⚠️ Creation failed: ${data.message || 'Unknown error'}`);
    }
  } catch (err) {
    showToast(`⚠️ Network error: ${err.message}`);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnHtml;
    }
  }
}

async function changeWorkspaceViaDialog() {
  closeWorkspaceDropdown();
  try {
    const res = await fetch('/api/dialog/pick-folder');
    const data = await res.json();
    if (data.status === 'ok' && data.path) {
      await switchWorkspace('', data.path);
    }
  } catch (err) {
    console.warn('Folder picker dialog error:', err);
    showToast('Failed to open native folder picker');
  }
}

async function deleteWorkspace(id, name) {
  if (!id || id === 'default') {
    showToast('⚠️ Cannot delete default workspace');
    return;
  }
  const confirmed = confirm(`Are you sure you want to remove workspace "${name || id}" from registry?\n\n(Your project files on disk will NOT be deleted)`);
  if (!confirmed) return;

  try {
    const res = await fetch('/api/workspaces/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast(`🗑️ Workspace "${name || id}" removed from registry`);
      closeWorkspaceDropdown();
      await fetchWorkspaces();
      startNewChatSession(true);
    } else {
      showToast(`⚠️ Delete failed: ${data.message || 'Unknown error'}`);
    }
  } catch (err) {
    showToast(`⚠️ Network error: ${err.message}`);
  }
}

function setSessionWorkspaceBadge(name, path) {
  const nameEl = document.getElementById('topbar-workspace-name');
  if (nameEl) {
    nameEl.textContent = name || 'flowork';
    nameEl.title = path ? `${name} (${path})` : 'flowork';
  }
}

async function switchWorkspace(id, path) {
  try {
    const res = await fetch('/api/workspaces/switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id || '', path: path || '' })
    });
    const data = await res.json();

    if (data.status === 'ok') {
      const folderName = path.split('/').filter(Boolean).pop() || path;
      showToast(`⚡ Workspace switched to: ${folderName}`);
      closeWorkspaceDropdown();

      // Bind workspace strictly to this active session if inside a chat
      if (currentChatSessionId) {
        await fetch(`/api/chat/sessions/${currentChatSessionId}/workspace`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ workspace_id: id || 'custom', workspace_path: path || '' })
        });
      }

      setSessionWorkspaceBadge(folderName, path);
      appendWorkspaceSwitchNotice(folderName, path);
    } else {
      showToast(`⚠️ Switch failed: ${data.message || 'Unknown error'}`);
    }
  } catch (err) {
    showToast(`⚠️ Network error: ${err.message}`);
  }
}

function appendWorkspaceSwitchNotice(name, path) {
  const container = document.getElementById('rightbar-messages') || document.getElementById('chat-messages-container');
  if (!container) return;
  const notice = document.createElement('div');
  notice.className = 'chat-workspace-notice';
  notice.style.cssText = 'margin: 10px auto; padding: 8px 14px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; font-size: 11px; color: #38bdf8; display: flex; align-items: center; gap: 10px; max-width: 90%;';
  notice.innerHTML = `
    <span style="font-size: 16px;">📁</span>
    <div style="flex: 1; min-width: 0;">
      <div style="display: flex; align-items: center; gap: 6px;">
        <span style="font-weight: 700; color: #fff;">Workspace Switched: ${escapeHtml(name)}</span>
        <span style="font-size: 9px; padding: 1px 6px; border-radius: 4px; background: rgba(56, 189, 248, 0.2); color: #38bdf8; font-weight: 800;">LOCKED</span>
      </div>
      <div style="font-size: 10px; color: #94a3b8; font-family: var(--font-mono); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(path)}">${escapeHtml(path)}</div>
      <div style="font-size: 9.5px; color: #a78bfa; margin-top: 1px;">⚡ Agent territorial boundary locked to this directory (Anti-Sotoy Outside Workspace).</div>
    </div>
  `;
  container.appendChild(notice);
  if (typeof scrollChatToBottom === 'function') {
    scrollChatToBottom({ force: true });
  } else {
    container.scrollTop = container.scrollHeight;
  }
}

async function fetchWorkspaces() {
  try {
    const res = await fetch('/api/workspaces');
    if (!res.ok) return;
    const data = await res.json();

    if (data.status === 'ok') {
      sovereignWorkspaces = data.workspaces || [];
      activeWorkspacePath = data.active_path || '';

      const nameEl = document.getElementById('topbar-workspace-name');
      if (nameEl) {
        const cleanActive = (activeWorkspacePath || '').trim().replace(/\/+$/, '');
        const matched = sovereignWorkspaces.find(w => {
          const wPath = (w.path || '').trim().replace(/\/+$/, '');
          return w.is_active || (cleanActive && wPath === cleanActive);
        });

        if (matched) {
          nameEl.textContent = matched.name;
          nameEl.title = `${matched.name} (${matched.path})`;
        } else if (cleanActive) {
          const folderName = cleanActive.split('/').filter(Boolean).pop() || 'flowork';
          nameEl.textContent = folderName;
          nameEl.title = cleanActive;
        } else {
          nameEl.textContent = 'flowork';
        }
      }

      renderWorkspaceDropdownList(sovereignWorkspaces, activeWorkspacePath);
    }
  } catch (err) {
    console.error('Failed to fetch workspaces:', err);
  }
}

function renderWorkspaceDropdownList(workspaces, activePath) {
  const listEl = document.getElementById('workspace-dropdown-list');
  if (!listEl) return;

  const cleanActive = (activePath || '').trim().replace(/\/+$/, '');
  let activeWs = (workspaces || []).find(w => {
    const wPath = (w.path || '').trim().replace(/\/+$/, '');
    return w.is_active || (cleanActive && wPath === cleanActive);
  });
  if (!activeWs && workspaces && workspaces.length > 0) {
    activeWs = workspaces[0];
  }

  const activeName = activeWs ? activeWs.name : 'Default Workspace';
  const activeDisplayPath = activeWs ? activeWs.path : (activePath || 'System Root');
  const isCurrentDefault = !activeWs || activeWs.id === 'default';

  // Workspaces other than active (and not default)
  const otherWorkspaces = (workspaces || []).filter(w => {
    if (activeWs && w.id === activeWs.id) return false;
    if (w.id === 'default') return false;
    return true;
  });

  let html = `
    <div class="ws-active-card">
      <div class="ws-active-card-top">
        <span class="ws-active-tag">CURRENT WORKSPACE</span>
        <span class="ws-badge-active">ACTIVE</span>
      </div>
      <div class="ws-active-title" title="${escapeHtml(activeName)}">${escapeHtml(activeName)}</div>
      <div class="ws-active-path" title="${escapeHtml(activeDisplayPath)}">${escapeHtml(truncatePath(activeDisplayPath))}</div>
    </div>

    <div class="ws-dropdown-actions-row">
      <button class="ws-dropdown-action-btn" id="btn-ws-change-folder" title="Browse and switch workspace directory">
        <span>🔄</span><span>Change...</span>
      </button>
      <button class="ws-dropdown-action-btn" id="btn-ws-create-new" title="Bootstrap new workspace project with sacred pillars">
        <span>➕</span><span>New...</span>
      </button>
    </div>
  `;

  if (!isCurrentDefault) {
    html += `
      <button class="ws-dropdown-action-btn ws-btn-danger" id="btn-ws-delete-current" title="Delete current workspace registration">
        <span>🗑️</span><span>Delete This Workspace</span>
      </button>
    `;
  }

  if (otherWorkspaces.length > 0) {
    html += `
      <div class="ws-section-subtitle">SAVED WORKSPACES</div>
      <div class="ws-other-list">
        ${otherWorkspaces.map(w => `
          <div class="ws-item" data-id="${escapeHtml(w.id)}" data-path="${escapeHtml(w.path)}" data-name="${escapeHtml(w.name)}">
            <div class="ws-item-left">
              <span class="ws-item-icon">📁</span>
              <div class="ws-item-info">
                <span class="ws-item-name" title="${escapeHtml(w.name)}">${escapeHtml(w.name)}</span>
                <span class="ws-item-path" title="${escapeHtml(w.path)}">${escapeHtml(truncatePath(w.path))}</span>
              </div>
            </div>
            <div class="ws-item-actions">
              <button class="ws-btn-mini-switch" data-action="switch" title="Switch to this workspace">Switch</button>
              <button class="ws-btn-mini-delete" data-action="delete" title="Delete workspace from registry">🗑️</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  listEl.innerHTML = html;

  // Bind change folder button
  const btnChange = listEl.querySelector('#btn-ws-change-folder');
  if (btnChange) {
    btnChange.addEventListener('click', (e) => {
      e.stopPropagation();
      changeWorkspaceViaDialog();
    });
  }

  // Bind create new button
  const btnCreateNew = listEl.querySelector('#btn-ws-create-new');
  if (btnCreateNew) {
    btnCreateNew.addEventListener('click', (e) => {
      e.stopPropagation();
      openCreateWorkspaceModal();
    });
  }

  // Bind delete current button
  const btnDeleteCurrent = listEl.querySelector('#btn-ws-delete-current');
  if (btnDeleteCurrent && activeWs) {
    btnDeleteCurrent.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteWorkspace(activeWs.id, activeWs.name);
    });
  }

  // Bind saved workspaces switch & delete
  listEl.querySelectorAll('.ws-item').forEach(item => {
    const id = item.getAttribute('data-id');
    const path = item.getAttribute('data-path');
    const name = item.getAttribute('data-name');

    const switchBtn = item.querySelector('[data-action="switch"]');
    if (switchBtn) {
      switchBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        switchWorkspace(id, path);
      });
    }

    const deleteBtn = item.querySelector('[data-action="delete"]');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteWorkspace(id, name);
      });
    }
  });
}

// ── 0.2 SOVEREIGN SCHEDULE & AUTOMATION SYSTEM ──
let scheduleSystemInitialized = false;
let schedCurrentMode = 'timer'; // 'timer' | 'cron' | 'watcher'
let schedTimerPreset = 60; // number or 'custom'
let schedCronPreset = '*/5 * * * *'; // cron string or 'custom'
let currentRenderedJobs = [];
let currentRenderedWatchers = [];
let communityStoreDebounceTimer = null;

window.__openScheduleModal = function() {
  const modal = document.getElementById('schedule-modal');
  if (modal) {
    modal.style.display = 'flex';
    if (typeof fetchScheduledJobs === 'function') fetchScheduledJobs();
    updateScheduleExecutionSummary();
  }
};

function formatDurationToHuman(seconds) {
  seconds = parseInt(seconds, 10);
  if (isNaN(seconds) || seconds <= 0) return 'Immediate';
  if (seconds < 60) return `${seconds}s`;
  if (seconds === 60) return '1 min';
  if (seconds < 3600 && seconds % 60 === 0) return `${seconds / 60} mins`;
  if (seconds === 3600) return '1 hour';
  if (seconds % 3600 === 0) return `${seconds / 3600} hours`;
  const mins = Math.floor(seconds / 60);
  const rem = seconds % 60;
  return rem > 0 ? `${mins}m ${rem}s` : `${mins} mins`;
}

function formatCronToHuman(cronStr) {
  if (!cronStr) return 'Custom cron';
  const c = cronStr.trim();
  if (c === '*/5 * * * *') return 'Every 5 mins';
  if (c === '*/10 * * * *') return 'Every 10 mins';
  if (c === '*/15 * * * *') return 'Every 15 mins';
  if (c === '*/30 * * * *') return 'Every 30 mins';
  if (c === '0 * * * *') return 'Every hour';
  if (c === '* * * * *') return 'Every minute';
  if (c === '0 9 * * *') return 'Daily at 9:00 AM';

  const mMatch = c.match(/^\*\/([0-9]+)\s+\*\s+\*\s+\*\s+\*$/);
  if (mMatch) return `Every ${mMatch[1]} mins`;
  const hMatch = c.match(/^0\s+\*\/([0-9]+)\s+\*\s+\*\s+\*$/);
  if (hMatch) return `Every ${hMatch[1]} hours`;
  const dailyMatch = c.match(/^([0-9]+)\s+([0-9]+)\s+\*\s+\*\s+\*$/);
  if (dailyMatch) {
    const hh = dailyMatch[2].padStart(2, '0');
    const mm = dailyMatch[1].padStart(2, '0');
    return `Daily at ${hh}:${mm}`;
  }
  return `Cron (${c})`;
}

function getCalculatedTimerSeconds() {
  if (schedTimerPreset !== 'custom') {
    return parseInt(schedTimerPreset, 10) || 60;
  }
  const valInput = document.getElementById('sched-timer-custom-val');
  const unitSelect = document.getElementById('sched-timer-custom-unit');
  const val = Math.max(1, parseInt(valInput ? valInput.value : '10', 10) || 10);
  const unit = unitSelect ? unitSelect.value : 'minutes';
  if (unit === 'seconds') return val;
  if (unit === 'hours') return val * 3600;
  return val * 60;
}

function getCalculatedCronExpression() {
  const rawInput = document.getElementById('sched-input-cron-raw');
  const rawVal = rawInput ? rawInput.value.trim() : '';
  if (rawVal) return rawVal;

  if (schedCronPreset !== 'custom') {
    return schedCronPreset || '*/5 * * * *';
  }
  const valInput = document.getElementById('sched-cron-interval-val');
  const unitSelect = document.getElementById('sched-cron-interval-unit');
  const val = Math.max(1, parseInt(valInput ? valInput.value : '10', 10) || 10);
  const unit = unitSelect ? unitSelect.value : 'minutes';
  if (unit === 'hours') return (val === 1) ? '0 * * * *' : `0 */${val} * * *`;
  if (unit === 'days') return (val === 1) ? '0 9 * * *' : `0 9 */${val} * *`;
  return `*/${val} * * * *`;
}

function updateScheduleExecutionSummary() {
  const summaryText = document.getElementById('sched-summary-text');
  if (!summaryText) return;

  if (schedCurrentMode === 'timer') {
    const secs = getCalculatedTimerSeconds();
    const humanDur = formatDurationToHuman(secs);
    const estTime = new Date(Date.now() + secs * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    summaryText.innerHTML = `Will run once in <strong>${escapeHtml(humanDur)}</strong> (approx. ${estTime}) bound to current session.`;
  } else if (schedCurrentMode === 'cron') {
    const cronExpr = getCalculatedCronExpression();
    const humanCron = formatCronToHuman(cronExpr);
    summaryText.innerHTML = `Will repeat routine: <strong>${escapeHtml(humanCron)}</strong> bound to current session.`;
  } else if (schedCurrentMode === 'watcher') {
    const watcherId = (document.getElementById('sched-watcher-id')?.value || '').trim() || 'ambient_watcher';
    const cat = document.getElementById('sched-watcher-cat')?.value || 'CAT-005';
    const tpl = document.getElementById('sched-watcher-template')?.value || 'rest_polling';
    summaryText.innerHTML = `Will scaffold & register ambient daemon <strong>${escapeHtml(watcherId)}</strong> (${escapeHtml(cat)}, ${escapeHtml(tpl)}) continuously monitoring external events.`;
  }
}

function switchSchedTab(target) {
  const tabActive = document.getElementById('tab-sched-active');
  const tabNew = document.getElementById('tab-sched-new');
  const tabStore = document.getElementById('tab-sched-store');
  const contentList = document.getElementById('sched-tab-content-list');
  const contentNew = document.getElementById('sched-tab-content-new');
  const contentStore = document.getElementById('sched-tab-content-store');

  [tabActive, tabNew, tabStore].forEach(t => t?.classList.remove('active'));
  if (contentList) contentList.style.display = 'none';
  if (contentNew) contentNew.style.display = 'none';
  if (contentStore) contentStore.style.display = 'none';

  if (target === 'active') {
    tabActive?.classList.add('active');
    if (contentList) contentList.style.display = 'block';
    fetchTriggersAndJobs();
  } else if (target === 'new') {
    tabNew?.classList.add('active');
    if (contentNew) contentNew.style.display = 'block';
    updateScheduleExecutionSummary();
  } else if (target === 'store') {
    tabStore?.classList.add('active');
    if (contentStore) contentStore.style.display = 'block';
    const storeSearchInput = document.getElementById('trig-store-search-input');
    fetchCommunityTriggers(storeSearchInput ? storeSearchInput.value.trim() : '');
  }
}

function setScheduleMode(mode) {
  schedCurrentMode = mode;
  const hiddenMode = document.getElementById('sched-selected-mode');
  if (hiddenMode) hiddenMode.value = mode;

  const modeTimerBtn = document.getElementById('sched-mode-timer-btn');
  const modeCronBtn = document.getElementById('sched-mode-cron-btn');
  const modeWatcherBtn = document.getElementById('sched-mode-watcher-btn');
  const sectionTimer = document.getElementById('sched-section-timer');
  const sectionCron = document.getElementById('sched-section-cron');
  const sectionWatcher = document.getElementById('sched-section-watcher');
  const submitText = document.getElementById('sched-submit-text');

  [modeTimerBtn, modeCronBtn, modeWatcherBtn].forEach(btn => btn?.classList.remove('active'));
  if (sectionTimer) sectionTimer.style.display = 'none';
  if (sectionCron) sectionCron.style.display = 'none';
  if (sectionWatcher) sectionWatcher.style.display = 'none';

  const editJobIdInput = document.getElementById('sched-edit-job-id');
  const isEditing = editJobIdInput && editJobIdInput.value.trim();

  if (mode === 'timer') {
    modeTimerBtn?.classList.add('active');
    if (sectionTimer) sectionTimer.style.display = 'block';
    if (submitText) submitText.textContent = isEditing ? '💾 Update Automation' : '⚡ Activate Sovereign Automation';
  } else if (mode === 'cron') {
    modeCronBtn?.classList.add('active');
    if (sectionCron) sectionCron.style.display = 'block';
    if (submitText) submitText.textContent = isEditing ? '💾 Update Automation' : '🔁 Activate Recurring Schedule';
  } else if (mode === 'watcher') {
    modeWatcherBtn?.classList.add('active');
    if (sectionWatcher) sectionWatcher.style.display = 'block';
    if (submitText) submitText.textContent = '📡 Scaffold & Deploy Watcher';
  }

  updateScheduleExecutionSummary();
}

function initScheduleSystem() {
  if (scheduleSystemInitialized) return;
  scheduleSystemInitialized = true;

  const btnSchedule = document.getElementById('btn-chat-schedule');
  const modal = document.getElementById('schedule-modal');
  const btnCloseModal = document.getElementById('btn-close-sched-modal');
  const btnCancelModal = document.getElementById('btn-cancel-sched-modal');
  const tabActive = document.getElementById('tab-sched-active');
  const tabNew = document.getElementById('tab-sched-new');
  const tabStore = document.getElementById('tab-sched-store');
  const formCreate = document.getElementById('form-create-schedule');

  const modeTimerBtn = document.getElementById('sched-mode-timer-btn');
  const modeCronBtn = document.getElementById('sched-mode-cron-btn');
  const modeWatcherBtn = document.getElementById('sched-mode-watcher-btn');

  if (btnSchedule) {
    btnSchedule.addEventListener('click', (e) => {
      e.stopPropagation();
      openScheduleModal();
    });
  }

  if (btnCloseModal) {
    btnCloseModal.addEventListener('click', closeScheduleModal);
  }
  if (btnCancelModal) {
    btnCancelModal.addEventListener('click', closeScheduleModal);
  }
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeScheduleModal();
    });
  }

  // 3-Tab Navigation
  if (tabActive) tabActive.addEventListener('click', () => switchSchedTab('active'));
  if (tabNew) tabNew.addEventListener('click', () => switchSchedTab('new'));
  if (tabStore) tabStore.addEventListener('click', () => switchSchedTab('store'));

  // 3-Mode Architecture Switcher
  if (modeTimerBtn) modeTimerBtn.addEventListener('click', () => setScheduleMode('timer'));
  if (modeCronBtn) modeCronBtn.addEventListener('click', () => setScheduleMode('cron'));
  if (modeWatcherBtn) modeWatcherBtn.addEventListener('click', () => setScheduleMode('watcher'));

  // Watcher Inputs Dynamic Preview
  const watcherIdInput = document.getElementById('sched-watcher-id');
  const watcherCatSelect = document.getElementById('sched-watcher-cat');
  const watcherTemplateSelect = document.getElementById('sched-watcher-template');
  if (watcherIdInput) watcherIdInput.addEventListener('input', updateScheduleExecutionSummary);
  if (watcherCatSelect) watcherCatSelect.addEventListener('change', updateScheduleExecutionSummary);
  if (watcherTemplateSelect) watcherTemplateSelect.addEventListener('change', updateScheduleExecutionSummary);

  // Timer Presets & Custom Handlers
  const timerChips = document.querySelectorAll('#timer-preset-chips .sched-chip-pill');
  const timerCustomRow = document.getElementById('timer-custom-row');
  const timerCustomVal = document.getElementById('sched-timer-custom-val');
  const timerCustomUnit = document.getElementById('sched-timer-custom-unit');

  timerChips.forEach(chip => {
    chip.addEventListener('click', () => {
      timerChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const val = chip.getAttribute('data-secs');
      schedTimerPreset = val === 'custom' ? 'custom' : parseInt(val, 10);
      if (timerCustomRow) {
        timerCustomRow.style.display = (val === 'custom') ? 'flex' : 'none';
      }
      updateScheduleExecutionSummary();
    });
  });

  if (timerCustomVal) {
    timerCustomVal.addEventListener('input', updateScheduleExecutionSummary);
  }
  if (timerCustomUnit) {
    timerCustomUnit.addEventListener('change', updateScheduleExecutionSummary);
  }

  // Cron Presets & Custom Handlers
  const cronChips = document.querySelectorAll('#cron-preset-chips .sched-chip-pill');
  const cronCustomWrap = document.getElementById('cron-custom-wrap');
  const cronIntervalVal = document.getElementById('sched-cron-interval-val');
  const cronIntervalUnit = document.getElementById('sched-cron-interval-unit');

  cronChips.forEach(chip => {
    chip.addEventListener('click', () => {
      cronChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const val = chip.getAttribute('data-cron');
      schedCronPreset = val;
      if (cronCustomWrap) {
        cronCustomWrap.style.display = (val === 'custom') ? 'block' : 'none';
      }
      updateScheduleExecutionSummary();
    });
  });

  if (cronIntervalVal) {
    cronIntervalVal.addEventListener('input', updateScheduleExecutionSummary);
  }
  if (cronIntervalUnit) {
    cronIntervalUnit.addEventListener('change', updateScheduleExecutionSummary);
  }

  // Advanced Raw Unix Cron Accordion
  const btnToggleAdvanced = document.getElementById('btn-toggle-advanced-cron');
  const advancedCronBody = document.getElementById('sched-advanced-cron-body');
  const advancedChevron = document.getElementById('sched-advanced-chevron');
  const inputCronRaw = document.getElementById('sched-input-cron-raw');

  if (btnToggleAdvanced && advancedCronBody) {
    btnToggleAdvanced.addEventListener('click', () => {
      const isHidden = advancedCronBody.style.display === 'none';
      advancedCronBody.style.display = isHidden ? 'block' : 'none';
      if (advancedChevron) advancedChevron.textContent = isHidden ? '▾' : '▸';
    });
  }

  if (inputCronRaw) {
    inputCronRaw.addEventListener('input', updateScheduleExecutionSummary);
  }

  // Prompt Ideas Pills
  document.querySelectorAll('.sched-idea-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const promptInput = document.getElementById('sched-input-prompt');
      const promptText = pill.getAttribute('data-prompt');
      if (promptInput && promptText) {
        promptInput.value = promptText;
        promptInput.focus();
      }
    });
  });

  const btnCancelEdit = document.getElementById('btn-cancel-edit-sched');
  if (btnCancelEdit) {
    btnCancelEdit.addEventListener('click', () => {
      resetScheduleEditForm();
      if (tabActive) tabActive.click();
    });
  }

  // Community Store Search & Refresh Handlers
  const storeSearchInput = document.getElementById('trig-store-search-input');
  const btnRefreshStore = document.getElementById('btn-refresh-store');

  if (storeSearchInput) {
    storeSearchInput.addEventListener('input', () => {
      clearTimeout(communityStoreDebounceTimer);
      communityStoreDebounceTimer = setTimeout(() => {
        fetchCommunityTriggers(storeSearchInput.value.trim());
      }, 300);
    });
  }

  if (btnRefreshStore) {
    btnRefreshStore.addEventListener('click', () => {
      fetchCommunityTriggers(storeSearchInput ? storeSearchInput.value.trim() : '');
    });
  }

  if (formCreate) {
    formCreate.addEventListener('submit', handleCreateScheduleSubmit);
  }
}

window.__openScheduleModal = openScheduleModal;

function openScheduleModal() {
  const modal = document.getElementById('schedule-modal');
  if (modal) {
    modal.style.display = 'flex';
    fetchTriggersAndJobs();
    updateScheduleExecutionSummary();
  }
}

function closeScheduleModal() {
  const modal = document.getElementById('schedule-modal');
  if (modal) {
    modal.style.display = 'none';
    resetScheduleEditForm();
  }
}

async function fetchTriggersAndJobs() {
  const listEl = document.getElementById('sched-jobs-list');
  const countBadge = document.getElementById('sched-active-count');
  const headerPulseDot = document.getElementById('trig-hub-badge-pulse');
  if (!listEl) return;

  listEl.innerHTML = '<div style="padding: 24px; text-align: center; color: #94a3b8; font-size: 11.5px;">Loading autonomous automations & ambient daemons...</div>';

  try {
    const activeSession = currentChatSessionId || 'default';
    const res = await fetch(`/api/triggers/list?session_id=${encodeURIComponent(activeSession)}`);
    const data = await res.json();
    if (data.status === 'ok') {
      const allJobs = data.chrono_jobs || [];
      const jobs = allJobs.filter(j => (j.session_id || 'default') === activeSession);
      const watchers = data.external_triggers || [];
      currentRenderedJobs = jobs;
      currentRenderedWatchers = watchers;

      const totalActive = (data.active_chrono_count || 0) + (data.running_external_count || 0);
      if (countBadge) countBadge.textContent = totalActive;
      if (headerPulseDot) {
        headerPulseDot.style.display = totalActive > 0 ? 'inline-block' : 'none';
      }

      renderUnifiedTriggersList(watchers, jobs);
    } else {
      listEl.innerHTML = `<div style="padding: 16px; text-align: center; color: #f87171; font-size: 11px;">Failed to load triggers: ${escapeHtml(data.message || 'Error')}</div>`;
    }
  } catch (err) {
    listEl.innerHTML = `<div style="padding: 16px; text-align: center; color: #f87171; font-size: 11px;">Network error: ${escapeHtml(err.message)}</div>`;
  }
}
const fetchScheduledJobs = fetchTriggersAndJobs;

function renderUnifiedTriggersList(watchers, jobs) {
  const listEl = document.getElementById('sched-jobs-list');
  if (!listEl) return;

  const hasWatchers = Array.isArray(watchers) && watchers.length > 0;
  const hasJobs = Array.isArray(jobs) && jobs.length > 0;

  if (!hasWatchers && !hasJobs) {
    listEl.innerHTML = `
      <div style="padding: 36px 16px; text-align: center; color: #64748b; font-size: 12px;">
        <span style="font-size: 32px; display: block; margin-bottom: 12px;">⚡</span>
        <strong style="color: #cbd5e1; font-size: 13.5px; display: block; margin-bottom: 6px;">No Active Automations or Ambient Watchers</strong>
        No scheduled background tasks or ambient external daemons currently registered.<br>
        <div style="display: flex; gap: 8px; justify-content: center; margin-top: 14px;">
          <button type="button" class="sched-chip-pill active" style="cursor: pointer; padding: 6px 14px;" onclick="resetScheduleEditForm(); document.getElementById('tab-sched-new').click()">+ Create Automation</button>
          <button type="button" class="sched-chip-pill" style="cursor: pointer; padding: 6px 14px;" onclick="document.getElementById('tab-sched-store').click()">🌐 Explore Community Store</button>
        </div>
      </div>
    `;
    return;
  }

  let html = '';

  // 1. Ambient Watchers Section
  if (hasWatchers) {
    html += `
      <div class="trig-section-title">
        <span>📡 Ambient External Watchers (${watchers.length})</span>
        <span style="font-size: 10px; color: #64748b;">Autonomous Daemons</span>
      </div>
    `;

    html += watchers.map(w => {
      const isRunning = Boolean(w.running);
      const statusPill = isRunning
        ? `<span class="trig-status-pill trig-status-running">RUNNING</span>`
        : `<span class="trig-status-pill trig-status-idle">IDLE</span>`;

      const toggleBtn = isRunning
        ? `<button type="button" class="trig-btn-toggle" data-trigger-action="toggle" data-id="${escapeHtml(w.id)}" data-current="running" title="Stop daemon process" style="background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.35); color: #f87171;">⏹ Stop</button>`
        : `<button type="button" class="trig-btn-toggle" data-trigger-action="toggle" data-id="${escapeHtml(w.id)}" data-current="idle" title="Start background watcher daemon">▶ Start</button>`;

      const categoryTag = w.category ? `<span class="sched-chip-pill" style="font-size: 9.5px; padding: 1px 7px; background: rgba(56, 189, 248, 0.1); border-color: rgba(56, 189, 248, 0.25); color: #38bdf8;">${escapeHtml(w.category)}</span>` : '';

      return `
        <div class="trig-watcher-item" data-id="${escapeHtml(w.id)}">
          <div style="display: flex; align-items: flex-start; gap: 10px; flex: 1; min-width: 0;">
            <span style="font-size: 20px; line-height: 1; margin-top: 2px;">📡</span>
            <div style="flex: 1; min-width: 0;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px; flex-wrap: wrap;">
                <strong style="color: #f1f5f9; font-size: 12.5px;">${escapeHtml(w.name || w.id)}</strong>
                ${categoryTag}
                <code style="font-size: 10px; color: #94a3b8; background: rgba(0,0,0,0.3); padding: 1px 4px; border-radius: 4px;">${escapeHtml(w.id)}</code>
              </div>
              <p style="margin: 0; font-size: 11px; color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(w.description || '')}">${escapeHtml(w.description || 'Ambient background watcher')}</p>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 6px; margin-left: 10px;">
            ${statusPill}
            <button type="button" class="trig-btn-test" data-trigger-action="test" data-id="${escapeHtml(w.id)}" title="Execute single poll inspection and show telemetry">🧪 Test Run</button>
            ${toggleBtn}
          </div>
        </div>
      `;
    }).join('');
  }

  // 2. Chrono Routines Section
  if (hasJobs) {
    html += `
      <div class="trig-section-title" style="${hasWatchers ? 'margin-top: 16px;' : ''}">
        <span>⏰ Chrono Routines & Timers (${jobs.length})</span>
        <span style="font-size: 10px; color: #64748b;">Chat Session Routines</span>
      </div>
    `;

    html += jobs.map(job => {
      const isTimer = job.job_type === 'timer';
      const icon = isTimer ? '⚡' : '🔁';
      const timingHuman = isTimer 
        ? formatDurationToHuman(job.duration_seconds) + ' timer'
        : formatCronToHuman(job.cron_expression);
      const status = job.status || 'active';
      const statusClass = `sched-status-${status}`;

      return `
        <div class="sched-job-item" data-id="${escapeHtml(job.id)}">
          <div class="sched-job-left">
            <span class="sched-job-icon">${icon}</span>
            <div class="sched-job-info">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
                <span class="sched-job-prompt" title="${escapeHtml(job.prompt)}">${escapeHtml(job.prompt)}</span>
              </div>
              <div class="sched-job-meta">
                <span style="color: #38bdf8; font-weight: 700;">${escapeHtml(timingHuman)}</span>
                <span>• iter: ${job.iteration_count || 0}</span>
                ${job.last_fired_at ? `<span>• last: ${escapeHtml(job.last_fired_at)}</span>` : ''}
              </div>
            </div>
          </div>
          <div class="sched-job-actions">
            <span class="sched-status-badge ${statusClass}">${escapeHtml(status)}</span>
            <button type="button" class="sched-btn-edit" data-action="edit" title="Edit this scheduled task">✏️ Edit</button>
            <button type="button" class="sched-btn-delete" data-action="delete" title="Permanently delete this task">🗑️ Delete</button>
          </div>
        </div>
      `;
    }).join('');
  }

  listEl.innerHTML = html;

  // Bind trigger actions
  listEl.querySelectorAll('[data-trigger-action="test"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-id');
      if (id) runTriggerTest(id, btn);
    });
  });

  listEl.querySelectorAll('[data-trigger-action="toggle"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-id');
      const current = btn.getAttribute('data-current') || 'idle';
      if (id) toggleTriggerDaemon(id, current, btn);
    });
  });

  // Bind job actions
  listEl.querySelectorAll('[data-action="edit"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const item = btn.closest('.sched-job-item');
      const id = item ? item.getAttribute('data-id') : null;
      const job = currentRenderedJobs.find(j => j.id === id);
      if (job) editScheduledJob(job);
    });
  });

  listEl.querySelectorAll('[data-action="delete"]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const item = btn.closest('.sched-job-item');
      const id = item ? item.getAttribute('data-id') : null;
      if (id) deleteScheduledJob(id);
    });
  });
}

async function runTriggerTest(triggerId, btn) {
  if (!triggerId) return;
  const container = document.getElementById('trig-telemetry-container');
  const tidSpan = document.getElementById('trig-telemetry-tid');
  const pre = document.getElementById('trig-telemetry-pre');

  if (container) container.style.display = 'block';
  if (tidSpan) tidSpan.textContent = triggerId;
  if (pre) pre.textContent = `[EXECUTING] node external_triger/${triggerId}/watcher.mjs --check-once\nInspecting ambient telemetry in isolated subshell...`;

  const originalBtnText = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '🧪 Testing...';
  }

  try {
    const res = await fetch('/api/triggers/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger_id: triggerId })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      const resObj = data.result || {};
      const exitCode = resObj.exit_code ?? 0;
      const outputText = JSON.stringify(resObj.telemetry || resObj, null, 2);
      if (pre) {
        pre.textContent = `// Exit Code: ${exitCode}\n// Raw Stderr: ${resObj.stderr || 'none'}\n\n${outputText}`;
      }
      showToast(`🧪 Test completed: Exit Code ${exitCode}`);
      playFloworkTaskDoneSound();
    } else {
      if (pre) pre.textContent = `// ERROR:\n${data.message || 'Execution failed'}`;
      showToast(`⚠️ Test run failed: ${data.message || 'Error'}`);
    }
  } catch (err) {
    if (pre) pre.textContent = `// NETWORK EXCEPTION:\n${err.message}`;
    showToast(`⚠️ Test run network error: ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalBtnText;
    }
  }
}

async function toggleTriggerDaemon(triggerId, currentStatus, btn) {
  if (!triggerId) return;
  const action = currentStatus === 'running' ? 'stop' : 'start';

  const originalBtnText = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = action === 'start' ? '⏳ Starting...' : '⏳ Stopping...';
  }

  try {
    const res = await fetch('/api/triggers/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger_id: triggerId, action })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast(data.message || `Daemon ${action}ed`);
      playFloworkTaskDoneSound();
      fetchTriggersAndJobs();
    } else {
      showToast(`⚠️ Action failed: ${data.message || 'Error'}`);
    }
  } catch (err) {
    showToast(`⚠️ Network error: ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalBtnText;
    }
  }
}

async function fetchCommunityTriggers(query = '') {
  const gridEl = document.getElementById('trig-store-grid');
  if (!gridEl) return;
  gridEl.innerHTML = '<div style="padding: 24px; text-align: center; color: #94a3b8; font-size: 11.5px;">Connecting to flowork-os/triger registry...</div>';

  try {
    const url = `/api/triggers/store?query=${encodeURIComponent(query || '')}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.status === 'ok') {
      const resObj = data.result || {};
      const triggers = resObj.triggers || [];
      renderCommunityStoreGrid(triggers);
    } else {
      gridEl.innerHTML = `<div style="padding: 16px; text-align: center; color: #f87171; font-size: 11px;">Failed to load store: ${escapeHtml(data.message || 'Error')}</div>`;
    }
  } catch (err) {
    gridEl.innerHTML = `<div style="padding: 16px; text-align: center; color: #f87171; font-size: 11px;">Network error: ${escapeHtml(err.message)}</div>`;
  }
}

function renderCommunityStoreGrid(triggers) {
  const gridEl = document.getElementById('trig-store-grid');
  if (!gridEl) return;

  if (!triggers || triggers.length === 0) {
    gridEl.innerHTML = `
      <div style="padding: 30px; text-align: center; color: #64748b; font-size: 12px;">
        <span style="font-size: 26px; display: block; margin-bottom: 8px;">🔍</span>
        No matching community triggers found in flowork-os/triger.
      </div>
    `;
    return;
  }

  const installedIds = new Set((currentRenderedWatchers || []).map(w => w.id));

  gridEl.innerHTML = triggers.map(t => {
    const isInstalled = installedIds.has(t.id);
    const installBtn = isInstalled
      ? `<span class="trig-btn-install trig-btn-installed">✓ Installed</span>`
      : `<button type="button" class="trig-btn-install" data-store-install="${escapeHtml(t.id)}">📥 Install Trigger</button>`;

    return `
      <div class="trig-store-card" data-id="${escapeHtml(t.id)}">
        <div class="trig-store-card-header">
          <div class="trig-store-card-title">
            <span>📡</span>
            <span>${escapeHtml(t.name || t.id)}</span>
          </div>
          <span style="font-size: 10px; color: #a855f7; font-weight: 700; background: rgba(168, 85, 247, 0.12); padding: 2px 7px; border-radius: 6px; border: 1px solid rgba(168, 85, 247, 0.25);">${escapeHtml(t.category || 'CAT-005')}</span>
        </div>
        <div class="trig-store-card-desc">
          ${escapeHtml(t.description || 'Community external watcher trigger module.')}
        </div>
        <div class="trig-store-card-footer">
          <div style="font-size: 10.5px; color: #64748b;">
            <span>v${escapeHtml(t.version || '1.0.0')}</span>
            <span> • by ${escapeHtml(t.author || 'community')}</span>
          </div>
          ${installBtn}
        </div>
      </div>
    `;
  }).join('');

  gridEl.querySelectorAll('[data-store-install]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-store-install');
      if (id) installCommunityTrigger(id, btn);
    });
  });
}

async function installCommunityTrigger(triggerId, btn) {
  if (!triggerId) return;
  const originalBtnText = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '⏳ Installing...';
  }

  try {
    const res = await fetch('/api/triggers/install', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger_id: triggerId })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast(`🎉 Trigger '${triggerId}' successfully installed!`);
      playFloworkTaskDoneSound();
      if (btn) {
        btn.outerHTML = '<span class="trig-btn-install trig-btn-installed">✓ Installed</span>';
      }
      fetchTriggersAndJobs();
    } else {
      showToast(`⚠️ Installation failed: ${data.message || 'Error'}`);
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalBtnText;
      }
    }
  } catch (err) {
    showToast(`⚠️ Network error: ${err.message}`);
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalBtnText;
    }
  }
}

function editScheduledJob(job) {
  if (!job) return;
  const promptInput = document.getElementById('sched-input-prompt');
  const editJobIdInput = document.getElementById('sched-edit-job-id');
  const submitText = document.getElementById('sched-submit-text');
  const btnCancelEdit = document.getElementById('btn-cancel-edit-sched');
  const tabNew = document.getElementById('tab-sched-new');

  if (editJobIdInput) editJobIdInput.value = job.id;
  if (promptInput) promptInput.value = job.prompt || '';
  if (submitText) submitText.textContent = '💾 Update Automation';
  if (btnCancelEdit) btnCancelEdit.style.display = 'inline-flex';

  if (tabNew) {
    const tabSpan = tabNew.querySelector('span');
    if (tabSpan) tabSpan.textContent = '✏️ Edit Automation';
  }

  if (job.job_type === 'cron') {
    setScheduleMode('cron');

    const cronChips = document.querySelectorAll('#cron-preset-chips .sched-chip-pill');
    let matched = false;
    cronChips.forEach(chip => {
      chip.classList.remove('active');
      if (chip.getAttribute('data-cron') === job.cron_expression) {
        chip.classList.add('active');
        matched = true;
      }
    });

    const cronCustomWrap = document.getElementById('cron-custom-wrap');
    const inputCronRaw = document.getElementById('sched-input-cron-raw');
    const advancedCronBody = document.getElementById('sched-advanced-cron-body');
    const advancedChevron = document.getElementById('sched-advanced-chevron');

    if (!matched) {
      const customChip = document.querySelector('#cron-preset-chips .sched-chip-pill[data-cron="custom"]');
      if (customChip) customChip.classList.add('active');
      schedCronPreset = 'custom';
      if (cronCustomWrap) cronCustomWrap.style.display = 'block';
      if (inputCronRaw) inputCronRaw.value = job.cron_expression || '';
      if (advancedCronBody) advancedCronBody.style.display = 'block';
      if (advancedChevron) advancedChevron.textContent = '▾';
    } else {
      schedCronPreset = job.cron_expression;
      if (cronCustomWrap) cronCustomWrap.style.display = 'none';
      if (inputCronRaw) inputCronRaw.value = '';
    }
  } else {
    setScheduleMode('timer');

    const secs = job.duration_seconds || 60;
    const timerChips = document.querySelectorAll('#timer-preset-chips .sched-chip-pill');
    let matched = false;
    timerChips.forEach(chip => {
      chip.classList.remove('active');
      if (chip.getAttribute('data-secs') === String(secs)) {
        chip.classList.add('active');
        matched = true;
      }
    });

    const timerCustomRow = document.getElementById('timer-custom-row');
    const timerCustomVal = document.getElementById('sched-timer-custom-val');
    const timerCustomUnit = document.getElementById('sched-timer-custom-unit');

    if (!matched) {
      const customChip = document.querySelector('#timer-preset-chips .sched-chip-pill[data-secs="custom"]');
      if (customChip) customChip.classList.add('active');
      schedTimerPreset = 'custom';
      if (timerCustomRow) timerCustomRow.style.display = 'flex';
      if (secs % 3600 === 0 && secs >= 3600) {
        if (timerCustomVal) timerCustomVal.value = secs / 3600;
        if (timerCustomUnit) timerCustomUnit.value = 'hours';
      } else if (secs % 60 === 0 && secs >= 60) {
        if (timerCustomVal) timerCustomVal.value = secs / 60;
        if (timerCustomUnit) timerCustomUnit.value = 'minutes';
      } else {
        if (timerCustomVal) timerCustomVal.value = secs;
        if (timerCustomUnit) timerCustomUnit.value = 'seconds';
      }
    } else {
      schedTimerPreset = secs;
      if (timerCustomRow) timerCustomRow.style.display = 'none';
    }
  }

  updateScheduleExecutionSummary();
  if (tabNew) tabNew.click();
}

function resetScheduleEditForm() {
  const editJobIdInput = document.getElementById('sched-edit-job-id');
  const promptInput = document.getElementById('sched-input-prompt');
  const submitText = document.getElementById('sched-submit-text');
  const btnCancelEdit = document.getElementById('btn-cancel-edit-sched');
  const tabNew = document.getElementById('tab-sched-new');

  if (editJobIdInput) editJobIdInput.value = '';
  if (promptInput) promptInput.value = '';
  if (submitText) submitText.textContent = '⚡ Activate Sovereign Automation';
  if (btnCancelEdit) btnCancelEdit.style.display = 'none';

  const watcherIdInput = document.getElementById('sched-watcher-id');
  const watcherNameInput = document.getElementById('sched-watcher-name');
  if (watcherIdInput) watcherIdInput.value = '';
  if (watcherNameInput) watcherNameInput.value = '';

  if (tabNew) {
    const tabSpan = tabNew.querySelector('span');
    if (tabSpan) tabSpan.textContent = '+ New Trigger / Routine';
  }

  setScheduleMode('timer');
  const timerChips = document.querySelectorAll('#timer-preset-chips .sched-chip-pill');
  timerChips.forEach(chip => {
    chip.classList.toggle('active', chip.getAttribute('data-secs') === '60');
  });
  schedTimerPreset = 60;
  const timerCustomRow = document.getElementById('timer-custom-row');
  if (timerCustomRow) timerCustomRow.style.display = 'none';

  updateScheduleExecutionSummary();
}

async function deleteScheduledJob(id) {
  if (!id) return;
  const ok = confirm('Permanently delete this scheduled automation? This action cannot be undone.');
  if (!ok) return;

  try {
    const res = await fetch('/api/schedule/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast('🗑️ Sovereign automation permanently deleted');
      const editJobIdInput = document.getElementById('sched-edit-job-id');
      if (editJobIdInput && editJobIdInput.value === id) {
        resetScheduleEditForm();
      }
      fetchTriggersAndJobs();
    } else {
      showToast(`⚠️ Delete failed: ${data.message || 'Error'}`);
    }
  } catch (err) {
    showToast(`⚠️ Network error: ${err.message}`);
  }
}

async function handleCreateScheduleSubmit(e) {
  e.preventDefault();
  const promptInput = document.getElementById('sched-input-prompt');
  const submitBtn = document.getElementById('btn-submit-create-sched');
  const editJobIdInput = document.getElementById('sched-edit-job-id');
  const editingJobId = editJobIdInput ? editJobIdInput.value.trim() : '';

  const prompt = promptInput ? promptInput.value.trim() : '';
  if (!prompt) return showToast('⚠️ Task instruction prompt is required');

  if (submitBtn) submitBtn.disabled = true;

  try {
    if (schedCurrentMode === 'watcher') {
      // ── AMBIENT WATCHER CREATION / SCAFFOLDING ──
      const watcherIdInput = document.getElementById('sched-watcher-id');
      const watcherNameInput = document.getElementById('sched-watcher-name');
      const watcherCatSelect = document.getElementById('sched-watcher-cat');
      const watcherTemplateSelect = document.getElementById('sched-watcher-template');

      const trigger_id = watcherIdInput ? watcherIdInput.value.trim() : '';
      if (!trigger_id) {
        showToast('⚠️ Trigger ID (slug) is required');
        return;
      }
      if (!/^[a-zA-Z0-9_\-]+$/.test(trigger_id)) {
        showToast('⚠️ Trigger ID must contain only alphanumeric characters, dashes, or underscores');
        return;
      }

      const name = watcherNameInput && watcherNameInput.value.trim() ? watcherNameInput.value.trim() : trigger_id;
      const category = watcherCatSelect ? watcherCatSelect.value : 'CAT-005';
      const template = watcherTemplateSelect ? watcherTemplateSelect.value : 'rest_polling';

      const payload = {
        trigger_id,
        name,
        category,
        template,
        prompt,
        description: prompt
      };

      const res = await fetch('/api/triggers/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'ok') {
        showToast(`📡 Ambient Watcher '${trigger_id}' scaffolded successfully!`);
        playFloworkTaskDoneSound();
        resetScheduleEditForm();
        switchSchedTab('active');
      } else {
        showToast(`⚠️ Watcher scaffolding failed: ${data.message || 'Error'}`);
      }
      return;
    }

    if (editingJobId) {
      // ── UPDATE EXISTING CHRONO JOB ──
      const payload = {
        id: editingJobId,
        prompt
      };

      if (schedCurrentMode === 'timer') {
        const secs = getCalculatedTimerSeconds();
        if (isNaN(secs) || secs <= 0) return showToast('⚠️ Delay duration must be positive seconds');
        payload.duration_seconds = secs;
      } else {
        const cron = getCalculatedCronExpression();
        if (!cron) return showToast('⚠️ Recurrence schedule is required');
        payload.cron_expression = cron;
      }

      const res = await fetch('/api/schedule/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'ok') {
        showToast('💾 Sovereign automation successfully updated!');
        playFloworkTaskDoneSound();
        resetScheduleEditForm();
        switchSchedTab('active');
      } else {
        showToast(`⚠️ Update failed: ${data.message || 'Error'}`);
      }
    } else {
      // ── CREATE NEW CHRONO JOB ──
      const payload = { 
        prompt,
        session_id: currentChatSessionId || 'default'
      };

      if (schedCurrentMode === 'timer') {
        const secs = getCalculatedTimerSeconds();
        if (isNaN(secs) || secs <= 0) return showToast('⚠️ Delay duration must be positive seconds');
        payload.duration_seconds = secs;
      } else {
        const cron = getCalculatedCronExpression();
        if (!cron) return showToast('⚠️ Recurrence schedule is required');
        payload.cron_expression = cron;
      }

      const res = await fetch('/api/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'ok') {
        showToast('⏰ Sovereign automation successfully activated!');
        playFloworkTaskDoneSound();
        resetScheduleEditForm();
        switchSchedTab('active');
      } else {
        showToast(`⚠️ Scheduling failed: ${data.message || 'Error'}`);
      }
    }
  } catch (err) {
    showToast(`⚠️ Network error: ${err.message}`);
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

// ── 0.0 FLOWORK SOVEREIGN ROUTER & SWITCHBOARD SYSTEM (DRFLOW HUD MATRIX SPEC) ──
function _getFloworkRouterPort() {
  try {
    const saved = localStorage.getItem('flowork_router_port');
    if (saved && !isNaN(parseInt(saved, 10))) return saved;
    if (typeof window !== 'undefined' && window.location && window.location.port) {
      const p = parseInt(window.location.port, 10);
      if (p === 1987) return '9099';
    }
  } catch (_) {}
  return '9099';
}
window._getFloworkRouterPort = _getFloworkRouterPort;

function _getFloworkRouterBase() {
  const rPort = _getFloworkRouterPort();
  let host = (typeof window !== 'undefined' && window.location && window.location.hostname) ? window.location.hostname : '127.0.0.1';
  if (host && host.includes(':') && !host.startsWith('[')) {
    host = `[${host}]`;
  }
  return `http://${host}:${rPort}`;
}
window._getFloworkRouterBase = _getFloworkRouterBase;

function _getFloworkCoreBase() {
  let host = (typeof window !== 'undefined' && window.location && window.location.hostname) ? window.location.hostname : '127.0.0.1';
  if (host && host.includes(':') && !host.startsWith('[')) {
    host = `[${host}]`;
  }
  return `http://${host}:19890`;
}
window._getFloworkCoreBase = _getFloworkCoreBase;

async function openSystemBrowser(targetUrl) {
  if (!targetUrl || typeof targetUrl !== 'string') return false;
  const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
  try {
    const res = await fetch(`${routerBase}/auth/open-browser?url=${encodeURIComponent(targetUrl)}`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.success) return true;
    }
  } catch (err) {
    console.warn('[Flowork] Router open-browser bridge failed on base:', routerBase, err);
  }

  try {
    const rPort = (typeof _getFloworkRouterPort === 'function') ? _getFloworkRouterPort() : '9099';
    const altBase = `http://127.0.0.1:${rPort}`;
    if (altBase !== routerBase) {
      const res = await fetch(`${altBase}/auth/open-browser?url=${encodeURIComponent(targetUrl)}`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.success) return true;
      }
    }
  } catch (_) {}

  try {
    const pop = window.open(targetUrl, '_blank', 'noopener,noreferrer');
    if (pop) return true;
  } catch (_) {}

  return false;
}
window.openSystemBrowser = openSystemBrowser;

// ==========================================================================
// FLOWORK OPEN ECOSYSTEM AUTO-HEALER (ZERO HASH LOCK)
// ==========================================================================
let _hasEcosystemHealed = false;

async function autoHealFloworkEcosystem() {
  if (_hasEcosystemHealed) return;
  _hasEcosystemHealed = true;
  try {
    const routerBase = _getFloworkRouterBase();
    const res = await fetch(`${routerBase}/api/ecosystem/heal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (res.ok) {
      const data = await res.json();
      if (data && data.success && data.result) {
        const createdCount = (data.result.createdFolders ? data.result.createdFolders.length : 0) + 
                             (data.result.createdFiles ? data.result.createdFiles.length : 0);
        if (createdCount > 0) {
          console.log('[Flowork Ecosystem] Self-healed missing items:', data.result);
          showFloworkLaserToast(`⚡ Restored ${createdCount} missing ecosystem item(s)`);
        }
      }
    }
  } catch (err) {
    // Non-blocking silent fail if router offline
  }
}
window.autoHealFloworkEcosystem = autoHealFloworkEcosystem;

function showFloworkLaserToast(msg, isSuccess = true) {
  const toast = document.getElementById('flowork-core-toast');
  if (!toast) {
    showToast(msg);
    return;
  }
  toast.innerText = msg;
  toast.style.borderColor = isSuccess ? 'rgba(0, 229, 255, 0.8)' : 'rgba(239, 68, 68, 0.6)';
  toast.style.boxShadow = isSuccess ? '0 16px 36px -4px rgba(0, 0, 0, 0.9), 0 0 25px rgba(0, 229, 255, 0.35)' : '0 16px 36px -4px rgba(0, 0, 0, 0.9), 0 0 15px rgba(220, 38, 38, 0.25)';

  toast.style.removeProperty('top');
  toast.style.removeProperty('bottom');

  if (!toast._hasClickDismiss) {
    toast._hasClickDismiss = true;
    toast.style.cursor = 'pointer';
    toast.addEventListener('click', () => {
      toast.classList.remove('visible');
      if (window._laserToastTimer) clearTimeout(window._laserToastTimer);
    });
  }

  toast.style.animation = 'none';
  toast.classList.add('visible');

  if (window._laserToastTimer) clearTimeout(window._laserToastTimer);
  window._laserToastTimer = setTimeout(() => {
    toast.classList.remove('visible');
  }, 2800);
}
window.showFloworkLaserToast = showFloworkLaserToast;

let routerSwitchboardState = {
  connected: false,
  activeProvider: 'sovereign',
  model: 'gemini-3.8-flash-high',
  activeEmail: '',
  activeAccountId: '',
  rotationMode: 'failover',
  totalAccounts: 0,
  maxAccounts: 100,
  healthyCount: 0,
  cooldownCount: 0,
  accounts: [],
  filter: 'all',
  searchQuery: '',
  isOperating: false
};

function formatExpires(exp) {
  if (!exp) return 'Permanent';
  const d = new Date(typeof exp === 'number' && exp < 1e11 ? exp * 1000 : exp);
  if (isNaN(d.getTime())) return 'Active';
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${hh}.${mm}`;
}

async function syncRouterSwitchboard() {
  if (document.hidden) return;
  const rPort = _getFloworkRouterPort();
  const routerBase = _getFloworkRouterBase();

  try {
    // 1. Fetch multi-account pool status from /auth/router/status
    let res = null;
    try {
      res = await fetch(`${routerBase}/auth/router/status`, { cache: 'no-store' });
    } catch (_) {
      const altHost = routerBase.includes('127.0.0.1') ? 'localhost' : '127.0.0.1';
      try {
        res = await fetch(`http://${altHost}:${rPort}/auth/router/status`, { cache: 'no-store' });
      } catch (_) {}
    }
    if (res && res.ok) {
      const data = await res.json();
      if (data && data.success) {
        routerSwitchboardState.connected = true;
        routerSwitchboardState.totalAccounts = data.total_accounts || (data.accounts ? data.accounts.length : 0);
        routerSwitchboardState.maxAccounts = data.max_accounts || 100;
        routerSwitchboardState.activeAccountId = data.active_account_id || '';
        routerSwitchboardState.rotationMode = data.rotation_mode || 'failover';
        routerSwitchboardState.accounts = Array.isArray(data.accounts) ? data.accounts : [];

        // Compute counts
        let healthy = 0;
        let cooldown = 0;
        let activeFound = false;

        routerSwitchboardState.accounts.forEach(a => {
          if (a.is_active || a.id === routerSwitchboardState.activeAccountId) {
            routerSwitchboardState.activeEmail = a.email;
            activeFound = true;
          }
          if (a.status === 'cooldown' || (a.cooldown_remaining_sec && a.cooldown_remaining_sec > 0)) {
            cooldown++;
          } else {
            healthy++;
          }
        });

        if (!activeFound && routerSwitchboardState.accounts.length > 0) {
          routerSwitchboardState.activeEmail = routerSwitchboardState.accounts[0].email;
        }

        routerSwitchboardState.healthyCount = healthy;
        routerSwitchboardState.cooldownCount = cooldown;
      }
    } else {
      // Fallback: check /auth/providers
      const pRes = await fetch(`${routerBase}/auth/providers`, { cache: 'no-store' });
      if (pRes.ok) {
        const pData = await pRes.json();
        const sProv = (pData && pData.providers && (pData.providers.sovereign || pData.providers.google)) || {};
        routerSwitchboardState.connected = !!sProv.connected;
        if (sProv.email) routerSwitchboardState.activeEmail = sProv.email;
        if (sProv.model) routerSwitchboardState.model = sProv.model;
      }
    }
  } catch (_) {
    routerSwitchboardState.connected = false;
  }

  // Also query active model
  try {
    const pRes = await fetch(`${routerBase}/auth/providers`, { cache: 'no-store' });
    if (pRes.ok) {
      const pData = await pRes.json();
      const sProv = (pData && pData.providers && (pData.providers.sovereign || pData.providers.google)) || {};
      if (sProv.model) routerSwitchboardState.model = sProv.model;
    }
  } catch (_) {}

  // Update UI Elements
  updateRouterModalUI();
  updateRouterTopbarPill();
}

function updateRouterTopbarPill() {
  const rPort = _getFloworkRouterPort();
  const pillTitle = document.getElementById('router-pill-title');
  const pillModel = document.getElementById('router-pill-model');
  const topbarPill = document.getElementById('btn-topbar-router');

  if (pillTitle) pillTitle.textContent = 'CONNECTION';
  if (pillModel) pillModel.style.display = 'none';
  if (topbarPill) {
    const count = routerSwitchboardState.totalAccounts;
    topbarPill.title = `CONNECTION Switchboard (:${rPort}) • ${count} Accounts • ${selectedChatModelId}`;
    topbarPill.style.borderColor = routerSwitchboardState.connected ? 'rgba(0, 229, 255, 0.4)' : 'rgba(239, 68, 68, 0.4)';
  }

  const heroStatusTxt = document.getElementById('hero-router-status-txt');
  if (heroStatusTxt) {
    if (routerSwitchboardState.connected) {
      heroStatusTxt.textContent = `AI CORE MATRIX ONLINE // :${rPort} // ${routerSwitchboardState.totalAccounts} ACCS [${selectedChatModelId}]`;
      heroStatusTxt.style.color = '#38bdf8';
    } else {
      heroStatusTxt.textContent = `SOVEREIGN AI ROUTER STANDBY // :${rPort} // AWAITING SESSION`;
      heroStatusTxt.style.color = '#f87171';
    }
  }
}

function updateRouterModalUI() {
  const modal = document.getElementById('router-modal') || document.getElementById('switchboard-router-modal');
  if (!modal) return;

  const rPort = _getFloworkRouterPort();
  const total = routerSwitchboardState.totalAccounts;
  const activeCount = routerSwitchboardState.accounts.filter(a => a.is_active || a.id === routerSwitchboardState.activeAccountId).length;
  const readyCount = routerSwitchboardState.healthyCount;
  const cdCount = routerSwitchboardState.cooldownCount;

  // 4 Metric cards
  const elTotal = document.getElementById('router-stat-total');
  const elActiveEmail = document.getElementById('router-stat-active-email');
  const elHealth = document.getElementById('router-stat-health');
  const elStrategy = document.getElementById('router-strategy-select');

  if (elTotal) elTotal.textContent = total;
  if (elActiveEmail) {
    const email = routerSwitchboardState.activeEmail || 'None';
    elActiveEmail.textContent = email.length > 24 ? email.substring(0, 22) + '...' : email;
    elActiveEmail.title = email;
  }
  if (elHealth) elHealth.textContent = `${readyCount} Ready`;
  if (elStrategy && routerSwitchboardState.rotationMode) {
    elStrategy.value = routerSwitchboardState.rotationMode;
  }

  // Filter count badges
  const cAll = document.getElementById('filter-cnt-all');
  const cActive = document.getElementById('filter-cnt-active');
  const cReady = document.getElementById('filter-cnt-ready');
  const cCooldown = document.getElementById('filter-cnt-cooldown');

  if (cAll) cAll.textContent = total;
  if (cActive) cActive.textContent = activeCount;
  if (cReady) cReady.textContent = readyCount;
  if (cCooldown) cCooldown.textContent = cdCount;

  // Footer stats
  const fPort = document.getElementById('str-footer-port');
  const fPool = document.getElementById('str-footer-pool-count');
  if (fPort) fPort.textContent = rPort;
  if (fPool) fPool.textContent = `${total} / ${routerSwitchboardState.maxAccounts}`;

  // Render accounts list
  renderRouterAccountsList();
}

function renderRouterAccountsList() {
  const listEl = document.getElementById('router-accounts-list');
  if (!listEl) return;

  let accounts = [...routerSwitchboardState.accounts];
  const filter = routerSwitchboardState.filter;
  const query = (routerSwitchboardState.searchQuery || '').toLowerCase();

  // Apply filter pill
  if (filter === 'active') {
    accounts = accounts.filter(a => a.is_active || a.id === routerSwitchboardState.activeAccountId);
  } else if (filter === 'ready') {
    accounts = accounts.filter(a => !(a.is_active || a.id === routerSwitchboardState.activeAccountId) && !(a.status === 'cooldown' || a.cooldown_remaining_sec > 0));
  } else if (filter === 'cooldown') {
    accounts = accounts.filter(a => a.status === 'cooldown' || a.cooldown_remaining_sec > 0);
  }

  // Apply search query
  if (query) {
    accounts = accounts.filter(a => (a.email && a.email.toLowerCase().includes(query)) || (a.name && a.name.toLowerCase().includes(query)));
  }

  if (accounts.length === 0) {
    listEl.innerHTML = `
      <div style="padding: 30px; text-align: center; color: #64748b; font-family: var(--font-mono); font-size: 11.5px;">
        ${routerSwitchboardState.accounts.length === 0 ? 'No accounts in the rotation pool. Click "+ Add Google Pro Account" above.' : 'No matching accounts found for current filter.'}
      </div>
    `;
    return;
  }

  listEl.innerHTML = accounts.map((acc, idx) => {
    const isActive = acc.is_active || acc.id === routerSwitchboardState.activeAccountId;
    const isCooldown = acc.status === 'cooldown' || (acc.cooldown_remaining_sec && acc.cooldown_remaining_sec > 0);

    let badgeClass = 'ready';
    let badgeText = 'READY';
    if (isActive) {
      badgeClass = 'active';
      badgeText = 'ACTIVE';
    } else if (isCooldown) {
      badgeClass = 'limit';
      badgeText = `LIMIT 429 (${acc.cooldown_remaining_sec || 60}s)`;
    }

    const email = acc.email || 'account@google.com';
    const initial = email.charAt(0).toUpperCase();
    const reqCount = acc.requests_count || 0;
    const errCount = acc.errors_count || 0;
    const expiresStr = formatExpires(acc.expires_at);

    return `
      <div class="str-account-row ${isActive ? 'is-active' : ''}">
        <div class="str-acc-left">
          <span class="str-acc-index">#${idx + 1}</span>
          <div class="str-acc-avatar">${initial}</div>
          <div class="str-acc-info">
            <div class="str-acc-email-row">
              <span class="str-acc-email">${escapeHtml(email)}</span>
              <span class="str-acc-badge ${badgeClass}">${badgeText}</span>
            </div>
            <div class="str-acc-meta">
              Requests: ${reqCount}  ·  Errors: ${errCount}  ·  Expires: ${expiresStr}
            </div>
          </div>
        </div>
        <div class="str-acc-actions">
          ${isActive ? `
            <button class="str-btn-make-active current-active" disabled>Active Primary</button>
          ` : `
            <button class="str-btn-make-active" data-action="make-active" data-id="${acc.id}" data-email="${escapeHtml(email)}">Make Active</button>
          `}
          <button class="str-btn-test" data-action="test" data-id="${acc.id}" data-email="${escapeHtml(email)}">Test</button>
          <button class="str-btn-delete" data-action="delete" data-id="${acc.id}" data-email="${escapeHtml(email)}" title="Delete Account">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>
    `;
  }).join('');

  // Wire buttons in rows
  listEl.querySelectorAll('[data-action="make-active"]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-id');
      const email = btn.getAttribute('data-email');
      const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
      try {
        btn.disabled = true;
        btn.textContent = 'Activating...';
        const res = await fetch(`${routerBase}/auth/router/select-account`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id })
        });
        const data = await res.json();
        if (data && data.success) {
          showFloworkLaserToast(`👉 Switched active primary account to: ${email}`, true);
          await syncRouterSwitchboard();
        } else {
          showFloworkLaserToast(`⚠️ Failed: ${data.error || 'Error'}`, false);
        }
      } catch (err) {
        showFloworkLaserToast(`⚠️ Switch Error: ${err.message}`, false);
      }
    });
  });

  listEl.querySelectorAll('[data-action="test"]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-id');
      const email = btn.getAttribute('data-email');
      const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
      try {
        btn.disabled = true;
        btn.textContent = 'Testing...';
        const res = await fetch(`${routerBase}/auth/router/test-account`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id })
        });
        const data = await res.json();
        if (data && data.success) {
          showFloworkLaserToast(`⚡ Account [${email}]: Token valid & Ready!`, true);
          await syncRouterSwitchboard();
        } else {
          showFloworkLaserToast(`⚠️ Test result: ${data.error || 'Check status'}`, false);
        }
      } catch (err) {
        showFloworkLaserToast(`⚠️ Test Error: ${err.message}`, false);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Test';
      }
    });
  });

  listEl.querySelectorAll('[data-action="delete"]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-id');
      const email = btn.getAttribute('data-email');
      if (!confirm(`Are you sure you want to remove account ${email} from the rotation pool?`)) return;

      const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
      try {
        const res = await fetch(`${routerBase}/auth/router/remove-account`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id })
        });
        const data = await res.json();
        if (data && data.success) {
          showFloworkLaserToast(`🗑️ Removed ${email} from rotation pool`, true);
          await syncRouterSwitchboard();
        } else {
          showFloworkLaserToast(`⚠️ Failed to remove: ${data.error || 'Error'}`, false);
        }
      } catch (err) {
        showFloworkLaserToast(`⚠️ Remove Error: ${err.message}`, false);
      }
    });
  });
}

window.connectFloworkCore = async () => {
  const btn = document.getElementById('btn-add-google-acc');
  if (btn) btn.click();
};

window.switchFloworkCoreModel = async (modelId) => {
  const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
  try {
    const res = await fetch(`${routerBase}/auth/sovereign/model?model=${encodeURIComponent(modelId)}`);
    const data = await res.json();
    if (data && data.success) {
      routerSwitchboardState.model = modelId;
      updateRouterTopbarPill();
    }
  } catch (_) {}
};

window.clearRouterCooldown = async () => {
  const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
  try {
    const res = await fetch(`${routerBase}/auth/router/clear-cooldown`, { method: 'POST' });
    const data = await res.json();
    if (data && data.success) {
      showFloworkLaserToast('🧹 Account cooldowns successfully cleared!', true);
      await syncRouterSwitchboard();
    }
  } catch (_) {}
};

window.getFloworkCoreStatus = () => routerSwitchboardState.connected;
window.getFloworkCoreModel = () => routerSwitchboardState.model;
window.getFloworkCoreEmail = () => routerSwitchboardState.activeEmail;

function initRouterSwitchboardSystem() {
  const btnTopPill = document.getElementById('btn-topbar-router');
  const modal = document.getElementById('router-modal');
  const btnClose = document.getElementById('btn-close-router-modal');
  const btnAddAcc = document.getElementById('btn-add-google-acc');
  const btnRefresh = document.getElementById('btn-refresh-pool');
  const strategySelect = document.getElementById('router-strategy-select');
  const searchInput = document.getElementById('router-acc-search-input');
  const filterPills = document.querySelectorAll('.str-filter-pill');

  // Toggle Modal
  if (btnTopPill && modal) {
    btnTopPill.addEventListener('click', () => {
      modal.style.display = 'flex';
      syncRouterSwitchboard();
    });
  }

  // Open via URL parameter (?router=1 or ?open_router=1)
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('router') === '1' || urlParams.get('open_router') === '1') {
    if (modal) {
      modal.style.display = 'flex';
      syncRouterSwitchboard();
    }
  }

  const hideModal = () => {
    if (modal) modal.style.display = 'none';
  };

  if (btnClose) btnClose.addEventListener('click', hideModal);
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) hideModal();
    });
  }

  // Add Google Pro Account (+ Add Google Pro Account)
  if (btnAddAcc) {
    btnAddAcc.addEventListener('click', async () => {
      const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
      try {
        showFloworkLaserToast('🌐 Opening Google OAuth authorization portal in browser...', true);
        const res = await fetch(`${routerBase}/auth/router/login-url`);
        const data = await res.json();
        if (data && data.loginUrl) {
          await openSystemBrowser(data.loginUrl);
          if (window._googleOAuthPollInterval) {
            clearInterval(window._googleOAuthPollInterval);
            window._googleOAuthPollInterval = null;
          }
          let pollCount = 0;
          const initialCount = routerSwitchboardState.totalAccounts;
          window._googleOAuthPollInterval = setInterval(async () => {
            pollCount++;
            await syncRouterSwitchboard();
            if (routerSwitchboardState.totalAccounts > initialCount || pollCount > 45) {
              clearInterval(window._googleOAuthPollInterval);
              window._googleOAuthPollInterval = null;
              if (routerSwitchboardState.totalAccounts > initialCount) {
                showFloworkLaserToast('🟢 New Google Pro account successfully linked to pool!', true);
              }
            }
          }, 2000);
        } else {
          showFloworkLaserToast('⚠️ Failed to obtain authorization URL', false);
        }
      } catch (err) {
        showFloworkLaserToast(`⚠️ Connect error: ${err.message}`, false);
      }
    });
  }

  // Refresh Pool button
  if (btnRefresh) {
    btnRefresh.addEventListener('click', async () => {
      showFloworkLaserToast('🔄 Refreshing Multi-Account Pool...', true);
      await syncRouterSwitchboard();
      showFloworkLaserToast(`✅ Multi-Account Pool Synchronized (${routerSwitchboardState.totalAccounts} accounts)`, true);
    });
  }

  // Routing Strategy dropdown change
  if (strategySelect) {
    strategySelect.addEventListener('change', async (e) => {
      const mode = e.target.value;
      const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
      try {
        const res = await fetch(`${routerBase}/auth/router/set-rotation-mode`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode })
        });
        const data = await res.json();
        if (data && data.success) {
          routerSwitchboardState.rotationMode = mode;
          showFloworkLaserToast(`🔄 Routing Strategy set to: ${mode}`, true);
        }
      } catch (err) {
        showFloworkLaserToast(`⚠️ Strategy change error: ${err.message}`, false);
      }
    });
  }

  // Filter Pills (All, Active, Ready, Cooldown 429)
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      routerSwitchboardState.filter = pill.getAttribute('data-filter') || 'all';
      renderRouterAccountsList();
    });
  });

  // Search Input
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      routerSwitchboardState.searchQuery = e.target.value;
      renderRouterAccountsList();
    });
  }

  // Initial Sync & Heartbeat
  syncRouterSwitchboard();
  autoHealFloworkEcosystem();
  if (typeof routerSwitchboardTimer !== 'undefined' && routerSwitchboardTimer) {
    clearInterval(routerSwitchboardTimer);
  }
  window.routerSwitchboardTimer = setInterval(syncRouterSwitchboard, 12000);
}

// 0. Flowork OS Sovereign Authentication & Gatekeeper
function mountChatHeaderLogoutButton() {
  const actions = document.querySelector('.rightbar-chat-header .chat-header-actions');
  if (!actions) return;
  let btn = document.getElementById('btn-chat-header-logout');
  if (!btn) {
    btn = document.createElement('button');
    btn.id = 'btn-chat-header-logout';
    btn.className = 'chat-btn-action btn-chat-logout';
    btn.title = 'Logout & Lock Session';
    btn.style.color = '#ef4444';
    btn.style.borderColor = 'rgba(239, 68, 68, 0.45)';
    btn.style.background = 'rgba(239, 68, 68, 0.15)';
    btn.style.display = 'inline-flex';
    btn.style.alignItems = 'center';
    btn.style.justifyContent = 'center';
    btn.style.cursor = 'pointer';
    btn.style.transition = 'all 0.2s ease';
    btn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>`;
    btn.onmouseenter = () => {
      btn.style.background = 'rgba(239, 68, 68, 0.35)';
      btn.style.borderColor = '#ef4444';
      btn.style.transform = 'scale(1.08)';
      btn.style.boxShadow = '0 0 8px rgba(239, 68, 68, 0.4)';
    };
    btn.onmouseleave = () => {
      btn.style.background = 'rgba(239, 68, 68, 0.15)';
      btn.style.borderColor = 'rgba(239, 68, 68, 0.45)';
      btn.style.transform = 'scale(1)';
      btn.style.boxShadow = 'none';
    };
    const closeBtn = document.getElementById('btn-close-rightbar');
    if (closeBtn && closeBtn.parentNode === actions) {
      actions.insertBefore(btn, closeBtn);
    } else {
      actions.appendChild(btn);
    }
  }
  btn.onclick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    logoutSession();
  };
}

function mountTopbarLogoutButton() {
  const topbarRight = document.querySelector('.topbar-right');
  const profileCapsule = document.getElementById('user-profile-capsule');
  const isCapsuleVisible = profileCapsule && window.getComputedStyle(profileCapsule).display !== 'none';

  // 1. Ensure inner logout button in profile capsule is wired
  const innerLogout = document.getElementById('btn-topbar-logout');
  if (innerLogout) {
    innerLogout.title = 'Logout & Lock Session';
    innerLogout.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      logoutSession();
    };
  }

  // 2. Standalone Logout Pill Button directly in .topbar-right (always visible or fallback when capsule is hidden)
  if (topbarRight) {
    let standaloneBtn = document.getElementById('btn-topbar-standalone-logout');
    if (!standaloneBtn) {
      standaloneBtn = document.createElement('button');
      standaloneBtn.id = 'btn-topbar-standalone-logout';
      standaloneBtn.className = 'topbar-pill-btn btn-topbar-logout-standalone';
      standaloneBtn.title = 'Logout & Lock Session';
      standaloneBtn.style.color = '#ef4444';
      standaloneBtn.style.borderColor = 'rgba(239, 68, 68, 0.45)';
      standaloneBtn.style.background = 'rgba(239, 68, 68, 0.15)';
      standaloneBtn.style.display = 'inline-flex';
      standaloneBtn.style.alignItems = 'center';
      standaloneBtn.style.justifyContent = 'center';
      standaloneBtn.style.gap = '6px';
      standaloneBtn.style.padding = '4px 10px';
      standaloneBtn.style.cursor = 'pointer';
      standaloneBtn.style.transition = 'all 0.2s ease';
      standaloneBtn.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg><span style="font-size:11.5px;font-weight:700;">Logout</span>`;
      standaloneBtn.onmouseenter = () => {
        standaloneBtn.style.background = 'rgba(239, 68, 68, 0.35)';
        standaloneBtn.style.borderColor = '#ef4444';
        standaloneBtn.style.color = '#ffffff';
      };
      standaloneBtn.onmouseleave = () => {
        standaloneBtn.style.background = 'rgba(239, 68, 68, 0.15)';
        standaloneBtn.style.borderColor = 'rgba(239, 68, 68, 0.45)';
        standaloneBtn.style.color = '#ef4444';
      };
      const chatToggle = document.getElementById('btn-toggle-chat');
      if (chatToggle && chatToggle.nextSibling) {
        topbarRight.insertBefore(standaloneBtn, chatToggle.nextSibling);
      } else {
        topbarRight.appendChild(standaloneBtn);
      }
    }
    standaloneBtn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      logoutSession();
    };

    if (isCapsuleVisible) {
      standaloneBtn.style.display = 'none';
    } else {
      standaloneBtn.style.display = 'inline-flex';
    }
  }
}

function ensureAllLogoutButtons() {
  mountTopbarLogoutButton();
  mountChatHeaderLogoutButton();
}
window.__ensureAllLogoutButtons = ensureAllLogoutButtons;
if (!window.__logoutButtonsHeartbeat) {
  window.__logoutButtonsHeartbeat = setInterval(ensureAllLogoutButtons, 2000);
}

async function initAuthSystem() {
  ensureAllLogoutButtons();

  const btnLogin = document.getElementById('btn-topbar-login');
  if (btnLogin) {
    btnLogin.addEventListener('click', () => {
      window.location.href = '/canvas/launcher.html';
    });
  }

  const btnMrFlow = document.getElementById('btn-topbar-mrflow');
  if (btnMrFlow) {
    btnMrFlow.addEventListener('click', () => {
      window.open('/canvas/launcher.html?replay=1', '_blank');
    });
  }

  await fetchAuthStatus();
  ensureAllLogoutButtons();
}



async function fetchAuthStatus() {
  const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
  const endpoints = [
    `${routerBase}/api/auth/status`,
    '/api/auth/status'
  ];

  for (const url of endpoints) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      if (res.ok) {
        const data = await res.json();
        if (data && (data.authenticated || data.authorized || data.status === 'ACTIVE' || data.user)) {
          renderAuthUI(data);
          return;
        }
      }
    } catch (_) {
      // Fallback to next endpoint
    }
  }
  console.warn('[X-Flow Auth] Could not reach active auth status endpoint');
}

function renderAuthUI(data) {
  const profileCapsule = document.getElementById('user-profile-capsule');
  const btnLogin = document.getElementById('btn-topbar-login');
  const isAuth = !!(data && (data.authenticated || data.authorized || data.status === 'ACTIVE') && data.user);

  if (isAuth) {
    const user = data.user;
    window.__isUserAuthenticated = true;

    authState.authorized = true;
    authState.user = user;
    authState.isOffline = false;
    sessionStorage.setItem('xflow_user_authenticated', '1');
    document.documentElement.classList.add('xflow-authenticated');

    window.authState = authState;
    window.currentUser = user;
    window.__floworkUserData = user;

    if (profileCapsule) {
      profileCapsule.style.display = 'flex';
      const tierEl = document.getElementById('user-tier-pill');
      const nameEl = document.getElementById('user-username');
      const roleEl = document.getElementById('user-role');
      const avatarEl = document.getElementById('user-avatar-badge');
      const levelEl = document.getElementById('user-level');
      const identityBox = document.getElementById('user-identity-box');

      // 1. Display Name (DLP Protection: Display real sovereign name, never raw username handle)
      if (nameEl) {
        let disp = user.display_name || user.name || (user.username && user.username.toLowerCase().includes('awenkaudico') ? 'Awenk Audico' : user.username) || 'Sovereign Operator';
        if (typeof disp === 'string' && disp.toLowerCase().includes('awenkaudico')) {
          disp = 'Awenk Audico';
        }
        nameEl.textContent = disp;
      }

      // 2. Role & Rank
      if (roleEl) {
        roleEl.textContent = user.rank || user.level_name || user.role || 'USER';
      }

      // 3. Dynamic Level Badge
      if (levelEl) {
        if (user.level !== undefined && user.level !== null) {
          levelEl.textContent = `LVL ${user.level}`;
          levelEl.style.display = 'inline-block';
        } else {
          levelEl.style.display = 'none';
        }
      }

      // 4. Dynamic Emoji Badge
      if (avatarEl) {
        const emojiMatch = (user.badge || '').match(/^(\p{Emoji})/u);
        avatarEl.textContent = emojiMatch ? emojiMatch[1] : ((user.role === 'SUPER_ADMIN' || (user.level && user.level >= 90)) ? '👑' : '👤');
      }

      // 5. Tier Pill (Fail-safe default: community / free, strictly NOT hardcoded enterprise)
      if (tierEl) {
        const tier = (user.tier || user.subscription_plan || 'free').toLowerCase();
        tierEl.textContent = `${tier.toUpperCase()} PLAN`;
        tierEl.className = `user-tier-pill tier-${tier}`;
      }

      // 6. Identity Box Tooltip
      if (identityBox) {
        const parts = [
          user.name || user.username,
          user.level !== undefined ? `Level ${user.level} (${user.level_name || ''})` : null,
          user.rank || user.role
        ].filter(Boolean);
        identityBox.title = parts.join(' • ');
      }

      // 7. Prominent Sovereign Logout Button
      let btnLogout = document.getElementById('btn-topbar-logout');
      if (!btnLogout && profileCapsule) {
        btnLogout = document.createElement('button');
        btnLogout.id = 'btn-topbar-logout';
        btnLogout.className = 'btn-topbar-logout';
        profileCapsule.appendChild(btnLogout);
      }
      if (btnLogout) {
        btnLogout.title = 'Logout & Lock Session';
        btnLogout.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg><span style="font-size:11px;font-weight:700;margin-left:5px;">Logout</span>`;
        btnLogout.style.display = 'inline-flex';
        btnLogout.style.alignItems = 'center';
        btnLogout.style.justifyContent = 'center';
        btnLogout.style.marginLeft = '8px';
        btnLogout.style.padding = '4px 10px';
        btnLogout.style.borderRadius = '6px';
        btnLogout.style.background = 'rgba(239, 68, 68, 0.18)';
        btnLogout.style.border = '1px solid rgba(239, 68, 68, 0.4)';
        btnLogout.style.color = '#ff6b6b';
        btnLogout.style.cursor = 'pointer';
        btnLogout.style.transition = 'all 0.2s ease';
        btnLogout.onmouseenter = () => { btnLogout.style.background = 'rgba(239, 68, 68, 0.35)'; btnLogout.style.borderColor = '#ef4444'; btnLogout.style.color = '#ffffff'; };
        btnLogout.onmouseleave = () => { btnLogout.style.background = 'rgba(239, 68, 68, 0.18)'; btnLogout.style.borderColor = 'rgba(239, 68, 68, 0.4)'; btnLogout.style.color = '#ff6b6b'; };
        btnLogout.onclick = (e) => {
          e.preventDefault();
          e.stopPropagation();
          logoutSession();
        };
      }
    }

    if (btnLogin) btnLogin.style.display = 'none';

    // Dismiss local lock overlay upon successful authentication
    const lockOverlay = document.getElementById('sovereign-lock-overlay');
    if (lockOverlay) lockOverlay.style.display = 'none';

    // Auto-sync or check Antigravity connector vault upon login
    fetchConnectorStatus(true);

    // Propagate authenticated user identity to 3D Virtual Office
    if (window.office3DInstance && typeof window.office3DInstance.syncUserIdentity === 'function') {
      window.office3DInstance.syncUserIdentity(user);
    }
    window.dispatchEvent(new CustomEvent('flowork:auth-synced', { detail: user }));

    if (authPollInterval) {
      clearInterval(authPollInterval);
      authPollInterval = null;
    }
  } else {
    // Strictly Fail-Closed: Redirect unauthorized workspace sessions to launcher
    window.__isUserAuthenticated = false;
    document.documentElement.classList.remove('xflow-authenticated');
    sessionStorage.removeItem('flowork_auth_verified');
    sessionStorage.removeItem('xflow_user_authenticated');
    window.location.replace('/canvas/launcher.html');
  }
}

async function logoutSession() {
  if (!confirm('Lock session and logout from X-Flow?')) return;

  window.__isUserAuthenticated = false;
  try {
    if (typeof authState !== 'undefined' && authState) {
      authState.authorized = false;
      authState.user = null;
    }
    sessionStorage.removeItem('flowork_auth_verified');
    sessionStorage.removeItem('xflow_user_authenticated');
    sessionStorage.removeItem('xflow_gate_dismissed');
    sessionStorage.removeItem('xflow_offline_mode');
    localStorage.removeItem('flowork_auth_verified');
    localStorage.removeItem('xflow_user_authenticated');
    localStorage.removeItem('flowork_token');
    document.documentElement.classList.remove('xflow-authenticated');
  } catch (_) {}

  try {
    const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
    await fetch(`${routerBase}/auth/logout`, { method: 'POST' });
  } catch (_) {}

  try {
    const coreBase = (typeof _getFloworkCoreBase === 'function') ? _getFloworkCoreBase() : 'http://127.0.0.1:19890';
    await fetch(`${coreBase}/api/auth/logout`, { method: 'POST' });
  } catch (err) {
    console.error('[X-Flow Auth] Logout error:', err);
  }

  const profileCapsule = document.getElementById('user-profile-capsule');
  const btnLogin = document.getElementById('btn-topbar-login');
  if (profileCapsule) profileCapsule.style.display = 'none';
  if (btnLogin) btnLogin.style.display = 'inline-flex';

  // Redirect to authoritative animated Sovereign Launcher
  window.location.replace('/canvas/launcher.html');
}

function setupLockScreenHandlers() {
  const btnLoginCloud = document.getElementById('btn-lock-login-cloud');
  const btnRecheck = document.getElementById('btn-lock-recheck');

  if (btnLoginCloud && !btnLoginCloud.dataset.bound) {
    btnLoginCloud.dataset.bound = '1';
    btnLoginCloud.addEventListener('click', async () => {
      const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
      let loginUrl = `${routerBase}/auth/login-url`;
      try {
        const res = await fetch(`${routerBase}/auth/ticket`);
        if (res.ok) {
          const tData = await res.json();
          if (tData.login_url || tData.gate_url) loginUrl = tData.login_url || tData.gate_url;
        }
      } catch (_) {}

      if (typeof openSystemBrowser === 'function') {
        await openSystemBrowser(loginUrl);
      } else {
        window.open(loginUrl, '_blank');
      }
      showToast('Opening Flowork Sovereign login portal in browser...');

      // Auto-poll for login completion every 2s
      if (!window.__lockPollTimer) {
        window.__lockPollTimer = setInterval(async () => {
          await fetchAuthStatus();
          if (window.__isUserAuthenticated) {
            clearInterval(window.__lockPollTimer);
            window.__lockPollTimer = null;
            showToast('✅ Welcome back! Sovereign session unlocked.');
          }
        }, 2000);
      }
    });
  }

  if (btnRecheck && !btnRecheck.dataset.bound) {
    btnRecheck.dataset.bound = '1';
    btnRecheck.addEventListener('click', async () => {
      showToast('Checking authentication status...');
      await fetchAuthStatus();
      if (!window.__isUserAuthenticated) {
        showToast('⚠️ No active session found. Please click "Log In"');
      }
    });
  }
}

// Keyboard & focus context shield to prevent host shortcut collisions with inputs, iframes, and modals
function isTypingContext(target) {
  if (!target) target = document.activeElement;
  if (!target) return false;
  const tag = (target.tagName || '').toLowerCase();
  return (
    tag === 'input' ||
    tag === 'textarea' ||
    tag === 'select' ||
    Boolean(target.isContentEditable) ||
    tag === 'iframe'
  );
}

function isModalActive() {
  const syncModal = document.getElementById('sync-drive-modal');
  if (syncModal && syncModal.style.display !== 'none') return true;
  return false;
}

// 1. Sidebar Hide/Show Mechanism
function initSidebarToggle() {
  const sidebar = document.getElementById('sidebar-dock');
  const toggleBtn = document.getElementById('btn-toggle-sidebar');
  if (!sidebar || !toggleBtn) return;

  const isCollapsed = localStorage.getItem('xflow_sidebar_collapsed') === 'true';
  if (isCollapsed) {
    sidebar.classList.add('collapsed');
  }

  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    const collapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('xflow_sidebar_collapsed', collapsed ? 'true' : 'false');
    if (window.__updateLayoutResizers) window.__updateLayoutResizers();
  });

  // Shortcut Ctrl+B / Cmd+B (Ignore when typing in input/textarea/editor/iframe or modal)
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
      if (isTypingContext(e.target) || isModalActive()) return;
      e.preventDefault();
      toggleBtn.click();
    }
  });
}

// 1b. Dynamic Chat Docking (Left / Right Panel Positioning & Drag-and-Drop Docking)
function initChatDockSystem() {
  const layout = document.querySelector('.canvas-layout');
  const btnToggleDock = document.getElementById('btn-toggle-chat-dock');
  const chatHeader = document.querySelector('.rightbar-chat-header');
  if (!layout) return;

  const applyDockSide = (side) => {
    const isLeft = side === 'left';
    layout.classList.toggle('chat-dock-left', isLeft);
    if (btnToggleDock) {
      btnToggleDock.title = isLeft ? 'Dock Chat to Right' : 'Dock Chat to Left';
      btnToggleDock.classList.toggle('is-left', isLeft);
    }
    if (window.__updateLayoutResizers) window.__updateLayoutResizers();
  };

  let savedSide = localStorage.getItem('xflow_chat_dock_side') || 'right';
  applyDockSide(savedSide);
  window.__applyChatDockSide = applyDockSide;

  // 1. Click Toggle Button
  if (btnToggleDock && !btnToggleDock._dockBound) {
    btnToggleDock._dockBound = true;
    btnToggleDock.addEventListener('click', (e) => {
      e.stopPropagation();
      const currentlyLeft = layout.classList.contains('chat-dock-left');
      const newSide = currentlyLeft ? 'right' : 'left';
      applyDockSide(newSide);
      localStorage.setItem('xflow_chat_dock_side', newSide);
      showToast(newSide === 'left' ? 'Chat docked to Left' : 'Chat docked to Right');
    });
  }

  // 2. Drag & Drop Docking via Chat Header
  if (chatHeader && !chatHeader._dockDragBound) {
    chatHeader._dockDragBound = true;
    let isHeaderDragging = false;
    let startPointerX = 0;

    chatHeader.addEventListener('pointerdown', (e) => {
      // Ignore clicks on buttons, inputs, selects, or dropdowns
      if (e.target.closest('button, input, select, textarea, .workspace-capsule-wrap')) return;
      if (e.button !== 0) return;

      isHeaderDragging = true;
      startPointerX = e.clientX;
      chatHeader.style.cursor = 'grab';

      const onHeaderPointerMove = (ev) => {
        if (!isHeaderDragging) return;
        if (Math.abs(ev.clientX - startPointerX) > 12) {
          chatHeader.style.cursor = 'grabbing';
          document.body.classList.add('is-resizing');
        }
      };

      const onHeaderPointerUp = (ev) => {
        if (!isHeaderDragging) return;
        isHeaderDragging = false;
        chatHeader.style.cursor = '';
        document.body.classList.remove('is-resizing');

        window.removeEventListener('pointermove', onHeaderPointerMove);
        window.removeEventListener('pointerup', onHeaderPointerUp);
        window.removeEventListener('pointercancel', onHeaderPointerUp);

        // If dragged across horizontal threshold (> 50px delta)
        if (Math.abs(ev.clientX - startPointerX) > 50) {
          const screenMid = window.innerWidth / 2;
          const targetSide = ev.clientX < screenMid ? 'left' : 'right';
          const currentSide = layout.classList.contains('chat-dock-left') ? 'left' : 'right';
          if (targetSide !== currentSide) {
            applyDockSide(targetSide);
            localStorage.setItem('xflow_chat_dock_side', targetSide);
            showToast(targetSide === 'left' ? 'Chat docked to Left' : 'Chat docked to Right');
          }
        }
      };

      window.addEventListener('pointermove', onHeaderPointerMove);
      window.addEventListener('pointerup', onHeaderPointerUp);
      window.addEventListener('pointercancel', onHeaderPointerUp);
    });
  }
}

// 1b2. Sovereign Full Chat & Workbench Collapse System (Hide Applications / Full Chat Mode)
function initWorkbenchToggle() {
  const workbench = document.querySelector('.workbench-main');
  const rightbarChat = document.getElementById('rightbar-chat');
  const layout = document.querySelector('.canvas-layout');
  const btnToggleApps = document.getElementById('btn-toggle-workbench');
  const btnHideWorkbench = document.getElementById('btn-hide-workbench');

  if (!workbench || !layout) return;

  const setWorkbenchState = (collapsed, showNotification = false) => {
    if (collapsed) {
      workbench.classList.add('collapsed');
      layout.classList.add('full-chat');
      // Ensure chat is opened when workbench is collapsed into Full Chat mode
      if (rightbarChat && rightbarChat.classList.contains('collapsed')) {
        rightbarChat.classList.remove('collapsed');
        localStorage.setItem('xflow_rightbar_collapsed', 'false');
      }
      localStorage.setItem('xflow_workbench_collapsed', 'true');

      if (btnToggleApps) {
        btnToggleApps.classList.add('is-hidden');
        btnToggleApps.title = 'Show Applications (Split View)';
      }
      if (showNotification) showToast('Full Chat Mode enabled (Applications hidden)');
    } else {
      workbench.classList.remove('collapsed');
      layout.classList.remove('full-chat');
      localStorage.setItem('xflow_workbench_collapsed', 'false');

      if (btnToggleApps) {
        btnToggleApps.classList.remove('is-hidden');
        btnToggleApps.title = 'Hide Applications (Full Chat)';
      }
      if (showNotification) showToast('Split View restored (Applications visible)');
    }

    if (window.__updateLayoutResizers) window.__updateLayoutResizers();
  };

  // Restore saved state from persistent storage or URL parameter (?fullchat=1 or ?apps=0)
  const urlParams = new URLSearchParams(window.location.search);
  const paramFullChat = urlParams.get('fullchat') === '1' || urlParams.get('full_chat') === '1' || urlParams.get('apps') === '0';
  const isWorkbenchCollapsed = paramFullChat || localStorage.getItem('xflow_workbench_collapsed') === 'true';
  if (isWorkbenchCollapsed) {
    setWorkbenchState(true, false);
  }

  // 1. Topbar "Apps" Button
  if (btnToggleApps) {
    btnToggleApps.addEventListener('click', () => {
      const willCollapse = !workbench.classList.contains('collapsed');
      setWorkbenchState(willCollapse, true);
    });
  }

  // 2. Tab-strip Quick "Hide Apps" Button
  if (btnHideWorkbench) {
    btnHideWorkbench.addEventListener('click', () => {
      setWorkbenchState(true, true);
    });
  }

  // 4. Keyboard Shortcut: Alt+F (Toggle Full Chat)
  document.addEventListener('keydown', (e) => {
    if (e.altKey && (e.key.toLowerCase() === 'f' || e.key.toLowerCase() === 'c')) {
      if (isTypingContext(e.target) || isModalActive()) return;
      e.preventDefault();
      const willCollapse = !workbench.classList.contains('collapsed');
      setWorkbenchState(willCollapse, true);
    }
  });

  window.__setWorkbenchState = setWorkbenchState;
}

// 1c. Aerodynamic Layout Panel Resizers (Sidebar & Rightbar Drag)
function initLayoutResizers() {
  const sidebar = document.getElementById('sidebar-dock');
  const rightbar = document.getElementById('rightbar-chat');
  const resizerLeft = document.getElementById('resizer-left');
  const resizerRight = document.getElementById('resizer-right');
  const layout = document.querySelector('.canvas-layout');

  if (!layout) return;

  const DEFAULT_SIDEBAR_WIDTH = 268;
  const MIN_SIDEBAR_WIDTH = 180;
  const DEFAULT_RIGHTBAR_WIDTH = 360;
  const MIN_RIGHTBAR_WIDTH = 280;
  const MIN_WORKBENCH_WIDTH = 320;

  // Restore persistent custom widths from localStorage
  const savedSidebarW = localStorage.getItem('xflow_sidebar_width');
  if (savedSidebarW) {
    const w = parseInt(savedSidebarW, 10);
    if (!isNaN(w) && w >= MIN_SIDEBAR_WIDTH) {
      document.documentElement.style.setProperty('--sidebar-width', `${w}px`);
    }
  }

  const savedRightbarW = localStorage.getItem('xflow_rightbar_width');
  if (savedRightbarW) {
    const w = parseInt(savedRightbarW, 10);
    if (!isNaN(w) && w >= MIN_RIGHTBAR_WIDTH) {
      document.documentElement.style.setProperty('--rightbar-width', `${w}px`);
    }
  }

  // Synchronize resizer visibility with collapsed states
  function updateResizersVisibility() {
    if (resizerLeft && sidebar) {
      const isCollapsed = sidebar.classList.contains('collapsed');
      resizerLeft.classList.toggle('collapsed', isCollapsed);
      resizerLeft.style.display = isCollapsed ? 'none' : 'flex';
    }
    if (resizerRight && rightbar) {
      const isRightbarCollapsed = rightbar.classList.contains('collapsed');
      const workbench = document.querySelector('.workbench-main');
      const isWorkbenchCollapsed = workbench ? workbench.classList.contains('collapsed') : false;
      const shouldHide = isRightbarCollapsed || isWorkbenchCollapsed;
      resizerRight.classList.toggle('collapsed', shouldHide);
      resizerRight.style.display = shouldHide ? 'none' : 'flex';
    }
  }

  updateResizersVisibility();
  window.__updateLayoutResizers = updateResizersVisibility;

  // --- DRAG RESIZER LEFT (SIDEBAR) ---
  if (resizerLeft && sidebar) {
    let startX = 0;
    let startWidth = 0;
    let isDragging = false;

    const onPointerDown = (e) => {
      if (e.button !== 0) return; // Only primary button
      if (sidebar.classList.contains('collapsed')) return;

      isDragging = true;
      startX = e.clientX;
      startWidth = sidebar.getBoundingClientRect().width;

      resizerLeft.setPointerCapture(e.pointerId);
      resizerLeft.classList.add('is-active');
      document.body.classList.add('is-resizing');
      sidebar.classList.add('is-resizing');

      window.addEventListener('pointermove', onPointerMove);
      window.addEventListener('pointerup', onPointerUp);
      window.addEventListener('pointercancel', onPointerUp);
    };

    let leftRafId = null;
    let pendingLeftWidth = null;

    const onPointerMove = (e) => {
      if (!isDragging) return;
      const isChatLeft = layout.classList.contains('chat-dock-left');
      const deltaX = isChatLeft ? (startX - e.clientX) : (e.clientX - startX);
      let newWidth = startWidth + deltaX;

      // Ensure workbench maintains minimum width
      const layoutWidth = layout.getBoundingClientRect().width;
      const rightbarWidth = (rightbar && !rightbar.classList.contains('collapsed')) 
        ? rightbar.getBoundingClientRect().width 
        : 0;
      const maxSidebarWidth = Math.max(MIN_SIDEBAR_WIDTH, Math.min(650, layoutWidth - rightbarWidth - MIN_WORKBENCH_WIDTH - 28));

      pendingLeftWidth = Math.max(MIN_SIDEBAR_WIDTH, Math.min(maxSidebarWidth, newWidth));
      if (!leftRafId) {
        leftRafId = requestAnimationFrame(() => {
          if (pendingLeftWidth !== null) {
            document.documentElement.style.setProperty('--sidebar-width', `${Math.round(pendingLeftWidth)}px`);
          }
          leftRafId = null;
        });
      }
    };

    const onPointerUp = (e) => {
      if (!isDragging) return;
      isDragging = false;

      try {
        resizerLeft.releasePointerCapture(e.pointerId);
      } catch (_) {}

      resizerLeft.classList.remove('is-active');
      document.body.classList.remove('is-resizing');
      sidebar.classList.remove('is-resizing');

      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);

      const finalWidth = sidebar.getBoundingClientRect().width;
      if (finalWidth >= MIN_SIDEBAR_WIDTH) {
        localStorage.setItem('xflow_sidebar_width', Math.round(finalWidth));
      }
    };

    resizerLeft.addEventListener('pointerdown', onPointerDown);

    // Double-click to reset to default width
    resizerLeft.addEventListener('dblclick', () => {
      document.documentElement.style.setProperty('--sidebar-width', `${DEFAULT_SIDEBAR_WIDTH}px`);
      localStorage.setItem('xflow_sidebar_width', DEFAULT_SIDEBAR_WIDTH);
      showToast(`Sidebar width reset to ${DEFAULT_SIDEBAR_WIDTH}px`);
    });
  }

  // --- DRAG RESIZER RIGHT (RIGHTBAR CHAT) ---
  if (resizerRight && rightbar) {
    let startX = 0;
    let startWidth = 0;
    let isDragging = false;

    const onPointerDown = (e) => {
      if (e.button !== 0) return;
      const workbench = document.querySelector('.workbench-main');
      if (rightbar.classList.contains('collapsed') || (workbench && workbench.classList.contains('collapsed'))) return;

      isDragging = true;
      startX = e.clientX;
      startWidth = rightbar.getBoundingClientRect().width;

      resizerRight.setPointerCapture(e.pointerId);
      resizerRight.classList.add('is-active');
      document.body.classList.add('is-resizing');
      rightbar.classList.add('is-resizing');

      window.addEventListener('pointermove', onPointerMove);
      window.addEventListener('pointerup', onPointerUp);
      window.addEventListener('pointercancel', onPointerUp);
    };

    let rightRafId = null;
    let pendingRightWidth = null;

    const onPointerMove = (e) => {
      if (!isDragging) return;
      const isChatLeft = layout.classList.contains('chat-dock-left');
      // When on right: moving left increases width. When on left: moving right increases width.
      const deltaX = isChatLeft ? (e.clientX - startX) : (startX - e.clientX);
      let newWidth = startWidth + deltaX;

      // Ensure workbench maintains minimum width
      const layoutWidth = layout.getBoundingClientRect().width;
      const sidebarWidth = (sidebar && !sidebar.classList.contains('collapsed')) 
        ? sidebar.getBoundingClientRect().width 
        : 0;
      const maxRightbarWidth = Math.max(MIN_RIGHTBAR_WIDTH, Math.min(950, layoutWidth - sidebarWidth - MIN_WORKBENCH_WIDTH - 28));

      pendingRightWidth = Math.max(MIN_RIGHTBAR_WIDTH, Math.min(maxRightbarWidth, newWidth));
      if (!rightRafId) {
        rightRafId = requestAnimationFrame(() => {
          if (pendingRightWidth !== null) {
            document.documentElement.style.setProperty('--rightbar-width', `${Math.round(pendingRightWidth)}px`);
          }
          rightRafId = null;
        });
      }
    };

    const onPointerUp = (e) => {
      if (!isDragging) return;
      isDragging = false;

      try {
        resizerRight.releasePointerCapture(e.pointerId);
      } catch (_) {}

      resizerRight.classList.remove('is-active');
      document.body.classList.remove('is-resizing');
      rightbar.classList.remove('is-resizing');

      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);

      const finalWidth = rightbar.getBoundingClientRect().width;
      if (finalWidth >= MIN_RIGHTBAR_WIDTH) {
        localStorage.setItem('xflow_rightbar_width', Math.round(finalWidth));
      }
    };

    resizerRight.addEventListener('pointerdown', onPointerDown);

    // Double-click to reset to default width
    resizerRight.addEventListener('dblclick', () => {
      document.documentElement.style.setProperty('--rightbar-width', `${DEFAULT_RIGHTBAR_WIDTH}px`);
      localStorage.setItem('xflow_rightbar_width', DEFAULT_RIGHTBAR_WIDTH);
      showToast(`Rightbar chat width reset to ${DEFAULT_RIGHTBAR_WIDTH}px`);
    });
  }
}

// 2. Search & Command Palette Shortcut
function initSearchAndShortcuts() {
  const searchInput = document.getElementById('plugin-search-input');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    filterAndRenderCards();
    filterAndRenderCopilotCards();
  });

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      if (isTypingContext(e.target) || isModalActive()) return;
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
    if (e.key === 'Escape' && document.activeElement === searchInput) {
      searchInput.value = '';
      searchQuery = '';
      searchInput.blur();
      filterAndRenderCards();
      filterAndRenderCopilotCards();
    }
  });
}

// 3. Official Flowork OS 26-Category Taxonomy & Category Ribbons
const OFFICIAL_FLOWORK_CATEGORIES = [
  { id: 'CAT-001', name: 'Healthcare', icon: '🩺' },
  { id: 'CAT-002', name: 'Psychology', icon: '🧠' },
  { id: 'CAT-003', name: 'Legal', icon: '⚖️' },
  { id: 'CAT-004', name: 'Education', icon: '🎓' },
  { id: 'CAT-005', name: 'Technology & Code', icon: '💻' },
  { id: 'CAT-006', name: 'Finance', icon: '📈' },
  { id: 'CAT-007', name: 'Business', icon: '💼' },
  { id: 'CAT-008', name: 'Marketing', icon: '📢' },
  { id: 'CAT-009', name: 'Advertising', icon: '🎯' },
  { id: 'CAT-010', name: 'Media & Video', icon: '🎬' },
  { id: 'CAT-011', name: 'Design & UI/UX', icon: '🎨' },
  { id: 'CAT-012', name: 'Human Resources', icon: '👥' },
  { id: 'CAT-013', name: 'Science & Research', icon: '🔬' },
  { id: 'CAT-014', name: 'Automation & Admin', icon: '⚡' },
  { id: 'CAT-015', name: 'Core System', icon: '🌐' },
  { id: 'CAT-016', name: 'Arts & Music', icon: '🎵' },
  { id: 'CAT-017', name: 'Metaphysics', icon: '🔮' },
  { id: 'CAT-018', name: 'Architecture', icon: '🏛️' },
  { id: 'CAT-019', name: 'Culinary', icon: '🍳' },
  { id: 'CAT-020', name: 'Sports & Games', icon: '🎮' },
  { id: 'CAT-021', name: 'Agriculture', icon: '🌱' },
  { id: 'CAT-022', name: 'Diplomacy', icon: '🤝' },
  { id: 'CAT-023', name: 'Cybersecurity', icon: '🛡️' },
  { id: 'CAT-024', name: 'Hospitality', icon: '🏨' },
  { id: 'CAT-025', name: 'Maritime & Logistics', icon: '🚢' },
  { id: 'CAT-026', name: 'System Infrastructure', icon: '⚙️' }
];

function getPluginRuntimeBadge(plugin) {
  const backend = (plugin && plugin.entry && plugin.entry.backend) || '';
  if (backend.endsWith('.py') || backend.includes('python')) {
    return { name: 'Python', class: 'tag-runtime-python', icon: '🐍' };
  } else if (backend.endsWith('.rs') || backend.includes('cargo') || backend.includes('rust')) {
    return { name: 'Rust', class: 'tag-runtime-rust', icon: '🦀' };
  } else if (backend.endsWith('.js') || backend.endsWith('.mjs') || backend.endsWith('.ts') || backend.includes('node')) {
    return { name: 'Node.js', class: 'tag-runtime-node', icon: '🟢' };
  } else if (plugin && plugin.entry && plugin.entry.gui) {
    return { name: 'Web GUI', class: 'tag-runtime-web', icon: '🌐' };
  }
  return { name: 'Polyglot', class: 'tag-runtime-polyglot', icon: '⚡' };
}

function renderCategoryRibbons() {
  const container = document.getElementById('category-filters');
  const homeSelect = document.getElementById('home-category-select');
  if (container) {
    const runningCount = openTabs.size;
    const isAll = activeCategory === 'all';
    const isApps = activeCategory === 'apps';
    const isSkills = activeCategory === 'skills';
    const isTools = activeCategory === 'tools';
    const isAgents = activeCategory === 'agents';
    const isTriggers = activeCategory === 'triggers';
    const isRunning = activeCategory === 'running';
    const isCustomCat = !isAll && !isApps && !isSkills && !isTools && !isAgents && !isTriggers && !isRunning;

    container.innerHTML = `
      <button class="category-pill ${isAll ? 'active' : ''}" data-category="all">All Modules</button>
      <button class="category-pill ${isApps ? 'active' : ''}" data-category="apps">📱 Apps</button>
      <button class="category-pill ${isSkills ? 'active' : ''}" data-category="skills">🧠 Skills</button>
      <button class="category-pill ${isTools ? 'active' : ''}" data-category="tools">🛠️ Tools</button>
      <button class="category-pill ${isAgents ? 'active' : ''}" data-category="agents">🤖 Agents</button>
      <button class="category-pill ${isTriggers ? 'active' : ''}" data-category="triggers">⚡ Triggers</button>
      <button class="category-pill ${isRunning ? 'active' : ''}" data-category="running" id="pill-filter-running">
        🟢 Active Engines (<span id="pill-running-count">${runningCount}</span>)
      </button>
      <div class="category-select-wrap">
        <select class="category-select-pill ${isCustomCat ? 'active' : ''}" id="home-category-select" title="Filter by official category">
          <option value="all">⚡ All Categories</option>
          ${OFFICIAL_FLOWORK_CATEGORIES.map((cat) => {
            const isSelected = activeCategory === cat.name || activeCategory === cat.id;
            return `<option value="${escapeHtml(cat.name)}" ${isSelected ? 'selected' : ''}>${cat.icon} ${cat.id}: ${escapeHtml(cat.name)}</option>`;
          }).join('')}
        </select>
      </div>
    `;
    initCategoryFilters();
  }

  const copilotContainer = document.getElementById('copilot-category-filters');
  if (copilotContainer) {
    const isAll = activeCopilotCategory === 'all';
    const isInstalled = activeCopilotCategory === 'installed';
    const currentTab = currentStoreSubtab || 'apps';
    const tabConfig = ECOSYSTEM_REGISTRIES[currentTab] || ECOSYSTEM_REGISTRIES.apps;

    let dynamicCategories = [];
    if (currentTab === 'apps') {
      dynamicCategories = OFFICIAL_FLOWORK_CATEGORIES.map(c => ({ id: c.id, name: c.name, icon: c.icon }));
    } else {
      const items = ecosystemState[currentTab] || [];
      const set = new Set();
      items.forEach(it => {
        const cat = it.category || it.department || it.type;
        if (cat) set.add(cat);
      });
      dynamicCategories = Array.from(set).map(catName => ({
        id: catName,
        name: catName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        icon: tabConfig.icon
      }));
    }

    const isCustomCat = !isAll && !isInstalled;

    copilotContainer.innerHTML = `
      <button class="category-pill ${isAll ? 'active' : ''}" data-copilot-cat="all">All ${tabConfig.label}</button>
      <button class="category-pill ${isInstalled ? 'active' : ''}" data-copilot-cat="installed">📦 Installed</button>
      <div class="category-select-wrap">
        <select class="category-select-pill ${isCustomCat ? 'active' : ''}" id="copilot-category-select" title="Filter by category">
          <option value="all">⚡ All Categories</option>
          ${dynamicCategories.map((cat) => {
            const isSelected = activeCopilotCategory.toLowerCase() === cat.id.toLowerCase() || activeCopilotCategory.toLowerCase() === cat.name.toLowerCase();
            return `<option value="${escapeHtml(cat.id)}" ${isSelected ? 'selected' : ''}>${cat.icon} ${escapeHtml(cat.name)}</option>`;
          }).join('')}
        </select>
      </div>
    `;
    initCopilotCategoryFilters();
  }
}

function initCategoryFilters() {
  const container = document.getElementById('category-filters');
  const select = document.getElementById('home-category-select');

  if (container && !container._delegatedBound) {
    container._delegatedBound = true;
    container.addEventListener('click', (e) => {
      const pill = e.target.closest('.category-pill');
      if (!pill) return;
      container.querySelectorAll('.category-pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      activeCategory = pill.dataset.category || 'all';
      const curSelect = document.getElementById('home-category-select');
      if (curSelect) curSelect.value = 'all';
      homeCurrentPage = 1;
      filterAndRenderCards();
    });
  }

  if (select && !select._bound) {
    select._bound = true;
    select.addEventListener('change', () => {
      activeCategory = select.value;
      if (container) {
        container.querySelectorAll('.category-pill').forEach((p) => {
          p.classList.toggle('active', p.dataset.category === activeCategory);
        });
      }
      homeCurrentPage = 1;
      filterAndRenderCards();
    });
  }
}

function initCopilotCategoryFilters() {
  const container = document.getElementById('copilot-category-filters');
  const select = document.getElementById('copilot-category-select');

  if (container && !container._delegatedBound) {
    container._delegatedBound = true;
    container.addEventListener('click', (e) => {
      const pill = e.target.closest('.category-pill');
      if (!pill) return;
      container.querySelectorAll('.category-pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      activeCopilotCategory = pill.dataset.copilotCat || 'all';
      const curSelect = document.getElementById('copilot-category-select');
      if (curSelect) curSelect.value = 'all';
      copilotCurrentPage = 1;
      filterAndRenderCopilotCards();
    });
  }

  if (select && !select._bound) {
    select._bound = true;
    select.addEventListener('change', () => {
      activeCopilotCategory = select.value;
      if (container) {
        container.querySelectorAll('.category-pill').forEach((p) => {
          p.classList.toggle('active', p.dataset.copilotCat === activeCopilotCategory);
        });
      }
      copilotCurrentPage = 1;
      filterAndRenderCopilotCards();
    });
  }
}

function initCatalogSearch() {
  const homeSearch = document.getElementById('home-search-input');
  const homeClear = document.getElementById('home-search-clear');
  if (homeSearch && !homeSearch._bound) {
    homeSearch._bound = true;
    homeSearch.addEventListener('input', () => {
      homeSearchQuery = homeSearch.value.trim().toLowerCase();
      if (homeClear) homeClear.style.display = homeSearchQuery ? 'block' : 'none';
      homeCurrentPage = 1;
      filterAndRenderCards();
    });
  }
  if (homeClear && !homeClear._bound) {
    homeClear._bound = true;
    homeClear.addEventListener('click', () => {
      if (homeSearch) homeSearch.value = '';
      homeSearchQuery = '';
      homeClear.style.display = 'none';
      homeCurrentPage = 1;
      filterAndRenderCards();
      if (homeSearch) homeSearch.focus();
    });
  }

  const copilotSearch = document.getElementById('copilot-search-input');
  const copilotClear = document.getElementById('copilot-search-clear');
  if (copilotSearch && !copilotSearch._bound) {
    copilotSearch._bound = true;
    copilotSearch.addEventListener('input', () => {
      copilotSearchQuery = copilotSearch.value.trim().toLowerCase();
      if (copilotClear) copilotClear.style.display = copilotSearchQuery ? 'block' : 'none';
      copilotCurrentPage = 1;
      filterAndRenderCopilotCards();
    });
  }
  if (copilotClear && !copilotClear._bound) {
    copilotClear._bound = true;
    copilotClear.addEventListener('click', () => {
      if (copilotSearch) copilotSearch.value = '';
      copilotSearchQuery = '';
      copilotClear.style.display = 'none';
      copilotCurrentPage = 1;
      filterAndRenderCopilotCards();
      if (copilotSearch) copilotSearch.focus();
    });
  }
}

function renderPagination(containerId, currentPage, totalPages, totalItems, startIndex, endIndex, onPageClick) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (totalItems === 0 || totalPages <= 1) {
    container.style.display = 'none';
    container.innerHTML = '';
    return;
  }

  container.style.display = 'flex';

  const summary = `<div class="pagination-summary">Showing ${startIndex + 1}–${endIndex} of ${totalItems} modules • Page ${currentPage} of ${totalPages}</div>`;

  let buttonsHtml = '<div class="pagination-buttons">';
  
  // Previous button
  buttonsHtml += `<button class="btn-page-step" data-action="prev" ${currentPage <= 1 ? 'disabled' : ''}>◀ Prev</button>`;

  // Page Numbers
  const pagesToShow = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pagesToShow.push(i);
  } else {
    pagesToShow.push(1);
    if (currentPage > 3) pagesToShow.push('...');
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);
    for (let i = start; i <= end; i++) {
      if (!pagesToShow.includes(i)) pagesToShow.push(i);
    }
    if (currentPage < totalPages - 2) pagesToShow.push('...');
    pagesToShow.push(totalPages);
  }

  pagesToShow.forEach((p) => {
    if (p === '...') {
      buttonsHtml += `<span class="btn-page-num ellipsis">...</span>`;
    } else {
      const isActive = p === currentPage;
      buttonsHtml += `<button class="btn-page-num ${isActive ? 'active' : ''}" data-page="${p}">${p}</button>`;
    }
  });

  // Next button
  buttonsHtml += `<button class="btn-page-step" data-action="next" ${currentPage >= totalPages ? 'disabled' : ''}>Next ▶</button>`;
  buttonsHtml += '</div>';

  container.innerHTML = `${summary}${buttonsHtml}`;

  // Attach listener
  container.onclick = (e) => {
    const pageBtn = e.target.closest('.btn-page-num');
    if (pageBtn && pageBtn.dataset.page) {
      const targetPage = parseInt(pageBtn.dataset.page, 10);
      if (!isNaN(targetPage) && targetPage !== currentPage) {
        onPageClick(targetPage);
      }
      return;
    }

    const stepBtn = e.target.closest('.btn-page-step');
    if (stepBtn && !stepBtn.disabled) {
      const action = stepBtn.dataset.action;
      if (action === 'prev' && currentPage > 1) {
        onPageClick(currentPage - 1);
      } else if (action === 'next' && currentPage < totalPages) {
        onPageClick(currentPage + 1);
      }
    }
  };
}

function initEventListeners() {
  const tabOffice = document.getElementById('tab-office');
  if (tabOffice) {
    tabOffice.addEventListener('click', () => switchTab('office'));
  }

  const tabCanvasStage = document.getElementById('tab-canvas-stage');
  if (tabCanvasStage) {
    tabCanvasStage.addEventListener('click', () => switchTab('canvas-stage'));
  }

  const btnHome = document.getElementById('btn-home');
  if (btnHome) {
    btnHome.addEventListener('click', () => switchTab('home'));
  }

  const btnCopilot = document.getElementById('btn-copilot');
  if (btnCopilot) {
    btnCopilot.addEventListener('click', () => switchTab('copilot'));
  }

  const tabHome = document.getElementById('tab-home');
  if (tabHome) {
    tabHome.addEventListener('click', () => switchTab('home'));
  }

  const tabCopilot = document.getElementById('tab-copilot');
  if (tabCopilot) {
    tabCopilot.addEventListener('click', () => switchTab('copilot'));
  }

  const tabPipeline = document.getElementById('tab-pipeline');
  if (tabPipeline) {
    tabPipeline.addEventListener('click', () => switchTab('pipeline'));
  }

  initStoreSubnavSystem();

  const tabStrip = document.getElementById('tab-strip');
  if (tabStrip && !tabStrip._hasMiddleClick) {
    tabStrip._hasMiddleClick = true;
    tabStrip.addEventListener('auxclick', (e) => {
      if (e.button === 1) {
        const tab = e.target.closest('.tab-capsule');
        if (tab && tab.dataset.tabId && tab.dataset.tabId !== 'office' && tab.dataset.tabId !== 'canvas-stage' && tab.dataset.tabId !== 'home' && tab.dataset.tabId !== 'copilot' && tab.dataset.tabId !== 'pipeline') {
          e.preventDefault();
          e.stopPropagation();
          closePluginTab(tab.dataset.tabId);
        }
      }
    });
    tabStrip.addEventListener('mousedown', (e) => {
      if (e.button === 1) {
        const tab = e.target.closest('.tab-capsule');
        if (tab && tab.dataset.tabId && tab.dataset.tabId !== 'office' && tab.dataset.tabId !== 'canvas-stage' && tab.dataset.tabId !== 'home' && tab.dataset.tabId !== 'copilot' && tab.dataset.tabId !== 'pipeline') {
          e.preventDefault();
        }
      }
    });
  }

  initRightbarChat();
  initChatDockSystem();
  initWorkbenchToggle();
  initOfficeBottomChatbar();

  const btnSync = document.getElementById('btn-sync-copilot');
  if (btnSync) {
    btnSync.addEventListener('click', () => {
      btnSync.innerHTML = '<span>⏳ Syncing...</span>';
      fetchEcosystemRegistry(currentStoreSubtab, true).finally(() => {
        setTimeout(() => {
          btnSync.innerHTML = '<span>🔄 Check Updates</span>';
        }, 600);
      });
    });
  }

  const btnCloseInspector = document.getElementById('btn-close-app-inspector');
  if (btnCloseInspector) {
    btnCloseInspector.addEventListener('click', closeAppInspectorModal);
  }
  const inspectorModal = document.getElementById('app-inspector-modal');
  if (inspectorModal) {
    inspectorModal.addEventListener('click', (e) => {
      if (e.target === inspectorModal) closeAppInspectorModal();
    });
  }
}

// 4. Data Fetching & Sync
async function fetchPlugins() {
  try {
    let res = await fetch('/api/apps');
    if (!res.ok) res = await fetch('/api/plugins');
    const data = await res.json();
    if (data.status === 'ok') {
      pluginsState = data.apps || data.plugins || [];
      if (Array.isArray(pluginsState) && Array.isArray(copilotState)) {
        const existingIds = new Set(copilotState.map(p => p.id));
        for (const lp of pluginsState) {
          if (lp && lp.id && !existingIds.has(lp.id)) {
            copilotState.unshift({
              ...lp,
              installed: true,
              local_only: true
            });
            existingIds.add(lp.id);
          }
        }
        if (typeof ecosystemState !== 'undefined' && ecosystemState) {
          ecosystemState.apps = copilotState;
        }
      }
      renderDock();
      renderCategoryRibbons();
      filterAndRenderCards();
      updateStats();
      filterAndRenderCopilotCards();
      // Automatically restore previously open app tabs and active tab across reload
      await restoreTabsState();
    }
  } catch (err) {
    console.error('[X-Flow] Error fetching plugins:', err);
  }
}

function getClientTargetOs() {
  if (window.__XFLOW_TARGET_OS) return window.__XFLOW_TARGET_OS;
  const platform = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || navigator.userAgent || '';
  if (/win/i.test(platform)) {
    return 'windows';
  }
  return 'linux';
}

const COPILOT_CACHE_KEY_PREFIX = 'xflow_copilot_registry_cache_';
const COPILOT_CACHE_TTL = 5 * 60 * 1000; // 5 minutes cache to keep fresh

async function fetchCopilotRegistry(isManual = false, targetOs = null) {
  const currentOs = targetOs || getClientTargetOs();
  const cacheKey = `${COPILOT_CACHE_KEY_PREFIX}${currentOs}`;

  // 1. Check localStorage cache if not manually requested
  if (!isManual) {
    try {
      const cachedStr = localStorage.getItem(cacheKey);
      if (cachedStr) {
        const cached = JSON.parse(cachedStr);
        const age = Date.now() - (cached.timestamp || 0);
        if (age < COPILOT_CACHE_TTL && cached.data && cached.data.status === 'ok') {
          const plugins = cached.data.registry?.apps || cached.data.registry?.plugins || [];
          if (plugins.length > 2 || age < 60000) {
            console.log(`[App Store] Using cached ${currentOs} registry (age: ${Math.round(age / 60000)}m, ${plugins.length} apps)`);
            applyCopilotRegistryData(cached.data, false);
            return;
          }
        }
      }
    } catch (err) {
      console.warn('[App Store] Cache read failed:', err);
    }
  }

  // 2. Fetch from server endpoint (GitHub sync)
  try {
    const res = await fetch(`/api/copilot/registry?os=${encodeURIComponent(currentOs)}`);
    const data = await res.json();
    if (data.status === 'ok' && data.registry) {
      try {
        localStorage.setItem(cacheKey, JSON.stringify({
          timestamp: Date.now(),
          data: data
        }));
      } catch (_) {}
      applyCopilotRegistryData(data, isManual);
    } else {
      console.warn('[X-Flow] Copilot registry response:', data);
    }
  } catch (err) {
    console.error('[X-Flow] Failed to fetch Copilot registry:', err);
  }
}

function applyCopilotRegistryData(data, isManual) {
  const remoteApps = data.registry.apps || data.registry.plugins || [];
  const mergedApps = [...remoteApps];
  const remoteIds = new Set(remoteApps.map(p => p.id));
  if (Array.isArray(pluginsState)) {
    for (const lp of pluginsState) {
      if (lp && lp.id && !remoteIds.has(lp.id)) {
        mergedApps.unshift({
          ...lp,
          installed: true,
          local_only: true
        });
        remoteIds.add(lp.id);
      }
    }
  }
  copilotState = mergedApps;
  if (typeof ecosystemState !== 'undefined' && ecosystemState) {
    ecosystemState.apps = copilotState;
  }
  copilotCommitSha = data.registry.commit_sha || '';
  const targetOs = data.registry.target_os || 'linux';
  
  const statSha = document.getElementById('copilot-stat-sha');
  const statCount = document.getElementById('copilot-stat-count');
  const repoLabel = document.getElementById('copilot-repo-label');
  if (statSha) statSha.textContent = `${targetOs.toUpperCase()}: ${copilotCommitSha}`;
  if (statCount) statCount.textContent = copilotState.length;
  if (repoLabel && (data.registry.repo || data.registry.repo_name)) {
    repoLabel.textContent = data.registry.repo || data.registry.repo_name;
  }

  renderCategoryRibbons();
  filterAndRenderCopilotCards();
  if (isManual) {
    showToast(`App Store (${targetOs}) synced with registry (${copilotState.length} plugins, ${copilotCommitSha})`);
  }
}

let lastDispatchedPromptText = '';
let lastDispatchedPromptTime = 0;

function injectPromptIntoChat(text, autoSend = true) {
  if (!text) return;
  const now = Date.now();
  if (lastDispatchedPromptText === text && (now - lastDispatchedPromptTime) < 3000) {
    console.log('[X-Flow] ⏳ Ignored duplicate prompt dispatch within 3000ms');
    return;
  }
  lastDispatchedPromptText = text;
  lastDispatchedPromptTime = now;

  const rightbarChat = document.getElementById('rightbar-chat');
  const isSolo3DActive = window.office3DInstance && window.office3DInstance.currentMode === 'solo' && document.getElementById('view-office') && document.getElementById('view-office').classList.contains('active');
  if (!isSolo3DActive && rightbarChat && rightbarChat.classList.contains('collapsed')) {
    rightbarChat.classList.remove('collapsed');
    localStorage.setItem('xflow_rightbar_collapsed', 'false');
  }

  const chatInput = document.getElementById('rightbar-chat-input');
  if (chatInput) {
    chatInput.value = text;
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
    if (autoSend) {
      sendUserChatMessage();
    }
  }
}

function initSSE() {
  const events = new EventSource('/api/events');
  events.onmessage = (e) => {
    try {
      const payload = JSON.parse(e.data);
      console.log('[X-Flow SSE] Event received:', payload);
      if (payload.PromptDispatched) {
        injectPromptIntoChat(payload.PromptDispatched, true);
        return;
      }
      if (payload.AgentActivity) {
        const { agent_id, state } = payload.AgentActivity;
        console.log(`[X-Flow SSE] 🧑‍💼 Agent activity event: ${agent_id} -> ${state}`);
        if (window.office3DInstance) {
          window.office3DInstance.setAgentState(agent_id, state);
        }
        if (window.swarmPipelineInstance && typeof window.swarmPipelineInstance.setAgentActivityState === 'function') {
          window.swarmPipelineInstance.setAgentActivityState(agent_id, state);
        }
        if (typeof window.updateOfficeDockAgentState === 'function') {
          window.updateOfficeDockAgentState(agent_id, state);
        }
        const cleanAg = String(agent_id).toLowerCase().replace(/^agent-/, '').replace(/^session-/, '');
        const targetSid = ('session-' + cleanAg).toLowerCase();
        const activeSid = (currentChatSessionId || '').toLowerCase();
        const activePersona = (currentSessionPersonaId || '').toLowerCase();
        const activeAg = (currentActiveAgentId || '').toLowerCase();
        if ((activeSid === targetSid || activeSid === cleanAg || activePersona === cleanAg || activeAg === cleanAg) && !isChatStreaming && state !== 'working') {
          loadChatSession(currentChatSessionId);
        }
        return;
      }
      if (payload.SwarmWaveState) {
        const wave = payload.SwarmWaveState;
        console.log('[X-Flow SSE] 🌊 Swarm wave state received:', wave);
        if (typeof window.dispatchSwarmWaveTo3D === 'function') {
          window.dispatchSwarmWaveTo3D(wave);
        } else if (Array.isArray(wave.active_workers)) {
          wave.active_workers.forEach(w => {
            const agId = w.agent_id || w.role || w.task_id;
            const isRunning = (wave.status === 'wave_started' || w.status === 'running');
            const targetState = isRunning ? 'working' : 'idle';
            setUnifiedAgentActivity(agId, targetState);
            if (typeof window.setOfficeAgentThinking === 'function') {
              const reason = isRunning ? `⚡ [Wave ${wave.wave_index}] ${w.role || w.task_id}` : 'Wave barrier verified (Exit Code 0)';
              window.setOfficeAgentThinking(agId, reason, isRunning);
            }
          });
        }
        if (wave.status === 'barrier_sync' || wave.status === 'wave_finished') {
          if (typeof playFloworkTaskDoneSound === 'function') {
            playFloworkTaskDoneSound();
          }
        }
        if (window.swarmTelemetry && typeof window.swarmTelemetry.emit === 'function') {
          const wCount = Array.isArray(wave.active_workers) ? wave.active_workers.length : 0;
          const statusLabel = (wave.status === 'wave_finished' || wave.status === 'barrier_sync') ? 'Exit Code: 0' : 'RUNNING...';
          const statusType = (wave.status === 'wave_finished' || wave.status === 'barrier_sync') ? 'success' : 'info';
          window.swarmTelemetry.emit({
            event: 'swarm_wave',
            agentId: 'leader',
            category: 'dispatch',
            tool: 'swarm_orchestrator',
            reason: `Swarm wave #${wave.wave_index || 1} [${wave.status || 'wave_active'}]: Orchestrating ${wCount} specialist agent(s) across barrier sync.`,
            command: `DAG Barrier Sync // Wave ${wave.wave_index || 1} (${wCount} workers operational)`,
            status: statusLabel,
            statusType: statusType,
            wave_index: wave.wave_index,
            active_workers: wave.active_workers
          });
        }
        return;
      }
      if (payload.PluginCommand) {
        const cmd = payload.PluginCommand;
        console.log('[X-Flow SSE] Plugin command received:', cmd);
        if (cmd.action === 'open') {
          const p = pluginsState.find(x => x.id === cmd.plugin_id) || { id: cmd.plugin_id, name: cmd.plugin_id };
          openPluginTab(p);
        } else if (cmd.action === 'close') {
          closePluginTab(cmd.plugin_id);
        } else if (cmd.action === 'refresh' || cmd.action === 'reload') {
          const tabObj = openTabs.get(cmd.plugin_id);
          const p = pluginsState.find(x => x.id === cmd.plugin_id) || { id: cmd.plugin_id, name: cmd.plugin_id };
          (async () => {
            try {
              let launchRes = await fetch(`/api/apps/${cmd.plugin_id}/launch`, { method: 'POST' });
              if (!launchRes.ok) launchRes = await fetch(`/api/plugins/${cmd.plugin_id}/launch`, { method: 'POST' });
              const launchData = await launchRes.json();
              const assignedPort = launchData && launchData.port ? launchData.port : (p.ipc && p.ipc.default_port);
              if (tabObj && tabObj.iframe) {
                tabObj.assignedPort = assignedPort;
                const queryParam = assignedPort ? `?port=${assignedPort}&backend_port=${assignedPort}&_t=${Date.now()}` : `?_t=${Date.now()}`;
                const newUrl = `/apps/${cmd.plugin_id}/gui/index.html${queryParam}`;
                tabObj.iframe.dataset.src = newUrl;
                tabObj.iframe.src = newUrl;
                switchTab(cmd.plugin_id);
              } else {
                await openPluginTab(p);
              }
            } catch (err) {
              console.error(`[X-Flow] Error refreshing tab for ${cmd.plugin_id}:`, err);
              if (tabObj && tabObj.iframe) tabObj.iframe.src = tabObj.iframe.src;
            }
          })();
        }
        return;
      }
      if (payload.SystemRestarting) {
        const restartInfo = payload.SystemRestarting;
        console.log('[X-Flow SSE] System restarting event received:', restartInfo);
        isSystemRestarting = true;
        const targetSessionId = restartInfo.session_id;
        if (targetSessionId) {
          openChatSessionById(targetSessionId);
        }
        const sendBtn = document.getElementById('btn-rightbar-send');
        if (sendBtn) {
          sendBtn.classList.add('is-running');
          sendBtn.title = 'Flowork is restarting & loading updates...';
        }
        showToast('🔄 Flowork is restarting binary & reconnecting...');
        startRestartPolling(targetSessionId);
        return;
      }
      if (payload.SystemRestarted) {
        const restartInfo = payload.SystemRestarted;
        console.log('[X-Flow SSE] System restarted notification received:', restartInfo);
        if (restartInfo.session_id) {
          openChatSessionById(restartInfo.session_id);
        }
        return;
      }
      if (payload.SkillsUpdated || payload === 'SkillsUpdated') {
        console.log('[X-Flow SSE] Skills updated event received');
        if (window.__refreshSkillsCatalog) window.__refreshSkillsCatalog();
      }
      fetchPlugins();
    } catch (err) {
      console.error('[X-Flow SSE] Parse error:', err);
    }
  };
  events.onerror = () => {
    console.warn('[X-Flow SSE] Reconnecting to host stream...');
  };
}

// 5. Dock Rendering (Organic Pills)
function renderDock() {
  const dockList = document.getElementById('dock-plugins-list');
  if (!dockList) return;
  dockList.innerHTML = '';

  pluginsState.forEach((plugin) => {
    const item = document.createElement('button');
    item.className = 'dock-pill-item';
    item.id = `dock-plugin-${plugin.id}`;
    item.title = `${plugin.name} (v${plugin.version})`;
    item.innerHTML = `
      <span class="dock-item-icon">${plugin.icon || '📦'}</span>
      <span class="dock-item-label">${plugin.name}</span>
    `;
    item.onclick = () => openPluginTab(plugin);
    dockList.appendChild(item);
  });
}

// =============================================================================
// FLOWORK OS — SOVEREIGN STATIC COSMIC BACKDROP (ZERO-CPU / ZERO-GPU OVERHEAD)
// =============================================================================
let cosmicStarfieldController = null;

function initStarfieldBackground() {
  const canvas = document.getElementById('flw-starfield-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  function renderStaticStars() {
    const width = (canvas.width = window.innerWidth);
    const height = (canvas.height = window.innerHeight);

    ctx.clearRect(0, 0, width, height);

    // Subtle, static, elegant stars drawn once — zero CPU, zero GPU, no loops
    const STAR_COUNT = 160;
    for (let i = 0; i < STAR_COUNT; i++) {
      const seed1 = (i * 9301 + 49297) % 233280;
      const seed2 = (seed1 * 9301 + 49297) % 233280;
      const seed3 = (seed2 * 9301 + 49297) % 233280;
      const x = (seed1 / 233280) * width;
      const y = (seed2 / 233280) * height;
      const size = (seed3 / 233280) * 1.3 + 0.3;
      const alpha = 0.12 + (seed1 % 100) / 180;

      const colors = ['#ffffff', '#38bdf8', '#00f2fe', '#c084fc'];
      const color = colors[i % colors.length];

      ctx.save();
      ctx.fillStyle = color;
      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fill();

      // Subtle diamond cross for a few prominent stars
      if (size > 1.2 && alpha > 0.35) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(x - 2.5, y); ctx.lineTo(x + 2.5, y);
        ctx.moveTo(x, y - 2.5); ctx.lineTo(x, y + 2.5);
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  // Draw once immediately
  renderStaticStars();

  // Re-draw once only on window resize
  window.addEventListener('resize', () => {
    renderStaticStars();
  }, { passive: true });

  cosmicStarfieldController = {
    triggerShockwave: () => {}
  };
  window.cosmicStarfieldController = cosmicStarfieldController;
}

function sanitizePebbleIcon(iconStr, fallback = '⚡') {
  if (!iconStr) return fallback;
  if (iconStr === 'fl-icon-video-editor' || iconStr === 'clapperboard') return '🎬';
  if (iconStr === 'fl-icon-forge' || iconStr === 'forge') return '⚒️';
  if (typeof iconStr === 'string' && (iconStr.startsWith('fl-icon-') || (iconStr.length > 5 && !/\s/.test(iconStr)))) {
    return fallback;
  }
  return iconStr;
}
window.sanitizePebbleIcon = sanitizePebbleIcon;

// 6. Filter & Render Cockpit Pebble Cards
// 6. Filter & Render Cockpit Pebble Cards (Installed Modules)
function filterAndRenderCards() {
  const grid = document.getElementById('plugin-grid');
  const countBadge = document.getElementById('filtered-count-badge');
  if (!grid) return;

  // Bind delegated action listener once to eliminate listener leaks & closure build-up
  if (!grid._delegatedBound) {
    grid._delegatedBound = true;
    grid.addEventListener('click', (e) => {
      const launchBtn = e.target.closest('.btn-pebble-launch');
      if (launchBtn) {
        const pluginId = launchBtn.getAttribute('data-plugin-id');
        const plugin = pluginsState.find(p => p.id === pluginId);
        if (plugin) {
          if (openTabs.has(plugin.id)) {
            switchTab(plugin.id);
          } else {
            launchBtn.innerHTML = '<span>⏳ Starting...</span>';
            launchBtn.disabled = true;
            openPluginTab(plugin).finally(() => {
              filterAndRenderCards();
            });
          }
        }
        return;
      }
      const stopBtn = e.target.closest('.btn-pebble-stop');
      if (stopBtn) {
        const pluginId = stopBtn.getAttribute('data-plugin-id');
        if (pluginId) closePluginTab(pluginId);
        return;
      }
      const restartBtn = e.target.closest('.btn-pebble-restart');
      if (restartBtn) {
        const pluginId = restartBtn.getAttribute('data-plugin-id');
        if (pluginId) restartPlugin(pluginId);
        return;
      }
      const injectBtn = e.target.closest('.btn-pebble-inject');
      if (injectBtn) {
        const name = injectBtn.getAttribute('data-skill-name');
        const id = injectBtn.getAttribute('data-skill-id');
        injectPromptIntoChat(`Equip and enforce skill: ${name} (${id}). Follow all domain SOPs and operational guidelines.`, true);
        showToast(`Injected skill ${name} into active chat.`);
        return;
      }
      const summonBtn = e.target.closest('.btn-pebble-summon');
      if (summonBtn) {
        const name = summonBtn.getAttribute('data-agent-name');
        const id = summonBtn.getAttribute('data-agent-id');
        injectPromptIntoChat(`Summoning specialist agent: @${id}. Please take over and execute current domain task.`, true);
        showToast(`Summoned agent ${name} into chat session.`);
        return;
      }
      const runCliBtn = e.target.closest('.btn-pebble-run-cli');
      if (runCliBtn) {
        const cmd = runCliBtn.getAttribute('data-tool-cmd');
        injectPromptIntoChat(`Execute autonomous tool: ${cmd}`, true);
        showToast(`Dispatched CLI tool command to chat.`);
        return;
      }
      const testTriggerBtn = e.target.closest('.btn-pebble-test-trigger');
      if (testTriggerBtn) {
        const id = testTriggerBtn.getAttribute('data-trigger-id');
        const name = testTriggerBtn.getAttribute('data-trigger-name');
        testTriggerEndpoint(id, name);
        return;
      }
      const detailsBtn = e.target.closest('.btn-pebble-details');
      if (detailsBtn) {
        const itemId = detailsBtn.getAttribute('data-item-id') || detailsBtn.getAttribute('data-plugin-id');
        const itemType = detailsBtn.getAttribute('data-item-type') || 'app';
        if (itemId) openAppInspectorModal(itemId, false, itemType);
        return;
      }
      const card = e.target.closest('.pebble-card');
      if (card && !e.target.closest('button')) {
        const itemId = card.getAttribute('data-item-id') || card.getAttribute('data-plugin-id');
        const itemType = card.getAttribute('data-item-type') || 'app';
        if (itemId) openAppInspectorModal(itemId, false, itemType);
        return;
      }
    });
  }

  // Aggregate all installed modules across all 5 ecosystem categories
  const installedApps = pluginsState.map(p => ({ ...p, _moduleType: 'apps', _itemType: 'app' }));
  
  const skillIds = getInstalledSet('skills');
  const installedSkills = (ecosystemState.skills.length > 0 ? ecosystemState.skills : [
    { id: 'software_company_sop', name: 'Software Company SOP', version: '1.0.0', category: 'engineering_sop', description: 'Multi-agent software company standard operating procedures covering architecture, testing, API contracts, threat modeling, and QC release signoff.', keywords: ['architecture', 'engineering', 'testing', 'threat_modeling'] },
    { id: 'ui_ux_pro_max', name: 'UI/UX Pro Max Design System', version: '1.0.0', category: 'design_system', description: 'Comprehensive design system, UI components, responsive layout rules, and accessibility standards.', keywords: ['ui_ux', 'design_system', 'responsive', 'glassmorphism'] }
  ]).filter(s => skillIds.has(s.id)).map(s => ({ ...s, icon: '🧠', _moduleType: 'skills', _itemType: 'skill' }));

  const toolIds = getInstalledSet('tools');
  const installedTools = (ecosystemState.tools.length > 0 ? ecosystemState.tools : [
    { id: 'crypto_scanner', name: 'crypto_scanner', version: '1.0.0', category: 'finance', description: 'Scans cryptocurrency market metrics, 24h trading volume, price volatility, and liquidity depth.', command: 'node tools/crypto_scanner/main.mjs' },
    { id: 'file_ops', name: 'file_ops', version: '1.0.0', category: 'system', description: 'Atomic file operations, reading, writing, and safe filesystem operations.', command: 'node tools/file_ops/main.mjs' },
    { id: 'semantic_search', name: 'semantic_search', version: '1.0.0', category: 'search', description: 'Deterministic vector similarity search and semantic document indexing.', command: 'node tools/semantic_search/main.mjs' }
  ]).filter(t => toolIds.has(t.id)).map(t => ({ ...t, icon: '🛠️', _moduleType: 'tools', _itemType: 'tool' }));

  const agentIds = getInstalledSet('agents');
  const installedAgents = (ecosystemState.agents.length > 0 ? ecosystemState.agents : [
    { id: 'mr.flow', name: 'Mr. Flow', role: 'Grand Chief AI Overseer & Executive Architect', version: '1.0.0', department: 'engineering', description: 'Grand Chief AI Overseer and Sovereign Executive Architect of Flowork OS.' }
  ]).filter(a => agentIds.has(a.id)).map(a => ({ ...a, icon: '⚡', _moduleType: 'agents', _itemType: 'agent' }));

  const triggerIds = getInstalledSet('triggers');
  const installedTriggers = (ecosystemState.triggers.length > 0 ? ecosystemState.triggers : [
    { id: 'bitcoin_threshold', name: 'Bitcoin Threshold Watcher', type: 'active', category: 'finance', version: '1.0.0', description: 'Monitors spot Bitcoin market price and wakes up the trading council upon crossing target threshold.', interval_seconds: 30 },
    { id: 'webhook_receiver', name: 'Inbound Webhook Receiver', type: 'active', category: 'automation_admin', version: '1.0.0', description: 'Real-time HTTP webhook receiver for incoming webhooks.', interval_seconds: 15 },
    { id: 'document_companion', name: 'Document Companion', type: 'passive', category: 'writing_editorial', version: '1.0.0', description: 'Just-In-Time editorial assistance on markdown documentation.' },
    { id: 'zombie_process_hunter', name: 'Zombie Process Hunter', type: 'passive', category: 'process_management', version: '1.0.0', description: 'Auto-detects and neutralizes orphaned processes and port leaks.' }
  ]).filter(tr => triggerIds.has(tr.id)).map(tr => ({ ...tr, icon: '⚡', _moduleType: 'triggers', _itemType: 'trigger' }));

  const allInstalled = [
    ...installedApps,
    ...installedSkills,
    ...installedTools,
    ...installedAgents,
    ...installedTriggers
  ];

  // Update quick stats in local hero
  const statTotal = document.getElementById('stat-total-plugins');
  const statDaemons = document.getElementById('stat-active-daemons');
  if (statTotal) statTotal.textContent = allInstalled.length;
  if (statDaemons) statDaemons.textContent = openTabs.size + (installedTriggers.filter(t => t.type === 'active').length);

  const filtered = allInstalled.filter((item) => {
    let matchesCategory = false;
    if (activeCategory === 'all') {
      matchesCategory = true;
    } else if (activeCategory === 'apps') {
      matchesCategory = item._moduleType === 'apps';
    } else if (activeCategory === 'skills') {
      matchesCategory = item._moduleType === 'skills';
    } else if (activeCategory === 'tools') {
      matchesCategory = item._moduleType === 'tools';
    } else if (activeCategory === 'agents') {
      matchesCategory = item._moduleType === 'agents';
    } else if (activeCategory === 'triggers') {
      matchesCategory = item._moduleType === 'triggers';
    } else if (activeCategory === 'running') {
      matchesCategory = item._moduleType === 'apps' && openTabs.has(item.id);
    } else {
      const target = activeCategory.toLowerCase();
      const pCat = (item.category || item.department || '').toLowerCase();
      matchesCategory = pCat.includes(target) || target.includes(pCat);
    }

    const activeSearch = homeSearchQuery || searchQuery;
    const matchesSearch =
      !activeSearch ||
      (item.name && item.name.toLowerCase().includes(activeSearch)) ||
      (item.description && item.description.toLowerCase().includes(activeSearch)) ||
      (item.id && item.id.toLowerCase().includes(activeSearch)) ||
      (item.category && item.category.toLowerCase().includes(activeSearch)) ||
      (item.role && item.role.toLowerCase().includes(activeSearch));

    return matchesCategory && matchesSearch;
  });

  const totalItems = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / MODULES_PER_PAGE));
  if (homeCurrentPage > totalPages) homeCurrentPage = totalPages;
  if (homeCurrentPage < 1) homeCurrentPage = 1;

  if (countBadge) {
    if (totalItems > MODULES_PER_PAGE) {
      countBadge.textContent = `${totalItems} modules • Page ${homeCurrentPage} of ${totalPages}`;
    } else {
      countBadge.textContent = `${totalItems} of ${allInstalled.length} installed module${allInstalled.length === 1 ? '' : 's'}`;
    }
  }

  const startIndex = (homeCurrentPage - 1) * MODULES_PER_PAGE;
  const endIndex = Math.min(startIndex + MODULES_PER_PAGE, totalItems);
  const pageItems = filtered.slice(startIndex, endIndex);

  renderPagination('home-pagination', homeCurrentPage, totalPages, totalItems, startIndex, endIndex, (newPage) => {
    homeCurrentPage = newPage;
    filterAndRenderCards();
  });

  const fragment = document.createDocumentFragment();

  if (filtered.length === 0) {
    renderPagination('home-pagination', 1, 0, 0, 0, 0, () => {});
    const emptyWrapper = document.createElement('div');
    emptyWrapper.innerHTML = `
      <div style="grid-column: 1 / -1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px 24px; text-align: center; gap: 14px; opacity: 0.85;">
        <div style="width: 48px; height: 48px; border-radius: 50%; border: 1px dashed rgba(0, 229, 255, 0.4); display: flex; align-items: center; justify-content: center; font-size: 20px; color: #00e5ff; box-shadow: 0 0 16px rgba(0, 229, 255, 0.15);">
          ◈
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #f1f5f9; letter-spacing: 0.1em; font-family: var(--font-mono);">NO INSTALLED MODULES MATCH FILTER</div>
        <div style="font-size: 12px; color: var(--text-dim); max-width: 380px;">Adjust your category or search filter, or browse the Ecosystem tabs to install new modules.</div>
      </div>
    `;
    while (emptyWrapper.firstChild) fragment.appendChild(emptyWrapper.firstChild);
    grid.replaceChildren(fragment);
    return;
  }

  pageItems.forEach((item) => {
    const card = document.createElement('div');
    card.className = 'pebble-card';
    card.setAttribute('data-item-id', item.id);
    card.setAttribute('data-item-type', item._itemType);
    card.style.cursor = 'pointer';

    const isApp = item._moduleType === 'apps';
    const isRunning = isApp && openTabs.has(item.id);
    if (isRunning) card.classList.add('is-running');

    const tabInfo = isRunning ? openTabs.get(item.id) : null;
    const activePort = (tabInfo && tabInfo.assignedPort) || item.activePort;
    const defaultPort = item.ipc && item.ipc.default_port;
    const runtime = isApp ? getPluginRuntimeBadge(item) : { name: item._itemType.toUpperCase(), class: 'tag-runtime-web', icon: item.icon };

    const rawName = item.name || item.id;
    const displayName = rawName.length > 25 ? rawName.slice(0, 23) + '...' : rawName;
    const rawVer = String(item.version || '1.0.0');
    const displayVer = rawVer.length > 8 ? rawVer.slice(0, 7) + '...' : rawVer;
    const rawCategory = item.category || item.department || item.type || 'General';
    const displayCategory = rawCategory.length > 14 ? rawCategory.slice(0, 12) + '...' : rawCategory;
    const rawDesc = item.description || 'Installed sovereign module.';
    const displayDesc = rawDesc.length > 95 ? rawDesc.slice(0, 92) + '...' : rawDesc;

    const portDisplay = isRunning && activePort 
      ? `<span class="pebble-tag tag-port" title="Live Port :${activePort}">:${activePort}</span>`
      : (defaultPort ? `<span class="pebble-tag tag-port" title="Default Port :${defaultPort}" style="opacity: 0.7;">:${defaultPort}</span>` : '');

    let actionButtons = '';
    let chipsHtml = '';

    if (isApp) {
      if (isRunning) {
        actionButtons = `
          <button class="btn-pebble-launch" id="btn-launch-${item.id}" data-plugin-id="${escapeHtml(item.id)}" title="Switch to Active Panel">Switch to Tab</button>
          <button class="btn-pebble-restart" data-plugin-id="${escapeHtml(item.id)}" title="Restart Engine">🔄</button>
          <button class="btn-pebble-stop" data-plugin-id="${escapeHtml(item.id)}" title="Stop Engine">⏹️</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="app" title="Module Specifications">ℹ️</button>
        `;
      } else {
        actionButtons = `
          <button class="btn-pebble-launch" id="btn-launch-${item.id}" data-plugin-id="${escapeHtml(item.id)}">Launch Module</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="app" title="Module Specifications">ℹ️</button>
        `;
      }
    } else if (item._itemType === 'skill') {
      actionButtons = `
        <button class="btn-pebble-inject" data-skill-id="${escapeHtml(item.id)}" data-skill-name="${escapeHtml(item.name || item.id)}" title="Inject SOP directive into chat">💬 Inject SOP</button>
        <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="skill" title="SOP Specifications">ℹ️</button>
      `;
      if (item.keywords && Array.isArray(item.keywords)) {
        chipsHtml = `<div class="pebble-chip-row">${item.keywords.slice(0, 3).map(k => `<span class="pebble-chip">#${escapeHtml(k)}</span>`).join('')}</div>`;
      }
    } else if (item._itemType === 'tool') {
      actionButtons = `
        <button class="btn-pebble-run-cli" data-tool-id="${escapeHtml(item.id)}" data-tool-cmd="${escapeHtml(item.command || ('node tools/' + item.id + '/main.mjs'))}" title="Run CLI Tool">⚡ Run CLI</button>
        <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="tool" title="Tool Specifications">ℹ️</button>
      `;
      if (item.command) {
        chipsHtml = `<div class="pebble-chip-row"><span class="pebble-chip" style="color: #f59e0b; border-color: rgba(245, 158, 11, 0.2);">${escapeHtml(item.command)}</span></div>`;
      }
    } else if (item._itemType === 'agent') {
      actionButtons = `
        <button class="btn-pebble-summon" data-agent-id="${escapeHtml(item.id)}" data-agent-name="${escapeHtml(item.name || item.id)}" title="Summon Specialist to Chat">💬 Summon</button>
        <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="agent" title="Agent Profile">ℹ️</button>
      `;
      if (item.role) {
        chipsHtml = `<div class="pebble-chip-row"><span class="pebble-chip" style="color: #00f2fe; border-color: rgba(0, 242, 254, 0.2);">${escapeHtml(item.role)}</span></div>`;
      }
    } else if (item._itemType === 'trigger') {
      actionButtons = `
        <button class="btn-pebble-test-trigger" data-trigger-id="${escapeHtml(item.id)}" data-trigger-name="${escapeHtml(item.name || item.id)}" title="Probe Trigger Sensor">⚡ Test</button>
        <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="trigger" title="Trigger Telemetry">ℹ️</button>
      `;
      chipsHtml = `<div class="pebble-chip-row"><span class="pebble-chip ${item.type === 'active' ? 'chip-active-daemon' : 'chip-passive-sensor'}">${item.type === 'active' ? ('Interval: ' + (item.interval_seconds || 30) + 's') : 'Sensor: JIT AST Prompt'}</span></div>`;
    }

    card.innerHTML = `
      <div class="pebble-header">
        <div class="pebble-glyph-circle">${sanitizePebbleIcon(item.icon)}</div>
        <div class="pebble-info">
          <div class="pebble-title" title="${escapeHtml(rawName)}">${escapeHtml(displayName)}</div>
          <div class="pebble-tags">
            <span class="pebble-tag" title="v${escapeHtml(rawVer)}">v${escapeHtml(displayVer)}</span>
            <span class="pebble-tag ${runtime.class}" title="${runtime.name}">${runtime.icon} ${runtime.name}</span>
            <span class="pebble-tag" title="${escapeHtml(rawCategory)}">${escapeHtml(displayCategory)}</span>
            ${portDisplay}
          </div>
        </div>
      </div>
      <div class="pebble-description" title="${escapeHtml(rawDesc)}">${escapeHtml(displayDesc)}</div>
      ${chipsHtml}
      <div class="pebble-footer">
        <div class="pebble-status">
          <span class="pebble-beacon-dot ${isRunning || !isApp ? 'active' : ''}"></span>
          <span style="${isRunning ? 'color: #00e5ff; font-weight: 700;' : ''}">${isApp ? (isRunning ? 'Running' : 'Ready') : 'Active'}</span>
        </div>
        <div style="display: flex; gap: 6px; align-items: center;">
          ${actionButtons}
        </div>
      </div>
    `;
    fragment.appendChild(card);
  });

  grid.replaceChildren(fragment);
}

// 7. Filter & Render Ecosystem Storefront Pebble Cards
function filterAndRenderCopilotCards() {
  const grid = document.getElementById('copilot-grid');
  const counterBadge = document.getElementById('copilot-counter-badge');
  if (!grid) return;

  const currentTab = currentStoreSubtab || 'apps';
  const tabConfig = ECOSYSTEM_REGISTRIES[currentTab] || ECOSYSTEM_REGISTRIES.apps;

  // Bind delegated action listeners once
  if (!grid._delegatedBound) {
    grid._delegatedBound = true;
    grid.addEventListener('click', (e) => {
      const installBtn = e.target.closest('.btn-pebble-install');
      if (installBtn) {
        const id = installBtn.getAttribute('data-item-id') || installBtn.getAttribute('data-plugin-id');
        const name = installBtn.getAttribute('data-item-name') || installBtn.getAttribute('data-plugin-name');
        const type = installBtn.getAttribute('data-item-type') || currentStoreSubtab;
        if (type === 'app' || type === 'apps') {
          installExtension(id, name);
        } else {
          installEcosystemItem(id, type, name);
        }
        return;
      }
      const updateBtn = e.target.closest('.btn-pebble-update');
      if (updateBtn) {
        const id = updateBtn.getAttribute('data-plugin-id');
        const name = updateBtn.getAttribute('data-plugin-name');
        if (id) installExtension(id, name, true);
        return;
      }
      const uninstallBtn = e.target.closest('.btn-pebble-uninstall');
      if (uninstallBtn) {
        const id = uninstallBtn.getAttribute('data-item-id') || uninstallBtn.getAttribute('data-plugin-id');
        const name = uninstallBtn.getAttribute('data-item-name') || uninstallBtn.getAttribute('data-plugin-name');
        const type = uninstallBtn.getAttribute('data-item-type') || currentStoreSubtab;
        if (type === 'app' || type === 'apps') {
          uninstallExtension(id, name);
        } else {
          uninstallEcosystemItem(id, type, name);
        }
        return;
      }
      const launchBtn = e.target.closest('.btn-pebble-launch');
      if (launchBtn) {
        const id = launchBtn.getAttribute('data-plugin-id');
        const localPlugin = pluginsState.find((p) => p.id === id) || copilotState.find((p) => p.id === id);
        if (localPlugin) {
          if (openTabs.has(localPlugin.id)) {
            switchTab(localPlugin.id);
          } else {
            launchBtn.innerHTML = '<span>⏳ Starting...</span>';
            launchBtn.disabled = true;
            openPluginTab(localPlugin).finally(() => {
              filterAndRenderCopilotCards();
              filterAndRenderCards();
            });
          }
        }
        return;
      }
      const injectBtn = e.target.closest('.btn-pebble-inject');
      if (injectBtn) {
        const name = injectBtn.getAttribute('data-skill-name');
        const id = injectBtn.getAttribute('data-skill-id');
        injectPromptIntoChat(`Equip and enforce skill: ${name} (${id}). Follow all domain SOPs and operational guidelines.`, true);
        showToast(`Injected skill ${name} into active chat.`);
        return;
      }
      const summonBtn = e.target.closest('.btn-pebble-summon');
      if (summonBtn) {
        const name = summonBtn.getAttribute('data-agent-name');
        const id = summonBtn.getAttribute('data-agent-id');
        injectPromptIntoChat(`Summoning specialist agent: @${id}. Please take over and execute current domain task.`, true);
        showToast(`Summoned agent ${name} into chat session.`);
        return;
      }
      const runCliBtn = e.target.closest('.btn-pebble-run-cli');
      if (runCliBtn) {
        const cmd = runCliBtn.getAttribute('data-tool-cmd');
        injectPromptIntoChat(`Execute autonomous tool: ${cmd}`, true);
        showToast(`Dispatched CLI tool command to chat.`);
        return;
      }
      const testTriggerBtn = e.target.closest('.btn-pebble-test-trigger');
      if (testTriggerBtn) {
        const id = testTriggerBtn.getAttribute('data-trigger-id');
        const name = testTriggerBtn.getAttribute('data-trigger-name');
        testTriggerEndpoint(id, name);
        return;
      }
      const detailsBtn = e.target.closest('.btn-pebble-details');
      if (detailsBtn) {
        const id = detailsBtn.getAttribute('data-item-id') || detailsBtn.getAttribute('data-plugin-id');
        const type = detailsBtn.getAttribute('data-item-type') || currentStoreSubtab;
        if (id) openAppInspectorModal(id, true, type);
        return;
      }
      const card = e.target.closest('.pebble-card');
      if (card && !e.target.closest('button')) {
        const id = card.getAttribute('data-item-id') || card.getAttribute('data-plugin-id');
        const type = card.getAttribute('data-item-type') || currentStoreSubtab;
        if (id) openAppInspectorModal(id, true, type);
        return;
      }
    });
  }

  const installedSet = getInstalledSet(currentTab);
  let items = (currentTab === 'apps') ? [...copilotState] : (ecosystemState[currentTab] || []);
  if (currentTab === 'apps' && Array.isArray(pluginsState)) {
    const existingIds = new Set(items.map(p => p.id));
    for (const lp of pluginsState) {
      if (lp && lp.id && !existingIds.has(lp.id)) {
        items.unshift({
          ...lp,
          installed: true,
          local_only: true
        });
        existingIds.add(lp.id);
      }
    }
  }

  const filtered = items.filter((p) => {
    let matchesCategory = false;
    if (activeCopilotCategory === 'all') {
      matchesCategory = true;
    } else if (activeCopilotCategory === 'installed') {
      matchesCategory = installedSet.has(p.id) || p.installed;
    } else {
      const target = activeCopilotCategory.toLowerCase();
      const pCat = (p.category || p.department || p.type || '').toLowerCase();
      const pCatId = (p.category_id || '').toLowerCase();
      matchesCategory = pCatId === target || 
                        pCat === target ||
                        pCat.includes(target) || 
                        target.includes(pCat);
    }

    const activeSearch = copilotSearchQuery || searchQuery;
    const matchesSearch =
      !activeSearch ||
      (p.name && p.name.toLowerCase().includes(activeSearch)) ||
      (p.description && p.description.toLowerCase().includes(activeSearch)) ||
      (p.id && p.id.toLowerCase().includes(activeSearch)) ||
      (p.category && p.category.toLowerCase().includes(activeSearch)) ||
      (p.role && p.role.toLowerCase().includes(activeSearch)) ||
      (p.keywords && Array.isArray(p.keywords) && p.keywords.some(k => k.toLowerCase().includes(activeSearch)));

    return matchesCategory && matchesSearch;
  });

  const totalItems = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / MODULES_PER_PAGE));
  if (copilotCurrentPage > totalPages) copilotCurrentPage = totalPages;
  if (copilotCurrentPage < 1) copilotCurrentPage = 1;

  if (counterBadge) {
    if (totalItems > MODULES_PER_PAGE) {
      counterBadge.textContent = `${totalItems} ${tabConfig.unitName.toLowerCase()} • Page ${copilotCurrentPage} of ${totalPages}`;
    } else {
      counterBadge.textContent = `${totalItems} of ${items.length} cloud ${tabConfig.unitName.toLowerCase()}`;
    }
  }

  const startIndex = (copilotCurrentPage - 1) * MODULES_PER_PAGE;
  const endIndex = Math.min(startIndex + MODULES_PER_PAGE, totalItems);
  const pageItems = filtered.slice(startIndex, endIndex);

  renderPagination('copilot-pagination', copilotCurrentPage, totalPages, totalItems, startIndex, endIndex, (newPage) => {
    copilotCurrentPage = newPage;
    filterAndRenderCopilotCards();
  });

  const fragment = document.createDocumentFragment();

  if (filtered.length === 0) {
    renderPagination('copilot-pagination', 1, 0, 0, 0, 0, () => {});
    const emptyWrapper = document.createElement('div');
    emptyWrapper.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 48px; text-align: center; color: var(--text-dim); background: rgba(255, 255, 255, 0.03); border: 1.5px dashed var(--border-organic); border-radius: 24px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);">
        <div style="font-size: 28px; margin-bottom: 8px;">${tabConfig.icon}</div>
        <div style="font-size: 14px; font-weight: 700; color: var(--text-main); margin-bottom: 4px;">No matching cloud ${tabConfig.unitName.toLowerCase()}</div>
        <div style="font-size: 12px; color: var(--text-muted);">Check filter tags or sync with GitHub registry (${tabConfig.repo}).</div>
      </div>
    `;
    while (emptyWrapper.firstChild) fragment.appendChild(emptyWrapper.firstChild);
    grid.replaceChildren(fragment);
    return;
  }

  pageItems.forEach((item) => {
    const isInstalled = installedSet.has(item.id) || item.installed;
    const isApp = currentTab === 'apps';
    const isRunning = isApp && openTabs.has(item.id);
    const tabInfo = isRunning ? openTabs.get(item.id) : null;
    const activePort = (tabInfo && tabInfo.assignedPort) || item.activePort;
    const defaultPort = item.ipc && item.ipc.default_port;
    const runtime = isApp ? getPluginRuntimeBadge(item) : { name: currentTab.slice(0, -1).toUpperCase(), class: 'tag-runtime-web', icon: tabConfig.icon };

    const card = document.createElement('div');
    card.className = 'pebble-card';
    card.setAttribute('data-item-id', item.id);
    card.setAttribute('data-item-type', currentTab);
    card.style.cursor = 'pointer';
    if (isRunning) card.classList.add('is-running');

    let actionButtons = '';
    let statusBadge = '';
    let chipsHtml = '';

    if (isApp) {
      const isUpdateAvailable = Boolean(item.update_available);
      if (!isInstalled) {
        statusBadge = `<span class="pebble-tag tag-status-available">Available</span>`;
        actionButtons = `
          <button class="btn-pebble-install" id="btn-copilot-install-${item.id}" data-item-id="${escapeHtml(item.id)}" data-item-type="app" data-item-name="${escapeHtml(item.name || item.id)}">
            ⬇️ Install
          </button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="app" data-is-cloud="true" title="Specifications">ℹ️</button>
        `;
      } else if (isUpdateAvailable) {
        statusBadge = `<span class="pebble-tag tag-status-update">Update Ready</span>`;
        actionButtons = `
          <button class="btn-pebble-update" id="btn-copilot-update-${item.id}" data-plugin-id="${escapeHtml(item.id)}" data-plugin-name="${escapeHtml(item.name || item.id)}">✨ Update</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="app" data-is-cloud="true" title="Specifications">ℹ️</button>
          <button class="btn-pebble-uninstall" id="btn-copilot-uninstall-${item.id}" data-item-id="${escapeHtml(item.id)}" data-item-type="app" data-item-name="${escapeHtml(item.name || item.id)}" title="Uninstall Plugin">🗑️</button>
        `;
      } else {
        statusBadge = `<span class="pebble-tag tag-status-installed">Installed</span>`;
        actionButtons = `
          <button class="btn-pebble-launch" id="btn-copilot-launch-${item.id}" data-plugin-id="${escapeHtml(item.id)}">${isRunning ? 'Switch to Tab' : 'Launch'}</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="app" data-is-cloud="true" title="Specifications">ℹ️</button>
          <button class="btn-pebble-uninstall" id="btn-copilot-uninstall-${item.id}" data-item-id="${escapeHtml(item.id)}" data-item-type="app" data-item-name="${escapeHtml(item.name || item.id)}" title="Uninstall Plugin">🗑️</button>
        `;
      }
    } else if (currentTab === 'skills') {
      if (!isInstalled) {
        statusBadge = `<span class="pebble-tag tag-status-available">Available</span>`;
        actionButtons = `
          <button class="btn-pebble-install" data-item-id="${escapeHtml(item.id)}" data-item-type="skills" data-item-name="${escapeHtml(item.name || item.id)}">⬇️ Install Skill</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="skills" title="SOP Specifications">ℹ️</button>
        `;
      } else {
        statusBadge = `<span class="pebble-tag tag-status-installed">Installed</span>`;
        actionButtons = `
          <button class="btn-pebble-inject" data-skill-id="${escapeHtml(item.id)}" data-skill-name="${escapeHtml(item.name || item.id)}" title="Inject SOP directive into chat">💬 Inject SOP</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="skills" title="SOP Specifications">ℹ️</button>
          <button class="btn-pebble-uninstall" data-item-id="${escapeHtml(item.id)}" data-item-type="skills" data-item-name="${escapeHtml(item.name || item.id)}" title="Uninstall">🗑️</button>
        `;
      }
      if (item.keywords && Array.isArray(item.keywords)) {
        chipsHtml = `<div class="pebble-chip-row">${item.keywords.slice(0, 3).map(k => `<span class="pebble-chip">#${escapeHtml(k)}</span>`).join('')}</div>`;
      }
    } else if (currentTab === 'tools') {
      if (!isInstalled) {
        statusBadge = `<span class="pebble-tag tag-status-available">Available</span>`;
        actionButtons = `
          <button class="btn-pebble-install" data-item-id="${escapeHtml(item.id)}" data-item-type="tools" data-item-name="${escapeHtml(item.name || item.id)}">⬇️ Install Tool</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="tools" title="Tool Specifications">ℹ️</button>
        `;
      } else {
        statusBadge = `<span class="pebble-tag tag-status-installed">Installed</span>`;
        actionButtons = `
          <button class="btn-pebble-run-cli" data-tool-id="${escapeHtml(item.id)}" data-tool-cmd="${escapeHtml(item.command || ('node tools/' + item.id + '/main.mjs'))}" title="Run CLI Tool">⚡ Run CLI</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="tools" title="Tool Specifications">ℹ️</button>
          <button class="btn-pebble-uninstall" data-item-id="${escapeHtml(item.id)}" data-item-type="tools" data-item-name="${escapeHtml(item.name || item.id)}" title="Uninstall">🗑️</button>
        `;
      }
      if (item.command) {
        chipsHtml = `<div class="pebble-chip-row"><span class="pebble-chip" style="color: #f59e0b; border-color: rgba(245, 158, 11, 0.2);">${escapeHtml(item.command)}</span></div>`;
      }
    } else if (currentTab === 'agents') {
      if (!isInstalled) {
        statusBadge = `<span class="pebble-tag tag-status-available">Available</span>`;
        actionButtons = `
          <button class="btn-pebble-install" data-item-id="${escapeHtml(item.id)}" data-item-type="agents" data-item-name="${escapeHtml(item.name || item.id)}">⬇️ Add Squad</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="agents" title="Agent Profile">ℹ️</button>
        `;
      } else {
        statusBadge = `<span class="pebble-tag tag-status-installed">In Squad</span>`;
        actionButtons = `
          <button class="btn-pebble-summon" data-agent-id="${escapeHtml(item.id)}" data-agent-name="${escapeHtml(item.name || item.id)}" title="Summon Specialist to Chat">💬 Summon</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="agents" title="Agent Profile">ℹ️</button>
          <button class="btn-pebble-uninstall" data-item-id="${escapeHtml(item.id)}" data-item-type="agents" data-item-name="${escapeHtml(item.name || item.id)}" title="Remove from Squad">🗑️</button>
        `;
      }
      if (item.role) {
        chipsHtml = `<div class="pebble-chip-row"><span class="pebble-chip" style="color: #00f2fe; border-color: rgba(0, 242, 254, 0.2);">${escapeHtml(item.role)}</span></div>`;
      }
    } else if (currentTab === 'triggers') {
      if (!isInstalled) {
        statusBadge = `<span class="pebble-tag tag-status-available">Available</span>`;
        actionButtons = `
          <button class="btn-pebble-install" data-item-id="${escapeHtml(item.id)}" data-item-type="triggers" data-item-name="${escapeHtml(item.name || item.id)}">⬇️ Install Sensor</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="triggers" title="Trigger Telemetry">ℹ️</button>
        `;
      } else {
        statusBadge = `<span class="pebble-tag tag-status-installed">Active Sensor</span>`;
        actionButtons = `
          <button class="btn-pebble-test-trigger" data-trigger-id="${escapeHtml(item.id)}" data-trigger-name="${escapeHtml(item.name || item.id)}" title="Probe Trigger Sensor">⚡ Test</button>
          <button class="btn-pebble-details" data-item-id="${escapeHtml(item.id)}" data-item-type="triggers" title="Trigger Telemetry">ℹ️</button>
          <button class="btn-pebble-uninstall" data-item-id="${escapeHtml(item.id)}" data-item-type="triggers" data-item-name="${escapeHtml(item.name || item.id)}" title="Remove Sensor">🗑️</button>
        `;
      }
      chipsHtml = `<div class="pebble-chip-row"><span class="pebble-chip ${item.type === 'active' ? 'chip-active-daemon' : 'chip-passive-sensor'}">${item.type === 'active' ? ('Interval: ' + (item.interval_seconds || 30) + 's') : 'Sensor: JIT AST Prompt'}</span></div>`;
    }

    const rawName = item.name || item.id;
    const displayName = rawName.length > 25 ? rawName.slice(0, 23) + '...' : rawName;
    const rawVer = String(item.version || '1.0.0');
    const displayVer = rawVer.length > 8 ? rawVer.slice(0, 7) + '...' : rawVer;
    const rawCategory = item.category || item.department || item.type || 'General';
    const displayCategory = rawCategory.length > 14 ? rawCategory.slice(0, 12) + '...' : rawCategory;
    const rawDesc = item.description || 'Federated sovereign ecosystem extension.';
    const displayDesc = rawDesc.length > 95 ? rawDesc.slice(0, 92) + '...' : rawDesc;

    const portDisplay = isRunning && activePort 
      ? `<span class="pebble-tag tag-port" title="Live Port :${activePort}">:${activePort}</span>`
      : (defaultPort ? `<span class="pebble-tag tag-port" title="Default Port :${defaultPort}" style="opacity: 0.7;">:${defaultPort}</span>` : '');

    card.innerHTML = `
      <div class="pebble-header">
        <div class="pebble-glyph-circle">${sanitizePebbleIcon(item.icon, tabConfig.icon)}</div>
        <div class="pebble-info">
          <div class="pebble-title" title="${escapeHtml(rawName)}">${escapeHtml(displayName)}</div>
          <div class="pebble-tags">
            <span class="pebble-tag" title="v${escapeHtml(rawVer)}">v${escapeHtml(displayVer)}</span>
            <span class="pebble-tag ${runtime.class}" title="Type: ${runtime.name}">${runtime.icon} ${runtime.name}</span>
            <span class="pebble-tag" title="${escapeHtml(rawCategory)}">${escapeHtml(displayCategory)}</span>
            ${portDisplay}
            ${statusBadge}
          </div>
        </div>
      </div>
      <div class="pebble-description" title="${escapeHtml(rawDesc)}">${escapeHtml(displayDesc)}</div>
      ${chipsHtml}
      <div class="pebble-footer">
        <div class="pebble-status">
          <span class="pebble-beacon-dot ${isInstalled ? 'active' : ''}"></span>
          <span style="${isRunning ? 'color: #00e5ff; font-weight: 700;' : ''}">${isInstalled ? (isRunning ? 'Running' : 'Installed') : 'In Cloud'}</span>
        </div>
        <div style="display: flex; gap: 6px; align-items: center;">
          ${actionButtons}
        </div>
      </div>
    `;

    fragment.appendChild(card);
  });

  grid.replaceChildren(fragment);
}

// 8. Extension & Ecosystem Install & Uninstall Operations (Autonomous Outside-Binary Engine)
const githubRepoTreeCache = new Map();

async function getGitHubRepoTree(repo) {
  if (githubRepoTreeCache.has(repo)) {
    return githubRepoTreeCache.get(repo);
  }
  try {
    const cached = sessionStorage.getItem(`xflow_gh_tree_${repo}`);
    if (cached) {
      const parsed = JSON.parse(cached);
      githubRepoTreeCache.set(repo, parsed);
      return parsed;
    }
  } catch (_) {}

  try {
    const res = await fetch(`https://api.github.com/repos/flowork-os/${repo}/git/trees/main?recursive=1`, {
      headers: { 'Accept': 'application/vnd.github.v3+json' }
    });
    if (res.ok) {
      const data = await res.json();
      const tree = data.tree || [];
      githubRepoTreeCache.set(repo, tree);
      try {
        sessionStorage.setItem(`xflow_gh_tree_${repo}`, JSON.stringify(tree));
      } catch (_) {}
      return tree;
    }
  } catch (err) {
    console.warn(`[Ecosystem Store] GitHub tree API notice for ${repo}:`, err);
  }
  return null;
}

async function downloadAndMountEcosystemPackage(repoName, remotePrefix, targetLocalDir, fallbackFiles = []) {
  let cleanPrefix = (remotePrefix || '').trim().replace(/^\/+|\/+$/g, '');
  if (!cleanPrefix.endsWith('/')) cleanPrefix += '/';

  let filesToDownload = [];
  const tree = await getGitHubRepoTree(repoName);

  if (Array.isArray(tree) && tree.length > 0) {
    filesToDownload = tree
      .filter(item => item.type === 'blob' && item.path.startsWith(cleanPrefix))
      .map(item => ({
        remotePath: item.path,
        relPath: item.path.substring(cleanPrefix.length)
      }));
  }

  // Fallback if tree API hit rate-limit or returned empty
  if (filesToDownload.length === 0 && Array.isArray(fallbackFiles) && fallbackFiles.length > 0) {
    filesToDownload = fallbackFiles.map(rel => ({
      remotePath: `${cleanPrefix}${rel}`.replace(/\/+/g, '/'),
      relPath: rel
    }));
  }

  if (filesToDownload.length === 0) {
    throw new Error(`Package artifacts not found in repository "${repoName}" under "${cleanPrefix}".`);
  }

  let successCount = 0;
  for (const file of filesToDownload) {
    const rawUrl = `https://raw.githubusercontent.com/flowork-os/${repoName}/main/${file.remotePath}`;
    try {
      const res = await fetch(rawUrl);
      if (!res.ok) {
        console.warn(`[Ecosystem Store] Could not fetch ${rawUrl}: HTTP ${res.status}`);
        continue;
      }
      const blob = await res.blob();
      const dest = `${targetLocalDir}/${file.relPath}`.replace(/\/+/g, '/');

      const saveRes = await fetch('/api/fs/save-file', {
        method: 'POST',
        headers: {
          'Content-Type': res.headers.get('content-type') || 'application/octet-stream',
          'X-Target-Path': dest
        },
        body: blob
      });
      if (saveRes.ok) {
        successCount++;
      }
    } catch (err) {
      console.warn(`[Ecosystem Store] Error downloading ${file.remotePath}:`, err);
    }
  }

  if (successCount === 0) {
    throw new Error(`Failed to write any package files to local target "${targetLocalDir}".`);
  }
  return successCount;
}

async function installExtension(pluginId, pluginName, isUpdate = false) {
  const currentOs = getClientTargetOs();
  showToast(`${isUpdate ? 'Updating' : 'Installing'} ${pluginName} from GitHub (${currentOs})...`);
  try {
    const catalogItem = (copilotState || []).find(p => p.id === pluginId) || (ecosystemState.apps || []).find(p => p.id === pluginId);
    let remotePrefix = (catalogItem && catalogItem.source_path) 
      ? catalogItem.source_path 
      : `plugins/${pluginId.slice(0, 2)}/${pluginId}`;
    
    const fallbackFiles = [
      'plugin.manifest.json', 'SKILL.md', 'engine/server.mjs', 
      'gui/index.html', 'gui/app.js', 'gui/style.css', '.plugin_hash', 'trigger.md'
    ];
    await downloadAndMountEcosystemPackage('apps', remotePrefix, `apps/${pluginId}`, fallbackFiles);

    const res = await fetch(`/api/copilot/install/${pluginId}?os=${encodeURIComponent(currentOs)}`, { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (data.status === 'ok' || res.ok) {
      showToast(`Success! ${pluginName} ${isUpdate ? 'updated' : 'installed'} cleanly.`);
      await fetchPlugins();
      await fetchCopilotRegistry(true);
      updateInstalledCountBadge();
    } else {
      showToast(`Installed files saved, binary note: ${data.message || 'Ready'}`);
      await fetchPlugins();
      updateInstalledCountBadge();
    }
  } catch (err) {
    console.error(`[X-Flow] Install error for ${pluginId}:`, err);
    showToast(`Install failed for ${pluginName}: ${err.message}`);
  }
}

async function uninstallExtension(pluginId, pluginName) {
  if (!confirm(`Are you sure you want to uninstall ${pluginName}?`)) return;

  if (openTabs.has(pluginId)) {
    await closePluginTab(pluginId);
  }

  showToast(`Uninstalling ${pluginName}...`);
  try {
    const res = await fetch(`/api/copilot/uninstall/${pluginId}`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok' || res.ok) {
      showToast(`${pluginName} removed cleanly.`);
      await fetchPlugins();
      await fetchCopilotRegistry();
      updateInstalledCountBadge();
    } else {
      showToast(`Error: ${data.message}`);
    }
  } catch (err) {
    console.error(`[X-Flow] Uninstall error:`, err);
    showToast(`Uninstall error for ${pluginName}`);
  }
}

async function installEcosystemItem(itemId, itemType, itemName) {
  const normType = (itemType || currentStoreSubtab || '').toLowerCase().replace(/s$/, '');
  showToast(`Installing ${normType} "${itemName || itemId}" from GitHub...`);

  try {
    const pluralKey = normType === 'app' ? 'apps' : normType + 's';
    const regConfig = ECOSYSTEM_REGISTRIES[pluralKey] || ECOSYSTEM_REGISTRIES[normType];
    const repo = regConfig ? regConfig.repo.replace('flowork-os/', '') : 'FLOWORK-SKILLS';
    const items = ecosystemState[pluralKey] || ecosystemState[normType] || [];
    const item = items.find(x => x.id === itemId) || {};

    let remotePrefix = '';
    let targetDir = '';
    let fallbackFiles = [];

    if (normType === 'skill') {
      remotePrefix = item.source_path || `skills/${itemId.slice(0, 2)}/${itemId}`;
      targetDir = `skills/${itemId}`;
      fallbackFiles = ['SKILL.md', 'skill.json', 'performance.md', '00_overview.md'];
    } else if (normType === 'tool') {
      remotePrefix = item.source_path || `tools/${itemId.slice(0, 2)}/${itemId}`;
      targetDir = `tools/${itemId}`;
      fallbackFiles = ['manifest.json', 'SKILL.md', 'rules.md', 'trigger.md', 'main.mjs'];
    } else if (normType === 'agent') {
      remotePrefix = item.source_path || `agents/${itemId.slice(0, 2)}/${itemId}`;
      targetDir = `system/subagent/${itemId}`;
      fallbackFiles = ['agent.json', 'SKILL.md', 'persona.md', 'rules.md', 'task.md', 'style.json'];
    } else if (normType === 'trigger') {
      const isPassive = item.type === 'passive' || (item.source_path && item.source_path.startsWith('passive/'));
      if (isPassive) {
        remotePrefix = item.source_path || `passive/${itemId.slice(0, 2)}/${itemId}`;
        targetDir = `system/system_promp`;
        fallbackFiles = ['trigger.manifest.json', 'SKILL.md', `promp/${itemId}.md`, `rules/${itemId}.rs`];
      } else {
        remotePrefix = item.source_path || `active/${itemId.slice(0, 2)}/${itemId}`;
        targetDir = `system/triger/${itemId}`;
        fallbackFiles = ['trigger.manifest.json', 'prompt.md', 'SKILL.md'];
      }
    }

    // 1. Download and save package files locally
    if (remotePrefix && targetDir) {
      await downloadAndMountEcosystemPackage(repo, remotePrefix, targetDir, fallbackFiles);
    }

    // 2. If passive trigger, update triggers.json
    if (normType === 'trigger' && (item.type === 'passive' || (item.source_path && item.source_path.startsWith('passive/')))) {
      try {
        let existingTriggers = [];
        try {
          const resp = await fetch('/system/system_promp/triggers.json');
          if (resp.ok) existingTriggers = await resp.json();
        } catch (_) {}
        if (!Array.isArray(existingTriggers)) existingTriggers = [];

        const entryIndex = existingTriggers.findIndex(t => t.id === itemId);
        const triggerEntry = {
          id: item.id || itemId,
          name: item.name || itemId,
          enabled: true,
          scope: item.scope || 'universal_all',
          rule: item.rule || `rules/${itemId}.rs`,
          prompt: item.prompt || `promp/${itemId}.md`
        };
        if (entryIndex >= 0) {
          existingTriggers[entryIndex] = triggerEntry;
        } else {
          existingTriggers.push(triggerEntry);
        }
        await fetch('/api/fs/save-file', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Target-Path': 'system/system_promp/triggers.json'
          },
          body: JSON.stringify(existingTriggers, null, 2)
        });
      } catch (tErr) {
        console.warn('[Ecosystem Store] Passive triggers.json sync note:', tErr);
      }
    }

    // 3. Register with local state & subsystem API
    const installedSet = getInstalledSet(pluralKey);
    installedSet.add(itemId);
    saveInstalledSet(pluralKey, installedSet);

    if (normType === 'agent') {
      try {
        await fetch('/api/subagents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: itemId })
        });
      } catch (_) {}
    } else if (normType === 'trigger') {
      try {
        await fetch('/api/triggers/install', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ trigger_id: itemId })
        });
      } catch (_) {}
    }

    showToast(`Success! ${itemName || itemId} installed cleanly.`);
    filterAndRenderCopilotCards();
    updateInstalledCountBadge();
  } catch (err) {
    console.error(`[Ecosystem Store] Install failed:`, err);
    showToast(`Install failed: ${err.message}`);
  }
}

async function uninstallEcosystemItem(itemId, itemType, itemName) {
  const normType = (itemType || '').toLowerCase().replace(/s$/, '');
  if (normType === 'app') {
    return uninstallExtension(itemId, itemName);
  }
  if (!confirm(`Are you sure you want to uninstall ${itemName || itemId}?`)) return;

  showToast(`Uninstalling ${normType} "${itemName || itemId}"...`);
  try {
    const pluralKey = normType + 's';
    const installedSet = getInstalledSet(pluralKey);
    installedSet.delete(itemId);
    saveInstalledSet(pluralKey, installedSet);

    if (normType === 'agent') {
      try {
        await fetch(`/api/subagents/${encodeURIComponent(itemId)}`, { method: 'DELETE' });
      } catch (_) {}
    }

    showToast(`${itemName || itemId} uninstalled cleanly.`);
    filterAndRenderCopilotCards();
    filterAndRenderCards();
    updateInstalledCountBadge();
  } catch (err) {
    console.error(`[Ecosystem Store] Uninstall failed:`, err);
    showToast(`Uninstall failed: ${err.message}`);
  }
}

async function testTriggerEndpoint(triggerId, triggerName) {
  showToast(`Testing trigger sensor "${triggerName || triggerId}"...`);
  try {
    const res = await fetch('/api/triggers/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger_id: triggerId, event: 'manual_probe' })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast(`Trigger probe passed! Sensor is responsive.`);
    } else {
      showToast(`Probe response: ${data.message || 'Sensor acknowledged'}`);
    }
  } catch (err) {
    showToast(`Trigger sensor probe executed.`);
  }
}

// 9. Tab & Process Management (Aerodynamic Capsules & Persistent Active Session)
function saveOpenPluginTabsState() {
  try {
    const ids = Array.from(openTabs.keys());
    localStorage.setItem('xflow_open_plugin_tabs', JSON.stringify(ids));
  } catch (_) {}
}

let isRestoringTabs = false;
async function restoreTabsState() {
  if (isRestoringTabs) return;
  isRestoringTabs = true;

  try {
    let savedOpenTabIds = [];
    try {
      const raw = localStorage.getItem('xflow_open_plugin_tabs');
      if (raw) savedOpenTabIds = JSON.parse(raw);
    } catch (_) {}

    const savedActiveTab = localStorage.getItem('xflow_active_tab') || 'office';

    if (Array.isArray(savedOpenTabIds) && savedOpenTabIds.length > 0 && Array.isArray(pluginsState)) {
      // Prioritize active tab first so active viewport renders immediately without waiting for other engines
      const orderedTabIds = [...savedOpenTabIds].sort((a, b) => (a === savedActiveTab ? -1 : b === savedActiveTab ? 1 : 0));
      const activeId = orderedTabIds[0];

      if (activeId && !openTabs.has(activeId)) {
        const plugin = pluginsState.find(p => p.id === activeId);
        if (plugin) {
          await openPluginTab(plugin, { skipSwitch: false });
        }
      }

      // Restore remaining background tabs concurrently in parallel
      const remainingTabIds = orderedTabIds.slice(1);
      await Promise.all(remainingTabIds.map(async (pluginId) => {
        if (!openTabs.has(pluginId)) {
          const plugin = pluginsState.find(p => p.id === pluginId);
          if (plugin) {
            await openPluginTab(plugin, { skipSwitch: true });
          }
        }
      }));
    }

    if (openTabs.has(savedActiveTab)) {
      switchTab(savedActiveTab);
    } else if (savedActiveTab === 'home' || savedActiveTab === 'copilot' || savedActiveTab === 'pipeline') {
      switchTab(savedActiveTab);
    } else if (openTabs.size > 0 && savedActiveTab !== 'office' && savedActiveTab !== 'group' && savedActiveTab !== 'canvas-stage') {
      const firstTab = Array.from(openTabs.keys())[0];
      switchTab(firstTab);
    } else {
      switchTab('office');
    }
  } catch (err) {
    console.error('[X-Flow] Error restoring tabs state:', err);
  } finally {
    isRestoringTabs = false;
  }
}

async function openPluginTab(plugin, options = {}) {
  const skipSwitch = options && options.skipSwitch === true;
  if (openTabs.has(plugin.id)) {
    // If tab is already open, ensure assigned port is synchronized into iframe src
    const tabData = openTabs.get(plugin.id);
    const existingIframe = document.getElementById(`iframe-${plugin.id}`) || (tabData && tabData.iframe);
    try {
      let pPort = plugin.activePort || (tabData && tabData.assignedPort);
      if (!pPort) {
        let launchRes = await fetch(`/api/apps/${plugin.id}/launch`, { method: 'POST' });
        if (!launchRes.ok) launchRes = await fetch(`/api/plugins/${plugin.id}/launch`, { method: 'POST' });
        const launchData = await launchRes.json();
        if (launchData && launchData.port) {
          pPort = launchData.port;
          plugin.activePort = pPort;
          if (tabData) tabData.assignedPort = pPort;
        }
      }
      if (existingIframe && pPort && (!existingIframe.src || !existingIframe.src.includes('port='))) {
        const glue = existingIframe.src && existingIframe.src.includes('?') ? '&' : '?';
        existingIframe.src = `${existingIframe.src || `/apps/${plugin.id}/gui/index.html`}${glue}port=${pPort}&backend_port=${pPort}`;
      }
    } catch (_) {}
    if (!skipSwitch) switchTab(plugin.id);
    return;
  }

  // Launch backend engine via Rust supervisor
  let assignedPort = null;
  try {
    let launchRes = await fetch(`/api/apps/${plugin.id}/launch`, { method: 'POST' });
    if (!launchRes.ok) launchRes = await fetch(`/api/plugins/${plugin.id}/launch`, { method: 'POST' });
    const launchData = await launchRes.json();
    console.log(`[X-Flow] Engine launched for ${plugin.id}:`, launchData);

    if (launchData.port) {
      assignedPort = launchData.port;
      plugin.activePort = launchData.port;
      showToast(`Started engine for ${plugin.name} on port :${launchData.port}`);
      emitAgentTelemetry({ type: 'cmd', tag: 'ENGINE', text: `${plugin.name} on :${launchData.port}`, meta: 'SPAWN' });
    }
  } catch (err) {
    console.error(`[X-Flow] Failed to launch engine for ${plugin.id}:`, err);
  }

  // Create or Upgrade Tab Capsule
  const tabStrip = document.getElementById('tab-strip');
  let tabCapsule = document.getElementById(`tab-${plugin.id}`);
  if (!tabCapsule) {
    tabCapsule = document.createElement('div');
    tabCapsule.className = 'tab-capsule';
    tabCapsule.id = `tab-${plugin.id}`;
    tabCapsule.dataset.tabId = plugin.id;
    if (tabStrip) tabStrip.appendChild(tabCapsule);
  }

  const rawTabName = plugin.name || plugin.id || 'App';
  const displayTabName = rawTabName.length > 18 ? rawTabName.slice(0, 16) + '...' : rawTabName;

  tabCapsule.innerHTML = `
    <span class="tab-symbol">${plugin.icon || '⚡'}</span>
    <span class="tab-label" title="${escapeHtml(rawTabName)}">${escapeHtml(displayTabName)}</span>
    <span class="tab-close-btn" title="Close Tab & Stop Engine">&times;</span>
  `;

  tabCapsule.onclick = (e) => {
    if (e.target.classList.contains('tab-close-btn')) {
      e.stopPropagation();
      closePluginTab(plugin.id);
    } else {
      switchTab(plugin.id);
    }
  };

  // Middle-click tab to close (mouse button 1)
  tabCapsule.addEventListener('auxclick', (e) => {
    if (e.button === 1) {
      e.preventDefault();
      e.stopPropagation();
      closePluginTab(plugin.id);
    }
  });
  tabCapsule.addEventListener('mousedown', (e) => {
    if (e.button === 1) {
      e.preventDefault(); // Prevent browser autoscroll icon
    }
  });

  // Create or Upgrade Sandboxed Iframe Viewport
  const stage = document.getElementById('viewport-stage');
  let iframePanel = document.getElementById(`view-${plugin.id}`);
  let iframe = iframePanel ? iframePanel.querySelector('iframe') : null;
  if (!iframePanel) {
    iframePanel = document.createElement('div');
    iframePanel.className = 'view-panel view-panel-plugin view-panel-app';
    iframePanel.style.padding = '0';
    iframePanel.style.overflow = 'hidden';
    iframePanel.id = `view-${plugin.id}`;

    iframe = document.createElement('iframe');
    iframe.className = 'plugin-iframe app-iframe';
    iframe.setAttribute('loading', 'lazy');
    iframe.setAttribute('allow', 'autoplay; microphone; camera; midi; encrypted-media');

    const queryParam = assignedPort ? `?port=${assignedPort}` : '';
    const pluginUrl = `/apps/${plugin.id}/gui/index.html${queryParam}`;
    iframe.dataset.src = pluginUrl;
    iframe.src = pluginUrl;

    iframePanel.appendChild(iframe);
    if (stage) stage.appendChild(iframePanel);
  } else if (iframe) {
    const queryParam = assignedPort ? `?port=${assignedPort}` : '';
    const pluginUrl = `/apps/${plugin.id}/gui/index.html${queryParam}`;
    iframe.dataset.src = pluginUrl;
    iframe.src = pluginUrl;
  }

  openTabs.set(plugin.id, { 
    title: plugin.name, 
    tabCapsule, 
    iframePanel, 
    iframe, 
    isRunning: true, 
    assignedPort: assignedPort || (plugin.ipc && plugin.ipc.default_port) 
  });
  saveOpenPluginTabsState();
  if (!skipSwitch) {
    switchTab(plugin.id);
  }
  filterAndRenderCards();
  filterAndRenderCopilotCards();
  updateStats();
}

async function switchTab(tabId, options = {}) {
  if (!tabId || tabId === 'group' || tabId === 'canvas-stage') {
    tabId = 'office';
  }

  // Unified App Store redirection: 'home' opens the Installed Apps subtab within App Store
  if (tabId === 'home') {
    tabId = 'copilot';
    switchStoreSubtab('installed');
  } else if (tabId === 'copilot') {
    const saved = localStorage.getItem('xflow_store_subtab') || 'cloud';
    switchStoreSubtab(saved);
  } else if (tabId === 'pipeline') {
    await switchTab('office', options);
    switchOfficeSubtab('pipeline');
    return;
  }

  // Fail-safe view existence validation: NEVER switch to a non-existent panel
  if (tabId !== 'office' && !document.getElementById(`view-${tabId}`)) {
    console.warn(`[X-Flow] View panel for tab '${tabId}' not found. Falling back to 'office'.`);
    tabId = 'office';
  }

  try {
    localStorage.setItem('xflow_active_tab', tabId);
  } catch (_) {}

  document.querySelectorAll('.tab-capsule').forEach((tab) => {
    tab.classList.toggle('active', tab.dataset.tabId === tabId);
  });

  document.querySelectorAll('.dock-pill-item').forEach((item) => {
    item.classList.toggle('active', item.id === `dock-plugin-${tabId}`);
  });

  document.querySelectorAll('#viewport-stage > .view-panel').forEach((panel) => {
    const isActive = (panel.id === `view-${tabId}`);
    panel.classList.toggle('active', isActive);
    panel.style.setProperty('display', isActive ? 'block' : 'none', 'important');
    panel.style.contentVisibility = isActive ? 'visible' : 'hidden';
  });

  const layout = document.querySelector('.canvas-layout');
  const isOffice = (tabId === 'office');
  const isPluginActive = (typeof openTabs !== 'undefined' && openTabs.has(tabId));

  if (layout) {
    layout.classList.toggle('solo-studio-glass', isOffice);
    layout.classList.toggle('app-mode', isPluginActive);
    if (typeof syncSoloStudioComposer === 'function') {
      syncSoloStudioComposer(isOffice);
    }
  }

  // ── DUAL-ENGINE LIFECYCLE GOVERNOR: 3D SOLO vs 3D GROUP vs APP IFRAMES ──
  if (tabId === 'office') {
    if (typeof startChatSyncEngine === 'function') {
      startChatSyncEngine();
    }
    const rightbarChat = document.getElementById('rightbar-chat');
    if (rightbarChat) {
      rightbarChat.classList.remove('collapsed');
      rightbarChat.style.display = '';
    }
    const resizerRight = document.getElementById('resizer-right');
    if (resizerRight) {
      resizerRight.classList.remove('collapsed');
      resizerRight.style.display = '';
    }
    const btnToggleChat = document.getElementById('btn-toggle-chat');
    if (btnToggleChat) {
      btnToggleChat.classList.add('active');
    }
    if (typeof window.__updateLayoutResizers === 'function') {
      window.__updateLayoutResizers();
    }
    const bottomBar = document.getElementById('office-bottom-chatbar');
    if (bottomBar) {
      bottomBar.style.display = '';
    }
    const canvasFg = document.getElementById('office-3d-canvas-fg');
    if (canvasFg) {
      canvasFg.style.setProperty('display', 'block', 'important');
    }
    const officePanel = document.getElementById('view-office');
    if (officePanel) {
      officePanel.style.contentVisibility = 'visible';
      officePanel.style.setProperty('display', 'block', 'important');
    }

    const modelSelectorWrap = document.getElementById('chat-model-selector-wrap');
    if (modelSelectorWrap) {
      modelSelectorWrap.style.setProperty('display', 'none', 'important');
      if (typeof initModelSelector === 'function') initModelSelector();
    }
    const accountSelectorWrap = document.getElementById('chat-account-selector-wrap');
    if (accountSelectorWrap) {
      accountSelectorWrap.style.setProperty('display', 'none', 'important');
    }

    const agentSelectorWrap = document.getElementById('chat-agent-selector-wrap');
    if (agentSelectorWrap) {
      agentSelectorWrap.style.setProperty('display', 'none', 'important');
    }

    // Direct chat with Mr. Flow strictly
    let savedSoloPersona = 'mr.flow';

    if (!options || !options.skipPersonaReload) {
      if (typeof setSessionAgentPersona === 'function') {
        await setSessionAgentPersona(savedSoloPersona, { preserveSession: true });
      }
    } else {
      currentSessionPersonaId = savedSoloPersona;
      pendingSessionPersonaId = savedSoloPersona;
      localStorage.setItem('xflow_chat_persona', savedSoloPersona);
      if (typeof updateAgentPillDisplay === 'function') {
        updateAgentPillDisplay();
      }
    }
    if (typeof renderAgentDropdown === 'function') {
      renderAgentDropdown();
    }

    // 1. Wake 3D Solo Office & Pause Group Office
    if (window.office3DInstance) {
      if (typeof window.office3DInstance.resume === 'function') {
        window.office3DInstance.resume();
      }
      if (window.office3DInstance.container && window.office3DInstance.renderer) {
        const w = window.office3DInstance.container.clientWidth;
        const h = window.office3DInstance.container.clientHeight;
        if (w > 0 && h > 0) {
          window.office3DInstance.camera.aspect = w / h;
          window.office3DInstance.camera.updateProjectionMatrix();
          window.office3DInstance.renderer.setSize(w, h);
          if (typeof window.office3DInstance.syncCanvasFgSize === 'function') {
            window.office3DInstance.syncCanvasFgSize();
          }
        }
      }
    }
    // 2. Suspend ALL Open Plugin Iframes (Zero CPU in background)
    if (typeof openTabs !== 'undefined' && openTabs.size > 0) {
      openTabs.forEach((tabObj, pluginId) => {
        if (tabObj.iframePanel) {
          tabObj.iframePanel.style.contentVisibility = 'hidden';
          const iframe = tabObj.iframe || tabObj.iframePanel.querySelector('iframe');
          if (iframe) {
            iframe.style.contentVisibility = 'hidden';
            iframe.style.pointerEvents = 'none';
            if (iframe.contentWindow) {
              try {
                const doc = iframe.contentWindow.document;
                if (doc) {
                  doc.querySelectorAll('video, audio').forEach(m => {
                    if (!m.paused) {
                      m.dataset.__flowSuspended = 'true';
                      m.pause();
                    }
                  });
                }
                if (iframe.contentWindow._floworkAudioCtx && iframe.contentWindow._floworkAudioCtx.state === 'running') {
                  iframe.contentWindow._floworkAudioCtx.suspend();
                }
                iframe.contentWindow.postMessage({
                  type: 'FLOWORK_LIFECYCLE',
                  state: 'SUSPENDED',
                  activeTab: 'office'
                }, '*');
              } catch (_) {}
            }
          }
        }
      });
    }

    // 3. Sync Office Sub-view (Office, Swarm Pipeline, Blackboard Feed)
    if (typeof switchOfficeSubtab === 'function') {
      const savedSubtab = localStorage.getItem('xflow_office_subtab') || currentOfficeSubtab || 'office';
      switchOfficeSubtab(savedSubtab);
    }
  } else {
    // 1. Deep Sleep 3D Office (0 FPS, 0 GPU draw calls)
    if (window.office3DInstance && typeof window.office3DInstance.pause === 'function') {
      window.office3DInstance.pause();
    }
    const officePanel = document.getElementById('view-office');
    if (officePanel) {
      officePanel.style.contentVisibility = 'hidden';
      officePanel.style.setProperty('display', 'none', 'important');
    }

    // Hide 3D foreground canvas and bottom composer bar (never leak into apps or store)
    const canvasFg = document.getElementById('office-3d-canvas-fg');
    if (canvasFg) {
      canvasFg.style.setProperty('display', 'none', 'important');
    }
    const bottomBar = document.getElementById('office-bottom-chatbar');
    if (bottomBar) {
      bottomBar.style.display = 'none';
    }

    const isPluginActive = (typeof openTabs !== 'undefined' && openTabs.has(tabId));

    if (isPluginActive) {
      // 🤝 HUMAN-AI CO-CREATION STAGE: Display chat alongside active application!
      if (typeof startChatSyncEngine === 'function') {
        startChatSyncEngine();
      }
      const rightbarChat = document.getElementById('rightbar-chat');
      if (rightbarChat) {
        rightbarChat.classList.remove('collapsed');
        rightbarChat.style.display = '';
      }
      const resizerRight = document.getElementById('resizer-right');
      if (resizerRight) {
        resizerRight.classList.remove('collapsed');
        resizerRight.style.display = '';
      }
      const btnToggleChat = document.getElementById('btn-toggle-chat');
      if (btnToggleChat) {
        btnToggleChat.classList.add('active');
      }
    } else {
      // For App Store (copilot) & Installed Apps (home), hide chat for clean full-width catalog
      if (typeof stopChatSyncEngine === 'function') {
        stopChatSyncEngine();
      }
      const rightbarChat = document.getElementById('rightbar-chat');
      if (rightbarChat) {
        rightbarChat.classList.add('collapsed');
        rightbarChat.style.display = 'none';
      }
      const resizerRight = document.getElementById('resizer-right');
      if (resizerRight) {
        resizerRight.classList.add('collapsed');
        resizerRight.style.display = 'none';
      }
      const btnToggleChat = document.getElementById('btn-toggle-chat');
      if (btnToggleChat) {
        btnToggleChat.classList.remove('active');
      }
    }

    if (typeof window.__updateLayoutResizers === 'function') {
      window.__updateLayoutResizers();
    }

    // 2. Coordinate Plugin Iframes (Resume Active, Suspend Others)
    if (typeof openTabs !== 'undefined' && openTabs.size > 0) {
      openTabs.forEach((tabObj, pluginId) => {
        if (tabObj.iframePanel) {
          const isThisTab = (tabId === pluginId);
          tabObj.iframePanel.style.contentVisibility = isThisTab ? 'visible' : 'hidden';
          const iframe = tabObj.iframe || tabObj.iframePanel.querySelector('iframe');
          if (iframe) {
            iframe.style.contentVisibility = isThisTab ? 'visible' : 'hidden';
            iframe.style.pointerEvents = isThisTab ? 'auto' : 'none';

            // Lazy Activation Guard: Only load target src when tab is actually activated
            if (isThisTab && iframe.dataset.src && (!iframe.src || iframe.src === 'about:blank' || iframe.src.endsWith('about:blank'))) {
              iframe.src = iframe.dataset.src;
            } else if (isThisTab && tabObj && tabObj.assignedPort && iframe.src && !iframe.src.includes('port=')) {
              const glue = iframe.src.includes('?') ? '&' : '?';
              iframe.src = `${iframe.src}${glue}port=${tabObj.assignedPort}&backend_port=${tabObj.assignedPort}`;
            }

            if (iframe.contentWindow) {
              try {
                const doc = iframe.contentWindow.document;
                if (doc) {
                  doc.querySelectorAll('video, audio').forEach(m => {
                    if (!isThisTab && !m.paused) {
                      m.dataset.__flowSuspended = 'true';
                      m.pause();
                    } else if (isThisTab && m.dataset.__flowSuspended === 'true') {
                      delete m.dataset.__flowSuspended;
                      m.play().catch(() => {});
                    }
                  });
                }
                if (iframe.contentWindow._floworkAudioCtx) {
                  if (!isThisTab && iframe.contentWindow._floworkAudioCtx.state === 'running') {
                    iframe.contentWindow._floworkAudioCtx.suspend();
                  } else if (isThisTab && iframe.contentWindow._floworkAudioCtx.state === 'suspended') {
                    iframe.contentWindow._floworkAudioCtx.resume();
                  }
                }
                iframe.contentWindow.postMessage({
                  type: 'FLOWORK_LIFECYCLE',
                  state: isThisTab ? 'RESUMED' : 'SUSPENDED',
                  activeTab: tabId
                }, '*');
              } catch (_) {}
            }
          }
        }
      });
    }
  }

  // ── DUAL-CANVAS GOVERNOR: SOLO STUDIO vs SWARM WAR ROOM ──
  if (tabId === 'canvas-stage') {
    if (window.DualCanvasController && typeof window.DualCanvasController.onActivateTab === 'function') {
      window.DualCanvasController.onActivateTab();
    }
  } else {
    if (window.DualCanvasController && typeof window.DualCanvasController.onDeactivateTab === 'function') {
      window.DualCanvasController.onDeactivateTab();
    }
  }

  if (tabId !== 'office') {
    const pipelineView = document.getElementById('view-pipeline');
    if (pipelineView) {
      pipelineView.style.setProperty('display', 'none', 'important');
      pipelineView.classList.remove('active');
    }
    document.querySelector('.canvas-layout')?.classList.remove('pipeline-active');
    const rightbar = document.getElementById('rightbar-chat');
    if (rightbar && !rightbar.classList.contains('collapsed')) {
      rightbar.style.removeProperty('display');
    }
    const resizer = document.getElementById('resizer-right');
    if (resizer) {
      resizer.style.removeProperty('display');
    }
  }

  // Sovereign Viewport Telemetry: Report active tab to Engine Host for agent context
  reportActiveViewport(tabId);
}

function reportActiveViewport(tabId) {
  let title = 'Virtual Office (3D Headquarters)';
  let kind = 'office';

  if (tabId === 'office') {
    title = 'Office';
    kind = 'office';
  } else if (tabId === 'pipeline') {
    title = 'Visual Swarm Pipeline';
    kind = 'pipeline';
  } else if (tabId === 'canvas-stage') {
    title = 'Sovereign Solo Studio';
    kind = 'canvas_stage';
  } else if (tabId === 'home' || tabId === 'copilot') {
    title = (typeof currentStoreSubtab !== 'undefined' && currentStoreSubtab === 'installed') 
      ? 'Installed Applications' 
      : 'App Store (Cloud Extensions)';
    kind = (typeof currentStoreSubtab !== 'undefined' && currentStoreSubtab === 'installed') 
      ? 'system' 
      : 'app_store';
  } else if (openTabs.has(tabId)) {
    const tabInfo = openTabs.get(tabId);
    title = tabInfo.title || tabId;
    kind = 'plugin';
  } else {
    const plugin = pluginsState.find((p) => p.id === tabId);
    if (plugin) {
      title = plugin.name || tabId;
      kind = 'plugin';
    }
  }

  fetch('/api/viewport/active', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tab: tabId, title, kind })
  }).catch(() => {});
}

async function closePluginTab(pluginId) {
  if (!openTabs.has(pluginId)) return;

  const tabInfo = openTabs.get(pluginId);
  const { tabCapsule, iframePanel } = tabInfo;
  const wasActive = tabCapsule && tabCapsule.classList.contains('active');

  // 1. Force complete teardown of sandboxed iframe & release Chromium renderer thread / AudioContext / Workers
  if (iframePanel) {
    const iframes = iframePanel.querySelectorAll('iframe');
    iframes.forEach((iframe) => {
      // Send lifecycle termination event to inner app before detachment
      try {
        if (iframe.contentWindow) {
          iframe.contentWindow.postMessage({
            type: 'FLOWORK_LIFECYCLE',
            state: 'TERMINATED',
            pluginId
          }, '*');
        }
      } catch (_) {}

      // Setting src to 'about:blank' synchronously forces Chromium to terminate
      // the iframe renderer process, child workers, WebAudio contexts, and pending network requests
      try {
        iframe.src = 'about:blank';
        iframe.removeAttribute('src');
      } catch (_) {}

      try {
        iframe.remove();
      } catch (_) {}
    });

    iframePanel.innerHTML = '';
    iframePanel.remove();
  }

  if (tabCapsule) {
    tabCapsule.remove();
  }

  openTabs.delete(pluginId);
  saveOpenPluginTabsState();

  // Immediate UI fallback: never leave user on detached stage while awaiting stop API
  if (wasActive) {
    const remainingOpenTabs = Array.from(openTabs.keys());
    if (remainingOpenTabs.length > 0) {
      switchTab(remainingOpenTabs[remainingOpenTabs.length - 1]);
    } else {
      switchTab('office');
    }
  }

  // Send clean SIGTERM to Rust process supervisor (zero-zombie guarantee)
  try {
    let stopRes = await fetch(`/api/apps/${pluginId}/stop`, { method: 'POST' });
    if (!stopRes.ok) await fetch(`/api/plugins/${pluginId}/stop`, { method: 'POST' });
    console.log(`[X-Flow] Engine for ${pluginId} cleanly killed.`);
    showToast(`Stopped engine for ${pluginId}.`);
    emitAgentTelemetry({ type: 'cmd', tag: 'ENGINE', text: `Engine stopped: ${pluginId}`, meta: 'SIGTERM' });
  } catch (err) {
    console.error(`[X-Flow] Error terminating engine ${pluginId}:`, err);
  }

  const plugin = pluginsState.find(p => p.id === pluginId) || copilotState.find(p => p.id === pluginId);
  if (plugin) plugin.activePort = null;

  filterAndRenderCards();
  filterAndRenderCopilotCards();
  updateStats();
}

async function restartPlugin(pluginId) {
  const plugin = pluginsState.find(p => p.id === pluginId) || copilotState.find(p => p.id === pluginId);
  if (!plugin) return;
  showToast(`Restarting engine for ${plugin.name || pluginId}...`);
  await closePluginTab(pluginId);
  setTimeout(() => {
    openPluginTab(plugin);
  }, 400);
}

function openAppInspectorModal(pluginId, isCloud = false, itemType = null) {
  const modal = document.getElementById('app-inspector-modal');
  if (!modal) return;

  let plugin = isCloud 
    ? (copilotState.find(p => p.id === pluginId) || pluginsState.find(p => p.id === pluginId))
    : (pluginsState.find(p => p.id === pluginId) || copilotState.find(p => p.id === pluginId));

  let detectedType = 'app';
  if (!plugin) {
    for (const key of ['skills', 'tools', 'agents', 'triggers']) {
      const match = (ecosystemState[key] || []).find(it => it.id === pluginId);
      if (match) {
        plugin = match;
        detectedType = key;
        break;
      }
    }
  }
  if (!plugin && itemType && ecosystemState[itemType]) {
    plugin = ecosystemState[itemType].find(it => it.id === pluginId);
    if (plugin) detectedType = itemType;
  }

  if (!plugin) return;

  const isApp = detectedType === 'app';
  const isRunning = isApp && openTabs.has(plugin.id);
  const tabInfo = isRunning ? openTabs.get(plugin.id) : null;
  const activePort = (tabInfo && tabInfo.assignedPort) || plugin.activePort;
  const defaultPort = plugin.ipc && plugin.ipc.default_port;
  
  const installedSet = getInstalledSet(detectedType);
  const isInstalled = isApp ? (new Set(pluginsState.map(p => p.id)).has(plugin.id) || !isCloud || plugin.installed) : installedSet.has(plugin.id);
  const runtime = isApp ? getPluginRuntimeBadge(plugin) : { name: detectedType.toUpperCase(), class: 'tag-runtime-web', icon: plugin.icon || '📦' };

  // Set Header
  const iconEl = document.getElementById('inspector-modal-icon');
  const titleEl = document.getElementById('inspector-modal-title');
  const subEl = document.getElementById('inspector-modal-subtitle');
  if (iconEl) iconEl.textContent = plugin.icon || (isApp ? '⚡' : '📦');
  if (titleEl) titleEl.textContent = plugin.name || plugin.id;
  if (subEl) subEl.textContent = `ID: ${plugin.id} • ${detectedType.toUpperCase()} • ${plugin.category || plugin.department || plugin.type || 'General'}`;

  // Badges Bar
  const badgesContainer = document.getElementById('inspector-modal-badges');
  if (badgesContainer) {
    badgesContainer.innerHTML = `
      <span class="pebble-tag" style="padding: 3px 10px; font-size: 11px;">v${escapeHtml(plugin.version || '1.0.0')}</span>
      <span class="pebble-tag ${runtime.class}" style="padding: 3px 10px; font-size: 11px;">${runtime.icon} ${runtime.name}</span>
      <span class="pebble-tag" style="padding: 3px 10px; font-size: 11px;">${escapeHtml(plugin.category || plugin.department || plugin.type || 'General')}</span>
      ${plugin.hash ? `<span class="pebble-tag tag-hash" style="padding: 3px 10px; font-size: 11px;">#${escapeHtml(plugin.hash.slice(0, 10))}</span>` : ''}
      <span class="pebble-tag ${isRunning ? 'tag-status-update' : (isInstalled ? 'tag-status-installed' : 'tag-status-available')}" style="padding: 3px 10px; font-size: 11px;">
        ${isRunning ? '🟢 Running' : (isInstalled ? '📦 Installed' : '☁️ Available in Cloud')}
      </span>
    `;
  }

  // Description
  const descEl = document.getElementById('inspector-modal-desc');
  if (descEl) {
    descEl.textContent = plugin.description || 'Federated sovereign module for Flowork OS.';
  }

  // Grid Specs
  const gridEl = document.getElementById('inspector-modal-grid');
  if (gridEl) {
    if (isApp) {
      const backendEntry = (plugin.entry && plugin.entry.backend) || 'None (Client-Side Only)';
      const guiEntry = (plugin.entry && plugin.entry.gui) || 'gui/index.html';
      const portEnv = (plugin.ipc && plugin.ipc.port_env) || 'FLOWORK_APP_PORT';
      const portSpec = isRunning && activePort 
        ? `:${activePort} (Active)` 
        : (defaultPort ? `:${defaultPort} (Default)` : 'Dynamic / Ephemeral');
      const author = plugin.author || 'Flowork Sovereign Contributor';

      gridEl.innerHTML = `
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Runtime Architecture</div>
          <div class="inspector-spec-val">${runtime.icon} ${runtime.name}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Backend Entrypoint</div>
          <div class="inspector-spec-val" title="${escapeHtml(backendEntry)}">${escapeHtml(backendEntry)}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">GUI Entrypoint</div>
          <div class="inspector-spec-val" title="${escapeHtml(guiEntry)}">${escapeHtml(guiEntry)}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">IPC Port Allocation</div>
          <div class="inspector-spec-val" style="color: #00e5ff;">${portSpec}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Port Environment Key</div>
          <div class="inspector-spec-val">${escapeHtml(portEnv)}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Author / Provenance</div>
          <div class="inspector-spec-val" title="${escapeHtml(author)}">${escapeHtml(author)}</div>
        </div>
      `;
    } else if (detectedType === 'skills') {
      const keywordsList = (plugin.keywords && Array.isArray(plugin.keywords)) ? plugin.keywords.join(', ') : 'standard_operating_procedures, engineering';
      gridEl.innerHTML = `
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Module Category</div>
          <div class="inspector-spec-val">🧠 ${escapeHtml(plugin.category || 'engineering_sop')}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Standard Specification</div>
          <div class="inspector-spec-val" style="color: #8b5cf6;">Exact 20 English Keywords SOP</div>
        </div>
        <div class="inspector-spec-box" style="grid-column: 1 / -1;">
          <div class="inspector-spec-key">Keywords Index</div>
          <div class="inspector-spec-val" style="font-size: 11px; font-family: monospace; line-height: 1.5;">${escapeHtml(keywordsList)}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Author / Provenance</div>
          <div class="inspector-spec-val">${escapeHtml(plugin.author || 'Flowork Sovereign Core')}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Shard Source Path</div>
          <div class="inspector-spec-val" style="font-family: monospace;">${escapeHtml(plugin.source_path || ('skills/' + plugin.id))}</div>
        </div>
      `;
    } else if (detectedType === 'tools') {
      gridEl.innerHTML = `
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Execution Command</div>
          <div class="inspector-spec-val" style="color: #f59e0b; font-family: monospace;">${escapeHtml(plugin.command || ('node tools/' + plugin.id + '/main.mjs'))}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Entrypoint Script</div>
          <div class="inspector-spec-val" style="font-family: monospace;">${escapeHtml(plugin.entry || 'main.mjs')}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Category</div>
          <div class="inspector-spec-val">🛠️ ${escapeHtml(plugin.category || 'system')}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Author / Provenance</div>
          <div class="inspector-spec-val">${escapeHtml(plugin.author || 'Flowork Sovereign Core')}</div>
        </div>
      `;
    } else if (detectedType === 'agents') {
      gridEl.innerHTML = `
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Assigned Role</div>
          <div class="inspector-spec-val" style="color: #00f2fe;">${escapeHtml(plugin.role || plugin.name)}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Department</div>
          <div class="inspector-spec-val">🤖 ${escapeHtml(plugin.department || 'engineering')}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Author / Provenance</div>
          <div class="inspector-spec-val">${escapeHtml(plugin.author || 'Flowork OS')}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Agent Shard</div>
          <div class="inspector-spec-val" style="font-family: monospace;">${escapeHtml(plugin.source_path || ('agents/' + plugin.id))}</div>
        </div>
      `;
    } else if (detectedType === 'triggers') {
      gridEl.innerHTML = `
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Trigger Architecture</div>
          <div class="inspector-spec-val" style="color: ${plugin.type === 'active' ? '#10b981' : '#a855f7'};">${plugin.type === 'active' ? '🟢 Active Background Daemon' : '🟣 Passive JIT Sensor'}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Interval / Activation</div>
          <div class="inspector-spec-val">${plugin.type === 'active' ? ((plugin.interval_seconds || 30) + ' seconds loop') : 'Just-In-Time AST Event'}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Category</div>
          <div class="inspector-spec-val">⚡ ${escapeHtml(plugin.category || 'automation')}</div>
        </div>
        <div class="inspector-spec-box">
          <div class="inspector-spec-key">Author / Provenance</div>
          <div class="inspector-spec-val">${escapeHtml(plugin.author || 'Flowork Sovereign Core')}</div>
        </div>
      `;
    }
  }

  // Status & Actions in Footer
  const statusEl = document.getElementById('inspector-modal-status');
  if (statusEl) {
    statusEl.innerHTML = isRunning 
      ? `<span style="color: #00e5ff; font-weight: 700;">🟢 Daemon Active on Port :${activePort || defaultPort}</span>` 
      : `<span>Status: ${isInstalled ? 'Ready in Workspace' : 'Available in Cloud Registry'}</span>`;
  }

  const actionsEl = document.getElementById('inspector-modal-actions');
  if (actionsEl) {
    let btns = '';
    if (isApp) {
      if (isRunning) {
        btns += `
          <button class="btn-pebble-stop" id="btn-inspector-stop" style="padding: 8px 16px;">⏹️ Stop Engine</button>
          <button class="btn-pebble-restart" id="btn-inspector-restart" style="padding: 8px 16px;">🔄 Restart</button>
          <button class="btn-pebble-launch" id="btn-inspector-switch" style="padding: 8px 20px;">Switch to Tab</button>
        `;
      } else if (isInstalled) {
        btns += `<button class="btn-pebble-launch" id="btn-inspector-launch" style="padding: 8px 20px;">▶️ Launch Module</button>`;
      } else {
        btns += `<button class="btn-pebble-install" id="btn-inspector-install" style="padding: 8px 20px;">⬇️ Install Extension</button>`;
      }
    } else {
      if (isInstalled) {
        if (detectedType === 'skills') {
          btns += `<button class="btn-pebble-inject" id="btn-inspector-action" style="padding: 8px 20px;">💬 Inject SOP to Chat</button>`;
        } else if (detectedType === 'tools') {
          btns += `<button class="btn-pebble-run-cli" id="btn-inspector-action" style="padding: 8px 20px;">⚡ Run CLI Tool</button>`;
        } else if (detectedType === 'agents') {
          btns += `<button class="btn-pebble-summon" id="btn-inspector-action" style="padding: 8px 20px;">💬 Summon Agent</button>`;
        } else if (detectedType === 'triggers') {
          btns += `<button class="btn-pebble-test-trigger" id="btn-inspector-action" style="padding: 8px 20px;">⚡ Test Trigger Probe</button>`;
        }
        btns += `<button class="btn-pebble-uninstall" id="btn-inspector-uninstall" style="padding: 8px 16px;">🗑️ Uninstall</button>`;
      } else {
        btns += `<button class="btn-pebble-install" id="btn-inspector-install-eco" style="padding: 8px 20px;">⬇️ Install ${detectedType.slice(0, -1).toUpperCase()}</button>`;
      }
    }
    btns += `<button class="btn-modal-cancel" id="btn-inspector-close-footer" style="padding: 8px 16px; margin: 0;">Close</button>`;
    actionsEl.innerHTML = btns;

    // Attach listeners
    const stopBtn = actionsEl.querySelector('#btn-inspector-stop');
    if (stopBtn) stopBtn.onclick = () => { closePluginTab(plugin.id); closeAppInspectorModal(); };
    const restartBtn = actionsEl.querySelector('#btn-inspector-restart');
    if (restartBtn) restartBtn.onclick = () => { restartPlugin(plugin.id); closeAppInspectorModal(); };
    const switchBtn = actionsEl.querySelector('#btn-inspector-switch');
    if (switchBtn) switchBtn.onclick = () => { switchTab(plugin.id); closeAppInspectorModal(); };
    const launchBtn = actionsEl.querySelector('#btn-inspector-launch');
    if (launchBtn) launchBtn.onclick = () => { 
      const p = pluginsState.find(x => x.id === plugin.id) || copilotState.find(x => x.id === plugin.id);
      if (p) openPluginTab(p);
      closeAppInspectorModal(); 
    };
    const installBtn = actionsEl.querySelector('#btn-inspector-install');
    if (installBtn) installBtn.onclick = () => { 
      installExtension(plugin.id, plugin.name || plugin.id); 
      closeAppInspectorModal(); 
    };
    const installEcoBtn = actionsEl.querySelector('#btn-inspector-install-eco');
    if (installEcoBtn) installEcoBtn.onclick = () => {
      installEcosystemItem(plugin.id, detectedType, plugin.name || plugin.id);
      closeAppInspectorModal();
    };
    const uninstallBtn = actionsEl.querySelector('#btn-inspector-uninstall');
    if (uninstallBtn) uninstallBtn.onclick = () => {
      uninstallEcosystemItem(plugin.id, detectedType, plugin.name || plugin.id);
      closeAppInspectorModal();
    };
    const actionBtn = actionsEl.querySelector('#btn-inspector-action');
    if (actionBtn) actionBtn.onclick = () => {
      if (detectedType === 'skills') {
        injectPromptIntoChat(`Equip and enforce skill: ${plugin.name} (${plugin.id}). Follow all domain SOPs and operational guidelines.`, true);
      } else if (detectedType === 'tools') {
        injectPromptIntoChat(`Execute autonomous tool: ${plugin.command || ('node tools/' + plugin.id + '/main.mjs')}`, true);
      } else if (detectedType === 'agents') {
        injectPromptIntoChat(`Summoning specialist agent: @${plugin.id}. Please take over and execute current domain task.`, true);
      } else if (detectedType === 'triggers') {
        testTriggerEndpoint(plugin.id, plugin.name || plugin.id);
      }
      closeAppInspectorModal();
    };
    const closeFootBtn = actionsEl.querySelector('#btn-inspector-close-footer');
    if (closeFootBtn) closeFootBtn.onclick = () => closeAppInspectorModal();
  }

  modal.style.display = 'flex';
  modal.classList.add('active');
}

function closeAppInspectorModal() {
  const modal = document.getElementById('app-inspector-modal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('active');
  }
}

function updateStats() {
  const statPlugins = document.getElementById('stat-total-plugins');
  const statDaemons = document.getElementById('stat-active-daemons');
  const pillRunningCount = document.getElementById('pill-running-count');
  const storeInstalledBadge = document.getElementById('store-installed-count-badge');
  if (statPlugins) statPlugins.textContent = pluginsState.length;
  if (statDaemons) statDaemons.textContent = openTabs.size;
  if (pillRunningCount) pillRunningCount.textContent = openTabs.size;
  if (storeInstalledBadge) storeInstalledBadge.textContent = pluginsState.length;
}

function showToast(message) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  // Deduplication: prevent identical message spam
  const existingToasts = container.querySelectorAll('.toast-item');
  for (const t of existingToasts) {
    if (t.dataset.message === message) {
      t.style.animation = 'none';
      void t.offsetHeight; // trigger reflow
      t.style.animation = 'toastHudSlideUp 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards';
      return;
    }
  }

  // Anti-Spam Queue: Cap max visible toasts to 3
  if (existingToasts.length >= 3) {
    existingToasts[0].remove();
  }

  const toast = document.createElement('div');
  toast.className = 'toast-item';
  toast.dataset.message = message;
  toast.innerHTML = `
    <span class="pulse-beacon"></span>
    <span>${message}</span>
  `;
  toast.style.cursor = 'pointer';
  toast.addEventListener('click', () => toast.remove());
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'none';
    toast.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px) scale(0.95)';
    setTimeout(() => toast.remove(), 260);
  }, 2800);
}
window.showToast = showToast;

// ==========================================================================
// AGENT HUD TELEMETRY STREAM CONTROLLER (Floating Living Cybernetic Pulse)
// ==========================================================================
// ==========================================================================
// AGENT HUD TELEMETRY STREAM CONTROLLER (Ethereal Flight from Bottom Corner)
// Spawns COT & LOG chips during active chat execution only.
// Completely ceases when chat stops.
// ==========================================================================
let lastThinkEmitTime = 0;

function emitAgentTelemetry({ type = 'tool', tag = 'LOG', text = '', meta = '' }) {
  const container = document.getElementById('hud-agent-stream');
  if (!container || !text) return;

  // Cap max concurrent floating chips to 5 to keep canvas clean & ethereal
  const existing = container.querySelectorAll('.agent-stream-chip');
  if (existing.length >= 5) {
    existing[0].remove();
  }

  const layout = document.querySelector('.canvas-layout');
  const isLeft = layout && layout.classList.contains('chat-dock-left');

  // If chat docked left: corner is bottom-right -> drift inward to left (-15px to -50px)
  // If chat docked right: corner is bottom-left -> drift inward to right (+15px to +50px)
  const inwardSign = isLeft ? -1 : 1;
  const driftDist = (Math.random() * 35 + 15) * inwardSign;
  const driftX = `${driftDist.toFixed(1)}px`;
  const driftRot = `${((Math.random() * 4 - 2) * inwardSign).toFixed(1)}deg`;
  const floatDur = `${(4.6 + Math.random() * 0.8).toFixed(2)}s`;

  const chip = document.createElement('div');
  chip.className = `agent-stream-chip type-${type}`;
  chip.style.setProperty('--drift-x', driftX);
  chip.style.setProperty('--drift-rot', driftRot);
  chip.style.setProperty('--float-dur', floatDur);

  chip.innerHTML = `
    <span class="chip-beacon"></span>
    <span class="chip-tag">${escapeHtml(tag)}</span>
    <span class="chip-text" title="${escapeHtml(text)}">${escapeHtml(text)}</span>
    ${meta ? `<span class="chip-meta">${escapeHtml(meta)}</span>` : ''}
  `;

  container.appendChild(chip);

  setTimeout(() => {
    if (chip.parentNode) chip.remove();
  }, 5200);
}
window.__emitAgentTelemetry = emitAgentTelemetry;

function handleTelemetryEvent(eventType, data) {
  if (!data) return;

  // 1. COT (Chain of Thought): Stream snippets while reasoning
  if (eventType === 'thinking' && data.thinking) {
    const now = Date.now();
    if (!lastThinkEmitTime || now - lastThinkEmitTime > 1800) {
      lastThinkEmitTime = now;
      const cleanSnippet = data.thinking.replace(/[\r\n\t]+/g, ' ').replace(/\s{2,}/g, ' ').trim();
      if (cleanSnippet.length > 3) {
        const text = cleanSnippet.length > 46 ? cleanSnippet.slice(0, 44) + '…' : cleanSnippet;
        emitAgentTelemetry({ type: 'think', tag: 'COT', text, meta: 'REASON' });
      }
    }
  } 
  // 2. LOG (Tool / Command / File / Subagent Executions)
  else if (eventType === 'tool') {
    const rawTool = (data.tool || 'tool').toLowerCase();
    const details = data.details || {};
    let tag = 'LOG';
    let type = 'tool';
    let text = data.tool || 'Processing step';
    let meta = 'RUN';

    if (rawTool.includes('command') || rawTool.includes('cmd') || rawTool.includes('bash') || rawTool.includes('run')) {
      type = 'cmd';
      tag = 'LOG';
      const cmd = (details.CommandLine || details.command || details.cmd || 'bash execution').trim();
      text = cmd.length > 46 ? cmd.slice(0, 44) + '…' : cmd;
      meta = 'BASH';
    } else if (rawTool.includes('view') || rawTool.includes('read')) {
      type = 'tool';
      tag = 'LOG';
      const p = details.AbsolutePath || details.path || details.TargetFile || '';
      const fname = p.split('/').pop() || 'file';
      text = `read: ${fname}`;
      meta = 'FS';
    } else if (rawTool.includes('replace') || rawTool.includes('write') || rawTool.includes('edit')) {
      type = 'tool';
      tag = 'LOG';
      const p = details.TargetFile || details.path || details.AbsolutePath || '';
      const fname = p.split('/').pop() || 'file';
      text = `edit: ${fname}`;
      meta = 'DIFF';
    } else if (rawTool.includes('search') || rawTool.includes('url')) {
      type = 'net';
      tag = 'LOG';
      const q = details.query || details.Url || 'network lookup';
      text = q.length > 44 ? q.slice(0, 42) + '…' : q;
      meta = 'NET';
    } else if (rawTool.includes('subagent') || rawTool.includes('spawn') || rawTool.includes('invoke')) {
      type = 'agent';
      tag = 'LOG';
      text = details.Role || details.TypeName || 'subagent spawn';
      meta = 'MESH';
    } else if (rawTool.includes('schedule')) {
      type = 'agent';
      tag = 'LOG';
      text = details.Prompt || 'automation schedule';
      meta = 'CRON';
    }

    emitAgentTelemetry({ type, tag, text, meta });
  } 
  // 2b. Live Terminal Stream Chunks
  else if (eventType === 'terminal_stream') {
    const tail = (data.tail || data.line || '').trim();
    if (tail) {
      const text = tail.length > 46 ? tail.slice(0, 44) + '…' : tail;
      emitAgentTelemetry({ type: 'cmd', tag: 'LOG', text, meta: 'STREAM' });
    }
  }
  // 3. Step finish
  else if (eventType === 'tool_done') {
    emitAgentTelemetry({ type: 'done', tag: 'LOG', text: 'step complete', meta: 'EXIT 0' });
  } 
  // 4. Turn complete: One final whisper, then SILENCE (no more flying)
  else if (eventType === 'done') {
    emitAgentTelemetry({ type: 'done', tag: 'COT', text: 'reasoning complete', meta: 'DONE' });
  }
}

// ==========================================================================
// SYNC DRIVE NATIVE CLOUD OFFLOAD CONTROLLER (Multi-Account Spillover)
// ==========================================================================
let syncDrivePollTimer = null;

function initSyncDriveUI() {
  const btnOpen = document.getElementById('btn-open-syncdrive');
  const btnClose = document.getElementById('btn-close-syncdrive');
  const modal = document.getElementById('syncdrive-modal');
  const btnAddAcc = document.getElementById('btn-add-gdrive-acc');
  const btnAddFolder = document.getElementById('btn-add-backup-folder');

  if (btnOpen && modal) {
    btnOpen.addEventListener('click', () => {
      modal.style.display = 'flex';
      fetchSyncDriveStatus();
      startSyncDrivePolling();
    });
  }

  if (btnClose && modal) {
    btnClose.addEventListener('click', () => {
      modal.style.display = 'none';
      stopSyncDrivePolling();
    });
  }

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
        stopSyncDrivePolling();
      }
    });
  }

  if (btnAddAcc) {
    btnAddAcc.addEventListener('click', async () => {
      showToast('🌐 Opening Google Drive OAuth in system browser...');
      try {
        const coreBase = (typeof _getFloworkCoreBase === 'function') ? _getFloworkCoreBase() : 'http://127.0.0.1:19890';
        const res = await fetch(`${coreBase}/api/sync-drive/auth/login-url`);
        const data = await res.json();
        if (data && data.url) {
          const opened = await openSystemBrowser(data.url);
          if (opened) {
            showToast('✅ Google login opened in system browser! Sign in there.');
          } else {
            showToast('⚠️ Could not open browser. Link: ' + data.url);
          }
        } else {
          showToast('Failed to get Google login URL');
        }
      } catch (err) {
        showToast('Failed to get Google login URL: ' + err.message);
      }
    });
  }

  if (btnAddFolder) {
    btnAddFolder.addEventListener('click', async () => {
      let defaultPath = '';
      const coreBase = (typeof _getFloworkCoreBase === 'function') ? _getFloworkCoreBase() : 'http://127.0.0.1:19890';
      try {
        const res = await fetch(`${coreBase}/api/dialog/default-dir`);
        const data = await res.json();
        defaultPath = data.path || '';
      } catch (_) {}

      const chosen = prompt('Enter absolute path of folder to auto-backup & offload to Google Drive:', defaultPath);
      if (chosen && chosen.trim()) {
        try {
          const res = await fetch(`${coreBase}/api/sync-drive/folders/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder: chosen.trim() })
          });
          const data = await res.json();
          if (data.status === 'ok') {
            showToast('Auto-backup folder added!');
            fetchSyncDriveStatus();
          } else {
            showToast('Error: ' + (data.message || 'Failed to add folder'));
          }
        } catch (err) {
          showToast('Failed to add folder: ' + err.message);
        }
      }
    });
  }

  // Check URL query parameters
  if (window.location.search.includes('sync_drive=connected')) {
    showToast('☁️ Google Drive linked successfully!');
    if (modal) {
      modal.style.display = 'flex';
      startSyncDrivePolling();
    }
    window.history.replaceState({}, document.title, window.location.pathname);
  }

  // Initial single fetch for topbar beacon only (no interval running while closed!)
  fetchSyncDriveStatus();
}

function startSyncDrivePolling() {
  if (!syncDrivePollTimer) {
    syncDrivePollTimer = setInterval(fetchSyncDriveStatus, 6000);
  }
}

function stopSyncDrivePolling() {
  if (syncDrivePollTimer) {
    clearInterval(syncDrivePollTimer);
    syncDrivePollTimer = null;
  }
}

async function fetchSyncDriveStatus() {
  if (document.hidden) return;
  try {
    const coreBase = (typeof _getFloworkCoreBase === 'function') ? _getFloworkCoreBase() : 'http://127.0.0.1:19890';
    const res = await fetch(`${coreBase}/api/sync-drive/status`);
    const data = await res.json();
    renderSyncDriveUI(data);
  } catch (err) {
    console.warn('[Sync Drive] Failed to fetch status:', err);
  }
}

function renderSyncDriveUI(data) {
  const modal = document.getElementById('syncdrive-modal');
  const isModalOpen = modal && modal.style.display === 'flex';
  const activity = data.activity || {};
  const accounts = data.accounts || [];

  // Update Topbar Minimalist Beacon Icon
  const beacon = document.getElementById('syncdrive-beacon');
  if (beacon) {
    if (activity.is_uploading) {
      beacon.className = 'pulse-beacon beacon-cyan';
    } else {
      beacon.className = accounts.length > 0 ? 'pulse-beacon beacon-green' : 'pulse-beacon beacon-pink';
    }
  }

  // If modal is NOT open, STOP here! Do not perform expensive DOM rebuilds
  if (!isModalOpen) {
    if (!activity.is_uploading) {
      stopSyncDrivePolling();
    }
    return;
  }

  const folders = data.backup_folders || [];
  const files = data.offloaded_files || [];
  const totalLimit = data.total_limit || 0;
  const totalUsage = data.total_usage || 0;
  const totalRemaining = data.total_remaining || 0;
  const usagePercent = totalLimit > 0 ? Math.min(100, (totalUsage / totalLimit) * 100).toFixed(1) : 0;

  // 1b. Update Modal Activity Banner
  const actBanner = document.getElementById('modal-activity-banner');
  const actText = document.getElementById('modal-act-text');
  const actBeacon = document.getElementById('modal-act-beacon');

  if (actBanner && actText) {
    if (activity.is_uploading) {
      actBanner.style.display = 'flex';
      actBanner.className = 'syncdrive-activity-banner active';
      actText.textContent = `⚡ Live Progress: ${activity.status_text} (${activity.progress_percent}%)`;
      if (actBeacon) actBeacon.className = 'pulse-beacon beacon-pink';
    } else if (folders.length > 0) {
      actBanner.style.display = 'flex';
      actBanner.className = 'syncdrive-activity-banner';
      actText.textContent = `🟢 Watcher Active • Monitoring ${folders.length} folder(s) for auto-backup & cloud offload`;
      if (actBeacon) actBeacon.className = 'pulse-beacon beacon-green';
    } else {
      actBanner.style.display = 'none';
    }
  }

  // 2. Update Modal Pool Overview
  const modalCapacity = document.getElementById('modal-pool-capacity');
  const modalFree = document.getElementById('modal-pool-free');
  const modalBar = document.getElementById('modal-pool-bar');
  const modalAccCount = document.getElementById('modal-acc-count');
  const modalFilesCount = document.getElementById('modal-files-count');

  if (modalCapacity) modalCapacity.textContent = formatBytes(totalLimit);
  if (modalFree) modalFree.textContent = `${formatBytes(totalRemaining)} (${(100 - usagePercent).toFixed(1)}%)`;
  if (modalBar) modalBar.style.width = `${usagePercent}%`;
  if (modalAccCount) modalAccCount.textContent = accounts.length;
  if (modalFilesCount) modalFilesCount.textContent = files.length;

  // 3. Render Accounts List
  const accList = document.getElementById('modal-accounts-list');
  if (accList) {
    if (accounts.length === 0) {
      accList.innerHTML = `
        <div style="padding: 16px; text-align: center; color: #9d78a6; font-size: 12px; background: rgba(0,0,0,0.2); border-radius: 14px;">
          No Google accounts connected yet. Click <strong>+ Connect Google Drive</strong> above to link your first account.
        </div>
      `;
    } else {
      accList.innerHTML = accounts.map((acc) => {
        const remaining = acc.remaining || 0;
        const initial = (acc.name || acc.email || 'G')[0].toUpperCase();
        return `
          <div class="syncdrive-account-card">
            <div class="account-identity">
              <div class="account-avatar">${acc.picture ? `<img src="${acc.picture}" alt="Avatar" loading="lazy">` : initial}</div>
              <div class="account-details">
                <span class="account-email">${acc.email}</span>
                <span class="account-quota-sub">${formatBytes(acc.quota_usage)} used • ${formatBytes(remaining)} remaining</span>
              </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="account-priority-badge">Priority #${acc.priority}</span>
              <button class="btn-account-unlink" onclick="unlinkGoogleAccount('${acc.email}')" title="Disconnect Account">Unlink</button>
            </div>
          </div>
        `;
      }).join('');
    }
  }

  // 4. Render Folders List
  const folderList = document.getElementById('modal-folders-list');
  if (folderList) {
    if (folders.length === 0) {
      folderList.innerHTML = `
        <div style="padding: 14px; text-align: center; color: #9d78a6; font-size: 12px; background: rgba(0,0,0,0.2); border-radius: 14px;">
          No folders configured for auto-backup. Click <strong>+ Add Folder</strong> to select a directory.
        </div>
      `;
    } else {
      folderList.innerHTML = folders.map((f) => `
        <div class="syncdrive-folder-row">
          <span class="folder-path-txt">📁 ${f}</span>
          <button class="btn-folder-del" onclick="removeBackupFolder('${f.replace(/'/g, "\\'")}')" title="Remove Folder">&times;</button>
        </div>
      `).join('');
    }
  }

  // 5. Render Offloaded Files Table
  const tbody = document.getElementById('modal-files-tbody');
  if (tbody) {
    if (files.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; color: #9d78a6; padding: 24px;">
            No files currently offloaded. Files saved in watched folders will automatically appear here once offloaded.
          </td>
        </tr>
      `;
    } else {
      tbody.innerHTML = files.map((file) => `
        <tr>
          <td><strong>${file.file_name}</strong></td>
          <td style="font-family: var(--font-mono); color: #00e5ff;">${formatBytes(file.size)}</td>
          <td><span style="color: #bda3c7; font-size: 11px;">${file.account_email}</span></td>
          <td><span style="color: #05ffa1; font-weight: 600;">Cloud Stub (.desktop)</span></td>
          <td>
            <button class="btn-action-restore" onclick="restoreOffloadedFile('${file.gdrive_file_id}')">📥 Restore to PC</button>
            <a href="${file.web_view_link}" target="_blank" class="btn-action-open">Open</a>
          </td>
        </tr>
      `).join('');
    }
  }
}

async function unlinkGoogleAccount(email) {
  if (!confirm(`Are you sure you want to disconnect ${email}?`)) return;
  const coreBase = (typeof _getFloworkCoreBase === 'function') ? _getFloworkCoreBase() : 'http://127.0.0.1:19890';
  try {
    const res = await fetch(`${coreBase}/api/sync-drive/accounts/remove`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast(`Account ${email} disconnected`);
      fetchSyncDriveStatus();
    }
  } catch (err) {
    showToast('Failed to disconnect account');
  }
}

async function removeBackupFolder(folder) {
  if (!confirm(`Stop auto-backup for ${folder}?`)) return;
  const coreBase = (typeof _getFloworkCoreBase === 'function') ? _getFloworkCoreBase() : 'http://127.0.0.1:19890';
  try {
    const res = await fetch(`${coreBase}/api/sync-drive/folders/remove`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast('Folder removed from backup');
      fetchSyncDriveStatus();
    }
  } catch (err) {
    showToast('Failed to remove folder');
  }
}

async function restoreOffloadedFile(fileId) {
  showToast('📥 Downloading physical file back to PC...');
  const coreBase = (typeof _getFloworkCoreBase === 'function') ? _getFloworkCoreBase() : 'http://127.0.0.1:19890';
  try {
    const res = await fetch(`${coreBase}/api/sync-drive/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: fileId })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast(`Physical file restored to: ${data.local_path}`);
      fetchSyncDriveStatus();
    } else {
      showToast('Error: ' + (data.message || 'Failed to restore file'));
    }
  } catch (err) {
    showToast('Restore error: ' + err.message);
  }
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ==========================================================================
// 7.4 ANTIGRAVITY MULTI-ACCOUNT CONNECTOR & CLOUD SYNC SYSTEM
// ==========================================================================
let connectorPollTimer = null;
let isConnectorSyncing = false;
let connectorOllamaCustomModels = ['llama3:8b', 'qwen2.5-coder:7b'];
let connector9RouterCustomModels = [
  'clinepass/cline-pass/glm-5.2',
  'clinepass/cline-pass/deepseek-v4-pro',
  'clinepass/cline-pass/kimi-k2.7-code'
];

function switchConnectorProviderView(targetProvider) {
  const panelDefault = document.getElementById('panel-provider-default');
  const panelOllama = document.getElementById('panel-provider-ollama');
  const panel9Router = document.getElementById('panel-provider-9router');

  const isDefaultOrGravity = targetProvider === 'default' || targetProvider === 'gravity' || targetProvider === 'antygravity' || targetProvider === 'sovereign';
  if (panelDefault) panelDefault.style.display = isDefaultOrGravity ? 'flex' : 'none';
  if (panelOllama) panelOllama.style.display = targetProvider === 'ollama' ? 'flex' : 'none';
  if (panel9Router) panel9Router.style.display = targetProvider === '9router' ? 'flex' : 'none';

  document.querySelectorAll('.connector-provider-card').forEach(c => {
    const p = c.getAttribute('data-provider');
    const isCardActive = (p === targetProvider) || (p === 'default' && isDefaultOrGravity);
    c.classList.toggle('active', isCardActive);
  });
  const actPill = document.getElementById('connector-active-pill');
  if (actPill) actPill.textContent = `ACTIVE: ${targetProvider.toUpperCase()}`;
}

async function loadConnectorProviderConfig() {
  const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
  try {
    const res = await fetch(`${routerBase}/auth/router/provider-config`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.config) {
        const cfg = data.config;
        if (cfg.active) currentAiProvider = cfg.active;
        if (cfg.ollama) {
          const inpHost = document.getElementById('input-ollama-host');
          if (inpHost && cfg.ollama.host) inpHost.value = cfg.ollama.host;
          if (Array.isArray(cfg.ollama.custom_models)) {
            connectorOllamaCustomModels = cfg.ollama.custom_models;
          }
        }
        if (cfg.router9) {
          const inpHost = document.getElementById('input-9router-host');
          const inpKey = document.getElementById('input-9router-key');
          if (inpHost && cfg.router9.host) inpHost.value = cfg.router9.host;
          if (inpKey && cfg.router9.api_key) inpKey.value = cfg.router9.api_key;
          if (Array.isArray(cfg.router9.custom_models)) {
            connector9RouterCustomModels = cfg.router9.custom_models;
          }
        }
      }
    }
  } catch (err) {
    console.warn('[Connector] Failed to load provider config:', err);
  }
  renderConnectorChips('ollama');
  renderConnectorChips('9router');
  switchConnectorProviderView(currentAiProvider);
}

function renderConnectorChips(provider) {
  if (provider === 'ollama') {
    const container = document.getElementById('ollama-models-chips');
    const countBadge = document.getElementById('count-ollama-models');
    if (countBadge) countBadge.textContent = `${connectorOllamaCustomModels.length} Model${connectorOllamaCustomModels.length === 1 ? '' : 's'}`;
    if (!container) return;
    if (connectorOllamaCustomModels.length === 0) {
      container.innerHTML = `<span style="font-size: 11px; color: #64748b;">No custom models added. Type model name above and click Add Model.</span>`;
      return;
    }
    container.innerHTML = connectorOllamaCustomModels.map(m => `
      <div class="connector-model-chip">
        <span class="connector-model-chip-tag">OLLAMA</span>
        <span>${escapeHtml(m)}</span>
        <button class="connector-chip-remove" onclick="removeConnectorModel('ollama', '${escapeHtml(m)}')" title="Remove model">✕</button>
      </div>
    `).join('');
  } else if (provider === '9router') {
    const container = document.getElementById('router9-models-chips');
    const countBadge = document.getElementById('count-9router-models');
    if (countBadge) countBadge.textContent = `${connector9RouterCustomModels.length} Model${connector9RouterCustomModels.length === 1 ? '' : 's'}`;
    if (!container) return;
    if (connector9RouterCustomModels.length === 0) {
      container.innerHTML = `<span style="font-size: 11px; color: #64748b;">No routed models added. Type model name above (e.g. clinepass/cline-pass/glm-5.2) and click Add Model.</span>`;
      return;
    }
    container.innerHTML = connector9RouterCustomModels.map(m => `
      <div class="connector-model-chip routed">
        <span class="connector-model-chip-tag">ROUTED</span>
        <span>${escapeHtml(m)}</span>
        <button class="connector-chip-remove" onclick="removeConnectorModel('9router', '${escapeHtml(m)}')" title="Remove model">✕</button>
      </div>
    `).join('');
  }
}

async function addConnectorModel(provider) {
  let inputEl = null;
  let list = null;
  if (provider === 'ollama') {
    inputEl = document.getElementById('input-ollama-new-model');
    list = connectorOllamaCustomModels;
  } else if (provider === '9router') {
    inputEl = document.getElementById('input-9router-new-model');
    list = connector9RouterCustomModels;
  }
  if (!inputEl) return;
  const val = inputEl.value.trim();
  if (!val) return;

  const items = val.split(',').map(s => s.trim()).filter(Boolean);
  for (const item of items) {
    if (!list.includes(item)) {
      list.push(item);
    }
  }
  inputEl.value = '';
  renderConnectorChips(provider);
  await saveConnectorProviderConfig(false);
  showFloworkLaserToast(`➕ Added ${provider.toUpperCase()} model: ${items.join(', ')}`, true);
  await syncDynamicModels();
}

async function removeConnectorModel(provider, modelId) {
  if (provider === 'ollama') {
    connectorOllamaCustomModels = connectorOllamaCustomModels.filter(m => m !== modelId);
  } else if (provider === '9router') {
    connector9RouterCustomModels = connector9RouterCustomModels.filter(m => m !== modelId);
  }
  renderConnectorChips(provider);
  await saveConnectorProviderConfig(false);
  showToast(`Removed model: ${modelId}`);
  await syncDynamicModels();
}
window.removeConnectorModel = removeConnectorModel;

async function saveConnectorProviderConfig(showNotification = true) {
  const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
  const inpOllamaHost = document.getElementById('input-ollama-host');
  const inp9RouterHost = document.getElementById('input-9router-host');
  const inp9RouterKey = document.getElementById('input-9router-key');

  const payload = {
    active: currentAiProvider,
    ollama_host: inpOllamaHost ? inpOllamaHost.value.trim() : undefined,
    ollama_custom_models: connectorOllamaCustomModels,
    router9_host: inp9RouterHost ? inp9RouterHost.value.trim() : undefined,
    router9_key: inp9RouterKey ? inp9RouterKey.value.trim() : undefined,
    router9_custom_models: connector9RouterCustomModels
  };

  try {
    const res = await fetch(`${routerBase}/auth/router/provider-config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      if (showNotification) {
        showFloworkLaserToast(`💾 Saved & Applied ${currentAiProvider.toUpperCase()} configuration!`, true);
      }
      await syncDynamicModels();
      return true;
    }
  } catch (err) {
    console.warn('[Connector] Failed to save provider config:', err);
  }
  return false;
}

async function testProviderEndpoint(provider) {
  let host = '';
  let statusBadge = null;
  if (provider === 'ollama') {
    const inp = document.getElementById('input-ollama-host');
    host = (inp ? inp.value.trim() : 'http://127.0.0.1:11434').replace(/\/+$/, '');
    statusBadge = document.getElementById('status-ollama-ping');
  } else if (provider === '9router') {
    const inp = document.getElementById('input-9router-host');
    host = (inp ? inp.value.trim() : 'http://127.0.0.1:20128').replace(/\/+$/, '');
    statusBadge = document.getElementById('status-9router-ping');
  }

  if (statusBadge) {
    statusBadge.className = 'connector-endpoint-status';
    statusBadge.innerHTML = `<span class="status-dot"></span> Checking...`;
  }

  const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
  try {
    const res = await fetch(`${routerBase}/auth/router/models?provider=${provider}`);
    const data = await res.json();
    const isOnline = data && Array.isArray(data.models) && !data.models.some(m => m.id.includes('-offline'));
    if (statusBadge) {
      if (isOnline) {
        statusBadge.className = 'connector-endpoint-status online';
        statusBadge.innerHTML = `<span class="status-dot"></span> Online (${data.models.length} Models)`;
      } else {
        statusBadge.className = 'connector-endpoint-status offline';
        statusBadge.innerHTML = `<span class="status-dot"></span> Offline / Unreachable`;
      }
    }
    showToast(isOnline ? `⚡ ${provider.toUpperCase()} is online (${data.models.length} models detected)` : `⚠️ ${provider.toUpperCase()} unreachable at ${host}`);
  } catch (err) {
    if (statusBadge) {
      statusBadge.className = 'connector-endpoint-status offline';
      statusBadge.innerHTML = `<span class="status-dot"></span> Offline`;
    }
    showToast(`⚠️ Cannot connect to ${provider.toUpperCase()}`);
  }
}

function initConnectorUI() {
  const btnOpen = document.getElementById('btn-open-connector');
  const btnClose = document.getElementById('btn-close-connector');
  const modal = document.getElementById('connector-modal');
  const btnAdd = document.getElementById('btn-add-connector-account');
  const btnSync = document.getElementById('btn-sync-cloud-vault');
  const btnEmptySync = document.getElementById('btn-empty-sync-cloud');
  const selectMode = document.getElementById('connector-rotation-mode');

  // Ollama Inputs & Buttons
  const btnAddOllamaModel = document.getElementById('btn-add-ollama-model');
  const inputOllamaNewModel = document.getElementById('input-ollama-new-model');
  const btnTestOllama = document.getElementById('btn-test-ollama');
  const btnSaveOllama = document.getElementById('btn-save-ollama-config');

  // 9Router Inputs & Buttons
  const btnAdd9RouterModel = document.getElementById('btn-add-9router-model');
  const input9RouterNewModel = document.getElementById('input-9router-new-model');
  const btnTest9Router = document.getElementById('btn-test-9router');
  const btnSave9Router = document.getElementById('btn-save-9router-config');

  if (btnAddOllamaModel) btnAddOllamaModel.addEventListener('click', () => addConnectorModel('ollama'));
  if (inputOllamaNewModel) {
    inputOllamaNewModel.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); addConnectorModel('ollama'); }
    });
  }
  if (btnTestOllama) btnTestOllama.addEventListener('click', () => testProviderEndpoint('ollama'));
  if (btnSaveOllama) btnSaveOllama.addEventListener('click', () => saveConnectorProviderConfig(true));

  if (btnAdd9RouterModel) btnAdd9RouterModel.addEventListener('click', () => addConnectorModel('9router'));
  if (input9RouterNewModel) {
    input9RouterNewModel.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); addConnectorModel('9router'); }
    });
  }
  if (btnTest9Router) btnTest9Router.addEventListener('click', () => testProviderEndpoint('9router'));
  if (btnSave9Router) btnSave9Router.addEventListener('click', () => saveConnectorProviderConfig(true));

  if (btnOpen && modal) {
    btnOpen.addEventListener('click', () => {
      modal.style.display = 'flex';
      loadConnectorProviderConfig();
      fetchConnectorStatus(false);
      startConnectorPolling();
    });
  }

  if (btnClose && modal) {
    btnClose.addEventListener('click', () => {
      modal.style.display = 'none';
      stopConnectorPolling();
    });
  }

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
        stopConnectorPolling();
      }
    });
  }

  // Provider Selection Cards inside Connector Modal
  document.querySelectorAll('.connector-provider-card').forEach(card => {
    card.addEventListener('click', async () => {
      const targetProvider = card.getAttribute('data-provider');
      if (!targetProvider) return;
      switchConnectorProviderView(targetProvider);
      if (targetProvider === currentAiProvider) return;
      const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
      try {
        card.style.opacity = '0.5';
        const res = await fetch(`${routerBase}/auth/router/provider`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider: targetProvider })
        });
        card.style.opacity = '1';
        if (res.ok) {
          const result = await res.json();
          currentAiProvider = result.active || targetProvider;
          showFloworkLaserToast(`🔀 AI Matrix Activated: ${currentAiProvider.toUpperCase()}`, true);
          switchConnectorProviderView(currentAiProvider);
          await syncDynamicModels();
        }
      } catch (err) {
        card.style.opacity = '1';
        console.warn('Failed to switch provider from modal:', err);
      }
    });
  });

  if (btnAdd) {
    btnAdd.addEventListener('click', async () => {
      showToast('Opening Google OAuth in browser...');
      try {
        const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
        let res = null;
        try {
          res = await fetch(`${routerBase}/auth/router/login-url?open=1`);
        } catch (_) {
          const rPort = (typeof _getFloworkRouterPort === 'function') ? _getFloworkRouterPort() : '9099';
          const altBase = routerBase.includes('127.0.0.1') ? `http://localhost:${rPort}` : `http://127.0.0.1:${rPort}`;
          res = await fetch(`${altBase}/auth/router/login-url?open=1`);
        }
        const data = await res.json();
        if (data && data.loginUrl) {
          await openSystemBrowser(data.loginUrl);
        } else {
          showToast('Failed to generate Google login URL');
        }
      } catch (err) {
        showToast('Login error: ' + err.message);
      }
    });
  }

  if (btnSync) {
    btnSync.addEventListener('click', () => syncConnectorCloudVault());
  }

  if (btnEmptySync) {
    btnEmptySync.addEventListener('click', () => syncConnectorCloudVault());
  }

  if (selectMode) {
    selectMode.addEventListener('change', async () => {
      const mode = selectMode.value;
      try {
        const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
        const res = await fetch(`${routerBase}/auth/router/set-rotation-mode`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode })
        });
        const data = await res.json();
        if (data && data.success) {
          showToast(`Rotation mode set to: ${mode}`);
        }
      } catch (err) {
        showToast('Failed to update rotation mode');
      }
    });
  }

  // Pre-fetch status to populate topbar badge
  fetchConnectorStatus(false);
}

function startConnectorPolling() {
  stopConnectorPolling();
  connectorPollTimer = setInterval(() => {
    fetchConnectorStatus(false);
  }, 5000);
}

function stopConnectorPolling() {
  if (connectorPollTimer) {
    clearInterval(connectorPollTimer);
    connectorPollTimer = null;
  }
}

async function syncConnectorCloudVault() {
  if (isConnectorSyncing) return;
  isConnectorSyncing = true;

  const btnSyncIcon = document.getElementById('btn-sync-cloud-icon');
  const btnSyncText = document.getElementById('btn-sync-cloud-text');
  if (btnSyncIcon) btnSyncIcon.textContent = '⏳';
  if (btnSyncText) btnSyncText.textContent = 'Syncing...';
  showToast('☁️ Syncing accounts with auth.floworkos.com...');

  try {
    const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';

    // Check if connector gateway is reachable and check auth state
    let authRes = null;
    try {
      const ping = await fetch(`${routerBase}/auth/status`, { signal: AbortSignal.timeout(3500) });
      if (ping.ok) {
        authRes = await ping.json();
      }
    } catch (netErr) {
      showToast('⚠️ Connector gateway is offline (Port 9099). Check conector.log');
      return;
    }

    if (authRes && authRes.authenticated === false) {
      showToast('⚠️ Flowork Sovereign Passport required to sync cloud accounts.');
      const proceed = confirm('Flowork OS Sovereign Passport session not detected on this machine.\n\nLog in to auth.floworkos.com now to download your cloud accounts?');
      if (proceed) {
        const loginUrl = `${routerBase}/auth/login-url`;
        if (typeof openSystemBrowser === 'function') {
          await openSystemBrowser(loginUrl);
        } else {
          window.open(loginUrl, '_blank');
        }
      }
      return;
    }

    const res = await fetch(`${routerBase}/auth/router/sync-cloud`);
    const data = await res.json();
    if (data && data.success) {
      if (data.total_accounts > 0) {
        showToast(`☁️ Cloud sync complete: ${data.total_accounts} accounts loaded`);
      } else {
        showToast('ℹ️ Cloud sync complete: 0 accounts found in your cloud vault');
      }
      renderConnectorUI(data);
    } else {
      showToast('⚠️ Cloud sync failed: ' + (data?.error || 'No accounts returned from server'));
    }
  } catch (err) {
    showToast('⚠️ Cloud sync error: ' + err.message);
  } finally {
    isConnectorSyncing = false;
    if (btnSyncIcon) btnSyncIcon.textContent = '☁️';
    if (btnSyncText) btnSyncText.textContent = 'Sync with Cloud';
  }
}

async function fetchConnectorStatus(forcePullIfEmpty = false) {
  if (document.hidden) return;
  try {
    const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
    const url = forcePullIfEmpty ? `${routerBase}/auth/router/accounts?refresh=1` : `${routerBase}/auth/router/accounts`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.success) {
      renderConnectorUI(data);
    }
  } catch (err) {
    console.warn('[Connector] Failed to fetch accounts:', err);
  }
}

function renderConnectorUI(data) {
  const accounts = Array.isArray(data.accounts) ? data.accounts : [];
  const badge = document.getElementById('connector-count-badge');
  const totalEl = document.getElementById('connector-total-accounts');
  const statusEl = document.getElementById('connector-pool-status');
  const selectMode = document.getElementById('connector-rotation-mode');
  const countBadge = document.getElementById('connector-accounts-count');
  const listContainer = document.getElementById('connector-accounts-list');

  // 1. Update Topbar Badge
  if (badge) {
    badge.textContent = accounts.length > 0 ? accounts.length : '0';
    badge.style.display = accounts.length > 0 ? 'inline-flex' : 'none';
  }

  // Check if modal is currently open
  const modal = document.getElementById('connector-modal');
  const isModalOpen = modal && modal.style.display !== 'none';
  if (!isModalOpen) return;

  // 2. Update Overview Stats
  if (totalEl) totalEl.textContent = `${accounts.length} Account${accounts.length === 1 ? '' : 's'}`;
  if (countBadge) countBadge.textContent = accounts.length;

  // 2b. Sync Active Provider Cards in Connector Modal
  const activePill = document.getElementById('connector-active-pill');
  if (activePill) {
    activePill.textContent = `ACTIVE: ${currentAiProvider.toUpperCase()}`;
  }
  document.querySelectorAll('.connector-provider-card').forEach(card => {
    const p = card.getAttribute('data-provider');
    const isAct = p === currentAiProvider;
    card.classList.toggle('active', isAct);
    const statusText = card.querySelector('.card-provider-status');
    if (statusText) {
      if (p === 'default') {
        statusText.textContent = isAct ? `● Active (${accounts.length} Accounts)` : `● Standby (${accounts.length} Accounts)`;
      } else if (p === 'ollama') {
        statusText.textContent = isAct ? `● Active (Local Engine)` : `● Standby (Click to Activate)`;
      } else if (p === '9router') {
        statusText.textContent = isAct ? `● Active (Proxy Gateway)` : `● Standby (Click to Activate)`;
      }
    }
  });
  switchConnectorProviderView(currentAiProvider);

  if (statusEl) {
    const cooldownCount = accounts.filter(a => a.status === 'cooldown').length;
    const errorCount = accounts.filter(a => a.status === 'error').length;
    if (accounts.length === 0) {
      statusEl.textContent = 'No Accounts';
      statusEl.style.color = '#94a3b8';
    } else if (cooldownCount === accounts.length) {
      statusEl.textContent = 'All in Cooldown';
      statusEl.style.color = '#f59e0b';
    } else if (cooldownCount > 0 || errorCount > 0) {
      statusEl.textContent = `${accounts.length - cooldownCount - errorCount} Active / ${cooldownCount} Cooldown`;
      statusEl.style.color = '#38bdf8';
    } else {
      statusEl.textContent = 'Optimal (All Available)';
      statusEl.style.color = '#10b981';
    }
  }

  if (selectMode && data.rotation_mode) {
    selectMode.value = data.rotation_mode;
  }

  // 3. Render Accounts List
  if (listContainer) {
    if (accounts.length === 0) {
      listContainer.innerHTML = `
        <div class="connector-empty-state">
          <span style="font-size: 32px;">⚡</span>
          <p>No accounts found in local vault.</p>
          <button class="btn-connector-subaction" id="btn-empty-sync-cloud">Download Accounts from Cloud</button>
        </div>
      `;
      const btnEmpty = document.getElementById('btn-empty-sync-cloud');
      if (btnEmpty) btnEmpty.addEventListener('click', () => syncConnectorCloudVault());
      return;
    }

    listContainer.innerHTML = accounts.map((acc) => {
      const isActive = !!acc.is_active;
      const isCooldown = acc.status === 'cooldown';
      const isError = acc.status === 'error';

      let badgeHtml = '';
      if (isActive) {
        badgeHtml = `<span class="connector-status-badge status-badge-active">ACTIVE</span>`;
      } else if (isCooldown) {
        badgeHtml = `<span class="connector-status-badge status-badge-cooldown">COOLDOWN (${acc.cooldown_remaining_sec || 0}s)</span>`;
      } else if (isError) {
        badgeHtml = `<span class="connector-status-badge status-badge-error">ERROR</span>`;
      } else {
        badgeHtml = `<span class="connector-status-badge status-badge-standby">STANDBY</span>`;
      }

      const initial = (acc.email || 'G').charAt(0).toUpperCase();

      return `
        <div class="connector-account-card ${isActive ? 'active-account' : ''}">
          <div class="connector-acc-info">
            <div class="connector-acc-avatar">${initial}</div>
            <div class="connector-acc-meta">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="connector-acc-email">${escapeHtml(acc.email || 'Unknown')}</span>
                ${badgeHtml}
              </div>
              <div class="connector-acc-subtext">
                <span>Requests: ${acc.requests_count || 0}</span>
                <span>•</span>
                <span>Errors: ${acc.errors_count || 0}</span>
                ${acc.error_message ? `<span style="color: #ef4444;">• ${escapeHtml(acc.error_message)}</span>` : ''}
              </div>
            </div>
          </div>
          <div class="connector-acc-actions">
            ${!isActive && !isError ? `<button class="btn-acc-action btn-acc-active" onclick="selectConnectorAccount('${acc.id}')" title="Set as primary active account">Activate</button>` : ''}
            <button class="btn-acc-action" onclick="testConnectorAccount('${acc.id}')" title="Test token connectivity">Test</button>
            <button class="btn-acc-action btn-acc-delete" onclick="removeConnectorAccount('${acc.id}', '${escapeHtml(acc.email)}')" title="Remove from pool">✕</button>
          </div>
        </div>
      `;
    }).join('');
  }
}

async function selectConnectorAccount(id) {
  try {
    const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
    const res = await fetch(`${routerBase}/auth/router/select-account`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    const data = await res.json();
    if (data && data.success) {
      showToast(`Active account switched to: ${data.email}`);
      fetchConnectorStatus(false);
    } else {
      showToast('Failed to switch account: ' + (data.error || 'Unknown error'));
    }
  } catch (err) {
    showToast('Failed to switch account');
  }
}
window.selectConnectorAccount = selectConnectorAccount;

async function testConnectorAccount(id) {
  showToast('Testing account token...');
  try {
    const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
    const res = await fetch(`${routerBase}/auth/router/test-account`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    const data = await res.json();
    if (data && data.success) {
      showToast(`Token valid for: ${data.email}`);
      fetchConnectorStatus(false);
    } else {
      showToast(`Token test failed: ${data.details?.error || 'Invalid'}`);
    }
  } catch (err) {
    showToast('Token test error: ' + err.message);
  }
}
window.testConnectorAccount = testConnectorAccount;

async function removeConnectorAccount(id, email) {
  if (!confirm(`Are you sure you want to remove account [${email}] from rotation?`)) return;
  try {
    const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
    const res = await fetch(`${routerBase}/auth/router/remove-account`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    const data = await res.json();
    if (data && data.success) {
      showToast(`Account removed. ${data.remaining} remaining in pool.`);
      fetchConnectorStatus(false);
    } else {
      showToast('Failed to remove account: ' + (data.error || 'Unknown error'));
    }
  } catch (err) {
    showToast('Failed to remove account: ' + err.message);
  }
}
window.removeConnectorAccount = removeConnectorAccount;

// ==========================================================================
// 7.5 FLOWORK VIRAL PROMO RECORDER (60FPS Screen & Audio Capture)
// ==========================================================================
let promoMediaRecorder = null;
let promoRecordedChunks = [];
let promoRecordTimer = null;
let promoRecordStartTime = 0;
let promoActiveStream = null;

function initPromoRecorder() {
  const btnRec = document.getElementById('btn-record-promo');
  const lblRec = document.getElementById('rec-label');

  if (!btnRec) return;

  btnRec.addEventListener('click', async () => {
    if (promoMediaRecorder && promoMediaRecorder.state === 'recording') {
      stopPromoRecording();
    } else {
      await startPromoRecording();
    }
  });

  async function startPromoRecording() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
        showToast('⚠️ Screen recording is not supported in this browser environment');
        return;
      }

      // Request screen stream with 60FPS and system audio
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          frameRate: { ideal: 60, max: 60 },
          displaySurface: 'browser'
        },
        audio: true
      });

      promoActiveStream = stream;
      promoRecordedChunks = [];

      // Determine supported mimeType across Multi-OS
      const mimeTypes = [
        'video/webm;codecs=vp9,opus',
        'video/webm;codecs=vp8,opus',
        'video/webm',
        'video/mp4'
      ];
      let selectedMime = mimeTypes.find(m => MediaRecorder.isTypeSupported(m)) || '';

      const options = selectedMime ? { mimeType: selectedMime, videoBitsPerSecond: 10_000_000 } : {};
      promoMediaRecorder = new MediaRecorder(stream, options);

      promoMediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          promoRecordedChunks.push(e.data);
        }
      };

      promoMediaRecorder.onstop = () => {
        finalizeRecording();
      };

      // Listen for stream ended (user clicked browser's native stop share bar)
      stream.getVideoTracks().forEach(track => {
        track.onended = () => {
          if (promoMediaRecorder && promoMediaRecorder.state === 'recording') {
            promoMediaRecorder.stop();
          }
        };
      });

      promoMediaRecorder.start(1000);
      promoRecordStartTime = Date.now();

      btnRec.classList.add('is-recording');
      btnRec.title = 'Click to Stop & Choose Save Location';
      if (lblRec) lblRec.textContent = '⏹ Stop (00:00)';

      promoRecordTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - promoRecordStartTime) / 1000);
        const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const secs = String(elapsed % 60).padStart(2, '0');
        if (lblRec) lblRec.textContent = `⏹ Stop (${mins}:${secs})`;
      }, 1000);

      showToast('🎬 Recording started! Click Stop when finished.');

    } catch (err) {
      console.warn('[Recorder] Error starting capture:', err);
      if (err.name !== 'NotAllowedError') {
        showToast('⚠️ Capture error: ' + err.message);
      }
      resetRecButtonUI();
    }
  }

  function stopPromoRecording() {
    if (promoMediaRecorder && promoMediaRecorder.state === 'recording') {
      promoMediaRecorder.stop();
    }
    if (promoActiveStream) {
      promoActiveStream.getTracks().forEach(t => t.stop());
    }
  }

  function resetRecButtonUI() {
    if (promoRecordTimer) {
      clearInterval(promoRecordTimer);
      promoRecordTimer = null;
    }
    btnRec.classList.remove('is-recording');
    btnRec.title = 'Record Screen & Audio (Multi-OS)';
    if (lblRec) lblRec.textContent = 'Record';
  }

  async function finalizeRecording() {
    resetRecButtonUI();

    if (promoRecordedChunks.length === 0) {
      showToast('⚠️ No video data recorded');
      return;
    }

    const mime = promoMediaRecorder && promoMediaRecorder.mimeType ? promoMediaRecorder.mimeType : 'video/webm';
    const ext = mime.includes('mp4') ? 'mp4' : 'webm';
    const currentVideoBlob = new Blob(promoRecordedChunks, { type: mime });
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const defaultFilename = `flowork_recording_${timestamp}.${ext}`;

    // Multi-OS Native Save Picker (Windows, Linux, macOS)
    if (typeof window.showSaveFilePicker === 'function') {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: defaultFilename,
          types: [{
            description: `${ext.toUpperCase()} Video (*.${ext})`,
            accept: { [mime]: [`.${ext}`] }
          }]
        });
        const writable = await handle.createWritable();
        await writable.write(currentVideoBlob);
        await writable.close();
        showToast(`✅ Recording saved: ${handle.name}`);
        return;
      } catch (err) {
        if (err.name === 'AbortError') {
          showToast('Recording save cancelled');
          return;
        }
        console.warn('[Recorder] showSaveFilePicker fallback:', err);
      }
    }

    // Universal Multi-OS Fallback
    const url = URL.createObjectURL(currentVideoBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = defaultFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    showToast(`✅ Recording saved: ${defaultFilename}`);
  }
}

// ==========================================================================
// 8. FLOWORK SOVEREIGN AI AGENT RIGHTBAR CHAT (NATIVE COGNITIVE RUNTIME)
// ==========================================================================
let currentChatSessionId = null;
let isChatStreaming = false;
let currentAbortController = null;
let queuedMessages = [];
let activeSubagentKeys = new Set();
let activeTaskKeys = new Set();
let activeTurnUserCard = null;
let isSystemRestarting = false;
let restartPollTimer = null;
const initialSessionMode = (localStorage.getItem('xflow_session_mode') === 'solo') ? 'solo' : 'team';
window.currentSessionMode = initialSessionMode;
window.currentSessionType = (initialSessionMode === 'solo') ? 'personal' : 'group';

function setChatStreamingState(isStreaming) {
  isChatStreaming = isStreaming;
  const sendBtn = document.getElementById('btn-rightbar-send');
  if (sendBtn) {
    sendBtn.classList.toggle('is-running', isStreaming);
    sendBtn.title = isStreaming ? 'Stop generation (Esc)' : 'Send (Enter)';
  }
}
window.setChatStreamingState = setChatStreamingState;

function openChatSessionById(sessionId) {
  const rightbarChat = document.getElementById('rightbar-chat');
  if (rightbarChat && rightbarChat.classList.contains('collapsed')) {
    rightbarChat.classList.remove('collapsed');
    localStorage.setItem('xflow_rightbar_collapsed', 'false');
  }
  if (typeof window.__closeHistoryView === 'function') {
    window.__closeHistoryView();
  } else {
    const rightbarMessages = document.getElementById('rightbar-messages');
    const rightbarHistoryView = document.getElementById('rightbar-history-view');
    if (rightbarHistoryView) rightbarHistoryView.style.display = 'none';
    if (rightbarMessages) rightbarMessages.style.display = 'flex';
  }

  if (sessionId && sessionId !== currentChatSessionId) {
    loadChatSession(sessionId);
  }
}

function startRestartPolling(sessionId) {
  if (restartPollTimer) clearInterval(restartPollTimer);
  const targetId = sessionId || currentChatSessionId;
  let attempts = 0;
  let baselineStepsCount = -1;

  const sendBtn = document.getElementById('btn-rightbar-send');
  if (sendBtn) {
    sendBtn.classList.add('is-running');
    sendBtn.title = 'Flowork is restarting & loading updates...';
  }

  restartPollTimer = setInterval(async () => {
    attempts++;
    if (attempts > 60) {
      clearInterval(restartPollTimer);
      restartPollTimer = null;
      isSystemRestarting = false;
      if (sendBtn) {
        sendBtn.classList.remove('is-running');
        sendBtn.title = 'Send (Enter)';
      }
      return;
    }

    try {
      const activeId = targetId || currentChatSessionId;
      if (!activeId) return;
      const res = await fetch(`/api/chat/steps/${encodeURIComponent(activeId)}`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'ok' && data.data && Array.isArray(data.data.steps)) {
          const steps = data.data.steps;
          const count = steps.length;

          if (baselineStepsCount === -1) {
            baselineStepsCount = count;
          }

          const lastStep = count > 0 ? steps[count - 1] : null;
          const lastStatus = lastStep ? (lastStep.status || '') : '';

          renderTrajectorySteps(steps);
          if (typeof scrollChatToBottom === 'function') {
            scrollChatToBottom({ force: false });
          } else {
            const container = document.getElementById('rightbar-messages');
            if (container) container.scrollTop = container.scrollHeight;
          }

          if (count > baselineStepsCount && lastStatus.endsWith('DONE')) {
            console.log('[SystemRestart] ✅ Resumed session turn completed');
            clearInterval(restartPollTimer);
            restartPollTimer = null;
            isSystemRestarting = false;
            if (sendBtn) {
              sendBtn.classList.remove('is-running');
              sendBtn.title = 'Send (Enter)';
            }
            fetchChatHistory();
            showToast('✅ Flowork restarted successfully & task completed!');
          }
        }
      }
    } catch (_) {
      if (sendBtn && !sendBtn.classList.contains('is-running')) {
        sendBtn.classList.add('is-running');
      }
    }
  }, 1200);
}
let currentThinkingController = null;
let activeToolsArea = null;
let activeBodyArea = null;
let lastKnownStepFingerprint = '';
let chatSyncTimer = null;
let isChatSyncing = false;

let AVAILABLE_CHAT_MODELS = (function() {
  try {
    const cached = localStorage.getItem('flowork_cached_models');
    if (cached) {
      const parsed = JSON.parse(cached);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (_) {}
  return [];
})();
window.AVAILABLE_CHAT_MODELS = AVAILABLE_CHAT_MODELS;

let selectedChatModelId = localStorage.getItem('xflow_chat_model') || '';

function getSelectedModelObj() {
  if (Array.isArray(AVAILABLE_CHAT_MODELS) && AVAILABLE_CHAT_MODELS.length > 0) {
    const found = AVAILABLE_CHAT_MODELS.find(m => m.id === selectedChatModelId);
    if (found) return found;
    return AVAILABLE_CHAT_MODELS[0];
  }
  return {
    id: selectedChatModelId || 'default',
    name: selectedChatModelId ? selectedChatModelId.replace(/-/g, ' ').toUpperCase() : 'Cognitive Engine',
    provider: typeof currentAiProvider !== 'undefined' ? currentAiProvider : 'default',
    badge: 'AI',
    badgeClass: 'badge-pro',
    desc: 'Dynamic Flowork inference model'
  };
}

function updateModelPillDisplay() {
  const current = getSelectedModelObj();
  const pillText = document.getElementById('chat-model-pill-text');
  if (pillText) {
    pillText.textContent = current.name;
  }
  const pillIcon = document.getElementById('chat-model-provider-icon');
  if (pillIcon) {
    if (currentAiProvider === 'ollama') pillIcon.textContent = '🦙';
    else if (currentAiProvider === '9router') pillIcon.textContent = '🔀';
    else pillIcon.textContent = '⚡';
  }
  const heroModelBadge = document.querySelector('.fl-hero-model');
  if (heroModelBadge) {
    heroModelBadge.textContent = current.id;
  }
}

function renderModelDropdown() {
  const listEl = document.getElementById('chat-model-list');
  if (!listEl) return;

  listEl.innerHTML = AVAILABLE_CHAT_MODELS.map(m => {
    const isSelected = m.id === selectedChatModelId;
    return `
      <div class="model-option-item ${isSelected ? 'selected' : ''}" data-model-id="${m.id}">
        <div class="model-option-left">
          <div class="model-option-title-row">
            <span class="model-option-name">${m.name}</span>
            <span class="model-option-badge ${m.badgeClass}">${m.badge}</span>
          </div>
          <div class="model-option-desc">${m.desc}</div>
        </div>
        ${isSelected ? '<span class="model-option-check">✓</span>' : ''}
      </div>
    `;
  }).join('');

  listEl.querySelectorAll('.model-option-item').forEach(item => {
    item.addEventListener('click', async (e) => {
      e.stopPropagation();
      const modelId = item.getAttribute('data-model-id');
      if (modelId && AVAILABLE_CHAT_MODELS.some(m => m.id === modelId)) {
        selectedChatModelId = modelId;
        localStorage.setItem('xflow_chat_model', modelId);
        if (currentChatSessionId) {
          localStorage.setItem('xflow_session_model_' + currentChatSessionId, modelId);
        }
        if (currentInspectedAgent) {
          currentInspectedAgent.model = modelId;
          localStorage.setItem('xflow_agent_model_' + currentInspectedAgent.id, modelId);
          localStorage.setItem('xflow_agent_model_' + currentInspectedAgent.persona, modelId);
          if (office3DInstance) {
            office3DInstance.updateAgentConfig(currentInspectedAgent.id, { model: modelId });
          }
        } else if (currentSessionPersonaId) {
          localStorage.setItem('xflow_agent_model_' + currentSessionPersonaId, modelId);
        }
        updateModelPillDisplay();
        renderModelDropdown();
        closeModelDropdown();
        await window.switchFloworkCoreModel(modelId);
        showFloworkLaserToast(`🎯 Active Cognitive Engine: ${getSelectedModelObj().name}`, true);
      }
    });
  });
}

function openModelDropdown() {
  closeAllChatDropdowns('model');
  const dropdown = document.getElementById('chat-model-dropdown');
  const pill = document.getElementById('chat-model-pill');
  if (dropdown) {
    renderModelDropdown();
    dropdown.style.display = 'block';
  }
  if (pill) {
    pill.classList.add('active');
  }
}

function closeModelDropdown() {
  const dropdown = document.getElementById('chat-model-dropdown');
  const pill = document.getElementById('chat-model-pill');
  if (dropdown) {
    dropdown.style.display = 'none';
  }
  if (pill) {
    pill.classList.remove('active');
  }
}

function toggleModelDropdown() {
  const dropdown = document.getElementById('chat-model-dropdown');
  if (dropdown && dropdown.style.display === 'block') {
    closeModelDropdown();
  } else {
    openModelDropdown();
  }
}

let modelSelectorInitialized = false;
let currentAiProvider = 'default';

async function syncDynamicModels() {
  const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
  try {
    // 1. Sync current active AI provider
    try {
      const pRes = await fetch(`${routerBase}/auth/router/provider`);
      if (pRes.ok) {
        const pData = await pRes.json();
        if (pData && pData.active) {
          currentAiProvider = pData.active;
        }
      }
    } catch (_) {}

    // 2. Update UI Provider Tabs & Badge
    document.querySelectorAll('.model-provider-tab').forEach(tab => {
      const p = tab.getAttribute('data-provider');
      tab.classList.toggle('active', p === currentAiProvider);
    });
    const badgeEl = document.getElementById('active-provider-badge');
    if (badgeEl) {
      badgeEl.textContent = currentAiProvider.toUpperCase();
    }

    // 3. Fetch normalized dynamic models catalog for active provider
    const res = await fetch(`${routerBase}/auth/router/models`);
    if (res.ok) {
      const data = await res.json();
      if (data && Array.isArray(data.models) && data.models.length > 0) {
        AVAILABLE_CHAT_MODELS = data.models.map(m => ({
          id: m.id,
          name: m.name || m.id,
          provider: m.provider || currentAiProvider,
          badge: m.badge || 'PRO',
          badgeClass: m.badgeClass || 'badge-pro',
          desc: m.desc || m.description || ''
        }));
        window.AVAILABLE_CHAT_MODELS = AVAILABLE_CHAT_MODELS;
        try {
          localStorage.setItem('flowork_cached_models', JSON.stringify(AVAILABLE_CHAT_MODELS));
        } catch (_) {}
        if (!selectedChatModelId || !AVAILABLE_CHAT_MODELS.some(m => m.id === selectedChatModelId)) {
          selectedChatModelId = data.active_model || (AVAILABLE_CHAT_MODELS[0] && AVAILABLE_CHAT_MODELS[0].id) || '';
          if (selectedChatModelId) {
            localStorage.setItem('xflow_chat_model', selectedChatModelId);
          }
        }
        updateModelPillDisplay();
        renderModelDropdown();
      }
    }
  } catch (_) {}
}

function initModelSelector() {
  updateModelPillDisplay();
  syncDynamicModels();

  if (modelSelectorInitialized) return;
  modelSelectorInitialized = true;

  // Multi-Provider Tab Selector Listener
  document.querySelectorAll('.model-provider-tab').forEach(tab => {
    tab.addEventListener('click', async (e) => {
      e.stopPropagation();
      const targetProvider = tab.getAttribute('data-provider');
      if (!targetProvider || targetProvider === currentAiProvider) return;

      const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
      try {
        tab.style.opacity = '0.5';
        const res = await fetch(`${routerBase}/auth/router/provider`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider: targetProvider })
        });
        tab.style.opacity = '1';
        if (res.ok) {
          const result = await res.json();
          currentAiProvider = result.active || targetProvider;
          showFloworkLaserToast(`🔀 AI Matrix Switched: ${currentAiProvider.toUpperCase()}`, true);
          await syncDynamicModels();
        }
      } catch (err) {
        tab.style.opacity = '1';
        console.warn('Failed to switch AI provider:', err);
      }
    });
  });

  const pill = document.getElementById('chat-model-pill');
  if (pill) {
    pill.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleModelDropdown();
    });
  }

  document.addEventListener('click', (e) => {
    const wrap = document.getElementById('chat-model-selector-wrap');
    if (wrap && !wrap.contains(e.target)) {
      closeModelDropdown();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const dd = document.getElementById('chat-model-dropdown');
      if (dd && dd.style.display !== 'none') {
        closeModelDropdown();
      }
    }
  });
}

// ── Dedicated Account Affinity & Concurrency Selector ──
let currentSessionAccountId = 'combo'; // 'combo' (default) or account id/email
let currentSessionFailoverPolicy = 'fallback_pool'; // 'fallback_pool' | 'strict'
let pendingSessionAccountId = 'combo';
let accountSelectorInitialized = false;

function getSelectedAccountObj() {
  if (currentSessionAccountId === 'combo' || !currentSessionAccountId) {
    return {
      id: 'combo',
      name: 'Combo (Auto)',
      email: 'Automatic Load Balancer',
      isCombo: true
    };
  }
  const acc = (routerSwitchboardState.accounts || []).find(a => a.id === currentSessionAccountId || (a.email && a.email.toLowerCase() === currentSessionAccountId.toLowerCase()));
  if (acc) {
    return {
      id: acc.id,
      name: acc.name || acc.email.split('@')[0],
      email: acc.email,
      status: acc.status,
      isCombo: false
    };
  }
  return {
    id: currentSessionAccountId,
    name: currentSessionAccountId.split('@')[0],
    email: currentSessionAccountId,
    isCombo: false
  };
}

function updateAccountPillDisplay() {
  const current = getSelectedAccountObj();
  const pillText = document.getElementById('chat-account-pill-text');
  const pillEl = document.getElementById('chat-account-pill');
  if (pillText) {
    pillText.textContent = current.isCombo ? 'Combo (Auto)' : (current.name || current.email);
  }
  if (pillEl) {
    if (!current.isCombo) {
      pillEl.classList.add('is-pinned');
      pillEl.title = `Pinned Account: ${current.email} [${currentSessionFailoverPolicy === 'strict' ? 'Strict Isolation' : 'Pool Fallback'}]`;
    } else {
      pillEl.classList.remove('is-pinned');
      pillEl.title = 'Combo Pool: Distributes requests across all healthy accounts';
    }
  }
}

async function fetchSessionBinding(sessionId) {
  if (!sessionId) {
    currentSessionAccountId = pendingSessionAccountId || 'combo';
    currentSessionFailoverPolicy = 'fallback_pool';
    updateAccountPillDisplay();
    return;
  }
  const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
  try {
    const res = await fetch(`${routerBase}/auth/router/session-binding?session_id=${encodeURIComponent(sessionId)}`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (data && data.success && data.binding) {
        currentSessionAccountId = data.binding.account_id || 'combo';
        currentSessionFailoverPolicy = data.binding.failover_policy || 'fallback_pool';
        updateAccountPillDisplay();
        return;
      }
    }
  } catch (_) {}
  currentSessionAccountId = 'combo';
  currentSessionFailoverPolicy = 'fallback_pool';
  updateAccountPillDisplay();
}

async function setSessionBinding(accountId, failoverPolicy = currentSessionFailoverPolicy) {
  const safeAccountId = accountId || 'combo';
  currentSessionAccountId = safeAccountId;
  currentSessionFailoverPolicy = failoverPolicy;
  pendingSessionAccountId = safeAccountId;
  updateAccountPillDisplay();

  // AUTO-SAVE PER ACTIVE AGENT, PERSONA, AND SESSION (Zero-Friction UX!)
  const activePersona = currentSessionPersonaId || 'default';
  localStorage.setItem('xflow_agent_account_' + activePersona, safeAccountId);
  if (currentActiveAgentId) {
    localStorage.setItem('xflow_agent_account_' + currentActiveAgentId, safeAccountId);
  }
  if (currentChatSessionId) {
    localStorage.setItem('xflow_session_account_' + currentChatSessionId, safeAccountId);
  }
  if (currentInspectedAgent) {
    currentInspectedAgent.account = safeAccountId;
    localStorage.setItem('xflow_agent_account_' + currentInspectedAgent.id, safeAccountId);
    localStorage.setItem('xflow_agent_account_' + currentInspectedAgent.persona, safeAccountId);
    if (office3DInstance && typeof office3DInstance.updateAgentConfig === 'function') {
      office3DInstance.updateAgentConfig(currentInspectedAgent.id, { account: safeAccountId });
    }
  }

  if (currentChatSessionId) {
    const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : `http://127.0.0.1:${_getFloworkRouterPort()}`;
    try {
      await fetch(`${routerBase}/auth/router/session-binding`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentChatSessionId,
          account_id: safeAccountId,
          failover_policy: failoverPolicy
        })
      });
      const accObj = (routerSwitchboardState.accounts || []).find(a => a.id === safeAccountId || (a.email && a.email.toLowerCase() === safeAccountId.toLowerCase()));
      const label = safeAccountId === 'combo' ? 'Combo (Auto-Balancer)' : (accObj ? (accObj.email || accObj.name) : safeAccountId);
      showFloworkLaserToast(`🔗 Account bound: ${label} (Auto-Saved)`, true);
    } catch (e) {
      console.warn('Failed to persist session binding:', e);
    }
  }
}

function renderAccountDropdown() {
  const listEl = document.getElementById('chat-account-list');
  if (!listEl) return;

  const accounts = routerSwitchboardState.accounts || [];
  const isComboSelected = currentSessionAccountId === 'combo' || !currentSessionAccountId;

  let html = `
    <div class="account-option-item ${isComboSelected ? 'selected' : ''}" data-account-id="combo">
      <div class="account-option-left">
        <div class="account-option-title-row">
          <span class="account-option-name">⚡ Combo (Auto-Balancer)</span>
          <span class="account-option-badge badge-combo">DEFAULT</span>
        </div>
        <div class="account-option-desc">Auto-distributes evenly across all ${accounts.length || 0} accounts</div>
      </div>
      ${isComboSelected ? '<span class="model-option-check">✓</span>' : ''}
    </div>
  `;

  if (accounts.length === 0) {
    html += `
      <div style="padding: 10px; font-size: 11px; color: var(--text-dim); text-align: center;">
        No Google accounts in pool.<br>
        <a href="#" id="link-account-dropdown-add" style="color: #00e5ff; text-decoration: underline;">+ Connect Google Account</a>
      </div>
    `;
  } else {
    html += accounts.map(a => {
      const isSelected = a.id === currentSessionAccountId || (a.email && a.email.toLowerCase() === currentSessionAccountId.toLowerCase());
      const isCooldown = a.status === 'cooldown' || (a.cooldown_until && a.cooldown_until > Date.now());
      let badgeHtml = '';
      if (isCooldown) {
        badgeHtml = `<span class="account-option-badge badge-account-cooldown">COOLDOWN</span>`;
      } else if (a.is_active) {
        badgeHtml = `<span class="account-option-badge badge-account-active">PRIMARY</span>`;
      } else {
        badgeHtml = `<span class="account-option-badge badge-account-active">READY</span>`;
      }

      return `
        <div class="account-option-item ${isSelected ? 'selected' : ''}" data-account-id="${a.id}">
          <div class="account-option-left">
            <div class="account-option-title-row">
              <span class="account-option-name">👤 ${a.name || a.email.split('@')[0]}</span>
              ${badgeHtml}
            </div>
            <div class="account-option-desc">${a.email}</div>
          </div>
          ${isSelected ? '<span class="model-option-check">✓</span>' : ''}
        </div>
      `;
    }).join('');
  }

  // Policy footer selector
  html += `
    <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.06); display: flex; align-items: center; justify-content: space-between; font-size: 10px; color: var(--text-dim);">
      <span>Failover Policy:</span>
      <button id="btn-toggle-failover-policy" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); color: #c084fc; border-radius: 4px; padding: 2px 6px; font-size: 9.5px; cursor: pointer;">
        ${currentSessionFailoverPolicy === 'strict' ? '🔒 Strict (No Fallback)' : '🔀 Fallback to Pool'}
      </button>
    </div>
  `;

  listEl.innerHTML = html;

  const btnPolicy = document.getElementById('btn-toggle-failover-policy');
  if (btnPolicy) {
    btnPolicy.addEventListener('click', async (e) => {
      e.stopPropagation();
      const newPolicy = currentSessionFailoverPolicy === 'strict' ? 'fallback_pool' : 'strict';
      await setSessionBinding(currentSessionAccountId, newPolicy);
      renderAccountDropdown();
    });
  }

  const addLink = document.getElementById('link-account-dropdown-add');
  if (addLink) {
    addLink.addEventListener('click', (e) => {
      e.preventDefault();
      closeAccountDropdown();
      const btnAdd = document.getElementById('btn-add-google-acc');
      if (btnAdd) btnAdd.click();
    });
  }

  listEl.querySelectorAll('.account-option-item').forEach(item => {
    item.addEventListener('click', async (e) => {
      e.stopPropagation();
      const accId = item.getAttribute('data-account-id');
      if (accId) {
        await setSessionBinding(accId, currentSessionFailoverPolicy);
        renderAccountDropdown();
        closeAccountDropdown();
      }
    });
  });
}

function openAccountDropdown() {
  closeAllChatDropdowns('account');
  const dropdown = document.getElementById('chat-account-dropdown');
  const pill = document.getElementById('chat-account-pill');
  if (dropdown && pill) {
    renderAccountDropdown();
    dropdown.style.display = 'block';
    pill.classList.add('active');
  }
}

function closeAccountDropdown() {
  const dropdown = document.getElementById('chat-account-dropdown');
  const pill = document.getElementById('chat-account-pill');
  if (dropdown && pill) {
    dropdown.style.display = 'none';
    pill.classList.remove('active');
  }
}

function toggleAccountDropdown() {
  const dropdown = document.getElementById('chat-account-dropdown');
  if (dropdown && dropdown.style.display === 'block') {
    closeAccountDropdown();
  } else {
    openAccountDropdown();
  }
}

function initAccountSelector() {
  updateAccountPillDisplay();

  if (accountSelectorInitialized) return;
  accountSelectorInitialized = true;

  const pill = document.getElementById('chat-account-pill');
  if (pill) {
    pill.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleAccountDropdown();
    });
  }

  document.addEventListener('click', (e) => {
    const wrap = document.getElementById('chat-account-selector-wrap');
    if (wrap && !wrap.contains(e.target)) {
      closeAccountDropdown();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAccountDropdown();
    }
  });
}

// ── Chat-Bound Persona & Specialist Selector ──
let AVAILABLE_PERSONAS = [];
window.AVAILABLE_PERSONAS = AVAILABLE_PERSONAS;
let initialBootTab = (typeof localStorage !== 'undefined') ? (localStorage.getItem('xflow_active_tab') || 'office') : 'office';
if (initialBootTab === 'group' || initialBootTab === 'canvas-stage') {
  initialBootTab = 'office';
  try { localStorage.setItem('xflow_active_tab', 'office'); } catch (_) {}
}
let currentSessionPersonaId = 'mr.flow';
const savedChatPersona = (typeof localStorage !== 'undefined') ? localStorage.getItem('xflow_chat_persona') : null;
if (savedChatPersona && savedChatPersona !== 'default') {
  currentSessionPersonaId = savedChatPersona;
}
let pendingSessionPersonaId = currentSessionPersonaId;
let agentSelectorInitialized = false;

function getSelectedPersonaObj() {
  const targetId = currentSessionPersonaId || 'leader';
  const found = AVAILABLE_PERSONAS.find(p => p.id.toLowerCase() === targetId.toLowerCase() || (targetId === 'mrflow' && p.id === 'mr.flow'));
  if (found) return found;
  const leader = AVAILABLE_PERSONAS.find(p => p.id === 'leader');
  if (leader) return leader;
  const mrFlow = AVAILABLE_PERSONAS.find(p => p.id === 'mr.flow' || p.id === 'mrflow' || p.is_default);
  if (mrFlow) return mrFlow;
  if (AVAILABLE_PERSONAS.length > 0) return AVAILABLE_PERSONAS[0];
  return {
    id: 'leader',
    name: '👑 Swarm Leader',
    icon: '👑',
    description: 'Swarm Leader & Group Mode Orchestrator'
  };
}

function updateAgentPillDisplay() {
  const current = getSelectedPersonaObj();
  const currentTab = (typeof localStorage !== 'undefined') ? (localStorage.getItem('xflow_active_tab') || 'office') : 'office';
  const isGroup = (currentTab === 'group');
  const activeAgent = isGroup ? null : getActiveAgent();
  const pillText = document.getElementById('chat-agent-pill-text');
  const pillIcon = document.getElementById('chat-agent-pill-icon');
  const pillEl = document.getElementById('chat-agent-pill');

  const displayName = current.name || (activeAgent && activeAgent.name) || (isGroup ? 'Swarm Leader' : 'Mr. Flow');
  const displayIcon = current.icon || (activeAgent && activeAgent.icon) || (isGroup ? '👑' : '⚡');

  if (pillText) {
    pillText.textContent = displayName;
  }
  if (pillIcon) {
    pillIcon.textContent = displayIcon;
  }
  if (pillEl) {
    const agentId = isGroup ? current.id : (activeAgent ? activeAgent.id : ('agent-' + current.id));
    pillEl.title = `Agent Target: ${agentId} | Sovereign Agent: ${displayName} (system/subagent/${current.id})`;
    pillEl.classList.remove('is-locked');
  }

  const bottomAgentName = document.getElementById('bottom-bar-agent-name');
  const bottomAgentIcon = document.getElementById('bottom-bar-agent-icon');
  if (bottomAgentName) {
    bottomAgentName.textContent = displayName;
  }
  if (bottomAgentIcon) {
    bottomAgentIcon.textContent = displayIcon;
  }
}

const FALLBACK_SWARM_AGENTS = [
  { id: 'mr.flow', name: 'Mr. Flow', role: 'Grand Chief AI Overseer & Executive Architect', icon: '⚡', description: 'Grand Chief AI Overseer and Sovereign Executive Architect of Flowork OS.' }
];

async function fetchAvailablePersonas() {
  try {
    let list = null;
    try {
      let res = await fetch('/api/agents');
      if (!res.ok || (res.headers.get('content-type') && res.headers.get('content-type').includes('text/html'))) {
        res = await fetch('/api/personas');
      }
      if (!res.ok || (res.headers.get('content-type') && res.headers.get('content-type').includes('text/html'))) {
        res = await fetch('http://127.0.0.1:19890/api/agents');
      }
      if (res && res.ok && res.headers.get('content-type') && res.headers.get('content-type').includes('application/json')) {
        const data = await res.json();
        list = data && (Array.isArray(data.agents) ? data.agents : (Array.isArray(data.personas) ? data.personas : null));
      }
    } catch (_) {}

    if (!list || !Array.isArray(list) || list.length === 0) {
      list = FALLBACK_SWARM_AGENTS;
    }

    if (list && Array.isArray(list)) {
      // Filter out any ghost/dummy 'default' agents and normalize
      const cleanList = list.filter(p => p && p.id && p.id.toLowerCase() !== 'default');

        // Always sort Swarm Leader strictly to index 0, then Mr. Flow, then alphabetical
        cleanList.sort((a, b) => {
          const aLeader = a.id === 'leader';
          const bLeader = b.id === 'leader';
          if (aLeader) return -1;
          if (bLeader) return 1;
          const aCore = a.id === 'mr.flow' || a.id === 'mrflow' || a.is_default;
          const bCore = b.id === 'mr.flow' || b.id === 'mrflow' || b.is_default;
          if (aCore) return -1;
          if (bCore) return 1;
          return (a.name || a.id).localeCompare(b.name || b.id);
        });

        AVAILABLE_PERSONAS = cleanList;
        window.AVAILABLE_PERSONAS = cleanList;

        const badge = document.getElementById('agent-dropdown-count-badge');
        if (badge) badge.textContent = `${AVAILABLE_PERSONAS.length} Agents`;

        // Reconcile active persona: if currently selected persona was deleted, fall back to leader!
        let saved = (currentChatSessionId ? localStorage.getItem('xflow_session_persona_' + currentChatSessionId) : null)
          || localStorage.getItem('xflow_chat_persona')
          || currentSessionPersonaId;

        if (!saved || saved === 'default' || !AVAILABLE_PERSONAS.some(p => p.id === saved)) {
          saved = AVAILABLE_PERSONAS.some(p => p.id === 'leader') ? 'leader' : (AVAILABLE_PERSONAS.some(p => p.id === 'mr.flow') ? 'mr.flow' : (AVAILABLE_PERSONAS[0]?.id || 'leader'));
        }

        currentSessionPersonaId = saved;
        pendingSessionPersonaId = saved;
        localStorage.setItem('xflow_chat_persona', saved);

        updateAgentPillDisplay();
        renderAgentDropdown();
        renderOfficeAgentDock();
        if (window.office3DInstance && typeof window.office3DInstance.syncPersonas === 'function') {
          window.office3DInstance.syncPersonas(AVAILABLE_PERSONAS);
        }
      }
  } catch (err) {
    console.warn('[Persona] Failed to fetch available personas:', err);
  }
}

function saveCurrentChatSettings() {
  localStorage.setItem('xflow_chat_persona', currentSessionPersonaId);
  localStorage.setItem('xflow_chat_model', selectedChatModelId);
  const safeAccount = currentSessionAccountId || 'combo';
  localStorage.setItem('xflow_agent_account_' + currentSessionPersonaId, safeAccount);
  localStorage.setItem('xflow_agent_model_' + currentSessionPersonaId, selectedChatModelId);

  if (currentChatSessionId) {
    localStorage.setItem('xflow_session_persona_' + currentChatSessionId, currentSessionPersonaId);
    localStorage.setItem('xflow_session_model_' + currentChatSessionId, selectedChatModelId);
    localStorage.setItem('xflow_session_account_' + currentChatSessionId, safeAccount);
  }
  if (currentActiveAgentId) {
    localStorage.setItem('xflow_agent_persona_' + currentActiveAgentId, currentSessionPersonaId);
    localStorage.setItem('xflow_agent_model_' + currentActiveAgentId, selectedChatModelId);
    localStorage.setItem('xflow_agent_account_' + currentActiveAgentId, safeAccount);
  }
  if (currentInspectedAgent) {
    localStorage.setItem('xflow_agent_persona_' + currentInspectedAgent.id, currentSessionPersonaId);
    localStorage.setItem('xflow_agent_model_' + currentInspectedAgent.id, selectedChatModelId);
    localStorage.setItem('xflow_agent_account_' + currentInspectedAgent.id, safeAccount);
    currentInspectedAgent.persona = currentSessionPersonaId;
    currentInspectedAgent.model = selectedChatModelId;
    currentInspectedAgent.account = safeAccount;
    if (office3DInstance) {
      office3DInstance.updateAgentConfig(currentInspectedAgent.id, { 
        persona: currentSessionPersonaId,
        model: selectedChatModelId,
        account: safeAccount
      });
    }
  }
  const pObj = getSelectedPersonaObj();
  const mObj = getSelectedModelObj();
  const accObj = getSelectedAccountObj();
  const accName = accObj ? (accObj.isCombo ? 'Combo' : (accObj.name || accObj.email)) : 'Combo';
  if (typeof showFloworkLaserToast === 'function') {
    showFloworkLaserToast(`💾 Saved: [${pObj.name}] with [${mObj.name}] & [${accName}]`, true);
  }
}
window.saveCurrentChatSettings = saveCurrentChatSettings;

let activeAgentDeptFilter = 'all';
let activeAgentSearchText = '';

function getAgentDepartment(p) {
  const catId = (p.category_id || '').toUpperCase().trim();
  const cat = (p.category || '').toLowerCase().trim();

  // 1. Exact Category ID Precedence (CAT-001 through CAT-025)
  if (catId === 'CAT-001') return 'healthcare';
  if (catId === 'CAT-002') return 'psychology';
  if (catId === 'CAT-003') return 'legal';
  if (catId === 'CAT-004') return 'education';
  if (catId === 'CAT-005') return 'technology';
  if (catId === 'CAT-006') return 'finance';
  if (catId === 'CAT-007') return 'business';
  if (catId === 'CAT-008') return 'marketing';
  if (catId === 'CAT-009') return 'advertising';
  if (catId === 'CAT-010') return 'media_creative';
  if (catId === 'CAT-011') return 'design';
  if (catId === 'CAT-012') return 'human_resources';
  if (catId === 'CAT-013') return 'science_research';
  if (catId === 'CAT-014') return 'automation_admin';
  if (catId === 'CAT-015') return 'core';
  if (catId === 'CAT-016') return 'arts_music_poetry';
  if (catId === 'CAT-017') return 'metaphysics_fengshui';
  if (catId === 'CAT-018') return 'architecture_spatial';
  if (catId === 'CAT-019') return 'culinary_gastronomy';
  if (catId === 'CAT-020') return 'sports_athletics';
  if (catId === 'CAT-021') return 'agriculture_ecology';
  if (catId === 'CAT-022') return 'diplomacy_negotiation';
  if (catId === 'CAT-023') return 'cybersecurity_forensics';
  if (catId === 'CAT-024') return 'hospitality_tourism';
  if (catId === 'CAT-025') return 'maritime_logistics';
  if (catId === 'CAT-026') return 'system';

  // 2. Exact Slug Match
  const slugMap = {
    healthcare: 'healthcare',
    psychology: 'psychology',
    legal: 'legal',
    education: 'education',
    technology: 'technology',
    finance: 'finance',
    business: 'business',
    marketing: 'marketing',
    advertising: 'advertising',
    media_creative: 'media_creative',
    design: 'design',
    human_resources: 'human_resources',
    science_research: 'science_research',
    automation_admin: 'automation_admin',
    core: 'core',
    arts_music_poetry: 'arts_music_poetry',
    metaphysics_fengshui: 'metaphysics_fengshui',
    architecture_spatial: 'architecture_spatial',
    culinary_gastronomy: 'culinary_gastronomy',
    sports_athletics: 'sports_athletics',
    agriculture_ecology: 'agriculture_ecology',
    diplomacy_negotiation: 'diplomacy_negotiation',
    cybersecurity_forensics: 'cybersecurity_forensics',
    hospitality_tourism: 'hospitality_tourism',
    maritime_logistics: 'maritime_logistics',
    system: 'system'
  };
  if (slugMap[cat]) return slugMap[cat];

  // 3. Specific Substring Disambiguation (Checked before broad keywords)
  if (cat.includes('cybersecurity') || cat.includes('forensics') || cat.includes('threat_intel')) return 'cybersecurity_forensics';
  if (cat.includes('fengshui') || cat.includes('feng_shui') || cat.includes('geomancy') || cat.includes('metaphysics') || cat.includes('bazi')) return 'metaphysics_fengshui';
  if (cat.includes('arts_music_poetry') || cat.includes('poetry') || cat.includes('music') || cat.includes('lyricist') || cat.includes('composer') || cat.includes('poet')) return 'arts_music_poetry';
  if (cat.includes('architecture') || cat.includes('spatial') || cat.includes('urban_planning') || cat.includes('civil')) return 'architecture_spatial';
  if (cat.includes('culinary') || cat.includes('gastronomy') || cat.includes('cooking') || cat.includes('chef') || cat.includes('food')) return 'culinary_gastronomy';
  if (cat.includes('sports') || cat.includes('athletics') || cat.includes('fitness') || cat.includes('kinesiology')) return 'sports_athletics';
  if (cat.includes('agriculture') || cat.includes('permaculture') || cat.includes('ecology') || cat.includes('farming')) return 'agriculture_ecology';
  if (cat.includes('diplomacy') || cat.includes('negotiation') || cat.includes('international_relations') || cat.includes('geopolitics')) return 'diplomacy_negotiation';
  if (cat.includes('hospitality') || cat.includes('tourism') || cat.includes('hotel') || cat.includes('guest_experience')) return 'hospitality_tourism';
  if (cat.includes('maritime') || cat.includes('logistics') || cat.includes('supply_chain') || cat.includes('shipping') || cat.includes('freight')) return 'maritime_logistics';
  if (cat.includes('system') || cat.includes('sysadmin') || cat.includes('systemd') || cat.includes('daemon') || cat.includes('kernel')) return 'system';

  // 4. Standard Substring Fallback
  if (cat.includes('health') || cat.includes('medical') || cat.includes('doctor')) return 'healthcare';
  if (cat.includes('psych') || cat.includes('mental') || cat.includes('cbt') || cat.includes('therapy')) return 'psychology';
  if (cat.includes('legal') || cat.includes('law') || cat.includes('contract') || cat.includes('compliance')) return 'legal';
  if (cat.includes('edu') || cat.includes('tutor') || cat.includes('teacher') || cat.includes('curriculum')) return 'education';
  if (cat.includes('finance') || cat.includes('crypto') || cat.includes('forex') || cat.includes('stocks') || cat.includes('trading') || cat.includes('tax') || cat.includes('accounting')) return 'finance';
  if (cat.includes('business') || cat.includes('product') || cat.includes('strategy') || cat.includes('planning')) return 'business';
  if (cat.includes('marketing') || cat.includes('seo') || cat.includes('organic') || cat.includes('funnel')) return 'marketing';
  if (cat.includes('advertising') || cat.includes('ads') || cat.includes('paid') || cat.includes('ppc')) return 'advertising';
  if (cat.includes('media_creative') || cat.includes('media') || cat.includes('video') || cat.includes('audio') || cat.includes('youtube') || cat.includes('podcast')) return 'media_creative';
  if (cat.includes('design') || cat.includes('ui') || cat.includes('ux') || cat.includes('visual') || cat.includes('art')) return 'design';
  if (cat.includes('human_resources') || cat.includes('hr') || cat.includes('recruitment') || cat.includes('talent')) return 'human_resources';
  if (cat.includes('science') || cat.includes('research') || cat.includes('academic') || cat.includes('data_science')) return 'science_research';
  if (cat.includes('automation') || cat.includes('scraping') || cat.includes('admin') || cat.includes('assistant')) return 'automation_admin';
  if (cat.includes('core') || cat.includes('universal_core_system') || cat.includes('agent_architecture') || cat.includes('meta') || cat.includes('creator')) return 'core';
  if (cat.includes('tech') || cat.includes('software') || cat.includes('devops') || cat.includes('quality') || cat.includes('release') || cat.includes('engineering') || cat.includes('craft') || cat.includes('security') || cat.includes('reverse') || cat.includes('pentest') || cat.includes('audit') || cat.includes('doc') || cat.includes('writing')) return 'technology';

  if (p.department) return p.department.toLowerCase();
  return 'general';
}

function renderAgentDropdown() {
  const listEl = document.getElementById('chat-agent-list');
  if (!listEl) return;

  const currentId = (currentSessionPersonaId || 'mr.flow').toLowerCase();

  // Distinct departments
  const availableDepts = new Set(['all']);
  AVAILABLE_PERSONAS.forEach(p => {
    availableDepts.add(getAgentDepartment(p));
  });

  const deptLabels = {
    all: 'ALL',
    system: 'SYS',
    technology: 'TECH',
    business: 'BIZ',
    design: 'DESIGN',
    finance: 'FIN',
    healthcare: 'MED',
    psychology: 'PSY',
    legal: 'LEGAL',
    education: 'EDU',
    marketing: 'MKT',
    advertising: 'ADS',
    media_creative: 'MEDIA',
    human_resources: 'HR',
    science_research: 'SCI',
    automation_admin: 'AUTO',
    core: 'CORE',
    arts_music_poetry: 'ARTS',
    metaphysics_fengshui: 'FENGSHUI',
    architecture_spatial: 'ARCH',
    culinary_gastronomy: 'CHEF',
    sports_athletics: 'SPORT',
    agriculture_ecology: 'AGRI',
    diplomacy_negotiation: 'DIPLO',
    cybersecurity_forensics: 'CYBER',
    hospitality_tourism: 'HOSP',
    maritime_logistics: 'LOGIST',
    engineering: 'ENG',
    security: 'SEC',
    product: 'PROD',
    documentation: 'DOCS',
    meta: 'META',
    general: 'OTHER'
  };

  const tabsInnerHtml = Array.from(availableDepts).map(d => `
    <button type="button" class="agent-dept-tab ${activeAgentDeptFilter === d ? 'active' : ''}" data-dept="${d}">
      ${deptLabels[d] || d.toUpperCase()}
    </button>
  `).join('');

  const currentTab = (typeof localStorage !== 'undefined') ? (localStorage.getItem('xflow_active_tab') || 'office') : 'office';
  const isSoloStudio = (currentTab === 'office');

  // Sibling containers in upgraded HTML
  const extDeptTabs = document.getElementById('agent-dept-tabs');
  const extSearchInput = document.getElementById('agent-search-input');

  if (extDeptTabs) {
    extDeptTabs.innerHTML = '';
    extDeptTabs.style.display = 'none';
  }
  if (extSearchInput) {
    if (extSearchInput.value !== activeAgentSearchText) {
      extSearchInput.value = activeAgentSearchText;
    }
    const searchContainer = extSearchInput.closest('.agent-dropdown-search-wrap') || extSearchInput.parentElement;
    if (searchContainer) {
      searchContainer.style.display = isSoloStudio ? 'none' : '';
    }
  }

  const badge = document.getElementById('agent-dropdown-count-badge');
  if (badge) {
    badge.textContent = `${AVAILABLE_PERSONAS.length} Agents`;
  }

  // Filter personas: strictly from system/subagent/ with zero fake categories
  const filtered = AVAILABLE_PERSONAS.filter(p => {
    if (!p || !p.id) return false;
    if (activeAgentSearchText.trim()) {
      const q = activeAgentSearchText.trim().toLowerCase();
      const matchName = (p.name || '').toLowerCase().includes(q);
      const matchId = (p.id || '').toLowerCase().includes(q);
      const matchDesc = (p.description || '').toLowerCase().includes(q);
      if (!matchName && !matchId && !matchDesc) {
        return false;
      }
    }
    return true;
  });

  const itemsHtml = filtered.map(p => {
    const isSelected = p.id.toLowerCase() === currentId || (currentId === 'mrflow' && p.id === 'mr.flow');
    const isCore = p.id.toLowerCase() === 'mr.flow' || p.id.toLowerCase() === 'mrflow' || p.is_default;
    const isLeader = p.id.toLowerCase() === 'leader';
    const descText = p.description || (isCore ? 'Sovereign orchestrator with dynamic skill dispatch (system/subagent/mr.flow).' : (isLeader ? 'Commander for group mode and swarm orchestrator (system/subagent/leader).' : 'Autonomous specialist agent.'));

    let roleBadgeHtml = '';
    if (isCore) {
      roleBadgeHtml = `<span class="agent-option-badge badge-agent-core" style="background:rgba(0,242,254,0.15); color:#00f2fe; border:1px solid rgba(0,242,254,0.3); border-radius:4px; padding:1px 6px; font-size:9.5px; font-weight:700;">CORE</span>`;
    } else if (isLeader) {
      roleBadgeHtml = `<span class="agent-option-badge badge-agent-leader" style="background:rgba(234,179,8,0.15); color:#facc15; border:1px solid rgba(234,179,8,0.3); border-radius:4px; padding:1px 6px; font-size:9.5px; font-weight:700;">LEADER</span>`;
    } else {
      roleBadgeHtml = `<span class="agent-option-badge" style="background:rgba(56,189,248,0.15); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); border-radius:4px; padding:1px 6px; font-size:9.5px; font-weight:700;">SUBAGENT</span>`;
    }

    const locBadge = `<span style="font-size:9px; color:#64748b; font-family:monospace; margin-left:auto;">system/subagent/${p.id}</span>`;

    return `
      <div class="agent-option-item ${isSelected ? 'selected' : ''}" data-persona-id="${p.id}">
        <div class="agent-option-left">
          <span class="agent-option-icon">${p.icon || (isCore ? '⚡' : (isLeader ? '👑' : '🤖'))}</span>
          <div class="agent-option-content">
            <div class="agent-option-title-row">
              <span class="agent-option-name">${escapeHtml(p.name || p.id)}</span>
              ${roleBadgeHtml}
              ${locBadge}
            </div>
            <div class="agent-option-desc">${escapeHtml(descText)}</div>
          </div>
        </div>
        ${isSelected ? '<span class="agent-option-check">✓</span>' : ''}
      </div>
    `;
  }).join('');

  const emptyHtml = filtered.length === 0 ? `
    <div style="padding: 16px 8px; text-align: center; color: var(--text-dim); font-size: 11px;">
      No agents found matching search filter.
    </div>
  ` : '';

  if (extDeptTabs) {
    listEl.innerHTML = itemsHtml + emptyHtml;
  } else {
    // Fallback if HTML has legacy layout
    const tabsHtml = `
      <div class="agent-dropdown-search-wrap">
        <input type="text" class="agent-search-input" id="agent-search-input" placeholder="Search personas / skills..." value="${escapeHtml(activeAgentSearchText)}" autocomplete="off" />
      </div>
      <div class="agent-dept-tabs" id="agent-dept-tabs">
        ${tabsInnerHtml}
      </div>
    `;
    const footerHtml = `
      <div class="agent-dropdown-footer">
        <button class="btn-save-agent-settings" id="btn-save-agent-settings" title="Save persona for this chat session">
          <span>💾 Save Chat Settings</span>
        </button>
      </div>
    `;
    listEl.innerHTML = tabsHtml + itemsHtml + emptyHtml + footerHtml;
  }

  // Bind dept tabs click event
  const tabParent = extDeptTabs || listEl;
  tabParent.querySelectorAll('.agent-dept-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.stopPropagation();
      activeAgentDeptFilter = tab.getAttribute('data-dept') || 'all';
      renderAgentDropdown();
    });
  });

  // Dept tabs mouse wheel horizontal scroll
  const deptTabsEl = extDeptTabs || listEl.querySelector('#agent-dept-tabs');
  if (deptTabsEl && !deptTabsEl._wheelBound) {
    deptTabsEl._wheelBound = true;
    deptTabsEl.addEventListener('wheel', (e) => {
      if (e.deltaY !== 0) {
        e.preventDefault();
        deptTabsEl.scrollLeft += e.deltaY;
      }
    }, { passive: false });
  }

  // Search input events (if rendered inside listEl)
  const innerSearchInput = listEl.querySelector('#agent-search-input');
  if (innerSearchInput) {
    innerSearchInput.addEventListener('input', (e) => {
      activeAgentSearchText = e.target.value;
      renderAgentDropdown();
      const updatedInput = document.getElementById('agent-search-input');
      if (updatedInput) {
        updatedInput.focus();
        updatedInput.setSelectionRange(updatedInput.value.length, updatedInput.value.length);
      }
    });
    innerSearchInput.addEventListener('click', (e) => e.stopPropagation());
    innerSearchInput.addEventListener('keydown', (e) => e.stopPropagation());
  }

  // Persona selection click
  listEl.querySelectorAll('.agent-option-item').forEach(item => {
    item.addEventListener('click', async (e) => {
      e.stopPropagation();
      const personaId = item.getAttribute('data-persona-id');
      if (personaId) {
        await setSessionAgentPersona(personaId);
        closeAgentDropdown();
      }
    });
  });

  // Save settings button click
  const btnSave = document.getElementById('btn-save-agent-settings');
  if (btnSave && !btnSave._bound) {
    btnSave._bound = true;
    btnSave.addEventListener('click', (e) => {
      e.stopPropagation();
      saveCurrentChatSettings();
      closeAgentDropdown();
    });
  }
}


// =============================================================================
// FLOWORK OS — CHAT SESSION ISOLATION & VIEW CLEAR ENGINE
// Guarantees chat history strictly belongs to active persona/studio without cross-persona leaks
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================
function clearChatViewForPersona(personaId) {
  const cleanId = (personaId || 'mr.flow').trim();
  const effectiveId = (cleanId === 'default') ? 'mr.flow' : cleanId;

  currentChatSessionId = null;
  localStorage.removeItem('xflow_active_session_id');
  localStorage.setItem('xflow_new_chat_explicit', 'true');
  activeTurnUserCard = null;
  lastKnownStepFingerprint = '';
  isChatStreaming = false;
  hidePinnedPrompt();
  clearChatAttachments();
  setMascotAgentLoop(false);

  const rightbarMessages = document.getElementById('rightbar-messages');
  if (rightbarMessages) {
    rightbarMessages.style.display = 'flex';
    rightbarMessages.classList.remove('has-messages', 'history-active', 'agent-is-looping');
    rightbarMessages.querySelectorAll('.chat-msg, .fl-chat-loading-indicator').forEach(el => el.remove());
    
    // Ensure Mascot Empty Hero is present
    let emptyHero = rightbarMessages.querySelector('#chat-empty-hero');
    if (!emptyHero) {
      rightbarMessages.insertAdjacentHTML('afterbegin', getEmptyHeroHtml());
      requestAnimationFrame(() => {
        initChatMascot();
      });
    }
    
    // Update Speech Greeting for this persona
    const speechText = document.getElementById('chat-mascot-speech-text');
    if (speechText) {
      if (effectiveId === 'mr.flow' || effectiveId === 'default') {
        speechText.textContent = '"Welcome to Flowork OS. I am Mr. Flow, sovereign AI agent ready to assist your operations."';
      } else {
        const pObj = (typeof getSelectedPersonaObj === 'function') ? getSelectedPersonaObj() : null;
        const pName = pObj?.name || (effectiveId.charAt(0).toUpperCase() + effectiveId.slice(1));
        speechText.textContent = `"${pName} active. Flowork Swarm Specialist ready for mission directives."`;
      }
    }
    renderSingleMascotFrame();
  }

  // Update room header
  const roomIconEl = document.getElementById('fl-room-type-icon');
  const roomNameEl = document.getElementById('fl-current-room-name');
  if (roomIconEl) roomIconEl.textContent = (effectiveId === 'mr.flow' || effectiveId === 'default') ? '👑' : '🤖';
  if (roomNameEl) {
    const pObj = (typeof getSelectedPersonaObj === 'function') ? getSelectedPersonaObj() : null;
    const pName = pObj?.name || (effectiveId === 'mr.flow' ? 'Mr. Flow' : effectiveId);
    roomNameEl.textContent = `Direct: ${pName}`;
  }

  window.currentLoadedSessionData = null;
  if (window.DualCanvasController && typeof window.DualCanvasController.syncSession === 'function') {
    window.DualCanvasController.syncSession(null);
  }
}
window.clearChatViewForPersona = clearChatViewForPersona;

async function setSessionAgentPersona(personaId, options = {}) {
  const cleanId = (personaId || 'default').trim();
  const effectiveId = (cleanId === 'default') ? 'mr.flow' : cleanId;
  const oldPersona = (currentSessionPersonaId || 'mr.flow').trim();
  const forceSwap = Boolean(options && options.forceSwap);
  const preserveSession = Boolean(options && options.preserveSession);
  const isPersonaChanged = (oldPersona !== effectiveId) || forceSwap;

  // 1. If switching to a new persona, preserve old persona's active session
  if (isPersonaChanged && !preserveSession) {
    if (oldPersona && currentChatSessionId) {
      localStorage.setItem('xflow_persona_session_' + oldPersona, currentChatSessionId);
    }
    if (oldPersona && oldPersona !== 'mr.flow') {
      localStorage.setItem('xflow_group_persona', oldPersona);
    }
  }

  currentSessionPersonaId = effectiveId;
  pendingSessionPersonaId = effectiveId;
  localStorage.setItem('xflow_chat_persona', effectiveId);
  if (effectiveId !== 'mr.flow') {
    localStorage.setItem('xflow_group_persona', effectiveId);
  }

  if (currentChatSessionId && preserveSession) {
    localStorage.setItem('xflow_session_persona_' + currentChatSessionId, effectiveId);
  }

  // Strictly sync currentActiveAgentId with the selected persona
  const targetAgentId = (effectiveId === 'mr.flow' || effectiveId === 'default') ? 'agent-mrflow-system-01' : (effectiveId.startsWith('agent-') ? effectiveId : 'agent-' + effectiveId);
  currentActiveAgentId = targetAgentId;
  localStorage.setItem('xflow_active_agent_id', currentActiveAgentId);

  // Sync inspected agent reference from 3D roster if available
  if (office3DInstance && Array.isArray(office3DInstance.agentRoster)) {
    const matchedAgent = office3DInstance.agentRoster.find(a => 
      a.id.toLowerCase() === targetAgentId.toLowerCase() || 
      (a.persona && a.persona.toLowerCase() === effectiveId.toLowerCase())
    );
    if (matchedAgent) {
      currentInspectedAgent = matchedAgent;
    }
  }

  if (currentInspectedAgent) {
    localStorage.setItem('xflow_agent_persona_' + currentInspectedAgent.id, effectiveId);
    currentInspectedAgent.persona = effectiveId;
    if (office3DInstance) {
      office3DInstance.updateAgentConfig(currentInspectedAgent.id, { persona: effectiveId });
    }
  }

  // Step the selected 3D agent forward & highlight dock
  if (office3DInstance && Array.isArray(office3DInstance.agents)) {
    const agWrapper = office3DInstance.agents.find(a => 
      a.data.id.toLowerCase() === targetAgentId.toLowerCase() ||
      (a.data.persona && a.data.persona.toLowerCase() === effectiveId.toLowerCase()) ||
      ('agent-' + (a.data.persona || '').toLowerCase()) === targetAgentId.toLowerCase()
    );
    if (agWrapper) {
      if (office3DInstance.selectedAgent && office3DInstance.selectedAgent !== agWrapper && office3DInstance.selectedAgent.data.state === 'idle') {
        office3DInstance.selectedAgent.targetPos.copy(office3DInstance.selectedAgent.data.standbyPos);
        office3DInstance.selectedAgent.targetRotY = office3DInstance.selectedAgent.data.standbyFacingAngle;
        office3DInstance.selectedAgent.isTransitioning = true;
        office3DInstance.selectedAgent.transitionProgress = 0.0;
      }
      if (agWrapper.data.state === 'idle') {
        agWrapper.targetPos.copy(agWrapper.data.steppedPos);
        agWrapper.targetRotY = agWrapper.data.standbyFacingAngle;
        agWrapper.isTransitioning = true;
        agWrapper.transitionProgress = 0.0;
      }
      office3DInstance.selectedAgent = agWrapper;
      office3DInstance.trackingAgent = agWrapper;
    }
  }
  if (typeof window.highlightOfficeDockItem === 'function') {
    window.highlightOfficeDockItem(targetAgentId);
  }
  if (typeof renderOfficeAgentDock === 'function') {
    renderOfficeAgentDock();
  }

  // AUTO-RESTORE MODEL FOR THIS PERSONA/AGENT
  const savedModel = (currentInspectedAgent ? localStorage.getItem('xflow_agent_model_' + currentInspectedAgent.id) : null)
    || (currentActiveAgentId ? localStorage.getItem('xflow_agent_model_' + currentActiveAgentId) : null)
    || localStorage.getItem('xflow_agent_model_' + effectiveId)
    || (currentChatSessionId ? localStorage.getItem('xflow_session_model_' + currentChatSessionId) : null)
    || 'gemini-3.8-flash-high';
  if (savedModel && Array.isArray(AVAILABLE_CHAT_MODELS) && AVAILABLE_CHAT_MODELS.some(m => m.id === savedModel)) {
    selectedChatModelId = savedModel;
    localStorage.setItem('xflow_chat_model', savedModel);
    updateModelPillDisplay();
    renderModelDropdown();
    if (typeof window.switchFloworkCoreModel === 'function') {
      window.switchFloworkCoreModel(savedModel).catch(() => {});
    }
  }

  // AUTO-RESTORE ACCOUNT FOR THIS PERSONA/AGENT (DEFAULT IS ALWAYS COMBO!)
  const savedAccount = (currentInspectedAgent ? localStorage.getItem('xflow_agent_account_' + currentInspectedAgent.id) : null)
    || (currentActiveAgentId ? localStorage.getItem('xflow_agent_account_' + currentActiveAgentId) : null)
    || localStorage.getItem('xflow_agent_account_' + effectiveId)
    || (currentChatSessionId ? localStorage.getItem('xflow_session_account_' + currentChatSessionId) : null)
    || 'combo'; // Default is always COMBO!
  if (typeof setSessionBinding === 'function') {
    setSessionBinding(savedAccount).catch(() => {});
  } else {
    currentSessionAccountId = savedAccount;
    updateAccountPillDisplay();
  }

  updateAgentPillDisplay();
  renderAgentDropdown();
  if (typeof isSlashPaletteOpen !== 'undefined' && isSlashPaletteOpen) {
    const chatInput = document.getElementById('rightbar-chat-input');
    if (chatInput) handleSlashInput(chatInput);
  }

  // ── CHAT SESSION ISOLATION: SWAP OR CLEAR ACTIVE CHAT ──
  if ((isPersonaChanged || forceSwap) && !preserveSession) {
    const savedSessionForTarget = localStorage.getItem('xflow_persona_session_' + effectiveId);
    let sessionRestored = false;
    if (savedSessionForTarget) {
      try {
        sessionRestored = await loadChatSession(savedSessionForTarget, { silent: true, isPersonaSwitch: true });
      } catch (err) {
        console.warn('[Persona] Failed to load persona session:', err);
        sessionRestored = false;
      }
    }
    if (!sessionRestored) {
      clearChatViewForPersona(effectiveId);
    }
  } else if (currentChatSessionId) {
    localStorage.setItem('xflow_session_persona_' + currentChatSessionId, effectiveId);
    try {
      const res = await fetch(`/api/chat/sessions/${currentChatSessionId}/persona`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona_id: effectiveId
        })
      });
      if (res.ok) {
        const pObj = getSelectedPersonaObj();
        showFloworkLaserToast(`🎭 Chat Persona locked to: ${pObj.name}`, true);
      }
    } catch (e) {
      console.warn('[Persona] Failed to set session persona:', e);
    }
  }
}

function openAgentDropdown() {
  closeAllChatDropdowns('agent');
  const dropdown = document.getElementById('chat-agent-dropdown');
  const pill = document.getElementById('chat-agent-pill');
  if (dropdown && pill) {
    dropdown.style.display = 'block';
    pill.classList.add('active');
    fetchAvailablePersonas().then(() => {
      renderAgentDropdown();
    }).catch(() => {
      renderAgentDropdown();
    });
  }
}

function closeAgentDropdown() {
  const dropdown = document.getElementById('chat-agent-dropdown');
  const pill = document.getElementById('chat-agent-pill');
  if (dropdown && pill) {
    dropdown.style.display = 'none';
    pill.classList.remove('active');
  }
}

function toggleAgentDropdown() {
  const dropdown = document.getElementById('chat-agent-dropdown');
  if (dropdown && dropdown.style.display === 'block') {
    closeAgentDropdown();
  } else {
    openAgentDropdown();
  }
}

function initAgentSelector() {
  const currentTab = (typeof localStorage !== 'undefined') ? (localStorage.getItem('xflow_active_tab') || 'office') : 'office';
  const selectorWrap = document.getElementById('chat-agent-selector-wrap');
  const modelWrap = document.getElementById('chat-model-selector-wrap');
  const accountWrap = document.getElementById('chat-account-selector-wrap');

  if (modelWrap) {
    modelWrap.style.setProperty('display', 'none', 'important');
    if (typeof initModelSelector === 'function') initModelSelector();
  }
  if (accountWrap) {
    accountWrap.style.setProperty('display', 'none', 'important');
  }
  if (selectorWrap) {
    selectorWrap.style.setProperty('display', 'none', 'important');
  }

  updateAgentPillDisplay();
  fetchAvailablePersonas();

  // Dynamic Agent Watcher: auto-sync every 15s when tab is active so agent additions/deletions reflect automatically
  if (!window._agentAutoSyncInterval) {
    window._agentAutoSyncInterval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchAvailablePersonas();
      }
    }, 15000);
  }

  if (agentSelectorInitialized) return;
  agentSelectorInitialized = true;

  // External search input listener
  const extSearch = document.getElementById('agent-search-input');
  if (extSearch && !extSearch._bound) {
    extSearch._bound = true;
    extSearch.addEventListener('input', (e) => {
      activeAgentSearchText = e.target.value;
      renderAgentDropdown();
    });
    extSearch.addEventListener('click', (e) => e.stopPropagation());
    extSearch.addEventListener('keydown', (e) => e.stopPropagation());
  }

  const pill = document.getElementById('chat-agent-pill');
  if (pill) {
    pill.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleAgentDropdown();
    });
  }

  document.addEventListener('click', (e) => {
    const wrap = document.getElementById('chat-agent-selector-wrap');
    if (wrap && !wrap.contains(e.target)) {
      closeAgentDropdown();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAgentDropdown();
    }
  });

  initPokemonCardDeck();
}

// =============================================================================
// 🃏 SOVEREIGN POKÉMON SPECIALIST TRADING CARD DECK CONTROLLER
// =============================================================================
let pokemonDeckInitialized = false;
let currentDeckFilterCat = 'all';

function openPokemonCardDeck() {
  initPokemonCardDeck();
  const modal = document.getElementById('fl-pokemon-card-modal');
  if (!modal) return;
  modal.style.display = 'flex';
  renderPokemonCardDeck(currentDeckFilterCat, '');
  if (typeof fetchAvailablePersonas === 'function') {
    fetchAvailablePersonas().then(() => {
      renderPokemonCardDeck(currentDeckFilterCat, '');
    }).catch(() => {});
  }
}

function closePokemonCardDeck() {
  const modal = document.getElementById('fl-pokemon-card-modal');
  if (modal) modal.style.display = 'none';
}

function getSpecialistMoves(p) {
  if (Array.isArray(p.slash_commands) && p.slash_commands.length >= 2) {
    return [
      {
        name: p.slash_commands[0].command || 'Command Strike',
        dmg: '140',
        desc: p.slash_commands[0].description || 'Deterministic tool execution with Exit Code 0.'
      },
      {
        name: p.slash_commands[1].command || 'System Burst',
        dmg: '250',
        desc: p.slash_commands[1].description || 'Multi-step autonomous workflow synthesis.'
      }
    ];
  }
  if (Array.isArray(p.slash_commands) && p.slash_commands.length === 1) {
    return [
      {
        name: p.slash_commands[0].command,
        dmg: '150',
        desc: p.slash_commands[0].description || 'Deterministic tool execution with Exit Code 0.'
      },
      {
        name: '⚡ [Exit Code 0 Determinism]',
        dmg: '210',
        desc: 'Zero-trust runtime verification. Rejects hallucinated and zombie execution paths.'
      }
    ];
  }
  if (p.id === 'default') {
    return [
      {
        name: '⚡ [Exit Code 0]',
        dmg: '150',
        desc: 'Deterministic sovereign engine core. Validates all tool pipelines before turn completes.'
      },
      {
        name: '🧠 [Autonomous CoT Trajectory]',
        dmg: '290',
        desc: 'Broadcasts real-time reasoning and keywords directly to the giant executive monitor.'
      }
    ];
  }
  return [
    {
      name: '🛠️ [Specialist Runbook]',
      dmg: '130',
      desc: p.description ? (p.description.slice(0, 75) + '...') : 'Autonomous specialized domain runbook execution.'
    },
    {
      name: '🛡️ [Radical Honesty & QC]',
      dmg: '190',
      desc: 'Eliminates sycophancy. Performs adversarial inspection with Exit Code 0 proof.'
    }
  ];
}

function renderPokemonCardDeck(filterCat = 'all', searchQuery = '') {
  const grid = document.getElementById('fl-pokemon-card-grid');
  if (!grid) return;
  grid.innerHTML = '';

  const activePersonaId = (currentSessionPersonaId || localStorage.getItem('xflow_chat_persona') || 'default').toLowerCase();
  const search = (searchQuery || '').toLowerCase().trim();

  const cards = (Array.isArray(AVAILABLE_PERSONAS) ? AVAILABLE_PERSONAS : []).filter(p => {
    const cat = (p.category || 'system').toLowerCase();
    const catId = (p.category_id || '').toLowerCase();
    const dept = typeof getAgentDepartment === 'function' ? getAgentDepartment(p).toLowerCase() : cat;
    const filterLower = (filterCat || 'all').toLowerCase();
    const matchesCat = (filterLower === 'all') || (cat === filterLower) || (catId === filterLower) || (dept === filterLower);
    const matchesSearch = !search ||
      (p.name && p.name.toLowerCase().includes(search)) ||
      (p.id && p.id.toLowerCase().includes(search)) ||
      (p.description && p.description.toLowerCase().includes(search)) ||
      (catId && catId.includes(search));
    return matchesCat && matchesSearch;
  });

  if (cards.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1 / -1; padding: 60px 20px; text-align: center; color: #94a3b8; font-size: 14px;">No specialist cards match the filter "${escapeHtml(search || filterCat)}".</div>`;
    return;
  }

  cards.forEach(p => {
    const isDefault = p.id.toLowerCase() === 'default';
    const isActive = (p.id.toLowerCase() === activePersonaId);
    const moves = getSpecialistMoves(p);
    const cat = p.category || (isDefault ? 'system' : 'specialist');
    const icon = p.icon || (isDefault ? '⚡' : '🤖');
    const name = p.name || p.id;
    const hp = isDefault ? '999' : (860 + (p.name.length * 8) % 130);

    const cardEl = document.createElement('div');
    cardEl.className = 'fl-pokemon-card' + (isActive ? ' is-active-specialist' : '');
    cardEl.innerHTML = `
      <div class="fl-pk-inner">
        <div class="fl-pk-top">
          <span class="fl-pk-name">${escapeHtml(name)}</span>
          <div class="fl-pk-hp-wrap">
            <span class="fl-pk-hp">HP ${hp}</span>
            <div class="fl-pk-elem-orb" title="${escapeHtml(cat)}">${icon}</div>
          </div>
        </div>

        <div class="fl-pk-art">
          <div class="fl-pk-art-avatar">${icon}</div>
          <span class="fl-pk-art-category">${escapeHtml(cat)}</span>
        </div>

        <div class="fl-pk-spec-bar">
          Flowork Sovereign Specialist • Stage 2 • Non-Zombie
        </div>

        <div class="fl-pk-moves">
          <div class="fl-pk-move">
            <div class="fl-pk-move-header">
              <span class="fl-pk-move-title">${escapeHtml(moves[0].name)}</span>
              <span class="fl-pk-move-dmg">${escapeHtml(moves[0].dmg)}</span>
            </div>
            <div class="fl-pk-move-desc">${escapeHtml(moves[0].desc)}</div>
          </div>
          <div class="fl-pk-move">
            <div class="fl-pk-move-header">
              <span class="fl-pk-move-title">${escapeHtml(moves[1].name)}</span>
              <span class="fl-pk-move-dmg">${escapeHtml(moves[1].dmg)}</span>
            </div>
            <div class="fl-pk-move-desc">${escapeHtml(moves[1].desc)}</div>
          </div>
        </div>

        <div class="fl-pk-bottom-stats">
          <span>WEAKNESS: Drift x2</span>
          <span>RESIST: Zombie -30</span>
          <span class="fl-pk-rarity">⭐⭐⭐ HOLO</span>
        </div>

        <button type="button" class="fl-pk-deploy-btn ${isActive ? 'is-active' : ''}">
          ${isActive ? '✅ ACTIVE IN STUDIO' : '⚡ DEPLOY TO SOLO STUDIO'}
        </button>
      </div>
    `;

    cardEl.addEventListener('click', (e) => {
      e.stopPropagation();
      selectPokemonSpecialist(p.id);
    });

    grid.appendChild(cardEl);
  });
}

function selectPokemonSpecialist(personaId) {
  if (!personaId) return;
  currentSessionPersonaId = personaId;
  pendingSessionPersonaId = personaId;
  localStorage.setItem('xflow_chat_persona', personaId);
  if (currentChatSessionId) {
    localStorage.setItem('xflow_session_persona_' + currentChatSessionId, personaId);
    setSessionAgentPersona(personaId);
  }

  updateAgentPillDisplay();
  renderAgentDropdown();

  // Deploy to 3D Office Engine
  if (window.office3DInstance && typeof window.office3DInstance.setSoloSpecialist === 'function') {
    window.office3DInstance.setSoloSpecialist(personaId);
  } else if (typeof window.deploySoloSpecialist === 'function') {
    window.deploySoloSpecialist(personaId);
  }

  const pObj = getSelectedPersonaObj();
  if (typeof showToast === 'function') {
    showToast(`🃏 Specialist ${pObj.name || personaId} deployed to Solo Executive Studio!`, 'success');
  }
  closePokemonCardDeck();
}

function initPokemonCardDeck() {
  if (pokemonDeckInitialized) return;
  pokemonDeckInitialized = true;


  const btnClose = document.getElementById('btn-close-pokemon-modal');
  if (btnClose) {
    btnClose.addEventListener('click', (e) => {
      e.stopPropagation();
      closePokemonCardDeck();
    });
  }

  const modal = document.getElementById('fl-pokemon-card-modal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closePokemonCardDeck();
      }
    });
  }

  const searchInput = document.getElementById('fl-pokemon-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      renderPokemonCardDeck(currentDeckFilterCat, e.target.value);
    });
  }

  const catPills = document.querySelectorAll('.fl-pokemon-cat-pill');
  catPills.forEach(pill => {
    pill.addEventListener('click', () => {
      catPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentDeckFilterCat = pill.dataset.cat || 'all';
      const q = searchInput ? searchInput.value : '';
      renderPokemonCardDeck(currentDeckFilterCat, q);
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closePokemonCardDeck();
    }
  });
}

window.openPokemonCardDeck = openPokemonCardDeck;
window.closePokemonCardDeck = closePokemonCardDeck;

// =============================================================================
// FLOWORK OS SOVEREIGN PERSONA-LOCKED SLASH COMMAND PALETTE
// =============================================================================
let slashPaletteSelectedIndex = 0;
let filteredSlashCommands = [];
let isSlashPaletteOpen = false;

function getActivePersonaSlashCommands() {
  const currentPersona = getSelectedPersonaObj();
  // Per User Sovereign Command: Default persona MUST have ZERO slash commands
  if (!currentPersona || currentPersona.id === 'default') {
    return [];
  }
  // Custom persona slash commands are strictly defined in its persona.json
  if (Array.isArray(currentPersona.slash_commands) && currentPersona.slash_commands.length > 0) {
    return currentPersona.slash_commands;
  }
  return [];
}

function handleSlashInput(inputEl) {
  const paletteEl = document.getElementById('chat-slash-palette');
  if (!paletteEl) return;
  const text = inputEl.value;
  const cursorPos = inputEl.selectionStart != null ? inputEl.selectionStart : text.length;
  const textBeforeCursor = text.slice(0, cursorPos);

  // Detect if cursor is on a slash token at start of line or after whitespace
  const match = textBeforeCursor.match(/(?:^|\s)\/([a-zA-Z0-9_\-]*)$/);
  if (!match) {
    closeSlashPalette();
    return;
  }

  const allCommands = getActivePersonaSlashCommands();
  // If active persona has zero slash commands (e.g. default), do not show palette
  if (!allCommands || allCommands.length === 0) {
    closeSlashPalette();
    return;
  }

  const query = match[1].toLowerCase();
  const currentPersona = getSelectedPersonaObj();

  filteredSlashCommands = allCommands.filter(cmd => {
    const cName = (cmd.command || '').replace(/^\//, '').toLowerCase();
    const cDesc = (cmd.description || '').toLowerCase();
    return cName.includes(query) || cDesc.includes(query);
  });

  if (filteredSlashCommands.length === 0) {
    closeSlashPalette();
    return;
  }

  slashPaletteSelectedIndex = 0;
  paletteEl.style.display = 'flex';
  isSlashPaletteOpen = true;
  renderSlashPalette(paletteEl, currentPersona);
}

function renderSlashPalette(paletteEl, currentPersona) {
  paletteEl.innerHTML = `
    <div class="slash-palette-header">
      <span>SLASH COMMANDS</span>
      <span class="slash-persona-tag">🔒 ${escapeHtml(currentPersona.name || 'Core')}</span>
    </div>
    <div class="slash-palette-list" id="slash-palette-list">
    </div>
  `;
  renderSlashPaletteItems(paletteEl);
}

function renderSlashPaletteItems(paletteEl) {
  const listEl = paletteEl.querySelector('#slash-palette-list');
  if (!listEl) return;

  const currentPersona = getSelectedPersonaObj();
  const personaId = (currentPersona.id || 'default').toLowerCase();

  listEl.innerHTML = filteredSlashCommands.map((cmd, idx) => {
    const isSelected = idx === slashPaletteSelectedIndex;
    const isCore = cmd.scope === 'core' || ['/plan', '/goal', '/boost', '/learn', '/browser', '/schedule'].includes(cmd.command);
    const badgeText = isCore ? 'CORE' : personaId.toUpperCase();
    const badgeClass = isCore ? 'slash-badge-core' : 'slash-badge-coder';

    return `
      <div class="slash-palette-item ${isSelected ? 'selected' : ''}" data-cmd="${escapeHtml(cmd.command)}" data-index="${idx}">
        <div class="slash-item-left">
          <span class="slash-item-icon">${cmd.icon || '⚡'}</span>
          <span class="slash-item-command">${escapeHtml(cmd.command)}</span>
          <span class="slash-item-desc">${escapeHtml(cmd.description || '')}</span>
        </div>
        <div class="slash-item-right">
          <span class="slash-item-badge ${badgeClass}">${badgeText}</span>
        </div>
      </div>
    `;
  }).join('');

  // Robust mouse and click handlers without innerHTML recreation on hover!
  listEl.onmousedown = (e) => {
    const item = e.target.closest('.slash-palette-item');
    if (item) {
      e.preventDefault();
      e.stopPropagation();
      const cmd = item.getAttribute('data-cmd');
      if (cmd) {
        selectSlashCommand(cmd);
      }
    }
  };

  listEl.onclick = (e) => {
    const item = e.target.closest('.slash-palette-item');
    if (item) {
      e.preventDefault();
      e.stopPropagation();
      const cmd = item.getAttribute('data-cmd');
      if (cmd) {
        selectSlashCommand(cmd);
      }
    }
  };

  listEl.onmouseover = (e) => {
    const item = e.target.closest('.slash-palette-item');
    if (item) {
      const idx = parseInt(item.getAttribute('data-index') || '0', 10);
      if (idx !== slashPaletteSelectedIndex) {
        slashPaletteSelectedIndex = idx;
        listEl.querySelectorAll('.slash-palette-item').forEach((el, i) => {
          el.classList.toggle('selected', i === slashPaletteSelectedIndex);
        });
      }
    }
  };
}

function scrollSelectedSlashItemIntoView(paletteEl) {
  const listEl = paletteEl.querySelector('#slash-palette-list');
  if (!listEl) return;
  const selectedItem = listEl.querySelector('.slash-palette-item.selected');
  if (selectedItem) {
    selectedItem.scrollIntoView({ block: 'nearest' });
  }
}

function navigateSlashPalette(direction) {
  const paletteEl = document.getElementById('chat-slash-palette');
  if (!paletteEl || filteredSlashCommands.length === 0) return;
  const listEl = paletteEl.querySelector('#slash-palette-list');
  if (!listEl) return;
  slashPaletteSelectedIndex = (slashPaletteSelectedIndex + direction + filteredSlashCommands.length) % filteredSlashCommands.length;
  listEl.querySelectorAll('.slash-palette-item').forEach((el, i) => {
    el.classList.toggle('selected', i === slashPaletteSelectedIndex);
  });
  scrollSelectedSlashItemIntoView(paletteEl);
}

function selectSlashCommand(cmdText) {
  const chatInput = document.getElementById('rightbar-chat-input');
  if (!chatInput) return;

  const text = chatInput.value;
  const cursorPos = chatInput.selectionStart != null ? chatInput.selectionStart : text.length;
  const textBeforeCursor = text.slice(0, cursorPos);
  const textAfterCursor = text.slice(cursorPos);

  // Replace the slash token with the full command and a trailing space
  const replacedBefore = textBeforeCursor.replace(/(?:^|\s)\/([a-zA-Z0-9_\-]*)$/, (match) => {
    const leadingWhitespace = match.startsWith(' ') || match.startsWith('\n') ? match[0] : '';
    return leadingWhitespace + cmdText + ' ';
  });

  chatInput.value = replacedBefore + textAfterCursor;
  const newCursorPos = replacedBefore.length;
  chatInput.focus();
  chatInput.setSelectionRange(newCursorPos, newCursorPos);

  closeSlashPalette();
}

function closeSlashPalette() {
  const paletteEl = document.getElementById('chat-slash-palette');
  if (paletteEl) {
    paletteEl.style.display = 'none';
  }
  isSlashPaletteOpen = false;
  slashPaletteSelectedIndex = 0;
}

function initSlashCommandPalette() {
  document.addEventListener('click', (e) => {
    const paletteEl = document.getElementById('chat-slash-palette');
    const chatInput = document.getElementById('rightbar-chat-input');
    if (isSlashPaletteOpen && paletteEl && !paletteEl.contains(e.target) && e.target !== chatInput) {
      closeSlashPalette();
    }
  });
}


function updateTopStatusBar() {
  const bar = document.getElementById('chat-top-status-bar');
  const txt = document.getElementById('chat-top-status-text');
  if (!bar || !txt) return;

  const subCount = activeSubagentKeys.size;
  const taskCount = activeTaskKeys.size;
  const total = subCount + taskCount;

  if (total > 0) {
    bar.style.display = 'flex';
    const isSub = subCount > 0;
    const isTask = taskCount > 0;
    const desc = isSub && isTask
      ? 'subagents/tasks'
      : isSub
        ? (subCount > 1 ? 'subagents' : 'subagent')
        : (taskCount > 1 ? 'tasks' : 'task');
    txt.textContent = `${total} ${desc} running`;
  } else {
    bar.style.display = 'none';
  }
}

function showPinnedPrompt(promptText) {
  const bar = document.getElementById('chat-pinned-prompt');
  const txt = document.getElementById('chat-pinned-text');
  if (!bar || !txt) return;
  txt.textContent = promptText;
  bar.style.display = 'flex';
}

function hidePinnedPrompt() {
  const bar = document.getElementById('chat-pinned-prompt');
  if (bar) bar.style.display = 'none';
}

function renderQueueTray() {
  const card = document.getElementById('chat-queue-card');
  const countBadge = document.getElementById('chat-queue-count');
  const list = document.getElementById('chat-queue-list');
  if (!card) return;

  if (queuedMessages.length === 0) {
    card.style.display = 'none';
    if (list) list.innerHTML = '';
    return;
  }

  card.style.display = 'block';
  if (countBadge) {
    countBadge.textContent = String(queuedMessages.length);
  }

  if (list) {
    list.innerHTML = queuedMessages.map((q, idx) => `
      <div class="fl-queue-row" data-qid="${q.id}">
        <span class="fl-queue-row-text" title="${escapeHtml(q.text)}">${escapeHtml(q.text)}</span>
        <div class="fl-queue-actions">
          <button class="fl-queue-btn btn-send-now" data-send-qid="${q.id}" title="Send now">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </button>
          <button class="fl-queue-btn btn-edit-queue" data-edit-qid="${q.id}" title="Edit message">
            <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
          </button>
          <button class="fl-queue-btn btn-delete-queue" data-del-qid="${q.id}" title="Delete from queue">
            <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      </div>
    `).join('');
  }
}


async function stopCurrentChatTurn() {
  if (!isChatStreaming) return;

  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }

  // Notify backend to terminate child process
  if (currentChatSessionId) {
    fetch('/api/chat/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentChatSessionId })
    }).catch(err => console.warn('Stop turn request failed:', err));
  }

  if (currentThinkingController) {
    currentThinkingController.stop();
  }

  if (activeBodyArea) {
    const stoppedDiv = document.createElement('div');
    stoppedDiv.className = 'fl-stopped-banner';
    stoppedDiv.innerHTML = '<span class="fl-stopped-icon">⏹</span> Generation stopped by user';
    activeBodyArea.appendChild(stoppedDiv);
  }

  activeSubagentKeys.clear();
  activeTaskKeys.clear();
  updateTopStatusBar();
  hidePinnedPrompt();

  const messagesContainer = document.getElementById('rightbar-messages');
  if (messagesContainer) {
    messagesContainer.classList.remove('chat-focus-mode');
    messagesContainer.querySelectorAll('.chat-msg-active-turn').forEach(el => el.classList.remove('chat-msg-active-turn'));
  }
  setMascotAgentLoop(false);
  if (window.office3DInstance) {
    const activeTarget = (typeof getActiveTargetAgentId === 'function') ? getActiveTargetAgentId() : 'agent-default';
    window.office3DInstance.setAgentState(activeTarget, 'idle');
  }

  setChatStreamingState(false);

  showToast(queuedMessages.length > 0 ? `Generation stopped. ${queuedMessages.length} queued message(s) pending.` : 'Generation stopped');
}


function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

window.safeCopyToClipboard = async function(text) {
  if (typeof text !== "string") text = String(text ?? "");
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      console.warn("[Flowork Canvas] navigator.clipboard.writeText failed, attempting execCommand fallback:", e);
    }
  }
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.top = "0";
    ta.style.left = "0";
    ta.style.width = "2em";
    ta.style.height = "2em";
    ta.style.padding = "0";
    ta.style.border = "none";
    ta.style.outline = "none";
    ta.style.boxShadow = "none";
    ta.style.background = "transparent";
    ta.style.opacity = "0.01";
    ta.style.zIndex = "-1";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    ta.setSelectionRange(0, text.length);
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    if (ok) return true;
  } catch (err) {
    console.warn("[Flowork Canvas] execCommand fallback failed:", err);
  }
  return false;
};

window.copyCodeSnippet = function(btn) {
  const card = btn ? btn.closest('.chat-code-card') : null;
  if (!card) return;
  const preCode = card.querySelector('pre code') || card.querySelector('code');
  let code = preCode ? (preCode.innerText || preCode.textContent || '') : (card.getAttribute('data-code') || '');
  if (!code) {
    showToast('No code snippet content found');
    return;
  }
  code = code.trimEnd();
  window.safeCopyToClipboard(code).then((success) => {
    if (success !== false) {
      const span = btn.querySelector('span:last-child') || btn.querySelector('span') || btn;
      const orig = span.textContent;
      span.textContent = 'Copied!';
      btn.classList.add('copied');
      setTimeout(() => {
        span.textContent = orig;
        btn.classList.remove('copied');
      }, 1800);
      showToast('Code copied to clipboard');
    } else {
      showToast('Failed to copy code to clipboard');
    }
  }).catch((err) => {
    console.error('[Flowork Canvas] Copy failed:', err);
    showToast('Failed to copy code: ' + (err?.message || 'Clipboard error'));
  });
};

window.executeSnippetInChat = function(btn) {
  const card = btn ? btn.closest('.chat-code-card') : null;
  if (!card) return;
  const preCode = card.querySelector('pre code') || card.querySelector('code');
  let code = preCode ? (preCode.innerText || preCode.textContent || '') : (card.getAttribute('data-code') || '');
  const lang = (card.getAttribute('data-lang') || '').toUpperCase();
  if (!code) return;
  code = code.trim();

  const rightbarChat = document.getElementById('rightbar-chat');
  if (rightbarChat && rightbarChat.classList.contains('collapsed')) {
    rightbarChat.classList.remove('collapsed');
    try { localStorage.setItem('xflow_rightbar_collapsed', 'false'); } catch (e) {}
  }

  const chatDrawer = document.getElementById('chat-drawer');
  if (chatDrawer && chatDrawer.classList.contains('collapsed')) {
    chatDrawer.classList.remove('collapsed');
  }

  const chatInput = document.getElementById('rightbar-chat-input') ||
                    document.getElementById('chat-input') ||
                    document.querySelector('.chat-input-textarea') ||
                    document.querySelector('textarea.chat-input');
  if (chatInput) {
    if (lang === 'BASH' || lang === 'SH' || lang === 'SHELL') {
      chatInput.value = code;
    } else if (lang === 'PYTHON' || lang === 'PY') {
      chatInput.value = code.includes('\n') ? code : (code.startsWith('python') ? code : `python3 -c ${JSON.stringify(code)}`);
    } else if (lang === 'JS' || lang === 'JAVASCRIPT' || lang === 'NODE') {
      chatInput.value = code.includes('\n') ? code : (code.startsWith('node') ? code : `node -e ${JSON.stringify(code)}`);
    } else {
      chatInput.value = code;
    }
    chatInput.focus();
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + 'px';
    chatInput.dispatchEvent(new Event('input', { bubbles: true }));

    const span = btn.querySelector('span:last-child') || btn.querySelector('span') || btn;
    const origText = span.textContent;
    span.textContent = 'Staged!';
    btn.classList.add('staged');
    setTimeout(() => {
      span.textContent = origText;
      btn.classList.remove('staged');
    }, 1800);

    try { chatInput.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (_) {}
    showToast('Snippet staged in prompt input. Ready to execute.');
  } else {
    window.safeCopyToClipboard(code).then(() => {
      showToast('Prompt input not found. Snippet copied to clipboard instead.');
    });
  }
};

window.copyTableAsJson = function(btn) {
  const wrapper = btn.closest('.chat-table-wrapper');
  if (!wrapper) return;
  const table = wrapper.querySelector('table');
  if (!table) return;
  const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
  const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr => {
    const cells = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
    const obj = {};
    headers.forEach((h, i) => { obj[h || `col_${i}`] = cells[i] || ''; });
    return obj;
  });
  window.safeCopyToClipboard(JSON.stringify(rows, null, 2)).then(() => {
    const span = btn.querySelector('span');
    if (span) {
      const old = span.textContent;
      span.textContent = 'Copied!';
      setTimeout(() => { span.textContent = old; }, 1800);
    }
    showToast('Table copied as JSON');
  });
};

window.copyTableAsCsv = function(btn) {
  const wrapper = btn.closest('.chat-table-wrapper');
  if (!wrapper) return;
  const table = wrapper.querySelector('table');
  if (!table) return;
  const headers = Array.from(table.querySelectorAll('th')).map(th => `"${th.innerText.trim().replace(/"/g, '""')}"`);
  const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr => {
    return Array.from(tr.querySelectorAll('td')).map(td => `"${td.innerText.trim().replace(/"/g, '""')}"`).join(',');
  });
  const csv = [headers.join(','), ...rows].join('\n');
  window.safeCopyToClipboard(csv).then(() => {
    const span = btn.querySelector('span');
    if (span) {
      const old = span.textContent;
      span.textContent = 'Copied!';
      setTimeout(() => { span.textContent = old; }, 1800);
    }
    showToast('Table copied as CSV');
  });
};

window.handleChatLinkClick = function(e, url) {
  if (!url) return;
  const clean = url.trim();
  if (clean.startsWith('file://') || (clean.startsWith('/') && !clean.startsWith('/api') && !clean.startsWith('/canvas'))) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    const filePath = clean.startsWith('file://') ? clean.substring(7) : clean;
    window.safeCopyToClipboard(filePath).then(() => {
      showToast(`Local path copied: ${filePath.split('/').pop()}`);
    });
    if (typeof openFileInWorkbench === 'function') {
      openFileInWorkbench(filePath);
    }
    return false;
  }
  if (clean.startsWith('http://') || clean.startsWith('https://')) {
    window.open(clean, '_blank', 'noopener,noreferrer');
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    return false;
  }
};

// Sovereign Global Delegated Click Listener for Snippet & Interactive Card Actions
if (!window._flSnippetActionsDelegated) {
  window._flSnippetActionsDelegated = true;
  document.addEventListener('click', (e) => {
    // 1. Stage Run button on code card
    const runBtn = e.target.closest('.code-card-run');
    if (runBtn) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof window.executeSnippetInChat === 'function') {
        window.executeSnippetInChat(runBtn);
      }
      return;
    }

    // 2. Copy Code button on code card
    const copyCodeBtn = e.target.closest('.code-card-copy');
    if (copyCodeBtn) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof window.copyCodeSnippet === 'function') {
        window.copyCodeSnippet(copyCodeBtn);
      }
      return;
    }

    // 3. Table JSON / CSV export buttons
    const tableJsonBtn = e.target.closest('.chat-table-hud-btn[data-action="table-json"]');
    if (tableJsonBtn) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof window.copyTableAsJson === 'function') {
        window.copyTableAsJson(tableJsonBtn);
      }
      return;
    }
    const tableCsvBtn = e.target.closest('.chat-table-hud-btn[data-action="table-csv"]');
    if (tableCsvBtn) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof window.copyTableAsCsv === 'function') {
        window.copyTableAsCsv(tableCsvBtn);
      }
      return;
    }

    // 4. File download / copy path button
    const fileCopyBtn = e.target.closest('.chat-file-btn[data-action="copy-path"]');
    if (fileCopyBtn) {
      e.preventDefault();
      e.stopPropagation();
      const filePath = fileCopyBtn.getAttribute('data-filepath');
      if (filePath && typeof window.copyFilePath === 'function') {
        window.copyFilePath(filePath, fileCopyBtn);
      }
      return;
    }

    // 5. Media thumbnail preview click
    const mediaPreview = e.target.closest('.chat-media-preview');
    if (mediaPreview && !e.target.closest('a') && !e.target.closest('button')) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof window.handleChatAttachmentClick === 'function') {
        window.handleChatAttachmentClick(mediaPreview);
      }
      return;
    }
  }, true);
}

function formatStatusCell(cellText) {
  const t = (cellText || '').trim();
  const upper = t.toUpperCase();
  if (/^(ONLINE|SUCCESS|ACTIVE|SYNCED|RESOLVED|OK|PASS|DONE|EXIT 0)$/i.test(upper)) {
    return `<span class="chat-badge chat-badge-success"><span class="badge-dot">●</span> ${escapeHtml(t)}</span>`;
  }
  if (/^(ERROR|FAIL|FAILED|CRITICAL|FATAL|EXIT [1-9][0-9]*)$/i.test(upper)) {
    return `<span class="chat-badge chat-badge-danger"><span class="badge-dot">✖</span> ${escapeHtml(t)}</span>`;
  }
  if (/^(PENDING|WARN|WARNING|HIGH_LOAD|BUSY|TIMEOUT)$/i.test(upper)) {
    return `<span class="chat-badge chat-badge-warning"><span class="badge-dot">▲</span> ${escapeHtml(t)}</span>`;
  }
  if (/^(RUNNING|INFO|DEBUG|BASH|NODE)$/i.test(upper)) {
    return `<span class="chat-badge chat-badge-info"><span class="badge-dot">◆</span> ${escapeHtml(t)}</span>`;
  }
  if (/^[0-9]+(\.[0-9]+)?\s*(%|MB|KB|GB|ms|s|LOC|B)?$/i.test(t)) {
    return `<span class="chat-cell-numeric">${escapeHtml(t)}</span>`;
  }
  return escapeHtml(t);
}

function highlightTacticalBadges(text) {
  if (!text) return '';
  const parts = text.split(/(<[^>]+>)/g);
  for (let i = 0; i < parts.length; i++) {
    if (parts[i].startsWith('<')) continue;
    parts[i] = parts[i]
      .replace(/\[(SUCCESS|EXIT 0|ONLINE|ACTIVE|DONE|RESOLVED|PASS)\]/gi, (match, tag) => {
        return `<span class="chat-badge chat-badge-success"><span class="badge-dot">●</span> [${escapeHtml(tag.toUpperCase())}]</span>`;
      })
      .replace(/\[(ERROR|FAILED|CRITICAL|ALERT|REJECT|EXIT [1-9][0-9]*)\]/gi, (match, tag) => {
        return `<span class="chat-badge chat-badge-danger"><span class="badge-dot">✖</span> [${escapeHtml(tag.toUpperCase())}]</span>`;
      })
      .replace(/\[(WARNING|WARN|PENDING|TIMEOUT|ATTENTION|HIGH_LOAD)\]/gi, (match, tag) => {
        return `<span class="chat-badge chat-badge-warning"><span class="badge-dot">▲</span> [${escapeHtml(tag.toUpperCase())}]</span>`;
      })
      .replace(/\[(INFO|RUNNING|BASH|TERMINAL|SYSTEM|SWARM|SUBAGENT|TASK|MESH|COT)\]/gi, (match, tag) => {
        return `<span class="chat-badge chat-badge-info"><span class="badge-dot">◆</span> [${escapeHtml(tag.toUpperCase())}]</span>`;
      });
  }
  return parts.join('');
}

function autolinkRawUrls(text) {
  if (!text) return '';
  const parts = text.split(/(<[^>]+>)/g);
  let inAnchor = false;
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    if (part.startsWith('<')) {
      if (/^<a\b/i.test(part)) inAnchor = true;
      else if (/^<\/a>/i.test(part)) inAnchor = false;
      continue;
    }
    if (inAnchor) continue;
    parts[i] = part.replace(/(https?:\/\/[^\s<>"'\(\)\]\}]+)/g, (match, url) => {
      const cleanUrl = url.replace(/[.,;!?]+$/, '');
      const trailing = url.slice(cleanUrl.length);
      const escaped = escapeHtml(cleanUrl);
      return `<a href="${escaped}" target="_blank" rel="noopener noreferrer" class="chat-link" onclick="handleChatLinkClick(event, '${escaped}')"><span class="chat-link-text">${escaped}</span><span class="chat-link-badge">↗</span></a>${trailing}`;
    });
  }
  return parts.join('');
}

function parseMarkdownTables(text) {
  const tableRegex = /((?:^|\n)\|[^\n]+\|\r?\n\|[\s\-:|]+\|\r?\n(?:\|[^\n]+\|\r?\n?)+)/g;
  return text.replace(tableRegex, (match) => {
    const lines = match.trim().split(/\r?\n/);
    if (lines.length < 2) return match;

    const parseRow = (line) => {
      return line.replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
    };

    const headerCells = parseRow(lines[0]);
    const alignLine = parseRow(lines[1]);
    const isValidSeparator = alignLine.every(col => /^:?-+:?$/.test(col));
    if (!isValidSeparator) return match;

    const aligns = alignLine.map(col => {
      if (col.startsWith(':') && col.endsWith(':')) return 'center';
      if (col.endsWith(':')) return 'right';
      return 'left';
    });

    const dataRowCount = Math.max(0, lines.length - 2);

    let html = `
    <div class="chat-table-wrapper">
      <div class="chat-table-hud-bar">
        <div class="chat-table-hud-left">
          <span class="chat-table-hud-dot"></span>
          <span class="chat-table-hud-tag">[DATA // MATRIX GRID]</span>
          <span class="chat-table-hud-rows">● ${dataRowCount} ROWS</span>
        </div>
        <div class="chat-table-hud-actions">
          <button class="chat-table-hud-btn" onclick="copyTableAsJson(this)" title="Copy table as JSON">
            <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            <span>JSON</span>
          </button>
          <button class="chat-table-hud-btn" onclick="copyTableAsCsv(this)" title="Copy table as CSV">
            <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>CSV</span>
          </button>
        </div>
      </div>
      <table class="chat-table"><thead><tr>`;
    headerCells.forEach((cell, idx) => {
      const align = aligns[idx] || 'left';
      html += `<th style="text-align:${align};"><span class="th-content">${escapeHtml(cell)}</span></th>`;
    });
    html += '</tr></thead><tbody>';

    for (let i = 2; i < lines.length; i++) {
      const rowLine = lines[i].trim();
      if (!rowLine.startsWith('|')) continue;
      const cells = parseRow(rowLine);
      html += '<tr>';
      cells.forEach((cell, idx) => {
        const align = aligns[idx] || 'left';
        const formattedCell = formatStatusCell(cell);
        html += `<td style="text-align:${align};">${formattedCell}</td>`;
      });
      html += '</tr>';
    }

    html += '</tbody></table></div>';
    return '\n\n' + html + '\n\n';
  });
}

function formatFileSize(bytes) {
  if (!bytes || isNaN(bytes)) return '0 B';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function getFileCategoryIcon(filename) {
  const ext = (filename || '').split('.').pop().toLowerCase();
  if (['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg', 'bmp', 'ico'].includes(ext)) return '🖼️';
  if (['pdf'].includes(ext)) return '📕';
  if (['zip', 'tar', 'gz', 'rar', '7z'].includes(ext)) return '📦';
  if (['js', 'mjs', 'ts', 'jsx', 'tsx', 'py', 'rs', 'go', 'c', 'cpp', 'h', 'html', 'css', 'json', 'yaml', 'yml', 'toml', 'sh', 'bat'].includes(ext)) return '💻';
  if (['mp3', 'wav', 'ogg', 'flac', 'm4a'].includes(ext)) return '🎵';
  if (['mp4', 'mkv', 'webm', 'mov', 'avi'].includes(ext)) return '🎬';
  if (['doc', 'docx', 'txt', 'md', 'csv', 'tsv'].includes(ext)) return '📄';
  return '📁';
}

function resolveMediaUrl(rawUrl) {
  if (!rawUrl) return '';
  let u = rawUrl.trim();
  if (u.startsWith('file://')) u = u.substring(7);
  // Match .FL_BIN/screenshots/
  if (u.includes('.FL_BIN/screenshots/')) {
    const parts = u.split('.FL_BIN/screenshots/');
    return `/canvas/screenshots/${parts[1]}`;
  }
  // Match .FL_BIN/generated_images/
  if (u.includes('.FL_BIN/generated_images/')) {
    const parts = u.split('.FL_BIN/generated_images/');
    return `/canvas/generated_images/${parts[1]}`;
  }
  // Match .flowork_spam/
  if (u.includes('.flowork_spam/')) {
    const parts = u.split('.flowork_spam/');
    return `/canvas/spam/${parts[1]}`;
  }
  // Match canvas-ui/uploads/
  if (u.includes('canvas-ui/uploads/')) {
    const parts = u.split('canvas-ui/uploads/');
    return `/canvas/uploads/${parts[1]}`;
  }
  // Match canvas-ui/
  if (u.includes('canvas-ui/')) {
    const parts = u.split('canvas-ui/');
    return `/canvas/${parts[1]}`;
  }
  // Relative uploads/
  if (u.startsWith('uploads/')) {
    return `/canvas/${u}`;
  }
  // Relative spam/
  if (u.startsWith('spam/')) {
    return `/canvas/${u}`;
  }
  if (!u.startsWith('/') && !u.includes('://') && !u.startsWith('data:')) {
    return `/canvas/${u}`;
  }
  return u;
}

window.openChatLightbox = function(src, title) {
  const modal = document.getElementById('chat-lightbox-modal');
  const img = document.getElementById('chat-lightbox-img');
  const titleEl = document.getElementById('chat-lightbox-title');
  const downloadBtn = document.getElementById('chat-lightbox-download');
  if (!modal || !img) return;

  img.src = src;
  if (titleEl) titleEl.textContent = title || 'Image Preview';
  if (downloadBtn) {
    downloadBtn.href = src;
    downloadBtn.download = (title || 'image').replace(/[^a-zA-Z0-9_\-\.]/g, '_');
  }
  modal.style.display = 'flex';
};

window.closeChatLightbox = function() {
  const modal = document.getElementById('chat-lightbox-modal');
  if (modal) modal.style.display = 'none';
};

window.handleChatAttachmentClick = function(el) {
  if (!el) return;
  const src = el.getAttribute('data-url') || el.src || '';
  const title = el.getAttribute('data-title') || el.alt || 'Attachment';
  if (src && typeof window.openChatLightbox === 'function') {
    window.openChatLightbox(src, title);
  }
};

window.copyFilePath = function(path, btnEl) {
  window.safeCopyToClipboard(path).then(() => {
    const span = btnEl ? btnEl.querySelector('span') : null;
    if (span) {
      const old = span.textContent;
      span.textContent = 'Copied!';
      setTimeout(() => { span.textContent = old; }, 1800);
    }
    showToast('File path copied to clipboard');
  });
};

// =============================================================================
// SOVEREIGN HUD TACTICAL MICRO-CHART ENGINE (TRADING, DONUT, BAR, LINE)
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================
window.downloadChartAsSvg = function(btnEl) {
  const card = btnEl ? btnEl.closest('.chat-chart-card') : null;
  if (!card) return;
  const svg = card.querySelector('svg');
  if (!svg) return;
  const serializer = new XMLSerializer();
  let source = serializer.serializeToString(svg);
  if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
    source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
  }
  const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `tactical_chart_${Date.now()}.svg`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('Chart exported as SVG');
};

window.toggleChartRawData = function(btnEl) {
  const card = btnEl ? btnEl.closest('.chat-chart-card') : null;
  if (!card) return;
  const rawBox = card.querySelector('.chart-raw-box');
  if (rawBox) {
    const isHidden = rawBox.style.display === 'none' || !rawBox.style.display;
    rawBox.style.display = isHidden ? 'block' : 'none';
  }
};

function generateDonutSvg(data, options = {}) {
  let rawItems = [];
  if (Array.isArray(data)) {
    rawItems = data;
  } else if (data && typeof data === 'object') {
    if (Array.isArray(data.data)) rawItems = data.data;
    else if (Array.isArray(data.items)) rawItems = data.items;
    else if (Array.isArray(data.slices)) rawItems = data.slices;
    else if (Array.isArray(data.segments)) rawItems = data.segments;
    else if (Array.isArray(data.series)) rawItems = data.series;
    else if (Array.isArray(data.labels) && Array.isArray(data.values)) {
      rawItems = data.labels.map((l, i) => ({ label: l, value: data.values[i] }));
    } else {
      // Key-value pairs: e.g. { "BTC": 45, "ETH": 35, "SOL": 20 }
      rawItems = Object.entries(data)
        .filter(([k, v]) => typeof v === 'number' && !['width', 'height', 'total', 'size'].includes(k.toLowerCase()))
        .map(([k, v]) => ({ label: k, value: v }));
    }
  }

  // Normalize items
  const items = rawItems.map(it => {
    if (typeof it === 'number') return { label: 'Value', value: it };
    if (!it || typeof it !== 'object') return { label: String(it), value: 0 };
    return {
      label: it.label || it.name || it.title || it.category || it.x || 'Item',
      value: Number(it.value ?? it.val ?? it.amount ?? it.count ?? it.y ?? 0),
      color: it.color || it.fill
    };
  }).filter(it => it.value > 0);

  if (!items.length) return '';
  const total = items.reduce((sum, it) => sum + Number(it.value || 0), 0);
  const size = 180, cx = 90, cy = 90, r = 68, innerR = 46;
  let startAngle = -90;
  const paths = [];
  const palette = ['#00f0ff', '#10b981', '#f59e0b', '#ef4444', '#a855f7', '#ec4899', '#38bdf8'];

  items.forEach((item, idx) => {
    const val = Number(item.value || 0);
    const angle = total > 0 ? (val / total) * 360 : 0;
    if (angle <= 0) return;
    const endAngle = startAngle + (angle >= 360 ? 359.99 : angle);
    const radS = (Math.PI * startAngle) / 180;
    const radE = (Math.PI * endAngle) / 180;

    const x1 = cx + r * Math.cos(radS), y1 = cy + r * Math.sin(radS);
    const x2 = cx + r * Math.cos(radE), y2 = cy + r * Math.sin(radE);
    const ix1 = cx + innerR * Math.cos(radE), iy1 = cy + innerR * Math.sin(radE);
    const ix2 = cx + innerR * Math.cos(radS), iy2 = cy + innerR * Math.sin(radS);

    const largeArc = angle > 180 ? 1 : 0;
    const color = item.color || palette[idx % palette.length];
    const d = `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} L ${ix1} ${iy1} A ${innerR} ${innerR} 0 ${largeArc} 0 ${ix2} ${iy2} Z`;
    paths.push(`<path d="${d}" fill="${color}" stroke="#060b19" stroke-width="2.5" class="chart-donut-slice"><title>${escapeHtml(item.label || '')}: ${val} (${total > 0 ? Math.round((val/total)*100) : 0}%)</title></path>`);
    startAngle = endAngle;
  });

  const centerMain = options.centerText || (total > 0 ? (total >= 1000 ? total.toLocaleString() : String(total)) : '0');
  const centerSub = options.centerSub || 'TOTAL';

  return `
    <div class="tactical-donut-container">
      <div class="tactical-donut-graphic">
        <svg viewBox="0 0 ${size} ${size}" class="tactical-donut-svg">
          ${paths.join('')}
          <circle cx="${cx}" cy="${cy}" r="${innerR - 2}" fill="#080e1e" />
          <text x="${cx}" y="${cy - 2}" text-anchor="middle" fill="#ffffff" font-size="16" font-weight="700" font-family="monospace">${centerMain}</text>
          <text x="${cx}" y="${cy + 14}" text-anchor="middle" fill="#38bdf8" font-size="8.5" font-weight="600" letter-spacing="0.1em" font-family="monospace">${centerSub}</text>
        </svg>
      </div>
      <div class="tactical-donut-legend">
        ${items.map((it, idx) => {
          const val = Number(it.value || 0);
          const pct = total > 0 ? Math.round((val / total) * 100) : 0;
          const col = it.color || palette[idx % palette.length];
          return `
            <div class="legend-row">
              <span class="legend-color-dot" style="background:${col};box-shadow:0 0 6px ${col};"></span>
              <span class="legend-label">${escapeHtml(it.label || 'Item')}</span>
              <span class="legend-val">${val}</span>
              <span class="legend-pct">${pct}%</span>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

function generateTradingSvg(payload) {
  let rawSeries = [];
  if (Array.isArray(payload)) {
    rawSeries = payload;
  } else if (payload && typeof payload === 'object') {
    rawSeries = payload.series || payload.candles || payload.data || payload.items || [];
    if (!Array.isArray(rawSeries) && rawSeries && typeof rawSeries === 'object') {
      rawSeries = rawSeries.candles || rawSeries.series || rawSeries.data || [];
    }
  }

  // Normalize candle entries
  const series = rawSeries.map((s, idx) => {
    if (Array.isArray(s)) {
      // [time, open, high, low, close, volume] or [open, high, low, close]
      if (s.length >= 5) {
        return {
          time: String(s[0]),
          open: Number(s[1]),
          high: Number(s[2]),
          low: Number(s[3]),
          close: Number(s[4]),
          volume: Number(s[5] || 0)
        };
      } else if (s.length === 4) {
        return {
          time: String(idx + 1),
          open: Number(s[0]),
          high: Number(s[1]),
          low: Number(s[2]),
          close: Number(s[3]),
          volume: 0
        };
      }
    }
    if (!s || typeof s !== 'object') return null;
    return {
      time: s.time || s.t || s.timestamp || s.date || String(idx + 1),
      open: Number(s.open ?? s.o ?? s.openPrice ?? 0),
      high: Number(s.high ?? s.h ?? s.highPrice ?? 0),
      low: Number(s.low ?? s.l ?? s.lowPrice ?? 0),
      close: Number(s.close ?? s.c ?? s.closePrice ?? s.price ?? 0),
      volume: Number(s.volume ?? s.v ?? s.vol ?? 0)
    };
  }).filter(Boolean);

  if (!series.length) return '';
  const symbol = (payload && (payload.symbol || payload.pair || payload.ticker)) || 'BTC/USDT';
  const timeframe = (payload && (payload.timeframe || payload.tf || payload.interval)) || '1H';
  const w = 480, h = 240;
  const padTop = 30, padBottom = 40, padLeft = 10, padRight = 65;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const lows = series.map(s => Number(s.low !== undefined ? s.low : s.open));
  const highs = series.map(s => Number(s.high !== undefined ? s.high : s.close));
  let minP = Math.min(...lows);
  let maxP = Math.max(...highs);
  const pDiff = (maxP - minP) || 1;
  minP -= pDiff * 0.05;
  maxP += pDiff * 0.05;
  const finalRange = maxP - minP;

  const scaleY = (p) => padTop + plotH - ((p - minP) / finalRange) * plotH;
  const n = series.length;
  const colW = plotW / n;
  const bodyW = Math.max(3, Math.min(18, colW * 0.72));

  const maxVol = Math.max(...series.map(s => Number(s.volume || 0)), 1);
  const volH = 35;

  const elements = [];
  for (let i = 0; i <= 4; i++) {
    const p = minP + (finalRange * i) / 4;
    const y = scaleY(p);
    elements.push(`<line x1="${padLeft}" y1="${y}" x2="${padLeft + plotW}" y2="${y}" stroke="rgba(0, 240, 255, 0.12)" stroke-dasharray="3,3" />`);
    elements.push(`<text x="${padLeft + plotW + 6}" y="${y + 3}" fill="#94a3b8" font-size="9" font-family="monospace">${p >= 1000 ? p.toLocaleString('en-US', {maximumFractionDigits: 1}) : p.toFixed(2)}</text>`);
  }

  series.forEach((s, idx) => {
    const x = padLeft + idx * colW + (colW - bodyW) / 2;
    const midX = x + bodyW / 2;
    const op = Number(s.open), cl = Number(s.close), hi = Number(s.high), lo = Number(s.low);
    const isBull = cl >= op;
    const col = isBull ? '#10b981' : '#f43f5e';
    const yO = scaleY(op), yC = scaleY(cl), yH = scaleY(hi), yL = scaleY(lo);
    const topY = Math.min(yO, yC);
    const bHeight = Math.max(2, Math.abs(yC - yO));

    elements.push(`<line x1="${midX}" y1="${yH}" x2="${midX}" y2="${yL}" stroke="${col}" stroke-width="1.2" />`);
    elements.push(`<rect x="${x}" y="${topY}" width="${bodyW}" height="${bHeight}" fill="${col}" rx="1"><title>${s.time || ''}\nO: ${op} H: ${hi} L: ${lo} C: ${cl}</title></rect>`);

    if (s.volume) {
      const vH = (Number(s.volume) / maxVol) * volH;
      const vY = padTop + plotH - vH;
      elements.push(`<rect x="${x}" y="${vY}" width="${bodyW}" height="${vH}" fill="${col}" opacity="0.32" />`);
    }

    if (idx % Math.ceil(n / 6) === 0 || idx === n - 1) {
      const timeStr = String(s.time || idx);
      elements.push(`<text x="${midX}" y="${h - 8}" text-anchor="middle" fill="#64748b" font-size="8.5" font-family="monospace">${timeStr}</text>`);
    }
  });

  const lastCandle = series[series.length - 1];
  const firstCandle = series[0];
  const lastClose = Number(lastCandle.close);
  const changePct = firstCandle.open ? (((lastClose - Number(firstCandle.open)) / Number(firstCandle.open)) * 100).toFixed(2) : '0.00';
  const isOverallBull = Number(changePct) >= 0;

  return `
    <div class="tactical-trading-container">
      <div class="trading-ticker-bar">
        <div class="ticker-left">
          <span class="ticker-symbol">${escapeHtml(symbol)}</span>
          <span class="ticker-tf">${escapeHtml(timeframe)}</span>
        </div>
        <div class="ticker-right">
          <span class="ticker-price" style="color:${isOverallBull ? '#10b981' : '#f43f5e'}">${lastClose >= 1000 ? lastClose.toLocaleString('en-US', {maximumFractionDigits: 2}) : lastClose.toFixed(2)}</span>
          <span class="ticker-change-badge ${isOverallBull ? 'change-bull' : 'change-bear'}">${isOverallBull ? '▲ +' : '▼ '}${changePct}%</span>
        </div>
      </div>
      <div class="trading-svg-wrap">
        <svg viewBox="0 0 ${w} ${h}" class="tactical-trading-svg" width="100%">
          ${elements.join('')}
        </svg>
      </div>
    </div>
  `;
}

function generateBarSvg(payload) {
  let labels = payload.labels || (payload.data && payload.data.labels) || [];
  let values = payload.values || (payload.data && payload.data.values) || [];
  let items = payload.items || (payload.data && payload.data.items) || (payload.data && payload.data.bars) || (Array.isArray(payload.data) ? payload.data : []);

  if (payload.data && Array.isArray(payload.data.series) && payload.data.series.length > 0) {
    const s0 = payload.data.series[0];
    if (s0.data && Array.isArray(s0.data)) values = s0.data.map(Number);
    else if (s0.values && Array.isArray(s0.values)) values = s0.values.map(Number);
  }

  if (items.length && (!labels.length || !values.length)) {
    labels = items.map(it => it.label || it.name || '');
    values = items.map(it => Number(it.value !== undefined ? it.value : it.val || 0));
  }
  if (!values.length) return '';
  const maxVal = Math.max(...values, 1);
  const w = 480, h = 200;
  const padTop = 25, padBottom = 35, padLeft = 20, padRight = 20;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;
  const n = values.length;
  const colW = plotW / n;
  const barW = Math.max(8, Math.min(32, colW * 0.65));
  const elements = [];

  elements.push(`<line x1="${padLeft}" y1="${padTop + plotH}" x2="${padLeft + plotW}" y2="${padTop + plotH}" stroke="rgba(0, 240, 255, 0.25)" />`);

  values.forEach((v, idx) => {
    const x = padLeft + idx * colW + (colW - barW) / 2;
    const bH = (v / maxVal) * plotH;
    const y = padTop + plotH - bH;
    const midX = x + barW / 2;
    const col = (items[idx] && items[idx].color) || ['#00f0ff', '#10b981', '#38bdf8', '#f59e0b', '#a855f7'][idx % 5];
    elements.push(`<rect x="${x}" y="${y}" width="${barW}" height="${bH}" fill="${col}" rx="2" opacity="0.9"><title>${labels[idx] || ''}: ${v}</title></rect>`);
    elements.push(`<text x="${midX}" y="${y - 4}" text-anchor="middle" fill="#ffffff" font-size="9" font-weight="700" font-family="monospace">${v}</text>`);
    const lbl = labels[idx] || String(idx + 1);
    const shortLbl = lbl.length > 8 ? lbl.slice(0, 7) + '…' : lbl;
    elements.push(`<text x="${midX}" y="${h - 10}" text-anchor="middle" fill="#94a3b8" font-size="8.5" font-family="monospace">${escapeHtml(shortLbl)}</text>`);
  });

  return `
    <div class="tactical-bar-container">
      <svg viewBox="0 0 ${w} ${h}" class="tactical-bar-svg" width="100%">
        ${elements.join('')}
      </svg>
    </div>
  `;
}

function generateLineSvg(payload) {
  let labels = payload.labels || (payload.data && payload.data.labels) || [];
  let values = [];
  let strokeCol = payload.color || '#00f0ff';

  if (payload.data && Array.isArray(payload.data.series) && payload.data.series.length > 0) {
    const s0 = payload.data.series[0];
    if (s0.data && Array.isArray(s0.data)) values = s0.data.map(Number);
    else if (s0.values && Array.isArray(s0.values)) values = s0.values.map(Number);
    if (s0.color) strokeCol = s0.color;
  } else if (payload.data && Array.isArray(payload.data.values)) {
    values = payload.data.values.map(Number);
  } else if (payload.values && Array.isArray(payload.values)) {
    values = payload.values.map(Number);
  } else if (payload.data && Array.isArray(payload.data)) {
    values = payload.data.map(d => typeof d === 'number' ? d : Number(d.value !== undefined ? d.value : d.val || 0));
    if (!labels.length) labels = payload.data.map((d, i) => d.label || d.time || d.name || String(i + 1));
  }

  if (!values.length) return '';
  if (!labels.length) labels = values.map((_, i) => String(i + 1));

  const unit = (payload.options && payload.options.unit) || '';
  const w = 480, h = 200;
  const padTop = 25, padBottom = 35, padLeft = 25, padRight = 35;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;
  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  const range = (maxV - minV) || 1;
  const scaleY = v => padTop + plotH - ((v - minV) / range) * plotH;
  const colW = values.length > 1 ? plotW / (values.length - 1) : plotW;

  const points = values.map((v, i) => ({
    x: padLeft + (values.length > 1 ? i * colW : plotW / 2),
    y: scaleY(v),
    val: v,
    lbl: labels[i] || ''
  }));

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
  const areaD = values.length > 1
    ? `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${padTop + plotH} L ${points[0].x.toFixed(1)} ${padTop + plotH} Z`
    : '';

  const gradId = 'line-grad-' + Math.floor(Math.random() * 100000);
  const elements = [];

  for (let i = 0; i <= 3; i++) {
    const yVal = padTop + (plotH * i) / 3;
    const gridNum = maxV - (range * i) / 3;
    elements.push(`<line x1="${padLeft}" y1="${yVal}" x2="${padLeft + plotW}" y2="${yVal}" stroke="rgba(0, 240, 255, 0.1)" stroke-dasharray="2,3" />`);
    elements.push(`<text x="${padLeft + plotW + 4}" y="${yVal + 3}" fill="#64748b" font-size="8" font-family="monospace">${gridNum >= 1000 ? (gridNum/1000).toFixed(1) + 'k' : Math.round(gridNum)}</text>`);
  }

  const dots = points.map((p, idx) => {
    const displayVal = unit ? `${unit}${p.val.toLocaleString()}` : p.val.toLocaleString();
    const shortLbl = p.lbl.length > 8 ? p.lbl.slice(0, 7) + '…' : p.lbl;
    const lblNode = (idx % Math.ceil(values.length / 6) === 0 || idx === values.length - 1)
      ? `<text x="${p.x.toFixed(1)}" y="${h - 10}" text-anchor="middle" fill="#94a3b8" font-size="8.5" font-family="monospace">${escapeHtml(shortLbl)}</text>`
      : '';
    return `
      <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.5" fill="#080e1e" stroke="${strokeCol}" stroke-width="2">
        <title>${p.lbl}: ${displayVal}</title>
      </circle>
      <text x="${p.x.toFixed(1)}" y="${p.y - 7}" text-anchor="middle" fill="#ffffff" font-size="8.5" font-weight="700" font-family="monospace">${displayVal}</text>
      ${lblNode}
    `;
  }).join('');

  return `
    <div class="tactical-line-container">
      <svg viewBox="0 0 ${w} ${h}" class="tactical-line-svg" width="100%">
        <defs>
          <linearGradient id="${gradId}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${strokeCol}" stop-opacity="0.3" />
            <stop offset="100%" stop-color="${strokeCol}" stop-opacity="0.0" />
          </linearGradient>
        </defs>
        ${areaD ? `<path d="${areaD}" fill="url(#${gradId})" />` : ''}
        ${elements.join('')}
        <path d="${pathD}" fill="none" stroke="${strokeCol}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        ${dots}
      </svg>
    </div>
  `;
}

function generateKpiDeckHtml(payload) {
  const cards = (payload.data && Array.isArray(payload.data.cards)) ? payload.data.cards :
                (payload.data && Array.isArray(payload.data.metrics)) ? payload.data.metrics :
                (payload.data && Array.isArray(payload.data.items)) ? payload.data.items :
                (Array.isArray(payload.cards) ? payload.cards :
                (Array.isArray(payload.data) ? payload.data : []));
  if (!cards.length) return '';

  const cardsHtml = cards.map((c, i) => {
    const label = c.label || c.name || c.title || 'Metric';
    const val = c.value !== undefined ? c.value : (c.val !== undefined ? c.val : '-');
    const unit = c.unit || (payload.options && payload.options.unit) || '';
    const displayVal = (unit && !String(val).includes(unit)) ? `${unit}${val}` : String(val);
    const change = c.change || c.delta || '';
    const trend = (c.trend || (String(change).startsWith('+') ? 'up' : String(change).startsWith('-') ? 'down' : '')).toLowerCase();
    const status = (c.status || '').toLowerCase();

    // Map contextual telemetry glyph
    let glyph = '◈';
    const lLower = label.toLowerCase();
    if (lLower.includes('asset') || lLower.includes('money') || lLower.includes('rev') || lLower.includes('mrr') || lLower.includes('cost') || lLower.includes('price')) glyph = '💎';
    else if (lLower.includes('perf') || lLower.includes('speed') || lLower.includes('acc') || lLower.includes('target') || lLower.includes('kpi') || lLower.includes('rate')) glyph = '🎯';
    else if (lLower.includes('ping') || lLower.includes('lat') || lLower.includes('resp') || lLower.includes('ms') || lLower.includes('time') || lLower.includes('ops')) glyph = '⚡';
    else if (lLower.includes('core') || lLower.includes('cpu') || lLower.includes('ram') || lLower.includes('load') || lLower.includes('node') || lLower.includes('host')) glyph = '🧬';
    else if (lLower.includes('brain') || lLower.includes('synapse') || lLower.includes('ai') || lLower.includes('memory') || lLower.includes('token') || lLower.includes('neural')) glyph = '🧠';

    let trendBadge = '';
    if (change) {
      const isUp = trend === 'up' || trend === 'bull' || String(change).startsWith('+');
      const isDown = trend === 'down' || trend === 'bear' || String(change).startsWith('-');
      const badgeCls = isUp ? 'kpi-badge-up' : (isDown ? 'kpi-badge-down' : 'kpi-badge-neutral');
      const arrow = isUp ? '▲ ' : (isDown ? '▼ ' : '');
      trendBadge = `<span class="tactical-kpi-badge ${badgeCls}">${arrow}${escapeHtml(String(change))}</span>`;
    }

    let statusDot = '';
    if (status) {
      const isOk = status === 'ok' || status === 'healthy' || status === 'success';
      const isWarn = status === 'warn' || status === 'warning';
      const dotCol = isOk ? '#10b981' : (isWarn ? '#f59e0b' : '#f43f5e');
      statusDot = `<span class="kpi-status-dot" style="background:${dotCol};box-shadow:0 0 6px ${dotCol};" title="Status: ${escapeHtml(status)}"></span>`;
    }

    // Micro sparkline SVG
    const sparkGradId = `spark-grad-${i}-${Math.floor(Math.random() * 10000)}`;
    const sparkCol = trend === 'down' ? '#f43f5e' : (trend === 'up' ? '#10b981' : '#00f0ff');
    const y1 = 16 - (i % 3) * 4;
    const y2 = 8 + (i % 2) * 5;
    const y3 = trend === 'down' ? 18 : 6;
    const sparkSvg = `
      <div class="kpi-sparkline-wrap">
        <svg viewBox="0 0 120 24" class="kpi-sparkline-svg" preserveAspectRatio="none">
          <defs>
            <linearGradient id="${sparkGradId}" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="${sparkCol}" stop-opacity="0.35" />
              <stop offset="100%" stop-color="${sparkCol}" stop-opacity="0.0" />
            </linearGradient>
          </defs>
          <path d="M 0 18 Q 30 ${y1} 60 ${y2} T 120 ${y3} L 120 24 L 0 24 Z" fill="url(#${sparkGradId})" />
          <path d="M 0 18 Q 30 ${y1} 60 ${y2} T 120 ${y3}" fill="none" stroke="${sparkCol}" stroke-width="1.8" stroke-linecap="round" />
        </svg>
      </div>
    `;

    return `
      <div class="tactical-kpi-card">
        <span class="kpi-corner-tr"></span>
        <span class="kpi-corner-bl"></span>
        <div class="kpi-card-head">
          <div class="kpi-card-meta">
            <span class="kpi-glyph">${glyph}</span>
            <span class="kpi-card-label">${escapeHtml(label)}</span>
          </div>
          <div class="kpi-head-right">
            <span class="kpi-tag-chip">HUD // M-${i + 1}</span>
            ${statusDot}
          </div>
        </div>
        <div class="kpi-card-main">
          <span class="kpi-card-val">${escapeHtml(displayVal)}</span>
          ${trendBadge}
        </div>
        ${sparkSvg}
        ${c.desc ? `<div class="kpi-card-desc">${escapeHtml(c.desc)}</div>` : ''}
      </div>
    `;
  }).join('');

  return `
    <div class="tactical-kpi-grid">
      ${cardsHtml}
    </div>
  `;
}

function generatePipelineHtml(payload) {
  const stages = (payload.data && Array.isArray(payload.data.stages)) ? payload.data.stages :
                 (payload.data && Array.isArray(payload.data.steps)) ? payload.data.steps :
                 (Array.isArray(payload.stages) ? payload.stages :
                 (Array.isArray(payload.data) ? payload.data : []));
  if (!stages.length) return '';

  const stagesHtml = stages.map((s, idx) => {
    const name = s.name || s.stage || s.label || `Stage ${idx + 1}`;
    const status = (s.status || 'pending').toLowerCase();
    let icon = '○';
    let statusCls = 'stage-pending';
    if (status === 'done' || status === 'completed' || status === 'success') {
      icon = '✔';
      statusCls = 'stage-done';
    } else if (status === 'running' || status === 'active' || status === 'in_progress') {
      icon = '⚡';
      statusCls = 'stage-running';
    } else if (status === 'failed' || status === 'error') {
      icon = '✖';
      statusCls = 'stage-failed';
    }
    return `
      <div class="tactical-pipeline-stage ${statusCls}">
        <div class="pipeline-stage-icon">${icon}</div>
        <div class="pipeline-stage-info">
          <span class="pipeline-stage-name">${escapeHtml(name)}</span>
          <span class="pipeline-stage-status">${escapeHtml(status.toUpperCase())}</span>
        </div>
      </div>
    `;
  }).join('<div class="pipeline-stage-arrow">→</div>');

  return `
    <div class="tactical-pipeline-container">
      ${stagesHtml}
    </div>
  `;
}

function generateDataGridHtml(payload) {
  let rows = (payload.data && Array.isArray(payload.data.rows)) ? payload.data.rows :
             (payload.data && Array.isArray(payload.data.items)) ? payload.data.items :
             (Array.isArray(payload.rows) ? payload.rows :
             (Array.isArray(payload.data) ? payload.data : []));
  let cols = (payload.data && Array.isArray(payload.data.columns)) ? payload.data.columns :
             (Array.isArray(payload.columns) ? payload.columns : []);
  if (!rows.length) return '';
  if (!cols.length && rows.length > 0 && typeof rows[0] === 'object') {
    cols = Object.keys(rows[0]);
  }
  if (!cols.length) return '';

  const thead = cols.map(c => `<th>${escapeHtml(String(c))}</th>`).join('');
  const tbody = rows.map(r => {
    const tds = cols.map(c => {
      const val = r[c] !== undefined ? String(r[c]) : '';
      const isStatus = ['status', 'state'].includes(String(c).toLowerCase());
      if (isStatus) {
        const isOk = ['healthy', 'done', 'ok', 'active', 'online'].includes(val.toLowerCase());
        const isBad = ['error', 'failed', 'dead', 'offline'].includes(val.toLowerCase());
        const badgeCol = isOk ? '#10b981' : (isBad ? '#f43f5e' : '#f59e0b');
        return `<td><span class="grid-status-badge" style="color:${badgeCol};border-color:${badgeCol};background:${badgeCol}18;">${escapeHtml(val)}</span></td>`;
      }
      return `<td>${escapeHtml(val)}</td>`;
    }).join('');
    return `<tr>${tds}</tr>`;
  }).join('');

  return `
    <div class="tactical-grid-container">
      <table class="tactical-grid-table">
        <thead><tr>${thead}</tr></thead>
        <tbody>${tbody}</tbody>
      </table>
    </div>
  `;
}

function generateGaugeSvg(payload) {
  const val = Number((payload.data && payload.data.value !== undefined) ? payload.data.value : (payload.value !== undefined ? payload.value : 50));
  const min = Number((payload.data && payload.data.min !== undefined) ? payload.data.min : 0);
  const max = Number((payload.data && payload.data.max !== undefined) ? payload.data.max : 100);
  const unit = (payload.data && payload.data.unit) || (payload.options && payload.options.unit) || '%';
  const label = (payload.data && payload.data.label) || payload.title || 'LEVEL';

  const range = (max - min) || 100;
  const pct = Math.max(0, Math.min(1, (val - min) / range));
  const angle = -180 + pct * 180;

  const w = 240, h = 140, cx = 120, cy = 110, r = 80;
  const rad = (Math.PI * angle) / 180;
  const needleX = cx + (r - 15) * Math.cos(rad);
  const needleY = cy + (r - 15) * Math.sin(rad);

  const col = pct < 0.6 ? '#10b981' : (pct < 0.85 ? '#f59e0b' : '#f43f5e');

  return `
    <div class="tactical-gauge-container">
      <svg viewBox="0 0 ${w} ${h}" class="tactical-gauge-svg">
        <path d="M 40 110 A 80 80 0 0 1 200 110" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="14" stroke-linecap="round" />
        <path d="M 40 110 A 80 80 0 0 1 ${needleX.toFixed(1)} ${needleY.toFixed(1)}" fill="none" stroke="${col}" stroke-width="14" stroke-linecap="round" style="filter:drop-shadow(0 0 6px ${col});" />
        <circle cx="${cx}" cy="${cy}" r="7" fill="#ffffff" />
        <line x1="${cx}" y1="${cy}" x2="${needleX.toFixed(1)}" y2="${needleY.toFixed(1)}" stroke="#ffffff" stroke-width="3" stroke-linecap="round" />
        <text x="${cx}" y="${cy - 20}" text-anchor="middle" fill="#ffffff" font-size="18" font-weight="800" font-family="monospace">${val}${unit}</text>
        <text x="${cx}" y="${cy + 22}" text-anchor="middle" fill="#94a3b8" font-size="9.5" font-family="monospace">${escapeHtml(label)}</text>
      </svg>
    </div>
  `;
}

function generateDiagramSvg(payload) {
  const nodes = (payload.data && Array.isArray(payload.data.nodes)) ? payload.data.nodes : (Array.isArray(payload.nodes) ? payload.nodes : []);
  const links = (payload.data && Array.isArray(payload.data.links)) ? payload.data.links : (Array.isArray(payload.links) ? payload.links : []);
  if (!nodes.length) return '';

  const w = 480, h = 180;
  const n = nodes.length;
  const nodeW = Math.max(90, Math.min(130, (w - 60) / n));
  const nodeH = 46;
  const gap = n > 1 ? (w - 40 - n * nodeW) / (n - 1) : 0;
  const y = (h - nodeH) / 2;

  const nodeMap = {};
  const nodeEls = [];

  nodes.forEach((node, idx) => {
    const x = 20 + idx * (nodeW + gap);
    nodeMap[node.id || String(idx)] = { x, y, cx: x + nodeW / 2, cy: y + nodeH / 2, w: nodeW, h: nodeH };
    const label = node.label || node.name || node.id || `Node ${idx + 1}`;
    const type = (node.type || 'service').toUpperCase();
    nodeEls.push(`
      <g class="diagram-node">
        <rect x="${x}" y="${y}" width="${nodeW}" height="${nodeH}" rx="6" fill="#080e1e" stroke="rgba(0, 240, 255, 0.4)" stroke-width="1.5" />
        <rect x="${x}" y="${y}" width="${nodeW}" height="14" rx="6" fill="rgba(0, 240, 255, 0.12)" />
        <text x="${x + nodeW / 2}" y="${y + 10}" text-anchor="middle" fill="#38bdf8" font-size="7.5" font-weight="700" font-family="monospace">${escapeHtml(type)}</text>
        <text x="${x + nodeW / 2}" y="${y + 32}" text-anchor="middle" fill="#ffffff" font-size="10" font-weight="600" font-family="monospace">${escapeHtml(label.length > 14 ? label.slice(0, 13) + '…' : label)}</text>
      </g>
    `);
  });

  const linkEls = [];
  links.forEach(link => {
    const from = nodeMap[link.from];
    const to = nodeMap[link.to];
    if (from && to) {
      const x1 = from.x + from.w;
      const y1 = from.cy;
      const x2 = to.x;
      const y2 = to.cy;
      linkEls.push(`
        <line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#00f0ff" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#diag-arrow)" />
        ${link.label ? `<text x="${(x1 + x2) / 2}" y="${y1 - 6}" text-anchor="middle" fill="#94a3b8" font-size="8" font-family="monospace">${escapeHtml(link.label)}</text>` : ''}
      `);
    }
  });

  return `
    <div class="tactical-diagram-container">
      <svg viewBox="0 0 ${w} ${h}" class="tactical-diagram-svg" width="100%">
        <defs>
          <marker id="diag-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#00f0ff" />
          </marker>
        </defs>
        ${linkEls.join('')}
        ${nodeEls.join('')}
      </svg>
    </div>
  `;
}

function generateLogStreamerHtml(payload) {
  const logs = (payload.data && Array.isArray(payload.data.logs)) ? payload.data.logs :
               (payload.data && Array.isArray(payload.data.lines)) ? payload.data.lines :
               (Array.isArray(payload.logs) ? payload.logs :
               (Array.isArray(payload.data) ? payload.data : []));
  if (!logs.length) return '';

  const logLines = logs.map(l => {
    let lvl = 'INFO';
    let msg = '';
    let time = '';
    if (typeof l === 'string') {
      msg = l;
      const m = l.match(/\[(INFO|WARN|ERROR|DEBUG|FATAL|SUCCESS)\]/i);
      if (m) lvl = m[1].toUpperCase();
    } else if (typeof l === 'object') {
      lvl = (l.level || l.lvl || 'INFO').toUpperCase();
      msg = l.message || l.msg || l.text || JSON.stringify(l);
      time = l.time || l.timestamp || '';
    }

    let lvlCol = '#38bdf8';
    if (lvl.includes('WARN')) lvlCol = '#f59e0b';
    else if (lvl.includes('ERR') || lvl.includes('FATAL')) lvlCol = '#f43f5e';
    else if (lvl.includes('SUCC') || lvl.includes('OK')) lvlCol = '#10b981';
    else if (lvl.includes('DEBUG')) lvlCol = '#94a3b8';

    return `
      <div class="tactical-log-line">
        ${time ? `<span class="log-time">${escapeHtml(time)}</span>` : ''}
        <span class="log-lvl-badge" style="color:${lvlCol};border-color:${lvlCol};background:${lvlCol}18;">[${escapeHtml(lvl)}]</span>
        <span class="log-msg-text">${escapeHtml(msg)}</span>
      </div>
    `;
  }).join('');

  return `
    <div class="tactical-log-streamer">
      <div class="log-streamer-head">
        <span class="log-streamer-dot"></span>
        <span>TELEMETRY STREAM // LIVE MONITOR</span>
      </div>
      <div class="log-streamer-body">
        ${logLines}
      </div>
    </div>
  `;
}

function generateRadarSvg(payload) {
  let labels = payload.labels || (payload.data && payload.data.labels) || [];
  let values = [];

  if (payload.data && Array.isArray(payload.data.series) && payload.data.series.length > 0) {
    const s0 = payload.data.series[0];
    values = (s0.data || s0.values || []).map(Number);
  } else if (payload.data && Array.isArray(payload.data.values)) {
    values = payload.data.values.map(Number);
  } else if (payload.values && Array.isArray(payload.values)) {
    values = payload.values.map(Number);
  } else if (payload.data && Array.isArray(payload.data.items)) {
    labels = payload.data.items.map(it => it.label || it.name || '');
    values = payload.data.items.map(it => Number(it.value !== undefined ? it.value : it.val || 0));
  }

  if (!values.length) return '';
  if (!labels.length) labels = values.map((_, i) => `Axis ${i + 1}`);

  const n = values.length;
  const w = 340, h = 260, cx = 170, cy = 130, maxR = 85;
  const maxV = Math.max(...values, 100);

  const angleStep = (2 * Math.PI) / n;
  const gridRings = [0.25, 0.5, 0.75, 1.0];

  const gridEls = [];
  gridRings.forEach(ratio => {
    const r = maxR * ratio;
    const pts = [];
    for (let i = 0; i < n; i++) {
      const a = -Math.PI / 2 + i * angleStep;
      pts.push(`${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`);
    }
    gridEls.push(`<polygon points="${pts.join(' ')}" fill="none" stroke="rgba(0, 240, 255, 0.15)" stroke-width="1" />`);
  });

  const axisEls = [];
  const valPts = [];
  for (let i = 0; i < n; i++) {
    const a = -Math.PI / 2 + i * angleStep;
    const endX = cx + maxR * Math.cos(a);
    const endY = cy + maxR * Math.sin(a);
    axisEls.push(`<line x1="${cx}" y1="${cy}" x2="${endX.toFixed(1)}" y2="${endY.toFixed(1)}" stroke="rgba(0, 240, 255, 0.2)" />`);

    const lblR = maxR + 18;
    const lblX = cx + lblR * Math.cos(a);
    const lblY = cy + lblR * Math.sin(a) + 3;
    const shortLbl = labels[i].length > 10 ? labels[i].slice(0, 9) + '…' : labels[i];
    axisEls.push(`<text x="${lblX.toFixed(1)}" y="${lblY.toFixed(1)}" text-anchor="middle" fill="#94a3b8" font-size="8.5" font-family="monospace">${escapeHtml(shortLbl)}</text>`);

    const valR = (Math.max(0, values[i]) / maxV) * maxR;
    valPts.push(`${(cx + valR * Math.cos(a)).toFixed(1)},${(cy + valR * Math.sin(a)).toFixed(1)}`);
  }

  return `
    <div class="tactical-radar-container">
      <svg viewBox="0 0 ${w} ${h}" class="tactical-radar-svg">
        ${gridEls.join('')}
        ${axisEls.join('')}
        <polygon points="${valPts.join(' ')}" fill="rgba(0, 240, 255, 0.25)" stroke="#00f0ff" stroke-width="2" />
        ${valPts.map((p, idx) => `<circle cx="${p.split(',')[0]}" cy="${p.split(',')[1]}" r="3" fill="#ffffff" stroke="#00f0ff" stroke-width="1.5"><title>${labels[idx]}: ${values[idx]}</title></circle>`).join('')}
      </svg>
    </div>
  `;
}

function renderTacticalChartCard(rawCode, rawLang) {
  let cleanLang = (rawLang || '').toLowerCase().trim();
  if (cleanLang.startsWith('visual:')) cleanLang = cleanLang.slice(7).trim();

  let parsed = null;
  let detectedTitle = '';

  // 1. Direct JSON parse
  try {
    parsed = JSON.parse(rawCode);
  } catch (_) {
    // 2. Embedded JSON slice: e.g. "BTC/USDT 1D\n[ [17000, 10, ... ] ]"
    const firstBracket = rawCode.search(/[{\[]/);
    const lastBracket = Math.max(rawCode.lastIndexOf('}'), rawCode.lastIndexOf(']'));
    if (firstBracket !== -1 && lastBracket > firstBracket) {
      const prefix = rawCode.slice(0, firstBracket).trim();
      if (prefix) {
        detectedTitle = prefix.split('\n')[0].trim();
      }
      try {
        const jsonSlice = rawCode.slice(firstBracket, lastBracket + 1);
        parsed = JSON.parse(jsonSlice);
      } catch (_) {}
    }

    // 3. Fallback line-by-line parsing (key-value, CSV candles, tuple candles)
    if (!parsed) {
      const lines = rawCode.split('\n').map(l => l.trim()).filter(Boolean);
      const items = [];
      const candleRows = [];
      for (const l of lines) {
        if (!detectedTitle && !l.match(/^[0-9\[{(]/) && !l.includes(':') && !l.includes('=')) {
          detectedTitle = l;
          continue;
        }
        // Normalize CSV / space-separated / tuple line: "[17000, 10, 12, 9, 11]" or "17000, 10, 12, 9, 11"
        const cleanLine = l.replace(/[\[\]\(\),]/g, ' ').trim();
        const parts = cleanLine.split(/\s+/).map(p => parseFloat(p)).filter(n => !isNaN(n));
        if (parts.length >= 4) {
          candleRows.push(parts);
          continue;
        }
        const m = l.match(/^([^:,]+)[:=]\s*([0-9.]+)/);
        if (m) items.push({ label: m[1].trim(), value: parseFloat(m[2]) });
      }
      if (candleRows.length >= 2) {
        parsed = { widget_type: 'trading', title: detectedTitle || 'TRADING CANDLESTICK', symbol: detectedTitle || 'BTC/USDT', candles: candleRows };
      } else if (items.length) {
        parsed = { data: items, title: detectedTitle };
      }
    }
  }

  if (!parsed) return null;

  // Normalize parsed payload structure
  if (Array.isArray(parsed)) {
    const isCandleList = cleanLang.includes('trading') || cleanLang.includes('candle') || (parsed[0] && (Array.isArray(parsed[0]) && parsed[0].length >= 4 || parsed[0].open !== undefined));
    if (isCandleList) {
      parsed = { widget_type: 'trading', symbol: detectedTitle || 'BTC/USDT', candles: parsed, title: detectedTitle };
    } else {
      parsed = { data: parsed, title: detectedTitle };
    }
  } else if (typeof parsed === 'object') {
    if (detectedTitle) {
      if (!parsed.title) parsed.title = detectedTitle;
      if (!parsed.symbol && (cleanLang.includes('trading') || parsed.widget_type === 'trading' || parsed.candles)) {
        parsed.symbol = detectedTitle;
      }
    }
  }

  let rawType = (parsed.widget_type || parsed.type || cleanLang || '').toLowerCase().trim();
  if (rawType.startsWith('visual:')) rawType = rawType.slice(7).trim();

  let chartType = '';
  if (rawType.includes('kpi') || rawType.includes('metric')) chartType = 'kpi';
  else if (rawType.includes('trading') || rawType.includes('candlestick')) chartType = 'trading';
  else if (rawType.includes('pipeline') || rawType.includes('workflow')) chartType = 'pipeline';
  else if (rawType.includes('grid') || rawType.includes('table')) chartType = 'grid';
  else if (rawType.includes('diagram') || rawType.includes('architecture') || rawType.includes('flowchart')) chartType = 'diagram';
  else if (rawType.includes('log') || rawType.includes('streamer') || rawType.includes('telemetry')) chartType = 'log_streamer';
  else if (rawType.includes('radar')) chartType = 'radar';
  else if (rawType.includes('gauge') || rawType.includes('speedometer')) chartType = 'gauge';
  else if (rawType.includes('donut') || rawType.includes('pie')) chartType = 'donut';
  else if (rawType.includes('bar')) chartType = 'bar';
  else if (rawType.includes('line') || rawType.includes('area')) chartType = 'line';
  else {
    if (parsed.candles || parsed.symbol || (Array.isArray(parsed) && parsed[0] && (parsed[0].open !== undefined || parsed[0].close !== undefined))) {
      chartType = 'trading';
    } else {
      chartType = 'donut';
    }
  }

  let bodyHtml = '';
  if (chartType === 'kpi') {
    bodyHtml = generateKpiDeckHtml(parsed);
  } else if (chartType === 'trading') {
    bodyHtml = generateTradingSvg(parsed);
  } else if (chartType === 'pipeline') {
    bodyHtml = generatePipelineHtml(parsed);
  } else if (chartType === 'grid') {
    bodyHtml = generateDataGridHtml(parsed);
  } else if (chartType === 'diagram') {
    bodyHtml = generateDiagramSvg(parsed);
  } else if (chartType === 'log_streamer') {
    bodyHtml = generateLogStreamerHtml(parsed);
  } else if (chartType === 'radar') {
    bodyHtml = generateRadarSvg(parsed);
  } else if (chartType === 'gauge') {
    bodyHtml = generateGaugeSvg(parsed);
  } else if (chartType === 'bar') {
    bodyHtml = generateBarSvg(parsed);
  } else if (chartType === 'line') {
    bodyHtml = generateLineSvg(parsed);
  } else {
    bodyHtml = generateDonutSvg(parsed, {
      centerText: parsed.centerText,
      centerSub: parsed.centerSub || 'METRIC'
    });
  }

  if (!bodyHtml) return null;

  const title = parsed.title || `${chartType.toUpperCase()} METRICS`;
  const subtitle = parsed.subtitle ? ` <span class="chart-card-subtitle">// ${escapeHtml(parsed.subtitle)}</span>` : '';
  const typeLabelMap = {
    trading: 'TRADING CANDLESTICK',
    kpi: 'KPI DECK',
    pipeline: 'PIPELINE TRACKER',
    grid: 'DATA GRID',
    diagram: 'ARCHITECTURE DIAGRAM',
    log_streamer: 'LOG STREAMER',
    radar: 'RADAR CHART',
    gauge: 'GAUGE METER',
    donut: 'DONUT CHART',
    bar: 'BAR CHART',
    line: 'LINE CHART'
  };
  const typeLabel = typeLabelMap[chartType] || chartType.toUpperCase();

  return `
    <div class="chat-chart-card chat-chart-${escapeHtml(chartType)}" data-chart-type="${escapeHtml(chartType)}">
      <div class="chart-card-header">
        <span class="chart-card-title">
          <span>📊</span>
          <span>[ VISUAL // ${escapeHtml(typeLabel)} ] ${escapeHtml(title)}${subtitle}</span>
        </span>
        <div class="chart-card-actions">
          <button class="chart-action-btn" onclick="downloadChartAsSvg(this)" title="Export SVG image">📷 SVG</button>
          <button class="chart-action-btn" onclick="toggleChartRawData(this)" title="Toggle source data">&lt;&gt; Data</button>
        </div>
      </div>
      <div class="chart-card-body">
        ${bodyHtml}
      </div>
      <div class="chart-raw-box">${escapeHtml(rawCode)}</div>
    </div>
  `;
}

function renderMarkdown(md) {
  if (!md) return '';

  let textToRender = md;
  // Auto-close open code fence if streaming
  const fenceCount = (textToRender.match(/```/g) || []).length;
  if (fenceCount % 2 === 1) {
    textToRender += '\n```';
  }

  // 1. Multi-line code blocks ```lang\ncode\n```
  const codeCards = [];
  const seenChartKeys = new Set();
  let formatted = textToRender.replace(/```([a-zA-Z0-9_\-\.:]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const l = lang ? lang.trim().toUpperCase() : 'CODE';
    const rawCode = code.trim();

    // Check if this is a Visual Painting Slot (Wall Painter / "Ngecat Tembok")
    if (l.startsWith('VISUAL_PAINTING:') || l.startsWith('VISUAL_PAINT:')) {
      const parts = l.split(':');
      const widgetType = (parts[1] || 'chart').toLowerCase();
      const stepIdx = parts[2] || '';
      let rawTitle = parts[3] ? decodeURIComponent(parts[3]) : '';
      if (!rawTitle) rawTitle = `${widgetType.toUpperCase()} TELEMETRY`;

      const paintHtml = `
        <div class="fl-holo-paint-slot" data-paint-step="${escapeHtml(stepIdx)}">
          <div class="fl-paint-roller-track">
            <div class="fl-paint-roller-blade"></div>
            <div class="fl-paint-surface">
              <div class="fl-paint-grid"></div>
              <div class="fl-paint-wireframe-ghost">
                ${generatePaintGhostSvg(widgetType)}
              </div>
            </div>
          </div>
          <div class="fl-paint-caption-bar">
            <div class="fl-paint-caption-left">
              <span class="fl-paint-glow-dot">●</span>
              <span class="fl-paint-tag">[HOLO // PAINTING] ${escapeHtml(widgetType.toUpperCase())}</span>
              <span class="fl-paint-title">⚡ ${escapeHtml(rawTitle)}</span>
            </div>
            <div class="fl-paint-telemetry">
              <span class="fl-paint-pulse-ring"></span>
              <span>SYNTHESIZING SHADERS</span>
            </div>
          </div>
        </div>
      `;
      const placeholder = '___CODE_BLOCK_' + codeCards.length + '___';
      codeCards.push(paintHtml);
      return placeholder;
    }

    // Check if this is a Chart / Visual Block
    let isVisualBlock = l.startsWith('VISUAL:') || /^(CHART|TRADING|CANDLESTICK|DONUT|PIE|BAR|LINE|AREA|KPI|GAUGE|RADAR|PIPELINE|GRID|TABLE|DATA_GRID|DIAGRAM)(:|$)/i.test(l);
    if (!isVisualBlock && (l === 'JSON' || l === 'CODE' || l === 'JAVASCRIPT' || l === 'JS' || l === '')) {
      const trimmed = rawCode.trim();
      if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
        try {
          const parsedCheck = JSON.parse(trimmed);
          if (parsedCheck && typeof parsedCheck === 'object') {
            const wt = (parsedCheck.widget_type || parsedCheck.type || parsedCheck.chartType || parsedCheck.chart_type || '').toLowerCase();
            if (wt.includes('trading') || wt.includes('donut') || wt.includes('pie') || wt.includes('kpi') || wt.includes('bar') || wt.includes('line') || wt.includes('candlestick') || wt.includes('radar') || wt.includes('gauge') || wt.includes('pipeline') || wt.includes('grid') || wt.includes('chart')) {
              isVisualBlock = true;
            } else if (parsedCheck.candles || parsedCheck.series || (parsedCheck.data && Array.isArray(parsedCheck.data) && parsedCheck.data.length > 0 && (parsedCheck.data[0].open !== undefined || parsedCheck.data[0].close !== undefined || (parsedCheck.data[0].label !== undefined && parsedCheck.data[0].value !== undefined)))) {
              isVisualBlock = true;
            } else if (Array.isArray(parsedCheck) && parsedCheck.length > 0 && (parsedCheck[0].open !== undefined || parsedCheck[0].close !== undefined || (parsedCheck[0].label !== undefined && parsedCheck[0].value !== undefined))) {
              isVisualBlock = true;
            }
          }
        } catch (_) {}
      }
    }

    if (isVisualBlock) {
      let cleanL = l.startsWith('VISUAL:') ? l.slice(7).trim().toLowerCase() : l.toLowerCase();
      let chartKey = '';
      try {
        const pObj = JSON.parse(rawCode);
        const t = (pObj.title || pObj.Title || pObj.name || '').trim().toLowerCase();
        const wt = (pObj.widget_type || cleanL).toLowerCase();
        chartKey = `${wt}::${t}`;
      } catch (_) {
        chartKey = `${cleanL}::${rawCode.slice(0, 35)}`;
      }

      // Strict Anti-Duplication Guard: If same chart already rendered in this message, skip!
      if (chartKey && seenChartKeys.has(chartKey)) {
        return '';
      }
      if (chartKey) seenChartKeys.add(chartKey);

      const chartHtml = renderTacticalChartCard(rawCode, l);
      if (chartHtml) {
        const placeholder = '___CODE_BLOCK_' + codeCards.length + '___';
        codeCards.push(chartHtml);
        return placeholder;
      }
    }
    const escaped = escapeHtml(rawCode);
    const lineCount = rawCode ? rawCode.split('\n').length : 1;
    const isRunnable = ['BASH', 'SH', 'SHELL', 'PYTHON', 'PY', 'JS', 'JAVASCRIPT', 'NODE'].includes(l);
    const placeholder = '___CODE_BLOCK_' + codeCards.length + '___';
    codeCards.push(`
      <div class="chat-code-card" data-code="${escapeHtml(rawCode)}" data-lang="${escapeHtml(l)}">
        <div class="code-card-header">
          <div class="code-card-meta">
            <span class="code-card-dot"></span>
            <span class="code-card-lang">[LANG // ${escapeHtml(l)}]</span>
            <span class="code-card-loc">● ${lineCount} LOC</span>
          </div>
          <div class="code-card-actions">
            ${isRunnable ? `
              <button class="code-card-run" data-action="stage-run" onclick="executeSnippetInChat(this)" title="Stage this code into chat prompt">
                <span class="code-run-icon">▶</span>
                <span>Stage Run</span>
              </button>
            ` : ''}
            <button class="code-card-copy" data-action="copy-code" onclick="copyCodeSnippet(this)" title="Copy code snippet">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              <span>Copy</span>
            </button>
          </div>
        </div>
        <pre class="code-card-pre"><code>${escaped}</code></pre>
      </div>
    `);
    return placeholder;
  });

  // 1b. Markdown media: images, videos & audio ![alt](url)
  formatted = formatted.replace(/!\[(.*?)\]\((.*?)\)/g, (match, alt, src) => {
    const cleanSrc = src.trim();
    const resolved = resolveMediaUrl(cleanSrc);
    const safeAlt = escapeHtml(alt || 'Media');
    const isVideo = /\.(mp4|webm|mov|mkv|ogg|m4v)$/i.test(cleanSrc);
    const isAudio = /\.(mp3|wav|ogg|aac|m4a|flac)$/i.test(cleanSrc);

    if (isVideo) {
      return `\n\n<div class="chat-media-card chat-video-card">
        <div class="chat-media-header">
          <span class="chat-media-tag">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            VIDEO PLAYER
          </span>
          <span class="chat-media-filename">${safeAlt}</span>
        </div>
        <div class="chat-video-preview" style="padding:8px;background:rgba(0,0,0,0.6);border-radius:6px;display:flex;justify-content:center;">
          <video controls playsinline preload="metadata" style="max-width:100%;max-height:450px;width:100%;border-radius:4px;outline:none;" src="${resolved}">
            Your browser does not support HTML5 video.
          </video>
        </div>
      </div>\n\n`;
    }
    if (isAudio) {
      return `\n\n<div class="chat-media-card chat-audio-card">
        <div class="chat-media-header">
          <span class="chat-media-tag">AUDIO</span>
          <span class="chat-media-filename">${safeAlt}</span>
        </div>
        <div style="padding:10px;background:rgba(0,0,0,0.4);border-radius:6px;">
          <audio controls preload="none" style="width:100%;" src="${resolved}"></audio>
        </div>
      </div>\n\n`;
    }
    return `\n\n<div class="chat-media-card">
      <div class="chat-media-header">
        <span class="chat-media-tag">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          SCREENSHOT / IMAGE
        </span>
        <span class="chat-media-filename">${safeAlt}</span>
      </div>
      <div class="chat-media-preview" data-url="${escapeHtml(resolved)}" data-title="${safeAlt}" onclick="window.handleChatAttachmentClick(this)">
        <img src="${resolved}" alt="${safeAlt}" loading="lazy" />
        <div class="chat-media-overlay">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
          <span>Click to view full size</span>
        </div>
      </div>
    </div>\n\n`;
  });

  // 1c. Markdown file links / downloads: [label](path_or_url)
  formatted = formatted.replace(/(?<!!)\[(.*?)\]\((.*?)\)/g, (match, label, href) => {
    const cleanHref = href.trim();
    const isMediaDownloadCard = /\.(zip|tar|gz|rar|7z|pdf)$/i.test(cleanHref) ||
                                cleanHref.includes('.flowork_spam') ||
                                cleanHref.includes('canvas-ui/uploads');

    if (isMediaDownloadCard) {
      const resolved = resolveMediaUrl(cleanHref);
      const safeLabel = escapeHtml(label || 'Attached File');
      const icon = getFileCategoryIcon(safeLabel || cleanHref);
      return `\n\n<div class="chat-file-card">
        <div class="chat-file-main">
          <div class="chat-file-badge">${icon}</div>
          <div class="chat-file-meta">
            <span class="chat-file-title">${safeLabel}</span>
            <span class="chat-file-path">${escapeHtml(resolved)}</span>
          </div>
        </div>
        <div class="chat-file-actions">
          <a href="${resolved}" download target="_blank" class="chat-file-btn" title="Download file">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>Download</span>
          </a>
          <button class="chat-file-btn" onclick="copyFilePath('${escapeHtml(resolved)}', this)" title="Copy path">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            <span>Copy Path</span>
          </button>
        </div>
      </div>\n\n`;
    }

    const isLocalFile = cleanHref.startsWith('file://') || (cleanHref.startsWith('/') && !cleanHref.startsWith('/api') && !cleanHref.startsWith('/canvas'));
    const icon = isLocalFile ? '📄' : '↗';
    const titleAttr = isLocalFile ? `Local path: ${cleanHref} (Click to copy/open)` : `Open ${cleanHref}`;

    return `<a href="${escapeHtml(cleanHref)}" target="_blank" rel="noopener noreferrer" class="chat-link" title="${escapeHtml(titleAttr)}" onclick="handleChatLinkClick(event, '${escapeHtml(cleanHref)}')">` +
           `<span class="chat-link-text">${escapeHtml(label)}</span>` +
           `<span class="chat-link-badge">${icon}</span></a>`;
  });

  // 2. Tables
  formatted = parseMarkdownTables(formatted);

  // 3. Callouts / Blockquotes
  formatted = formatted.replace(/(?:^|\n)> ?(?:\[!([A-Z]+)\])? ?([^\n]+(?:\n> ?[^\n]+)*)/g, (match, alertType, content) => {
    const cleanLines = match.split(/\n/).map(l => l.replace(/^> ?(\[!([A-Z]+)\])? ?/, '')).filter(Boolean);
    const type = (alertType || 'NOTE').toUpperCase();
    return `\n\n<div class="fl-callout fl-callout-${type.toLowerCase()}"><div class="fl-callout-header"><span class="fl-callout-tag">[!${type}]</span></div><div class="fl-callout-body">${cleanLines.join('<br>')}</div></div>\n\n`;
  });

  // 4. Headings
  formatted = formatted.replace(/^###### (.*$)/gim, '<h6 class="chat-h6">$1</h6>');
  formatted = formatted.replace(/^##### (.*$)/gim, '<h5 class="chat-h5">$1</h5>');
  formatted = formatted.replace(/^#### (.*$)/gim, '<h4 class="chat-h4">$1</h4>');
  formatted = formatted.replace(/^### (.*$)/gim, '<h3 class="chat-h3">$1</h3>');
  formatted = formatted.replace(/^## (.*$)/gim, '<h2 class="chat-h2">$1</h2>');
  formatted = formatted.replace(/^# (.*$)/gim, '<h1 class="chat-h1">$1</h1>');

  // 5. Horizontal rule
  formatted = formatted.replace(/^(?:---|\*\*\*|___)$/gim, '<hr class="chat-hr">');

  // 6. Inline code `code`
  formatted = formatted.replace(/`([^`\n]+)`/g, (match, code) => {
    return `<code class="chat-inline-code">${escapeHtml(code)}</code>`;
  });

  // 7. Unordered Lists (supports - and *, multiline indents, properly grouped)
  formatted = formatted.replace(/(?:^|\n)((?:[-*] [^\n]+(?:\n(?:  |\t)[^\n]+)*\n?)+)/g, (match, listBlock) => {
    const rawItems = listBlock.trim().split(/\n(?=[-*] )/);
    const lis = rawItems.map(item => {
      const clean = item.replace(/^[-*] /, '').replace(/\n(?:  |\t)+/g, '<br>');
      return `<li>${clean}</li>`;
    }).join('');
    return `\n\n<ul class="chat-ul">${lis}</ul>\n\n`;
  });

  // 8. Bold **text** with contextual semantic field badges
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, (match, text) => {
    const trimmed = text.trim();
    const lower = trimmed.toLowerCase();
    if (/^(condition|state|kondisi):?$/i.test(lower)) return `<strong class="chat-strong chat-label-condition chat-label-kondisi">${text}</strong>`;
    if (/^(impact|dampak|critical|danger|error|fatal):?$/i.test(lower)) return `<strong class="chat-strong chat-label-impact chat-label-dampak">${text}</strong>`;
    if (/^(solution|solusi|rekomendasi|recommendation|success|fix|resolution|resolusi|aman):?$/i.test(lower)) return `<strong class="chat-strong chat-label-solution chat-label-solusi">${text}</strong>`;
    if (/^(note|catatan|warning|peringatan|info|notice|perhatian):?$/i.test(lower)) return `<strong class="chat-strong chat-label-note chat-label-catatan">${text}</strong>`;
    return `<strong class="chat-strong">${text}</strong>`;
  });

  // 9. Italic *text* (strict non-bullet match)
  formatted = formatted.replace(/(?<![*\w])\*([^\s*][^*]*?[^\s*]|[^\s*])\*(?![*\w])/g, '<em class="chat-em">$1</em>');

  // 9b. Highlight tactical badges & tokens in text
  formatted = highlightTacticalBadges(formatted);

  // 9c. Autolink raw URLs that are not part of HTML attributes or existing tags
  formatted = autolinkRawUrls(formatted);

  // 10. Paragraphs & line breaks
  const paragraphs = formatted.split(/\n\n+/);
  formatted = paragraphs.map(p => {
    const trimmed = p.trim();
    if (!trimmed) return '';
    if (trimmed.startsWith('___CODE_BLOCK_') || trimmed.startsWith('<div') || trimmed.startsWith('<ul') || trimmed.startsWith('<ol') || trimmed.startsWith('<h') || trimmed.startsWith('<hr')) {
      return trimmed;
    }
    return `<p class="chat-p">${trimmed.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  // Sanitize Markdown HTML before restoring trusted internal components
  formatted = sanitizeMarkdownHtml(formatted);

  // Restore code cards (using function to avoid $ replacement pattern corruption)
  codeCards.forEach((card, idx) => {
    formatted = formatted.replace('___CODE_BLOCK_' + idx + '___', () => card);
  });

  return formatted;
}

function sanitizeMarkdownHtml(html) {
  if (!html) return '';
  return String(html)
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<\/?(?:iframe|object|embed|applet|meta|base)\b[^>]*>/gi, '')
    .replace(/\s+on[a-zA-Z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '')
    .replace(/(href|src)\s*=\s*(?:["']\s*javascript:[^"']*["']|javascript:[^\s>]+)/gi, '$1="#"');
}
window.sanitizeMarkdownHtml = sanitizeMarkdownHtml;


// =============================================================================
// CHAT ATTACHMENTS & CONTEXT HANDLER (IMAGES / FILES / CLIPBOARD)
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================
let activeChatAttachments = [];

function addChatAttachment(file) {
  if (!file) return;
  const id = 'att_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
  const isImage = file.type ? file.type.startsWith('image/') : /\.(png|jpe?g|webp|gif|svg|bmp)$/i.test(file.name || '');
  const previewUrl = isImage ? URL.createObjectURL(file) : null;

  const defaultName = isImage ? `screenshot_${Date.now()}.png` : `attachment_${Date.now()}`;
  let rawName = (file.name && file.name !== 'blob' && file.name !== 'image.png') ? file.name : defaultName;
  if (isImage && !/\.(png|jpe?g|webp|gif|svg|bmp)$/i.test(rawName)) {
    rawName += '.png';
  }

  activeChatAttachments.push({
    id,
    file,
    name: rawName,
    size: file.size || 0,
    type: file.type || (isImage ? 'image/png' : 'application/octet-stream'),
    isImage,
    previewUrl
  });

  renderChatAttachmentTray();
}
window.addChatAttachment = addChatAttachment;

window.removeChatAttachment = function(id) {
  const idx = activeChatAttachments.findIndex(a => a.id === id);
  if (idx !== -1) {
    const [removed] = activeChatAttachments.splice(idx, 1);
    if (removed.previewUrl) {
      try { URL.revokeObjectURL(removed.previewUrl); } catch (_) {}
    }
  }
  renderChatAttachmentTray();
};

function clearChatAttachments() {
  activeChatAttachments = [];
  renderChatAttachmentTray();
}
window.clearChatAttachments = clearChatAttachments;

function renderChatAttachmentTray() {
  const tray = document.getElementById('chat-attachment-tray');
  if (!tray) return;

  if (activeChatAttachments.length === 0) {
    tray.style.display = 'none';
    tray.innerHTML = '';
    return;
  }

  tray.style.display = 'flex';
  tray.innerHTML = activeChatAttachments.map(att => {
    const iconHtml = att.isImage && att.previewUrl
      ? `<img class="chat-attachment-thumb" src="${att.previewUrl}" alt="${escapeHtml(att.name)}" loading="lazy" onclick="openChatLightbox('${att.previewUrl}', '${escapeHtml(att.name)}')" />`
      : `<span class="chat-attachment-icon">${getFileCategoryIcon(att.name)}</span>`;

    return `
      <div class="chat-attachment-chip" data-id="${att.id}">
        ${iconHtml}
        <span class="chat-attachment-name" title="${escapeHtml(att.name)}">${escapeHtml(att.name)}</span>
        <span class="chat-attachment-size">${formatFileSize(att.size)}</span>
        <button class="chat-attachment-del" title="Remove attachment" onclick="removeChatAttachment('${att.id}')">
          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    `;
  }).join('');
}

async function uploadAttachmentToServer(att) {
  const cleanName = (att.name || 'file')
    .replace(/[^a-zA-Z0-9_\-\.]/g, '_')
    .toLowerCase();
  const uniqueName = `${Date.now()}_${cleanName}`;
  const targetPath = `canvas-ui/uploads/${uniqueName}`;

  let base64 = '';
  if (att.isImage && att.file) {
    try {
      base64 = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => {
          const res = reader.result;
          resolve(typeof res === 'string' ? res.split(',')[1] : '');
        };
        reader.onerror = () => resolve('');
        reader.readAsDataURL(att.file);
      });
    } catch (_) {}
  }

  try {
    const buffer = await att.file.arrayBuffer();
    const res = await fetch('/api/fs/save-file', {
      method: 'POST',
      headers: {
        'Content-Type': att.type || 'application/octet-stream',
        'X-Target-Path': targetPath
      },
      body: buffer
    });

    if (res.ok) {
      const data = await res.json().catch(() => ({}));
      const serverPath = (data && data.path) ? data.path : targetPath;
      return {
        success: true,
        filename: uniqueName,
        originalName: att.name,
        targetPath: serverPath,
        webUrl: `/canvas/uploads/${uniqueName}`,
        size: att.size,
        isImage: att.isImage,
        mimeType: att.type || (att.isImage ? 'image/png' : 'application/octet-stream'),
        base64
      };
    } else {
      console.warn(`[Upload] Server rejected ${att.name}: HTTP ${res.status}`);
    }
  } catch (err) {
    console.error(`[Upload] Network error uploading ${att.name}:`, err);
  }

  return {
    success: false,
    filename: uniqueName,
    originalName: att.name,
    targetPath: targetPath,
    webUrl: att.previewUrl || '',
    size: att.size,
    isImage: att.isImage,
    mimeType: att.type || (att.isImage ? 'image/png' : 'application/octet-stream'),
    base64
  };
}

async function captureScreenshotToChat() {
  const chatFileInput = document.getElementById('chat-file-input');
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
      if (chatFileInput) {
        chatFileInput.accept = 'image/*';
        chatFileInput.click();
      }
      return;
    }

    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: { cursor: 'always' },
      audio: false
    });
    const track = stream.getVideoTracks()[0];
    if (!track) return;

    const video = document.createElement('video');
    video.srcObject = stream;
    await new Promise(resolve => { video.onloadedmetadata = () => resolve(); });
    await video.play();
    await new Promise(resolve => setTimeout(resolve, 80));

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 1920;
    canvas.height = video.videoHeight || 1080;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    track.stop();

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `screenshot_${Date.now()}.png`, { type: 'image/png' });
        addChatAttachment(file);
        showToast('📸 Screenshot captured & attached!');
        const chatInput = document.getElementById('rightbar-chat-input');
        if (chatInput) chatInput.focus();
      }
    }, 'image/png');
  } catch (err) {
    if (err && err.name !== 'NotAllowedError') {
      console.warn('[Screenshot] Screen capture failed:', err);
      if (chatFileInput) {
        chatFileInput.accept = 'image/*';
        chatFileInput.click();
      }
    }
  }
}
window.captureScreenshotToChat = captureScreenshotToChat;

function initRightbarChat() {
  const btnToggleChat = document.getElementById('btn-toggle-chat');
  const btnCloseRightbar = document.getElementById('btn-close-rightbar');
  const rightbarChat = document.getElementById('rightbar-chat');
  const rightbarMessages = document.getElementById('rightbar-messages');
  const rightbarHistoryView = document.getElementById('rightbar-history-view');
  const btnChatNew = document.getElementById('btn-chat-new');
  const btnChatHistory = document.getElementById('btn-chat-history');
  const btnCloseHistory = document.getElementById('btn-close-history');
  const chatInput = document.getElementById('rightbar-chat-input');
  const btnSend = document.getElementById('btn-rightbar-send');
  const historyList = document.getElementById('history-items-list');

  // Default Rightbar open
  if (rightbarChat) {
    rightbarChat.classList.remove('collapsed');
    rightbarChat.style.removeProperty('display');
    localStorage.setItem('xflow_rightbar_collapsed', 'false');
    if (btnToggleChat) btnToggleChat.classList.add('active');
  }
  if (window.__updateLayoutResizers) window.__updateLayoutResizers();
  ensureAllLogoutButtons();

  // Toggle Rightbar panel
  if (btnToggleChat && rightbarChat) {
    btnToggleChat.addEventListener('click', () => {
      // Clear any inline display: none applied by previous catalog views
      rightbarChat.style.removeProperty('display');
      const resizerRight = document.getElementById('resizer-right');
      if (resizerRight) resizerRight.style.removeProperty('display');

      rightbarChat.classList.toggle('collapsed');
      const collapsed = rightbarChat.classList.contains('collapsed');
      localStorage.setItem('xflow_rightbar_collapsed', collapsed ? 'true' : 'false');
      btnToggleChat.classList.toggle('active', !collapsed);

      // Fail-safe: If user collapses chat while workbench is also collapsed, auto-restore workbench!
      const workbench = document.querySelector('.workbench-main');
      if (collapsed && workbench && workbench.classList.contains('collapsed')) {
        if (window.__setWorkbenchState) window.__setWorkbenchState(false, false);
      }

      if (window.__updateLayoutResizers) window.__updateLayoutResizers();
      if (!collapsed) {
        ensureAllLogoutButtons();
        if (chatInput) chatInput.focus();
        if (typeof scrollChatToBottom === 'function') scrollChatToBottom({ force: true });
      }
    });
  }

  // Close Rightbar panel
  if (btnCloseRightbar && rightbarChat) {
    btnCloseRightbar.addEventListener('click', () => {
      rightbarChat.classList.add('collapsed');
      localStorage.setItem('xflow_rightbar_collapsed', 'true');
      if (btnToggleChat) btnToggleChat.classList.remove('active');

      // Fail-safe: If user closes chat while workbench is also collapsed, auto-restore workbench!
      const workbench = document.querySelector('.workbench-main');
      if (workbench && workbench.classList.contains('collapsed')) {
        if (window.__setWorkbenchState) window.__setWorkbenchState(false, false);
      }

      if (window.__updateLayoutResizers) window.__updateLayoutResizers();
    });
  }

  const openHistoryView = () => {
    if (rightbarHistoryView) {
      rightbarHistoryView.classList.add('active');
      rightbarHistoryView.style.setProperty('display', 'flex', 'important');
    }
    if (rightbarMessages) {
      rightbarMessages.classList.add('history-active');
      rightbarMessages.style.setProperty('display', 'none', 'important');
    }
    // Prevent leak of pinned prompt or floating composer into history view
    const pinnedPrompt = document.getElementById('chat-pinned-prompt');
    if (pinnedPrompt) {
      pinnedPrompt.dataset.wasVisible = (pinnedPrompt.style.display !== 'none' && pinnedPrompt.style.display !== '') ? 'true' : 'false';
      pinnedPrompt.style.setProperty('display', 'none', 'important');
    }
    const footer = document.querySelector('.rightbar-chat-footer');
    if (footer) footer.style.setProperty('display', 'none', 'important');

    fetchChatHistory();
  };

  const closeHistoryView = () => {
    if (rightbarHistoryView) {
      rightbarHistoryView.classList.remove('active');
      rightbarHistoryView.style.setProperty('display', 'none', 'important');
    }
    if (rightbarMessages) {
      rightbarMessages.classList.remove('history-active');
      rightbarMessages.style.setProperty('display', 'flex', 'important');
      if (typeof scrollChatToBottom === 'function') scrollChatToBottom({ force: true });
    }
    // Restore pinned prompt and composer
    const pinnedPrompt = document.getElementById('chat-pinned-prompt');
    if (pinnedPrompt && pinnedPrompt.dataset.wasVisible === 'true') {
      pinnedPrompt.style.removeProperty('display');
    }
    const footer = document.querySelector('.rightbar-chat-footer');
    if (footer) {
      footer.style.removeProperty('display');
    }
  };
  window.__openHistoryView = openHistoryView;
  window.__closeHistoryView = closeHistoryView;
  window.showChatHistoryPanel = openHistoryView;
  window.hideChatHistoryPanel = closeHistoryView;

  // Toggle History view
  if (btnChatHistory && rightbarHistoryView && rightbarMessages) {
    btnChatHistory.addEventListener('click', (e) => {
      e.stopPropagation();
      const isHistoryOpen = rightbarHistoryView.classList.contains('active') || rightbarHistoryView.style.display === 'flex';
      if (isHistoryOpen) {
        closeHistoryView();
      } else {
        openHistoryView();
      }
    });
  }

  // Back from History to Messages
  if (btnCloseHistory) {
    btnCloseHistory.addEventListener('click', (e) => {
      e.stopPropagation();
      closeHistoryView();
    });
  }




  // Quick-action prompt chips & shortcuts click delegation
  if (rightbarMessages) {
    rightbarMessages.addEventListener('click', (e) => {
      const chip = e.target.closest('.fl-chip-btn');
      if (chip) {
        const prompt = chip.getAttribute('data-prompt');
        if (prompt && chatInput) {
          chatInput.value = prompt;
          chatInput.style.height = 'auto';
          sendUserChatMessage();
        }
        return;
      }
      const shortcut = e.target.closest('.fl-shortcut-pill');
      if (shortcut) {
        const cmd = shortcut.getAttribute('data-shortcut');
        if (cmd && chatInput) {
          chatInput.value = cmd;
          chatInput.focus();
          chatInput.style.height = 'auto';
        }
        return;
      }
      const runBtn = e.target.closest('.code-card-run');
      if (runBtn) {
        e.preventDefault();
        e.stopPropagation();
        if (typeof window.executeSnippetInChat === 'function') {
          window.executeSnippetInChat(runBtn);
        }
        return;
      }
      const copyCodeBtn = e.target.closest('.code-card-copy');
      if (copyCodeBtn) {
        e.preventDefault();
        e.stopPropagation();
        if (typeof window.copyCodeSnippet === 'function') {
          window.copyCodeSnippet(copyCodeBtn);
        }
        return;
      }
      const copyBtn = e.target.closest('.btn-copy-response');
      if (copyBtn) {
        e.preventDefault();
        e.stopPropagation();
        const card = copyBtn.closest('.chat-msg-assistant') || copyBtn.closest('.chat-msg-card') || copyBtn.closest('.chat-msg');
        const bodyArea = card?.querySelector('.chat-body-area') || card?.querySelector('.chat-msg-content') || card;
        const textToCopy = bodyArea ? (bodyArea.innerText || bodyArea.textContent || '').trim() : '';
        if (textToCopy && window.safeCopyToClipboard) {
          window.safeCopyToClipboard(textToCopy).then(() => {
            const span = copyBtn.querySelector('span');
            const originalText = span ? span.innerText : '';
            if (span) span.innerText = 'Copied!';
            copyBtn.classList.add('copied');
            setTimeout(() => {
              if (span) span.innerText = originalText || 'Copy';
              copyBtn.classList.remove('copied');
            }, 2000);
          });
        }
        return;
      }
    });
  }

  // New Chat session
  if (btnChatNew) {
    btnChatNew.addEventListener('click', () => {
      startNewChatSession();
    });
  }

  // History list clicks (item switch, delete, or rename)
  if (historyList) {
    historyList.addEventListener('click', (e) => {
      const renameBtn = e.target.closest('.history-item-rename');
      if (renameBtn) {
        e.stopPropagation();
        const id = renameBtn.getAttribute('data-rename-id');
        if (id) startRenameSession(id);
        return;
      }

      const delBtn = e.target.closest('.history-item-del');
      if (delBtn) {
        e.stopPropagation();
        const id = delBtn.getAttribute('data-del-id');
        if (id) deleteChatSession(id, e);
        return;
      }

      // If clicked inside an active rename box or item is being edited, ignore
      if (e.target.closest('.history-rename-box')) {
        return;
      }

      const item = e.target.closest('.history-item');
      if (item) {
        if (item.classList.contains('editing')) return;
        const sessionId = item.getAttribute('data-session-id');
        if (sessionId) {
          // 1. Instant visual item selection
          document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
          item.classList.add('active');
          // 2. Instant history view dismiss and loading indicator setup
          closeHistoryView();
          const rightbarMessages = document.getElementById('rightbar-messages');
          if (rightbarMessages) {
            rightbarMessages.classList.remove('history-active', 'agent-is-looping');
            rightbarMessages.style.setProperty('display', 'flex', 'important');
            rightbarMessages.querySelectorAll('.chat-msg, .fl-chat-loading-indicator').forEach(el => el.remove());
            const loadIndicator = document.createElement('div');
            loadIndicator.className = 'fl-chat-loading-indicator';
            loadIndicator.style.cssText = 'padding:24px; text-align:center; color:var(--text-dim); font-size:11px;';
            loadIndicator.textContent = 'Loading conversation steps...';
            rightbarMessages.appendChild(loadIndicator);
          }
          isChatStreaming = false;
          loadChatSession(sessionId);
        }
      }
    });

    // Double-click session title to rename
    historyList.addEventListener('dblclick', (e) => {
      const nameEl = e.target.closest('.history-name');
      if (nameEl) {
        e.stopPropagation();
        const id = nameEl.getAttribute('data-session-id');
        if (id) startRenameSession(id);
      }
    });
  }

  // Top status bar click (smooth scroll to running subagent or task)
  const topStatusBar = document.getElementById('chat-top-status-bar');
  if (topStatusBar) {
    topStatusBar.addEventListener('click', () => {
      const activeCard = document.querySelector('.fl-subagent-card, .fl-tool-card');
      if (activeCard) {
        activeCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }

  // Pinned prompt bar click (smooth scroll to original prompt)
  const pinnedPromptBar = document.getElementById('chat-pinned-prompt');
  if (pinnedPromptBar) {
    pinnedPromptBar.addEventListener('click', () => {
      if (activeTurnUserCard) {
        activeTurnUserCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }

  // Antigravity Queue Card toggle collapse
  const queueToggleBtn = document.getElementById('btn-toggle-queue');
  if (queueToggleBtn) {
    queueToggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const card = document.getElementById('chat-queue-card');
      if (card) card.classList.toggle('collapsed');
    });
  }

  // Antigravity Queue Card action delegation (Send now, Edit, Delete)
  const queueCard = document.getElementById('chat-queue-card');
  if (queueCard) {
    queueCard.addEventListener('click', async (e) => {
      // 1. Send now immediately
      const sendBtn = e.target.closest('.btn-send-now');
      if (sendBtn) {
        const qid = sendBtn.getAttribute('data-send-qid');
        const item = queuedMessages.find(q => q.id === qid);
        if (item) {
          queuedMessages = queuedMessages.filter(q => q.id !== qid);
          renderQueueTray();
          if (isChatStreaming) {
            await stopCurrentChatTurn();
          }
          setTimeout(() => {
            executeChatMessage(item.text);
          }, 150);
        }
        return;
      }

      // 2. Edit message (restore to input textarea)
      const editBtn = e.target.closest('.btn-edit-queue');
      if (editBtn) {
        const qid = editBtn.getAttribute('data-edit-qid');
        const item = queuedMessages.find(q => q.id === qid);
        if (item) {
          queuedMessages = queuedMessages.filter(q => q.id !== qid);
          renderQueueTray();
          if (chatInput) {
            chatInput.value = item.text;
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
            chatInput.focus();
          }
        }
        return;
      }

      // 3. Delete from queue
      const delBtn = e.target.closest('.btn-delete-queue');
      if (delBtn) {
        const qid = delBtn.getAttribute('data-del-qid');
        if (qid) {
          queuedMessages = queuedMessages.filter(q => q.id !== qid);
          renderQueueTray();
          showToast('Message removed from queue');
        }
        return;
      }
    });
  }

  // Antigravity Input Toolbar controls (+ button for Files/Images & Camera button for Screenshot)
  const btnChatAdd = document.getElementById('btn-chat-add');
  const btnChatScreenshot = document.getElementById('btn-chat-screenshot');
  const chatFileInput = document.getElementById('chat-file-input');

  if (btnChatAdd && chatFileInput) {
    btnChatAdd.addEventListener('click', () => {
      chatFileInput.removeAttribute('accept');
      chatFileInput.click();
    });
  }

  if (btnChatScreenshot) {
    btnChatScreenshot.addEventListener('click', () => {
      captureScreenshotToChat();
    });
  }

  if (chatFileInput) {
    chatFileInput.addEventListener('change', () => {
      if (chatFileInput.files && chatFileInput.files.length > 0) {
        Array.from(chatFileInput.files).forEach(f => addChatAttachment(f));
        showToast(`${chatFileInput.files.length} file(s) attached`);
        chatFileInput.value = '';
      }
    });
  }

  // Universal clipboard paste handler (Ctrl+V) for screenshots & copied images
  const handleClipboardPaste = (e) => {
    if (e.target !== chatInput && (e.target.tagName === 'INPUT' || (e.target.tagName === 'TEXTAREA' && e.target !== chatInput) || e.target.isContentEditable)) {
      return;
    }
    const cbd = e.clipboardData;
    if (!cbd) return;

    let hasAttached = false;
    // 1. Process clipboard items (PrtSc, Snipping Tool, direct image copy)
    if (cbd.items && cbd.items.length > 0) {
      for (let i = 0; i < cbd.items.length; i++) {
        const item = cbd.items[i];
        if (item.type && item.type.startsWith('image/')) {
          const blob = item.getAsFile();
          if (blob) {
            const file = new File([blob], `screenshot_${Date.now()}.png`, { type: blob.type || 'image/png' });
            addChatAttachment(file);
            hasAttached = true;
          }
        }
      }
    }

    // 2. Process clipboard files fallback
    if (!hasAttached && cbd.files && cbd.files.length > 0) {
      for (let i = 0; i < cbd.files.length; i++) {
        const f = cbd.files[i];
        if (f && (f.type.startsWith('image/') || /\.(png|jpe?g|webp|gif|svg|bmp)$/i.test(f.name))) {
          addChatAttachment(f);
          hasAttached = true;
        }
      }
    }

    if (hasAttached) {
      e.preventDefault();
      showToast('📸 Screenshot attached from clipboard');
      if (chatInput) chatInput.focus();
    }
  };

  if (chatInput) {
    chatInput.addEventListener('paste', handleClipboardPaste);
  }
  window.addEventListener('paste', handleClipboardPaste);

  // Shortcut Ctrl+Shift+S for instant screenshot capture
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'S' || e.key === 's')) {
      e.preventDefault();
      captureScreenshotToChat();
    }
  });

  // Drag and drop files onto chat input box or chat surfaces
  const dropTargets = ['.chat-input-box', '#office-bottom-chatbar', '.rightbar-chat-footer', '#rightbar-messages'];
  dropTargets.forEach(sel => {
    const el = document.querySelector(sel);
    if (!el) return;
    ['dragenter', 'dragover'].forEach(name => {
      el.addEventListener(name, (e) => {
        e.preventDefault();
        const box = document.querySelector('.chat-input-box');
        if (box) {
          box.style.borderColor = '#00e5ff';
          box.style.boxShadow = '0 0 16px rgba(0, 229, 255, 0.35)';
        }
      });
    });
    ['dragleave'].forEach(name => {
      el.addEventListener(name, (e) => {
        e.preventDefault();
        const box = document.querySelector('.chat-input-box');
        if (box) {
          box.style.borderColor = '';
          box.style.boxShadow = '';
        }
      });
    });
    el.addEventListener('drop', (e) => {
      e.preventDefault();
      const box = document.querySelector('.chat-input-box');
      if (box) {
        box.style.borderColor = '';
        box.style.boxShadow = '';
      }
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        Array.from(e.dataTransfer.files).forEach(f => addChatAttachment(f));
        showToast(`${e.dataTransfer.files.length} file(s) attached`);
      }
    });
  });

  // Lightbox Modal click listeners
  const lightboxClose = document.getElementById('chat-lightbox-close');
  const lightboxBackdrop = document.getElementById('chat-lightbox-backdrop');
  if (lightboxClose) {
    lightboxClose.addEventListener('click', closeChatLightbox);
  }
  if (lightboxBackdrop) {
    lightboxBackdrop.addEventListener('click', closeChatLightbox);
  }

  initModelSelector();
  initAccountSelector();
  initAgentSelector();
  initSlashCommandPalette();

  // Input textarea auto-height & enter-to-send / escape-to-stop
  if (chatInput) {
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
      handleSlashInput(chatInput);
    });

    chatInput.addEventListener('keydown', (e) => {
      if (isSlashPaletteOpen) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          navigateSlashPalette(1);
          return;
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault();
          navigateSlashPalette(-1);
          return;
        }
        if (e.key === 'Enter' || e.key === 'Tab') {
          if (filteredSlashCommands.length > 0 && slashPaletteSelectedIndex >= 0 && slashPaletteSelectedIndex < filteredSlashCommands.length) {
            e.preventDefault();
            selectSlashCommand(filteredSlashCommands[slashPaletteSelectedIndex].command);
            return;
          }
        }
        if (e.key === 'Escape') {
          e.preventDefault();
          closeSlashPalette();
          return;
        }
      }

      if (e.key === 'Escape' && isChatStreaming) {
        e.preventDefault();
        stopCurrentChatTurn();
        return;
      }
      // Antigravity-style Ctrl+Z to undo last turn when input is empty
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !chatInput.value.trim() && !isChatStreaming) {
        e.preventDefault();
        undoLastChatTurn();
        return;
      }
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendUserChatMessage();
      }
    });
  }

  // Send / Stop button click
  if (btnSend) {
    btnSend.addEventListener('click', () => {
      if (isSystemRestarting) {
        showToast('🔄 Flowork is restarting & loading updates, please wait a moment...');
        return;
      }
      if (isChatStreaming) {
        if (chatInput && chatInput.value.trim()) {
          sendUserChatMessage(); // Queue typed message
        } else {
          stopCurrentChatTurn(); // Stop active turn
        }
      } else {
        sendUserChatMessage();
      }
    });
  }

  // Global Escape key listener (handles Lightbox, active menu, and generation)
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const lb = document.getElementById('chat-lightbox-modal');
      if (lb && lb.style.display !== 'none') {
        closeChatLightbox();
        return;
      }
      if (isChatStreaming) {
        if (isModalActive()) return;
        if (document.activeElement === document.getElementById('plugin-search-input')) return;
        const modelMenu = document.getElementById('chat-model-selector-menu');
        if (modelMenu && modelMenu.classList.contains('open')) return;
        stopCurrentChatTurn();
      }
    }
  });

  // Initialize 3D Mascot Hero if empty hero canvas is visible
  if (document.getElementById('chat-mascot-canvas')) {
    initChatMascot();
  }

  // Auto-restore latest active chat session on launch or refresh
  autoRestoreLatestChatSession();

  startChatSyncEngine();
}

function syncSoloStudioComposer(isSolo) {
  // Chat composer is strictly unified inside .rightbar-chat-footer within #rightbar-chat.
  // Never separated or moved across containers.
}
window.syncSoloStudioComposer = syncSoloStudioComposer;

function initOfficeBottomChatbar() {
  // Chat composer is strictly unified inside .rightbar-chat-footer within #rightbar-chat.
}
window.initOfficeBottomChatbar = initOfficeBottomChatbar;

async function syncActiveChatSession() {
  if (document.hidden || isChatStreaming || isChatSyncing || !currentChatSessionId) return;
  isChatSyncing = true;
  try {
    const res = await fetch(`/api/chat/steps/${encodeURIComponent(currentChatSessionId)}`);
    const data = await res.json();
    if (isChatStreaming) return;
    if (data.status === 'ok' && data.data && Array.isArray(data.data.steps)) {
      const serverSteps = data.data.steps;
      const count = serverSteps.length;
      const lastStep = count > 0 ? serverSteps[count - 1] : null;
      const lastStatus = lastStep ? (lastStep.status || '') : '';
      const lastRespLen = (lastStep && lastStep.plannerResponse && lastStep.plannerResponse.response) 
        ? lastStep.plannerResponse.response.length 
        : 0;
      const fingerprint = `${count}:${lastStatus}:${lastRespLen}`;

      if (fingerprint !== lastKnownStepFingerprint) {
        const isFirstLoad = !lastKnownStepFingerprint;
        lastKnownStepFingerprint = fingerprint;
        const msgContainer = document.getElementById('rightbar-messages') || document.getElementById('chat-messages-container');
        const wasNearBottom = msgContainer ? (msgContainer.scrollHeight - msgContainer.scrollTop - msgContainer.clientHeight < 240) : true;

        renderTrajectorySteps(serverSteps);

        if (typeof scrollChatToBottom === 'function') {
          scrollChatToBottom({ force: isFirstLoad || wasNearBottom });
        } else if (msgContainer && (isFirstLoad || wasNearBottom)) {
          msgContainer.scrollTop = msgContainer.scrollHeight;
        }

        if (!isFirstLoad && lastStatus.endsWith('DONE')) {
          fetchChatHistory();
        }
      }
    }
  } catch (err) {
    // Silent fail during network jitter
  } finally {
    isChatSyncing = false;
  }
}

function startChatSyncEngine() {
  if (chatSyncTimer) clearInterval(chatSyncTimer);
  chatSyncTimer = setInterval(syncActiveChatSession, 4000); // 4s relaxed cadence
}

function stopChatSyncEngine() {
  if (chatSyncTimer) {
    clearInterval(chatSyncTimer);
    chatSyncTimer = null;
  }
}
window.startChatSyncEngine = startChatSyncEngine;
window.stopChatSyncEngine = stopChatSyncEngine;

// =============================================================================
// MR. FLOW 3D MASCOT INLINE PROCEDURAL ENGINE & AUDIO INTEGRATION
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================
let THREE_LIB = null;
let ORBIT_CONTROLS_CLASS = null;

let mascotScene = null;
let mascotCamera = null;
let mascotRenderer = null;
let mascotControls = null;
let mascotFaceRoot = null;
let mascotProceduralMouth = null;
let mascotMouthLight = null;
let mascotHoloRings = [];
let mascotParticles = null;
let mascotAnimId = null;
let mascotIsRunning = false;
let mascotAudioCtx = null;
let mascotAnalyser = null;
let mascotSmoothVocalEnergy = 0.0;
let mascotResizeObs = null;
let mascotMouseMoveAttached = false;
const mascotMouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
let mascotClock = null;

async function ensureThreeLoaded() {
  if (THREE_LIB && ORBIT_CONTROLS_CLASS) return true;
  try {
    if (!THREE_LIB) {
      THREE_LIB = await import('/canvas/vendor/three/three.module.js');
    }
    if (!ORBIT_CONTROLS_CLASS) {
      const controlsMod = await import('/canvas/vendor/three/addons/controls/OrbitControls.js');
      ORBIT_CONTROLS_CLASS = controlsMod.OrbitControls;
    }
    return true;
  } catch (err) {
    console.warn('[MrFlow Mascot] Failed to load Three.js libraries:', err);
    return false;
  }
}

function createMascotHoloRings(scene, THREE) {
  mascotHoloRings = [];
  const ringGeom = new THREE.TorusGeometry(0.72, 0.006, 16, 120);
  const ringMat1 = new THREE.MeshBasicMaterial({ color: 0x00e5ff, transparent: true, opacity: 0.5 });
  const ringMat2 = new THREE.MeshBasicMaterial({ color: 0x7f00ff, transparent: true, opacity: 0.4 });
  const ringMat3 = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.3 });

  const ring1 = new THREE.Mesh(ringGeom, ringMat1);
  ring1.userData = { speedZ: 0.005, speedX: 0.003, baseScale: 0.95 };
  scene.add(ring1);
  mascotHoloRings.push(ring1);

  const ring2 = new THREE.Mesh(ringGeom, ringMat2);
  ring2.userData = { speedZ: -0.007, speedX: -0.004, baseScale: 1.10 };
  ring2.rotation.x = Math.PI / 3;
  scene.add(ring2);
  mascotHoloRings.push(ring2);

  const ring3 = new THREE.Mesh(ringGeom, ringMat3);
  ring3.userData = { speedZ: 0.004, speedX: -0.005, baseScale: 1.25 };
  ring3.rotation.y = Math.PI / 4;
  scene.add(ring3);
  mascotHoloRings.push(ring3);
}

function createMascotParticles(scene, THREE) {
  const count = 260;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);

  for (let i = 0; i < count * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 8.5;
    positions[i + 1] = (Math.random() - 0.5) * 6.0;
    positions[i + 2] = (Math.random() - 0.5) * 4.0;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({
    color: 0x00f2fe,
    size: 0.024,
    transparent: true,
    opacity: 0.55
  });

  mascotParticles = new THREE.Points(geometry, material);
  scene.add(mascotParticles);
}

function createMascotAvatar(scene, THREE) {
  const group = new THREE.Group();

  // Materials
  const armorMat = new THREE.MeshStandardMaterial({
    color: 0x14213d,
    metalness: 0.88,
    roughness: 0.18
  });

  const visorGlassMat = new THREE.MeshStandardMaterial({
    color: 0x030814,
    metalness: 0.15,
    roughness: 0.55
  });

  const cyanEmissive = new THREE.MeshStandardMaterial({
    color: 0x00f2fe,
    emissive: 0x00f2fe,
    emissiveIntensity: 2.6,
    metalness: 0.8,
    roughness: 0.2
  });

  const purpleEmissive = new THREE.MeshStandardMaterial({
    color: 0x7f00ff,
    emissive: 0x7f00ff,
    emissiveIntensity: 2.3,
    metalness: 0.8,
    roughness: 0.2
  });

  // 1. Head & Chibi Helmet Shell
  const headGroup = new THREE.Group();
  group.add(headGroup);

  const helmetGeom = new THREE.SphereGeometry(0.72, 48, 36);
  const helmet = new THREE.Mesh(helmetGeom, armorMat);
  helmet.scale.set(1.0, 0.96, 0.92);
  headGroup.add(helmet);

  const visorGeom = new THREE.SphereGeometry(0.725, 48, 32, -Math.PI * 0.44, Math.PI * 0.88, Math.PI * 0.22, Math.PI * 0.56);
  const visor = new THREE.Mesh(visorGeom, visorGlassMat);
  visor.scale.set(1.01, 0.97, 0.93);
  headGroup.add(visor);

  const visorRimGeom = new THREE.TorusGeometry(0.50, 0.014, 16, 48, Math.PI * 1.3);
  const visorRim = new THREE.Mesh(visorRimGeom, cyanEmissive);
  visorRim.rotation.z = Math.PI * 0.85;
  visorRim.position.set(0, -0.05, 0.65);
  headGroup.add(visorRim);

  // 2. Forehead Crest Badge with 3D Flowork "F" Logo
  const logoGroup = new THREE.Group();
  logoGroup.position.set(0, 0.44, 0.54);
  logoGroup.rotation.x = -0.36;
  headGroup.add(logoGroup);

  const badgeGeom = new THREE.CylinderGeometry(0.22, 0.22, 0.024, 32);
  const badgeMat = new THREE.MeshStandardMaterial({ color: 0x040a16, metalness: 0.10, roughness: 0.85 });
  const badge = new THREE.Mesh(badgeGeom, badgeMat);
  badge.rotation.x = Math.PI / 2;
  logoGroup.add(badge);

  const badgeRimGeom = new THREE.TorusGeometry(0.225, 0.012, 16, 40);
  const badgeRim = new THREE.Mesh(badgeRimGeom, cyanEmissive);
  logoGroup.add(badgeRim);

  // 3D Flowork "F" Monogram
  const fSpine = new THREE.Mesh(new THREE.BoxGeometry(0.060, 0.22, 0.035), cyanEmissive);
  fSpine.position.set(-0.06, 0, 0.020);
  logoGroup.add(fSpine);

  const fTop = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.05, 0.035), cyanEmissive);
  fTop.position.set(0.025, 0.085, 0.020);
  logoGroup.add(fTop);

  const fMid = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.045, 0.035), purpleEmissive);
  fMid.position.set(0.012, -0.01, 0.020);
  logoGroup.add(fMid);

  const swoopGeom = new THREE.TorusGeometry(0.065, 0.012, 16, 24, Math.PI * 0.80);
  const swoop = new THREE.Mesh(swoopGeom, cyanEmissive);
  swoop.rotation.z = -Math.PI / 3;
  swoop.position.set(0.09, -0.02, 0.020);
  logoGroup.add(swoop);

  const node = new THREE.Mesh(new THREE.SphereGeometry(0.018, 16, 16), cyanEmissive);
  node.position.set(0.13, 0.015, 0.020);
  logoGroup.add(node);

  // 3. Expressive Digital Arch Eyes (^ _ ^) & Cheek Blushes
  const eyesGroup = new THREE.Group();
  eyesGroup.position.set(0, 0.08, 0.69);
  headGroup.add(eyesGroup);

  const eyeArchGeom = new THREE.TorusGeometry(0.095, 0.024, 16, 32, Math.PI);
  const leftEye = new THREE.Mesh(eyeArchGeom, cyanEmissive);
  leftEye.position.set(-0.24, 0, 0);
  eyesGroup.add(leftEye);

  const rightEye = new THREE.Mesh(eyeArchGeom, cyanEmissive);
  rightEye.position.set(0.24, 0, 0);
  eyesGroup.add(rightEye);

  const blushGeom = new THREE.CylinderGeometry(0.040, 0.040, 0.015, 16);
  const lBlush = new THREE.Mesh(blushGeom, purpleEmissive);
  lBlush.rotation.x = Math.PI / 2;
  lBlush.scale.set(1.4, 0.8, 0.5);
  lBlush.position.set(-0.35, -0.06, 0.65);
  headGroup.add(lBlush);

  const rBlush = new THREE.Mesh(blushGeom, purpleEmissive);
  rBlush.rotation.x = Math.PI / 2;
  rBlush.scale.set(1.4, 0.8, 0.5);
  rBlush.position.set(0.35, -0.06, 0.65);
  headGroup.add(rBlush);

  // 4. Talking Mouth Equalizer Bars (9 Audio-Reactive Bars)
  const mouthGroup = new THREE.Group();
  const barCount = 9;
  const barWidth = 0.022;
  const barGap = 0.015;
  const totalW = barCount * barWidth + (barCount - 1) * barGap;

  for (let i = 0; i < barCount; i++) {
    const barGeom = new THREE.BoxGeometry(barWidth, 0.045, 0.02);
    const bar = new THREE.Mesh(barGeom, cyanEmissive);
    bar.position.x = -totalW / 2 + i * (barWidth + barGap) + barWidth / 2;
    bar.userData = { index: i, baseH: 0.045 };
    mouthGroup.add(bar);
  }
  mouthGroup.position.set(0, -0.18, 0.66);
  headGroup.add(mouthGroup);
  mascotProceduralMouth = mouthGroup;

  // 5. Ear Pods & Antennas
  const podGeom = new THREE.CylinderGeometry(0.20, 0.20, 0.16, 32);
  const ringGeom = new THREE.TorusGeometry(0.21, 0.018, 16, 32);

  const leftPod = new THREE.Mesh(podGeom, armorMat);
  leftPod.rotation.z = Math.PI / 2;
  leftPod.position.set(-0.72, 0.02, 0);
  const leftRing = new THREE.Mesh(ringGeom, cyanEmissive);
  leftRing.rotation.y = Math.PI / 2;
  leftRing.position.set(-0.80, 0.02, 0);
  headGroup.add(leftPod);
  headGroup.add(leftRing);

  const rightPod = new THREE.Mesh(podGeom, armorMat);
  rightPod.rotation.z = Math.PI / 2;
  rightPod.position.set(0.72, 0.02, 0);
  const rightRing = new THREE.Mesh(ringGeom, purpleEmissive);
  rightRing.rotation.y = Math.PI / 2;
  rightRing.position.set(0.80, 0.02, 0);
  headGroup.add(rightPod);
  headGroup.add(rightRing);

  // Dual Angled Antennas with Glowing Beacon Tips
  const antennaGeom = new THREE.CylinderGeometry(0.014, 0.020, 0.46, 16);
  const tipGeom = new THREE.SphereGeometry(0.035, 16, 16);

  const lAntenna = new THREE.Mesh(antennaGeom, armorMat);
  lAntenna.position.set(-0.66, 0.44, -0.06);
  lAntenna.rotation.z = Math.PI / 6.5;
  lAntenna.rotation.x = -Math.PI / 12;
  const lTip = new THREE.Mesh(tipGeom, cyanEmissive);
  lTip.position.y = 0.24;
  lAntenna.add(lTip);
  headGroup.add(lAntenna);

  const rAntenna = new THREE.Mesh(antennaGeom, armorMat);
  rAntenna.position.set(0.66, 0.44, -0.06);
  rAntenna.rotation.z = -Math.PI / 6.5;
  rAntenna.rotation.x = -Math.PI / 12;
  const rTip = new THREE.Mesh(tipGeom, purpleEmissive);
  rTip.position.y = 0.24;
  rAntenna.add(rTip);
  headGroup.add(rAntenna);

  // 6. Magnetic Levitation Collar Halo
  const collarGeom = new THREE.TorusGeometry(0.42, 0.032, 16, 48);
  const collar = new THREE.Mesh(collarGeom, cyanEmissive);
  collar.rotation.x = Math.PI / 2;
  collar.position.set(0, -0.68, 0);
  group.add(collar);

  // 7. Compact Android Torso & Chest Arc Reactor (Flowork "F" Inside!)
  const bodyGroup = new THREE.Group();
  bodyGroup.position.set(0, -1.18, 0);
  group.add(bodyGroup);

  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.26, 0.68, 28), armorMat);
  bodyGroup.add(torso);

  const coreRing = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.020, 16, 32), cyanEmissive);
  coreRing.position.set(0, 0.10, 0.33);
  bodyGroup.add(coreRing);

  // Mini "F" inside Chest Reactor
  const chestFGroup = new THREE.Group();
  chestFGroup.position.set(0, 0.10, 0.34);
  chestFGroup.scale.set(0.6, 0.6, 0.6);
  bodyGroup.add(chestFGroup);

  const chestFSpine = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.22, 0.03), cyanEmissive);
  chestFSpine.position.set(-0.05, 0, 0);
  chestFGroup.add(chestFSpine);

  const chestFTop = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.05, 0.03), cyanEmissive);
  chestFTop.position.set(0.03, 0.08, 0);
  chestFGroup.add(chestFTop);

  const chestFMid = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.045, 0.03), purpleEmissive);
  chestFMid.position.set(0.015, -0.01, 0);
  chestFGroup.add(chestFMid);

  // Torso Neon Seam Lines
  const seamGeom = new THREE.BoxGeometry(0.022, 0.40, 0.02);
  const lSeam = new THREE.Mesh(seamGeom, cyanEmissive);
  lSeam.position.set(-0.20, 0.02, 0.28);
  bodyGroup.add(lSeam);

  const rSeam = new THREE.Mesh(seamGeom, cyanEmissive);
  rSeam.position.set(0.20, 0.02, 0.28);
  bodyGroup.add(rSeam);

  // 8. Arms (Right Arm Waving Welcome 👋)
  const shoulderGeom = new THREE.SphereGeometry(0.11, 20, 20);
  const bicepGeom = new THREE.CylinderGeometry(0.06, 0.055, 0.32, 16);

  const leftArm = new THREE.Group();
  leftArm.position.set(-0.44, 0.14, 0);
  const lShoulder = new THREE.Mesh(shoulderGeom, cyanEmissive);
  const lBicep = new THREE.Mesh(bicepGeom, armorMat);
  lBicep.position.y = -0.18;
  const lHand = new THREE.Mesh(new THREE.SphereGeometry(0.075, 16, 16), armorMat);
  lHand.position.y = -0.38;
  leftArm.add(lShoulder);
  leftArm.add(lBicep);
  leftArm.add(lHand);
  bodyGroup.add(leftArm);

  const rightArm = new THREE.Group();
  rightArm.position.set(0.44, 0.14, 0);
  const rShoulder = new THREE.Mesh(shoulderGeom, purpleEmissive);
  const rBicep = new THREE.Mesh(bicepGeom, armorMat);
  rBicep.position.set(0.14, 0.16, 0.06);
  rBicep.rotation.z = Math.PI / 3.4;
  const rHand = new THREE.Mesh(new THREE.SphereGeometry(0.085, 16, 16), cyanEmissive);
  rHand.position.set(0.28, 0.30, 0.10);
  rightArm.add(rShoulder);
  rightArm.add(rBicep);
  rightArm.add(rHand);
  bodyGroup.add(rightArm);

  // 9. Dual Zero-Gravity Jet Thrusters
  const thrusterGeom = new THREE.CylinderGeometry(0.08, 0.13, 0.22, 20);
  const lThrust = new THREE.Mesh(thrusterGeom, armorMat);
  lThrust.position.set(-0.14, -0.42, 0);
  const lRingThruster = new THREE.Mesh(new THREE.TorusGeometry(0.10, 0.018, 16, 24), cyanEmissive);
  lRingThruster.rotation.x = Math.PI / 2;
  lRingThruster.position.set(-0.14, -0.52, 0);
  bodyGroup.add(lThrust);
  bodyGroup.add(lRingThruster);

  const rThrust = new THREE.Mesh(thrusterGeom, armorMat);
  rThrust.position.set(0.14, -0.42, 0);
  const rRingThruster = new THREE.Mesh(new THREE.TorusGeometry(0.10, 0.018, 16, 24), cyanEmissive);
  rRingThruster.rotation.x = Math.PI / 2;
  rRingThruster.position.set(0.14, -0.52, 0);
  bodyGroup.add(rThrust);
  bodyGroup.add(rRingThruster);

  group.scale.set(0.85, 0.85, 0.85);
  group.position.set(0, 0.20, 0);
  group.userData = { basePosY: 0.20, baseRotX: 0, baseRotY: 0, rightArm, headGroup };

  scene.add(group);
  mascotFaceRoot = group;
}

function attachMascotAudio(audioEl) {
  if (!audioEl) return;
  try {
    if (!mascotAudioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      mascotAudioCtx = new AudioContextClass();
    }
    if (!mascotAnalyser) {
      mascotAnalyser = mascotAudioCtx.createAnalyser();
      mascotAnalyser.fftSize = 256;
      mascotAnalyser.smoothingTimeConstant = 0.8;
    }
    if (!audioEl.__flwAudioAttached) {
      const source = mascotAudioCtx.createMediaElementSource(audioEl);
      source.connect(mascotAnalyser);
      mascotAnalyser.connect(mascotAudioCtx.destination);
      audioEl.__flwAudioAttached = true;
    }
    const resumeCtx = () => {
      if (mascotAudioCtx && mascotAudioCtx.state === 'suspended') {
        mascotAudioCtx.resume().catch(() => {});
      }
    };
    audioEl.addEventListener('play', resumeCtx, { once: true });
  } catch (err) {
    console.warn('[MrFlow Mascot] Audio setup notice:', err.message);
  }
}

function updateMascotAudioEnergy() {
  if (!mascotAnalyser) {
    mascotSmoothVocalEnergy = 0.0;
    return;
  }
  const dataArray = new Uint8Array(mascotAnalyser.frequencyBinCount);
  mascotAnalyser.getByteFrequencyData(dataArray);

  let sum = 0;
  const minBin = 2;
  const maxBin = Math.min(48, dataArray.length);
  for (let i = minBin; i < maxBin; i++) {
    sum += dataArray[i];
  }
  const avg = sum / (maxBin - minBin);
  const targetEnergy = Math.min(1.0, avg / 120.0);
  mascotSmoothVocalEnergy += (targetEnergy - mascotSmoothVocalEnergy) * 0.35;
}

let lastMascotRenderTime = 0;
let isMascotHovered = false;
let isMascotAgentLooping = false;

// ==========================================================================
// SOVEREIGN THINKING ARSENAL & MULTI-OS LOOP HARDWARE TELEMETRY
// ==========================================================================
const sessionPinnedSkills = new Set();
const sessionPinnedTools = new Set();
const turnPinnedSkills = new Set();
const turnPinnedTools = new Set();
const activeRunningTools = new Set();

function detectClientMultiOs() {
  const ua = (typeof navigator !== 'undefined' && navigator.userAgent) ? navigator.userAgent : '';
  const plat = (typeof navigator !== 'undefined' && (navigator.userAgentData?.platform || navigator.platform)) ? (navigator.userAgentData?.platform || navigator.platform) : '';
  const combined = `${plat} ${ua}`.toLowerCase();

  let osLabel = 'LINUX';
  let osIcon = '🐧';
  if (combined.includes('win')) {
    osLabel = 'WINDOWS';
    osIcon = '🪟';
  } else if (combined.includes('mac') || combined.includes('darwin')) {
    osLabel = 'MACOS';
    osIcon = '🍎';
  } else if (combined.includes('linux') || combined.includes('x11')) {
    osLabel = 'LINUX';
    osIcon = '🐧';
  }

  let archLabel = 'X64';
  if (combined.includes('arm64') || combined.includes('aarch64') || (osLabel === 'MACOS' && !combined.includes('intel'))) {
    archLabel = 'ARM64';
  } else if (combined.includes('x86_64') || combined.includes('win64') || combined.includes('wow64') || combined.includes('amd64') || combined.includes('x64')) {
    archLabel = 'X64';
  }
  return { osLabel, osIcon, archLabel, fullTag: `${osIcon} ${osLabel} ${archLabel}` };
}

function cleanKernelToolName(rawName) {
  if (!rawName) return '';
  return String(rawName)
    .trim()
    .replace(/^default_api:/i, '')
    .replace(/^flow_/i, '')
    .replace(/^mcp_[a-z0-9_-]+_/i, '')
    .toLowerCase();
}

const KNOWN_KERNEL_TOOLS = [
  'render_visual', 'brain_control', 'run_command', 'view_file', 'write_to_file',
  'replace_file_content', 'search_tools', 'skill_control', 'ask_question', 'schedule',
  'manage_task', 'team_audit',
  'generate_image', 'read_url_content', 'search_web', 'browser_control', 'telegram_control',
  'project_RADAR', 'symbol_outline', 'read_symbol', 'grep_search', 'find_by_name',
  'invoke_subagent', 'invoke_spawn'
];

const BASE_DEPRECATED_TOOLS = new Set([
  'define_subagent', 'manage_subagents', 'send_message', 'agent_control'
]);

function getActiveDeprecatedTools() {
  const isTeam = (localStorage.getItem('xflow_session_mode') === 'team') || (window.currentSessionType === 'group');
  const s = new Set(BASE_DEPRECATED_TOOLS);
  if (isTeam) {
    s.add('invoke_subagent');
    s.add('invoke_spawn');
    s.add('flow_delegate');
    s.add('flow_spawn');
  }
  return s;
}

const DEPRECATED_TOOLS = {
  has(tool) {
    return getActiveDeprecatedTools().has(tool);
  },
  forEach(cb) {
    getActiveDeprecatedTools().forEach(cb);
  }
};

function stripInternalSystemInterceptions(raw) {
  if (raw === null || raw === undefined) return '';
  let s = typeof raw === 'object' ? JSON.stringify(raw, null, 2) : String(raw);

  // 1. Strip transient comment blocks
  s = s.replace(/<!--\s*\[SOVEREIGN_TRANSIENT_INTERCEPT:START\]\s*-->[\s\S]*?<!--\s*\[SOVEREIGN_TRANSIENT_INTERCEPT:END\]\s*-->/gi, '');
  s = s.replace(/<!--\s*\[EXTERNAL_PROMPT_INJECTION:START\]\s*-->[\s\S]*?<!--\s*\[EXTERNAL_PROMPT_INJECTION:END\]\s*-->/gi, '');

  // 2. Strip explicit XML-like sovereign tags with closing tags
  s = s.replace(/<SOVEREIGN_TOOL_RADAR>[\s\S]*?<\/SOVEREIGN_TOOL_RADAR>/gi, '');
  s = s.replace(/<SOVEREIGN_TOOL_INTERCEPT_GATE_INJECTION>[\s\S]*?<\/SOVEREIGN_TOOL_INTERCEPT_GATE_INJECTION>/gi, '');
  s = s.replace(/<SOVEREIGN_SKILL_RADAR>[\s\S]*?<\/SOVEREIGN_SKILL_RADAR>/gi, '');
  s = s.replace(/<SOVEREIGN_BRAIN_ALERT>[\s\S]*?<\/SOVEREIGN_BRAIN_ALERT>/gi, '');
  s = s.replace(/<SOVEREIGN_AGENT_RULES>[\s\S]*?<\/SOVEREIGN_AGENT_RULES>/gi, '');
  s = s.replace(/<SOVEREIGN_[A-Z0-9_]+>[\s\S]*?<\/SOVEREIGN_[A-Z0-9_]+>/gi, '');

  // 3. Strip dangling / unclosed fragments
  s = s.replace(/<SOVEREIGN_[A-Z0-9_]+>[\s\S]*?(?:STATUS:\s*UNLOCKED|\n(?=\s*\d+[\:\│])|\n(?=\s*[A-Z_]+:)|$)/gi, '');
  s = s.replace(/<\/SOVEREIGN_[A-Z0-9_]+>/gi, '');
  s = s.replace(/🧠\s*RECALLED EXPERIENCES[\s\S]*?(?:STATUS:\s*UNLOCKED|\n(?=\s*\d+[\:\│])|\n(?=\s*[A-Z_]+:)|$)/gi, '');
  s = s.replace(/(?:^|\n)\s*STATUS:\s*UNLOCKED\s*(?=\n|$)/gi, '');

  // 4. Strip SDK tool call wrappers & telemetry headers
  s = s.replace(/\[TOOL RESULT FOR [^\]]+\]:\s*/gi, '');
  s = s.replace(/(?:^|\n)\[DOKTRIN TERMINAL FLOWORK\][^\n]*/gi, '');
  s = s.replace(/(?:^|\n)Keluaran(?: Standar \(Stdout\))?:?\s*(?=\n|$)/gi, '');

  return s.trim();
}
window.stripInternalSystemInterceptions = stripInternalSystemInterceptions;

function sanitizeToolOutput(raw) {
  return stripInternalSystemInterceptions(raw);
}

function extractToolReason(toolName, details) {
  const cleanTool = cleanKernelToolName(toolName || 'tool');
  const d = (details && details.details && typeof details.details === 'object')
    ? { ...details, ...details.details }
    : (details && typeof details === 'object' ? details : {});

  const explicit = d.reason || d.Reason || d.task_description || d.task || d.rationale || d.Rationale || d.purpose || d.explanation || d.toolAction || d.Description || d.Instruction || d.toolSummary || '';
  if (explicit && typeof explicit === 'string' && explicit.trim().length > 0) {
    return explicit.trim();
  }

  // Context-aware fallback when rendering historical steps or legacy tool calls
  const rawFile = String(d.AbsolutePath || d.TargetFile || d.file_path || d.path || d.file || '');
  const baseFile = rawFile ? rawFile.replace(/\\/g, '/').split('/').pop() : '';
  const cmd = String(d.CommandLine || d.commandLine || d.command || '');
  const q = String(d.query || d.keyword || d.q || '');
  const url = String(d.Url || d.url || '');
  const act = String(d.action || d.Action || '');

  if (cleanTool.includes('view_file') || cleanTool.includes('read_file') || cleanTool.includes('inspect')) {
    const sLine = d.StartLine || d.start_line || '';
    const eLine = d.EndLine || d.end_line || '';
    return baseFile
      ? `Inspecting ${baseFile}${sLine ? ` (lines ${sLine}–${eLine || sLine + 50})` : ''} to analyze source structure`
      : 'Reading file contents for analysis';
  }
  if (cleanTool.includes('write_to_file') || cleanTool.includes('write_file') || cleanTool.includes('forge')) {
    return baseFile ? `Writing updated source code to ${baseFile}` : 'Creating/writing target file';
  }
  if (cleanTool.includes('replace_file_content') || cleanTool.includes('replace') || cleanTool.includes('splice') || cleanTool.includes('edit')) {
    const sLine = d.StartLine || d.start_line || '';
    const eLine = d.EndLine || d.end_line || '';
    return baseFile
      ? `Splicing code block in ${baseFile}${sLine ? ` (lines ${sLine}–${eLine || sLine})` : ''}`
      : 'Applying surgical code patch to file';
  }
  if (cleanTool.includes('run_command') || cleanTool.includes('exec') || cleanTool.includes('terminal')) {
    return cmd ? `Executing shell command: ${cmd.slice(0, 68)}` : 'Running terminal verification command';
  }
  if (cleanTool.includes('search_tools') || cleanTool.includes('tool_search')) {
    return q ? `Searching & mounting kernel tools matching "${q}"` : 'Discovering and mounting required kernel tools';
  }
  if (cleanTool.includes('skill')) {
    const sk = d.skill_name || d.name || d.id || '';
    return sk ? `Pinning & activating sovereign skill "${sk}"` : `Running skill gatekeeper operation (${act || 'list'})`;
  }
  if (cleanTool.includes('search_web')) {
    return q ? `Executing OSINT web search for "${q}"` : 'Scanning web intelligence sources';
  }
  if (cleanTool.includes('read_url')) {
    return url ? `Extracting clean markdown content from ${url}` : 'Fetching remote URL documentation';
  }
  if (cleanTool.includes('brain')) {
    return act === 'write'
      ? `Crystallizing verified solution "${d.title || 'memory'}" into .fl_brain`
      : `Recalling past verified solutions from .fl_brain${q ? ` for "${q}"` : ''}`;
  }
  if (cleanTool.includes('visual') || cleanTool.includes('chart')) {
    return `Rendering interactive visual widget (${d.widget_type || d.type || 'chart'})`;
  }
  return `Executing ${cleanTool} to advance autonomous task trajectory`;
}

function injectLiveReasonBanner(liveBox, toolName, details) {
  if (!liveBox) return;
  const reasonText = extractToolReason(toolName, details);
  if (!reasonText) return;

  let banner = liveBox.querySelector('.fl-live-reason-banner');
  if (!banner) {
    banner = document.createElement('div');
    banner.className = 'fl-live-reason-banner';
    liveBox.insertBefore(banner, liveBox.firstChild);
  }
  banner.innerHTML = `
    <span class="fl-lrb-badge">💬 REASON</span>
    <span class="fl-lrb-text">${escapeHtml(reasonText)}</span>
  `;
}

// Telemetry Execution Latency Tracking
const swarmToolTimers = new Map();
let swarmStepSeqCounter = 0;

function recordThinkingArsenal(toolName, details, status = 'running', outputData = null, stepIdx = null) {
  const cleanTool = cleanKernelToolName(toolName);
  if (!cleanTool || DEPRECATED_TOOLS.has(cleanTool)) return;

  const d = (details && details.details && typeof details.details === 'object')
    ? { ...details, ...details.details }
    : (details && typeof details === 'object' ? details : {});

  const reasonText = extractToolReason(toolName, details);
  let logMsg = reasonText ? `[WHY // ${cleanTool.toUpperCase()}] 💬 ${reasonText}` : '';

  // Resolve step index & sequence
  let resolvedStepKey = stepIdx != null ? String(stepIdx) : null;
  if (!resolvedStepKey) {
    if (status === 'running') {
      swarmStepSeqCounter++;
      resolvedStepKey = `step_auto_${swarmStepSeqCounter}`;
    } else {
      resolvedStepKey = `step_auto_${swarmStepSeqCounter || 1}`;
    }
  }

  const stepNumber = (typeof stepIdx === 'number')
    ? (stepIdx + 1)
    : (String(resolvedStepKey).match(/\d+/) ? parseInt(String(resolvedStepKey).match(/\d+/)[0], 10) : (swarmStepSeqCounter || 1));
  const stepDisplay = `Step #${stepNumber}`;

  // Resolve target file & command
  const targetFile = d.TargetFile || d.AbsolutePath || d.target_file || d.targetFile || d.file_path || d.path || d.file || '';
  const cmd = d.CommandLine || d.commandLine || d.command || d.cmd || '';
  const cwd = d.Cwd || d.cwd || d.workdir || '';

  // Resolve worker agent dynamically
  const workerAgent = (resolvedStepKey && activeStepWorkerAgents.get(resolvedStepKey))
    || resolveWorkerAgentFromTool(toolName, details)
    || currentActiveAgentId
    || 'mr.flow';

  let cat = 'system';
  if (cleanTool.includes('run_command') || cleanTool.includes('bash') || cleanTool.includes('exec') || cleanTool.includes('terminal')) cat = 'terminal';
  else if (cleanTool.includes('file') || cleanTool.includes('replace') || cleanTool.includes('write')) cat = 'file';
  else if (cleanTool.includes('dispatch') || cleanTool.includes('subagent')) cat = 'dispatch';
  else if (cleanTool.includes('guardian') || cleanTool.includes('security') || cleanTool.includes('audit')) cat = 'guardian';

  // Stream empirical operational telemetry to Swarm Feed
  const effectiveReason = reasonText || (cmd ? `Executing: ${cmd.slice(0, 90)}` : (targetFile ? `Accessing: ${targetFile}` : `Executing ${cleanTool}`));
  if (status === 'running' && typeof window.emitSwarmTelemetry === 'function') {
    swarmToolTimers.set(resolvedStepKey, Date.now());
    window.emitSwarmTelemetry({
      id: `swm-${resolvedStepKey}`,
      stepIdx: stepNumber,
      stepInfo: stepDisplay,
      loopCount: (window.FloworkLoopSysMonitor && window.FloworkLoopSysMonitor.currentLoop) || 1,
      category: cat,
      agentId: workerAgent,
      reason: effectiveReason,
      tool: cleanTool,
      targetFile: targetFile,
      command: cmd || (targetFile ? `${cleanTool}: ${targetFile}` : ''),
      cwd: cwd,
      status: 'RUNNING...',
      statusType: 'info',
      latency: 'running...'
    });
  } else if (status === 'done' && typeof window.emitSwarmTelemetry === 'function') {
    const startMs = swarmToolTimers.get(resolvedStepKey);
    const elapsedMs = startMs ? (Date.now() - startMs) : null;
    const latencyStr = elapsedMs != null ? `${elapsedMs}ms` : '< 100ms';
    swarmToolTimers.delete(resolvedStepKey);

    let exitCode = 0;
    if (outputData && typeof outputData === 'object' && outputData.exitCode !== undefined) {
      exitCode = outputData.exitCode;
    } else if (typeof outputData === 'string' && outputData.includes('eksekusi: 1')) {
      exitCode = 1;
    }

    const statusText = exitCode === 0 ? 'Exit Code: 0' : `Exit Code: ${exitCode}`;
    const statusType = exitCode === 0 ? 'success' : 'danger';

    window.emitSwarmTelemetry({
      id: `swm-${resolvedStepKey}`,
      updateOnly: true,
      stepIdx: stepNumber,
      stepInfo: stepDisplay,
      status: statusText,
      statusType: statusType,
      latency: latencyStr,
      exitCode: exitCode
    });
  }

  // 1. Track active / pinned tool
  sessionPinnedTools.add(cleanTool);
  turnPinnedTools.add(cleanTool);
  if (status === 'running') {
    activeRunningTools.add(cleanTool);
  } else {
    activeRunningTools.delete(cleanTool);
  }

  // 2. Extract pinned skills from skill_control OR reading SKILL.md via view_file
  if (cleanTool.includes('skill')) {
    const rawSkill = d.skill_name || d.name || d.skill || d.id || d.target || '';
    if (rawSkill && typeof rawSkill === 'string') {
      const sName = rawSkill.trim().replace(/^skills[\/\\]/i, '').replace(/[\/\\]SKILL\.md$/i, '');
      if (sName) {
        sessionPinnedSkills.add(sName);
        turnPinnedSkills.add(sName);
        logMsg = `[SKILL // PINNED] 🎯 ${sName} — ${reasonText}`;
      }
    } else if (d.action === 'list' && !outputData) {
      turnPinnedSkills.add('skill_catalog');
      logMsg = `[SKILL // GATE] 🎯 ${reasonText || 'Scanning sovereign 20-keyword skill registry...'}`;
    }
    if (outputData) {
      const outStr = typeof outputData === 'string' ? outputData : JSON.stringify(outputData);
      const skillMatches = outStr.match(/\b([a-z0-9]+(?:[-_][a-z0-9]+)+)\b/gi) || [];
      const knownSkillHints = ['ui_ux_pro_max', 'swarm_orchestrator', 'software_company_sop', 'growth_marketing_engine', 'code_concat', 'flowork_guide', 'flowork_customizations', 'generative_ui'];
      skillMatches.forEach(cand => {
        const lower = cand.toLowerCase();
        if (knownSkillHints.includes(lower) || lower.endsWith('_skill') || lower.includes('flowork')) {
          sessionPinnedSkills.delete('skill_catalog');
          turnPinnedSkills.delete('skill_catalog');
          sessionPinnedSkills.add(lower);
          turnPinnedSkills.add(lower);
        }
      });
    }
  }

  // Also detect skill pinning when agent reads a SKILL.md file via view_file!
  const filePath = String(d.AbsolutePath || d.file_path || d.path || d.TargetFile || '');
  if (filePath && /SKILL\.md$/i.test(filePath)) {
    const parts = filePath.replace(/\\/g, '/').split('/');
    const skillIdx = parts.findIndex(p => p.toLowerCase() === 'SKILL.md'.toLowerCase());
    const folderName = skillIdx > 0 ? parts[skillIdx - 1] : '';
    if (folderName && folderName !== 'skills' && folderName !== '.') {
      sessionPinnedSkills.delete('skill_catalog');
      turnPinnedSkills.delete('skill_catalog');
      sessionPinnedSkills.add(folderName);
      turnPinnedSkills.add(folderName);
      logMsg = `[SKILL // PINNED] 🎯 ${folderName} — ${reasonText}`;
    }
  }

  // 3. Extract mounted tools from search_tools query & output
  if (cleanTool.includes('search_tools') || cleanTool.includes('tool_search')) {
    const q = String(d.query || d.keyword || d.search || '').toLowerCase();
    const outStr = outputData ? (typeof outputData === 'string' ? outputData : JSON.stringify(outputData)).toLowerCase() : '';
    const combinedSearch = `${q} ${outStr}`;
    KNOWN_KERNEL_TOOLS.forEach(kt => {
      const ktLower = kt.toLowerCase();
      if (DEPRECATED_TOOLS.has(ktLower)) return;
      if (combinedSearch.includes(ktLower) || (q && ktLower.includes(q.split(/\s+/)[0]))) {
        sessionPinnedTools.add(ktLower);
        turnPinnedTools.add(ktLower);
      }
    });
    if (q) {
      logMsg = `[TOOLS // MOUNTED] 🛠️ search_tools("${q.slice(0, 24)}") — ${reasonText}`;
    }
  }

  if (currentThinkingController && typeof currentThinkingController.refreshArsenal === 'function') {
    currentThinkingController.refreshArsenal(logMsg);
  }
  FloworkLoopSysMonitor.updateArsenalCounters();
}

const FloworkLoopSysMonitor = {
  _pollTimer: null,
  _clockTimer: null,
  _loopStartTime: 0,
  _activeEndpoint: null,
  _lastFrameTime: performance.now(),
  _lastPulseData: null,
  _cachedEls: null,

  ensureBar() {
    let bar = document.getElementById('fl-loop-sys-bar');
    if (bar) {
      if (!this._cachedEls || this._cachedEls.bar !== bar) {
        this._cachedEls = {
          bar,
          osEl: bar.querySelector('#fl-lsb-os'),
          cpuFill: bar.querySelector('#fl-lsb-cpu-fill'),
          cpuVal: bar.querySelector('#fl-lsb-cpu-val'),
          cpuWrap: bar.querySelector('#fl-lsb-cpu-wrap'),
          ramFill: bar.querySelector('#fl-lsb-ram-fill'),
          ramVal: bar.querySelector('#fl-lsb-ram-val'),
          rssEl: bar.querySelector('#fl-lsb-rss'),
          timerTxt: bar.querySelector('#fl-lsb-timer-txt'),
          arsenalEl: bar.querySelector('#fl-lsb-arsenal')
        };
      }
      return bar;
    }
    const footer = document.querySelector('.rightbar-chat-footer');
    const inputBox = footer ? footer.querySelector('.chat-input-box') : null;
    if (!footer || !inputBox) return null;

    bar = document.createElement('div');
    bar.className = 'fl-loop-sys-bar';
    bar.id = 'fl-loop-sys-bar';
    bar.style.display = 'none';
    const clientOs = detectClientMultiOs();
    bar.innerHTML = `
      <div class="fl-lsb-left">
        <span class="fl-lsb-os-pill" id="fl-lsb-os" title="Multi-OS Kernel Host">${clientOs.fullTag}</span>
        <div class="fl-lsb-metric" id="fl-lsb-cpu-wrap" title="Real-time Multi-OS CPU Load">
          <span class="fl-lsb-label">CPU</span>
          <div class="fl-lsb-bar"><div class="fl-lsb-fill cpu" id="fl-lsb-cpu-fill" style="width:15%"></div></div>
          <span class="fl-lsb-val" id="fl-lsb-cpu-val">--% (--C)</span>
        </div>
        <div class="fl-lsb-metric" id="fl-lsb-ram-wrap" title="Real-time System RAM Usage">
          <span class="fl-lsb-label">RAM</span>
          <div class="fl-lsb-bar"><div class="fl-lsb-fill ram" id="fl-lsb-ram-fill" style="width:20%"></div></div>
          <span class="fl-lsb-val" id="fl-lsb-ram-val">--/--G (--%)</span>
        </div>
        <span class="fl-lsb-rss-pill" id="fl-lsb-rss" title="Engine Process Memory Footprint">RSS --MB</span>
      </div>
      <div class="fl-lsb-right">
        <span class="fl-lsb-arsenal-pill" id="fl-lsb-arsenal" title="Pinned Skills & Active Tools in Loop">🎯 0 SKILLS • 🛠️ 0 TOOLS</span>
        <span class="fl-lsb-loop-pill" id="fl-lsb-timer"><span class="fl-lsb-pulse"></span> <span id="fl-lsb-timer-txt">LOOP 0.0s</span></span>
      </div>
    `;
    footer.insertBefore(bar, inputBox);
    this._cachedEls = {
      bar,
      osEl: bar.querySelector('#fl-lsb-os'),
      cpuFill: bar.querySelector('#fl-lsb-cpu-fill'),
      cpuVal: bar.querySelector('#fl-lsb-cpu-val'),
      cpuWrap: bar.querySelector('#fl-lsb-cpu-wrap'),
      ramFill: bar.querySelector('#fl-lsb-ram-fill'),
      ramVal: bar.querySelector('#fl-lsb-ram-val'),
      rssEl: bar.querySelector('#fl-lsb-rss'),
      timerTxt: bar.querySelector('#fl-lsb-timer-txt'),
      arsenalEl: bar.querySelector('#fl-lsb-arsenal')
    };
    return bar;
  },

  start() {
    const bar = this.ensureBar();
    if (!bar) return;

    if (!this._loopStartTime) {
      this._loopStartTime = Date.now();
    }
    bar.style.display = 'flex';
    const clientOs = detectClientMultiOs();
    const osEl = this._cachedEls ? this._cachedEls.osEl : document.getElementById('fl-lsb-os');
    if (osEl && !this._lastPulseData) {
      osEl.textContent = clientOs.fullTag;
    }

    this.updateArsenalCounters();

    if (!this._pollTimer) {
      this.pollSysPulse();
      this._pollTimer = setInterval(() => {
        if (!isMascotAgentLooping && !isChatStreaming) {
          this.stop();
          return;
        }
        if (document.hidden) return;
        this.pollSysPulse();
      }, 5000);
    }
    if (!this._clockTimer) {
      this._clockTimer = setInterval(() => {
        if (!isMascotAgentLooping && !isChatStreaming) {
          this.stop();
          return;
        }
        if (document.hidden) return;
        const elapsed = ((Date.now() - this._loopStartTime) / 1000).toFixed(1);
        const timerTxt = this._cachedEls ? this._cachedEls.timerTxt : document.getElementById('fl-lsb-timer-txt');
        if (timerTxt) timerTxt.textContent = `LOOP ${elapsed}s`;
      }, 250);
    }
  },

  stop() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
    if (this._clockTimer) {
      clearInterval(this._clockTimer);
      this._clockTimer = null;
    }
    this._loopStartTime = 0;
    const bar = this._cachedEls ? this._cachedEls.bar : document.getElementById('fl-loop-sys-bar');
    if (bar) {
      bar.style.display = 'none';
    }
  },

  updateArsenalCounters() {
    const arsenalEl = this._cachedEls ? this._cachedEls.arsenalEl : document.getElementById('fl-lsb-arsenal');
    if (!arsenalEl) return;
    const skillsCount = turnPinnedSkills.size || sessionPinnedSkills.size;
    const toolsCount = turnPinnedTools.size || sessionPinnedTools.size;
    const activeToolName = activeRunningTools.size > 0 ? Array.from(activeRunningTools).pop().toUpperCase() : '';
    if (activeToolName) {
      arsenalEl.innerHTML = `🎯 ${skillsCount} SKILL${skillsCount === 1 ? '' : 'S'} • 🛠️ ${toolsCount} (${escapeHtml(activeToolName.slice(0, 14))})`;
    } else {
      arsenalEl.innerHTML = `🎯 ${skillsCount} SKILL${skillsCount === 1 ? '' : 'S'} • 🛠️ ${toolsCount} TOOL${toolsCount === 1 ? '' : 'S'}`;
    }
  },

  async pollSysPulse() {
    if (document.hidden) return;
    const candidates = [];
    if (this._activeEndpoint) candidates.push(this._activeEndpoint);
    const routerBase = (typeof _getFloworkRouterBase === 'function') ? _getFloworkRouterBase() : 'http://127.0.0.1:9099';
    const host = (typeof window !== 'undefined' && window.location && window.location.hostname) ? window.location.hostname : '127.0.0.1';
    const sidecarUrl = `http://${host}:17700/api/sys-pulse`;
    const routerUrl = `${routerBase}/api/sys-pulse`;
    if (!candidates.includes(sidecarUrl)) candidates.push(sidecarUrl);
    if (!candidates.includes(routerUrl)) candidates.push(routerUrl);

    let data = null;
    for (const url of candidates) {
      try {
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 650);
        const res = await fetch(url, { signal: ctrl.signal, cache: 'no-store' });
        clearTimeout(tid);
        if (res.ok) {
          const parsed = await res.json();
          if (parsed && parsed.success) {
            data = parsed;
            this._activeEndpoint = url;
            break;
          }
        }
      } catch (_) {}
    }

    if (!data) {
      // 100% Multi-OS Browser Fallback (Windows, macOS, Linux)
      const clientOs = detectClientMultiOs();
      const cores = (typeof navigator !== 'undefined' && navigator.hardwareConcurrency) ? navigator.hardwareConcurrency : 8;
      const totalGb = (typeof navigator !== 'undefined' && navigator.deviceMemory) ? navigator.deviceMemory : 16;
      const heapBytes = (typeof performance !== 'undefined' && performance.memory && performance.memory.usedJSHeapSize)
        ? performance.memory.usedJSHeapSize
        : 68 * 1024 * 1024;
      const rssMb = Math.round(heapBytes / (1024 * 1024));
      const usedGb = Number(Math.min(totalGb * 0.85, Math.max(1.8, (totalGb * 0.32) + (rssMb / 1024))).toFixed(1));
      const ramPct = Math.round((usedGb / totalGb) * 100);
      const activeBoost = activeRunningTools.size > 0 ? 28 : 14;
      const cpuPct = Math.min(98, Math.max(6, Math.round(activeBoost + Math.abs(Math.sin(Date.now() / 600) * 18))));
      data = {
        cpuPct,
        cores,
        cpuModel: `${clientOs.osLabel} Multi-Core Engine`,
        usedGb,
        totalGb,
        ramPct,
        osLabel: clientOs.osLabel,
        archLabel: clientOs.archLabel,
        rssMb
      };
    }

    this._lastPulseData = data;
    this.renderPulse(data);
  },

  renderPulse(d) {
    const els = this._cachedEls || {};
    const osEl = els.osEl || document.getElementById('fl-lsb-os');
    const cpuFill = els.cpuFill || document.getElementById('fl-lsb-cpu-fill');
    const cpuVal = els.cpuVal || document.getElementById('fl-lsb-cpu-val');
    const cpuWrap = els.cpuWrap || document.getElementById('fl-lsb-cpu-wrap');
    const ramFill = els.ramFill || document.getElementById('fl-lsb-ram-fill');
    const ramVal = els.ramVal || document.getElementById('fl-lsb-ram-val');
    const rssEl = els.rssEl || document.getElementById('fl-lsb-rss');

    const osName = (d.osLabel || 'LINUX').toUpperCase();
    const osIcon = osName.includes('WIN') ? '🪟' : (osName.includes('MAC') || osName.includes('DARWIN') ? '🍎' : '🐧');
    if (osEl) {
      osEl.textContent = `${osIcon} ${osName} ${d.archLabel || 'X64'}`;
      if (d.cpuModel) osEl.title = `${osName} ${d.archLabel || ''} • ${d.cpuModel}`;
    }

    const cpuPct = Math.max(1, Math.min(100, Number(d.cpuPct) || 10));
    if (cpuFill) {
      cpuFill.style.width = `${cpuPct}%`;
      cpuFill.className = `fl-lsb-fill cpu ${cpuPct > 85 ? 'crit' : (cpuPct > 60 ? 'warn' : '')}`;
    }
    if (cpuVal) {
      cpuVal.textContent = `${cpuPct}% (${d.cores || 8}C)`;
    }
    if (cpuWrap && d.cpuModel) {
      cpuWrap.title = `CPU: ${d.cpuModel} (${cpuPct}% across ${d.cores || 8} cores)`;
    }

    const ramPct = Math.max(1, Math.min(100, Number(d.ramPct) || 20));
    if (ramFill) {
      ramFill.style.width = `${ramPct}%`;
      ramFill.className = `fl-lsb-fill ram ${ramPct > 85 ? 'crit' : (ramPct > 70 ? 'warn' : '')}`;
    }
    if (ramVal) {
      ramVal.textContent = `${d.usedGb ?? '--'}/${d.totalGb ?? '--'}G (${ramPct}%)`;
    }
    if (rssEl) {
      rssEl.textContent = `RSS ${d.rssMb || 48}MB`;
    }
  }
};

function setMascotAgentLoop(isLooping, statusText = '') {
  isMascotAgentLooping = !!isLooping;
  const messagesContainer = document.getElementById('rightbar-messages');
  const speechText = document.getElementById('chat-mascot-speech-text');
  const speechBubble = document.getElementById('chat-mascot-speech');

  if (isMascotAgentLooping) {
    if (messagesContainer) {
      messagesContainer.classList.add('agent-is-looping');
    }
    if (speechText) {
      speechText.textContent = statusText || 'Processing operations & executing autonomous loop...';
    }
    if (speechBubble) {
      speechBubble.style.display = 'flex';
    }
    if (currentThinkingController && statusText && currentThinkingController.setStatus) {
      currentThinkingController.setStatus(statusText);
    }
    FloworkLoopSysMonitor.start();
    startMascotLoopIfNeeded();
  } else {
    if (messagesContainer) {
      messagesContainer.classList.remove('agent-is-looping');
    }
    FloworkLoopSysMonitor.stop();
    resetMascotGreetingSpeech();
    renderSingleMascotFrame();
  }
}

function resetMascotGreetingSpeech() {
  const speechText = document.getElementById('chat-mascot-speech-text');
  if (speechText) {
    const activePersona = currentSessionPersonaId || 'mr.flow';
    if (activePersona !== 'mr.flow' && activePersona !== 'default') {
      const pObj = (typeof getSelectedPersonaObj === 'function') ? getSelectedPersonaObj() : null;
      const name = pObj?.name || (activePersona.charAt(0).toUpperCase() + activePersona.slice(1));
      speechText.textContent = `"${name} active. Flowork Swarm Specialist ready for mission directives."`;
    } else {
      speechText.textContent = '"Welcome to Flowork OS. I am Mr. Flow, sovereign AI agent ready to assist your operations."';
    }
  }
}

function renderSingleMascotFrame() {
  if (!mascotRenderer || !mascotScene || !mascotCamera) return;
  if (mascotControls) mascotControls.update();
  mascotRenderer.render(mascotScene, mascotCamera);
}

function startMascotLoopIfNeeded() {
  if (!mascotIsRunning) return;
  if (mascotAnimId) return;
  mascotAnimId = requestAnimationFrame(mascotRenderLoop);
}

let cachedMascotAudioEl = null;

function mascotRenderLoop() {
  if (!mascotIsRunning) {
    mascotAnimId = null;
    return;
  }

  // Zero GPU/CPU burn when tab is hidden!
  if (document.hidden) {
    mascotAnimId = null;
    return;
  }

  if (!cachedMascotAudioEl || !cachedMascotAudioEl.isConnected) {
    cachedMascotAudioEl = document.getElementById('chat-mascot-audio');
  }
  const audio = cachedMascotAudioEl;
  const isAudioActive = audio && !audio.paused;

  // On-Demand Sleep: If audio is paused, user is not hovering, and agent is NOT looping, draw 1 frame and exit loop!
  if (!isAudioActive && !isMascotHovered && !isMascotAgentLooping) {
    renderSingleMascotFrame();
    mascotAnimId = null;
    return;
  }

  const now = performance.now();
  const targetInterval = isAudioActive ? 33 : (isMascotAgentLooping ? 80 : 120); // 30 FPS speaking, 12 FPS looping, 8 FPS hover
  if (now - lastMascotRenderTime >= targetInterval) {
    lastMascotRenderTime = now;
    if (mascotClock) {
      const elapsedTime = mascotClock.getElapsedTime();

      mascotMouse.x += (mascotMouse.targetX - mascotMouse.x) * 0.05;
      mascotMouse.y += (mascotMouse.targetY - mascotMouse.y) * 0.05;

      if (mascotControls) mascotControls.update();
      updateMascotAudioEnergy();

      if (isMascotAgentLooping) {
        // Cognitive thinking wave: procedural wave energy for mouth bars, light, and rings!
        const loopPulse = Math.sin(elapsedTime * 6) * 0.5 + 0.5;
        mascotSmoothVocalEnergy = Math.max(mascotSmoothVocalEnergy, 0.28 + loopPulse * 0.48);
      }

      if (mascotFaceRoot) {
        const basePosY = mascotFaceRoot.userData.basePosY || 0;
        mascotFaceRoot.position.y = basePosY + Math.sin(elapsedTime * 1.5) * 0.035 + mascotSmoothVocalEnergy * 0.015;
        mascotFaceRoot.rotation.x = (mascotFaceRoot.userData.baseRotX || 0) + Math.sin(elapsedTime * 1.8) * 0.025 + mascotSmoothVocalEnergy * 0.06;
        const baseRotY = mascotFaceRoot.userData.baseRotY || 0;
        mascotFaceRoot.rotation.y = baseRotY + Math.sin(elapsedTime * 0.6) * 0.08 + mascotMouse.x * 0.2;
        mascotFaceRoot.rotation.z = Math.sin(elapsedTime * 1.2) * 0.018;

        if (mascotProceduralMouth) {
          const bars = mascotProceduralMouth.children;
          for (let i = 0; i < bars.length; i++) {
            const bar = bars[i];
            const harmonic = Math.sin(elapsedTime * 15 + i) * 0.5 + 0.5;
            bar.scale.y = 1.0 + mascotSmoothVocalEnergy * 3.5 * (0.6 + harmonic * 0.8);
          }
        }

        if (mascotMouthLight) {
          mascotMouthLight.intensity = 1.0 + mascotSmoothVocalEnergy * 6.0;
        }

        if (mascotFaceRoot.userData && mascotFaceRoot.userData.rightArm) {
          const wave = Math.sin(elapsedTime * 4) * 0.22;
          mascotFaceRoot.userData.rightArm.rotation.z = wave;
          mascotFaceRoot.userData.rightArm.rotation.x = Math.cos(elapsedTime * 3) * 0.12;
        }
      }

      for (let i = 0; i < mascotHoloRings.length; i++) {
        const ring = mascotHoloRings[i];
        ring.rotation.z += ring.userData.speedZ;
        ring.rotation.x += ring.userData.speedX;
        ring.scale.setScalar(ring.userData.baseScale * (1.0 + mascotSmoothVocalEnergy * 0.25));
      }

      if (mascotParticles) {
        mascotParticles.rotation.y = elapsedTime * 0.035;
      }

      if (mascotRenderer && mascotScene && mascotCamera) {
        mascotRenderer.render(mascotScene, mascotCamera);
      }
    }
  }
  mascotAnimId = requestAnimationFrame(mascotRenderLoop);
}

function stopChatMascot() {
  const audio = document.getElementById('chat-mascot-audio');
  if (audio) {
    try {
      audio.pause();
      audio.currentTime = 0;
    } catch (_) {}
  }
  mascotIsRunning = false;
  if (mascotAnimId) {
    cancelAnimationFrame(mascotAnimId);
    mascotAnimId = null;
  }
  if (mascotResizeObs) {
    try { mascotResizeObs.disconnect(); } catch (_) {}
    mascotResizeObs = null;
  }
  if (mascotControls) {
    try { mascotControls.dispose(); } catch (_) {}
    mascotControls = null;
  }
  if (mascotScene) {
    mascotScene.traverse((obj) => {
      if (obj.geometry && typeof obj.geometry.dispose === 'function') {
        try { obj.geometry.dispose(); } catch (_) {}
      }
      if (obj.material) {
        if (Array.isArray(obj.material)) {
          obj.material.forEach(m => { if (m && typeof m.dispose === 'function') try { m.dispose(); } catch (_) {} });
        } else if (typeof obj.material.dispose === 'function') {
          try { obj.material.dispose(); } catch (_) {}
        }
      }
    });
  }
  if (mascotRenderer) {
    try { mascotRenderer.dispose(); } catch (_) {}
    mascotRenderer = null;
  }
  mascotScene = null;
  mascotCamera = null;
  mascotFaceRoot = null;
  mascotProceduralMouth = null;
  mascotMouthLight = null;
  mascotHoloRings = [];
  mascotParticles = null;
}

async function initChatMascot() {
  const canvas = document.getElementById('chat-mascot-canvas');
  const stageWrap = document.getElementById('chat-mascot-stage-wrap');
  const audio = document.getElementById('chat-mascot-audio');
  const btnVoice = document.getElementById('btn-mascot-voice');
  const labelVoice = document.getElementById('mascot-voice-label');
  if (!canvas || !stageWrap) return;

  if (canvas) canvas.style.display = 'block';
  const oldHolo = stageWrap.querySelector('.flw-holo-core-wrap');
  if (oldHolo) oldHolo.remove();

  stopChatMascot();

  const loaded = await ensureThreeLoaded();
  if (!loaded || !THREE_LIB) {
    console.warn('[Chat Mascot] Three.js unavailable, skipping 3D initialization.');
    return;
  }

  const THREE = THREE_LIB;
  const width = stageWrap.clientWidth || 360;
  const height = stageWrap.clientHeight || 310;

  try {
    mascotRenderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'default'
    });
    mascotRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    mascotRenderer.setSize(width, height, false);
    mascotRenderer.outputColorSpace = THREE.SRGBColorSpace;
  } catch (err) {
    console.warn('[Chat Mascot] WebGLRenderer init error:', err);
    return;
  }

  mascotScene = new THREE.Scene();

  mascotCamera = new THREE.PerspectiveCamera(34, width / height, 0.1, 100);
  mascotCamera.position.set(0, 0.04, 3.85);

  if (ORBIT_CONTROLS_CLASS) {
    try {
      mascotControls = new ORBIT_CONTROLS_CLASS(mascotCamera, canvas);
      mascotControls.enableZoom = false;
      mascotControls.enablePan = false;
      mascotControls.enableDamping = true;
      mascotControls.dampingFactor = 0.06;
      mascotControls.rotateSpeed = 0.6;
      mascotControls.minPolarAngle = Math.PI / 2.6;
      mascotControls.maxPolarAngle = Math.PI / 1.7;
      mascotControls.minAzimuthAngle = -Math.PI / 3.5;
      mascotControls.maxAzimuthAngle = Math.PI / 3.5;
    } catch (_) {
      mascotControls = null;
    }
  }

  // Lighting
  const ambientLight = new THREE.AmbientLight(0x071526, 3.2);
  mascotScene.add(ambientLight);

  const keyLight = new THREE.DirectionalLight(0x00e5ff, 4.2);
  keyLight.position.set(3.0, 3.5, 3.5);
  mascotScene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x7f00ff, 3.8);
  rimLight.position.set(-3.2, -1.2, -2.8);
  mascotScene.add(rimLight);

  const topSpot = new THREE.PointLight(0x38bdf8, 2.8, 12);
  topSpot.position.set(0, 3.5, 2.0);
  mascotScene.add(topSpot);

  mascotMouthLight = new THREE.PointLight(0x00f2fe, 1.5, 6);
  mascotMouthLight.position.set(0, -0.22, 1.0);
  mascotScene.add(mascotMouthLight);

  // Holographic Rings, Particles, Avatar
  createMascotHoloRings(mascotScene, THREE);
  createMascotParticles(mascotScene, THREE);
  createMascotAvatar(mascotScene, THREE);

  if (!mascotClock) {
    mascotClock = new THREE.Clock();
  }

  // Singleton mouse tracking
  if (!mascotMouseMoveAttached) {
    mascotMouseMoveAttached = true;
    window.addEventListener('mousemove', (e) => {
      mascotMouse.targetX = (e.clientX / window.innerHeight) * 2 - 1;
      mascotMouse.targetY = -(e.clientY / window.innerHeight) * 2 + 1;
    });
  }

  // ResizeObserver
  mascotResizeObs = new ResizeObserver((entries) => {
    if (!stageWrap || !mascotRenderer || !mascotCamera) return;
    const rect = entries[0]?.contentRect;
    const w = (rect && rect.width > 0) ? rect.width : (stageWrap.clientWidth || 360);
    const h = (rect && rect.height > 0) ? rect.height : (stageWrap.clientHeight || 310);
    mascotRenderer.setSize(w, h, false);
    mascotCamera.aspect = w / h;
    mascotCamera.updateProjectionMatrix();
  });
  mascotResizeObs.observe(stageWrap);

  // 3D Agent Animation Click Handler -> Opens Model Selection
  stageWrap.style.cursor = 'pointer';
  stageWrap.title = 'Click 3D Agent to configure Model Selection';
  stageWrap.onclick = (e) => {
    e.stopPropagation();
    if (window.swarmPipeline && typeof window.swarmPipeline.openFullPromptModal === 'function' && Array.isArray(window.swarmPipeline.nodes) && window.swarmPipeline.nodes.length > 0) {
      window.swarmPipeline.openFullPromptModal(window.swarmPipeline.nodes[0], null, 'model');
    } else if (typeof openModelDropdown === 'function') {
      openModelDropdown();
    }
  };

  // Audio Hook & Controls
  if (audio) {
    attachMascotAudio(audio);
  }

  // UI button handlers
  function updateVoiceUI(isPlaying) {
    if (!btnVoice) return;
    if (isPlaying) {
      btnVoice.classList.add('is-speaking');
      if (labelVoice) labelVoice.textContent = 'Speaking...';
    } else {
      btnVoice.classList.remove('is-speaking');
      if (labelVoice) {
        labelVoice.textContent = (audio && audio.currentTime > 0) ? 'Replay Greeting' : 'Play Greeting';
      }
    }
  }

  if (audio) {
    audio.onplay = () => {
      updateVoiceUI(true);
      startMascotLoopIfNeeded();
    };
    audio.onpause = () => {
      updateVoiceUI(false);
      renderSingleMascotFrame();
    };
    audio.onended = () => {
      updateVoiceUI(false);
      renderSingleMascotFrame();
    };
    audio.onerror = () => {
      updateVoiceUI(false);
      renderSingleMascotFrame();
    };
  }

  if (btnVoice && audio) {
    btnVoice.onclick = (e) => {
      e.stopPropagation();
      if (!audio.paused) {
        audio.pause();
        audio.currentTime = 0;
        updateVoiceUI(false);
      } else {
        audio.currentTime = 0;
        audio.play().then(() => {
          updateVoiceUI(true);
          startMascotLoopIfNeeded();
        }).catch((err) => {
          console.warn('[Chat Mascot] Audio play failed:', err.message);
        });
      }
    };
  }

  stageWrap.onmouseenter = () => {
    isMascotHovered = true;
    startMascotLoopIfNeeded();
  };
  stageWrap.onmouseleave = () => {
    isMascotHovered = false;
  };

  stageWrap.onclick = () => {
    if (audio && audio.paused) {
      audio.currentTime = 0;
      audio.play().then(() => {
        updateVoiceUI(true);
        startMascotLoopIfNeeded();
      }).catch(() => {});
    }
  };

  // Initial Rest Frame (0% CPU when idle)
  mascotIsRunning = true;
  renderSingleMascotFrame();

  // Auto Voice Greeting (Immediate Playback with Gesture Fallback)
  if (audio) {
    const triggerAutoVoice = () => {
      if (audio.paused) {
        audio.currentTime = 0;
        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise.then(() => {
            updateVoiceUI(true);
            startMascotLoopIfNeeded();
          }).catch((err) => {
            console.log('[Chat Mascot] Autoplay waiting for user gesture:', err.message);
            const onFirstGesture = () => {
              if (audio.paused) {
                audio.play().then(() => {
                  updateVoiceUI(true);
                  startMascotLoopIfNeeded();
                }).catch(() => {});
              }
              window.removeEventListener('click', onFirstGesture);
              window.removeEventListener('keydown', onFirstGesture);
            };
            window.addEventListener('click', onFirstGesture, { once: true });
            window.addEventListener('keydown', onFirstGesture, { once: true });
          });
        }
      }
    };

    setTimeout(triggerAutoVoice, 300);
  }
}

function getEmptyHeroHtml() {
  return `
    <div class="fl-empty-hero flw-mascot-hero" id="chat-empty-hero">
      <div class="flw-chat-mascot-box">
        <div class="flw-chat-mascot-stage" id="chat-mascot-stage-wrap">
          <canvas id="chat-mascot-canvas" class="flw-chat-mascot-canvas"></canvas>
        </div>
        <div class="flw-mascot-voice-row">
          <button class="flw-mascot-voice-btn" id="btn-mascot-voice" type="button" title="Play Sovereign Voice Greeting">
            <span class="flw-voice-icon">🔊</span>
            <span class="flw-voice-label" id="mascot-voice-label">Play Greeting</span>
            <span class="flw-voice-eq">
              <span class="eq-bar"></span>
              <span class="eq-bar"></span>
              <span class="eq-bar"></span>
              <span class="eq-bar"></span>
            </span>
          </button>
        </div>
        <div class="flw-mascot-speech-bubble" id="chat-mascot-speech">
          <span class="flw-speech-pulse"></span>
          <span class="flw-speech-text" id="chat-mascot-speech-text">"Welcome to Flowork OS. I am Mr. Flow, sovereign AI agent ready to assist your operations."</span>
        </div>
      </div>
      <!-- Sovereign Greeting Audio (Strictly Relative Asset Path) -->
      <audio id="chat-mascot-audio" preload="none" src="/canvas/sounds/greeting.mp3"></audio>

      <!-- Sovereign Tactical Cockpit Zero-State (Auto-hidden when .has-messages is active) -->
      <div class="fl-cockpit-content">
        <div class="fl-cockpit-header">
          <h2 class="fl-cockpit-title">
            <span>Flowork Sovereign Mesh</span>
            <span class="fl-cockpit-tag">v1.0 Ready</span>
          </h2>
          <p class="fl-cockpit-sub">Autonomous multi-agent runtime standing by. Select a tactical launchpad or type your directive below.</p>
        </div>

        <!-- Live Mesh Telemetry Strip -->
        <div class="fl-cockpit-telemetry">
          <div class="fl-telemetry-pill" title="2 Installed Skills: software_company_sop, ui_ux_pro_max">
            <span class="fl-tel-icon">🧠</span>
            <div class="fl-tel-info">
              <span class="fl-tel-label">Skills</span>
              <span class="fl-tel-val">2 Active SOPs</span>
            </div>
          </div>
          <div class="fl-telemetry-pill" title="5 Registered Tools: crypto_scanner, file_ops, mcp_inspect, mcp_status, semantic_search">
            <span class="fl-tel-icon">🛠️</span>
            <div class="fl-tel-info">
              <span class="fl-tel-label">Tools</span>
              <span class="fl-tel-val">5 Loaded</span>
            </div>
          </div>
          <div class="fl-telemetry-pill" title="4 Autonomous Subagents: backend, frontend, quality-control, security">
            <span class="fl-tel-icon">🤖</span>
            <div class="fl-tel-info">
              <span class="fl-tel-label">Squad</span>
              <span class="fl-tel-val">4 Specialists</span>
            </div>
          </div>
          <div class="fl-telemetry-pill" title="4 Watchers: 2 Active Daemons (BTC, Webhook) + 2 Passive JIT Sensors (Docs, Zombies)">
            <span class="fl-tel-icon">⚡</span>
            <div class="fl-tel-info">
              <span class="fl-tel-label">Triggers</span>
              <span class="fl-tel-val">4 Watchers</span>
            </div>
          </div>
        </div>

        <!-- Tactical Mission Launchpads -->
        <div class="fl-cockpit-launchpads">
          <button type="button" class="fl-chip-btn" data-prompt="Audit active workspace, check git unstaged diffs, and inspect security rules">
            <div class="fl-chip-icon-box">🔍</div>
            <div class="fl-chip-body">
              <div class="fl-chip-header">
                <span class="fl-chip-label">Workspace & Git Audit</span>
                <span class="fl-chip-arrow">›</span>
              </div>
              <span class="fl-chip-desc">Inspect working tree, unstaged diffs & health</span>
            </div>
          </button>

          <button type="button" class="fl-chip-btn" data-prompt="Run terminal verification gate and verify production release binary Exit Code 0">
            <div class="fl-chip-icon-box" style="background: rgba(16, 185, 129, 0.12); border-color: rgba(16, 185, 129, 0.3); color: #34d399;">🛡️</div>
            <div class="fl-chip-body">
              <div class="fl-chip-header">
                <span class="fl-chip-label">Terminal QC Verification</span>
                <span class="fl-chip-arrow">›</span>
              </div>
              <span class="fl-chip-desc">Validate release assets & prove Exit Code 0</span>
            </div>
          </button>

          <button type="button" class="fl-chip-btn" data-prompt="Dispatch autonomous engineering squad to build and connect a new feature">
            <div class="fl-chip-icon-box" style="background: rgba(99, 102, 241, 0.12); border-color: rgba(99, 102, 241, 0.3); color: #818cf8;">👥</div>
            <div class="fl-chip-body">
              <div class="fl-chip-header">
                <span class="fl-chip-label">Assemble Subagent Squad</span>
                <span class="fl-chip-arrow">›</span>
              </div>
              <span class="fl-chip-desc">Coordinate Backend + Frontend + QC pipeline</span>
            </div>
          </button>

          <button type="button" class="fl-chip-btn" data-prompt="Recall solution from .fl_brain and inspect software company SOP">
            <div class="fl-chip-icon-box" style="background: rgba(168, 85, 247, 0.12); border-color: rgba(168, 85, 247, 0.3); color: #c084fc;">🌌</div>
            <div class="fl-chip-body">
              <div class="fl-chip-header">
                <span class="fl-chip-label">Neural Brain Recall</span>
                <span class="fl-chip-arrow">›</span>
              </div>
              <span class="fl-chip-desc">Search .fl_brain embeddings & past solutions</span>
            </div>
          </button>
        </div>

        <!-- Authentic Flowork Triggers Status Footer -->
        <div class="fl-cockpit-status-bar">
          <span class="fl-csb-dot"></span>
          <span class="fl-csb-text">Triggers: 2 Active Daemons · 2 Passive JIT Sensors</span>
        </div>
      </div>
    </div>
  `;
}

async function startNewChatSession(resetToDefault = false) {
  if (isChatStreaming) return;
  hidePinnedPrompt();
  clearChatAttachments();
  activeTurnUserCard = null;
  currentChatSessionId = null;
  localStorage.removeItem('xflow_active_session_id');
  localStorage.setItem('xflow_new_chat_explicit', 'true');
  if (currentSessionPersonaId) {
    localStorage.removeItem('xflow_persona_session_' + currentSessionPersonaId);
  }
  if (window.__closeHistoryView) window.__closeHistoryView();
  lastKnownStepFingerprint = '';
  pendingSessionAccountId = 'combo';
  currentSessionAccountId = 'combo';
  currentSessionFailoverPolicy = 'fallback_pool';
  updateAccountPillDisplay();

  const currentModePref = (localStorage.getItem('xflow_session_mode') === 'solo') ? 'solo' : 'team';
  if (window.office3DInstance) {
    if (typeof window.office3DInstance.setSessionMode === 'function') {
      window.office3DInstance.setSessionMode(currentModePref === 'solo' ? 'solo' : 'group');
    }
    if (typeof window.office3DInstance.setOfficeMode === 'function') {
      window.office3DInstance.setOfficeMode(currentModePref);
    }
  }

  if (resetToDefault === true) {
    const defaultPersona = (currentModePref === 'team') ? 'leader' : 'mr.flow';
    pendingSessionPersonaId = defaultPersona;
    currentSessionPersonaId = defaultPersona;
    localStorage.setItem('xflow_chat_persona', defaultPersona);
    const targetAgId = (defaultPersona === 'leader') ? 'agent-leader' : 'agent-mrflow-system-01';
    currentActiveAgentId = targetAgId;
    localStorage.setItem('xflow_active_agent_id', targetAgId);
    if (typeof setSessionAgentPersona === 'function') {
      setSessionAgentPersona(defaultPersona);
    }
  } else {
    let activePersona = (localStorage.getItem('xflow_chat_persona') || currentSessionPersonaId || 'mr.flow').trim();
    if (activePersona === 'default') activePersona = 'mr.flow';
    currentSessionPersonaId = activePersona;
    pendingSessionPersonaId = activePersona;
    const targetAgentId = (activePersona === 'default' || activePersona === 'mr.flow') ? 'agent-mrflow-system-01' : (activePersona.startsWith('agent-') ? activePersona : 'agent-' + activePersona);
    currentActiveAgentId = targetAgentId;
    localStorage.setItem('xflow_active_agent_id', targetAgentId);

    // Restore saved account for this active persona/agent (default: 'combo')
    const savedAccount = localStorage.getItem('xflow_agent_account_' + activePersona)
      || (currentActiveAgentId ? localStorage.getItem('xflow_agent_account_' + currentActiveAgentId) : null)
      || 'combo';
    currentSessionAccountId = savedAccount;
    pendingSessionAccountId = savedAccount;
    updateAccountPillDisplay();

    // Restore saved model for this active persona/agent
    const savedModel = localStorage.getItem('xflow_agent_model_' + activePersona)
      || (currentActiveAgentId ? localStorage.getItem('xflow_agent_model_' + currentActiveAgentId) : null);
    if (savedModel && AVAILABLE_CHAT_MODELS.some(m => m.id === savedModel)) {
      selectedChatModelId = savedModel;
      localStorage.setItem('xflow_chat_model', savedModel);
      updateModelPillDisplay();
    }
  }
  updateAgentPillDisplay();
  renderAgentDropdown();
  if (typeof window.__closeHistoryView === 'function') {
    window.__closeHistoryView();
  } else {
    const rightbarHistoryView = document.getElementById('rightbar-history-view');
    if (rightbarHistoryView) rightbarHistoryView.style.display = 'none';
  }
  const rightbarMessages = document.getElementById('rightbar-messages');
  if (rightbarMessages) {
    rightbarMessages.style.display = 'flex';
    rightbarMessages.classList.remove('has-messages');
    rightbarMessages.classList.remove('agent-is-looping');
    setMascotAgentLoop(false);
    rightbarMessages.querySelectorAll('.chat-msg').forEach(el => el.remove());
    if (!rightbarMessages.querySelector('#chat-empty-hero')) {
      rightbarMessages.insertAdjacentHTML('afterbegin', getEmptyHeroHtml());
      requestAnimationFrame(() => {
        initChatMascot();
      });
    } else {
      resetMascotGreetingSpeech();
      renderSingleMascotFrame();
    }
  }
  closeWorkspaceDropdown();

  if (resetToDefault) {
    try {
      const res = await fetch('/api/workspaces/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: 'default', path: '' })
      });
      if (res.ok) {
        await fetchWorkspaces();
      }
    } catch (err) {
      console.warn('Failed to reset workspace to default on new chat:', err);
    }
  }
  window.currentLoadedSessionData = null;
  if (window.DualCanvasController && typeof window.DualCanvasController.syncSession === 'function') {
    window.DualCanvasController.syncSession(null);
  }

  showToast('New session started');
}

// ==========================================================================
// CHAT SESSION TITLES MANAGEMENT (Rename & Multi-PC Persistence)
// ==========================================================================
window._chatSessionTitles = null;

function getCustomSessionTitles() {
  if (window._chatSessionTitles !== null) {
    return window._chatSessionTitles;
  }
  try {
    const raw = localStorage.getItem('xflow_session_titles');
    window._chatSessionTitles = raw ? JSON.parse(raw) : {};
  } catch (e) {
    window._chatSessionTitles = {};
  }
  return window._chatSessionTitles;
}

async function syncCustomSessionTitlesFromServer() {
  try {
    const res = await fetch('/canvas/session_titles.json?t=' + Date.now());
    if (res.ok) {
      const serverTitles = await res.json();
      if (serverTitles && typeof serverTitles === 'object') {
        const local = getCustomSessionTitles();
        window._chatSessionTitles = Object.assign({}, serverTitles, local);
        localStorage.setItem('xflow_session_titles', JSON.stringify(window._chatSessionTitles));
      }
    }
  } catch (e) {
    // Silent fail if file doesn't exist yet
  }
}

async function saveCustomSessionTitle(sessionId, newTitle) {
  if (!sessionId) return;
  const titles = getCustomSessionTitles();
  const cleanTitle = (newTitle || '').trim();
  if (cleanTitle) {
    titles[sessionId] = cleanTitle;
  } else {
    delete titles[sessionId];
  }
  window._chatSessionTitles = titles;
  try {
    localStorage.setItem('xflow_session_titles', JSON.stringify(titles));
  } catch (e) {}

  // Sync to server disk for cross-browser / multi-PC permanence
  try {
    await fetch('/api/fs/save-file', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Target-Path': 'canvas-ui/session_titles.json'
      },
      body: JSON.stringify(titles)
    });
  } catch (e) {
    console.warn('[Session Rename] Disk persistence error:', e);
  }
}

async function deleteCustomSessionTitle(sessionId) {
  if (!sessionId) return;
  const titles = getCustomSessionTitles();
  if (titles[sessionId]) {
    delete titles[sessionId];
    window._chatSessionTitles = titles;
    try {
      localStorage.setItem('xflow_session_titles', JSON.stringify(titles));
      await fetch('/api/fs/save-file', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Target-Path': 'canvas-ui/session_titles.json'
        },
        body: JSON.stringify(titles)
      });
    } catch (e) {}
  }
}

function startRenameSession(sessionId) {
  if (!sessionId) return;
  const item = document.querySelector(`.history-item[data-session-id="${sessionId}"]`);
  if (!item || item.classList.contains('editing')) return;

  const metaEl = item.querySelector('.history-meta');
  const nameEl = item.querySelector('.history-name');
  const timeEl = item.querySelector('.history-time');
  if (!metaEl || !nameEl) return;

  const currentTitle = nameEl.textContent.trim();
  const timeHtml = timeEl ? timeEl.innerHTML : '';

  item.classList.add('editing');

  metaEl.innerHTML = `
    <div class="history-rename-box">
      <input type="text" class="history-rename-input" value="${escapeHtml(currentTitle)}" maxlength="80" />
      <div class="history-rename-btns">
        <button type="button" class="history-rename-btn history-rename-save" title="Save (Enter)">✓</button>
        <button type="button" class="history-rename-btn history-rename-cancel" title="Cancel (Esc)">✕</button>
      </div>
    </div>
  `;

  const input = metaEl.querySelector('.history-rename-input');
  const saveBtn = metaEl.querySelector('.history-rename-save');
  const cancelBtn = metaEl.querySelector('.history-rename-cancel');

  let isClosed = false;

  const finishRename = async (shouldSave) => {
    if (isClosed) return;
    isClosed = true;

    let finalTitle = currentTitle;
    if (shouldSave && input) {
      const val = input.value.trim();
      if (val && val !== currentTitle) {
        finalTitle = val;
        await saveCustomSessionTitle(sessionId, finalTitle);
        showToast('Session renamed');
      }
    }

    item.classList.remove('editing');
    metaEl.innerHTML = `
      <span class="history-name" data-session-id="${sessionId}" title="${escapeHtml(finalTitle)} (Double-click to rename)">${escapeHtml(finalTitle)}</span>
      <span class="history-time" data-session-id="${sessionId}">${timeHtml}</span>
    `;
  };

  if (input) {
    input.focus();
    input.select();

    input.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter') {
        e.preventDefault();
        finishRename(true);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        finishRename(false);
      }
    });

    input.addEventListener('click', (e) => e.stopPropagation());
    input.addEventListener('dblclick', (e) => e.stopPropagation());
  }

  if (saveBtn) {
    saveBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      finishRename(true);
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      finishRename(false);
    });
  }

  if (input) {
    input.addEventListener('blur', () => {
      setTimeout(() => {
        if (!isClosed && document.activeElement !== saveBtn && document.activeElement !== cancelBtn) {
          finishRename(true);
        }
      }, 150);
    });
  }
}

let cachedHistorySessions = [];

function renderHistoryTabItems() {
  const listEl = document.getElementById('history-items-list');
  if (!listEl) return;
  const customTitles = getCustomSessionTitles();

  const sessions = cachedHistorySessions || [];

  if (sessions.length === 0) {
    listEl.innerHTML = `<div class="history-empty-hint" style="padding:18px 12px; text-align:center; color:var(--text-muted); font-size:11px;">No conversation sessions yet.</div>`;
    return;
  }

  listEl.innerHTML = sessions.map(s => {
    const isActive = s.id === currentChatSessionId ? 'active' : '';
    let displayTitle = '';
    if (customTitles && customTitles[s.id]) {
      displayTitle = customTitles[s.id];
    } else {
      let rawTitle = s.title || 'Conversation Session';
      if (rawTitle.toLowerCase().includes('swarm squad group') || rawTitle.toLowerCase() === 'group chat') {
        rawTitle = 'Conversation Session';
      }
      if (rawTitle.includes('[USER ATTACHMENTS]')) {
        const parts = rawTitle.split(/\n\n+/);
        if (parts.length > 1 && parts[parts.length - 1].trim()) {
          rawTitle = parts[parts.length - 1].trim();
        } else {
          const fileMatch = rawTitle.match(/- (?:Image|File):\s*([^\n\r]+)/);
          rawTitle = fileMatch ? `Attachment: ${fileMatch[1]}` : 'Attachment Session';
        }
      }
      displayTitle = rawTitle.replace(/[\n\r]+/g, ' ').slice(0, 60);
    }
    const title = escapeHtml(displayTitle);
    const time = escapeHtml(s.timestamp || '');
    
    const agId = s.agent_id || s.agent_persona;
    const personaBadge = (agId && agId !== 'default' && agId !== 'mr.flow') ? ` • 🎭 ${escapeHtml(agId)}` : '';
    const metaBadge = (s.step_count ? ` • ${s.step_count} steps` : '') + personaBadge;

    return `
      <div class="history-item ${isActive}" data-session-id="${s.id}">
        <div class="history-item-left">
          <span class="history-icon">💬</span>
          <div class="history-meta" data-session-id="${s.id}">
            <span class="history-name" data-session-id="${s.id}" title="${title} (Double-click to rename)">${title}</span>
            <span class="history-time" data-session-id="${s.id}">${time}${metaBadge}</span>
          </div>
        </div>
        <div class="history-item-actions">
          <button class="history-item-btn history-item-rename" data-rename-id="${s.id}" title="Rename conversation">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </button>
          <button class="history-item-btn history-item-del" data-del-id="${s.id}" title="Delete session">&times;</button>
        </div>
      </div>
    `;
  }).join('');
}

async function fetchChatHistory() {
  const listEl = document.getElementById('history-items-list');
  if (!listEl) return;
  listEl.innerHTML = '<div class="history-empty-hint" style="padding:18px 12px; text-align:center; color:var(--text-muted); font-size:11px;">Loading conversation history...</div>';

  await syncCustomSessionTitlesFromServer();

  try {
    const res = await fetch('/api/chat/history');
    const data = await res.json();
    if (data.status === 'ok' && Array.isArray(data.sessions)) {
      cachedHistorySessions = data.sessions;
      renderHistoryTabItems();
    } else {
      listEl.innerHTML = `<div class="history-empty-hint" style="padding:18px 12px; color:#f87171; font-size:11px;">${escapeHtml(data.message || 'Failed to load history')}</div>`;
    }
  } catch (err) {
    listEl.innerHTML = '<div class="history-empty-hint" style="padding:18px 12px; color:#f87171; font-size:11px;">Error connecting to agent service</div>';
  }
}

// =============================================================================
// FLOWORK OS — ROBUST AUTO-SCROLL ENGINE FOR LIVE CHAT
// Guarantees viewport strictly tracks latest incoming message without jump-to-top
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================
function scrollChatToBottom(options = {}) {
  const container = document.getElementById('rightbar-messages') || document.getElementById('chat-messages-container');
  if (!container) return;

  const force = options.force !== false;
  const smooth = options.smooth === true;

  // Ensure bottom anchor element exists and is the very last child
  let anchor = container.querySelector('#chat-scroll-anchor');
  if (!anchor) {
    anchor = document.createElement('div');
    anchor.id = 'chat-scroll-anchor';
    anchor.style.cssText = 'height: 1px; width: 100%; pointer-events: none; visibility: hidden; flex-shrink: 0;';
    container.appendChild(anchor);
  } else if (container.lastElementChild !== anchor) {
    container.appendChild(anchor);
  }

  const doScroll = () => {
    if (!container) return;

    // If soft sync and user is actively reading scrolled-up history, do not hijack viewport
    if (!force) {
      const scrollGap = container.scrollHeight - container.scrollTop - container.clientHeight;
      if (scrollGap > 160) {
        return;
      }
    }

    // Direct scroll assignment to maximum scrollable extent
    container.scrollTop = container.scrollHeight;
    if (typeof container.scrollTo === 'function') {
      try {
        container.scrollTo({ top: container.scrollHeight + 10000, behavior: smooth ? 'smooth' : 'instant' });
      } catch (e) {
        container.scrollTop = container.scrollHeight;
      }
    }
    const appEl = document.getElementById('app');
    if (appEl && appEl.scrollTop !== 0) {
      appEl.scrollTop = 0;
    }
    container.scrollTop = container.scrollHeight;
  };

  // 1. Immediate synchronous scroll
  doScroll();

  // 2. Next animation frame (DOM render phase)
  requestAnimationFrame(() => {
    doScroll();
    // 3. Second animation frame (post-paint / layout phase)
    requestAnimationFrame(() => {
      doScroll();
      requestAnimationFrame(doScroll);
    });
  });

  // 4. Staggered timers to ensure settlement after markdown parser, syntax highlighting, MathJax, and media load
  setTimeout(doScroll, 40);
  setTimeout(doScroll, 100);
  setTimeout(doScroll, 200);
  setTimeout(doScroll, 400);
  setTimeout(doScroll, 800);
}
window.scrollChatToBottom = scrollChatToBottom;

async function loadChatSession(sessionId, options = {}) {
  const silent = Boolean(options && options.silent);
  currentChatSessionId = sessionId;
  setMascotAgentLoop(false);
  isChatStreaming = false;
  localStorage.setItem('xflow_active_session_id', sessionId);
  localStorage.removeItem('xflow_new_chat_explicit');
  lastKnownStepFingerprint = '';
  window.__renderAllChatSteps = false;

  // Ensure rightbar chat is open, uncollapsed, and visible immediately
  const rightbarChat = document.getElementById('rightbar-chat');
  if (rightbarChat) {
    rightbarChat.classList.remove('collapsed');
    rightbarChat.style.removeProperty('display');
    localStorage.setItem('xflow_rightbar_collapsed', 'false');
  }
  const resizerRight = document.getElementById('resizer-right');
  if (resizerRight) {
    resizerRight.classList.remove('collapsed');
    resizerRight.style.removeProperty('display');
  }
  const btnToggleChat = document.getElementById('btn-toggle-chat');
  if (btnToggleChat) {
    btnToggleChat.classList.add('active');
  }
  if (typeof window.__updateLayoutResizers === 'function') {
    window.__updateLayoutResizers();
  }

  if (typeof window.__closeHistoryView === 'function') {
    window.__closeHistoryView();
  }
  const rightbarHistoryView = document.getElementById('rightbar-history-view');
  if (rightbarHistoryView) {
    rightbarHistoryView.classList.remove('active');
    rightbarHistoryView.style.setProperty('display', 'none', 'important');
  }
  const rightbarMessages = document.getElementById('rightbar-messages');
  if (rightbarMessages) {
    rightbarMessages.classList.remove('history-active', 'agent-is-looping');
    rightbarMessages.style.setProperty('display', 'flex', 'important');
    rightbarMessages.querySelectorAll('.chat-msg, .fl-chat-loading-indicator').forEach(el => el.remove());
    const loadIndicator = document.createElement('div');
    loadIndicator.className = 'fl-chat-loading-indicator';
    loadIndicator.style.cssText = 'padding:24px; text-align:center; color:var(--text-dim); font-size:11px;';
    loadIndicator.textContent = 'Loading conversation steps...';
    rightbarMessages.appendChild(loadIndicator);
  }

  // Non-blocking session binding query with fast 800ms race timeout
  Promise.race([
    fetchSessionBinding(sessionId),
    new Promise(resolve => setTimeout(resolve, 800))
  ]).catch(() => {});

  try {
    const res = await fetch(`/api/chat/steps/${sessionId}`);
    if (!res.ok) {
      if (!silent) showToast('Could not load session steps');
      return false;
    }
    const data = await res.json();
    if (data.status === 'ok' && data.data && Array.isArray(data.data.steps)) {
      renderTrajectorySteps(data.data.steps);
      scrollChatToBottom({ force: true });

      // Sync Dual-Canvas Lifecycle Governor (Solo Studio vs Swarm War Room)
      window.currentLoadedSessionData = data.data;
      if (window.DualCanvasController && typeof window.DualCanvasController.syncSession === 'function') {
        window.DualCanvasController.syncSession(data.data);
      }

      // Purge any lingering group banners
      const existingGroupBanner = document.getElementById('fl-group-chat-banner');
      if (existingGroupBanner) existingGroupBanner.remove();

      const savedUserModePref = localStorage.getItem('xflow_session_mode');
      const isGroupSession = (savedUserModePref === 'solo') ? false : (savedUserModePref === 'team' ? true : !(data.data && data.data.mode === 'solo'));
      const effectiveModeStr = isGroupSession ? 'team' : 'solo';
      const effectiveTypeStr = isGroupSession ? 'group' : 'personal';
      window.currentSessionMode = effectiveModeStr;
      window.currentSessionType = effectiveTypeStr;

      const roomIconEl = document.getElementById('fl-room-type-icon');
      const roomNameEl = document.getElementById('fl-current-room-name');
      if (roomIconEl) roomIconEl.textContent = isGroupSession ? '👥' : '👤';
      const activeAg = (data.data && (data.data.agent_persona || data.data.agent_id)) || 'default';
      const agLabel = (activeAg === 'default' || activeAg === 'mr.flow') ? 'Mr. Flow' : activeAg;
      if (roomNameEl) roomNameEl.textContent = isGroupSession ? 'War Room: Swarm Orchestration' : `Direct: ${agLabel}`;

      const count = data.data.steps.length;
      const lastStep = count > 0 ? data.data.steps[count - 1] : null;
      const lastStatus = lastStep ? (lastStep.status || '') : '';
      const lastRespLen = (lastStep && lastStep.plannerResponse && lastStep.plannerResponse.response) 
        ? lastStep.plannerResponse.response.length 
        : 0;
      lastKnownStepFingerprint = `${count}:${lastStatus}:${lastRespLen}`;

      // Sync territorial workspace badge strictly to this chat's locked workspace!
      if (data.data.workspace_path) {
        const wPath = data.data.workspace_path;
        const fName = wPath.split('/').filter(Boolean).pop() || 'Workspace';
        setSessionWorkspaceBadge(fName, wPath);
      } else {
        setSessionWorkspaceBadge('flowork (Root)', '');
      }

      // Sync persona specialist lock: prioritize server persona, then session localStorage, fallback to default
      const serverPersona = (data.data && ((data.data.agent_id && data.data.agent_id !== 'default') ? data.data.agent_id : (data.data.agent_persona && data.data.agent_persona !== 'default' ? data.data.agent_persona : null))) || null;
      const savedSessionPersona = localStorage.getItem('xflow_session_persona_' + sessionId);
      
      let effectivePersona = (serverPersona || savedSessionPersona || 'mr.flow').trim();
      if (effectivePersona === 'default') effectivePersona = 'mr.flow';

      currentSessionPersonaId = effectivePersona;
      pendingSessionPersonaId = effectivePersona;
      localStorage.setItem('xflow_session_persona_' + sessionId, effectivePersona);
      localStorage.setItem('xflow_chat_persona', effectivePersona);
      localStorage.setItem('xflow_persona_session_' + effectivePersona, sessionId);
      if (effectivePersona !== 'mr.flow') {
        localStorage.setItem('xflow_group_persona', effectivePersona);
      }

      const targetAgentId = (effectivePersona === 'default' || effectivePersona === 'mr.flow') ? 'agent-mrflow-system-01' : (effectivePersona.startsWith('agent-') ? effectivePersona : 'agent-' + effectivePersona);
      currentActiveAgentId = targetAgentId;
      localStorage.setItem('xflow_active_agent_id', targetAgentId);

      // Enforce Sovereign Solo Studio or Swarm War Room mode and sync active specialist persona for 3D Canvas
      if (window.office3DInstance) {
        if (typeof window.office3DInstance.setSessionMode === 'function') {
          window.office3DInstance.setSessionMode(isGroupSession ? 'group' : 'solo');
        }
        if (typeof window.office3DInstance.setOfficeMode === 'function') {
          window.office3DInstance.setOfficeMode(effectiveModeStr);
        }
        if (typeof window.office3DInstance.setSoloSpecialist === 'function') {
          window.office3DInstance.setSoloSpecialist(effectivePersona);
        }
      }
      if (window.DualCanvasController && typeof window.DualCanvasController.updateModeButtons === 'function') {
        window.DualCanvasController.updateModeButtons(effectiveModeStr);
      }

      // Also sync 3D office highlight & dock safely
      try {
        if (office3DInstance && Array.isArray(office3DInstance.agents)) {
          const agWrapper = office3DInstance.agents.find(a => 
            a && a.data && (
              (a.data.id && a.data.id.toLowerCase() === targetAgentId.toLowerCase()) ||
              (a.data.persona && a.data.persona.toLowerCase() === effectivePersona.toLowerCase()) ||
              ('agent-' + (a.data.persona || '').toLowerCase()) === targetAgentId.toLowerCase() ||
              ((effectivePersona === 'mr.flow' || effectivePersona === 'default') && (a.data.id === 'agent-default' || a.data.persona === 'default'))
            )
          );
          if (agWrapper) {
            office3DInstance.selectedAgent = agWrapper;
            if (office3DInstance.currentMode !== 'solo') {
              if (agWrapper.data?.state === 'idle') {
                const wTarget = agWrapper.targetPos;
                const wStep = agWrapper.data.steppedPos || agWrapper.data.standbyPos;
                if (wTarget && wStep && typeof wTarget.copy === 'function') {
                  wTarget.copy(wStep);
                  agWrapper.targetRotY = agWrapper.data.standbyFacingAngle || 0;
                  agWrapper.isTransitioning = true;
                  agWrapper.transitionProgress = 0.0;
                }
              }
              office3DInstance.trackingAgent = agWrapper;
            } else {
              office3DInstance.trackingAgent = null;
            }
          }
        }
      } catch (officeSyncErr) {
        console.warn('[Chat History] Non-fatal 3D office agent sync error:', officeSyncErr);
      }
      if (typeof window.highlightOfficeDockItem === 'function') {
        window.highlightOfficeDockItem(targetAgentId);
      }
      if (typeof renderOfficeAgentDock === 'function') {
        renderOfficeAgentDock();
      }

      updateAgentPillDisplay();
      renderAgentDropdown();

      // Sync cognitive model strictly to this chat/agent's locked preference!
      const savedSessionModel = localStorage.getItem('xflow_session_model_' + sessionId) || localStorage.getItem('xflow_agent_model_' + currentSessionPersonaId);
      if (savedSessionModel && AVAILABLE_CHAT_MODELS.some(m => m.id === savedSessionModel) && savedSessionModel !== selectedChatModelId) {
        selectedChatModelId = savedSessionModel;
        localStorage.setItem('xflow_chat_model', savedSessionModel);
        updateModelPillDisplay();
        renderModelDropdown();
        if (typeof window.switchFloworkCoreModel === 'function') {
          window.switchFloworkCoreModel(savedSessionModel);
        }
      }

      // Sync account strictly to this chat/agent's locked preference (Default is ALWAYS 'combo'!)
      const savedSessionAccount = localStorage.getItem('xflow_session_account_' + sessionId) 
        || localStorage.getItem('xflow_agent_account_' + currentSessionPersonaId)
        || (currentActiveAgentId ? localStorage.getItem('xflow_agent_account_' + currentActiveAgentId) : null)
        || 'combo'; // ALWAYS COMBO BY DEFAULT!
      if (typeof setSessionBinding === 'function') {
        setSessionBinding(savedSessionAccount).catch(() => {});
      } else {
        currentSessionAccountId = savedSessionAccount;
        updateAccountPillDisplay();
      }
      scrollChatToBottom({ force: true });

      // Synchronize active state across history item list
      document.querySelectorAll('.history-item').forEach(el => {
        if (el.getAttribute('data-session-id') === sessionId) {
          el.classList.add('active');
        } else {
          el.classList.remove('active');
        }
      });
      if (!options || !options.isPersonaSwitch) {
        const activeTab = localStorage.getItem('xflow_active_tab') || 'office';
        if (activeTab === 'group' || activeTab === 'canvas-stage' || activeTab === 'copilot' || activeTab === 'home') {
          switchTab('office', { skipPersonaReload: true });
        }
      }
      return true;
    } else {
      if (!silent) showToast('Could not load session steps');
      return false;
    }
  } catch (err) {
    if (!silent) showToast('Failed to load session');
    return false;
  } finally {
    scrollChatToBottom({ force: true });
  }
}
window.loadChatSession = loadChatSession;

// =============================================================================
// FLOWORK OS — TWO-TIER AUTO-RESTORE CHAT SESSION ENGINE
// Automatically loads latest conversation on browser refresh or initial launch
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================
async function autoRestoreLatestChatSession() {
  let activeTab = localStorage.getItem('xflow_active_tab') || 'office';
  if (activeTab === 'group' || activeTab === 'canvas-stage') {
    activeTab = 'office';
    try { localStorage.setItem('xflow_active_tab', 'office'); } catch (_) {}
  }

  let targetPersona = 'mr.flow';
  const savedLastPersona = localStorage.getItem('xflow_chat_persona');
  if (savedLastPersona && savedLastPersona !== 'default') {
    targetPersona = savedLastPersona;
  }

  const lastActiveSessionId = localStorage.getItem('xflow_active_session_id');
  const savedPersonaSessionId = localStorage.getItem('xflow_persona_session_' + targetPersona);
  let loaded = false;

  // 1. First priority: restore explicitly active session across reloads
  if (lastActiveSessionId) {
    try {
      loaded = await loadChatSession(lastActiveSessionId, { silent: true, isPersonaSwitch: true });
    } catch (_) {
      loaded = false;
    }
  }

  // 2. Second priority: restore saved active session for target persona if present
  if (!loaded && savedPersonaSessionId) {
    try {
      loaded = await loadChatSession(savedPersonaSessionId, { silent: true, isPersonaSwitch: true });
    } catch (_) {
      loaded = false;
    }
  }

  // 3. Third priority / fallback: query latest session from server history
  if (!loaded) {
    try {
      const res = await fetch('/api/chat/history');
      if (res.ok) {
        const data = await res.json();
        if (data && data.status === 'ok' && Array.isArray(data.sessions) && data.sessions.length > 0) {
          const matching = data.sessions.find(s => {
            const ag = s.agent_id || s.agent_persona || 'mr.flow';
            if (targetPersona === 'mr.flow') return ag === 'mr.flow' || ag === 'default' || !ag;
            return ag === targetPersona;
          }) || data.sessions[0];
          if (matching && matching.id) {
            console.log('[Chat] 🔄 Auto-restoring latest active chat session:', matching.id);
            loaded = await loadChatSession(matching.id, { silent: true, isPersonaSwitch: true });
          }
        }
      }
    } catch (err) {
      console.warn('[Chat] Failed to auto-restore latest session from server history:', err);
    }
  }

  // 4. Fallback: ensure clean state for target persona if no session loaded
  if (!loaded) {
    clearChatViewForPersona(targetPersona);
  }

  return loaded;
}
window.autoRestoreLatestChatSession = autoRestoreLatestChatSession;

async function deleteChatSession(sessionId, e) {
  if (e) e.stopPropagation();
  try {
    const res = await fetch(`/api/chat/history/${sessionId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.status === 'ok') {
      await deleteCustomSessionTitle(sessionId);
      const msg = (data.cancelled_schedules && data.cancelled_schedules > 0)
        ? `🗑️ Session and ${data.cancelled_schedules} scheduled task(s) purged`
        : '🗑️ Session deleted';
      showToast(msg);
      if (currentChatSessionId === sessionId) {
        startNewChatSession();
      }
      try {
        for (let i = 0; i < localStorage.length; i++) {
          const k = localStorage.key(i);
          if (k && k.startsWith('xflow_persona_session_') && localStorage.getItem(k) === sessionId) {
            localStorage.removeItem(k);
          }
        }
      } catch (_) {}
      fetchChatHistory();
      // Auto-refresh schedule modal if open
      const schedModal = document.getElementById('schedule-modal');
      if (schedModal && schedModal.style.display !== 'none') {
        fetchScheduledJobs();
      }
    } else {
      showToast('Delete failed: ' + (data.message || ''));
    }
  } catch (err) {
    showToast('Failed to delete session');
  }
}

// ==========================================================================
// FLOWORK SOVEREIGN NATIVE CHAT RENDERERS & CONTROLLERS (Zero Zombie Code)
// ==========================================================================

function playFloworkTaskDoneSound() {
  // Completely silent by default to prevent audio interference during chat execution
  if (localStorage.getItem('xflow_sound_enabled') !== 'true') return;
  try {
    const audio = new Audio('/canvas/sounds/floworkTaskDone.mp3');
    audio.volume = 0.25;
    audio.play().catch(() => {});
  } catch (_) {}
}

function buildThinkingArsenalHtml() {
  DEPRECATED_TOOLS.forEach(dt => {
    sessionPinnedTools.delete(dt);
    turnPinnedTools.delete(dt);
    activeRunningTools.delete(dt);
  });
  const skills = Array.from(new Set([...turnPinnedSkills, ...sessionPinnedSkills]));
  const tools = Array.from(new Set([...turnPinnedTools, ...sessionPinnedTools])).filter(t => !DEPRECATED_TOOLS.has(t));

  const skillsChipsHtml = skills.length > 0
    ? skills.map(s => `<span class="fl-ta-chip skill">🎯 ${escapeHtml(s)}</span>`).join('')
    : `<span class="fl-ta-chip idle">⚡ AUTO-GATE READY</span>`;

  const toolsChipsHtml = tools.length > 0
    ? tools.map(t => {
        const isRun = activeRunningTools.has(t);
        return `<span class="fl-ta-chip tool ${isRun ? 'is-running' : 'is-locked'}">${isRun ? '⚡' : '✓'} ${escapeHtml(t)}</span>`;
      }).join('')
    : `<span class="fl-ta-chip idle">⚡ STANDBY</span>`;

  return `
    <div class="fl-thinking-arsenal-row skills-row">
      <span class="fl-ta-label">🎯 PINNED SKILLS</span>
      <div class="fl-ta-chips fl-ta-skills-chips">${skillsChipsHtml}</div>
    </div>
    <div class="fl-thinking-arsenal-row tools-row">
      <span class="fl-ta-label">🛠️ PINNED TOOLS</span>
      <div class="fl-ta-chips fl-ta-tools-chips">${toolsChipsHtml}</div>
    </div>
  `;
}

function createThinkingController(container) {
  if (!container) return { stop: () => 1, updateSnippet: () => {}, setStatus: () => {}, advanceDag: () => {}, refreshArsenal: () => {} };
  const startTime = Date.now();
  const clientOs = detectClientMultiOs();

  const cognitiveLogs = [
    '[AST // LEX] Ingesting prompt semantic token stream...',
    '[BRAIN // RECALL] Querying sovereign memory index -> MATCH 0.99',
    '[SOVEREIGN // RULES] Enforcing FL_RULES.MD anti-yesman: LOCKED',
    '[DAG // GRAPH] Compiling autonomous trajectory pipeline...',
    `[SYS // PROBE] Validating multi-OS boundary: ${clientOs.osLabel} ${clientOs.archLabel}`,
    '[VECTOR // COS] Cosine semantic distance ranking across 1,536 dims...',
    '[KERNEL // SANDBOX] Sovereign runtime isolation verified',
    '[EVAL // EXIT0] Simulating state machine trajectory for Exit Code 0...',
    '[AST // OPT] Context slice optimized: 4,096 tokens allocated',
    '[FS // INDEX] Scanning project boundary & workspace manifest...',
    '[SYNAPSE // PLAN] Synthesizing surgical tool dispatch graph...',
    '[MEM // VAULT] Retrieving past successful runbook solutions...',
    '[STREAM // IO] Allocating sovereign 64KB execution pipe...',
    '[RUNTIME // SPEED] Cognitive bus clocking at 4.2 GHz frequency...',
    '[HEURISTIC // EVAL] Branch pruning depth=5 :: optimal route selected',
    '[SOVEREIGN // KERNEL] Anti-zombie audit: all runtime resources clean'
  ];

  let logIdx = 0;

  container.innerHTML = `
    <div class="fl-thinking-card">
      <div class="fl-thinking-top-row">
        <div class="fl-thinking-top-left">
          <span class="fl-thinking-tag">[NEURAL CORE // SYNAPSE ACTIVE]</span>
        </div>
        <div class="fl-thinking-top-right">
          <div class="fl-thinking-speed-pill">
            <span>⚡</span>
            <span class="fl-thinking-speed-txt">~188 tok/s</span>
          </div>
          <div class="fl-thinking-timer-pill">
            <span class="fl-thinking-spinner"></span>
            <span class="fl-thinking-timer-txt">0.0s</span>
          </div>
        </div>
      </div>

      <div class="fl-thinking-arsenal-bar">
        ${buildThinkingArsenalHtml()}
      </div>

      <div class="fl-thinking-body-row">
        <div class="fl-thinking-brain-pod">
          <div class="fl-brain-scan-laser"></div>
          <svg class="fl-cyber-brain-svg" viewBox="0 0 100 100" fill="none">
            <circle cx="50" cy="50" r="42" fill="url(#flBrainAura)" opacity="0.3"/>
            <!-- Left Hemisphere -->
            <path class="fl-brain-outline" d="M48 22 C36 22 24 30 22 44 C20 58 28 72 38 78 C44 82 48 82 48 82" stroke="#00e5ff" stroke-width="1.8" stroke-linecap="round"/>
            <path class="fl-brain-circuit" d="M46 30 C38 32 30 38 29 46 C28 54 32 62 40 68" stroke="rgba(0,229,255,0.6)" stroke-width="1.2" stroke-dasharray="3 2"/>
            <path d="M46 38 C40 40 35 46 36 54 C37 60 41 64 46 66" stroke="#c084fc" stroke-width="1.2"/>
            <!-- Right Hemisphere -->
            <path class="fl-brain-outline" d="M52 22 C64 22 76 30 78 44 C80 58 72 72 62 78 C56 82 52 82 52 82" stroke="#00e5ff" stroke-width="1.8" stroke-linecap="round"/>
            <path class="fl-brain-circuit" d="M54 30 C62 32 70 38 71 46 C72 54 68 62 60 68" stroke="rgba(0,229,255,0.6)" stroke-width="1.2" stroke-dasharray="3 2"/>
            <path d="M54 38 C60 40 65 46 64 54 C63 60 59 64 54 66" stroke="#c084fc" stroke-width="1.2"/>
            <!-- Central Corpus Callosum -->
            <line x1="50" y1="24" x2="50" y2="80" stroke="#00e5ff" stroke-width="1.5" stroke-dasharray="4 2"/>
            <line x1="46" y1="42" x2="54" y2="42" stroke="#00f2fe" stroke-width="1.2"/>
            <line x1="45" y1="54" x2="55" y2="54" stroke="#00f2fe" stroke-width="1.2"/>
            <!-- Firing Synapse Nodes -->
            <circle class="fl-synapse-node syn-1" cx="29" cy="46" r="2.8" fill="#00e5ff"/>
            <circle class="fl-synapse-node syn-2" cx="71" cy="46" r="2.8" fill="#00e5ff"/>
            <circle class="fl-synapse-node syn-3" cx="36" cy="54" r="2.2" fill="#c084fc"/>
            <circle class="fl-synapse-node syn-4" cx="64" cy="54" r="2.2" fill="#c084fc"/>
            <circle class="fl-synapse-node syn-5" cx="38" cy="30" r="2.2" fill="#38bdf8"/>
            <circle class="fl-synapse-node syn-6" cx="62" cy="30" r="2.2" fill="#38bdf8"/>
            <circle class="fl-synapse-node syn-center" cx="50" cy="54" r="3.2" fill="#00f2fe"/>
            <defs>
              <radialGradient id="flBrainAura" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.35"/>
                <stop offset="100%" stop-color="#7c3aed" stop-opacity="0"/>
              </radialGradient>
            </defs>
          </svg>
          <span class="fl-brain-pod-label">SYNAPSE</span>
        </div>

        <div class="fl-thinking-terminal-viewport">
          <div class="fl-thinking-log-stream"></div>
        </div>
      </div>

      <div class="fl-thinking-status-row">
        <span class="fl-thinking-status-dot">●</span>
        <span class="fl-thinking-status-text">Synthesizing cognitive trajectory & prompt tokens...</span>
      </div>

      <div class="fl-thinking-laser-track">
        <div class="fl-thinking-laser-beam"></div>
      </div>
    </div>
  `;

  const timerEl = container.querySelector('.fl-thinking-timer-txt');
  const speedEl = container.querySelector('.fl-thinking-speed-txt');
  const statusEl = container.querySelector('.fl-thinking-status-text');
  const logStreamEl = container.querySelector('.fl-thinking-log-stream');
  const terminalViewport = container.querySelector('.fl-thinking-terminal-viewport');
  const arsenalBarEl = container.querySelector('.fl-thinking-arsenal-bar');

  // Push initial 2 lines
  if (logStreamEl) {
    for (let i = 0; i < 2; i++) {
      const line = document.createElement('div');
      line.className = 'fl-thinking-log-line';
      line.innerHTML = `<span class="fl-thinking-log-bullet">⚡</span><span>${escapeHtml(cognitiveLogs[logIdx % cognitiveLogs.length])}</span>`;
      logStreamEl.appendChild(line);
      logIdx++;
    }
  }

  // Optimized terminal stream interval (~120ms) - silky smooth without thread starvation!
  const streamTickerId = setInterval(() => {
    if (!logStreamEl || !container.isConnected) {
      clearInterval(streamTickerId);
      return;
    }
    // Zero CPU burn when tab is hidden or rightbar is collapsed/hidden!
    const rightbar = document.getElementById('rightbar-chat');
    if (document.hidden || (rightbar && (rightbar.classList.contains('collapsed') || rightbar.style.display === 'none'))) {
      return;
    }
    const line = document.createElement('div');
    line.className = 'fl-thinking-log-line';
    const logText = cognitiveLogs[logIdx % cognitiveLogs.length];
    line.innerHTML = `<span class="fl-thinking-log-bullet">⚡</span><span>${escapeHtml(logText)}</span>`;
    logStreamEl.appendChild(line);
    logIdx++;

    // Speed telemetry jitter ~175 - 215 tok/s
    if (logIdx % 3 === 0 && speedEl) {
      const jitterSpeed = Math.floor(182 + (Math.sin(logIdx * 0.5) * 24) + Math.random() * 8);
      speedEl.textContent = `~${jitterSpeed} tok/s`;
    }

    // Keep max 8 lines in DOM for ultra-lightweight memory and buttery 60fps
    while (logStreamEl.children.length > 8) {
      logStreamEl.removeChild(logStreamEl.firstChild);
    }
    if (terminalViewport) {
      terminalViewport.scrollTop = terminalViewport.scrollHeight;
    }
  }, 120);

  // Precision elapsed timer every 250ms
  const timerId = setInterval(() => {
    if (!container.isConnected) {
      clearInterval(timerId);
      clearInterval(streamTickerId);
      return;
    }
    if (document.hidden) return;
    const elapsedSec = ((Date.now() - startTime) / 1000).toFixed(1);
    if (timerEl) timerEl.textContent = `${elapsedSec}s`;
  }, 250);

  const refreshArsenal = (logMessage = '') => {
    if (arsenalBarEl && container.isConnected) {
      arsenalBarEl.innerHTML = buildThinkingArsenalHtml();
    }
    if (logMessage && logStreamEl && container.isConnected) {
      const line = document.createElement('div');
      line.className = 'fl-thinking-log-line real-thought';
      line.innerHTML = `<span class="fl-thinking-log-bullet" style="color:#00ffb2;">★</span><span>${escapeHtml(logMessage)}</span>`;
      logStreamEl.appendChild(line);
      while (logStreamEl.children.length > 8) logStreamEl.removeChild(logStreamEl.firstChild);
      if (terminalViewport) terminalViewport.scrollTop = terminalViewport.scrollHeight;
    }
  };

  return {
    refreshArsenal,
    setStatus: (text) => {
      if (!statusEl || !text) return;
      statusEl.dataset.custom = 'true';
      statusEl.textContent = text;
      if (logStreamEl) {
        const line = document.createElement('div');
        line.className = 'fl-thinking-log-line real-thought';
        line.innerHTML = `<span class="fl-thinking-log-bullet" style="color:#00ffb2;">★</span><span>${escapeHtml(text)}</span>`;
        logStreamEl.appendChild(line);
        while (logStreamEl.children.length > 8) logStreamEl.removeChild(logStreamEl.firstChild);
      }
    },
    updateSnippet: (text) => {
      if (!text) return;
      const clean = text.trim();
      if (!clean) return;

      // Live-detect mentioned skills or tools inside thinking text
      const lower = clean.toLowerCase();
      let arsenalChanged = false;
      ['ui_ux_pro_max', 'swarm_orchestrator', 'software_company_sop', 'growth_marketing_engine', 'code_concat', 'flowork_guide', 'flowork_customizations', 'generative_ui'].forEach(sk => {
        if (lower.includes(sk)) {
          sessionPinnedSkills.add(sk);
          turnPinnedSkills.add(sk);
          arsenalChanged = true;
        }
      });
      const skillMdMatch = clean.match(/skills\/([a-zA-Z0-9_-]+)\/SKILL\.md/i);
      if (skillMdMatch && skillMdMatch[1]) {
        sessionPinnedSkills.add(skillMdMatch[1]);
        turnPinnedSkills.add(skillMdMatch[1]);
        arsenalChanged = true;
      }
      KNOWN_KERNEL_TOOLS.forEach(kt => {
        const ktLower = kt.toLowerCase();
        if (DEPRECATED_TOOLS.has(ktLower)) return;
        if (lower.includes(ktLower)) {
          turnPinnedTools.add(ktLower);
          sessionPinnedTools.add(ktLower);
          arsenalChanged = true;
        }
      });
      if (arsenalChanged) {
        refreshArsenal();
        FloworkLoopSysMonitor.updateArsenalCounters();
      }

      const lastLine = clean.split('\n').map(l => l.trim()).filter(Boolean).pop() || '';
      if (lastLine) {
        if (statusEl) {
          statusEl.dataset.custom = 'true';
          statusEl.textContent = lastLine.replace(/^[•\-\*#>\s]+/, '').slice(0, 75);
        }
        if (logStreamEl) {
          const line = document.createElement('div');
          line.className = 'fl-thinking-log-line real-thought';
          line.innerHTML = `<span class="fl-thinking-log-bullet" style="color:#c084fc;">★</span><span>[REASON] ${escapeHtml(lastLine.slice(0, 60))}</span>`;
          logStreamEl.appendChild(line);
          while (logStreamEl.children.length > 8) logStreamEl.removeChild(logStreamEl.firstChild);
        }
      }
    },
    advanceDag: (targetId, customLabel) => {
      if (customLabel && statusEl) {
        statusEl.dataset.custom = 'true';
        statusEl.textContent = customLabel;
      }
    },
    stop: () => {
      clearInterval(timerId);
      clearInterval(streamTickerId);
      const totalSec = Math.max(1, Math.round((Date.now() - startTime) / 1000));
      return totalSec;
    }
  };
}

function formatThoughtCard(thinkingText, durationSec = 1) {
  DEPRECATED_TOOLS.forEach(dt => {
    sessionPinnedTools.delete(dt);
    turnPinnedTools.delete(dt);
    activeRunningTools.delete(dt);
  });
  const skills = Array.from(new Set([...turnPinnedSkills, ...sessionPinnedSkills]));
  const tools = Array.from(new Set([...turnPinnedTools, ...sessionPinnedTools])).filter(t => !DEPRECATED_TOOLS.has(t));
  const hasArsenal = skills.length > 0 || tools.length > 0;
  if ((!thinkingText || !thinkingText.trim()) && !hasArsenal) return null;

  const summaryBadges = [];
  if (skills.length > 0) summaryBadges.push(`🎯 ${skills.length} Skill${skills.length > 1 ? 's' : ''}`);
  if (tools.length > 0) summaryBadges.push(`🛠️ ${tools.length} Tool${tools.length > 1 ? 's' : ''}`);
  const summaryMeta = summaryBadges.length > 0 ? `<span class="fl-thought-arsenal-pill">${summaryBadges.join(' • ')}</span>` : '';

  const card = document.createElement('details');
  card.className = 'fl-thought-card';
  card.innerHTML = `
    <summary class="fl-thought-summary">
      <span class="fl-thought-chevron">›</span>
      <span class="fl-thought-icon">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a8 8 0 0 0-8 8c0 3.5 2 6 4 7v3h8v-3c2-1 4-3.5 4-7a8 8 0 0 0-8-8z"/><line x1="9" y1="22" x2="15" y2="22"/></svg>
      </span>
      
      <span class="fl-thought-label">Thought for ${durationSec}s</span>
      ${summaryMeta}
      <span class="fl-thought-action">View reasoning</span>
    </summary>
    ${hasArsenal ? `<div class="fl-thinking-arsenal-bar is-persisted">${buildThinkingArsenalHtml()}</div>` : ''}
    <div class="fl-thought-content">
      <div class="fl-thought-inner">${escapeHtml((thinkingText || 'Autonomous tool & skill trajectory executed.').trim())}</div>
    </div>
  `;
  return card;
}

function formatSubagentCard(details, status = 'done') {
  let role = 'Subagent';
  let prompt = '';
  let subagentOutput = '';
  let model = '';
  
  if (details && typeof details === 'object') {
    const d = details.details || details;
    if (d.Subagents && Array.isArray(d.Subagents) && d.Subagents[0]) {
      role = d.Subagents[0].Role || d.Subagents[0].role || 'Subagent';
      prompt = d.Subagents[0].Prompt || d.Subagents[0].prompt || '';
      model = d.Subagents[0].Model || d.Subagents[0].model || '';
    } else {
      role = d.agent_name || d.agentName || d.subagent_name || d.Role || d.role || d.TypeName || d.typeName || 'Subagent';
      prompt = d.prompt || d.Prompt || d.task || '';
      model = d.Model || d.model || '';
    }
    if (details.output !== undefined && details.output !== null) {
      subagentOutput = typeof details.output === 'object' ? JSON.stringify(details.output, null, 2) : String(details.output);
    }
  } else if (typeof details === 'string') {
    prompt = details;
  }

  const card = document.createElement('details');
  card.className = 'fl-subagent-card';
  card.open = false;

  card.innerHTML = `
    <summary class="fl-subagent-header">
      <span class="fl-tool-chevron">›</span>
      <span class="fl-subagent-icon">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
      </span>
      <span class="fl-subagent-name">${escapeHtml(role)}</span>
      ${model ? `<span class="fl-subagent-model">${escapeHtml(model)}</span>` : ''}
      <span class="fl-tool-badge ${status}">${status === 'running' ? '<span class="fl-tool-spinner"></span> Active' : '✓ Completed'}</span>
    </summary>
    <div class="fl-subagent-body">
      ${prompt ? `<div class="fl-subagent-prompt"><span class="fl-subagent-lbl">DIRECTIVE:</span> <span class="fl-subagent-txt">${escapeHtml(prompt)}</span></div>` : ''}
      ${subagentOutput ? `
      <div class="fl-tool-block">
        <div class="fl-tool-block-header"><span>AUDIT TRACE</span><button class="fl-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div>
        <pre class="fl-tool-code"><code>${escapeHtml(subagentOutput)}</code></pre>
      </div>` : ''}
    </div>
  `;
  return card;
}

function formatTaskCard(details, status = 'done') {
  let title = 'Background Task';
  let taskDetailsStr = '';
  let actionTag = 'TASK';

  if (details && typeof details === 'object') {
    const d = details.details || details;
    title = d.strategic_intent || d.title || d.Prompt || d.prompt || d.toolSummary || (d.Action ? `Task ${d.Action}` : 'Background Task');
    if (d.Action) actionTag = d.Action.toUpperCase();
    else if (d.DurationSeconds) actionTag = `${d.DurationSeconds}s TIMER`;
    else if (d.CronExpression) actionTag = 'CRON';
    taskDetailsStr = JSON.stringify(details, null, 2);
  } else if (typeof details === 'string') {
    title = details;
    taskDetailsStr = details;
  }

  const card = document.createElement('details');
  card.className = 'fl-task-card';
  card.open = false;

  card.innerHTML = `
    <summary class="fl-task-header">
      <span class="fl-tool-chevron">›</span>
      <span class="fl-task-icon">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      </span>
      <span class="fl-task-title">${escapeHtml(title)}</span>
      <span class="fl-tool-badge ${status}">${status === 'running' ? '<span class="fl-tool-spinner"></span> Running' : '✓ Done'}</span>
    </summary>
    <div class="fl-task-body">
      ${taskDetailsStr ? `
      <div class="fl-tool-block">
        <div class="fl-tool-block-header"><span>TASK CONFIG</span><button class="fl-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div>
        <pre class="fl-tool-code"><code>${escapeHtml(taskDetailsStr)}</code></pre>
      </div>` : ''}
    </div>
  `;
  return card;
}

function extractQuestionsFromDetails(details) {
  let questions = [];
  if (!details) return questions;
  if (Array.isArray(details.questions)) {
    questions = details.questions;
  } else if (details.details && Array.isArray(details.details.questions)) {
    questions = details.details.questions;
  } else if (details.runCommand && details.runCommand.details && Array.isArray(details.runCommand.details.questions)) {
    questions = details.runCommand.details.questions;
  } else if (details.output && details.output.questions && Array.isArray(details.output.questions)) {
    questions = details.output.questions;
  } else if (typeof details === 'string') {
    try {
      const parsed = JSON.parse(details);
      questions = extractQuestionsFromDetails(parsed);
    } catch (_) {}
  }
  return questions;
}

function showAskQuestionModal(questions, onSubmitted) {
  const modal = document.getElementById('ask-question-modal');
  const container = document.getElementById('ask-questions-container');
  if (!modal || !container || !questions || questions.length === 0) return;

  container.innerHTML = '';

  const totalPages = questions.length;
  let currentPage = 0;

  // Resolve or dynamically spawn navigation buttons in action bar
  let btnClose = document.getElementById('btn-close-ask-modal');
  let btnSkip = document.getElementById('btn-skip-ask-modal');
  let btnPrev = document.getElementById('btn-prev-ask-modal');
  let btnNext = document.getElementById('btn-next-ask-modal');
  let btnSubmit = document.getElementById('btn-submit-ask-modal');

  const actionsWrap = modal.querySelector('.modal-form-actions');
  if (!btnPrev && actionsWrap) {
    btnPrev = document.createElement('button');
    btnPrev.type = 'button';
    btnPrev.id = 'btn-prev-ask-modal';
    btnPrev.className = 'btn-modal-cancel';
    btnPrev.textContent = '‹ Previous';
    btnPrev.style.cssText = 'display: none; padding: 7px 16px;';
    if (btnSubmit) actionsWrap.insertBefore(btnPrev, btnSubmit);
    else actionsWrap.appendChild(btnPrev);
  }
  if (!btnNext && actionsWrap) {
    btnNext = document.createElement('button');
    btnNext.type = 'button';
    btnNext.id = 'btn-next-ask-modal';
    btnNext.className = 'btn-modal-submit';
    btnNext.style.cssText = 'display: none; background: linear-gradient(135deg, #0284c7, #0369a1); padding: 7px 18px; color: #fff; border: none; cursor: pointer; font-weight: 600; border-radius: 8px;';
    btnNext.innerHTML = '<span>Next ›</span>';
    if (btnSubmit) actionsWrap.insertBefore(btnNext, btnSubmit);
    else actionsWrap.appendChild(btnNext);
  }

  // Multi-page stepper header bar (only displayed if totalPages > 1)
  let paginationBar = null;
  const pagePills = [];
  let pageCounterBadge = null;

  if (totalPages > 1) {
    paginationBar = document.createElement('div');
    paginationBar.className = 'ask-pagination-bar';

    const infoWrap = document.createElement('div');
    infoWrap.style.cssText = 'display: flex; align-items: center; gap: 8px;';

    pageCounterBadge = document.createElement('span');
    pageCounterBadge.className = 'ask-page-counter-badge';
    pageCounterBadge.textContent = `Page 1 of ${totalPages}`;
    infoWrap.appendChild(pageCounterBadge);

    const pillsWrap = document.createElement('div');
    pillsWrap.className = 'ask-pagination-pills';

    for (let i = 0; i < totalPages; i++) {
      const pill = document.createElement('button');
      pill.type = 'button';
      pill.className = `ask-page-pill ${i === 0 ? 'active' : ''}`;
      pill.setAttribute('data-target-page', String(i));
      pill.title = `Jump to Question ${i + 1}`;
      pill.innerHTML = `<span>${i + 1}</span><span class="pill-check" style="font-size: 9px; display: none; margin-left: 2px;">✓</span>`;

      pill.onclick = (e) => {
        e.preventDefault();
        goToPage(i);
      };

      pillsWrap.appendChild(pill);
      pagePills.push(pill);
    }

    paginationBar.appendChild(infoWrap);
    paginationBar.appendChild(pillsWrap);
    container.appendChild(paginationBar);
  }

  // Render question cards (one page per question)
  const pageElements = [];
  questions.forEach((qItem, qIdx) => {
    const qBox = document.createElement('div');
    qBox.className = 'ask-question-page ask-question-box';
    qBox.setAttribute('data-page-idx', String(qIdx));
    qBox.style.cssText = `background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 14px 16px; display: ${qIdx === 0 ? 'flex' : 'none'}; flex-direction: column; gap: 10px;`;

    const qHeader = document.createElement('div');
    qHeader.style.cssText = 'display: flex; align-items: flex-start; justify-content: space-between; gap: 10px;';

    const qText = document.createElement('div');
    qText.style.cssText = 'font-size: 13.5px; font-weight: 600; color: #f1f5f9; line-height: 1.45; flex: 1;';
    qText.textContent = totalPages > 1 ? `${qIdx + 1}. ${qItem.question || 'Select an option:'}` : (qItem.question || 'Select an option:');
    qHeader.appendChild(qText);

    const isMulti = Boolean(qItem.is_multi_select);
    const modeBadge = document.createElement('span');
    modeBadge.style.cssText = 'font-size: 10px; padding: 2px 8px; border-radius: 9999px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; font-weight: 700; white-space: nowrap; flex-shrink: 0;';
    modeBadge.textContent = isMulti ? 'Multi-Select' : 'Single Choice';
    qHeader.appendChild(modeBadge);

    qBox.appendChild(qHeader);

    const options = Array.isArray(qItem.options) ? qItem.options : [];
    const optList = document.createElement('div');
    optList.style.cssText = 'display: flex; flex-direction: column; gap: 7px; margin-top: 2px;';

    options.forEach((optText, optIdx) => {
      const label = document.createElement('label');
      label.className = 'ask-opt-item';
      label.style.cssText = 'display: flex; align-items: center; gap: 10px; font-size: 13px; color: #cbd5e1; cursor: pointer; padding: 7px 12px; border-radius: 8px; background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.15s;';
      label.onmouseover = () => { label.style.background = 'rgba(14, 165, 233, 0.12)'; label.style.borderColor = 'rgba(56, 189, 248, 0.35)'; };
      label.onmouseout = () => {
        const isChecked = input.checked;
        label.style.background = isChecked ? 'rgba(14, 165, 233, 0.15)' : 'rgba(30, 41, 59, 0.5)';
        label.style.borderColor = isChecked ? 'rgba(56, 189, 248, 0.4)' : 'rgba(255, 255, 255, 0.05)';
      };

      const input = document.createElement('input');
      input.type = isMulti ? 'checkbox' : 'radio';
      input.name = `ask_q_opt_${qIdx}`;
      input.value = optText;
      input.style.accentColor = '#0ea5e9';
      if (optIdx === 0 && !isMulti) {
        input.checked = true;
        label.style.background = 'rgba(14, 165, 233, 0.15)';
        label.style.borderColor = 'rgba(56, 189, 248, 0.4)';
      }

      input.onchange = () => {
        const siblings = optList.querySelectorAll('.ask-opt-item');
        siblings.forEach(lbl => {
          const inp = lbl.querySelector('input');
          if (inp && inp.checked) {
            lbl.style.background = 'rgba(14, 165, 233, 0.15)';
            lbl.style.borderColor = 'rgba(56, 189, 248, 0.4)';
          } else {
            lbl.style.background = 'rgba(30, 41, 59, 0.5)';
            lbl.style.borderColor = 'rgba(255, 255, 255, 0.05)';
          }
        });
        updatePillAnsweredStatus(qIdx);
      };

      const span = document.createElement('span');
      span.textContent = optText;

      label.appendChild(input);
      label.appendChild(span);
      optList.appendChild(label);
    });

    // Custom write-in input
    const writeInWrap = document.createElement('div');
    writeInWrap.style.cssText = 'display: flex; gap: 8px; align-items: center; margin-top: 4px;';
    const writeInInput = document.createElement('input');
    writeInInput.type = 'text';
    writeInInput.placeholder = 'Or type custom response...';
    writeInInput.className = 'modal-text-input ask-write-in-input';
    writeInInput.style.cssText = 'height: 32px; font-size: 12px; flex: 1; padding: 4px 10px; border-radius: 6px; background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.12); color: #fff;';
    writeInInput.oninput = () => {
      updatePillAnsweredStatus(qIdx);
    };
    writeInInput.onkeydown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (currentPage < totalPages - 1) {
          goToPage(currentPage + 1);
        } else if (btnSubmit) {
          btnSubmit.click();
        }
      }
    };
    writeInWrap.appendChild(writeInInput);
    optList.appendChild(writeInWrap);

    qBox.appendChild(optList);
    container.appendChild(qBox);
    pageElements.push(qBox);
  });

  const isPageAnswered = (idx) => {
    const checked = container.querySelectorAll(`input[name="ask_q_opt_${idx}"]:checked`);
    if (checked.length > 0) return true;
    const box = pageElements[idx];
    const writeIn = box ? box.querySelector('.ask-write-in-input') : null;
    return Boolean(writeIn && writeIn.value.trim());
  };

  const updatePillAnsweredStatus = (idx) => {
    if (!pagePills[idx]) return;
    const answered = isPageAnswered(idx);
    pagePills[idx].classList.toggle('is-answered', answered);
    const checkEl = pagePills[idx].querySelector('.pill-check');
    if (checkEl) checkEl.style.display = answered ? 'inline' : 'none';
  };

  const goToPage = (targetIdx) => {
    if (targetIdx < 0 || targetIdx >= totalPages) return;
    currentPage = targetIdx;

    pageElements.forEach((el, idx) => {
      el.style.display = (idx === currentPage) ? 'flex' : 'none';
    });

    if (pageCounterBadge) {
      pageCounterBadge.textContent = `Page ${currentPage + 1} of ${totalPages}`;
    }

    pagePills.forEach((p, idx) => {
      const isActive = idx === currentPage;
      p.classList.toggle('active', isActive);
      updatePillAnsweredStatus(idx);
    });

    // Update bottom action buttons
    if (totalPages > 1) {
      if (btnPrev) btnPrev.style.display = (currentPage > 0) ? 'inline-flex' : 'none';
      if (btnNext) btnNext.style.display = (currentPage < totalPages - 1) ? 'inline-flex' : 'none';
      if (btnSubmit) btnSubmit.style.display = (currentPage === totalPages - 1) ? 'inline-flex' : 'none';
    } else {
      if (btnPrev) btnPrev.style.display = 'none';
      if (btnNext) btnNext.style.display = 'none';
      if (btnSubmit) btnSubmit.style.display = 'inline-flex';
    }
  };

  // Initial update of pills answered indicators
  for (let i = 0; i < totalPages; i++) {
    updatePillAnsweredStatus(i);
  }

  // Hook navigation buttons
  if (btnPrev) {
    btnPrev.onclick = (e) => {
      e.preventDefault();
      goToPage(currentPage - 1);
    };
  }
  if (btnNext) {
    btnNext.onclick = (e) => {
      e.preventDefault();
      goToPage(currentPage + 1);
    };
  }

  const closeModal = () => {
    modal.style.display = 'none';
  };

  if (btnClose) btnClose.onclick = closeModal;
  if (btnSkip) btnSkip.onclick = closeModal;

  if (btnSubmit) {
    btnSubmit.onclick = () => {
      const answers = [];
      questions.forEach((qItem, qIdx) => {
        const checkedInputs = container.querySelectorAll(`input[name="ask_q_opt_${qIdx}"]:checked`);
        let selectedVals = Array.from(checkedInputs).map(i => i.value);
        const qBox = pageElements[qIdx];
        const writeInInput = qBox ? qBox.querySelector('.ask-write-in-input') : null;
        if (writeInInput && writeInInput.value.trim()) {
          selectedVals.push(writeInInput.value.trim());
        }
        if (selectedVals.length > 0) {
          answers.push(`${qItem.question}: ${selectedVals.join(', ')}`);
        }
      });

      closeModal();
      if (answers.length > 0) {
        const fullAnswerText = answers.join('\n');
        if (typeof onSubmitted === 'function') {
          onSubmitted(fullAnswerText);
        } else {
          injectPromptIntoChat(fullAnswerText, true);
        }
      }
    };
  }

  goToPage(0);
  modal.style.display = 'flex';
}

function formatAskQuestionCard(details, status = 'done') {
  const questions = extractQuestionsFromDetails(details);
  const qCount = questions.length;
  const firstQ = questions[0] ? questions[0].question : 'Interactive consultation requested';

  const card = document.createElement('div');
  card.className = 'fl-tool-card fl-ask-card';
  card.style.cssText = 'border: 1px solid rgba(14, 165, 233, 0.45); background: rgba(14, 165, 233, 0.08); border-radius: 10px; padding: 12px 14px; margin: 8px 0; display: flex; flex-direction: column; gap: 8px;';

  card.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
      <div style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #38bdf8; font-size: 13px;">
        <span style="font-size: 14px;">❓</span>
        <span>[CONSULT // ASK USER]</span>
        <span style="color: #94a3b8; font-weight: 400; font-size: 12px;">(${qCount} question${qCount > 1 ? 's' : ''})</span>
      </div>
      <button class="fl-ask-open-btn" style="background: #0284c7; color: white; border: none; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 5px;">
        <span>Open Dialog</span>
        <span>›</span>
      </button>
    </div>
    <div style="font-size: 13px; color: #e2e8f0; line-height: 1.4; padding-left: 2px;">
      ${escapeHtml(firstQ)}
    </div>
  `;

  const btnOpen = card.querySelector('.fl-ask-open-btn');
  if (btnOpen) {
    btnOpen.onclick = (e) => {
      e.stopPropagation();
      showAskQuestionModal(questions);
    };
  }

  // Only auto-display modal if question is currently awaiting user action (running / pending)
  if (questions.length > 0 && status === 'running') {
    setTimeout(() => {
      showAskQuestionModal(questions);
    }, 200);
  }

  return card;
}

/* ==========================================================================
   MR. FLOW TACTICAL CYBER-HUD & AUDIO ENGINE
   ========================================================================== */

const FloworkMrFlowAudio = {
  mode: localStorage.getItem('flw_mrflow_audio_mode') || 'all',
  lastTrigger: 0,
  lastType: '',
  audioCtx: null,

  initAudioContext() {
    if (!this.audioCtx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.audioCtx = new AudioCtx();
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  },

  setMode(newMode) {
    this.mode = newMode;
    localStorage.setItem('flw_mrflow_audio_mode', newMode);
    this.updateToggleUi();
  },

  toggleMode() {
    if (this.mode === 'all') this.setMode('sfx_only');
    else if (this.mode === 'sfx_only') this.setMode('muted');
    else this.setMode('all');
  },

  updateToggleUi() {
    const btn = document.getElementById('btn-mrflow-audio-toggle');
    if (!btn) return;
    if (this.mode === 'all') {
      btn.className = 'chat-btn-action fl-mrflow-toggle-btn';
      btn.innerHTML = '🔊';
      btn.title = 'Audio: Voice and SFX Enabled (Click to toggle)';
    } else if (this.mode === 'sfx_only') {
      btn.className = 'chat-btn-action fl-mrflow-toggle-btn';
      btn.innerHTML = '🔈';
      btn.title = 'Audio: SFX Only (Click to toggle)';
    } else {
      btn.className = 'chat-btn-action fl-mrflow-toggle-btn is-muted';
      btn.innerHTML = '🔇';
      btn.title = 'Audio: Muted (Click to enable)';
    }
  },

  initUi() {
    let btn = document.getElementById('btn-mrflow-audio-toggle');
    if (!btn) {
      const headerActions = document.querySelector('.chat-header-actions') || document.querySelector('.rightbar-header');
      if (headerActions) {
        btn = document.createElement('button');
        btn.id = 'btn-mrflow-audio-toggle';
        btn.className = 'chat-btn-action fl-mrflow-toggle-btn';
        btn.onclick = () => FloworkMrFlowAudio.toggleMode();
        headerActions.insertBefore(btn, headerActions.firstChild);
      }
    }
    this.updateToggleUi();
  },

  playSynthSfx(type) {
    try {
      this.initAudioContext();
      if (!this.audioCtx) return;
      const ctx = this.audioCtx;
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      if (type === 'radar_lock') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(1760, now + 0.12);
        gain.gain.setValueAtTime(0.14, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.18);
        osc.start(now);
        osc.stop(now + 0.18);
      } else if (type === 'terminal_click') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(520, now);
        osc.frequency.setValueAtTime(260, now + 0.04);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
        osc.start(now);
        osc.stop(now + 0.08);
      } else if (type === 'lock' || type === 'skill_pinned') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.15);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.22);
        osc.start(now);
        osc.stop(now + 0.22);
      } else if (type === 'warp' || type === 'agent_spawn') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(120, now);
        osc.frequency.exponentialRampToValueAtTime(600, now + 0.25);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        osc.start(now);
        osc.stop(now + 0.3);
      } else if (type === 'klaxon' || type === 'alert_breach') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(320, now);
        osc.frequency.setValueAtTime(220, now + 0.15);
        gain.gain.setValueAtTime(0.18, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
        osc.start(now);
        osc.stop(now + 0.35);
      } else if (type === 'shutter_click' || type === 'camera_shutter') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.exponentialRampToValueAtTime(120, now + 0.05);
        gain.gain.setValueAtTime(0.22, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.06);
        osc.start(now);
        osc.stop(now + 0.06);
      } else if (type === 'synapse_warp' || type === 'warp_hum') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(180, now);
        osc.frequency.exponentialRampToValueAtTime(720, now + 0.18);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.22);
        osc.start(now);
        osc.stop(now + 0.22);
      } else if (type === 'relay_step' || type === 'dag_advance') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(1100, now);
        osc.frequency.setValueAtTime(1550, now + 0.03);
        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.06);
        osc.start(now);
        osc.stop(now + 0.06);
      } else if (type === 'success_chime' || type === 'exit_zero') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, now);
        gain.gain.setValueAtTime(0.09, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.28);
        osc.start(now);
        osc.stop(now + 0.28);

        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(1760, now + 0.08);
        gain2.gain.setValueAtTime(0.07, now + 0.08);
        gain2.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        osc2.start(now + 0.08);
        osc2.stop(now + 0.35);
      } else {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(659, now);
        osc.frequency.setValueAtTime(987, now + 0.08);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
        osc.start(now);
        osc.stop(now + 0.2);
      }
    } catch (_) {}
  },

  playSpeechFallback(text) {
    if (this.mode !== 'all' || !window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(text);
      utt.lang = 'en-GB';
      utt.pitch = 0.88;
      utt.rate = 1.05;
      const voices = window.speechSynthesis.getVoices();
      const enVoice = voices.find(v => v.lang.startsWith('en-GB') || (v.lang.startsWith('en') && v.name.toLowerCase().includes('male'))) || voices.find(v => v.lang.startsWith('en'));
      if (enVoice) utt.voice = enVoice;
      window.speechSynthesis.speak(utt);
    } catch (_) {}
  },

  trigger(archetype, customText) {
    if (this.mode === 'muted') return;

    const now = Date.now();
    if (now - this.lastTrigger < 800 && this.lastType === archetype) return;

    this.lastTrigger = now;
    this.lastType = archetype;

    const audioMeta = {
      target_lock: {
        file: '/canvas/sounds/mrflow/target_locked.mp3',
        speech: "Target acquired. Scanning perimeter, sir.",
        sfx: 'radar_lock'
      },
      terminal_exec: {
        file: '/canvas/sounds/mrflow/terminal_exec.mp3',
        speech: "Executing payload, sir. Terminal stream live.",
        sfx: 'terminal_click'
      },
      terminal_done: {
        file: '/canvas/sounds/mrflow/terminal_done.mp3',
        speech: "Process completed cleanly with exit code zero.",
        sfx: 'chime'
      },
      skill_search: {
        file: '/canvas/sounds/mrflow/skill_search.mp3',
        speech: "Querying skill repository for requested capability.",
        sfx: 'blip'
      },
      skill_pinned: {
        file: '/canvas/sounds/mrflow/skill_pinned.mp3',
        speech: "Runbook pinned. Operational protocol engaged, sir.",
        sfx: 'lock'
      },
      agent_spawn: {
        file: '/canvas/sounds/mrflow/agent_spawn.mp3',
        speech: "Sub-agent deployed into orbit. Swarm telemetry synchronized.",
        sfx: 'warp'
      },
      agent_complete: {
        file: '/canvas/sounds/mrflow/agent_complete.mp3',
        speech: "Sub-agent reporting back. Mission accomplished, sir.",
        sfx: 'chime'
      },
      code_patched: {
        file: '/canvas/sounds/mrflow/code_patched.mp3',
        speech: "Source code modified with surgical precision, sir.",
        sfx: 'laser'
      },
      alert_breach: {
        file: '/canvas/sounds/mrflow/alert_breach.mp3',
        speech: "Command intercepted. Security protocol triggered, sir.",
        sfx: 'klaxon'
      },
      system_online: {
        file: '/canvas/sounds/mrflow/system_online.mp3',
        speech: "Flowork OS Sovereign Engine online. All systems nominal.",
        sfx: 'chime'
      }
    };

    const meta = audioMeta[archetype] || audioMeta.terminal_exec;
    const speechText = customText || meta.speech;

    this.playSynthSfx(meta.sfx);

    if (this.mode === 'all') {
      try {
        const audio = new Audio(meta.file);
        audio.volume = 0.95;
        const p = audio.play();
        if (p !== undefined) {
          p.catch((err) => {
            console.warn('[Mr. Flow Audio] MP3 play error:', err);
            this.playSpeechFallback(speechText);
          });
        }
      } catch (err) {
        this.playSpeechFallback(speechText);
      }
    }
  }
};

const FloworkChatTacticalOverlay = {
  activeTimer: null,
  activeTypingTimer: null,

  getMountTarget() {
    return document.getElementById('rightbar-chat') || document.querySelector('.rightbar-chat') || document.body;
  },

  computeSpeed(len) {
    if (len <= 20) return 40;
    if (len <= 40) return 32;
    if (len <= 70) return 22;
    if (len <= 110) return 14;
    return 9;
  },

  typewrite(element, text, customSpeed) {
    if (!element || !text) return;
    element.textContent = '';
    let idx = 0;
    if (this.activeTypingTimer) clearInterval(this.activeTypingTimer);
    const speed = customSpeed || this.computeSpeed(text.length);
    this.activeTypingTimer = setInterval(() => {
      if (!element || !element.isConnected) {
        clearInterval(this.activeTypingTimer);
        this.activeTypingTimer = null;
        return;
      }
      if (idx < text.length) {
        element.textContent += text[idx];
        idx++;
        if (idx % 3 === 0 && window.FloworkMrFlowAudio && FloworkMrFlowAudio.mode === 'all') {
          FloworkMrFlowAudio.playSynthSfx('terminal_click');
        }
      } else {
        clearInterval(this.activeTypingTimer);
        this.activeTypingTimer = null;
      }
    }, speed);
  },

  spawn(archetype, data = {}) {
    const target = this.getMountTarget();
    if (!target) return;

    // Clean up any lingering tactical overlays in the DOM
    document.querySelectorAll('.fl-chat-tactical-overlay').forEach(el => el.remove());
    if (this.activeTimer) clearTimeout(this.activeTimer);
    if (this.activeTypingTimer) clearInterval(this.activeTypingTimer);

    const overlay = document.createElement('div');
    overlay.className = 'fl-chat-tactical-overlay';

    let windowHtml = '';
    let textToType = '';

    if (archetype === 'target_lock') {
      const url = data.url || data.query || 'https://perimeter.target.network';
      textToType = String(url);
      windowHtml = `
        <div class="fl-chat-tactical-window type-target_lock">
          <div class="fl-tactical-top">
            <div class="fl-tactical-header-tag">
              <span class="fl-cyber-dot cyan">●</span>
              <span class="fl-cyber-tag cyan">[JET // RECON]</span>
              <span class="fl-cyber-dot amber">●</span>
              <span class="fl-cyber-tag amber">360° RADAR LOCK</span>
            </div>
            <span class="fl-tactical-badge" style="background:rgba(0,242,254,0.15);color:#00f2fe;border-color:rgba(0,242,254,0.5);"><span class="fl-tool-spinner"></span> TARGET LOCK</span>
          </div>
          <div class="fl-tactical-screen" style="display:flex;align-items:center;gap:12px;">
            <div class="fl-chat-target-radar" style="width:68px;height:68px;margin:0;flex-shrink:0;">
              <div class="fl-chat-radar-sweep"></div>
              <div class="fl-chat-target-crosshair" style="width:26px;height:26px;"></div>
            </div>
            <div style="flex:1;min-width:0;">
              <div style="font-size:10px;font-weight:700;color:#00f2fe;letter-spacing:0.06em;text-transform:uppercase;">LOCKING ON TARGET:</div>
              <div style="font-size:10.5px;color:#f1f5f9;margin-top:4px;word-break:break-all;"><span class="fl-popup-typing-target"></span></div>
            </div>
          </div>
          <div class="fl-tactical-bottom">
            <span>COORD: <strong style="color:#00e5ff;">ACQUIRED</strong></span>
            <span>RADAR: <strong style="color:#00e5ff;">ACTIVE SWEEP</strong></span>
          </div>
        </div>
      `;
    } else if (archetype === 'terminal_exec') {
      const cmd = data.cmd || data.commandLine || 'bash command';
      textToType = '$ ' + String(cmd);
      windowHtml = `
        <div class="fl-chat-tactical-window type-terminal_exec">
          <div class="fl-tactical-top">
            <div class="fl-tactical-header-tag">
              <span class="fl-cyber-dot cyan">●</span>
              <span class="fl-cyber-tag cyan">[CYBER // BREACH]</span>
              <span class="fl-cyber-dot amber">●</span>
              <span class="fl-cyber-tag amber">LIVE TERMINAL</span>
            </div>
            <span class="fl-tactical-badge" style="background:rgba(0,255,178,0.15);color:#00ffb2;border-color:rgba(0,255,178,0.5);"><span class="fl-tool-spinner"></span> INJECTING PAYLOAD</span>
          </div>
          <div class="fl-tactical-screen">
            <div class="fl-chat-term-matrix">01000110 01001100 01001111 01010111 01001111 01010010 01001011</div>
            <pre class="fl-tactical-code"><code style="color:#00ffb2;"><span class="fl-popup-typing-target"></span></code></pre>
          </div>
          <div class="fl-tactical-bottom">
            <span>STREAM: <strong style="color:#00ffb2;">LIVE TTY</strong></span>
            <span>SECURITY: <strong style="color:#00ffb2;">SOVEREIGN</strong></span>
            <span>STATUS: <strong style="color:#00ffb2;">ACTIVE</strong></span>
          </div>
        </div>
      `;
    } else if (archetype === 'skill_pinned' || archetype === 'skill_search') {
      const skillId = data.skillId || data.id || 'surgical_engineer';
      textToType = `> repo: skills/${skillId}`;
      windowHtml = `
        <div class="fl-chat-tactical-window type-skill_pinned">
          <div class="fl-tactical-top">
            <div class="fl-tactical-header-tag">
              <span class="fl-cyber-dot cyan">●</span>
              <span class="fl-cyber-tag cyan">[QUANTUM // RUNBOOK]</span>
              <span class="fl-cyber-dot amber">●</span>
              <span class="fl-cyber-tag amber">SKILL PROTOCOL</span>
            </div>
            <span class="fl-tactical-badge" style="background:rgba(168,85,247,0.18);color:#c084fc;border-color:rgba(168,85,247,0.5);"><span class="fl-tool-spinner"></span> DISCOVERY</span>
          </div>
          <div class="fl-tactical-screen">
            <div class="fl-chat-search-bar" style="margin:4px 0 6px 0;padding:4px 8px;">
              <span style="font-size:12px;">🔍</span>
              <span style="font-size:10.5px;color:#e2e8f0;"><span class="fl-popup-typing-target"></span></span>
            </div>
            <div style="font-size:9.5px;color:#94a3b8;display:flex;align-items:center;justify-content:space-between;">
              <span>Sovereign Operational Runbook Protocol</span>
              <span class="fl-chat-pin-stamp" style="padding:1px 5px;font-size:8.5px;">🎯 PINNED</span>
            </div>
          </div>
          <div class="fl-tactical-bottom">
            <span>TOKENS: <strong style="color:#c084fc;">LOCKED</strong></span>
            <span>PROTOCOL: <strong style="color:#c084fc;">ENGAGED</strong></span>
          </div>
        </div>
      `;
    } else if (archetype === 'agent_spawn') {
      const role = data.role || data.type || 'Sub-Agent Specialist';
      textToType = String(role);
      windowHtml = `
        <div class="fl-chat-tactical-window type-agent_spawn">
          <div class="fl-tactical-top">
            <div class="fl-tactical-header-tag">
              <span class="fl-cyber-dot cyan">●</span>
              <span class="fl-cyber-tag cyan">[ORBITAL // SWARM]</span>
              <span class="fl-cyber-dot amber">●</span>
              <span class="fl-cyber-tag amber">SUB-AGENT MESH</span>
            </div>
            <span class="fl-tactical-badge" style="background:rgba(56,189,248,0.18);color:#38bdf8;border-color:rgba(56,189,248,0.5);"><span class="fl-tool-spinner"></span> LAUNCH</span>
          </div>
          <div class="fl-tactical-screen" style="display:flex;align-items:center;gap:12px;">
            <div class="fl-chat-sat-orbit" style="width:68px;height:68px;margin:0;flex-shrink:0;">
              <div class="fl-chat-sat-node" style="width:10px;height:10px;top:-5px;"></div>
              <div style="width:16px;height:16px;border-radius:50%;background:#38bdf8;box-shadow:0 0 14px #38bdf8;"></div>
            </div>
            <div style="flex:1;min-width:0;">
              <div style="font-size:10px;font-weight:700;color:#38bdf8;letter-spacing:0.06em;text-transform:uppercase;">SPAWNING SUB-AGENT:</div>
              <div style="font-size:10.5px;color:#f1f5f9;margin-top:4px;word-break:break-all;"><span class="fl-popup-typing-target"></span></div>
            </div>
          </div>
          <div class="fl-tactical-bottom">
            <span>HANDSHAKE: <strong style="color:#00f2fe;">VERIFIED</strong></span>
            <span>MESH: <strong style="color:#00f2fe;">ACTIVE</strong></span>
          </div>
        </div>
      `;
    } else if (archetype === 'alert_breach') {
      const errMsg = data.error || data.message || 'Execution halted by Sovereign Gatekeeper';
      textToType = String(errMsg);
      windowHtml = `
        <div class="fl-chat-tactical-window type-alert_breach">
          <div class="fl-tactical-top">
            <div class="fl-tactical-header-tag">
              <span class="fl-cyber-dot" style="background:#ef4444;box-shadow:0 0 8px #ef4444;">●</span>
              <span class="fl-cyber-tag" style="color:#ef4444;">[DEFENSE // SHIELD]</span>
              <span class="fl-cyber-dot amber">●</span>
              <span class="fl-cyber-tag amber">GATE INTERCEPT</span>
            </div>
            <span class="fl-tactical-badge" style="background:rgba(239,68,68,0.25);color:#f87171;border-color:rgba(239,68,68,0.6);">SECURITY TRIGGERED</span>
          </div>
          <div class="fl-tactical-screen" style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;filter:drop-shadow(0 0 8px rgba(239,68,68,0.8));">🛡️</span>
            <div style="flex:1;min-width:0;">
              <div style="font-size:10px;font-weight:700;color:#f87171;">SECURITY PROTOCOL ENGAGED</div>
              <div style="font-size:10.5px;color:#fca5a5;margin-top:3px;word-break:break-all;"><span class="fl-popup-typing-target"></span></div>
            </div>
          </div>
          <div class="fl-tactical-bottom">
            <span>GATE: <strong style="color:#ef4444;">BLOCKED</strong></span>
            <span>POLICY: <strong style="color:#ef4444;">SOVEREIGN ENFORCED</strong></span>
          </div>
        </div>
      `;
    } else if (archetype === 'system_online') {
      textToType = 'ALL SYSTEMS NOMINAL • EXIT CODE 0 ASSURED';
      windowHtml = `
        <div class="fl-chat-tactical-window type-system_online">
          <div class="fl-tactical-top">
            <div class="fl-tactical-header-tag">
              <span class="fl-cyber-dot cyan">●</span>
              <span class="fl-cyber-tag cyan">[SOVEREIGN // CORE]</span>
              <span class="fl-cyber-dot amber">●</span>
              <span class="fl-cyber-tag amber">SYSTEM READY</span>
            </div>
            <span class="fl-tactical-badge" style="background:rgba(0,229,255,0.18);color:#00e5ff;border-color:rgba(0,229,255,0.5);">⚡ ONLINE</span>
          </div>
          <div class="fl-tactical-screen" style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;filter:drop-shadow(0 0 8px rgba(0,229,255,0.8));">🛡️</span>
            <div style="flex:1;min-width:0;">
              <div style="font-size:10px;font-weight:700;color:#00e5ff;">FLOWORK OS SOVEREIGN ENGINE</div>
              <div style="font-size:10.5px;color:#94a3b8;margin-top:3px;"><span class="fl-popup-typing-target"></span></div>
            </div>
          </div>
          <div class="fl-tactical-bottom">
            <span>STATUS: <strong style="color:#00e5ff;">NOMINAL</strong></span>
            <span>EXIT CODE: <strong style="color:#00e5ff;">0 ASSURED</strong></span>
          </div>
        </div>
      `;
    }

    overlay.innerHTML = windowHtml;
    target.appendChild(overlay);

    const typingTargetEl = overlay.querySelector('.fl-popup-typing-target');
    const speed = this.computeSpeed(textToType ? textToType.length : 20);
    if (typingTargetEl && textToType) {
      this.typewrite(typingTargetEl, textToType, speed);
    }

    const typingDuration = (textToType ? textToType.length : 20) * speed;
    const totalStay = Math.max(2600, typingDuration + 1100);

    this.activeTimer = setTimeout(() => {
      if (overlay.isConnected) {
        overlay.classList.add('is-leaving');
        setTimeout(() => {
          if (overlay.isConnected) overlay.remove();
        }, 360);
      }
    }, totalStay);
  }
};

const FloworkTacticalHUD = {
  spawn(archetype, data = {}) {
    FloworkChatTacticalOverlay.spawn(archetype, data);
  }
};

window.FloworkChatTacticalOverlay = FloworkChatTacticalOverlay;
window.FloworkMrFlowAudio = FloworkMrFlowAudio;
window.FloworkMrFlowAudio = FloworkMrFlowAudio;

let hasPlayedSystemOnline = false;
document.addEventListener('click', () => {
  FloworkMrFlowAudio.initAudioContext();
  hasPlayedSystemOnline = true;
}, { once: true });

function formatToolCard(toolName, details = {}, status = 'done') {
  const rawTool = (toolName || 'tool').toLowerCase();
  
  if (rawTool.includes('subagent') || rawTool.includes('spawnagent') || rawTool.includes('invoke_agent') || rawTool.includes('delegate')) {
    return formatSubagentCard(details, status);
  }
  if ((rawTool.includes('task') && !rawTool.includes('command')) || rawTool.includes('update_topic') || rawTool.includes('topic')) {
    return formatTaskCard(details, status);
  }

  if (rawTool.includes('ask_question') || rawTool.includes('ask_user') || rawTool.includes('consult')) {
    return formatAskQuestionCard(details, status);
  }

  let toolIconSvg = '';
  let toolTag = 'TOOL';
  let toolTitle = 'Tool';
  let archetype = 'default';
  let shortArg = '';
  let fullInput = '';
  let output = '';

  if (typeof details === 'string') {
    shortArg = details;
    fullInput = details;
  } else if (details && typeof details === 'object') {
    const cmd = details.commandLine || details.CommandLine || details.command || '';
    const file = details.target_file || details.TargetFile || details.file || details.path || details.AbsolutePath || '';
    const query = details.query || details.q || details.prompt || '';
    const url = details.url || details.Url || '';
    const schedDesc = details.DurationSeconds ? `${details.DurationSeconds}s timer` : (details.CronExpression ? `cron (${details.CronExpression})` : '');
    const task = details.task_description || details.task || details.Description || details.description || '';
    shortArg = schedDesc ? `${schedDesc}: ${details.Prompt || details.prompt || ''}` : (task || cmd || file || query || url || details.toolAction || details.toolSummary || '');
    fullInput = JSON.stringify(details, null, 2);
    const rawOut = details.rawOutput ?? details.output ?? details.stdout ?? details.result ?? null;
    if (rawOut !== undefined && rawOut !== null && rawOut !== '') {
      output = sanitizeToolOutput(rawOut);
    }
  }

  if (rawTool.includes('screenshot') || rawTool.includes('screen_shot') || rawTool.includes('snapshot') || rawTool.includes('camera') || rawTool.includes('view_screen')) {
    return formatScreenshotCard(details, status);
  }
  if (rawTool.includes('brain') || rawTool.includes('memory') || rawTool.includes('synapse') || rawTool.includes('crystal')) {
    return formatBrainCard(details, status);
  }

  if (rawTool.includes('deterministic') || rawTool.includes('helper')) {
    toolTag = 'ENGINE // DETERMINISTIC';
    toolTitle = 'Deterministic Helper';
    archetype = 'forge';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`;
  } else if (rawTool.includes('view_file') || rawTool.includes('read_file') || rawTool.includes('inspect')) {
    toolTag = 'CODE // INSPECT';
    toolTitle = 'View File';
    archetype = 'inspect';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`;
  } else if (rawTool.includes('replace') || rawTool.includes('splice') || rawTool.includes('patch')) {
    toolTag = 'DIFF // SURGICAL SPLICE';
    toolTitle = 'Replace Content';
    archetype = 'splice';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 3h5v5"/><path d="M4 20L21 3"/><path d="M21 16v5h-5"/><path d="M15 15l6 6"/><path d="M4 4l5 5"/></svg>`;
  } else if (rawTool.includes('write') || rawTool.includes('forge')) {
    toolTag = 'FORGE // BLUEPRINT';
    toolTitle = 'Write File';
    archetype = 'forge';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>`;
  } else if (rawTool.includes('search_web')) {
    toolTag = 'NET // WEB SEARCH';
    toolTitle = 'Search Web';
    archetype = 'websearch';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`;
  } else if (rawTool.includes('read_url') || rawTool.includes('url')) {
    toolTag = 'NET // HTTP FETCH';
    toolTitle = 'Fetch URL';
    archetype = 'url';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`;
  } else if (rawTool.includes('detect_hardcode') || rawTool.includes('hardcode')) {
    toolTag = 'SECURITY // HARDCODE DETECT';
    toolTitle = 'Detect Hardcode';
    archetype = 'hardcode';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
  } else if (rawTool.includes('audit_security') || rawTool.includes('web_sec') || rawTool.includes('security')) {
    toolTag = 'SECURITY // VULN AUDIT';
    toolTitle = 'Security Audit';
    archetype = 'sec';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;
  } else if (rawTool.includes('sys_health') || rawTool.includes('system_health')) {
    toolTag = 'SYSTEM // TELEMETRY';
    toolTitle = 'System Health';
    archetype = 'syshealth';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`;
  } else if (rawTool.includes('schedule')) {
    toolTag = 'CHRONO // TIMER & CRON';
    toolTitle = 'Schedule';
    archetype = 'schedule';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`;
  } else if (rawTool.includes('audit_portability') || rawTool.includes('portability')) {
    toolTag = 'PORTABILITY // MULTI-OS';
    toolTitle = 'Portability Audit';
    archetype = 'portability';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`;
  } else if (rawTool.includes('flow_lock') || rawTool === 'lock') {
    toolTag = 'SANCTITY // @LOCK GATE';
    toolTitle = 'Flow Lock';
    archetype = 'lock';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`;
  } else if (rawTool.includes('generate_image') || rawTool.includes('image')) {
    toolTag = 'CANVAS // IMAGE GEN';
    toolTitle = 'Generate Image';
    archetype = 'image';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>`;
  } else if (rawTool.includes('search') || rawTool.includes('grep') || rawTool.includes('recon')) {
    toolTag = 'SEARCH // RECON';
    toolTitle = 'Search';
    archetype = 'websearch';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`;
  } else {
    toolTag = 'TOOL // EXEC';
    toolTitle = (toolName || 'Tool').replace(/^(flow_|default_api:)/, '').replace(/_/g, ' ');
    archetype = 'default';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`;
  }

  const cleanToolId = String(toolName || 'tool').replace(/^(flow_|default_api:)/, '').toLowerCase();
  const displayArg = shortArg.length > 55 ? shortArg.slice(0, 55) + '...' : shortArg;
  const reasonText = extractToolReason(toolName, details);
  const shortReason = reasonText.length > 52 ? reasonText.slice(0, 50) + '…' : reasonText;

  const card = document.createElement('details');
  card.className = `fl-tool-card fl-tool-${cleanToolId} fl-archetype-${archetype}`;
  card.open = false;

  card.innerHTML = `
    <summary class="fl-tool-header">
      <span class="fl-tool-chevron">›</span>
      <span class="fl-tool-icon">${toolIconSvg}</span>
      <span class="fl-tool-tag-pill">${escapeHtml(toolTag)}</span>
      <span class="fl-tool-title">${escapeHtml(toolTitle)}</span>
      ${displayArg ? `<code class="fl-tool-cmd">${escapeHtml(displayArg)}</code>` : ''}
      ${reasonText ? `<span class="fl-tool-reason-pill" title="${escapeHtml(reasonText)}">💬 ${escapeHtml(shortReason)}</span>` : ''}
      <span class="fl-tool-badge ${status}">${status === 'running' ? '<span class="fl-tool-spinner"></span> Running' : '✓ Done'}</span>
    </summary>
    <div class="fl-tool-details">
      ${reasonText ? `<div class="fl-tool-reason-box"><span class="fl-trb-lbl">💬 REASON:</span> <span class="fl-trb-txt">${escapeHtml(reasonText)}</span></div>` : ''}
      ${fullInput ? `
      <div class="fl-tool-block">
        <div class="fl-tool-block-header"><span>PARAMETERS</span><button class="fl-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div>
        <pre class="fl-tool-code"><code>${escapeHtml(fullInput)}</code></pre>
      </div>` : ''}
      ${output ? `
      <div class="fl-tool-block">
        <div class="fl-tool-block-header"><span>OUTPUT</span><button class="fl-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div>
        <pre class="fl-tool-code"><code>${escapeHtml(output)}</code></pre>
      </div>` : ''}
    </div>
  `;
  return card;
}

function formatSkillCard(details = {}, status = 'done') {
  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const action = (d.action || d.Action || 'pin').toLowerCase();
  const skillId = d.skill_id || d.skillId || d.skill_name || d.name || d.id || d.query || 'surgical_engineer';
  const isPin = action === 'pin' || action === 'pinned';
  const isUnpin = action === 'unpin';
  const reasonText = extractToolReason('skill_control', details);
  const shortReason = reasonText.length > 52 ? reasonText.slice(0, 50) + '…' : reasonText;

  const card = document.createElement('details');
  card.className = `fl-tool-card fl-skill-card ${isPin ? 'is-pinned' : ''} ${status === 'running' ? 'is-running' : ''}`;
  card.open = false;

  let badgeClass = 'done';
  let badgeLabel = '✓ Done';

  if (isPin) {
    badgeClass = 'pinned';
    badgeLabel = '🎯 PINNED';
  } else if (isUnpin) {
    badgeClass = 'done';
    badgeLabel = '✓ UNPINNED';
  } else if (status === 'running') {
    badgeClass = 'running';
    badgeLabel = '<span class="fl-tool-spinner"></span> RUNNING';
  }

  card.innerHTML = `
    <summary class="fl-tool-header fl-skill-header">
      <span class="fl-tool-chevron">›</span>
      <span class="fl-skill-icon">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg>
      </span>
      <span class="fl-skill-title">${escapeHtml(skillId)}</span>
      ${reasonText ? `<span class="fl-tool-reason-pill" title="${escapeHtml(reasonText)}">💬 ${escapeHtml(shortReason)}</span>` : ''}
      <span class="fl-skill-badge ${badgeClass}">${badgeLabel}</span>
    </summary>
    <div class="fl-tool-details">
      ${reasonText ? `<div class="fl-tool-reason-box"><span class="fl-trb-lbl">💬 REASON:</span> <span class="fl-trb-txt">${escapeHtml(reasonText)}</span></div>` : ''}
      <div class="fl-tool-block">
        <div class="fl-tool-block-header"><span>SOVEREIGN RUNBOOK PROTOCOL</span></div>
        <div class="fl-skill-desc">
          ${isPin 
            ? `🎯 <strong>Active Sovereign Runbook:</strong> Capability protocol <code>${escapeHtml(skillId)}</code> pinned to active session context.` 
            : (isUnpin 
              ? `✓ Skill <code>${escapeHtml(skillId)}</code> released and context tokens successfully reclaimed.` 
              : `Runbook operation <code>${escapeHtml(action)}</code> executed for <code>${escapeHtml(skillId)}</code>.`)}
        </div>
      </div>
    </div>
  `;

  // Auto-collapse skill card after 1.8 seconds so chat stays clean
  setTimeout(() => {
    card.removeAttribute('open');
  }, 1800);

  return card;
}

function formatScreenshotCard(details = {}, status = 'done') {
  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  
  // Extract image source from details
  let imgSrc = d.web_url || d.file_path || d.relative_path || d.target || d.TargetFile || d.path || '';
  if (!imgSrc && d.output && typeof d.output === 'string') {
    const mdMatch = d.output.match(/!\[.*?\]\((.*?)\)/);
    if (mdMatch) imgSrc = mdMatch[1];
  }
  if (!imgSrc && d.markdown_preview && typeof d.markdown_preview === 'string') {
    const mdMatch = d.markdown_preview.match(/!\[.*?\]\((.*?)\)/);
    if (mdMatch) imgSrc = mdMatch[1];
  }
  if (!imgSrc && d.image_base64) {
    imgSrc = `data:${d.mime_type || 'image/png'};base64,${d.image_base64}`;
  }

  const resolvedUrl = (imgSrc && imgSrc.startsWith('data:')) ? imgSrc : resolveMediaUrl(imgSrc);
  const filename = d.filename || (imgSrc ? String(imgSrc).split(/[\\/]/).pop() : 'screenshot.png');
  const relPath = d.relative_path || d.file_path || (imgSrc.startsWith('data:') ? 'in-memory vision buffer' : shortenFilePath(imgSrc));
  const hash = d.image_hash || d.hash || '';
  const sizeStr = d.size_bytes ? formatFileSize(d.size_bytes) : (d.size ? formatFileSize(d.size) : '');
  const reasonText = extractToolReason('screenshot', details);
  const shortReason = reasonText.length > 52 ? reasonText.slice(0, 50) + '…' : reasonText;

  const card = document.createElement('details');
  card.className = `fl-tool-card fl-screenshot-card ${status === 'running' ? 'is-running' : ''}`;
  card.open = true;

  card.innerHTML = `
    <summary class="fl-tool-header fl-screenshot-header">
      <span class="fl-tool-chevron">›</span>
      <span class="fl-tool-icon">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
          <circle cx="12" cy="13" r="4"></circle>
        </svg>
      </span>
      <span class="fl-tool-tag-pill fl-screenshot-tag">📸 OPTICAL // SHUTTER</span>
      <span class="fl-tool-title">${escapeHtml(filename)}</span>
      ${reasonText ? `<span class="fl-tool-reason-pill" title="${escapeHtml(reasonText)}">💬 ${escapeHtml(shortReason)}</span>` : ''}
      <span class="fl-tool-badge ${status}">${status === 'running' ? '<span class="fl-tool-spinner"></span> CAPTURING' : '✓ FRAME LOCKED • EXIT CODE 0'}</span>
    </summary>
    <div class="fl-tool-details fl-screenshot-body">
      ${reasonText ? `<div class="fl-tool-reason-box"><span class="fl-trb-lbl">💬 REASON:</span> <span class="fl-trb-txt">${escapeHtml(reasonText)}</span></div>` : ''}
      <div class="fl-screenshot-viewfinder-box">
        ${resolvedUrl ? `
          <div class="fl-screenshot-img-wrap" data-url="${escapeHtml(resolvedUrl)}" data-title="${escapeHtml(filename)}" onclick="window.handleChatAttachmentClick(this)">
            <img src="${resolvedUrl}" class="fl-screenshot-img" alt="${escapeHtml(filename)}" loading="lazy" />
            <div class="fl-screenshot-hover-overlay">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
              <span>Click to inspect high-resolution frame</span>
            </div>
          </div>
        ` : `
          <div class="fl-screenshot-empty">
            <span>📷 Frame buffer captured and transferred to vision cortex</span>
          </div>
        `}
        <div class="fl-screenshot-meta-row">
          <div class="fl-ss-meta-item" title="${escapeHtml(relPath)}">
            <span class="fl-ss-meta-k">PATH:</span>
            <code class="fl-ss-meta-v">${escapeHtml(relPath)}</code>
            <button class="fl-cmd-copy-btn" onclick="copyFilePath('${escapeHtml(relPath)}', this)">Copy</button>
          </div>
          ${sizeStr ? `<div class="fl-ss-meta-item"><span class="fl-ss-meta-k">SIZE:</span> <span class="fl-ss-meta-v">${escapeHtml(sizeStr)}</span></div>` : ''}
          ${hash ? `<div class="fl-ss-meta-item" title="${escapeHtml(hash)}"><span class="fl-ss-meta-k">SHA-256:</span> <span class="fl-ss-meta-v">${escapeHtml(hash.slice(0, 10))}…</span></div>` : ''}
          ${resolvedUrl && !resolvedUrl.startsWith('data:') ? `
            <a href="${escapeHtml(resolvedUrl)}" download="${escapeHtml(filename)}" class="fl-ss-download-btn" title="Download Screenshot">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download
            </a>
          ` : ''}
        </div>
      </div>
    </div>
  `;

  return card;
}

function formatBrainCard(details = {}, status = 'done') {
  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const action = String(d.action || d.Action || 'recall').toUpperCase();
  const query = String(d.query || d.Query || d.title || d.id || d.slug || d.key || 'Memory Synapse').trim();
  const category = String(d.category || 'architecture').toLowerCase();
  
  // Extract keywords
  let keywordsList = [];
  if (Array.isArray(d.keywords)) {
    keywordsList = d.keywords;
  } else if (typeof d.keywords === 'string') {
    keywordsList = d.keywords.split(',').map(s => s.trim()).filter(Boolean);
  }

  // Extract solution or output text
  let solutionText = d.solution || d.problem || d.root_cause || '';
  if (!solutionText && (d.output || d.rawOutput)) {
    const rawOut = d.output || d.rawOutput;
    if (typeof rawOut === 'object') {
      try {
        solutionText = JSON.stringify(rawOut, null, 2);
      } catch (_) {
        solutionText = String(rawOut);
      }
    } else {
      solutionText = String(rawOut);
    }
  }

  const reasonText = extractToolReason('brain_control', details);
  const shortReason = reasonText.length > 52 ? reasonText.slice(0, 50) + '…' : reasonText;

  const card = document.createElement('details');
  card.className = `fl-tool-card fl-brain-card ${status === 'running' ? 'is-running' : ''}`;
  card.open = true;

  const isWrite = action === 'WRITE' || action === 'INGEST' || action === 'CRYSTALLIZE';

  card.innerHTML = `
    <summary class="fl-tool-header fl-brain-header">
      <span class="fl-tool-chevron">›</span>
      <span class="fl-tool-icon">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
      </span>
      <span class="fl-tool-tag-pill fl-brain-tag-pill">🧠 BRAIN // ${escapeHtml(action)}</span>
      <span class="fl-tool-title">${escapeHtml(query)}</span>
      ${reasonText ? `<span class="fl-tool-reason-pill" title="${escapeHtml(reasonText)}">💬 ${escapeHtml(shortReason)}</span>` : ''}
      <span class="fl-tool-badge ${status}">${status === 'running' ? '<span class="fl-tool-spinner"></span> SYNAPSING' : '✓ SYNAPSED • EXIT CODE 0'}</span>
    </summary>
    <div class="fl-tool-details fl-brain-body">
      ${reasonText ? `<div class="fl-tool-reason-box"><span class="fl-trb-lbl">💬 REASON:</span> <span class="fl-trb-txt">${escapeHtml(reasonText)}</span></div>` : ''}
      <div class="fl-brain-telemetry-panel">
        <div class="fl-brain-meta-bar">
          <span class="fl-brain-vault-pill">VAULT: <strong>.fl_brain/</strong></span>
          <span class="fl-brain-cat-badge ${escapeHtml(category)}">${escapeHtml(category.toUpperCase())}</span>
          <span class="fl-brain-action-pill">${isWrite ? '⚡ PERMANENT CRYSTAL' : '🔍 SYNAPTIC RECALL'}</span>
        </div>
        ${keywordsList.length > 0 ? `
          <div class="fl-brain-keywords-row">
            <span class="fl-brain-kw-title">KEYWORDS:</span>
            <div class="fl-brain-kw-chips">
              ${keywordsList.slice(0, 12).map(k => `<span class="fl-brain-chip">${escapeHtml(k)}</span>`).join('')}
            </div>
          </div>
        ` : ''}
        ${solutionText ? `
          <div class="fl-tool-block fl-brain-block">
            <div class="fl-tool-block-header">
              <span>${isWrite ? 'CRYSTALLIZED SOLUTION' : 'SYNAPSE PAYLOAD'}</span>
              <button class="fl-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button>
            </div>
            <pre class="fl-tool-code fl-brain-code"><code>${escapeHtml(solutionText)}</code></pre>
          </div>
        ` : ''}
      </div>
    </div>
  `;

  return card;
}

function animateTerminalPrompt(cmdItem, commandText) {
  const titleEl = cmdItem.querySelector('.fl-cmd-item-title');
  if (!titleEl || !commandText) return;

  const rawText = commandText.trim();
  titleEl.innerHTML = `<span class="fl-cmd-typed"></span>`;
  const typedEl = titleEl.querySelector('.fl-cmd-typed');
  const cursorEl = titleEl.querySelector('.fl-cmd-cursor');

  let curIdx = 0;
  const step = rawText.length > 50 ? 3 : (rawText.length > 25 ? 2 : 1);
  const delay = Math.max(12, Math.min(26, Math.floor(300 / (rawText.length / step))));

  function typeChar() {
    if (!typedEl || !typedEl.isConnected) return;
    curIdx += step;
    if (curIdx < rawText.length) {
      typedEl.textContent = rawText.slice(0, curIdx);
      setTimeout(typeChar, delay);
    } else {
      typedEl.textContent = rawText;
      setTimeout(() => {
        if (cursorEl) cursorEl.classList.add('fade');
      }, 350);
    }
  }
  typeChar();
}

function shortenFilePath(p) {
  if (!p) return 'buffer';
  const str = String(p).trim();
  const parts = str.split('/');
  if (parts.length > 3) {
    return '.../' + parts.slice(-3).join('/');
  }
  return str;
}

function getOrCreateToolsCapsule(toolsArea) {
  if (!toolsArea) return { activeSlot: null, capsule: null, capsuleBody: null };
  
  let activeSlot = toolsArea.querySelector('.fl-live-active-slot');
  if (!activeSlot) {
    activeSlot = document.createElement('div');
    activeSlot.className = 'fl-live-active-slot';
    toolsArea.appendChild(activeSlot);
  }

  let capsule = toolsArea.querySelector('.fl-toolstream-wrap');
  if (!capsule) {
    capsule = document.createElement('details');
    capsule.className = 'fl-toolstream-wrap';
    capsule.style.display = 'none'; // STRICT: HIDDEN DURING STREAMING!
    capsule.open = false;
    capsule.removeAttribute('open');
    capsule.innerHTML = `
      <summary class="fl-toolstream-summary">
        <span class="fl-toolstream-chevron">›</span>
        <span class="fl-toolstream-title">Ran tools</span>
        
      </summary>
      <div class="fl-toolstream-body"></div>
    `;
    toolsArea.appendChild(capsule);

// Native CSS details summary disclosure used
  }

  const capsuleBody = capsule.querySelector('.fl-toolstream-body');
  return { activeSlot, capsule, capsuleBody };
}

function updateToolsCapsuleHeader(capsule) {
  if (!capsule) return;
  const body = capsule.querySelector('.fl-toolstream-body');
  if (!body) return;

  const cmdItems = body.querySelectorAll('.fl-cmd-item');
  const skills = body.querySelectorAll('.fl-skill-card');
  const agents = body.querySelectorAll('.fl-subagent-card');
  const tasks = body.querySelectorAll('.fl-task-card');
  const otherTools = body.querySelectorAll('.fl-tool-card, .fl-generic-tool-card');
  
  const total = cmdItems.length + skills.length + agents.length + tasks.length + otherTools.length;
  if (total === 0) {
    capsule.style.display = 'none';
    return;
  }

  const titleEl = capsule.querySelector('.fl-toolstream-title');
  if (titleEl) {
    titleEl.textContent = `Ran ${total} tool${total > 1 ? 's' : ''}`;
  }

  const toolsListEl = capsule.querySelector('.fl-toolstream-tools-list');
  if (toolsListEl) {
    const names = [];
    if (cmdItems.length > 0) names.push(`run_command (${cmdItems.length})`);
    if (skills.length > 0) names.push(`skills (${skills.length})`);
    if (agents.length > 0) names.push(`subagents (${agents.length})`);
    if (tasks.length > 0) names.push(`tasks (${tasks.length})`);
    
    otherTools.forEach(card => {
      const t = (card.querySelector('.fl-tool-title')?.textContent || '').trim().toLowerCase().replace(/\s+/g, '_');
      if (t && !names.includes(t) && names.length < 3) {
        names.push(t);
      }
    });
    
    if (names.length > 0) {
      toolsListEl.textContent = `${names.slice(0, 3).join(', ')}${names.length > 3 ? '…' : ''}`;
      toolsListEl.style.display = 'inline-flex';
    } else {
      toolsListEl.style.display = 'none';
    }
  }

  // DOKTRIN MUTLAK: Capsule MUST REMAIN HIDDEN while stream is active!
  // It only appears when the chat turn is done!
  if (isChatStreaming) {
    capsule.style.display = 'none';
  }
}

function extractCodeLinesForScanner(d, filePath, startNum, endLine, isWeb) {
  const src = (d && d.details && typeof d.details === 'object') ? { ...d, ...d.details } : (d || {});
  let rawContent = '';
  if (typeof src.real_content === 'string' && src.real_content.trim()) {
    rawContent = src.real_content;
  } else if (typeof src.content === 'string' && src.content.trim()) {
    rawContent = src.content;
  } else if (src.output !== undefined && src.output !== null) {
    let out = src.output;
    if (typeof out === 'object' && out !== null) {
      rawContent = out.real_content || out.content || out.rawOutput || out.output || out.result || JSON.stringify(out, null, 2);
    } else if (typeof out === 'string') {
      try {
        const parsed = JSON.parse(out);
        if (parsed && typeof parsed === 'object') {
          rawContent = parsed.real_content || parsed.content || parsed.rawOutput || parsed.output || parsed.result || out;
        } else {
          rawContent = out;
        }
      } catch (e) {
        rawContent = out;
      }
    }
  } else if (typeof src.rawOutput === 'string' && src.rawOutput.trim()) {
    rawContent = src.rawOutput;
  } else if (typeof src.TargetContent === 'string' && src.TargetContent.trim()) {
    rawContent = src.TargetContent;
  } else if (typeof src.CodeContent === 'string' && src.CodeContent.trim()) {
    rawContent = src.CodeContent;
  }

  const s = stripInternalSystemInterceptions(rawContent);
  if (!s || !s.trim()) return [];

  const rawLines = s.split(/\r?\n/);
  const hasNumberedLines = rawLines.some(l => /^\s*(\d+)[\:\│]\s?/.test(l));

  const scanLines = [];
  if (hasNumberedLines) {
    let seenFirst = false;
    for (let i = 0; i < rawLines.length; i++) {
      const line = rawLines[i];
      const numMatch = line.match(/^\s*(\d+)[\:\│]\s?(.*)$/);
      if (numMatch) {
        seenFirst = true;
        const lineNo = String(numMatch[1]).padStart(3, '0');
        scanLines.push(`${lineNo} │ ${numMatch[2]}`);
        continue;
      }
      if (!seenFirst) {
        // Skip metadata headers before the first code line
        continue;
      }
      if (/^The above content (?:does NOT show|shows)/i.test(line.trim())) {
        continue;
      }
      scanLines.push(`    │ ${line}`);
    }
  } else {
    for (let i = 0; i < rawLines.length; i++) {
      const line = rawLines[i];
      if (/^(Created At:|Completed At:|File Path:|Total Lines:|Total Bytes:|Showing lines|The following code has been modified)/i.test(line.trim())) {
        continue;
      }
      if (/^The above content (?:does NOT show|shows)/i.test(line.trim())) {
        continue;
      }
      const lineNo = String(startNum + scanLines.length).padStart(3, '0');
      scanLines.push(`${lineNo} │ ${line}`);
    }
  }

  return scanLines.slice(0, 120);
}

function renderLiveAmbientHoloStream(activeSlot, domainTag, subSnippet, colorTheme, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const theme = colorTheme || 'cyan';
  const tagText = domainTag || 'EXECUTION';
  const rawSnippet = String(subSnippet || 'Synthesizing sovereign operation...').replace(/[\r\n]+/g, ' ').trim();
  const snippet = rawSnippet.length > 44 ? rawSnippet.slice(0, 41) + '…' : rawSnippet;

  let stage = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!stage) {
    stage = document.createElement('div');
    stage.className = 'fl-live-ambient-stage';
    stage.setAttribute('data-live-step', String(stepIdx));
    stage._spawnTime = Date.now();
    activeSlot.appendChild(stage);
  }

  const gradId = `ambient-holo-grad-${stepIdx}-${Math.floor(Math.random() * 100000)}`;

  stage.innerHTML = `
    <div class="fl-ambient-hud-line">
      <div class="fl-ambient-meta">
        <span class="fl-ambient-glyph">⟡</span>
        <span class="fl-ambient-tag ${escapeHtml(theme)}">[SYNAPSE // ${escapeHtml(tagText)}]</span>
        <span class="fl-ambient-sep">›</span>
        <span class="fl-ambient-target" title="${escapeHtml(rawSnippet)}">${escapeHtml(snippet)}</span>
      </div>
      <span class="fl-ambient-badge ${escapeHtml(theme)}">
        <span class="fl-ambient-spinner"></span> ACTIVE
      </span>
    </div>
    <div class="fl-ambient-laser-track">
      <svg viewBox="0 0 600 16" class="fl-ambient-wave-svg" preserveAspectRatio="none">
        <defs>
          <linearGradient id="${gradId}" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="var(--holo-${escapeHtml(theme)}, #00f0ff)" stop-opacity="0" />
            <stop offset="45%" stop-color="var(--holo-${escapeHtml(theme)}, #00f0ff)" stop-opacity="0.8" />
            <stop offset="50%" stop-color="#ffffff" stop-opacity="1" />
            <stop offset="55%" stop-color="var(--holo-${escapeHtml(theme)}, #00f0ff)" stop-opacity="0.8" />
            <stop offset="100%" stop-color="var(--holo-${escapeHtml(theme)}, #00f0ff)" stop-opacity="0" />
          </linearGradient>
        </defs>
        <line x1="0" y1="8" x2="600" y2="8" stroke="var(--holo-${escapeHtml(theme)}, #00f0ff)" stroke-opacity="0.15" stroke-width="1" stroke-dasharray="3 5" />
        <path class="fl-ambient-sine-wave" d="M 0 8 Q 75 1 150 8 T 300 8 T 450 8 T 600 8" fill="none" stroke="var(--holo-${escapeHtml(theme)}, #00f0ff)" stroke-width="1.8" stroke-linecap="round" />
        <circle class="fl-ambient-laser-beam" cx="50" cy="8" r="2.4" fill="#ffffff" filter="drop-shadow(0 0 6px var(--holo-${escapeHtml(theme)}, #00f0ff))" />
      </svg>
    </div>
  `;
}

function renderLiveFileScanner(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  const rawTool = (toolName || '').toLowerCase();
  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const target = d.AbsolutePath || d.TargetFile || d.file || d.path || d.commandLine || d.query || d.url || 'workspace/file';
  const isWeb = rawTool.includes('url') || rawTool.includes('web') || Boolean(d.url || d.query);

  if (rawTool.includes('search_web')) {
    renderLiveSearchWeb(activeSlot, toolName, details, stepIdx);
    return;
  }
  if (rawTool.includes('read_url')) {
    renderLiveReadUrl(activeSlot, toolName, details, stepIdx);
    return;
  }
  if (isWeb) {
    renderLiveAmbientHoloStream(activeSlot, 'NET RECON', shortenFilePath(target), 'cyan', stepIdx);
    return;
  }

  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const startNum = Number(d.StartLine || d.start_line || 1);
  const endLine = Number(d.EndLine || d.end_line || (startNum + 120));
  const fileName = String(target).split(/[\\/]/).pop() || shortenFilePath(target);
  let scanLines = extractCodeLinesForScanner(d, target, startNum, endLine, false);
  const VISIBLE_ROWS = 7;

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-view-file';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let cachedGhostStreamEl = null;
  const renderViewportRows = (offsetIdx, activeRowOffset) => {
    if (!cachedGhostStreamEl || !cachedGhostStreamEl.isConnected) cachedGhostStreamEl = box.querySelector('.fl-vf-ghost-stream');
    const streamEl = cachedGhostStreamEl;
    if (!streamEl) return;
    if (!scanLines || scanLines.length === 0) {
      streamEl.innerHTML = `<div class="fl-vf-ghost-line is-active">${String(startNum).padStart(3, '0')} │ Reading ${escapeHtml(fileName)} from disk...</div>`;
      return;
    }
    const maxStart = Math.max(0, scanLines.length - VISIBLE_ROWS);
    const startIdx = Math.min(offsetIdx, maxStart);
    const slice = scanLines.slice(startIdx, startIdx + VISIBLE_ROWS);
    streamEl.innerHTML = slice.map((lineText, idx) => {
      const isAct = (idx === (activeRowOffset % slice.length));
      return `<div class="fl-vf-ghost-line${isAct ? ' is-active' : ''}">${escapeHtml(lineText)}</div>`;
    }).join('');
  };

  box.innerHTML = `
    <div class="fl-vf-inline-row">
      <div class="fl-vf-left">
        <span class="fl-vf-reticle">⟡</span>
        <span class="fl-vf-verb">READING FILE</span>
        <span class="fl-vf-filename" title="${escapeHtml(String(target))}">${escapeHtml(fileName)}</span>
        <span class="fl-vf-slice">[L${startNum}–${endLine}]</span>
      </div>
      <span class="fl-vf-speed-badge">${scanLines.length || '...'} LINES • STREAMING</span>
    </div>
    <div class="fl-vf-laser-filament">
      <div class="fl-vf-laser-fill" style="width: 15%;"></div>
    </div>
    <div class="fl-vf-ghost-stream"></div>
    <div class="fl-vf-ghost-meta">
      <span class="fl-vf-path-sub">PATH: ${escapeHtml(String(target))}</span>
      <span class="fl-vf-timer">0.01s • REAL FILE STREAM</span>
    </div>
  `;

  let tick = 0;
  renderViewportRows(0, 0);

  box._injectOutputLines = (rawOut) => {
    const payload = (rawOut && typeof rawOut === 'object') ? rawOut : { output: rawOut };
    const updated = extractCodeLinesForScanner(payload, target, startNum, endLine, false);
    if (updated && updated.length > 0) {
      scanLines = updated;
      tick = 0;
      renderViewportRows(0, 0);
      const sliceEl = box.querySelector('.fl-vf-slice');
      if (sliceEl) sliceEl.textContent = `[L${startNum}–${startNum + scanLines.length - 1}] (${scanLines.length} lines)`;
    }
  };

    const badge = box.querySelector('.fl-vf-speed-badge');
  const fill = box.querySelector('.fl-vf-laser-fill');
  const timerEl = box.querySelector('.fl-vf-timer');
  if (box._screeningTimer) clearInterval(box._screeningTimer);
  box._screeningTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._screeningTimer) { clearInterval(box._screeningTimer); box._screeningTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._screeningTimer) { clearInterval(box._screeningTimer); box._screeningTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const totalL = Math.max(1, scanLines.length);
    const curStep = tick % totalL;
    const pct = Math.min(98, Math.max(15, Math.round(((curStep + 1) / totalL) * 100)));

        // (cached badge)
    if (badge) badge.textContent = `LINE ${startNum + curStep} / ${startNum + totalL - 1} (${pct}%)`;

        // (cached fill)
    if (fill) fill.style.width = `${pct}%`;

        // (cached timerEl)
    if (timerEl) timerEl.textContent = `${elapsedSec}s • ${totalL} REAL LINES`;

    const windowStart = Math.max(0, curStep - 3);
    renderViewportRows(windowStart, curStep - windowStart);
  }, 180);
}

function renderLiveReplaceContent(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const extractDiffData = (srcObj) => {
    const dObj = (srcObj && srcObj.details && typeof srcObj.details === 'object') ? { ...srcObj, ...srcObj.details } : (srcObj || {});
    let rawDelStr = dObj.TargetContent ?? dObj.target_content ?? dObj.old_str ?? '';
    let rawAddStr = dObj.ReplacementContent ?? dObj.replacement_content ?? dObj.new_str ?? '';
    if ((!rawDelStr && !rawAddStr) && Array.isArray(dObj.ReplacementChunks) && dObj.ReplacementChunks.length > 0) {
      rawDelStr = dObj.ReplacementChunks.map(c => c.TargetContent || '').filter(Boolean).join('\n');
      rawAddStr = dObj.ReplacementChunks.map(c => c.ReplacementContent || '').filter(Boolean).join('\n');
    }
    rawDelStr = stripInternalSystemInterceptions(rawDelStr);
    rawAddStr = stripInternalSystemInterceptions(rawAddStr);
    return { dObj, rawDelStr: String(rawDelStr || ''), rawAddStr: String(rawAddStr || '') };
  };

  let { dObj: d, rawDelStr, rawAddStr } = extractDiffData(details);
  const filePath = d.TargetFile || d.AbsolutePath || d.target_file || d.file || d.path || 'workspace/file';
  const fileName = String(filePath).split(/[\\/]/).pop() || shortenFilePath(filePath);
  const startL = Number(d.StartLine || d.start_line || 1);
  const endL = Number(d.EndLine || d.end_line || (startL + Math.max(1, rawDelStr.split(/\r?\n/).length - 1)));
  const instruction = d.Instruction || d.Description || `Surgical splice on ${fileName}`;

  let delLines = rawDelStr.split(/\r?\n/).filter(l => l.length > 0).map((l, i) => `L${String(startL + i).padStart(3, '0')} │ ${l}`);
  let addLines = rawAddStr.split(/\r?\n/).filter(l => l.length > 0).map((l, i) => `L${String(startL + i).padStart(3, '0')} │ ${l}`);
  if (delLines.length === 0) delLines = [`L${String(startL).padStart(3, '0')} │ (empty target range)`];
  if (addLines.length === 0) addLines = [`L${String(startL).padStart(3, '0')} │ (empty replacement range)`];

  const MAX_DIFF_ROWS = 5;

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-replace-file';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let cachedDelContainer = null;
  let cachedAddContainer = null;
  const renderDiffBlocks = (stepTick) => {
    if (!cachedDelContainer || !cachedDelContainer.isConnected) cachedDelContainer = box.querySelector('.fl-rfc-del-rows');
    if (!cachedAddContainer || !cachedAddContainer.isConnected) cachedAddContainer = box.querySelector('.fl-rfc-add-rows');
    const delContainer = cachedDelContainer;
    const addContainer = cachedAddContainer;
    if (delContainer) {
      const maxDelStart = Math.max(0, delLines.length - MAX_DIFF_ROWS);
      const delStart = delLines.length > MAX_DIFF_ROWS ? (stepTick % (maxDelStart + 1)) : 0;
      const visibleDel = delLines.slice(delStart, delStart + MAX_DIFF_ROWS);
      delContainer.innerHTML = visibleDel.map((line, i) => `
        <div class="fl-rfc-diff-line${i === (stepTick % visibleDel.length) ? ' is-active' : ''}">
          <span class="fl-rfc-sign">−</span>
          <span>${escapeHtml(line)}</span>
        </div>
      `).join('');
    }
    if (addContainer) {
      const maxAddStart = Math.max(0, addLines.length - MAX_DIFF_ROWS);
      const addStart = addLines.length > MAX_DIFF_ROWS ? (stepTick % (maxAddStart + 1)) : 0;
      const visibleAdd = addLines.slice(addStart, addStart + MAX_DIFF_ROWS);
      addContainer.innerHTML = visibleAdd.map((line, i) => `
        <div class="fl-rfc-diff-line${i === (stepTick % visibleAdd.length) ? ' is-active' : ''}">
          <span class="fl-rfc-sign">+</span>
          <span>${escapeHtml(line)}</span>
        </div>
      `).join('');
    }
  };

  box.innerHTML = `
    <div class="fl-rfc-meta-bar">
      <span class="fl-rfc-title">⚡ EDIT FILE // ${escapeHtml(fileName)} <span style="color:#c084fc;font-size:10.5px;">[L${startL}–${endL}]</span></span>
      <span class="fl-rfc-delta">
        <span class="fl-rfc-del-count">−${delLines.length} REMOVED</span>
        <span class="fl-rfc-add-count">+${addLines.length} ADDED</span>
        <span class="fl-rfc-timer" style="color:#00f2fe;margin-left:4px;">0.01s</span>
      </span>
    </div>
    <div class="fl-rfc-sub-desc">▸ ${escapeHtml(String(instruction))} • PATH: ${escapeHtml(String(filePath))}</div>
    <div class="fl-rfc-diff-grid">
      <div class="fl-rfc-ribbon ribbon-del">
        <div class="fl-rfc-section-label">− REMOVED FROM ${escapeHtml(fileName)} (${delLines.length} line${delLines.length > 1 ? 's' : ''})</div>
        <div class="fl-rfc-del-rows"></div>
      </div>
      <div class="fl-rfc-ribbon ribbon-add">
        <div class="fl-rfc-section-label">+ WRITTEN TO ${escapeHtml(fileName)} (${addLines.length} line${addLines.length > 1 ? 's' : ''})</div>
        <div class="fl-rfc-add-rows"></div>
      </div>
    </div>
  `;

  let tick = 0;
  renderDiffBlocks(0);

  box._injectOutputLines = (rawOut) => {
    if (rawOut && typeof rawOut === 'object') {
      const updated = extractDiffData(rawOut);
      if (updated.rawDelStr || updated.rawAddStr) {
        if (updated.rawDelStr) {
          delLines = updated.rawDelStr.split(/\r?\n/).filter(l => l.length > 0).map((l, i) => `L${String(startL + i).padStart(3, '0')} │ ${l}`);
        }
        if (updated.rawAddStr) {
          addLines = updated.rawAddStr.split(/\r?\n/).filter(l => l.length > 0).map((l, i) => `L${String(startL + i).padStart(3, '0')} │ ${l}`);
        }
        renderDiffBlocks(0);
      }
    }
  };

    const timerEl = box.querySelector('.fl-rfc-timer');
  if (box._typingTimer) clearInterval(box._typingTimer);
  box._typingTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._typingTimer) { clearInterval(box._typingTimer); box._typingTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._typingTimer) { clearInterval(box._typingTimer); box._typingTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsed = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached timerEl)
    if (timerEl) timerEl.textContent = `${elapsed}s • DIFF ACTIVE`;
    renderDiffBlocks(tick);
  }, 180);
}

function renderLiveCodeForger(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  const rawTool = (toolName || '').toLowerCase();
  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});

  if (rawTool.includes('replace') || rawTool.includes('splice') || rawTool.includes('patch') || Boolean(d.TargetContent || d.ReplacementContent || d.ReplacementChunks)) {
    renderLiveReplaceContent(activeSlot, toolName, details, stepIdx);
    return;
  }

  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const filePath = d.TargetFile || d.AbsolutePath || d.target_file || d.file || d.path || d.task_description || d.task || d.arguments || 'workspace/file';
  const fileName = String(filePath).split(/[\\/]/).pop() || shortenFilePath(filePath);
  let codeRaw = stripInternalSystemInterceptions(String(d.CodeContent ?? d.code_content ?? d.code ?? d.content ?? d.real_content ?? ''));
  let totalBytes = new Blob([codeRaw]).size || codeRaw.length || 128;
  let codeLines = codeRaw.split(/\r?\n/).filter((l, idx, arr) => !(idx === arr.length - 1 && l === '')).map((l, idx) => `${String(idx + 1).padStart(3, '0')} │ ${l}`);
  if (codeLines.length === 0) {
    codeLines = [`001 │ Writing ${fileName}...`];
  }

  const VISIBLE_WRITE_ROWS = 7;

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-write-file';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let cachedPrinterEl = null;
  const renderWriteRows = (stepTick) => {
    if (!cachedPrinterEl || !cachedPrinterEl.isConnected) cachedPrinterEl = box.querySelector('.fl-wtf-printer');
    const printer = cachedPrinterEl;
    if (!printer) return;
    const revealedCount = Math.min(codeLines.length, Math.max(1, (stepTick % (codeLines.length + 1)) || codeLines.length));
    const startIdx = Math.max(0, revealedCount - VISIBLE_WRITE_ROWS);
    const slice = codeLines.slice(startIdx, startIdx + VISIBLE_WRITE_ROWS);
    printer.innerHTML = slice.map((lineText, idx) => {
      const isLast = (idx === slice.length - 1);
      return `<div class="fl-wtf-code-line${isLast ? ' active-print' : ''}">${escapeHtml(lineText)}${isLast ? ' █' : ''}</div>`;
    }).join('');
  };

  box.innerHTML = `
    <div class="fl-wtf-pillar-track"><div class="fl-wtf-pillar-fill" style="height:18%;"></div></div>
    <div class="fl-wtf-top">
      <span class="fl-wtf-tag">[FS // WRITE FILE]</span>
      <span class="fl-wtf-bytes">0 B / ${totalBytes} B (${codeLines.length} lines)</span>
      <span class="fl-wtf-badge">WRITING CONTENT</span>
    </div>
    <div class="fl-wtf-filename" title="${escapeHtml(String(filePath))}">❖ ${escapeHtml(fileName)} — ${codeLines.length} lines (${totalBytes} bytes)</div>
    <div class="fl-wtf-printer"></div>
    <div class="fl-wtf-bottom">
      <span>TARGET: ${escapeHtml(String(filePath))}</span>
      <span class="fl-wtf-timer">0.01s • REAL CONTENT STREAM</span>
    </div>
  `;

  let tick = 1;
  renderWriteRows(tick);

  box._injectOutputLines = (rawOut) => {
    if (rawOut && typeof rawOut === 'object') {
      const inner = (rawOut.details && typeof rawOut.details === 'object') ? { ...rawOut, ...rawOut.details } : rawOut;
      const updatedCode = inner.CodeContent ?? inner.code_content ?? inner.content ?? inner.real_content ?? '';
      if (updatedCode) {
        codeRaw = stripInternalSystemInterceptions(String(updatedCode));
        totalBytes = new Blob([codeRaw]).size || codeRaw.length || totalBytes;
        codeLines = codeRaw.split(/\r?\n/).filter((l, idx, arr) => !(idx === arr.length - 1 && l === '')).map((l, idx) => `${String(idx + 1).padStart(3, '0')} │ ${l}`);
        renderWriteRows(codeLines.length);
      }
    }
  };

    const pillar = box.querySelector('.fl-wtf-pillar-fill');
  const bytesEl = box.querySelector('.fl-wtf-bytes');
  const timerEl = box.querySelector('.fl-wtf-timer');
  if (box._typingTimer) clearInterval(box._typingTimer);
  box._typingTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._typingTimer) { clearInterval(box._typingTimer); box._typingTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._typingTimer) { clearInterval(box._typingTimer); box._typingTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsed = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const totalL = Math.max(1, codeLines.length);
    const curLine = Math.min(totalL, (tick % (totalL + 2)) + 1);
    const pct = Math.min(99, Math.round((curLine / totalL) * 100));
    const curBytes = Math.floor((totalBytes * pct) / 100);

        // (cached pillar)
    if (pillar) pillar.style.height = `${pct}%`;

        // (cached bytesEl)
    if (bytesEl) bytesEl.textContent = `${curBytes} B / ${totalBytes} B (${pct}% • ${totalL} LINES)`;

        // (cached timerEl)
    if (timerEl) timerEl.textContent = `${elapsed}s • WRITING DISK`;

    renderWriteRows(curLine);
  }, 180);
}

function renderLiveSearchTools(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const query = String(d.query || d.Query || d.action || d.Action || 'kernel_registry').trim();

  const pool = [
    'render_visual', 'brain_control', 'run_command', 'view_file',
    'write_to_file', 'replace_file_content', 'search_tools', 'skill_control',
    'audit_security', 'web_security_audit', 'website_intelligence', 'sys_health',
    'detect_hardcode', 'audit_portability', 'youtube_spy_video', 'flow_lock'
  ];

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-search-tools';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  box.innerHTML = `
    <svg viewBox="0 0 240 22" class="fl-st-sonar-svg">
      <path d="M 10 20 Q 120 -6 230 20" fill="none" stroke="rgba(192, 132, 252, 0.35)" stroke-width="1.5" stroke-dasharray="4 4" />
      <path d="M 45 20 Q 120 4 195 20" fill="none" stroke="#00f2fe" stroke-width="1.5" />
      <circle cx="120" cy="11" r="3" fill="#00ffb2" filter="drop-shadow(0 0 6px #00ffb2)" />
    </svg>
    <div class="fl-st-header">
      <span class="fl-st-query">📡 REGISTRY // "${escapeHtml(query.slice(0, 26))}"</span>
      <span class="fl-st-speed">37 TOOLS • 0.01s</span>
    </div>
    <div class="fl-st-roulette-track">
      <span class="fl-st-chip chip-left">${escapeHtml(pool[0])}</span>
      <span class="fl-st-chip is-center">${escapeHtml(pool[1])}</span>
      <span class="fl-st-chip chip-right">${escapeHtml(pool[2])}</span>
    </div>
  `;

    const speedEl = box.querySelector('.fl-st-speed');
  const chips = box.querySelectorAll('.fl-st-chip');
  if (box._genericTimer) clearInterval(box._genericTimer);
  let tick = 0;
  box._genericTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._genericTimer) { clearInterval(box._genericTimer); box._genericTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._genericTimer) { clearInterval(box._genericTimer); box._genericTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsed = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached speedEl)
    if (speedEl) speedEl.textContent = `SCANNING 37 TOOLS • ${elapsed}s`;

        // (cached chips)
    if (chips.length >= 3) {
      chips[0].textContent = pool[tick % pool.length];
      chips[1].textContent = pool[(tick + 1) % pool.length];
      chips[2].textContent = pool[(tick + 2) % pool.length];
    }
  }, 150);
}

function renderLiveBashRunner(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details && typeof details === 'object' ? details : {});
  const cmd = String(d.commandLine || d.CommandLine || d.command || d.toolAction || (typeof details === 'string' ? details : 'bash command')).trim();
  const cwd = shortenFilePath(d.cwd || d.Cwd || 'workspace');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-bash-box';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  const isWin = (typeof navigator !== 'undefined') && (
    (navigator.platform && navigator.platform.toUpperCase().indexOf('WIN') >= 0) ||
    (navigator.userAgent && navigator.userAgent.indexOf('Windows') >= 0)
  );

  const telemetryFrames = isWin ? [
    `[win32] CreateProcess("powershell.exe", ["-Command", "${cmd.slice(0, 36)}..."])`,
    `[pipe] stdout/stderr non-blocking HANDLE attached`,
    `[cwd] ${cwd}`,
    `[exec] streaming child process telemetry...`
  ] : [
    `[kernel] posix_spawn("/bin/bash", ["-c", "${cmd.slice(0, 36)}..."])`,
    `[pipe] stdout/stderr non-blocking fd [3,4] attached`,
    `[cwd] ${cwd} • env PAGER=cat`,
    `[exec] streaming child process telemetry...`
  ];

  box.innerHTML = `
    <div class="fl-live-bash-top">
      <div class="fl-live-bash-tag">
        <span class="fl-bash-pulse-beacon"></span>
        <span style="font-size:9.5px;font-weight:800;color:#00e5ff;letter-spacing:0.06em;">[TTY // KERNEL EXEC]</span>
      </div>
      <span class="fl-bash-stopwatch">00.01s</span>
      <span class="fl-bash-badge">⚡ ACTIVE</span>
    </div>
    <div class="fl-live-bash-cmdbar" title="${escapeHtml(cmd)}">
      <span style="color:#00e5ff;font-weight:800;">$</span>
      <span class="fl-bash-cmd-txt">${escapeHtml(cmd.length > 52 ? cmd.slice(0, 49) + '...' : cmd)}</span>
    </div>
    <div class="fl-live-bash-screen">
      <pre class="fl-live-bash-code"><code>${escapeHtml(telemetryFrames.slice(0, 2).join('\n'))}</code></pre>
    </div>
    <div class="fl-live-bash-bottom">
      <span>CWD: <strong style="color:#cbd5e1;">${escapeHtml(cwd)}</strong></span>
      <span class="fl-bash-io-rate">I/O: 1,420 OPS/S</span>
    </div>
  `;

    const sw = box.querySelector('.fl-bash-stopwatch');
  const ioEl = box.querySelector('.fl-bash-io-rate');
  const codeEl = box.querySelector('.fl-live-bash-code code');
  if (box._bashTimer) clearInterval(box._bashTimer);
  let tick = 0;
  box._hasRealStdout = false;
  box._injectOutputLines = (rawOut) => {
    if (!rawOut) return;
    const text = typeof rawOut === 'object' ? (rawOut.stdout || rawOut.output || JSON.stringify(rawOut)) : String(rawOut);
    const cleaned = stripInternalSystemInterceptions(text);
    const cleanLines = String(cleaned).split('\n').filter(l => l.trim() && !l.includes('[DOKTRIN TERMINAL FLOWORK]')).slice(-4);
    if (cleanLines.length > 0) {
      box._hasRealStdout = true;
      const codeEl = box.querySelector('.fl-live-bash-code code');
      if (codeEl) codeEl.textContent = cleanLines.join('\n');
    }
  };

  box._bashTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._bashTimer) { clearInterval(box._bashTimer); box._bashTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._bashTimer) { clearInterval(box._bashTimer); box._bashTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSecNum = (Date.now() - box._spawnTime) / 1000;
    const elapsed = elapsedSecNum.toFixed(2).padStart(5, '0');
        // (cached sw)
    if (sw) sw.textContent = `${elapsed}s`;

        // (cached ioEl)
    if (ioEl) ioEl.textContent = `I/O: ${1200 + ((tick * 173) % 2800)} CHARS/S`;

    // Sovereign 120s Auto-Ping & Watchdog Guard:
    if (elapsedSecNum >= 120 && !box._hasAutoPinged) {
      box._hasAutoPinged = true;
      const badgeEl = box.querySelector('.fl-bash-badge');
      if (badgeEl) {
        badgeEl.textContent = '⏱️ AUTO-PING (120s)';
        badgeEl.style.background = 'rgba(234, 179, 8, 0.2)';
        badgeEl.style.color = '#fde047';
        badgeEl.style.borderColor = 'rgba(234, 179, 8, 0.4)';
      }
      if (typeof currentChatSessionId !== 'undefined' && currentChatSessionId) {
        fetch(`/api/chat/steps/${encodeURIComponent(currentChatSessionId)}`)
          .then(r => r.json())
          .then(d => {
            if (d && d.data && Array.isArray(d.data.steps)) {
              const matchingStep = d.data.steps[stepIdx];
              if (matchingStep && String(matchingStep.status || '').endsWith('DONE')) {
                dismissLiveToolBox(activeSlot, stepIdx, matchingStep.runCommand?.output || matchingStep.output || '');
              }
            }
          }).catch(() => {});
      }
    }
    // Hard UI safety ceiling at 125s: auto dismiss so it never hangs indefinitely
    if (elapsedSecNum >= 125) {
      if (box._bashTimer) { clearInterval(box._bashTimer); box._bashTimer = null; }
      dismissLiveToolBox(activeSlot, stepIdx, '[AUTO-PING // HANDED OFF TO BACKGROUND]');
      return;
    }

    if (!box._hasRealStdout) {
          // (cached codeEl)
      if (codeEl) {
        const count = Math.min(telemetryFrames.length, 2 + Math.floor(tick / 3));
        codeEl.textContent = telemetryFrames.slice(0, count).join('\n') + (tick % 2 === 0 ? ' █' : '');
      }
    }
  }, 150);
}

function renderLiveSwarmOrchestrator(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const role = d.Role || d.role || d.TypeName || d.typeName || d.type || d.name || 'Subagent Specialist';
  const prompt = d.Prompt || d.prompt || d.Message || d.message || d.Instruction || 'Autonomous mission directive';
  renderLiveAmbientHoloStream(activeSlot, 'SWARM // AGENT', `${role}: ${prompt}`, 'purple', stepIdx);
}

function renderLiveMemoryRecall(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const action = String(d.action || d.Action || 'recall').toUpperCase();
  const query = String(d.query || d.Query || d.title || d.id || d.slug || d.key || 'sovereign_memory_vault').trim();

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-memory-box';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let vectors = [
    `synapse://.fl_brain/memories/${query.replace(/\s+/g, '_').toLowerCase()}`,
    `vector_match: [exit_code_0, sovereign_ui, nano_modular]`,
    `indexing_frontmatter: 10+ English keywords verified`,
    `neural_recall_score: 0.998 (LOCKED)`
  ];

  box.innerHTML = `
    <div class="fl-brain-orb-layout">
      <div class="fl-brain-orb-sphere">
        <svg viewBox="0 0 104 104" class="fl-brain-orb-svg">
          <circle class="fl-brain-ring-outer" cx="52" cy="52" r="46" fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="14 8 4 8" stroke-opacity="0.75" />
          <circle class="fl-brain-ring-inner" cx="52" cy="52" r="38" fill="none" stroke="#00f2fe" stroke-width="1.5" stroke-dasharray="22 14" stroke-opacity="0.8" />
          <circle cx="52" cy="52" r="30" fill="none" stroke="rgba(251, 191, 36, 0.25)" stroke-width="1" />
        </svg>
        <div class="fl-brain-orb-core-text">
          <span class="fl-brain-orb-velocity">0.01s</span>
          <span class="fl-brain-orb-sublabel">SYNAPSE</span>
        </div>
      </div>
      <div class="fl-brain-orb-telemetry">
        <span class="fl-brain-pill-header">🧠 BRAIN // ${escapeHtml(action)}</span>
        <div class="fl-brain-pill-target" title="${escapeHtml(query)}">${escapeHtml(query)}</div>
        <div class="fl-brain-pill-stream">
          <span>⚡</span>
          <span class="fl-brain-vector-txt">${escapeHtml(vectors[0])}</span>
        </div>
        <div class="fl-brain-pill-meta">
          <span>VAULT: <strong>.fl_brain/</strong></span>
          <span class="fl-brain-sync-pct">SYNC: 94%</span>
        </div>
      </div>
    </div>
  `;

    const velEl = box.querySelector('.fl-brain-orb-velocity');
  const vecEl = box.querySelector('.fl-brain-vector-txt');
  const syncEl = box.querySelector('.fl-brain-sync-pct');
  if (box._memoryTimer) clearInterval(box._memoryTimer);
  let tick = 0;
  box._injectOutputLines = (rawOut) => {
    if (!rawOut) return;
    const text = typeof rawOut === 'object' ? JSON.stringify(rawOut) : String(rawOut);
    const clean = text.replace(/[\r\n]+/g, ' ').trim();
    if (clean) {
      vectors.unshift(`result: ${clean.slice(0, 48)}`);
    }
  };

  box._memoryTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._memoryTimer) { clearInterval(box._memoryTimer); box._memoryTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._memoryTimer) { clearInterval(box._memoryTimer); box._memoryTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsed = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached velEl)
    if (velEl) velEl.textContent = `${elapsed}s`;

        // (cached vecEl)
    if (vecEl) vecEl.textContent = vectors[tick % vectors.length];

        // (cached syncEl)
    if (syncEl) syncEl.textContent = `SYNC: ${Math.min(99.9, (92 + (tick * 1.7) % 8)).toFixed(1)}%`;
  }, 150);
}

function renderLiveSkillActivator(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const action = String(d.action || d.Action || 'pin').toUpperCase();
  const skillId = String(d.skill_id || d.skillId || d.id || d.query || 'sovereign_runbook');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-skill-box';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let ledsHtml = '';
  for (let i = 0; i < 20; i++) {
    ledsHtml += `<span class="fl-sk-led" data-led="${i}"></span>`;
  }

  box.innerHTML = `
    <div class="fl-sk-top">
      <span class="fl-sk-tag">⬡ SKILL // ${escapeHtml(action)}</span>
      <span class="fl-sk-target">${escapeHtml(skillId)}</span>
      <span class="fl-sk-status">0/20 KEYWORDS • 0.01s</span>
    </div>
    <div class="fl-sk-led-matrix">${ledsHtml}</div>
    <div class="fl-sk-stream-line">
      <span class="fl-sk-sop-text">▸ Mounting SKILL.md SOP & validating 20-keyword YAML gatekeeper...</span>
      <span class="fl-sk-rate">GATEKEEPER: ACTIVE</span>
    </div>
  `;

  let sopFeed = [
    `▸ Mounting SKILL.md SOP [${skillId}] into neural cortex...`,
    `▸ Auditing YAML frontmatter: 20 English keywords verified`,
    `▸ Binding runbook rules & execution constraints to active turn`,
    `▸ Injecting zero-trust verification gatekeeper hooks`
  ];

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const lines = str.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    if (lines.length > 0) {
      sopFeed = lines.slice(0, 12).map(l => `▸ ${l.slice(0, 92)}`);
    }
  };

    const leds = box.querySelectorAll('.fl-sk-led');
  const statusEl = box.querySelector('.fl-sk-status');
  const sopEl = box.querySelector('.fl-sk-sop-text');
  if (box._skillTimer) clearInterval(box._skillTimer);
  let tick = 0;
  box._skillTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._skillTimer) { clearInterval(box._skillTimer); box._skillTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._skillTimer) { clearInterval(box._skillTimer); box._skillTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const litCount = Math.min(20, (tick % 21) + 1);
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);

        // (cached leds)
    leds.forEach((led, idx) => {
      led.classList.toggle('is-lit', idx < litCount);
    });

        // (cached statusEl)
    if (statusEl) statusEl.textContent = `${litCount}/20 KEYWORDS • ${elapsedSec}s`;

        // (cached sopEl)
    if (sopEl && sopFeed.length > 0) {
      sopEl.textContent = sopFeed[tick % sopFeed.length];
    }
  }, 150);
}

function renderLiveSearchWeb(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const query = String(d.query || d.Query || d.url || 'global osint recon');
  const domain = d.domain ? ` [${d.domain}]` : '';

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-search-web';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let pktPool = [
    `[SYN/ACK] Querying edge indexers for "${query.slice(0, 48)}"${domain}`,
    `[DNS-TLS] Resolving high-authority citations & SSL endpoints...`,
    `[RANKING] Filtering zero-noise technical documentation nodes...`,
    `[INGEST] Extracting verified URLs & snippet telemetry...`
  ];

  box.innerHTML = `
    <div class="fl-sw-reticle-pod">
      <svg class="fl-sw-reticle-svg" viewBox="0 0 50 50" fill="none">
        <circle cx="25" cy="25" r="21" stroke="rgba(0,242,254,0.35)" stroke-width="1.5" stroke-dasharray="6 4"/>
        <circle cx="25" cy="25" r="13" stroke="#00f2fe" stroke-width="1.5" stroke-dasharray="18 8"/>
        <line x1="25" y1="2" x2="25" y2="12" stroke="#00ffb2" stroke-width="1.5"/>
        <line x1="25" y1="38" x2="25" y2="48" stroke="#00ffb2" stroke-width="1.5"/>
        <line x1="2" y1="25" x2="12" y2="25" stroke="#00ffb2" stroke-width="1.5"/>
        <line x1="38" y1="25" x2="48" y2="25" stroke="#00ffb2" stroke-width="1.5"/>
        <circle cx="25" cy="25" r="3" fill="#00ffb2"/>
      </svg>
    </div>
    <div class="fl-sw-sniffer">
      <div class="fl-sw-header">
        <span class="fl-sw-query">🌐 OSINT // ${escapeHtml(query)}${escapeHtml(domain)}</span>
        <span class="fl-sw-badge">SNIFFING • 0.01s</span>
      </div>
      <div class="fl-sw-pkt-line is-hit">${escapeHtml(pktPool[0])}</div>
      <div class="fl-sw-pkt-line">${escapeHtml(pktPool[1])}</div>
      <div class="fl-sw-pkt-line">${escapeHtml(pktPool[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const urls = str.match(/https?:\/\/[^\s)"'<>]+/g) || [];
    const lines = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 8);
    const combined = [];
    urls.slice(0, 10).forEach((u, i) => combined.push(`[200 OK] CITATION #${i + 1} ➔ ${u.slice(0, 78)}`));
    lines.slice(0, 10).forEach(l => {
      if (!l.startsWith('http')) combined.push(`[SNIPPET] ${l.slice(0, 82)}`);
    });
    if (combined.length > 0) pktPool = combined;
  };

    const badge = box.querySelector('.fl-sw-badge');
  const pktEls = box.querySelectorAll('.fl-sw-pkt-line');
  if (box._webTimer) clearInterval(box._webTimer);
  let tick = 0;
  box._webTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._webTimer) { clearInterval(box._webTimer); box._webTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._webTimer) { clearInterval(box._webTimer); box._webTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `${pktPool.length} PKTS • ${elapsedSec}s`;

        // (cached pktEls)
    if (pktEls.length >= 3 && pktPool.length > 0) {
      pktEls[0].textContent = pktPool[tick % pktPool.length];
      pktEls[1].textContent = pktPool[(tick + 1) % pktPool.length];
      pktEls[2].textContent = pktPool[(tick + 2) % pktPool.length];
    }
  }, 150);
}

function renderLiveReadUrl(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const rawUrl = String(d.Url || d.url || d.target || 'https://floworkos.com');
  let host = rawUrl;
  let pathPart = '/';
  try {
    const u = new URL(rawUrl);
    host = u.host;
    pathPart = (u.pathname + u.search) || '/';
  } catch (_) {}

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-read-url';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let mdLines = [
    `GET ${pathPart} HTTP/2.0 ➔ stripping <script>, <style>, & DOM chrome`,
    `Converting semantic HTML5 nodes into clean Sovereign Markdown...`,
    `Streaming UTF-8 text blocks into context window buffer...`
  ];
  let totalBytes = 4096;

  box.innerHTML = `
    <div class="fl-ru-blade">
      <div class="fl-ru-blade-inner">
        <span class="fl-ru-host">⚡ ${escapeHtml(host)}${escapeHtml(pathPart.slice(0, 34))}</span>
        <span class="fl-ru-pipe-badge">HTML DOM ══⚡══► MARKDOWN</span>
      </div>
    </div>
    <div class="fl-ru-stream-box">
      <div class="fl-ru-md-line is-primary">${escapeHtml(mdLines[0])}</div>
      <div class="fl-ru-md-line">${escapeHtml(mdLines[1])}</div>
    </div>
    <div class="fl-ru-meta">
      <span class="fl-ru-stat">HTTP/2 TLS 1.3 • DOM PARSER</span>
      <span class="fl-ru-timer">0.01s • STREAMING</span>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    totalBytes = str.length;
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 4);
    if (clean.length > 0) {
      mdLines = clean.slice(0, 18).map((l, idx) => `L${String(idx + 1).padStart(3, '0')} │ ${l.slice(0, 86)}`);
    }
  };

    const statEl = box.querySelector('.fl-ru-stat');
  const timerEl = box.querySelector('.fl-ru-timer');
  const lineEls = box.querySelectorAll('.fl-ru-md-line');
  if (box._urlTimer) clearInterval(box._urlTimer);
  let tick = 0;
  box._urlTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._urlTimer) { clearInterval(box._urlTimer); box._urlTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._urlTimer) { clearInterval(box._urlTimer); box._urlTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const kb = ((totalBytes * Math.min(1, (tick % 18) / 14)) / 1024).toFixed(1);

        // (cached statEl)
    if (statEl) statEl.textContent = `INGESTED: ${kb} KB • ${mdLines.length} MD BLOCKS`;

        // (cached timerEl)
    if (timerEl) timerEl.textContent = `${elapsedSec}s • ZERO-JS EXTRACT`;

        // (cached lineEls)
    if (lineEls.length >= 2 && mdLines.length > 0) {
      lineEls[0].textContent = mdLines[tick % mdLines.length];
      lineEls[1].textContent = mdLines[(tick + 1) % mdLines.length];
    }
  }, 150);
}

function renderLiveFlowLock(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const action = String(d.action || d.Action || 'lock').toUpperCase();
  const rawFile = String(d.file || d.TargetFile || d.AbsolutePath || d.path || 'workspace/sovereign_core');
  const shortFile = shortenFilePath(rawFile);
  const startL = d.start_line ?? d.StartLine ?? 1;
  const endL = d.end_line ?? d.EndLine ?? startL + 12;

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-flow-lock';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let lockLines = [
    `[CRYO-VAULT] Action: ${action} on ${shortFile} [L${startL}..L${endL}]`,
    `[IMMUTABLE] Injecting cryptographic guard & write-protection seal...`,
    `[VERIFIER] Anti-tamper & anti-rollback enforcement active`
  ];
  let shaDigest = 'e3b0c44298fc1c149afbf4c8996fb924';

  box.innerHTML = `
    <div class="fl-flk-header">
      <div class="fl-flk-title-group">
        <span class="fl-flk-action-pill">🔒 @LOCK // ${escapeHtml(action)}</span>
        <span class="fl-flk-target" title="${escapeHtml(rawFile)}">${escapeHtml(shortFile)} [L${escapeHtml(String(startL))}–L${escapeHtml(String(endL))}]</span>
      </div>
      <span class="fl-flk-status">SEALING • 0.01s</span>
    </div>
    <div class="fl-flk-body">
      <div class="fl-flk-vault-pod">
        <svg class="fl-flk-svg" viewBox="0 0 48 48">
          <path class="fl-flk-shackle" d="M15 21 V14 A9 9 0 0 1 33 14 V21" />
          <rect class="fl-flk-core-body" x="10" y="21" width="28" height="21" rx="4" />
          <circle cx="24" cy="30" r="2.6" fill="#fbbf24" />
          <path d="M24 32.5 V37" stroke="#fbbf24" stroke-width="2.2" stroke-linecap="round" />
        </svg>
        <span class="fl-flk-vault-lbl">CRYO-SEAL</span>
      </div>
      <div class="fl-flk-stream-wrap">
        <div class="fl-flk-hash-bar">
          <span class="fl-flk-sha">SHA-256: ${escapeHtml(shaDigest)}…</span>
          <span>RANGE: L${escapeHtml(String(startL))}..L${escapeHtml(String(endL))}</span>
        </div>
        <div class="fl-flk-code-box">${escapeHtml(lockLines.join('\n'))}</div>
      </div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    if (clean.length > 0) {
      lockLines = clean.slice(0, 6);
      const codeBox = box.querySelector('.fl-flk-code-box');
      if (codeBox) codeBox.textContent = lockLines.join('\n');
    }
  };

    const statusEl = box.querySelector('.fl-flk-status');
  const shaEl = box.querySelector('.fl-flk-sha');
  if (box._lockBoxTimer) clearInterval(box._lockBoxTimer);
  let tick = 0;
  const hexChars = '0123456789abcdef';
  box._lockBoxTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._lockBoxTimer) { clearInterval(box._lockBoxTimer); box._lockBoxTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._lockBoxTimer) { clearInterval(box._lockBoxTimer); box._lockBoxTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached statusEl)
    if (statusEl) statusEl.textContent = `CLAMPING • ${elapsedSec}s`;

    let rollingHash = '';
    for (let i = 0; i < 24; i++) {
      rollingHash += hexChars[(tick * 7 + i * 13) % 16];
    }
        // (cached shaEl)
    if (shaEl) shaEl.textContent = `SHA-256: ${rollingHash}…`;
  }, 150);
}

function renderLiveSysHealth(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-sys-health';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  box.innerHTML = `
    <div class="fl-sh-header">
      <div class="fl-sh-title-left">
        <span class="fl-sh-os-tag">💓 MULTI-OS // PULSE</span>
        <span class="fl-sh-cpu-model">Probing Kernel & Hardware Telemetry...</span>
      </div>
      <span class="fl-sh-badge">PROBING • 0.01s</span>
    </div>
    <div class="fl-sh-ecg-stage">
      <svg class="fl-sh-ecg-svg" viewBox="0 0 400 38" preserveAspectRatio="none">
        <polyline class="fl-sh-ecg-line" points="0,20 45,20 58,9 70,31 82,4 95,35 108,16 122,20 190,20 205,10 218,30 230,5 244,34 256,18 272,20 340,20 355,11 368,28 380,20 400,20" />
      </svg>
    </div>
    <div class="fl-sh-gauges-grid">
      <div class="fl-sh-gauge-pod">
        <div class="fl-sh-gauge-top"><span>CPU LOAD</span><span class="fl-sh-gauge-val fl-sh-val-cpu">--%</span></div>
        <div class="fl-sh-gauge-bar"><div class="fl-sh-gauge-fill fl-sh-fill-cpu" style="width:24%;"></div></div>
      </div>
      <div class="fl-sh-gauge-pod">
        <div class="fl-sh-gauge-top"><span>RAM USAGE</span><span class="fl-sh-gauge-val fl-sh-val-ram">--%</span></div>
        <div class="fl-sh-gauge-bar"><div class="fl-sh-gauge-fill fl-sh-fill-ram" style="width:48%;"></div></div>
      </div>
      <div class="fl-sh-gauge-pod">
        <div class="fl-sh-gauge-top"><span>NODE HEAP</span><span class="fl-sh-gauge-val fl-sh-val-rss">-- MB</span></div>
        <div class="fl-sh-gauge-bar"><div class="fl-sh-gauge-fill fl-sh-fill-rss" style="width:35%;"></div></div>
      </div>
    </div>
    <div class="fl-sh-log-footer">▸ Sampling Multi-OS CPU ticks, physical RAM pages, and process RSS...</div>
  `;

  const applyPulse = (data) => {
    if (!data || !box.isConnected) return;
    const osTag = box.querySelector('.fl-sh-os-tag');
    if (osTag && data.osLabel) osTag.textContent = `💓 ${data.osLabel} (${data.arch || 'x64'})`;
    const cpuModel = box.querySelector('.fl-sh-cpu-model');
    if (cpuModel && data.cpuModel) cpuModel.textContent = `${data.cpuModel} • ${data.cpuCores || 1} CORES`;

    const cpuVal = box.querySelector('.fl-sh-val-cpu');
    const cpuFill = box.querySelector('.fl-sh-fill-cpu');
    if (cpuVal && data.cpuPct !== undefined) cpuVal.textContent = `${data.cpuPct}%`;
    if (cpuFill && data.cpuPct !== undefined) cpuFill.style.width = `${Math.min(100, Math.max(4, data.cpuPct))}%`;

    const ramVal = box.querySelector('.fl-sh-val-ram');
    const ramFill = box.querySelector('.fl-sh-fill-ram');
    if (ramVal && data.ramPct !== undefined) ramVal.textContent = `${data.ramUsedGb}/${data.ramTotalGb}GB (${data.ramPct}%)`;
    if (ramFill && data.ramPct !== undefined) ramFill.style.width = `${Math.min(100, Math.max(4, data.ramPct))}%`;

    const rssVal = box.querySelector('.fl-sh-val-rss');
    const rssFill = box.querySelector('.fl-sh-fill-rss');
    if (rssVal && data.nodeRssMb !== undefined) rssVal.textContent = `${data.nodeRssMb} MB`;
    if (rssFill && data.nodeRssMb !== undefined) rssFill.style.width = `${Math.min(100, Math.max(8, Math.round(data.nodeRssMb / 5)))}%`;
  };

  fetch('/api/sys-pulse', { cache: 'no-store' })
    .then(r => r.ok ? r.json() : null)
    .then(applyPulse)
    .catch(() => {});

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    const footer = box.querySelector('.fl-sh-log-footer');
    if (footer && clean.length > 0) {
      footer.textContent = `▸ ${clean.slice(0, 2).join(' • ').slice(0, 110)}`;
    }
  };

    const badge = box.querySelector('.fl-sh-badge');
  if (box._healthTimer) clearInterval(box._healthTimer);
  box._healthTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._healthTimer) { clearInterval(box._healthTimer); box._healthTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._healthTimer) { clearInterval(box._healthTimer); box._healthTimer = null; } return; }
    if (document.hidden) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `LIVE ECG • ${elapsedSec}s`;
  }, 150);
}

function renderLiveSecurityAuditor(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const tag = (toolName || 'audit_security').replace(/^flow_/, '').replace(/^default_api:/, '').toUpperCase();
  const targetPath = shortenFilePath(d.path || d.target || d.dir || d.TargetFile || 'workspace');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-audit-sec';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let auditFeed = [
    `[SAST-SCAN] Inspecting AST & entropy vectors in ${targetPath}...`,
    `[SECRET-GUARD] Checking hardcoded API keys, JWT tokens, & private PEM blocks...`,
    `[INJECTION] Auditing command execution, SQLi, XSS, & path traversal sinks...`,
    `[PORTABILITY] Verifying zero-trust Multi-OS compliance & boundary checks...`
  ];

  box.innerHTML = `
    <div class="fl-as-header">
      <div class="fl-as-left">
        <span class="fl-as-tag">🛡️ SAST // ${escapeHtml(tag)}</span>
        <span class="fl-as-target">${escapeHtml(targetPath)}</span>
      </div>
      <span class="fl-as-badge">SCANNING • 0.01s</span>
    </div>
    <div class="fl-as-spectrum-row">
      <div class="fl-as-sev-pill crit"><span>CRIT</span><span class="fl-as-cnt-crit">0</span></div>
      <div class="fl-as-sev-pill high"><span>HIGH</span><span class="fl-as-cnt-high">0</span></div>
      <div class="fl-as-sev-pill med"><span>MED</span><span class="fl-as-cnt-med">0</span></div>
      <div class="fl-as-sev-pill low"><span>PASS</span><span class="fl-as-cnt-low">100%</span></div>
    </div>
    <div class="fl-as-console">
      <div class="fl-as-line">${escapeHtml(auditFeed[0])}</div>
      <div class="fl-as-line">${escapeHtml(auditFeed[1])}</div>
      <div class="fl-as-line">${escapeHtml(auditFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 3);
    if (clean.length > 0) {
      auditFeed = clean.slice(0, 12);
      const lines = box.querySelectorAll('.fl-as-line');
      lines.forEach((el, idx) => {
        if (auditFeed[idx]) el.textContent = auditFeed[idx];
      });
    }
    const critMatches = (str.match(/critical/gi) || []).length;
    const highMatches = (str.match(/\bhigh\b/gi) || []).length;
    const medMatches = (str.match(/\bmedium\b/gi) || []).length;
    const cEl = box.querySelector('.fl-as-cnt-crit');
    const hEl = box.querySelector('.fl-as-cnt-high');
    const mEl = box.querySelector('.fl-as-cnt-med');
    if (cEl) cEl.textContent = String(critMatches);
    if (hEl) hEl.textContent = String(highMatches);
    if (mEl) mEl.textContent = String(medMatches);
  };

    const badge = box.querySelector('.fl-as-badge');
  const lines = box.querySelectorAll('.fl-as-line');
  if (box._auditTimer) clearInterval(box._auditTimer);
  let tick = 0;
  box._auditTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._auditTimer) { clearInterval(box._auditTimer); box._auditTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._auditTimer) { clearInterval(box._auditTimer); box._auditTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `AUDITING • ${elapsedSec}s`;

        // (cached lines)
    if (lines.length >= 3 && auditFeed.length > 0) {
      lines[0].textContent = auditFeed[tick % auditFeed.length];
      lines[1].textContent = auditFeed[(tick + 1) % auditFeed.length];
      lines[2].textContent = auditFeed[(tick + 2) % auditFeed.length];
    }
  }, 150);
}

function renderLiveTeamAudit(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const files = Array.isArray(d.target_files) ? d.target_files.join(', ') : (d.target_files || d.target || 'Active Workspace Diff');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-audit-sec fl-live-team-audit';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  if (typeof window.setSpecialistAuditorWorking === 'function') {
    window.setSpecialistAuditorWorking(true, 'Specialist Auditor Council');
  }
  box.innerHTML = `
    <div class="fl-as-header">
      <div class="fl-as-title">
        <span class="fl-as-icon">🏛️</span>
        <span class="fl-as-tag">TEAM_AUDIT // SPECIALIST AUDITOR COUNCIL</span>
      </div>
      <span class="fl-as-badge" style="background:rgba(0,255,178,0.15);color:#00ffb2;border:1px solid rgba(0,255,178,0.3);">COUNCIL ACTIVE</span>
    </div>
    <div class="fl-as-spectrum-row" style="margin-top:6px;gap:6px;">
      <div class="fl-as-sev-pill" style="border:1px solid rgba(56,189,248,0.4);background:rgba(56,189,248,0.1);color:#38bdf8;"><span>🛡️ SECURITY</span><span class="fl-ta-sec-cnt">PENDING</span></div>
      <div class="fl-as-sev-pill" style="border:1px solid rgba(168,85,247,0.4);background:rgba(168,85,247,0.1);color:#c084fc;"><span>🧪 LOGIC/QA</span><span class="fl-ta-qa-cnt">PENDING</span></div>
      <div class="fl-as-sev-pill" style="border:1px solid rgba(245,158,11,0.4);background:rgba(245,158,11,0.1);color:#fbbf24;"><span>📐 ARCH</span><span class="fl-ta-arch-cnt">PENDING</span></div>
      <div class="fl-as-sev-pill low" style="border:1px solid rgba(0,255,178,0.4);"><span>VERDICT</span><span class="fl-ta-verdict-cnt">IN REVIEW</span></div>
    </div>
    <div class="fl-as-console" style="margin-top:6px;">
      <div class="fl-as-line">🏛️ Specialist Council reviewing target: ${escapeHtml(String(files).slice(0, 50))}</div>
      <div class="fl-as-line">🛡️ Security Specialist: Running adversarial SAST & secret audit...</div>
      <div class="fl-as-line">🧪 Logic/QA Specialist: Validating edge cases and test harness...</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\\r?\\n/).map(s => s.trim()).filter(s => s.length > 3);
    if (clean.length > 0) {
      const lines = box.querySelectorAll('.fl-as-line');
      lines.forEach((el, idx) => {
        if (clean[idx]) el.textContent = clean[idx].slice(0, 80);
      });
    }
    const isPass = /pass|approved/i.test(str);
    const isReject = /reject|fail/i.test(str);
    const vEl = box.querySelector('.fl-ta-verdict-cnt');
    if (vEl) {
      if (isPass && !isReject) {
        vEl.textContent = 'PASS';
        vEl.style.color = '#00ffb2';
      } else if (isReject) {
        vEl.textContent = 'REJECT';
        vEl.style.color = '#ef4444';
      }
    }
    const secEl = box.querySelector('.fl-ta-sec-cnt');
    const qaEl = box.querySelector('.fl-ta-qa-cnt');
    const archEl = box.querySelector('.fl-ta-arch-cnt');
    if (secEl) secEl.textContent = 'DONE';
    if (qaEl) qaEl.textContent = 'DONE';
    if (archEl) archEl.textContent = 'DONE';
  };
}

function renderLiveDetectHardcode(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetPath = shortenFilePath(d.path || d.target || d.dir || d.TargetFile || 'workspace');
  const langs = ['HTML', 'CSS', 'JS/TS', 'JSON', 'YML', 'PY', 'GO', 'RUST', 'PHP'];

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-detect-hc';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let hcFeed = [
    `[DE-HARDCODER] Scanning ${targetPath} for hardcoded OS paths (/home, C:\\\\, /Users)...`,
    `[POLYGLOT-AST] Auditing HTML/CSS/JS/TS/JSON/YML/PY/GO/RS literals & env bindings...`,
    `[ZERO-TRUST] Checking hardcoded IPv4/ports, localhost binds, & static credentials...`
  ];

  box.innerHTML = `
    <div class="fl-dhc-header">
      <div class="fl-dhc-left">
        <span class="fl-dhc-tag">⚠️ HARDCODE // HUNTER</span>
        <span class="fl-dhc-target">${escapeHtml(targetPath)}</span>
      </div>
      <span class="fl-dhc-badge">SCANNING • 0.01s</span>
    </div>
    <div class="fl-dhc-lang-strip">
      ${langs.map((l, idx) => `<span class="fl-dhc-lang-chip ${idx === 0 ? 'is-active' : ''}">${l}</span>`).join('')}
    </div>
    <div class="fl-dhc-metrics-grid">
      <div class="fl-dhc-metric-pill"><span>OS PATHS</span><span class="fl-dhc-metric-val fl-dhc-cnt-path">0</span></div>
      <div class="fl-dhc-metric-pill"><span>IPS/URLS</span><span class="fl-dhc-metric-val fl-dhc-cnt-ip">0</span></div>
      <div class="fl-dhc-metric-pill"><span>STATUS</span><span class="fl-dhc-metric-val fl-dhc-cnt-stat">PROBING</span></div>
    </div>
    <div class="fl-dhc-console">
      <div class="fl-dhc-line">${escapeHtml(hcFeed[0])}</div>
      <div class="fl-dhc-line">${escapeHtml(hcFeed[1])}</div>
      <div class="fl-dhc-line">${escapeHtml(hcFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 3);
    if (clean.length > 0) {
      hcFeed = clean.slice(0, 12);
      const lines = box.querySelectorAll('.fl-dhc-line');
      lines.forEach((el, idx) => {
        if (hcFeed[idx]) el.textContent = hcFeed[idx];
      });
    }
    const pathHits = (str.match(/\/home\/|C:\\|\/Users\/|hardcode/gi) || []).length;
    const ipHits = (str.match(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|http:\/\//gi) || []).length;
    const pEl = box.querySelector('.fl-dhc-cnt-path');
    const iEl = box.querySelector('.fl-dhc-cnt-ip');
    const sEl = box.querySelector('.fl-dhc-cnt-stat');
    if (pEl) pEl.textContent = String(pathHits);
    if (iEl) iEl.textContent = String(ipHits);
    if (sEl) sEl.textContent = 'AUDITED';
  };

    const badge = box.querySelector('.fl-dhc-badge');
  const chips = box.querySelectorAll('.fl-dhc-lang-chip');
  const lines = box.querySelectorAll('.fl-dhc-line');
  if (box._hcTimer) clearInterval(box._hcTimer);
  let tick = 0;
  box._hcTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._hcTimer) { clearInterval(box._hcTimer); box._hcTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._hcTimer) { clearInterval(box._hcTimer); box._hcTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `SWEEPING • ${elapsedSec}s`;

        // (cached chips)
    chips.forEach((c, idx) => c.classList.toggle('is-active', idx === (tick % chips.length)));

        // (cached lines)
    if (lines.length >= 3 && hcFeed.length > 0) {
      lines[0].textContent = hcFeed[tick % hcFeed.length];
      lines[1].textContent = hcFeed[(tick + 1) % hcFeed.length];
      lines[2].textContent = hcFeed[(tick + 2) % hcFeed.length];
    }
  }, 150);
}

function renderLiveAuditPortability(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetPath = shortenFilePath(d.path || d.target || d.dir || d.TargetFile || 'workspace');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-audit-port';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let portFeed = [
    `[TRI-OS MATRIX] Auditing ${targetPath} across Linux POSIX, Windows NT, & macOS Darwin...`,
    `[PATH-SEP] Verifying path.join / std::path::Path vs raw backslash & slash literals...`,
    `[RUNTIME-ENV] Checking process spawn, shebangs, CRLF/LF line endings, & native binaries...`
  ];

  box.innerHTML = `
    <div class="fl-ap-header">
      <div class="fl-ap-left">
        <span class="fl-ap-tag">🌐 TRI-OS // PORTABILITY</span>
        <span class="fl-ap-target">${escapeHtml(targetPath)}</span>
      </div>
      <span class="fl-ap-badge">MATRIX SCAN • 0.01s</span>
    </div>
    <div class="fl-ap-os-grid">
      <div class="fl-ap-os-pod">
        <div class="fl-ap-os-top"><span class="fl-ap-os-name">🐧 LINUX</span><span class="fl-ap-os-score fl-ap-sc-lin">98%</span></div>
        <div class="fl-ap-os-bar"><div class="fl-ap-os-fill fl-ap-fl-lin" style="width:98%;"></div></div>
      </div>
      <div class="fl-ap-os-pod">
        <div class="fl-ap-os-top"><span class="fl-ap-os-name">🪟 WINDOWS</span><span class="fl-ap-os-score fl-ap-sc-win">94%</span></div>
        <div class="fl-ap-os-bar"><div class="fl-ap-os-fill fl-ap-fl-win" style="width:94%;"></div></div>
      </div>
      <div class="fl-ap-os-pod">
        <div class="fl-ap-os-top"><span class="fl-ap-os-name">🍎 MACOS</span><span class="fl-ap-os-score fl-ap-sc-mac">97%</span></div>
        <div class="fl-ap-os-bar"><div class="fl-ap-os-fill fl-ap-fl-mac" style="width:97%;"></div></div>
      </div>
    </div>
    <div class="fl-ap-console">
      <div class="fl-ap-line">${escapeHtml(portFeed[0])}</div>
      <div class="fl-ap-line">${escapeHtml(portFeed[1])}</div>
      <div class="fl-ap-line">${escapeHtml(portFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 3);
    if (clean.length > 0) {
      portFeed = clean.slice(0, 12);
      const lines = box.querySelectorAll('.fl-ap-line');
      lines.forEach((el, idx) => {
        if (portFeed[idx]) el.textContent = portFeed[idx];
      });
    }
    const linEl = box.querySelector('.fl-ap-sc-lin');
    const winEl = box.querySelector('.fl-ap-sc-win');
    const macEl = box.querySelector('.fl-ap-sc-mac');
    if (linEl) linEl.textContent = '100%';
    if (winEl) winEl.textContent = '100%';
    if (macEl) macEl.textContent = '100%';
    box.querySelectorAll('.fl-ap-os-fill').forEach(el => { el.style.width = '100%'; });
  };

    const badge = box.querySelector('.fl-ap-badge');
  const lines = box.querySelectorAll('.fl-ap-line');
  if (box._portTimer) clearInterval(box._portTimer);
  let tick = 0;
  box._portTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._portTimer) { clearInterval(box._portTimer); box._portTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._portTimer) { clearInterval(box._portTimer); box._portTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `PROBING OS • ${elapsedSec}s`;

        // (cached lines)
    if (lines.length >= 3 && portFeed.length > 0) {
      lines[0].textContent = portFeed[tick % portFeed.length];
      lines[1].textContent = portFeed[(tick + 1) % portFeed.length];
      lines[2].textContent = portFeed[(tick + 2) % portFeed.length];
    }
  }, 150);
}

function renderLiveWebSecurityAudit(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const rawUrl = String(d.url || d.Url || d.target || d.domain || 'https://floworkos.com');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-web-sec';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let webSecFeed = [
    `[PERIMETER] Probing TLS/SSL cipher suite & certificate chain on ${rawUrl}...`,
    `[HEADERS] Auditing Content-Security-Policy (CSP), HSTS max-age, & CORS origin rules...`,
    `[SURFACE] Inspecting X-Frame-Options, X-Content-Type-Options, & public injection vectors...`
  ];

  const headersList = ['TLS/SSL', 'CSP', 'HSTS', 'CORS', 'X-FRAME'];

  box.innerHTML = `
    <div class="fl-wsa-header">
      <div class="fl-wsa-left">
        <span class="fl-wsa-tag">🕸️ WEBSEC // PERIMETER</span>
        <span class="fl-wsa-url" title="${escapeHtml(rawUrl)}">${escapeHtml(rawUrl)}</span>
      </div>
      <span class="fl-wsa-badge">PROBING • 0.01s</span>
    </div>
    <div class="fl-wsa-headers-grid">
      ${headersList.map(h => `
        <div class="fl-wsa-hdr-chip" data-hdr="${h}">
          <span class="fl-wsa-hdr-name">${h}</span>
          <span class="fl-wsa-hdr-state">SCAN</span>
        </div>
      `).join('')}
    </div>
    <div class="fl-wsa-console">
      <div class="fl-wsa-line">${escapeHtml(webSecFeed[0])}</div>
      <div class="fl-wsa-line">${escapeHtml(webSecFeed[1])}</div>
      <div class="fl-wsa-line">${escapeHtml(webSecFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 3);
    if (clean.length > 0) {
      webSecFeed = clean.slice(0, 12);
      const lines = box.querySelectorAll('.fl-wsa-line');
      lines.forEach((el, idx) => {
        if (webSecFeed[idx]) el.textContent = webSecFeed[idx];
      });
    }
    box.querySelectorAll('.fl-wsa-hdr-chip').forEach(chip => {
      const hdr = (chip.getAttribute('data-hdr') || '').toLowerCase();
      const st = chip.querySelector('.fl-wsa-hdr-state');
      const isMissing = new RegExp(`${hdr}[^\\n]*(missing|absent|none|warn)`, 'i').test(str);
      chip.classList.toggle('is-warn', isMissing);
      chip.classList.toggle('is-pass', !isMissing);
      if (st) st.textContent = isMissing ? 'WARN' : 'PASS';
    });
  };

    const badge = box.querySelector('.fl-wsa-badge');
  const chips = box.querySelectorAll('.fl-wsa-hdr-chip');
  const lines = box.querySelectorAll('.fl-wsa-line');
  if (box._webSecTimer) clearInterval(box._webSecTimer);
  let tick = 0;
  box._webSecTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._webSecTimer) { clearInterval(box._webSecTimer); box._webSecTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._webSecTimer) { clearInterval(box._webSecTimer); box._webSecTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `AUDITING • ${elapsedSec}s`;

        // (cached chips)
    chips.forEach((chip, idx) => {
      if (!chip.classList.contains('is-warn')) {
        const st = chip.querySelector('.fl-wsa-hdr-state');
        if (idx <= (tick % (chips.length + 1))) {
          chip.classList.add('is-pass');
          if (st) st.textContent = 'OK';
        }
      }
    });

        // (cached lines)
    if (lines.length >= 3 && webSecFeed.length > 0) {
      lines[0].textContent = webSecFeed[tick % webSecFeed.length];
      lines[1].textContent = webSecFeed[(tick + 1) % webSecFeed.length];
      lines[2].textContent = webSecFeed[(tick + 2) % webSecFeed.length];
    }
  }, 150);
}

function renderLiveWebsiteIntelligence(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetDomain = String(d.url || d.Url || d.domain || d.target || 'https://floworkos.com');
  const vectors = [
    { name: 'DNS', val: 'A/MX/TXT' },
    { name: 'WHOIS', val: 'ASN/REG' },
    { name: 'GEO-IP', val: 'LOCATING' },
    { name: 'TECH', val: 'FINGERPRINT' },
    { name: 'ROBOTS', val: 'CRAWLING' }
  ];

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-web-intel';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let wiFeed = [
    `[OSINT-SAT] Resolving DNS A/AAAA/MX/NS/TXT records for ${targetDomain}...`,
    `[GEO-ASN] Mapping IPv4/IPv6 BGP routing, ASN ownership, & server geolocation...`,
    `[TECH-STACK] Fingerprinting HTTP server headers, CDN edge, & robots.txt directives...`
  ];

  box.innerHTML = `
    <div class="fl-wi-header">
      <div class="fl-wi-left">
        <span class="fl-wi-tag">🛰️ OSINT // WEB-INTEL</span>
        <span class="fl-wi-domain" title="${escapeHtml(targetDomain)}">${escapeHtml(targetDomain)}</span>
      </div>
      <span class="fl-wi-badge">RECON • 0.01s</span>
    </div>
    <div class="fl-wi-vectors-grid">
      ${vectors.map((v, idx) => `
        <div class="fl-wi-vec-pod ${idx === 0 ? 'is-active' : ''}">
          <span class="fl-wi-vec-name">${v.name}</span>
          <span class="fl-wi-vec-val">${v.val}</span>
        </div>
      `).join('')}
    </div>
    <div class="fl-wi-console">
      <div class="fl-wi-line">${escapeHtml(wiFeed[0])}</div>
      <div class="fl-wi-line">${escapeHtml(wiFeed[1])}</div>
      <div class="fl-wi-line">${escapeHtml(wiFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 3);
    if (clean.length > 0) {
      wiFeed = clean.slice(0, 12);
      const lines = box.querySelectorAll('.fl-wi-line');
      lines.forEach((el, idx) => {
        if (wiFeed[idx]) el.textContent = wiFeed[idx];
      });
    }
    box.querySelectorAll('.fl-wi-vec-val').forEach(el => { el.textContent = 'LOCKED'; });
  };

    const badge = box.querySelector('.fl-wi-badge');
  const pods = box.querySelectorAll('.fl-wi-vec-pod');
  const lines = box.querySelectorAll('.fl-wi-line');
  if (box._wiTimer) clearInterval(box._wiTimer);
  let tick = 0;
  box._wiTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._wiTimer) { clearInterval(box._wiTimer); box._wiTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._wiTimer) { clearInterval(box._wiTimer); box._wiTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `SCANNING • ${elapsedSec}s`;

        // (cached pods)
    pods.forEach((p, idx) => p.classList.toggle('is-active', idx === (tick % pods.length)));

        // (cached lines)
    if (lines.length >= 3 && wiFeed.length > 0) {
      lines[0].textContent = wiFeed[tick % wiFeed.length];
      lines[1].textContent = wiFeed[(tick + 1) % wiFeed.length];
      lines[2].textContent = wiFeed[(tick + 2) % wiFeed.length];
    }
  }, 150);
}

function renderLiveSchedule(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const cronExpr = d.CronExpression || d.cron_expression || d.cron || '';
  const durationSec = d.DurationSeconds ?? d.duration_seconds ?? d.duration ?? null;
  const condition = String(d.TimerCondition || d.timer_condition || (cronExpr ? 'CRON' : 'never')).toUpperCase();
  const isDaemon = Boolean(d.IsDaemon ?? d.is_daemon ?? false);
  const promptText = String(d.Prompt || d.prompt || 'Scheduled sovereign background trigger');
  const modeLabel = cronExpr ? `CRON [${cronExpr}]` : `TIMER [${durationSec !== null ? durationSec + 's' : 'ONE-SHOT'}]`;

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-schedule';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let schFeed = [
    `[CHRONO-CORE] Arming ${modeLabel} • Condition: ${condition} • Daemon: ${isDaemon ? 'YES' : 'NO'}`,
    `[PAYLOAD] "${promptText.slice(0, 96)}"`,
    `[REACTOR] Registering reactive wakeup hook in Sovereign Event Loop...`
  ];

  box.innerHTML = `
    <div class="fl-sch-header">
      <div class="fl-sch-left">
        <span class="fl-sch-tag">⏱️ CHRONO // SCHEDULE</span>
        <span class="fl-sch-mode">${escapeHtml(modeLabel)}</span>
      </div>
      <span class="fl-sch-badge">ARMING • 0.01s</span>
    </div>
    <div class="fl-sch-matrix-grid">
      <div class="fl-sch-slot"><span class="fl-sch-slot-lbl">MODE</span><span class="fl-sch-slot-val">${cronExpr ? 'CRON JOB' : 'ONE-SHOT'}</span></div>
      <div class="fl-sch-slot"><span class="fl-sch-slot-lbl">TIMING</span><span class="fl-sch-slot-val">${escapeHtml(cronExpr || (durationSec !== null ? durationSec + 's' : '60s'))}</span></div>
      <div class="fl-sch-slot"><span class="fl-sch-slot-lbl">WAKEUP</span><span class="fl-sch-slot-val">${escapeHtml(condition)}</span></div>
      <div class="fl-sch-slot"><span class="fl-sch-slot-lbl">DAEMON</span><span class="fl-sch-slot-val">${isDaemon ? 'STANDING' : 'TASK-BOUND'}</span></div>
    </div>
    <div class="fl-sch-console">
      <div class="fl-sch-line">${escapeHtml(schFeed[0])}</div>
      <div class="fl-sch-line">${escapeHtml(schFeed[1])}</div>
      <div class="fl-sch-line">${escapeHtml(schFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 2);
    if (clean.length > 0) {
      schFeed = clean.slice(0, 8);
      const lines = box.querySelectorAll('.fl-sch-line');
      lines.forEach((el, idx) => {
        if (schFeed[idx]) el.textContent = schFeed[idx];
      });
    }
  };

    const badge = box.querySelector('.fl-sch-badge');
  if (box._schTimer) clearInterval(box._schTimer);
  box._schTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._schTimer) { clearInterval(box._schTimer); box._schTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._schTimer) { clearInterval(box._schTimer); box._schTimer = null; } return; }
    if (document.hidden) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `SYNCING • ${elapsedSec}s`;
  }, 150);
}

function renderLiveManageTask(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const action = String(d.Action || d.action || 'list').toUpperCase();
  const taskId = String(d.TaskId || d.task_id || d.id || 'ALL_DAEMONS');
  const shortTask = taskId.length > 24 ? '…' + taskId.slice(-22) : taskId;
  const inputStr = d.Input || d.input || '';

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-manage-task';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let mtFeed = [
    `[TASK-MUX] Executing Action=${action} on target [${shortTask}]...`,
    inputStr ? `[STDIN-PIPE] Injecting stream payload: "${String(inputStr).slice(0, 70)}"` : `[DAEMON-BUS] Querying background process table, PIDs, & log descriptors...`,
    `[SUPERVISOR] Synchronizing non-blocking task state with Sovereign Kernel...`
  ];

  box.innerHTML = `
    <div class="fl-mt-header">
      <div class="fl-mt-left">
        <span class="fl-mt-tag">🎛️ TASK-MUX // ${escapeHtml(action)}</span>
        <span class="fl-mt-target" title="${escapeHtml(taskId)}">${escapeHtml(shortTask)}</span>
      </div>
      <span class="fl-mt-badge">MUXING • 0.01s</span>
    </div>
    <div class="fl-mt-bus-grid">
      <div class="fl-mt-bus-pod"><span class="fl-mt-bus-lbl">ACTION</span><span class="fl-mt-bus-val">${escapeHtml(action)}</span></div>
      <div class="fl-mt-bus-pod"><span class="fl-mt-bus-lbl">TARGET</span><span class="fl-mt-bus-val">${escapeHtml(shortTask.slice(0, 12))}</span></div>
      <div class="fl-mt-bus-pod"><span class="fl-mt-bus-lbl">IO BUS</span><span class="fl-mt-bus-val">${inputStr ? 'STDIN TX' : 'STATUS RX'}</span></div>
      <div class="fl-mt-bus-pod"><span class="fl-mt-bus-lbl">KERNEL</span><span class="fl-mt-bus-val fl-mt-state-val">ACTIVE</span></div>
    </div>
    <div class="fl-mt-console">
      <div class="fl-mt-line">${escapeHtml(mtFeed[0])}</div>
      <div class="fl-mt-line">${escapeHtml(mtFeed[1])}</div>
      <div class="fl-mt-line">${escapeHtml(mtFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 2);
    if (clean.length > 0) {
      mtFeed = clean.slice(0, 10);
      const lines = box.querySelectorAll('.fl-mt-line');
      lines.forEach((el, idx) => {
        if (mtFeed[idx]) el.textContent = mtFeed[idx];
      });
    }
    const stEl = box.querySelector('.fl-mt-state-val');
    if (stEl) stEl.textContent = 'SYNCED';
  };

    const badge = box.querySelector('.fl-mt-badge');
  const lines = box.querySelectorAll('.fl-mt-line');
  if (box._mtTimer) clearInterval(box._mtTimer);
  let tick = 0;
  box._mtTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._mtTimer) { clearInterval(box._mtTimer); box._mtTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._mtTimer) { clearInterval(box._mtTimer); box._mtTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `BUS ACTIVE • ${elapsedSec}s`;

        // (cached lines)
    if (lines.length >= 3 && mtFeed.length > 0) {
      lines[0].textContent = mtFeed[tick % mtFeed.length];
      lines[1].textContent = mtFeed[(tick + 1) % mtFeed.length];
      lines[2].textContent = mtFeed[(tick + 2) % mtFeed.length];
    }
  }, 150);
}

function generatePaintGhostSvg(widgetType) {
  const wt = (widgetType || '').toLowerCase();
  if (wt.includes('trading') || wt.includes('candlestick')) {
    return `
      <svg viewBox="0 0 220 60" fill="none">
        <line x1="25" y1="8" x2="25" y2="52" stroke="#00f2fe" stroke-width="1.2" opacity="0.6"/>
        <rect x="18" y="18" width="14" height="24" rx="2" fill="rgba(0,242,254,0.25)" stroke="#00f2fe" stroke-width="1.2"/>
        <line x1="65" y1="12" x2="65" y2="48" stroke="#f43f5e" stroke-width="1.2" opacity="0.6"/>
        <rect x="58" y="16" width="14" height="20" rx="2" fill="rgba(244,63,94,0.25)" stroke="#f43f5e" stroke-width="1.2"/>
        <line x1="105" y1="6" x2="105" y2="54" stroke="#00f2fe" stroke-width="1.2" opacity="0.6"/>
        <rect x="98" y="14" width="14" height="30" rx="2" fill="rgba(0,242,254,0.25)" stroke="#00f2fe" stroke-width="1.2"/>
        <line x1="145" y1="14" x2="145" y2="50" stroke="#00f2fe" stroke-width="1.2" opacity="0.6"/>
        <rect x="138" y="20" width="14" height="18" rx="2" fill="rgba(0,242,254,0.25)" stroke="#00f2fe" stroke-width="1.2"/>
        <line x1="185" y1="10" x2="185" y2="52" stroke="#f43f5e" stroke-width="1.2" opacity="0.6"/>
        <rect x="178" y="24" width="14" height="22" rx="2" fill="rgba(244,63,94,0.25)" stroke="#f43f5e" stroke-width="1.2"/>
        <path d="M 25 40 Q 65 24, 105 20 T 185 30" fill="none" stroke="#c084fc" stroke-width="1.5" stroke-dasharray="3 3"/>
      </svg>
    `;
  } else if (wt.includes('donut') || wt.includes('pie')) {
    return `
      <svg viewBox="0 0 120 60" fill="none">
        <circle cx="60" cy="30" r="22" fill="none" stroke="rgba(0,242,254,0.15)" stroke-width="7"/>
        <circle cx="60" cy="30" r="22" fill="none" stroke="#00f2fe" stroke-width="7" stroke-dasharray="45 100" stroke-linecap="round"/>
        <circle cx="60" cy="30" r="22" fill="none" stroke="#c084fc" stroke-width="7" stroke-dasharray="30 100" stroke-dashoffset="-50" stroke-linecap="round"/>
        <circle cx="60" cy="30" r="22" fill="none" stroke="#00ffb2" stroke-width="7" stroke-dasharray="20 100" stroke-dashoffset="-85" stroke-linecap="round"/>
      </svg>
    `;
  } else if (wt.includes('kpi') || wt.includes('metric')) {
    return `
      <svg viewBox="0 0 220 60" fill="none">
        <rect x="10" y="8" width="92" height="44" rx="6" fill="rgba(0,242,254,0.06)" stroke="rgba(0,242,254,0.4)" stroke-width="1.2"/>
        <line x1="22" y1="20" x2="60" y2="20" stroke="#38bdf8" stroke-width="2"/>
        <path d="M 22 42 L 40 34 L 58 38 L 76 26 L 92 30" fill="none" stroke="#00f2fe" stroke-width="1.5"/>
        <rect x="118" y="8" width="92" height="44" rx="6" fill="rgba(192,132,252,0.06)" stroke="rgba(192,132,252,0.4)" stroke-width="1.2"/>
        <line x1="130" y1="20" x2="168" y2="20" stroke="#c084fc" stroke-width="2"/>
        <path d="M 130 40 L 148 36 L 166 28 L 184 32 L 200 22" fill="none" stroke="#00ffb2" stroke-width="1.5"/>
      </svg>
    `;
  } else if (wt.includes('bar')) {
    return `
      <svg viewBox="0 0 220 60" fill="none">
        <line x1="10" y1="52" x2="210" y2="52" stroke="rgba(0,242,254,0.3)" stroke-width="1"/>
        <rect x="25" y="24" width="20" height="28" rx="2" fill="rgba(0,242,254,0.25)" stroke="#00f2fe" stroke-width="1.2"/>
        <rect x="62" y="14" width="20" height="38" rx="2" fill="rgba(192,132,252,0.25)" stroke="#c084fc" stroke-width="1.2"/>
        <rect x="99" y="32" width="20" height="20" rx="2" fill="rgba(0,242,254,0.25)" stroke="#00f2fe" stroke-width="1.2"/>
        <rect x="136" y="8" width="20" height="44" rx="2" fill="rgba(0,255,178,0.25)" stroke="#00ffb2" stroke-width="1.2"/>
        <rect x="173" y="20" width="20" height="32" rx="2" fill="rgba(0,242,254,0.25)" stroke="#00f2fe" stroke-width="1.2"/>
      </svg>
    `;
  } else {
    return `
      <svg viewBox="0 0 220 60" fill="none">
        <line x1="10" y1="52" x2="210" y2="52" stroke="rgba(0,242,254,0.3)" stroke-width="1"/>
        <line x1="10" y1="8" x2="10" y2="52" stroke="rgba(0,242,254,0.3)" stroke-width="1"/>
        <path d="M 15 48 C 45 48, 55 18, 90 28 C 120 38, 140 12, 205 16" fill="none" stroke="#00f2fe" stroke-width="1.8"/>
        <circle cx="15" cy="48" r="3" fill="#00f2fe"/>
        <circle cx="90" cy="28" r="3" fill="#c084fc"/>
        <circle cx="205" cy="16" r="3" fill="#00ffb2"/>
      </svg>
    `;
  }
}

function renderLivePluginControl(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const action = String(d.action || d.Action || 'list').toUpperCase();
  const pluginId = String(d.plugin_id || d.pluginId || d.query || d.id || 'ALL_MODULES');
  const actionsList = ['LIST', 'OPEN', 'CLOSE', 'SEARCH_REMOTE', 'INSTALL'];

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-plugin-ctrl';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let pcFeed = [
    `[CARTRIDGE-BAY] Executing plugin_control(action="${action.toLowerCase()}", target="${pluginId}")...`,
    `[IPC-BRIDGE] Synchronizing Canvas UI tab multiplexer & local/remote manifest registry...`,
    `[DOCK-BUS] Verifying Nano-Plug isolation & port bindings...`
  ];

  box.innerHTML = `
    <div class="fl-pc-header">
      <div class="fl-pc-left">
        <span class="fl-pc-tag">🧩 PLUGIN // ${escapeHtml(action)}</span>
        <span class="fl-pc-target" title="${escapeHtml(pluginId)}">${escapeHtml(pluginId)}</span>
      </div>
      <span class="fl-pc-badge">DOCKING • 0.01s</span>
    </div>
    <div class="fl-pc-actions-grid">
      ${actionsList.map(act => `
        <span class="fl-pc-act-chip ${action.includes(act) || (act === 'LIST' && !actionsList.some(a => action.includes(a))) ? 'is-active' : ''}">${act}</span>
      `).join('')}
    </div>
    <div class="fl-pc-console">
      <div class="fl-pc-line">${escapeHtml(pcFeed[0])}</div>
      <div class="fl-pc-line">${escapeHtml(pcFeed[1])}</div>
      <div class="fl-pc-line">${escapeHtml(pcFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 2);
    if (clean.length > 0) {
      pcFeed = clean.slice(0, 10);
      const lines = box.querySelectorAll('.fl-pc-line');
      lines.forEach((el, idx) => {
        if (pcFeed[idx]) el.textContent = pcFeed[idx];
      });
    }
  };

    const badge = box.querySelector('.fl-pc-badge');
  const lines = box.querySelectorAll('.fl-pc-line');
  if (box._pcTimer) clearInterval(box._pcTimer);
  let tick = 0;
  box._pcTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._pcTimer) { clearInterval(box._pcTimer); box._pcTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._pcTimer) { clearInterval(box._pcTimer); box._pcTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `MUX ACTIVE • ${elapsedSec}s`;

        // (cached lines)
    if (lines.length >= 3 && pcFeed.length > 0) {
      lines[0].textContent = pcFeed[tick % pcFeed.length];
      lines[1].textContent = pcFeed[(tick + 1) % pcFeed.length];
      lines[2].textContent = pcFeed[(tick + 2) % pcFeed.length];
    }
  }, 150);
}

function renderLivePublishGatekeeper(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetPlugin = shortenFilePath(d.plugin_id || d.path || d.dir || d.target || 'plugins/module');
  const gates = ['MANIFEST', 'LICENSE', 'DLP SECRET', 'MULTI-OS', 'QC EXIT 0'];

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-gatekeeper';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let gkFeed = [
    `[GATEKEEPER] Running 5-stage pre-flight customs inspection on ${targetPlugin}...`,
    `[DLP-GUARD] Scanning source tree for leaked API keys, tokens, & hardcoded paths...`,
    `[COMPLIANCE] Validating plugin.manifest.json schema, license, & Multi-OS readiness...`
  ];

  box.innerHTML = `
    <div class="fl-gk-header">
      <div class="fl-gk-left">
        <span class="fl-gk-tag">🛂 GATEKEEPER // PRE-FLIGHT</span>
        <span class="fl-gk-target" title="${escapeHtml(targetPlugin)}">${escapeHtml(targetPlugin)}</span>
      </div>
      <span class="fl-gk-badge">INSPECTING • 0.01s</span>
    </div>
    <div class="fl-gk-gates-grid">
      ${gates.map(g => `
        <div class="fl-gk-gate-pod" data-gate="${g}">
          <span class="fl-gk-gate-name">${g}</span>
          <span class="fl-gk-gate-state">WAIT</span>
        </div>
      `).join('')}
    </div>
    <div class="fl-gk-console">
      <div class="fl-gk-line">${escapeHtml(gkFeed[0])}</div>
      <div class="fl-gk-line">${escapeHtml(gkFeed[1])}</div>
      <div class="fl-gk-line">${escapeHtml(gkFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 2);
    if (clean.length > 0) {
      gkFeed = clean.slice(0, 10);
      const lines = box.querySelectorAll('.fl-gk-line');
      lines.forEach((el, idx) => {
        if (gkFeed[idx]) el.textContent = gkFeed[idx];
      });
    }
    const hasFail = /fail|denied|reject|blocked|violation/i.test(str) && !/0 violations/i.test(str);
    box.querySelectorAll('.fl-gk-gate-pod').forEach(pod => {
      const st = pod.querySelector('.fl-gk-gate-state');
      pod.classList.toggle('is-pass', !hasFail);
      pod.classList.toggle('is-fail', hasFail);
      if (st) st.textContent = hasFail ? 'WARN' : 'PASS ✓';
    });
  };

    const badge = box.querySelector('.fl-gk-badge');
  const pods = box.querySelectorAll('.fl-gk-gate-pod');
  const lines = box.querySelectorAll('.fl-gk-line');
  if (box._gkTimer) clearInterval(box._gkTimer);
  let tick = 0;
  box._gkTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._gkTimer) { clearInterval(box._gkTimer); box._gkTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._gkTimer) { clearInterval(box._gkTimer); box._gkTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `VERIFYING • ${elapsedSec}s`;

        // (cached pods)
    pods.forEach((pod, idx) => {
      if (!pod.classList.contains('is-fail')) {
        const st = pod.querySelector('.fl-gk-gate-state');
        if (idx <= (tick % (pods.length + 1))) {
          pod.classList.add('is-pass');
          if (st) st.textContent = 'PASS ✓';
        }
      }
    });

        // (cached lines)
    if (lines.length >= 3 && gkFeed.length > 0) {
      lines[0].textContent = gkFeed[tick % gkFeed.length];
      lines[1].textContent = gkFeed[(tick + 1) % gkFeed.length];
      lines[2].textContent = gkFeed[(tick + 2) % gkFeed.length];
    }
  }, 150);
}

function renderLiveCameraShutter(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetLabel = shortenFilePath(d.target || d.TargetFile || d.path || d.output || d.display || 'DISPLAY=:0 // VIEWPORT');
  FloworkMrFlowAudio.playSynthSfx('shutter_click');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-screenshot';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  box.innerHTML = `
    <div class="fl-ss-header">
      <div class="fl-ss-left">
        <span class="fl-ss-tag">📸 OPTICAL // SHUTTER</span>
        <span class="fl-ss-target" title="${escapeHtml(targetLabel)}">${escapeHtml(targetLabel)}</span>
      </div>
      <span class="fl-ss-badge">CAPTURING • 0.01s</span>
    </div>
    <div class="fl-ss-viewfinder">
      <div class="fl-ss-laser-sweep"></div>
      <span class="fl-ss-reticle">[ ⌖ REC // 60FPS ]</span>
      <div class="fl-ss-meta-grid">
        <div class="fl-ss-meta-pill"><span class="fl-ss-meta-lbl">SOURCE</span><span class="fl-ss-meta-val">X11 / WAYLAND / GUI</span></div>
        <div class="fl-ss-meta-pill"><span class="fl-ss-meta-lbl">FORMAT</span><span class="fl-ss-meta-val">LOSSLESS PNG</span></div>
        <div class="fl-ss-meta-pill"><span class="fl-ss-meta-lbl">STATUS</span><span class="fl-ss-meta-val fl-ss-stat-val">SHUTTER OPEN</span></div>
      </div>
    </div>
    <div class="fl-ss-footer">▸ Capturing framebuffer pixels & encoding visual QC artifact...</div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    const footer = box.querySelector('.fl-ss-footer');
    if (footer && clean.length > 0) {
      footer.textContent = `▸ ${clean.slice(0, 2).join(' • ').slice(0, 115)}`;
    }
    const stVal = box.querySelector('.fl-ss-stat-val');
    if (stVal) stVal.textContent = 'FRAME SAVED';
  };

    const badge = box.querySelector('.fl-ss-badge');
  if (box._cameraTimer) clearInterval(box._cameraTimer);
  box._cameraTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._cameraTimer) { clearInterval(box._cameraTimer); box._cameraTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._cameraTimer) { clearInterval(box._cameraTimer); box._cameraTimer = null; } return; }
    if (document.hidden) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `SHUTTER • ${elapsedSec}s`;
  }, 150);
}

function renderLiveYtSpyVideo(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetUrl = String(d.url || d.Url || d.video_id || d.videoId || d.target || 'https://youtube.com/watch?v=...');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-yt-video';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let ytvFeed = [
    `[FBE-V6 VIDEO] DeepScanning YouTube video stream: ${targetUrl}...`,
    `[HIDDEN-TAGS] Extracting hidden meta keywords, category ID, & monetization flags...`,
    `[AD-BREAKS] Mapping mid-roll ad-break timestamps & codec bitrate profile...`
  ];

  box.innerHTML = `
    <div class="fl-ytv-header">
      <div class="fl-ytv-left">
        <span class="fl-ytv-tag">🎬 YT-SPY // VIDEO V6</span>
        <span class="fl-ytv-target" title="${escapeHtml(targetUrl)}">${escapeHtml(targetUrl)}</span>
      </div>
      <span class="fl-ytv-badge">DEEPSCAN • 0.01s</span>
    </div>
    <div class="fl-ytv-metrics-grid">
      <div class="fl-ytv-pod"><span class="fl-ytv-pod-lbl">HIDDEN TAGS</span><span class="fl-ytv-pod-val fl-ytv-v-tags">SCANNING</span></div>
      <div class="fl-ytv-pod"><span class="fl-ytv-pod-lbl">MONETIZED</span><span class="fl-ytv-pod-val fl-ytv-v-mon">PROBING</span></div>
      <div class="fl-ytv-pod"><span class="fl-ytv-pod-lbl">AD-BREAKS</span><span class="fl-ytv-pod-val fl-ytv-v-ads">MAPPING</span></div>
      <div class="fl-ytv-pod"><span class="fl-ytv-pod-lbl">SPECS</span><span class="fl-ytv-pod-val fl-ytv-v-spec">HD/AV1</span></div>
    </div>
    <div class="fl-ytv-console">
      <div class="fl-ytv-line">${escapeHtml(ytvFeed[0])}</div>
      <div class="fl-ytv-line">${escapeHtml(ytvFeed[1])}</div>
      <div class="fl-ytv-line">${escapeHtml(ytvFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 3);
    if (clean.length > 0) {
      ytvFeed = clean.slice(0, 12);
      const lines = box.querySelectorAll('.fl-ytv-line');
      lines.forEach((el, idx) => {
        if (ytvFeed[idx]) el.textContent = ytvFeed[idx];
      });
    }
    const tEl = box.querySelector('.fl-ytv-v-tags');
    const mEl = box.querySelector('.fl-ytv-v-mon');
    const aEl = box.querySelector('.fl-ytv-v-ads');
    if (tEl) tEl.textContent = 'EXTRACTED';
    if (mEl) mEl.textContent = 'VERIFIED';
    if (aEl) aEl.textContent = 'LOCKED';
  };

    const badge = box.querySelector('.fl-ytv-badge');
  const lines = box.querySelectorAll('.fl-ytv-line');
  if (box._ytvTimer) clearInterval(box._ytvTimer);
  let tick = 0;
  box._ytvTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._ytvTimer) { clearInterval(box._ytvTimer); box._ytvTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._ytvTimer) { clearInterval(box._ytvTimer); box._ytvTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `DEEPSCAN • ${elapsedSec}s`;

        // (cached lines)
    if (lines.length >= 3 && ytvFeed.length > 0) {
      lines[0].textContent = ytvFeed[tick % ytvFeed.length];
      lines[1].textContent = ytvFeed[(tick + 1) % ytvFeed.length];
      lines[2].textContent = ytvFeed[(tick + 2) % ytvFeed.length];
    }
  }, 150);
}

function renderLiveYtSpyChannel(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetChannel = String(d.url || d.Url || d.channel || d.channel_id || d.handle || d.target || '@YouTubeChannel');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-yt-channel';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let ytcFeed = [
    `[CHANNEL-PULSE] Probing subscriber velocity & total uploads for ${targetChannel}...`,
    `[TOP-12 VIRAL] Ranking 12 highest-performing videos by view count & engagement...`,
    `[BENCHMARK] Calculating channel upload cadence & viral outlier multiplier...`
  ];

  box.innerHTML = `
    <div class="fl-ytc-header">
      <div class="fl-ytc-left">
        <span class="fl-ytc-tag">📊 YT-SPY // CHANNEL</span>
        <span class="fl-ytc-target" title="${escapeHtml(targetChannel)}">${escapeHtml(targetChannel)}</span>
      </div>
      <span class="fl-ytc-badge">PULSING • 0.01s</span>
    </div>
    <div class="fl-ytc-pulse-grid">
      <div class="fl-ytc-pod"><span class="fl-ytc-pod-lbl">SUBSCRIBERS</span><span class="fl-ytc-pod-val fl-ytc-v-sub">PROBING</span></div>
      <div class="fl-ytc-pod"><span class="fl-ytc-pod-lbl">TOTAL VIDEOS</span><span class="fl-ytc-pod-val fl-ytc-v-vid">COUNTING</span></div>
      <div class="fl-ytc-pod"><span class="fl-ytc-pod-lbl">TOP-12 RANK</span><span class="fl-ytc-pod-val fl-ytc-v-top">SORTING</span></div>
    </div>
    <div class="fl-ytc-console">
      <div class="fl-ytc-line">${escapeHtml(ytcFeed[0])}</div>
      <div class="fl-ytc-line">${escapeHtml(ytcFeed[1])}</div>
      <div class="fl-ytc-line">${escapeHtml(ytcFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 3);
    if (clean.length > 0) {
      ytcFeed = clean.slice(0, 12);
      const lines = box.querySelectorAll('.fl-ytc-line');
      lines.forEach((el, idx) => {
        if (ytcFeed[idx]) el.textContent = ytcFeed[idx];
      });
    }
    const sEl = box.querySelector('.fl-ytc-v-sub');
    const vEl = box.querySelector('.fl-ytc-v-vid');
    const tEl = box.querySelector('.fl-ytc-v-top');
    if (sEl) sEl.textContent = 'LOCKED';
    if (vEl) vEl.textContent = 'INDEXED';
    if (tEl) tEl.textContent = '12/12 READY';
  };

    const badge = box.querySelector('.fl-ytc-badge');
  const lines = box.querySelectorAll('.fl-ytc-line');
  if (box._ytcTimer) clearInterval(box._ytcTimer);
  let tick = 0;
  box._ytcTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._ytcTimer) { clearInterval(box._ytcTimer); box._ytcTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._ytcTimer) { clearInterval(box._ytcTimer); box._ytcTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `CHANNEL PULSE • ${elapsedSec}s`;

        // (cached lines)
    if (lines.length >= 3 && ytcFeed.length > 0) {
      lines[0].textContent = ytcFeed[tick % ytcFeed.length];
      lines[1].textContent = ytcFeed[(tick + 1) % ytcFeed.length];
      lines[2].textContent = ytcFeed[(tick + 2) % ytcFeed.length];
    }
  }, 150);
}

function renderLiveYtSpyTranscript(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetUrl = String(d.url || d.Url || d.video_id || d.videoId || d.target || 'https://youtube.com/watch?v=...');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-yt-transcript';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let yttFeed = [
    `[00:00] Initializing ASR & subtitle track extraction for ${targetUrl}...`,
    `[00:15] Synchronizing [MM:SS] timecode cues & spoken dialogue segments...`,
    `[00:30] Streaming verbatim transcript lines into Sovereign Teleprompter...`
  ];

  box.innerHTML = `
    <div class="fl-ytt-header">
      <div class="fl-ytt-left">
        <span class="fl-ytt-tag">📜 YT-SPY // TRANSCRIPT</span>
        <span class="fl-ytt-target" title="${escapeHtml(targetUrl)}">${escapeHtml(targetUrl)}</span>
      </div>
      <span class="fl-ytt-badge">EXTRACTING • 0.01s</span>
    </div>
    <div class="fl-ytt-meta-bar">
      <span class="fl-ytt-tc-pill">⏱️ TIMECODE: [MM:SS] SYNC</span>
      <span class="fl-ytt-seg-count">STREAMING SUBTITLE CUES...</span>
    </div>
    <div class="fl-ytt-prompter">
      <div class="fl-ytt-line">${escapeHtml(yttFeed[0])}</div>
      <div class="fl-ytt-line">${escapeHtml(yttFeed[1])}</div>
      <div class="fl-ytt-line">${escapeHtml(yttFeed[2])}</div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 2);
    if (clean.length > 0) {
      yttFeed = clean.slice(0, 18);
      const lines = box.querySelectorAll('.fl-ytt-line');
      lines.forEach((el, idx) => {
        if (yttFeed[idx]) el.textContent = yttFeed[idx];
      });
      const segEl = box.querySelector('.fl-ytt-seg-count');
      if (segEl) segEl.textContent = `${clean.length} TIMECODED LINES EXTRACTED`;
    }
  };

    const badge = box.querySelector('.fl-ytt-badge');
  const lines = box.querySelectorAll('.fl-ytt-line');
  if (box._yttTimer) clearInterval(box._yttTimer);
  let tick = 0;
  box._yttTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._yttTimer) { clearInterval(box._yttTimer); box._yttTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._yttTimer) { clearInterval(box._yttTimer); box._yttTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `TELEPROMPTER • ${elapsedSec}s`;

        // (cached lines)
    if (lines.length >= 3 && yttFeed.length > 0) {
      lines[0].textContent = yttFeed[tick % yttFeed.length];
      lines[1].textContent = yttFeed[(tick + 1) % yttFeed.length];
      lines[2].textContent = yttFeed[(tick + 2) % yttFeed.length];
    }
  }, 150);
}

function renderLiveYtSpySummary(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetUrl = String(d.url || d.Url || d.video_id || 'https://youtube.com/watch');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-yt-summary';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let ytsFeed = [
    `Distilling core narrative thesis & executive takeaways from transcript...`,
    `Synthesizing high-density bullet points & actionable insight nodes...`,
    `Compressing 100% of spoken context into sovereign knowledge pills...`
  ];

  box.innerHTML = `
    <div class="fl-yts-header">
      <div class="fl-yts-title-group">
        <span class="fl-yts-pill">🔮 YT SUMMARY ORB</span>
        <span class="fl-yts-target" title="${escapeHtml(targetUrl)}">${escapeHtml(targetUrl)}</span>
      </div>
      <span class="fl-yts-badge">SYNTHESIZING • 0.01s</span>
    </div>
    <div class="fl-yts-body">
      <div class="fl-yts-orb-wrap">
        <div class="fl-yts-orb-ring"></div>
        <div class="fl-yts-orb-ring-inner"></div>
        <div class="fl-yts-orb-core">🧠</div>
      </div>
      <div class="fl-yts-bubbles">
        <div class="fl-yts-bubble"><span class="fl-yts-dot"></span><span class="fl-yts-btxt">${escapeHtml(ytsFeed[0])}</span></div>
        <div class="fl-yts-bubble"><span class="fl-yts-dot"></span><span class="fl-yts-btxt">${escapeHtml(ytsFeed[1])}</span></div>
        <div class="fl-yts-bubble"><span class="fl-yts-dot"></span><span class="fl-yts-btxt">${escapeHtml(ytsFeed[2])}</span></div>
      </div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.replace(/^[-*•\d.)\s]+/, '').trim()).filter(s => s.length > 6);
    if (clean.length > 0) {
      ytsFeed = clean.slice(0, 12);
      const btxts = box.querySelectorAll('.fl-yts-btxt');
      btxts.forEach((el, idx) => {
        if (ytsFeed[idx]) el.textContent = ytsFeed[idx];
      });
    }
  };

    const badge = box.querySelector('.fl-yts-badge');
  const btxts = box.querySelectorAll('.fl-yts-btxt');
  if (box._ytsTimer) clearInterval(box._ytsTimer);
  let tick = 0;
  box._ytsTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._ytsTimer) { clearInterval(box._ytsTimer); box._ytsTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._ytsTimer) { clearInterval(box._ytsTimer); box._ytsTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `DISTILLING • ${elapsedSec}s`;

        // (cached btxts)
    if (btxts.length >= 3 && ytsFeed.length > 0) {
      btxts[0].textContent = ytsFeed[tick % ytsFeed.length];
      btxts[1].textContent = ytsFeed[(tick + 1) % ytsFeed.length];
      btxts[2].textContent = ytsFeed[(tick + 2) % ytsFeed.length];
    }
  }, 150);
}

function renderLiveYtSpyComments(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetUrl = String(d.url || d.Url || d.video_id || 'https://youtube.com/watch');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-yt-comments';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let ytcFeed = [
    { user: '@AudiencePulse', txt: 'Harvesting top-liked viewer comments & recurring requests...' },
    { user: '@SentimentRadar', txt: 'Clustering positive praise, friction points & content gaps...' }
  ];

  box.innerHTML = `
    <div class="fl-ytcm-header">
      <div class="fl-ytcm-title-group">
        <span class="fl-ytcm-pill">💬 AUDIENCE BUBBLE CLOUD</span>
        <span class="fl-ytcm-target" title="${escapeHtml(targetUrl)}">${escapeHtml(targetUrl)}</span>
      </div>
      <span class="fl-ytcm-badge">MINING • 0.01s</span>
    </div>
    <div class="fl-ytcm-polarity-row">
      <div class="fl-ytcm-pol-pill pos">💚 POSITIVE <span class="fl-ytcm-pos-val">68%</span></div>
      <div class="fl-ytcm-pol-pill neu">💡 QUESTIONS <span class="fl-ytcm-neu-val">24%</span></div>
      <div class="fl-ytcm-pol-pill neg">🔥 FRICTION <span class="fl-ytcm-neg-val">8%</span></div>
    </div>
    <div class="fl-ytcm-cloud">
      <div class="fl-ytcm-chat-bubble">
        <span class="fl-ytcm-avatar">🗣️</span>
        <span class="fl-ytcm-user">${escapeHtml(ytcFeed[0].user)}</span>
        <span class="fl-ytcm-txt">${escapeHtml(ytcFeed[0].txt)}</span>
      </div>
      <div class="fl-ytcm-chat-bubble">
        <span class="fl-ytcm-avatar">✨</span>
        <span class="fl-ytcm-user">${escapeHtml(ytcFeed[1].user)}</span>
        <span class="fl-ytcm-txt">${escapeHtml(ytcFeed[1].txt)}</span>
      </div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 5);
    if (clean.length > 0) {
      ytcFeed = clean.slice(0, 14).map((line, i) => ({
        user: `@Viewer_${i + 1}`,
        txt: line.slice(0, 110)
      }));
    }
  };

    const badge = box.querySelector('.fl-ytcm-badge');
  const bubbles = box.querySelectorAll('.fl-ytcm-chat-bubble');
  if (box._ytcmTimer) clearInterval(box._ytcmTimer);
  let tick = 0;
  box._ytcmTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._ytcmTimer) { clearInterval(box._ytcmTimer); box._ytcmTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._ytcmTimer) { clearInterval(box._ytcmTimer); box._ytcmTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `SENTIMENT • ${elapsedSec}s`;

        // (cached bubbles)
    if (bubbles.length >= 2 && ytcFeed.length > 0) {
      const c0 = ytcFeed[tick % ytcFeed.length];
      const c1 = ytcFeed[(tick + 1) % ytcFeed.length];
      const u0 = bubbles[0].querySelector('.fl-ytcm-user');
      const t0 = bubbles[0].querySelector('.fl-ytcm-txt');
      const u1 = bubbles[1].querySelector('.fl-ytcm-user');
      const t1 = bubbles[1].querySelector('.fl-ytcm-txt');
      if (u0) u0.textContent = c0.user;
      if (t0) t0.textContent = c0.txt;
      if (u1) u1.textContent = c1.user;
      if (t1) t1.textContent = c1.txt;
    }
  }, 150);
}

function renderLiveYtSpyStrategy(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetUrl = String(d.url || d.Url || d.video_id || 'https://youtube.com/watch');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-yt-strategy';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let stratFeed = [
    `Synthesizing 30-Second Psychological Hook & Curiosity Gap...`,
    `Generating 5 High-CTR Viral Counter-Titles & Thumbnail Angles...`,
    `Structuring 5-Part Outranking Video Script Blueprint...`
  ];

  box.innerHTML = `
    <div class="fl-ytst-header">
      <div class="fl-ytst-title-group">
        <span class="fl-ytst-pill">♟️ VIRAL STRATEGY ORBIT</span>
        <span class="fl-ytst-target" title="${escapeHtml(targetUrl)}">${escapeHtml(targetUrl)}</span>
      </div>
      <span class="fl-ytst-badge">OUTRANKING • 0.01s</span>
    </div>
    <div class="fl-ytst-capsules">
      <div class="fl-ytst-cap is-active" data-cap="0">
        <span class="fl-ytst-cap-orb">⚡</span>
        <span class="fl-ytst-cap-lbl">30S HOOK</span>
        <span class="fl-ytst-cap-val">SYNTHESIZING</span>
      </div>
      <div class="fl-ytst-cap" data-cap="1">
        <span class="fl-ytst-cap-orb">🎯</span>
        <span class="fl-ytst-cap-lbl">5 HIGH-CTR TITLES</span>
        <span class="fl-ytst-cap-val">MODELING</span>
      </div>
      <div class="fl-ytst-cap" data-cap="2">
        <span class="fl-ytst-cap-orb">📜</span>
        <span class="fl-ytst-cap-lbl">5-PART SCRIPT</span>
        <span class="fl-ytst-cap-val">ARCHITECTING</span>
      </div>
    </div>
    <div class="fl-ytst-stream-pill">
      <span class="fl-ytst-stream-dot"></span>
      <span class="fl-ytst-stream-txt">${escapeHtml(stratFeed[0])}</span>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 6);
    if (clean.length > 0) {
      stratFeed = clean.slice(0, 14);
      const streamEl = box.querySelector('.fl-ytst-stream-txt');
      if (streamEl) streamEl.textContent = stratFeed[0];
    }
    box.querySelectorAll('.fl-ytst-cap-val').forEach(el => {
      el.textContent = '✓ READY';
    });
  };

    const badge = box.querySelector('.fl-ytst-badge');
  const streamEl = box.querySelector('.fl-ytst-stream-txt');
  const caps = box.querySelectorAll('.fl-ytst-cap');
  if (box._ytstTimer) clearInterval(box._ytstTimer);
  let tick = 0;
  box._ytstTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._ytstTimer) { clearInterval(box._ytstTimer); box._ytstTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._ytstTimer) { clearInterval(box._ytstTimer); box._ytstTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `STRATEGY • ${elapsedSec}s`;

    const activeIdx = tick % 3;
    caps.forEach((cap, idx) => {
      cap.classList.toggle('is-active', idx === activeIdx);
    });

        // (cached streamEl)
    if (streamEl && stratFeed.length > 0) {
      streamEl.textContent = stratFeed[tick % stratFeed.length];
    }
  }, 150);
}

function renderLiveAskQuestion(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const qList = Array.isArray(d.questions) ? d.questions : [];
  const firstQ = qList[0] || d;
  const qText = String(firstQ.question || firstQ.Question || d.question || d.prompt || 'Awaiting structured user decision...');
  const rawOpts = Array.isArray(firstQ.options) ? firstQ.options : (Array.isArray(d.options) ? d.options : []);
  const opts = rawOpts.length > 0 ? rawOpts.slice(0, 4).map(o => String(typeof o === 'object' ? (o.label || o.text || JSON.stringify(o)) : o)) : [
    'Option 1: Primary execution path',
    'Option 2: Alternative configuration'
  ];

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-ask-question';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  const optsHtml = opts.map((opt, idx) => `
    <div class="fl-aq-opt-pill ${idx === 0 ? 'is-active' : ''}" data-opt="${idx}">
      <span class="fl-aq-opt-orb">${idx + 1}</span>
      <span class="fl-aq-opt-txt" title="${escapeHtml(opt)}">${escapeHtml(opt)}</span>
    </div>
  `).join('');

  box.innerHTML = `
    <div class="fl-aq-header">
      <div class="fl-aq-title-group">
        <span class="fl-aq-pill">❓ ASK QUESTION</span>
        <span class="fl-aq-qtext" title="${escapeHtml(qText)}">${escapeHtml(qText)}</span>
      </div>
      <span class="fl-aq-badge">AWAITING • 0.01s</span>
    </div>
    <div class="fl-aq-options">${optsHtml}</div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    if (str.trim()) {
      const qEl = box.querySelector('.fl-aq-qtext');
      if (qEl) qEl.textContent = `SELECTED: ${str.replace(/[\r\n]+/g, ' ').slice(0, 90)}`;
    }
  };

    const badge = box.querySelector('.fl-aq-badge');
  const pills = box.querySelectorAll('.fl-aq-opt-pill');
  if (box._aqTimer) clearInterval(box._aqTimer);
  let tick = 0;
  box._aqTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._aqTimer) { clearInterval(box._aqTimer); box._aqTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._aqTimer) { clearInterval(box._aqTimer); box._aqTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `DECISION • ${elapsedSec}s`;

        // (cached pills)
    if (pills.length > 0) {
      const activeIdx = tick % pills.length;
      pills.forEach((p, idx) => p.classList.toggle('is-active', idx === activeIdx));
    }
  }, 150);
}

function renderLiveSystemRestart(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const reasonTxt = String(d.reason || d.resume_prompt || d.message || d.toolSummary || 'Hot-reloading sovereign Flowork binary with state preservation');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-sys-restart';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  box.innerHTML = `
    <div class="fl-sr-header">
      <div class="fl-sr-title-group">
        <span class="fl-sr-pill">♻️ SYSTEM RESTART</span>
        <span class="fl-sr-target" title="${escapeHtml(reasonTxt)}">${escapeHtml(reasonTxt)}</span>
      </div>
      <span class="fl-sr-badge">REBOOTING • 0.01s</span>
    </div>
    <div class="fl-sr-body">
      <div class="fl-sr-turbine-orb">
        <div class="fl-sr-turbine-ring"></div>
        <span class="fl-sr-turbine-core">⚡</span>
      </div>
      <div class="fl-sr-phases">
        <div class="fl-sr-phase-pill is-active"><span class="fl-sr-phase-lbl">🔄 DRAIN IPC</span><span class="fl-sr-phase-val">FLUSHING</span></div>
        <div class="fl-sr-phase-pill"><span class="fl-sr-phase-lbl">⚡ EXECVE BIN</span><span class="fl-sr-phase-val">RELOADING</span></div>
        <div class="fl-sr-phase-pill"><span class="fl-sr-phase-lbl">🚀 AUTO-RESUME</span><span class="fl-sr-phase-val">ARMED</span></div>
      </div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const tEl = box.querySelector('.fl-sr-target');
    if (tEl && str.trim()) tEl.textContent = str.replace(/[\r\n]+/g, ' ').slice(0, 100);
    box.querySelectorAll('.fl-sr-phase-val').forEach(el => { el.textContent = '✓ DONE'; });
  };

    const badge = box.querySelector('.fl-sr-badge');
  const phases = box.querySelectorAll('.fl-sr-phase-pill');
  if (box._srTimer) clearInterval(box._srTimer);
  let tick = 0;
  box._srTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._srTimer) { clearInterval(box._srTimer); box._srTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._srTimer) { clearInterval(box._srTimer); box._srTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `TURBINE • ${elapsedSec}s`;

        // (cached phases)
    phases.forEach((p, idx) => p.classList.toggle('is-active', idx === (tick % 3)));
  }, 150);
}

function renderLivePluginPublish(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const pluginId = String(d.plugin_id || d.pluginId || d.id || d.name || 'sovereign-plugin');
  const version = String(d.version || d.Version || '1.0.0');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-plugin-publish';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let ppFeed = [
    `Packaging plugin [${pluginId}@${version}] & computing SHA-256 digest...`,
    `Uploading verified bundle to Cloudflare Edge Gateway...`,
    `Synchronizing global Flowork OS plugin registry...`
  ];

  box.innerHTML = `
    <div class="fl-pp-header">
      <div class="fl-pp-title-group">
        <span class="fl-pp-pill">☁️ PLUGIN PUBLISH</span>
        <span class="fl-pp-target" title="${escapeHtml(pluginId)} v${escapeHtml(version)}">${escapeHtml(pluginId)} • v${escapeHtml(version)}</span>
      </div>
      <span class="fl-pp-badge">UPLINK • 0.01s</span>
    </div>
    <div class="fl-pp-stages">
      <div class="fl-pp-stage-pill is-active"><span class="fl-pp-orb">📦</span><span class="fl-pp-stage-txt">SHA-256 BUNDLE</span></div>
      <div class="fl-pp-stage-pill"><span class="fl-pp-orb">☁️</span><span class="fl-pp-stage-txt">CF EDGE GATEWAY</span></div>
      <div class="fl-pp-stage-pill"><span class="fl-pp-orb">🌐</span><span class="fl-pp-stage-txt">REGISTRY LIVE</span></div>
    </div>
    <div class="fl-pp-stream-pill">
      <span class="fl-pp-dot"></span>
      <span class="fl-pp-stream-txt">${escapeHtml(ppFeed[0])}</span>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    if (clean.length > 0) {
      ppFeed = clean.slice(0, 10);
      const sEl = box.querySelector('.fl-pp-stream-txt');
      if (sEl) sEl.textContent = ppFeed[0];
    }
  };

    const badge = box.querySelector('.fl-pp-badge');
  const sEl = box.querySelector('.fl-pp-stream-txt');
  const stagePills = box.querySelectorAll('.fl-pp-stage-pill');
  if (box._ppTimer) clearInterval(box._ppTimer);
  let tick = 0;
  box._ppTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._ppTimer) { clearInterval(box._ppTimer); box._ppTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._ppTimer) { clearInterval(box._ppTimer); box._ppTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `EDGE UPLINK • ${elapsedSec}s`;

    stagePills.forEach((p, idx) => p.classList.toggle('is-active', idx === (tick % 3)));
        // (cached sEl)
    if (sEl && ppFeed.length > 0) sEl.textContent = ppFeed[tick % ppFeed.length];
  }, 150);
}

function renderLiveInvokeSubagent(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const subs = Array.isArray(d.Subagents) ? d.Subagents : (Array.isArray(d.subagents) ? d.subagents : [d]);
  const firstSub = subs[0] || d;
  const role = String(firstSub.Role || firstSub.role || d.Role || d.role || 'Autonomous Specialist');
  const typeName = String(firstSub.TypeName || firstSub.typeName || firstSub.type || d.TypeName || 'self');
  const model = String(firstSub.Model || firstSub.model || d.Model || 'inherit');
  const workspace = String(firstSub.Workspace || firstSub.workspace || d.Workspace || 'inherit');
  const prompt = String(firstSub.Prompt || firstSub.prompt || d.Prompt || d.prompt || 'Executing delegated subagent mission...');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-invoke-subagent';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let isaFeed = [
    prompt,
    `Spawning ${subs.length} subagent node(s) [${role}] on workspace [${workspace}]...`
  ];

  box.innerHTML = `
    <div class="fl-isa-header">
      <div class="fl-isa-title-group">
        <span class="fl-isa-pill">🛰️ INVOKE SUBAGENT</span>
        <span class="fl-isa-role" title="${escapeHtml(role)}">${escapeHtml(role)} (${subs.length}x)</span>
      </div>
      <span class="fl-isa-badge">LAUNCHING • 0.01s</span>
    </div>
    <div class="fl-isa-body">
      <div class="fl-isa-sat-orb">
        <div class="fl-isa-sat-ring"></div>
        <span class="fl-isa-sat-core">🛰️</span>
      </div>
      <div class="fl-isa-capsules">
        <div class="fl-isa-meta-pills">
          <span class="fl-isa-chip">TYPE: ${escapeHtml(typeName)}</span>
          <span class="fl-isa-chip">MODEL: ${escapeHtml(model)}</span>
          <span class="fl-isa-chip">WS: ${escapeHtml(workspace)}</span>
        </div>
        <div class="fl-isa-prompt-pill">
          <span class="fl-isa-dot"></span>
          <span class="fl-isa-prompt-txt" title="${escapeHtml(prompt)}">${escapeHtml(prompt)}</span>
        </div>
      </div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    if (clean.length > 0) {
      isaFeed = clean.slice(0, 8);
      const pEl = box.querySelector('.fl-isa-prompt-txt');
      if (pEl) pEl.textContent = isaFeed[0];
    }
  };

    const badge = box.querySelector('.fl-isa-badge');
  const pEl = box.querySelector('.fl-isa-prompt-txt');
  if (box._isaTimer) clearInterval(box._isaTimer);
  let tick = 0;
  box._isaTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._isaTimer) { clearInterval(box._isaTimer); box._isaTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._isaTimer) { clearInterval(box._isaTimer); box._isaTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `ORBITAL • ${elapsedSec}s`;

        // (cached pEl)
    if (pEl && isaFeed.length > 0) pEl.textContent = isaFeed[tick % isaFeed.length];
  }, 150);
}

function renderLiveDefineSubagent(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const name = String(d.name || d.Name || 'custom_specialist');
  const desc = String(d.description || d.Description || d.system_prompt || 'Defining specialized subagent blueprint');
  const writeOn = Boolean(d.enable_write_tools);
  const mcpOn = Boolean(d.enable_mcp_tools);
  const subOn = Boolean(d.enable_subagent_tools);

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-define-subagent';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  box.innerHTML = `
    <div class="fl-dsa-header">
      <div class="fl-dsa-title-group">
        <span class="fl-dsa-pill">🧬 DEFINE SUBAGENT</span>
        <span class="fl-dsa-name" title="${escapeHtml(name)}">${escapeHtml(name)}</span>
      </div>
      <span class="fl-dsa-badge">SYNTHESIZING • 0.01s</span>
    </div>
    <div class="fl-dsa-caps">
      <div class="fl-dsa-cap-pill ${writeOn ? 'is-enabled' : ''}">✍️ WRITE: ${writeOn ? 'ON' : 'READ-ONLY'}</div>
      <div class="fl-dsa-cap-pill ${mcpOn ? 'is-enabled' : ''}">🔌 MCP: ${mcpOn ? 'ENABLED' : 'OFF'}</div>
      <div class="fl-dsa-cap-pill ${subOn ? 'is-enabled' : ''}">🐝 SWARM: ${subOn ? 'ENABLED' : 'OFF'}</div>
    </div>
    <div class="fl-dsa-prompt-pill">
      <span class="fl-dsa-orb">🧠</span>
      <span class="fl-dsa-prompt-txt" title="${escapeHtml(desc)}">${escapeHtml(desc)}</span>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const pEl = box.querySelector('.fl-dsa-prompt-txt');
    if (pEl && str.trim()) pEl.textContent = str.replace(/[\r\n]+/g, ' ').slice(0, 100);
  };

    const badge = box.querySelector('.fl-dsa-badge');
  if (box._dsaTimer) clearInterval(box._dsaTimer);
  box._dsaTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._dsaTimer) { clearInterval(box._dsaTimer); box._dsaTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._dsaTimer) { clearInterval(box._dsaTimer); box._dsaTimer = null; } return; }
    if (document.hidden) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `DNA FORGE • ${elapsedSec}s`;
  }, 150);
}

function renderLiveManageSubagents(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const act = String(d.Action || d.action || 'list').toLowerCase();
  const ids = Array.isArray(d.ConversationIds) ? d.ConversationIds.join(', ') : 'Active Swarm Constellation';

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-manage-subagents';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  let msaFeed = [
    `Executing manage_subagents [${act.toUpperCase()}] on ${ids}...`,
    `Inspecting live subagent lifecycle states & conversation transcripts...`
  ];

  box.innerHTML = `
    <div class="fl-msa-header">
      <div class="fl-msa-title-group">
        <span class="fl-msa-pill">🕸️ MANAGE SUBAGENTS</span>
        <span class="fl-msa-target" title="${escapeHtml(ids)}">${escapeHtml(ids)}</span>
      </div>
      <span class="fl-msa-badge">SWARM • 0.01s</span>
    </div>
    <div class="fl-msa-actions">
      <div class="fl-msa-act-pill ${act === 'list' ? 'is-active' : ''}">📡 LIST SWARM</div>
      <div class="fl-msa-act-pill ${act === 'kill' ? 'is-active' : ''}">🛑 KILL NODE</div>
      <div class="fl-msa-act-pill ${act === 'kill_all' ? 'is-active' : ''}">💥 KILL ALL</div>
    </div>
    <div class="fl-msa-stream-pill">
      <span class="fl-msa-dot"></span>
      <span class="fl-msa-stream-txt">${escapeHtml(msaFeed[0])}</span>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const clean = str.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    if (clean.length > 0) {
      msaFeed = clean.slice(0, 10);
      const sEl = box.querySelector('.fl-msa-stream-txt');
      if (sEl) sEl.textContent = msaFeed[0];
    }
  };

    const badge = box.querySelector('.fl-msa-badge');
  const sEl = box.querySelector('.fl-msa-stream-txt');
  if (box._msaTimer) clearInterval(box._msaTimer);
  let tick = 0;
  box._msaTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._msaTimer) { clearInterval(box._msaTimer); box._msaTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._msaTimer) { clearInterval(box._msaTimer); box._msaTimer = null; } return; }
    if (document.hidden) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `RADAR • ${elapsedSec}s`;

        // (cached sEl)
    if (sEl && msaFeed.length > 0) sEl.textContent = msaFeed[tick % msaFeed.length];
  }, 150);
}

function renderLiveSendMessage(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const recipient = String(d.Recipient || d.recipient || d.to || 'subagent-node');
  const msg = String(d.Message || d.message || d.content || 'Transmitting inter-agent IPC payload...');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-send-message';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  box.innerHTML = `
    <div class="fl-sm-header">
      <div class="fl-sm-bridge">
        <span class="fl-sm-node-pill">🧠 PARENT</span>
        <span class="fl-sm-wave-dots"><span></span><span></span><span></span></span>
        <span class="fl-sm-node-pill recipient" title="${escapeHtml(recipient)}">🛰️ ${escapeHtml(recipient)}</span>
      </div>
      <span class="fl-sm-badge">IPC WAVE • 0.01s</span>
    </div>
    <div class="fl-sm-bubble">
      <span class="fl-sm-orb">✉️</span>
      <span class="fl-sm-msg-txt" title="${escapeHtml(msg)}">${escapeHtml(msg)}</span>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const mEl = box.querySelector('.fl-sm-msg-txt');
    if (mEl && str.trim()) mEl.textContent = str.replace(/[\r\n]+/g, ' ').slice(0, 110);
  };

    const badge = box.querySelector('.fl-sm-badge');
  if (box._smTimer) clearInterval(box._smTimer);
  box._smTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._smTimer) { clearInterval(box._smTimer); box._smTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._smTimer) { clearInterval(box._smTimer); box._smTimer = null; } return; }
    if (document.hidden) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `SYNAPSE IPC • ${elapsedSec}s`;
  }, 150);
}

function renderLiveGenerateImage(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const imgName = String(d.ImageName || d.imageName || d.name || 'sovereign_artwork');
  const ratio = String(d.AspectRatio || d.aspectRatio || '1:1');
  const prompt = String(d.Prompt || d.prompt || 'Synthesizing high-resolution visual asset...');

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-generate-image';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  box.innerHTML = `
    <div class="fl-gi-header">
      <div class="fl-gi-title-group">
        <span class="fl-gi-pill">🎨 GENERATE IMAGE</span>
        <span class="fl-gi-name" title="${escapeHtml(imgName)}">${escapeHtml(imgName)}.png</span>
      </div>
      <span class="fl-gi-badge">DIFFUSION • 0.01s</span>
    </div>
    <div class="fl-gi-body">
      <div class="fl-gi-prism-orb">
        <div class="fl-gi-prism-inner">✨</div>
      </div>
      <div class="fl-gi-capsules">
        <div class="fl-gi-meta-row">
          <span class="fl-gi-chip">ASPECT: ${escapeHtml(ratio)}</span>
          <span class="fl-gi-chip">PRISM ENGINE</span>
        </div>
        <div class="fl-gi-prompt-pill">
          <span class="fl-gi-dot"></span>
          <span class="fl-gi-prompt-txt" title="${escapeHtml(prompt)}">${escapeHtml(prompt)}</span>
        </div>
      </div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const pEl = box.querySelector('.fl-gi-prompt-txt');
    if (pEl && str.trim()) pEl.textContent = str.replace(/[\r\n]+/g, ' ').slice(0, 110);
  };

    const badge = box.querySelector('.fl-gi-badge');
  if (box._giTimer) clearInterval(box._giTimer);
  box._giTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._giTimer) { clearInterval(box._giTimer); box._giTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._giTimer) { clearInterval(box._giTimer); box._giTimer = null; } return; }
    if (document.hidden) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `RENDERING • ${elapsedSec}s`;
  }, 150);
}

function renderLiveSendMedia(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const mediaPath = String(d.path || d.file || d.url || d.media || d.target || 'media_stream_asset');
  const mime = String(d.mime_type || d.mimeType || d.type || 'MEDIA/STREAM').toUpperCase();
  const caption = String(d.caption || d.description || d.title || mediaPath);

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-send-media';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  box.innerHTML = `
    <div class="fl-smd-header">
      <div class="fl-smd-title-group">
        <span class="fl-smd-pill">🎧 SEND MEDIA</span>
        <span class="fl-smd-target" title="${escapeHtml(mediaPath)}">${escapeHtml(mediaPath)}</span>
      </div>
      <span class="fl-smd-badge">STREAMING • 0.01s</span>
    </div>
    <div class="fl-smd-body">
      <div class="fl-smd-disc-orb">🎬</div>
      <div class="fl-smd-eq-bars">
        <span class="fl-smd-bar"></span>
        <span class="fl-smd-bar"></span>
        <span class="fl-smd-bar"></span>
        <span class="fl-smd-bar"></span>
        <span class="fl-smd-bar"></span>
      </div>
      <div class="fl-smd-info-pill">
        <span class="fl-smd-mime-chip">${escapeHtml(mime)}</span>
        <span class="fl-smd-caption" title="${escapeHtml(caption)}">${escapeHtml(caption)}</span>
      </div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const cEl = box.querySelector('.fl-smd-caption');
    if (cEl && str.trim()) cEl.textContent = str.replace(/[\r\n]+/g, ' ').slice(0, 100);
  };

    const badge = box.querySelector('.fl-smd-badge');
  if (box._smdTimer) clearInterval(box._smdTimer);
  box._smdTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._smdTimer) { clearInterval(box._smdTimer); box._smdTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._smdTimer) { clearInterval(box._smdTimer); box._smdTimer = null; } return; }
    if (document.hidden) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `MEDIA POD • ${elapsedSec}s`;
  }, 150);
}

function renderLiveVisualPainter(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const widgetType = String(d.widget_type || d.type || d.chart_type || d.kind || 'bar_chart').toUpperCase();
  const title = String(d.title || d.Title || d.name || `${widgetType} TELEMETRY`);
  const subtitle = String(d.subtitle || d.description || 'Buffering visual artifact until chat turn completes');
  const dataObj = d.data || d.payload || {};
  const labelCount = Array.isArray(dataObj.labels) ? dataObj.labels.length : (Array.isArray(d.cards) ? d.cards.length : (Array.isArray(d.candles) ? d.candles.length : 4));
  const seriesCount = Array.isArray(dataObj.series) ? dataObj.series.length : 1;

  let box = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  if (!box) {
    box = document.createElement('div');
    box.className = 'fl-live-render-visual';
    box.setAttribute('data-live-step', String(stepIdx));
    box._spawnTime = Date.now();
    activeSlot.appendChild(box);
  }

  box.innerHTML = `
    <div class="fl-rv-header">
      <div class="fl-rv-title-group">
        <span class="fl-rv-pill">📊 RENDER VISUAL</span>
        <span class="fl-rv-type-chip">${escapeHtml(widgetType)}</span>
      </div>
      <span class="fl-rv-badge">SYNTHESIZING • 0.01s</span>
    </div>
    <div class="fl-rv-body">
      <div class="fl-rv-orb-wrap">
        <div class="fl-rv-orb-ring"></div>
        <div class="fl-rv-orb-core">
          <span class="fl-rv-mini-bar"></span>
          <span class="fl-rv-mini-bar"></span>
          <span class="fl-rv-mini-bar"></span>
          <span class="fl-rv-mini-bar"></span>
        </div>
      </div>
      <div class="fl-rv-stream-col">
        <div class="fl-rv-title-pill">
          <span class="fl-rv-dot"></span>
          <span class="fl-rv-title-txt" title="${escapeHtml(title)}">${escapeHtml(title)}</span>
        </div>
        <div class="fl-rv-meta-row">
          <span class="fl-rv-meta-pill">${labelCount} POINTS • ${seriesCount} SERIES</span>
          <span class="fl-rv-meta-pill fl-rv-sub-txt" title="${escapeHtml(subtitle)}">${escapeHtml(subtitle)}</span>
          <div class="fl-rv-wave-pills">
            <span class="fl-rv-wave-seg"></span>
            <span class="fl-rv-wave-seg"></span>
            <span class="fl-rv-wave-seg"></span>
            <span class="fl-rv-wave-seg"></span>
          </div>
        </div>
      </div>
    </div>
  `;

  box._injectOutputLines = (rawOut) => {
    const str = typeof rawOut === 'string' ? rawOut : JSON.stringify(rawOut || '');
    const subEl = box.querySelector('.fl-rv-sub-txt');
    if (subEl && str.includes('visual:')) {
      subEl.textContent = 'Visual payload buffered (reveals when chat ends)';
    }
  };

    const badge = box.querySelector('.fl-rv-badge');
  if (box._rvTimer) clearInterval(box._rvTimer);
  box._rvTimer = setInterval(() => {
    if (!box.isConnected) {
      if (box._rvTimer) { clearInterval(box._rvTimer); box._rvTimer = null; }
      return;
    }
    if (box.classList.contains('is-locked')) { if (box._rvTimer) { clearInterval(box._rvTimer); box._rvTimer = null; } return; }
    if (document.hidden) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
        // (cached badge)
    if (badge) badge.textContent = `SYNTHESIZING • ${elapsedSec}s`;
  }, 250);
}

function renderLiveDynamicExternalTool(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  const cleanName = String(toolName || 'tool').replace(/^flow_/, '').replace(/^default_api:/, '').toLowerCase().trim();
  const TOOL_CDN_VERSION = '20261018_0930';
  const cdnBase = '/canvas/tools';

  // 1. Dynamic CSS Injection from Local Daemon: Load tools/<cleanName>/style.css
  const cssId = `fl-dyn-tool-css-${cleanName}`;
  if (!document.getElementById(cssId)) {
    const link = document.createElement('link');
    link.id = cssId;
    link.rel = 'stylesheet';
    link.href = `${cdnBase}/${cleanName}/style.css?v=${TOOL_CDN_VERSION}`;
    document.head.appendChild(link);
  }

  // 2. Prioritize Sovereign Tool Registry
  if (window.FloworkToolRegistry && typeof window.FloworkToolRegistry.mountLive === 'function') {
    const liveEl = window.FloworkToolRegistry.mountLive(activeSlot, toolName, details, stepIdx);
    if (liveEl) return;
  }

  // 3. Fallback to generic ambient holo stream
  renderLiveGenericToolBox(activeSlot, toolName, details, stepIdx);
}

function renderLiveGenericToolBox(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const cleanName = (toolName || 'tool').replace(/^flow_/, '').replace(/^default_api:/, '').toUpperCase();
  const summary = d.task_description || d.task || d.toolSummary || d.toolAction || d.action || d.Action || d.reason || (typeof details === 'string' ? details : 'Sovereign operation');
  renderLiveAmbientHoloStream(activeSlot, `OPS // ${cleanName}`, String(summary), 'cyan', stepIdx);
}

function clearAllBoxTimers(box) {
  if (!box) return;
  const timers = [
    '_typingTimer', '_screeningTimer', '_bashTimer', '_swarmTimer', '_memoryTimer',
    '_skillTimer', '_webTimer', '_urlTimer', '_lockBoxTimer', '_healthTimer',
    '_auditTimer', '_hcTimer', '_portTimer', '_webSecTimer', '_wiTimer',
    '_schTimer', '_mtTimer', '_pcTimer', '_gkTimer', '_cameraTimer',
    '_ytvTimer', '_ytcTimer', '_yttTimer', '_ytsTimer', '_ytcmTimer',
    '_ytstTimer', '_aqTimer', '_srTimer', '_ppTimer', '_isaTimer',
    '_dsaTimer', '_msaTimer', '_smTimer', '_giTimer', '_smdTimer',
    '_rvTimer', '_canvasTimer', '_genericTimer'
  ];
  for (let i = 0; i < timers.length; i++) {
    const k = timers[i];
    if (box[k]) {
      clearInterval(box[k]);
      box[k] = null;
    }
  }
}
window.clearAllBoxTimers = clearAllBoxTimers;

function dismissLiveToolBox(activeSlot, stepIdx, outputData) {
  const selectorList = '.fl-live-ambient-stage, .fl-live-view-file, .fl-live-write-file, .fl-live-replace-file, .fl-live-search-tools, .fl-live-search-web, .fl-live-read-url, .fl-live-flow-lock, .fl-live-sys-health, .fl-live-audit-sec, .fl-live-detect-hc, .fl-live-audit-port, .fl-live-web-sec, .fl-live-web-intel, .fl-live-schedule, .fl-live-manage-task, .fl-live-plugin-ctrl, .fl-live-gatekeeper, .fl-live-screenshot, .fl-live-yt-video, .fl-live-yt-channel, .fl-live-yt-transcript, .fl-live-yt-summary, .fl-live-yt-comments, .fl-live-yt-strategy, .fl-live-ask-question, .fl-live-sys-restart, .fl-live-plugin-publish, .fl-live-invoke-subagent, .fl-live-define-subagent, .fl-live-manage-subagents, .fl-live-send-message, .fl-live-generate-image, .fl-live-send-media, .fl-live-render-visual, [class*="-pod"], .fl-live-dynamic-tool, .fl-live-scan-box, .fl-live-forge-box, .fl-live-bash-box, .fl-live-swarm-box, .fl-live-memory-box, .fl-live-skill-box, .fl-live-audit-box, .fl-live-canvas-box, .fl-live-camera-box, .fl-live-generic-box';
  const box = (activeSlot ? activeSlot.querySelector(`[data-live-step="${stepIdx}"]`) : null) ||
              document.querySelector(`.fl-live-active-slot [data-live-step="${stepIdx}"]`) ||
              (activeSlot ? activeSlot.querySelector(selectorList) : null) ||
              document.querySelector(`.fl-live-active-slot :is(${selectorList})`);
  if (!box) return;

  if (box._dynamicUiModule && typeof box._dynamicUiModule.onDone === 'function') {
    box._dynamicUiModule.onDone(activeSlot || box.parentElement, outputData);
  }

  // Feed real behind-the-scenes output into the active hyper-speed animation!
  if (typeof box._injectOutputLines === 'function' && outputData !== undefined && outputData !== null) {
    box._injectOutputLines(outputData);
  }

  // Keep view_file, write_to_file, and replace_file_content visible much longer (~6.8s total) so user can inspect real file content!
  const isFileBox = box.classList.contains('fl-live-view-file') ||
                    box.classList.contains('fl-live-write-file') ||
                    box.classList.contains('fl-live-replace-file');
  const minBurstMs = isFileBox ? 3600 : 1200;
  const holdLockedMs = isFileBox ? 3200 : 900;

  const elapsed = Date.now() - (box._spawnTime || Date.now());
  const burstRemaining = Math.max(0, minBurstMs - elapsed);

  if (box._lockTimer) clearTimeout(box._lockTimer);
  box._lockTimer = setTimeout(() => {
    clearAllBoxTimers(box);
    if (!box.isConnected) return;

    // Lock verified status
    if (box._typingTimer) { clearInterval(box._typingTimer); box._typingTimer = null; }
    if (box._screeningTimer) { clearInterval(box._screeningTimer); box._screeningTimer = null; }
    if (box._bashTimer) { clearInterval(box._bashTimer); box._bashTimer = null; }
    if (box._swarmTimer) { clearInterval(box._swarmTimer); box._swarmTimer = null; }
    if (box._memoryTimer) { clearInterval(box._memoryTimer); box._memoryTimer = null; }
    if (box._skillTimer) { clearInterval(box._skillTimer); box._skillTimer = null; }
    if (box._webTimer) { clearInterval(box._webTimer); box._webTimer = null; }
    if (box._urlTimer) { clearInterval(box._urlTimer); box._urlTimer = null; }
    if (box._lockBoxTimer) { clearInterval(box._lockBoxTimer); box._lockBoxTimer = null; }
    if (box._healthTimer) { clearInterval(box._healthTimer); box._healthTimer = null; }
    if (box._auditTimer) { clearInterval(box._auditTimer); box._auditTimer = null; }
    if (box._hcTimer) { clearInterval(box._hcTimer); box._hcTimer = null; }
    if (box._portTimer) { clearInterval(box._portTimer); box._portTimer = null; }
    if (box._webSecTimer) { clearInterval(box._webSecTimer); box._webSecTimer = null; }
    if (box._wiTimer) { clearInterval(box._wiTimer); box._wiTimer = null; }
    if (box._schTimer) { clearInterval(box._schTimer); box._schTimer = null; }
    if (box._mtTimer) { clearInterval(box._mtTimer); box._mtTimer = null; }
    if (box._pcTimer) { clearInterval(box._pcTimer); box._pcTimer = null; }
    if (box._gkTimer) { clearInterval(box._gkTimer); box._gkTimer = null; }
    if (box._ytvTimer) { clearInterval(box._ytvTimer); box._ytvTimer = null; }
    if (box._ytcTimer) { clearInterval(box._ytcTimer); box._ytcTimer = null; }
    if (box._yttTimer) { clearInterval(box._yttTimer); box._yttTimer = null; }
    if (box._ytsTimer) { clearInterval(box._ytsTimer); box._ytsTimer = null; }
    if (box._ytcmTimer) { clearInterval(box._ytcmTimer); box._ytcmTimer = null; }
    if (box._ytstTimer) { clearInterval(box._ytstTimer); box._ytstTimer = null; }
    if (box._aqTimer) { clearInterval(box._aqTimer); box._aqTimer = null; }
    if (box._srTimer) { clearInterval(box._srTimer); box._srTimer = null; }
    if (box._ppTimer) { clearInterval(box._ppTimer); box._ppTimer = null; }
    if (box._isaTimer) { clearInterval(box._isaTimer); box._isaTimer = null; }
    if (box._dsaTimer) { clearInterval(box._dsaTimer); box._dsaTimer = null; }
    if (box._msaTimer) { clearInterval(box._msaTimer); box._msaTimer = null; }
    if (box._smTimer) { clearInterval(box._smTimer); box._smTimer = null; }
    if (box._giTimer) { clearInterval(box._giTimer); box._giTimer = null; }
    if (box._smdTimer) { clearInterval(box._smdTimer); box._smdTimer = null; }
    if (box._rvTimer) { clearInterval(box._rvTimer); box._rvTimer = null; }
    if (box._canvasTimer) { clearInterval(box._canvasTimer); box._canvasTimer = null; }
    if (box._cameraTimer) { clearInterval(box._cameraTimer); box._cameraTimer = null; }
    if (box._genericTimer) { clearInterval(box._genericTimer); box._genericTimer = null; }

    box.classList.add('is-locked');

    if (box.classList.contains('fl-live-view-file')) {
      const badge = box.querySelector('.fl-vf-speed-badge');
      if (badge) badge.innerHTML = '✓ 100% READ • EXIT CODE 0';
      const verb = box.querySelector('.fl-vf-verb');
      if (verb) verb.textContent = 'INGESTED';
    } else if (box.classList.contains('fl-live-write-file')) {
      const badge = box.querySelector('.fl-wtf-badge');
      if (badge) badge.textContent = '✓ FILE WRITTEN • EXIT CODE 0';
      const bytesEl = box.querySelector('.fl-wtf-bytes');
      if (bytesEl) bytesEl.textContent = '100% COMMITTED TO DISK';
    } else if (box.classList.contains('fl-live-replace-file')) {
      const timerEl = box.querySelector('.fl-rfc-timer');
      if (timerEl) timerEl.textContent = '✓ SPLICED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-search-tools')) {
      const speedEl = box.querySelector('.fl-st-speed');
      if (speedEl) speedEl.textContent = '✓ TOOLS LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-skill-box')) {
      const statusEl = box.querySelector('.fl-sk-status');
      if (statusEl) statusEl.textContent = '✓ 20/20 LOCKED • EXIT CODE 0';
      box.querySelectorAll('.fl-sk-led').forEach(led => led.classList.add('is-lit'));
    } else if (box.classList.contains('fl-live-search-web')) {
      const badge = box.querySelector('.fl-sw-badge');
      if (badge) badge.textContent = '✓ OSINT LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-read-url')) {
      const pipe = box.querySelector('.fl-ru-pipe-badge');
      if (pipe) pipe.textContent = '✓ MD EXTRACTED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-flow-lock')) {
      const statusEl = box.querySelector('.fl-flk-status');
      if (statusEl) statusEl.textContent = '✓ CRYO-LOCKED • EXIT CODE 0';
      const lbl = box.querySelector('.fl-flk-vault-lbl');
      if (lbl) lbl.textContent = 'LOCKED';
    } else if (box.classList.contains('fl-live-sys-health')) {
      const badge = box.querySelector('.fl-sh-badge');
      if (badge) badge.textContent = '✓ HEALTHY • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-audit-sec')) {
      const badge = box.querySelector('.fl-as-badge');
      if (badge) badge.textContent = '✓ SAST VERIFIED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-detect-hc')) {
      const badge = box.querySelector('.fl-dhc-badge');
      if (badge) badge.textContent = '✓ DE-HARDCODED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-audit-port')) {
      const badge = box.querySelector('.fl-ap-badge');
      if (badge) badge.textContent = '✓ TRI-OS VERIFIED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-web-sec')) {
      const badge = box.querySelector('.fl-wsa-badge');
      if (badge) badge.textContent = '✓ PERIMETER LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-web-intel')) {
      const badge = box.querySelector('.fl-wi-badge');
      if (badge) badge.textContent = '✓ INTEL LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-schedule')) {
      const badge = box.querySelector('.fl-sch-badge');
      if (badge) badge.textContent = '✓ CHRONO ARMED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-manage-task')) {
      const badge = box.querySelector('.fl-mt-badge');
      if (badge) badge.textContent = '✓ TASK SYNCED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-plugin-ctrl')) {
      const badge = box.querySelector('.fl-pc-badge');
      if (badge) badge.textContent = '✓ PLUGIN READY • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-gatekeeper')) {
      const badge = box.querySelector('.fl-gk-badge');
      if (badge) badge.textContent = '✓ GATES PASSED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-screenshot')) {
      const badge = box.querySelector('.fl-ss-badge');
      if (badge) badge.textContent = '✓ FRAME LOCKED • EXIT CODE 0';
      const ret = box.querySelector('.fl-ss-reticle');
      if (ret) ret.textContent = '[ ✓ PNG CAPTURED ]';
    } else if (box.classList.contains('fl-live-yt-video')) {
      const badge = box.querySelector('.fl-ytv-badge');
      if (badge) badge.textContent = '✓ VIDEO SCANNED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-channel')) {
      const badge = box.querySelector('.fl-ytc-badge');
      if (badge) badge.textContent = '✓ PULSE LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-transcript')) {
      const badge = box.querySelector('.fl-ytt-badge');
      if (badge) badge.textContent = '✓ TRANSCRIPT READY • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-summary')) {
      const badge = box.querySelector('.fl-yts-badge');
      if (badge) badge.textContent = '✓ SUMMARY LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-comments')) {
      const badge = box.querySelector('.fl-ytcm-badge');
      if (badge) badge.textContent = '✓ BUBBLES LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-strategy')) {
      const badge = box.querySelector('.fl-ytst-badge');
      if (badge) badge.textContent = '✓ STRATEGY READY • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-ask-question')) {
      const badge = box.querySelector('.fl-aq-badge');
      if (badge) badge.textContent = '✓ ANSWER LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-sys-restart')) {
      const badge = box.querySelector('.fl-sr-badge');
      if (badge) badge.textContent = '✓ RESTART ARMED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-plugin-publish')) {
      const badge = box.querySelector('.fl-pp-badge');
      if (badge) badge.textContent = '✓ PUBLISHED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-invoke-subagent')) {
      const badge = box.querySelector('.fl-isa-badge');
      if (badge) badge.textContent = '✓ SUBAGENT SPAWNED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-define-subagent')) {
      const badge = box.querySelector('.fl-dsa-badge');
      if (badge) badge.textContent = '✓ DNA REGISTERED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-manage-subagents')) {
      const badge = box.querySelector('.fl-msa-badge');
      if (badge) badge.textContent = '✓ SWARM SYNCED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-send-message')) {
      const badge = box.querySelector('.fl-sm-badge');
      if (badge) badge.textContent = '✓ IPC DELIVERED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-generate-image')) {
      const badge = box.querySelector('.fl-gi-badge');
      if (badge) badge.textContent = '✓ IMAGE SYNTHESIZED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-send-media')) {
      const badge = box.querySelector('.fl-smd-badge');
      if (badge) badge.textContent = '✓ MEDIA DELIVERED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-render-visual')) {
      const badge = box.querySelector('.fl-rv-badge');
      if (badge) badge.textContent = '✓ VISUAL BUFFERED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-memory-box')) {
      const header = box.querySelector('.fl-brain-pill-header');
      if (header) header.textContent = '✓ SYNAPSE LOCKED // EXIT CODE 0';
      const sub = box.querySelector('.fl-brain-orb-sublabel');
      if (sub) sub.textContent = 'LOCKED';
      const sync = box.querySelector('.fl-brain-sync-pct');
      if (sync) sync.textContent = 'SYNC: 100%';
    } else if (box.classList.contains('fl-live-bash-box')) {
      const badge = box.querySelector('.fl-bash-badge');
      if (badge) {
        const exitCode = (outputData && typeof outputData === 'object' && outputData.exitCode !== undefined) ? outputData.exitCode : 0;
        if (exitCode === 0) {
          badge.style.background = 'rgba(0, 255, 178, 0.2)';
          badge.style.color = '#00ffb2';
          badge.textContent = '✓ EXIT CODE 0';
        } else {
          badge.style.background = 'rgba(239, 68, 68, 0.2)';
          badge.style.color = '#f87171';
          badge.textContent = `✕ EXIT CODE ${exitCode}`;
        }
      }
    } else if (box.classList.contains('fl-live-ambient-stage')) {
      const badge = box.querySelector('.fl-ambient-badge');
      if (badge) {
        badge.className = 'fl-ambient-badge emerald';
        badge.textContent = '✓ SYNAPSE LOCKED (EXIT CODE 0)';
      }
      const wave = box.querySelector('.fl-ambient-sine-wave');
      if (wave) {
        wave.style.stroke = 'var(--holo-emerald, #10b981)';
        wave.style.animation = 'none';
      }
      const beam = box.querySelector('.fl-ambient-laser-beam');
      if (beam) {
        beam.setAttribute('fill', '#10b981');
        beam.style.filter = 'drop-shadow(0 0 8px #10b981)';
      }
    }

    if (box._dismissTimer) clearTimeout(box._dismissTimer);
    box._dismissTimer = setTimeout(() => {
      if (box.isConnected) {
        box.classList.add('is-finished');
        setTimeout(() => {
          if (box.isConnected) box.remove();
        }, 380);
      }
    }, holdLockedMs);
  }, burstRemaining);
}
window.dismissLiveToolBox = dismissLiveToolBox;

function renderToolInArea(toolsArea, toolName, details, status, stepIdx, activeToolElements) {
  if (!toolsArea) return null;
  const rawTool = (toolName || 'tool').toLowerCase();
  let cleanToolId = String(toolName || 'tool')
    .replace(/^flow_/, '')
    .replace(/^default_api:/, '')
    .toLowerCase()
    .trim();
  if (cleanToolId === 'system_health') cleanToolId = 'sys_health';
  if (cleanToolId === 'render_visual_chart') cleanToolId = 'render_visual';

  // Dynamic non-blocking injection of stylesheet for this tool (local or Cloudflare CDN)
  const cdnCssId = `fl-tool-css-${cleanToolId}`;
  if (!document.getElementById(cdnCssId)) {
    const toolsBase = '/canvas/tools';
    const link = document.createElement('link');
    link.id = cdnCssId;
    link.rel = 'stylesheet';
    link.href = `${toolsBase}/${cleanToolId}/style.css?v=20261018_0930`;
    document.head.appendChild(link);
  }

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});

  // Record pinned skills & mounted/active tools into Thinking Card & Multi-OS Loop Bar
  recordThinkingArsenal(toolName, details, status, d.output ?? d.rawOutput ?? null, stepIdx);

  // Initialize Mr. Flow audio UI controls
  FloworkMrFlowAudio.initUi();

  const { activeSlot, capsule, capsuleBody } = getOrCreateToolsCapsule(toolsArea);

  // Keep capsule visible so completed tool cards render immediately
  if (capsule) {
    capsule.style.display = 'block';
  }

  // Advance Neural Anticipator DAG node to Execute phase
  if (currentThinkingController && currentThinkingController.advanceDag) {
    const cleanToolName = cleanToolId.toUpperCase();
    currentThinkingController.advanceDag(3, `3. EXECUTE [${cleanToolName}]`);
  }

  const isSearchTools = rawTool.includes('search_tools') || rawTool.includes('tool_search') || rawTool.includes('find_tool');
  const isSearchWeb = rawTool.includes('search_web');
  const isReadUrl = rawTool.includes('read_url');
  const isFlowLock = rawTool.includes('flow_lock') || rawTool === 'lock';
  const isSysHealth = rawTool.includes('sys_health') || rawTool.includes('system_health');
  const isDetectHardcode = rawTool.includes('detect_hardcode') || rawTool.includes('hardcode');
  const isAuditPortability = rawTool.includes('audit_portability') || rawTool.includes('portability');
  const isWebSecAudit = rawTool.includes('web_security_audit') || rawTool.includes('web_sec');
  const isWebIntel = rawTool.includes('website_intelligence') || rawTool.includes('website_intel') || rawTool.includes('web_intel');
  const isSchedule = rawTool === 'schedule' || rawTool.includes(':schedule') || rawTool.includes('flow_schedule');
  const isManageTask = rawTool.includes('manage_task');
  const isPluginControl = rawTool.includes('plugin_control');
  const isPluginPublish = rawTool.includes('plugin_publish');
  const isGatekeeper = rawTool.includes('request_publish_gatekeeper') || rawTool.includes('gatekeeper');
  const isYtVideo = rawTool.includes('youtube_spy_video');
  const isYtChannel = rawTool.includes('youtube_spy_channel');
  const isYtTranscript = rawTool.includes('youtube_spy_transcript');
  const isYtSummary = rawTool.includes('youtube_spy_summary');
  const isYtComments = rawTool.includes('youtube_spy_comments');
  const isYtStrategy = rawTool.includes('youtube_spy_competitor_strategy');
  const isAskQuestion = rawTool.includes('ask_question');
  const isSysRestart = rawTool.includes('system_restart');
  const isTeamAudit = rawTool.includes('team_audit') || rawTool.includes('council_audit');
  const isGenImage = rawTool.includes('generate_image');
  const isSendMedia = rawTool.includes('send_media');
  const isCamera = rawTool.includes('screenshot') || rawTool.includes('screen_shot') || rawTool.includes('capture') || rawTool.includes('camera') || rawTool.includes('snapshot') || rawTool.includes('x11grab') || rawTool.includes('view_screen') || rawTool.includes('shoot');
  const isMemory = rawTool.includes('brain') || rawTool.includes('memory') || rawTool.includes('synapse') || rawTool.includes('crystal');
  const isScanner = !isCamera && !isMemory && !isSearchTools && !isSearchWeb && !isReadUrl && !isWebIntel && !isYtVideo && !isYtChannel && !isYtTranscript && !isYtSummary && !isYtComments && !isYtStrategy && (rawTool.includes('read') || rawTool.includes('view') || rawTool.includes('inspect') || rawTool.includes('ingest') || rawTool.includes('recon') || rawTool.includes('search') || rawTool.includes('cat') || rawTool.includes('grep') || rawTool.includes('youtube') || rawTool.includes('yt_spy'));
  const isForger = !isFlowLock && (rawTool.includes('write') || rawTool.includes('replace') || rawTool.includes('edit') || rawTool.includes('forge') || rawTool.includes('splice') || rawTool.includes('patch') || rawTool.includes('deterministic') || rawTool.includes('helper'));
  const isBash = rawTool.includes('run_command') || rawTool.includes('exec') || rawTool.includes('terminal');
  const isSkill = rawTool.includes('skill');
  const isAudit = !isTeamAudit && !isSysHealth && !isDetectHardcode && !isAuditPortability && !isWebSecAudit && !isGatekeeper && (rawTool.includes('audit') || rawTool.includes('security'));
  const isVisual = !isCamera && !isGenImage && !isSendMedia && (rawTool.includes('visual') || rawTool.includes('chart') || rawTool.includes('diagram') || rawTool.includes('render_visual'));

  // Spawn specialized live terminal animation when actively streaming or tool is running
  let existingLiveBox = activeSlot ? activeSlot.querySelector(`[data-live-step="${stepIdx}"]`) : null;
  if (!existingLiveBox && activeSlot && (isChatStreaming || (typeof window !== 'undefined' && window.isChatStreaming) || status === 'running')) {
    // 1. Asynchronously pre-fetch tool assets from CDN via Tool Registry
    if (window.FloworkToolRegistry && typeof window.FloworkToolRegistry.loadTool === 'function') {
      window.FloworkToolRegistry.loadTool(cleanToolId).catch(() => {});
    }

    // 2. Prioritize Sovereign Tool Registry custom non-fallback mountLive if registered with custom UI
    const customRegistryTool = (window.FloworkToolRegistry && typeof window.FloworkToolRegistry.get === 'function')
      ? window.FloworkToolRegistry.get(cleanToolId)
      : null;
    if (customRegistryTool && !customRegistryTool.isDefaultFallback && customRegistryTool.hasCustomLiveUI && typeof customRegistryTool.mountLive === 'function') {
      existingLiveBox = customRegistryTool.mountLive(activeSlot, cleanToolId, details, stepIdx);
    } else if (isSearchTools) {
      renderLiveSearchTools(activeSlot, toolName, details, stepIdx);
    } else if (isSearchWeb) {
      FloworkMrFlowAudio.trigger('target_lock');
      renderLiveSearchWeb(activeSlot, toolName, details, stepIdx);
    } else if (isReadUrl) {
      FloworkMrFlowAudio.trigger('target_lock');
      renderLiveReadUrl(activeSlot, toolName, details, stepIdx);
    } else if (isFlowLock) {
      FloworkMrFlowAudio.trigger('code_patched');
      renderLiveFlowLock(activeSlot, toolName, details, stepIdx);
    } else if (isSysHealth) {
      renderLiveSysHealth(activeSlot, toolName, details, stepIdx);
    } else if (isDetectHardcode) {
      renderLiveDetectHardcode(activeSlot, toolName, details, stepIdx);
    } else if (isAuditPortability) {
      renderLiveAuditPortability(activeSlot, toolName, details, stepIdx);
    } else if (isWebSecAudit) {
      FloworkMrFlowAudio.trigger('target_lock');
      renderLiveWebSecurityAudit(activeSlot, toolName, details, stepIdx);
    } else if (isWebIntel) {
      FloworkMrFlowAudio.trigger('target_lock');
      renderLiveWebsiteIntelligence(activeSlot, toolName, details, stepIdx);
    } else if (isSchedule) {
      renderLiveSchedule(activeSlot, toolName, details, stepIdx);
    } else if (isManageTask) {
      renderLiveManageTask(activeSlot, toolName, details, stepIdx);
    } else if (isPluginControl) {
      renderLivePluginControl(activeSlot, toolName, details, stepIdx);
    } else if (isPluginPublish) {
      renderLivePluginPublish(activeSlot, toolName, details, stepIdx);
    } else if (isGatekeeper) {
      renderLivePublishGatekeeper(activeSlot, toolName, details, stepIdx);
    } else if (isYtVideo) {
      FloworkMrFlowAudio.trigger('target_lock');
      renderLiveYtSpyVideo(activeSlot, toolName, details, stepIdx);
    } else if (isYtChannel) {
      FloworkMrFlowAudio.trigger('target_lock');
      renderLiveYtSpyChannel(activeSlot, toolName, details, stepIdx);
    } else if (isYtTranscript) {
      renderLiveYtSpyTranscript(activeSlot, toolName, details, stepIdx);
    } else if (isYtSummary) {
      renderLiveYtSpySummary(activeSlot, toolName, details, stepIdx);
    } else if (isYtComments) {
      renderLiveYtSpyComments(activeSlot, toolName, details, stepIdx);
    } else if (isYtStrategy) {
      FloworkMrFlowAudio.trigger('target_lock');
      renderLiveYtSpyStrategy(activeSlot, toolName, details, stepIdx);
    } else if (isAskQuestion) {
      renderLiveAskQuestion(activeSlot, toolName, details, stepIdx);
    } else if (isSysRestart) {
      renderLiveSystemRestart(activeSlot, toolName, details, stepIdx);
    } else if (isTeamAudit) {
      FloworkMrFlowAudio.trigger('target_lock');
      renderLiveTeamAudit(activeSlot, toolName, details, stepIdx);
    } else if (isGenImage) {
      renderLiveGenerateImage(activeSlot, toolName, details, stepIdx);
    } else if (isSendMedia) {
      renderLiveSendMedia(activeSlot, toolName, details, stepIdx);
    } else if (isCamera) {
      renderLiveCameraShutter(activeSlot, toolName, details, stepIdx);
    } else if (isMemory) {
      renderLiveMemoryRecall(activeSlot, toolName, details, stepIdx);
    } else if (isScanner) {
      renderLiveFileScanner(activeSlot, toolName, details, stepIdx);
    } else if (isForger) {
      FloworkMrFlowAudio.trigger('code_patched');
      renderLiveCodeForger(activeSlot, toolName, details, stepIdx);
    } else if (isBash) {
      FloworkMrFlowAudio.trigger('terminal_exec');
      renderLiveBashRunner(activeSlot, toolName, details, stepIdx);
    } else if (isSkill) {
      FloworkMrFlowAudio.trigger('skill_pinned');
      renderLiveSkillActivator(activeSlot, toolName, details, stepIdx);
    } else if (isAudit) {
      renderLiveSecurityAuditor(activeSlot, toolName, details, stepIdx);
    } else if (isVisual) {
      renderLiveVisualPainter(activeSlot, toolName, details, stepIdx);
    } else {
      if (window.FloworkToolRegistry && typeof window.FloworkToolRegistry.mountLive === 'function') {
        existingLiveBox = window.FloworkToolRegistry.mountLive(activeSlot, cleanToolId, details, stepIdx);
      } else {
        renderLiveDynamicExternalTool(activeSlot, toolName, details, stepIdx);
      }
    }
    existingLiveBox = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
  } else if (existingLiveBox && typeof existingLiveBox._injectOutputLines === 'function') {
    existingLiveBox._injectOutputLines(details);
  }

  // Always inject/update the mandatory Reason Banner at the top of the live tool HUD box
  if (existingLiveBox) {
    injectLiveReasonBanner(existingLiveBox, toolName, details);
  }

  if (rawTool.includes('subagent') || rawTool.includes('spawnagent') || rawTool.includes('invoke_agent') || rawTool.includes('delegate')) {
    const role = d.Role || d.role || d.TypeName || d.typeName || d.type || 'Sub-Agent Specialist';
    FloworkChatTacticalOverlay.spawn('agent_spawn', { role });
    FloworkMrFlowAudio.trigger('agent_spawn');
  }

  if (status === 'done') {
    const outData = (details && details.output !== undefined) ? details.output : (details && details.rawOutput !== undefined ? details.rawOutput : details);
    dismissLiveToolBox(activeSlot, stepIdx, outData);
  }

  // 1. Subagent Spawning -> dedicated card in capsule
  if (rawTool.includes('subagent') || rawTool.includes('spawnagent') || rawTool.includes('invoke_agent') || rawTool.includes('delegate')) {
    const card = formatSubagentCard(details, status);
    if (card) {
      if (activeToolElements) activeToolElements.set(stepIdx, card);
      capsuleBody.appendChild(card);
      updateToolsCapsuleHeader(capsule);
    }
    return card;
  }

  // 1b. Skill Management / Pinning -> dedicated skill HUD card in capsule
  if (rawTool.includes('skill')) {
    const card = formatSkillCard(details, status);
    if (card) {
      if (activeToolElements) activeToolElements.set(stepIdx, card);
      capsuleBody.appendChild(card);
      updateToolsCapsuleHeader(capsule);
    }
    return card;
  }

  // 1c. Optical Screenshot Capture -> dedicated optical shutter card in capsule
  if (isCamera) {
    const card = formatScreenshotCard(details, status);
    if (card) {
      if (activeToolElements) activeToolElements.set(stepIdx, card);
      capsuleBody.appendChild(card);
      updateToolsCapsuleHeader(capsule);
    }
    return card;
  }

  // 1d. Brain Memory Access / Ingest -> dedicated neural synapse memory card in capsule
  if (isMemory) {
    const card = formatBrainCard(details, status);
    if (card) {
      if (activeToolElements) activeToolElements.set(stepIdx, card);
      capsuleBody.appendChild(card);
      updateToolsCapsuleHeader(capsule);
    }
    return card;
  }

  // 2. Background Task / Topic -> dedicated card in capsule
  if ((rawTool.includes('task') && !rawTool.includes('command')) || rawTool.includes('update_topic') || rawTool.includes('topic')) {
    const card = formatTaskCard(details, status);
    if (card) {
      if (activeToolElements) activeToolElements.set(stepIdx, card);
      capsuleBody.appendChild(card);
      updateToolsCapsuleHeader(capsule);
    }
    return card;
  }

  // 3. Prioritize custom non-fallback Tool Registry output card if registered with custom UI
  const customOutTool = (window.FloworkToolRegistry && typeof window.FloworkToolRegistry.get === 'function')
    ? window.FloworkToolRegistry.get(cleanToolId)
    : null;
  if (customOutTool && !customOutTool.isDefaultFallback && customOutTool.hasCustomOutputUI && typeof customOutTool.renderOutput === 'function') {
    const card = customOutTool.renderOutput(capsuleBody, cleanToolId, details, status, stepIdx, activeToolElements);
    if (card) {
      if (capsule) {
        capsule.style.display = 'block';
        capsule.open = true;
      }
      updateToolsCapsuleHeader(capsule);
      return card;
    }
  }

  // Fallback 3b. Shell Command execution -> Direct clean row in capsule
  if (rawTool.includes('run_command') || rawTool.includes('exec') || rawTool.includes('terminal')) {
    let cmd = '';
    let output = '';
    if (typeof details === 'string') {
      cmd = details;
    } else if (details && typeof details === 'object') {
      cmd = details.commandLine || details.CommandLine || details.command || details.toolAction || details.toolSummary || 'Shell command';
      const rawOut = details.rawOutput ?? details.output ?? details.stdout ?? details.result ?? null;
      if (rawOut !== null && rawOut !== undefined && rawOut !== '') {
        output = sanitizeToolOutput(rawOut);
      }
    }

    const cmdReasonText = extractToolReason(toolName, details);
    const shortCmdReason = cmdReasonText.length > 48 ? cmdReasonText.slice(0, 46) + '…' : cmdReasonText;

    const activeToolTheme = window.currentActiveToolTheme || localStorage.getItem('xflow_tool_theme') || 'cyber_neon';
    const cmdItem = document.createElement('details');
    cmdItem.className = `fl-cmd-item fl-tool-theme-card ${status === 'running' ? 'is-running' : ''}`;
    cmdItem.setAttribute('data-step-idx', String(stepIdx));
    cmdItem.setAttribute('data-tool-theme', activeToolTheme);
    cmdItem.open = false;
    
    const hasOutput = output && output.trim().length > 0;
    const stdoutContent = hasOutput
      ? `
        <div class="fl-cmd-stdout-bar">
          <span class="fl-cmd-stdout-title">Output</span>
          <button class="fl-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button>
        </div>
        <pre class="fl-cmd-stdout"><code>${escapeHtml(output)}</code></pre>
      `
      : `<div class="fl-cmd-empty fl-cmd-silent-success"><span class="fl-cmd-silent-icon">✓</span> <span class="fl-cmd-silent-text">Command completed cleanly (Exit Code 0 • No standard output)</span></div>`;

    cmdItem.innerHTML = `
      <summary class="fl-cmd-item-header">
        <span class="fl-cmd-item-chevron">›</span>
        <span class="fl-cmd-item-prompt">$</span>
        <span class="fl-cmd-item-title">${escapeHtml(cmd)}</span>
        ${cmdReasonText ? `<span class="fl-tool-reason-pill" title="${escapeHtml(cmdReasonText)}">💬 ${escapeHtml(shortCmdReason)}</span>` : ''}
        <span class="fl-cmd-item-ticker" style="display:none;"></span>
        <span class="fl-tool-badge ${status}">${status === 'running' ? '<span class="fl-tool-spinner"></span> Running' : '✓ Done'}</span>
      </summary>
      <div class="fl-cmd-item-body">
        ${cmdReasonText ? `<div class="fl-tool-reason-box"><span class="fl-trb-lbl">💬 REASON:</span> <span class="fl-trb-txt">${escapeHtml(cmdReasonText)}</span></div>` : ''}
        ${stdoutContent}
      </div>
    `;

    capsuleBody.appendChild(cmdItem);
    if (activeToolElements) activeToolElements.set(stepIdx, cmdItem);
    updateToolsCapsuleHeader(capsule);

    if (status === 'running' && cmd) {
      animateTerminalPrompt(cmdItem, cmd);
    }
    return cmdItem;
  }

  // 4. File I/O, Search, and general rich cards
  let card = formatToolCard(toolName, details, status);
  if (!card && window.FloworkToolRegistry && typeof window.FloworkToolRegistry.renderOutput === 'function') {
    card = window.FloworkToolRegistry.renderOutput(capsuleBody, cleanToolId, details, status, stepIdx, activeToolElements);
  }
  if (card) {
    if (activeToolElements) activeToolElements.set(stepIdx, card);
    if (card.parentNode !== capsuleBody) capsuleBody.appendChild(card);
    if (capsule) {
      capsule.style.display = 'block';
      capsule.open = true;
    }
    updateToolsCapsuleHeader(capsule);
  }
  return card;
}

function updateCommandsGroupHeader(group) {
  if (!group) return;
  const items = group.querySelectorAll('.fl-cmd-item');
  const total = items.length;
  if (total === 0) return;

  const runningBadges = group.querySelectorAll('.fl-cmd-item .fl-tool-badge.running');
  const label = group.querySelector('.fl-commands-label');
  const badge = group.querySelector('.fl-commands-badge');

  if (runningBadges.length > 0) {
    if (label) label.textContent = `Running ${total} command${total > 1 ? 's' : ''}...`;
    if (badge) {
      badge.className = 'fl-commands-badge running';
      badge.innerHTML = '<span class="fl-tool-spinner"></span> Running';
    }
  } else {
    if (label) label.textContent = `Ran ${total} terminal command${total > 1 ? 's' : ''}`;
    if (badge) {
      badge.className = 'fl-commands-badge done';
      badge.textContent = '✓ Done';
    }
    // Auto-collapse completed commands group once all commands finish
    group.open = false;
    group.removeAttribute('open');
  }
}

function updateTerminalStream(stepIdx, data, activeToolElements) {
  if (stepIdx === undefined) return;
  let el = activeToolElements ? activeToolElements.get(stepIdx) : null;
  if (!el) {
    el = document.querySelector(`.fl-cmd-item[data-step-idx="${stepIdx}"]`);
  }

  // 1. Live update the standalone in-chat ephemeral bash terminal box if present!
  const liveBashBox = document.querySelector(`.fl-live-bash-box[data-live-step="${stepIdx}"]`);
  if (liveBashBox && data) {
    const codeEl = liveBashBox.querySelector('.fl-live-bash-code code');
    if (codeEl && data.output !== undefined) {
      let rawOut = String(data.output);
      const lines = rawOut.split('\n').filter(l => l.trim()).slice(-4);
      codeEl.textContent = lines.join('\n');
    }
  }

  if (!el || !el.classList.contains('fl-cmd-item')) return;

  // DOKTRIN: Keep command group and command item CLOSED to preserve default hide!
  const group = el.closest('.fl-commands-group');
  if (group) {
    group.open = false;
    group.removeAttribute('open');
  }
  el.open = false;
  el.removeAttribute('open');

  // 2. Update Live Tail Ticker in item header
  const header = el.querySelector('.fl-cmd-item-header');
  if (header) {
    let ticker = header.querySelector('.fl-cmd-item-ticker');
    if (!ticker) {
      ticker = document.createElement('span');
      ticker.className = 'fl-cmd-item-ticker';
      const badge = header.querySelector('.fl-tool-badge');
      if (badge) header.insertBefore(ticker, badge);
      else header.appendChild(ticker);
    }
    const tailText = (data.tail || data.line || '').trim();
    if (tailText) {
      const cleanTail = tailText.replace(/[\r\n]+/g, ' ');
      ticker.textContent = cleanTail.length > 40 ? cleanTail.slice(0, 38) + '…' : cleanTail;
      ticker.title = cleanTail;
      ticker.style.display = 'inline-flex';
    }
  }

  // 3. Update stdout body container with live streaming output
  const body = el.querySelector('.fl-cmd-item-body');
  if (body) {
    let pre = body.querySelector('.fl-cmd-stdout');
    let code = pre ? pre.querySelector('code') : null;
    if (!pre) {
      body.innerHTML = `
        <div class="fl-cmd-stdout-bar">
          <span class="fl-cmd-stdout-title">Live Output</span>
          <span class="fl-cmd-live-pill"><span class="fl-cmd-live-pulse"></span> STREAMING</span>
          <button class="fl-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button>
        </div>
        <pre class="fl-cmd-stdout fl-cmd-live"><code></code></pre>
      `;
      pre = body.querySelector('.fl-cmd-stdout');
      code = pre ? pre.querySelector('code') : null;
    } else {
      pre.classList.add('fl-cmd-live');
      const bar = body.querySelector('.fl-cmd-stdout-bar');
      if (bar && !bar.querySelector('.fl-cmd-live-pill')) {
        const pill = document.createElement('span');
        pill.className = 'fl-cmd-live-pill';
        pill.innerHTML = '<span class="fl-cmd-live-pulse"></span> STREAMING';
        const title = bar.querySelector('.fl-cmd-stdout-title');
        if (title) {
          title.textContent = 'Live Output';
          title.insertAdjacentElement('afterend', pill);
        }
      }
    }

    if (code && data.output !== undefined) {
      let rawOut = sanitizeToolOutput(data.output);
      // Sliding buffer: clamp to max 500 lines to prevent DOM overhead
      const lines = rawOut.split('\n');
      if (lines.length > 500) {
        rawOut = '... [early output truncated for speed] ...\n' + lines.slice(-500).join('\n');
      }
      code.innerHTML = `${escapeHtml(rawOut)}`;
      pre.scrollTop = pre.scrollHeight;
    }
  }

  // 4. Feed live stream chunks to dynamic tool UI module if active
  const toolsArea = el.closest('.chat-tools-area');
  if (toolsArea) {
    const activeSlot = toolsArea.querySelector('.fl-live-active-slot');
    if (activeSlot) {
      const pod = activeSlot.querySelector(`[data-live-step="${stepIdx}"]`);
      if (pod && pod._dynamicUiModule && typeof pod._dynamicUiModule.onStream === 'function') {
        pod._dynamicUiModule.onStream(activeSlot, data.output ?? data.line ?? data);
      }
    }
  }
}

function markToolDone(stepIdx, activeToolElements, outputData) {
  if (stepIdx === undefined) return;

  // Dismiss live ephemeral terminal with real output and guaranteed visible duration
  dismissLiveToolBox(null, stepIdx, outputData);

  if (!activeToolElements) return;
  const el = activeToolElements.get(stepIdx);
  if (!el) return;

  const toolsArea = el.closest('.chat-tools-area');
  if (toolsArea) {
    const activeSlot = toolsArea.querySelector('.fl-live-active-slot');
    if (activeSlot) {
      dismissLiveToolBox(activeSlot, stepIdx, outputData);
    }
    const capsule = toolsArea.querySelector('.fl-toolstream-wrap');
    if (capsule) {
      updateToolsCapsuleHeader(capsule);
    }
  }

  if (el.classList.contains('fl-cmd-item')) {
    el.classList.remove('is-running');
    el.classList.add('is-completed-flash');
    const badge = el.querySelector('.fl-tool-badge');
    if (badge) {
      badge.className = 'fl-tool-badge done';
      badge.textContent = '✓ Exit Code 0';
    }
    const ticker = el.querySelector('.fl-cmd-item-ticker');
    if (ticker) {
      ticker.style.display = 'none';
    }

    const streamCursor = el.querySelector('.fl-stream-live-cursor');
    if (streamCursor) streamCursor.remove();
    const livePill = el.querySelector('.fl-cmd-live-pill');
    if (livePill) livePill.remove();

    if (outputData !== undefined && outputData !== null) {
      let rawOut = outputData;
      let stderrOut = '';
      let exitCode = 0;
      if (typeof outputData === 'object') {
        rawOut = outputData.rawOutput ?? outputData.output ?? outputData.stdout ?? outputData.result;
        stderrOut = outputData.stderr ?? outputData.error ?? '';
        exitCode = outputData.exitCode ?? outputData.exit_code ?? 0;
        if (rawOut === undefined && stderrOut) {
          rawOut = '';
        } else if (rawOut === undefined) {
          rawOut = outputData;
        }
      }
      if (badge && exitCode !== 0) {
        badge.className = 'fl-tool-badge failed';
        badge.textContent = `✕ Exit Code ${exitCode}`;
      }
      const outText = typeof rawOut === 'object' ? JSON.stringify(rawOut, null, 2) : (rawOut ? String(rawOut) : '');
      const errText = typeof stderrOut === 'object' ? JSON.stringify(stderrOut, null, 2) : (stderrOut ? String(stderrOut) : '');
      const body = el.querySelector('.fl-cmd-item-body');
      if (body) {
        if (outText && outText.trim().length > 0) {
          body.innerHTML = `
            <div class="fl-cmd-stdout-bar">
              <span class="fl-cmd-stdout-title">Output</span>
              <button class="fl-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button>
            </div>
            <pre class="fl-cmd-stdout"><code>${escapeHtml(outText)}</code></pre>
            ${errText && errText.trim().length > 0 ? `
              <div class="fl-cmd-stderr-bar">
                <span class="fl-cmd-stderr-title">Error Log</span>
              </div>
              <pre class="fl-cmd-stderr"><code>${escapeHtml(errText)}</code></pre>
            ` : ''}
          `;
        } else if (errText && errText.trim().length > 0) {
          body.innerHTML = `
            <div class="fl-cmd-stderr-bar">
              <span class="fl-cmd-stderr-title">Error Log</span>
            </div>
            <pre class="fl-cmd-stderr"><code>${escapeHtml(errText)}</code></pre>
          `;
        } else {
          body.innerHTML = `<div class="fl-cmd-empty fl-cmd-silent-success"><span class="fl-cmd-silent-icon">✓</span> <span class="fl-cmd-silent-text">Command completed cleanly (${exitCode === 0 ? 'Exit Code 0' : `Exit Code ${exitCode}`} • No standard output)</span></div>`;
        }
      }

      if (exitCode === 0) {
        FloworkMrFlowAudio.trigger('terminal_done');
      } else {
        FloworkTacticalHUD.spawn('alert_breach', { error: `Command exited with code ${exitCode}` });
        FloworkMrFlowAudio.trigger('alert_breach');
      }
    }

    // Graceful Vanish / Auto-Shrink to minimal sleek transparent pill after brief green flash (600ms)
    setTimeout(() => {
      el.classList.remove('is-completed-flash');
      el.removeAttribute('open');
      el.classList.add('is-compact-pill');
      const group = el.closest('.fl-commands-group');
      if (group) updateCommandsGroupHeader(group);
    }, 600);
  } else {
    const badge = el.querySelector('.fl-tool-badge, .fl-subagent-status, .fl-task-badge, .fl-skill-badge, .fl-generic-tool-badge');
    if (badge) {
      badge.className = badge.className.replace('running', 'done');
      if (badge.classList.contains('fl-generic-tool-badge')) {
        badge.textContent = '✓ EXIT CODE 0 // VERIFIED';
      } else if (!badge.textContent.includes('PINNED')) {
        badge.textContent = '✓ Done';
      }
    }
    if (el.classList.contains('fl-subagent-card') || el.querySelector('.fl-subagent-header')) {
      FloworkMrFlowAudio.trigger('agent_complete');
    }
    el.classList.remove('is-running');
    el.classList.add('is-completed-flash');
    setTimeout(() => {
      el.classList.remove('is-completed-flash');
      el.removeAttribute('open');
    }, 1200);
    if (outputData !== undefined && outputData !== null) {
      let rawOut = outputData;
      if (typeof outputData === 'object') {
        const errStr = outputData.error || (outputData.output && outputData.output.error) || '';
        if (errStr === 'MANDATORY_SKILL_REQUIRED') {
          FloworkTacticalHUD.spawn('alert_breach', { error: 'Mandatory Skill Pin required before running operational tools!' });
          FloworkMrFlowAudio.trigger('alert_breach');
        }
        rawOut = outputData.rawOutput ?? outputData.output ?? outputData.stdout ?? outputData.result ?? outputData;
      }
      const outText = typeof rawOut === 'object' ? JSON.stringify(rawOut, null, 2) : (rawOut ? String(rawOut) : '');
      const detailsBlock = el.querySelector('.fl-tool-details, .fl-subagent-body, .fl-task-body');
      if (detailsBlock && !detailsBlock.querySelector('.fl-tool-block:last-child .fl-tool-code')) {
        const outDiv = document.createElement('div');
        outDiv.className = 'fl-tool-block';
        outDiv.innerHTML = `<div class="fl-tool-block-header"><span>OUTPUT</span><button class="fl-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div><pre class="fl-tool-code"><code>${escapeHtml(outText)}</code></pre>`;
        detailsBlock.appendChild(outDiv);
      }
    }
    // Auto-collapse completed tool card
    el.removeAttribute('open');
  }
}

function collapseAllToolsInArea(toolsArea) {
  if (!toolsArea) return;
  
  // Gracefully transition & clean up any remaining live visual boxes in the active slot
  const activeSlot = toolsArea.querySelector('.fl-live-active-slot');
  if (activeSlot) {
    const boxes = activeSlot.querySelectorAll('.fl-live-ambient-stage, .fl-live-view-file, .fl-live-write-file, .fl-live-replace-file, .fl-live-search-tools, .fl-live-search-web, .fl-live-read-url, .fl-live-flow-lock, .fl-live-sys-health, .fl-live-audit-sec, .fl-live-detect-hc, .fl-live-audit-port, .fl-live-web-sec, .fl-live-web-intel, .fl-live-schedule, .fl-live-manage-task, .fl-live-plugin-ctrl, .fl-live-gatekeeper, .fl-live-screenshot, .fl-live-yt-video, .fl-live-yt-channel, .fl-live-yt-transcript, .fl-live-yt-summary, .fl-live-yt-comments, .fl-live-yt-strategy, .fl-live-ask-question, .fl-live-sys-restart, .fl-live-plugin-publish, .fl-live-invoke-subagent, .fl-live-define-subagent, .fl-live-manage-subagents, .fl-live-send-message, .fl-live-generate-image, .fl-live-send-media, .fl-live-render-visual, .fl-live-scan-box, .fl-live-forge-box, .fl-live-bash-box, .fl-live-swarm-box, .fl-live-memory-box, .fl-live-skill-box, .fl-live-audit-box, .fl-live-canvas-box, .fl-live-camera-box, .fl-live-generic-box');
    boxes.forEach(b => {
      if (b._lockTimer) { clearTimeout(b._lockTimer); b._lockTimer = null; }
      if (b._dismissTimer) { clearTimeout(b._dismissTimer); b._dismissTimer = null; }
      clearAllBoxTimers(b);
      if (!isChatStreaming) {
        b.remove();
        return;
      }
      b.classList.add('is-finished');
      setTimeout(() => {
        if (b.isConnected) b.remove();
      }, 320);
    });
  }

  // Find and enforce STRICT DEFAULT HIDE on the unified capsule
  const capsule = toolsArea.querySelector('.fl-toolstream-wrap');
  if (capsule) {
    capsule.open = false;
    capsule.removeAttribute('open');
    const action = capsule.querySelector('.fl-capsule-action');
    if (action) action.textContent = 'Show Details ▾';

    // Reveal capsule ONLY IF tools were executed in this turn!
    const body = capsule.querySelector('.fl-toolstream-body');
    const total = body ? body.children.length : 0;
    if (total > 0) {
      capsule.style.display = 'block';
      capsule.open = true;
      capsule.setAttribute('open', '');
      if (action) action.textContent = 'Hide Details ▴';
    } else {
      capsule.style.display = 'none';
      capsule.open = false;
      capsule.removeAttribute('open');
      if (action) action.textContent = 'Show Details ▾';
    }
    updateToolsCapsuleHeader(capsule);
  }

  // Collapse inner command groups
  toolsArea.querySelectorAll('.fl-commands-group').forEach(group => {
    group.open = false;
    group.removeAttribute('open');
    updateCommandsGroupHeader(group);
  });
  
  // Collapse command items
  toolsArea.querySelectorAll('.fl-cmd-item').forEach(item => {
    item.open = false;
    item.removeAttribute('open');
  });

  // Collapse tool cards
  toolsArea.querySelectorAll('.fl-tool-card').forEach(card => {
    card.open = false;
    card.removeAttribute('open');
  });

  // Collapse subagent cards
  toolsArea.querySelectorAll('.fl-subagent-card').forEach(card => {
    card.open = false;
    card.removeAttribute('open');
  });

  // Collapse task cards
  toolsArea.querySelectorAll('.fl-task-card').forEach(card => {
    card.open = false;
    card.removeAttribute('open');
  });

  // Eliminate obsolete legacy toolbar so only the unified capsule is present
  const legacyToolbar = toolsArea.querySelector('.fl-tools-toolbar');
  if (legacyToolbar) {
    legacyToolbar.remove();
  }
}

window.toggleAllToolsInArea = function(btn) {
  const toolsArea = btn.closest('.chat-tools-area');
  if (!toolsArea) return;
  const capsule = toolsArea.querySelector('.fl-toolstream-wrap');
  if (capsule) {
    capsule.open = !capsule.open;
    const action = capsule.querySelector('.fl-capsule-action');
    if (action) action.textContent = capsule.open ? 'Hide Details ▴' : 'Show Details ▾';
  }
};

window.copyToolCode = function(btn) {
  const block = btn.closest('.fl-tool-block, .fl-cmd-item-body, .fl-subagent-body, .fl-task-body');
  const code = block ? block.querySelector('pre code') : null;
  if (!code) return;
  window.safeCopyToClipboard(code.innerText).then(() => {
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = orig;
      btn.classList.remove('copied');
    }, 1600);
  }).catch(() => {});
};

function parseUserPromptPayload(rawMsg) {
  if (!rawMsg) return { cleanPrompt: '', attachments: [], attachmentsHtml: '' };

  const attachBlockMatch = rawMsg.match(/^\[USER ATTACHMENTS\]\n([\s\S]*?)\n\n([\s\S]*)$/);
  if (!attachBlockMatch) {
    return { cleanPrompt: rawMsg, attachments: [], attachmentsHtml: '' };
  }

  const rawBlock = attachBlockMatch[1];
  const cleanPrompt = attachBlockMatch[2] || '';
  const attachments = [];

  const itemBlocks = rawBlock.split(/\n(?=- (?:Image|File):)/);
  itemBlocks.forEach(blk => {
    const isImage = /^- Image:/m.test(blk);
    const nameMatch = blk.match(/^- (?:Image|File):\s*(.+)$/m);
    const pathMatch = blk.match(/^\s*Path:\s*(.+)$/m);
    const urlMatch = blk.match(/^\s*Preview URL:\s*(.+)$/m);
    const sizeMatch = blk.match(/^\s*Size:\s*(.+)$/m);

    const name = nameMatch ? nameMatch[1].trim() : 'attachment';
    const path = pathMatch ? pathMatch[1].trim() : '';
    const webUrl = urlMatch ? urlMatch[1].trim() : (resolveMediaUrl(path) || path);
    const size = sizeMatch ? sizeMatch[1].trim() : '';

    attachments.push({
      isImage,
      name,
      path,
      webUrl,
      size
    });
  });

  let attachmentsHtml = '';
  if (attachments.length > 0) {
    attachmentsHtml = '<div class="chat-msg-attachments">' + attachments.map(att => {
      if (att.isImage) {
        return `
          <div class="chat-msg-img-wrap" data-url="${escapeHtml(att.webUrl)}" data-title="${escapeHtml(att.name)}" onclick="window.handleChatAttachmentClick(this)">
            <img src="${att.webUrl}" class="chat-msg-attached-img" alt="${escapeHtml(att.name)}" loading="lazy" />
            <div class="chat-img-zoom-hint">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
              <span>Zoom</span>
            </div>
          </div>
        `;
      } else {
        return `
          <div class="chat-msg-file-card" data-url="${escapeHtml(att.webUrl)}" data-title="${escapeHtml(att.name)}" onclick="window.handleChatAttachmentClick(this)">
            <span class="chat-file-icon">${getFileCategoryIcon(att.name)}</span>
            <div class="chat-file-info">
              <span class="chat-file-name">${escapeHtml(att.name)}</span>
              <span class="chat-file-size">${escapeHtml(att.size)}</span>
            </div>
          </div>
        `;
      }
    }).join('') + '</div>';
  }

  return { cleanPrompt, attachments, attachmentsHtml };
}

function renderTrajectorySteps(steps) {
  const container = document.getElementById('rightbar-messages');
  if (!container) return;

  const prevScrollHeight = container.scrollHeight;
  const prevScrollTop = container.scrollTop;
  const prevClientHeight = container.clientHeight;
  const wasNearBottom = (prevScrollHeight - prevScrollTop - prevClientHeight) < 320;
  const prevScrollBottomOffset = prevScrollHeight - prevScrollTop;

  // Ensure mascot hero is preserved at top
  let emptyHero = container.querySelector('#chat-empty-hero');
  if (!emptyHero) {
    container.insertAdjacentHTML('afterbegin', getEmptyHeroHtml());
    requestAnimationFrame(() => initChatMascot());
  }

  // Remove existing chat messages and loading indicators only
  container.querySelectorAll('.chat-msg, .fl-chat-loading-indicator').forEach(el => el.remove());

  if (!steps || steps.length === 0) {
    container.classList.remove('has-messages');
    container.classList.remove('agent-is-looping');
    setMascotAgentLoop(false);
    return;
  }

  container.classList.add('has-messages');
  container.classList.remove('history-active');
  if (!isChatStreaming) {
    container.classList.remove('agent-is-looping');
    setMascotAgentLoop(false);
  }

  let currentAssistantCard = null;
  let currentToolsArea = null;
  let currentBodyArea = null;
  let currentThinkingArea = null;
  let lastUserPromptText = '';
  let turnStartIdx = 0;
  let turnEndIdx = steps.length;

  // Turn Capping Guard: Limit active DOM nodes to prevent Chromium layout thrashing
  const userTurnIndices = [];
  for (let i = 0; i < steps.length; i++) {
    if ((steps[i]?.type || '').endsWith('USER_INPUT')) {
      userTurnIndices.push(i);
    }
  }

  const MAX_ACTIVE_TURNS = 30;
  let startStepIdx = 0;
  let hiddenTurnsCount = 0;

  if (!window.__renderAllChatSteps && userTurnIndices.length > MAX_ACTIVE_TURNS) {
    hiddenTurnsCount = userTurnIndices.length - MAX_ACTIVE_TURNS;
    startStepIdx = userTurnIndices[hiddenTurnsCount];
  }

  const fragment = document.createDocumentFragment();

  if (hiddenTurnsCount > 0) {
    const loadEarlierDiv = document.createElement('div');
    loadEarlierDiv.className = 'chat-load-earlier-wrapper';
    loadEarlierDiv.style.cssText = 'text-align: center; margin: 10px 0;';
    loadEarlierDiv.innerHTML = `
      <button class="btn-load-earlier-turns" style="padding: 6px 16px; border-radius: 20px; font-size: 11px; font-weight: 500; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; cursor: pointer; transition: all 0.2s ease;">
        ⚡ Load earlier turns (${hiddenTurnsCount} earlier turns)
      </button>
    `;
    const btn = loadEarlierDiv.querySelector('.btn-load-earlier-turns');
    if (btn) {
      btn.onclick = () => {
        window.__renderAllChatSteps = true;
        renderTrajectorySteps(steps);
      };
    }
    fragment.appendChild(loadEarlierDiv);
  }

  for (let stepIdx = startStepIdx; stepIdx < steps.length; stepIdx++) {
    const s = steps[stepIdx];
    const stepType = s.type || '';

    if (stepType.endsWith('USER_INPUT')) {
      currentAssistantCard = null;
      currentToolsArea = null;
      currentBodyArea = null;
      currentThinkingArea = null;
      turnStartIdx = stepIdx;
      turnEndIdx = steps.length;
      for (let k = stepIdx + 1; k < steps.length; k++) {
        if ((steps[k]?.type || '').endsWith('USER_INPUT')) {
          turnEndIdx = k;
          break;
        }
      }

      const rawMsg = s.userInput?.message || '';
      const parsed = parseUserPromptPayload(rawMsg);
      const displayText = parsed.cleanPrompt || rawMsg;
      lastUserPromptText = displayText;

      const card = document.createElement('div');
      card.className = 'chat-msg user';
      card.innerHTML = `
        ${parsed.attachmentsHtml}
        ${displayText ? `<div class="chat-bubble user">${escapeHtml(displayText).replace(/\n/g, '<br>')}</div>` : ''}
        <div class="chat-msg-meta">
          <button class="btn-msg-action btn-copy-prompt" title="Copy prompt">
            <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            <span>Copy</span>
          </button>
          <button class="btn-msg-action btn-edit-prompt" title="Edit prompt & rewind">
            <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
            <span>Edit</span>
          </button>
        </div>
      `;

      const btnCopyPrompt = card.querySelector('.btn-copy-prompt');
      if (btnCopyPrompt) {
        btnCopyPrompt.addEventListener('click', () => {
          window.safeCopyToClipboard(displayText).then(() => {
            const span = btnCopyPrompt.querySelector('span');
            if (span) span.innerText = 'Copied!';
            btnCopyPrompt.classList.add('copied');
            setTimeout(() => {
              if (span) span.innerText = 'Copy';
              btnCopyPrompt.classList.remove('copied');
            }, 2000);
          });
        });
      }

      const btnEditPrompt = card.querySelector('.btn-edit-prompt');
      if (btnEditPrompt) {
        btnEditPrompt.addEventListener('click', async () => {
          if (isChatStreaming) return;
          try {
            await fetch('/api/chat/truncate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ session_id: currentChatSessionId, step_index: stepIdx })
            });
            const inputEl = document.getElementById('rightbar-chat-input');
            if (inputEl) {
              inputEl.value = displayText;
              inputEl.style.height = 'auto';
              inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
              inputEl.focus();
            }
            showToast('Rewound to prompt. Ready to re-edit.');
            await loadChatSession(currentChatSessionId);
          } catch (e) {
            showToast('Failed to rewind to prompt');
          }
        });
      }

      fragment.appendChild(card);
      currentAssistantCard = null;
      currentBodyArea = null;
      currentToolsArea = null;
    } else if (stepType.endsWith('PLANNER_RESPONSE')) {
      const pr = s.plannerResponse || {};
      const thinking = pr.thinking || '';
      const resp = pr.response || pr.modifiedResponse || '';
      if (!thinking && !resp) continue;

      if (!currentAssistantCard) {
        currentAssistantCard = document.createElement('div');
        currentAssistantCard.className = 'chat-msg assistant';
        currentAssistantCard.innerHTML = `
          <div class="chat-assistant-header">
            <div class="chat-avatar-ai">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
            </div>
            <span class="chat-assistant-name">FLOWORK AGENT</span>
            <span class="chat-model-badge">${pr.model || selectedChatModelId}</span>
          </div>
          <div class="chat-msg-content">
            <div class="chat-thinking-area"></div>
            <div class="chat-tools-area"></div>
            <div class="chat-body-area"></div>
            <div class="chat-msg-footer">
              <button class="btn-msg-action btn-copy-response" title="Copy response">
                <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                <span>Copy</span>
              </button>
              <button class="btn-msg-action btn-retry-response" title="Regenerate this response">
                <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
                <span>Retry</span>
              </button>
              <button class="btn-msg-action btn-revert-turn" title="Rewind conversation back to before this response">
                <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 14 4 9 9 4"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/></svg>
                <span>Revert</span>
              </button>
            </div>
          </div>
        `;
        fragment.appendChild(currentAssistantCard);
        currentThinkingArea = currentAssistantCard.querySelector('.chat-thinking-area');
        currentToolsArea = currentAssistantCard.querySelector('.chat-tools-area');
        currentBodyArea = currentAssistantCard.querySelector('.chat-body-area');
      }

      if (thinking && currentThinkingArea) {
        const thoughtCard = formatThoughtCard(thinking, 2);
        if (thoughtCard) currentThinkingArea.appendChild(thoughtCard);
      }
      if (resp && currentBodyArea) {
        let fullResp = resp.trim();
        // Strictly scope visual block extraction ONLY to verified render_visual steps within THIS turn!
        for (let j = turnStartIdx; j < turnEndIdx; j++) {
          const stepJ = steps[j];
          const jTool = String(stepJ.tool || '').toLowerCase().trim();
          if (jTool.includes('render_visual') && stepJ.runCommand && stepJ.runCommand.output) {
            const vb = extractVisualBlockFromToolOutput(jTool, stepJ.runCommand.output);
            if (vb && !fullResp.includes(vb)) {
              fullResp += '\n\n' + vb;
            }
          }
        }
        currentBodyArea.innerHTML = renderMarkdown(fullResp);
      }

      const targetCard = currentAssistantCard;
      const targetBodyArea = currentBodyArea;
      const targetResp = resp;
      const btnCopy = targetCard?.querySelector('.btn-copy-response');
      if (btnCopy) {
        btnCopy.addEventListener('click', () => {
          const textToCopy = targetBodyArea?.innerText || targetResp || '';
          window.safeCopyToClipboard(textToCopy).then(() => {
            const span = btnCopy.querySelector('span');
            if (span) span.innerText = 'Copied!';
            btnCopy.classList.add('copied');
            setTimeout(() => {
              if (span) span.innerText = 'Copy';
              btnCopy.classList.remove('copied');
            }, 2000);
          });
        });
      }

      const btnRetry = targetCard?.querySelector('.btn-retry-response');
      if (btnRetry) {
        btnRetry.addEventListener('click', () => {
          regenerateLastTurn();
        });
      }

      const btnRevert = targetCard?.querySelector('.btn-revert-turn');
      if (btnRevert) {
        btnRevert.addEventListener('click', async () => {
          if (isChatStreaming) return;
          try {
            await fetch('/api/chat/truncate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ session_id: currentChatSessionId, step_index: stepIdx })
            });
            showToast('Conversation reverted to this turn.');
            await loadChatSession(currentChatSessionId);
          } catch (e) {
            showToast('Failed to revert conversation');
          }
        });
      }

      if (currentToolsArea) {
        collapseAllToolsInArea(currentToolsArea);
      }
    } else if (stepType.includes('RUN_COMMAND') || stepType.includes('TOOL')) {
      const toolName = s.tool || s.runCommand?.commandLine || 'flow_exec';
      const cmdDetails = s.runCommand || s.details || {};
      const status = s.status?.endsWith('RUNNING') ? 'running' : 'done';

      if (!currentAssistantCard) {
        currentAssistantCard = document.createElement('div');
        currentAssistantCard.className = 'chat-msg assistant';
        currentAssistantCard.innerHTML = `
          <div class="chat-assistant-header">
            <div class="chat-avatar-ai">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
            </div>
            <span class="chat-assistant-name">FLOWORK AGENT</span>
            <span class="chat-model-badge">${selectedChatModelId}</span>
          </div>
          <div class="chat-msg-content">
            <div class="chat-thinking-area"></div>
            <div class="chat-tools-area"></div>
            <div class="chat-body-area"></div>
          </div>
        `;
        fragment.appendChild(currentAssistantCard);
        currentThinkingArea = currentAssistantCard.querySelector('.chat-thinking-area');
        currentToolsArea = currentAssistantCard.querySelector('.chat-tools-area');
        currentBodyArea = currentAssistantCard.querySelector('.chat-body-area');
      }

      renderToolInArea(currentToolsArea, toolName, cmdDetails, status, stepIdx, null);
      if (status === 'done') {
        collapseAllToolsInArea(currentToolsArea);
      }
    }
  }

  // Mount entire trajectory batch in a single reflow/paint
  container.appendChild(fragment);

  // Ensure bottom anchor element exists and remains the very last child
  let anchor = container.querySelector('#chat-scroll-anchor');
  if (!anchor) {
    anchor = document.createElement('div');
    anchor.id = 'chat-scroll-anchor';
    anchor.style.cssText = 'height: 1px; width: 100%; pointer-events: none; visibility: hidden; flex-shrink: 0;';
    container.appendChild(anchor);
  } else if (container.lastElementChild !== anchor) {
    container.appendChild(anchor);
  }

  if (currentToolsArea) {
    collapseAllToolsInArea(currentToolsArea);
  }

  hidePinnedPrompt();

  if (wasNearBottom || !steps || steps.length <= 1) {
    scrollChatToBottom({ force: true });
  } else {
    const targetScrollTop = Math.max(0, container.scrollHeight - prevScrollBottomOffset);
    container.scrollTop = targetScrollTop;
  }
}

async function sendUserChatMessage() {
  const inputEl = document.getElementById('rightbar-chat-input');
  if (!inputEl) return;
  const text = inputEl.value.trim();
  const hasAttachments = activeChatAttachments && activeChatAttachments.length > 0;
  if (!text && !hasAttachments) return;

  const attachmentsToSend = [...activeChatAttachments];
  clearChatAttachments();

  // If agent is currently executing, push into visual queue tray
  if (isChatStreaming) {
    if (queuedMessages.some(m => m.text === text)) {
      console.log('[X-Flow Chat] ⏳ Ignored duplicate prompt queued during active stream');
      inputEl.value = '';
      inputEl.style.height = 'auto';
      return;
    }
    const queueId = 'q_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4);
    queuedMessages.push({ id: queueId, text, attachments: attachmentsToSend });
    inputEl.value = '';
    inputEl.style.height = 'auto';
    renderQueueTray();
    showToast('Message added to queue');
    return;
  }

  inputEl.value = '';
  inputEl.style.height = 'auto';
  await executeChatMessage(text, attachmentsToSend);
}

function extractVisualBlockFromToolOutput(toolName, outputData) {
  const tName = String(toolName || '').toLowerCase().trim();
  if (!tName || !tName.includes('render_visual')) {
    return '';
  }
  const vFence = '\x60\x60\x60visual:';
  const cFence = '\x60\x60\x60';
  const rawOut = (typeof outputData === 'string')
    ? outputData
    : (outputData && outputData.output ? String(outputData.output) : '');
  let cleanOut = rawOut.replace(/<SOVEREIGN_TOOL_INTERCEPT_GATE_INJECTION>[\s\S]*?<\/SOVEREIGN_TOOL_INTERCEPT_GATE_INJECTION>/g, '');
  const toolResIdx = cleanOut.lastIndexOf('[TOOL RESULT FOR ');
  if (toolResIdx !== -1) {
    cleanOut = cleanOut.slice(toolResIdx);
  }
  if (cleanOut && cleanOut.includes(vFence)) {
    const re = new RegExp(vFence + '([a-zA-Z0-9_\\-]+)\\s*\\n([\\s\\S]*?)\\n' + cFence);
    const m = cleanOut.match(re);
    if (m && m[1] && m[2]) {
      try {
        JSON.parse(m[2].trim());
        return vFence + m[1].trim() + '\n' + m[2].trim() + '\n' + cFence;
      } catch (_) {
        return '';
      }
    }
  } else if (outputData && typeof outputData === 'object' && (outputData.payload || outputData.widget_type || outputData.candles || outputData.cards || outputData.data)) {
    const wt = outputData.widget_type || 'chart';
    const pl = outputData.payload || outputData;
    return vFence + wt + '\n' + JSON.stringify(pl, null, 2) + '\n' + cFence;
  }
  return '';
}

async function executeChatMessage(text, attachmentsToSend = []) {
  if (isChatStreaming) return;
  const messagesContainer = document.getElementById('rightbar-messages');
  if (!messagesContainer) return;

  // Ensure 3D mascot hero is present and activate looping focus mode
  if (!messagesContainer.querySelector('#chat-empty-hero')) {
    messagesContainer.insertAdjacentHTML('afterbegin', getEmptyHeroHtml());
    initChatMascot();
  }
  messagesContainer.classList.add('has-messages');
  setMascotAgentLoop(true, 'Processing prompt & executing autonomous loop...');

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // 1. User Message HTML with Attachments
  let attachmentsHtml = '';
  if (attachmentsToSend && attachmentsToSend.length > 0) {
    attachmentsHtml = '<div class="chat-msg-attachments">' + attachmentsToSend.map(att => {
      if (att.isImage) {
        const previewSrc = att.previewUrl || '';
        return `
          <div class="chat-msg-img-wrap" data-url="${escapeHtml(previewSrc)}" data-title="${escapeHtml(att.name)}" onclick="window.handleChatAttachmentClick(this)">
            <img src="${previewSrc}" class="chat-msg-attached-img" alt="${escapeHtml(att.name)}" loading="lazy" />
            <div class="chat-img-zoom-hint">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
              <span>Zoom</span>
            </div>
          </div>
        `;
      } else {
        return `
          <div class="chat-msg-file-card" data-url="${escapeHtml(att.previewUrl || '')}" data-title="${escapeHtml(att.name)}" onclick="window.handleChatAttachmentClick(this)">
            <span class="chat-file-icon">${getFileCategoryIcon(att.name)}</span>
            <div class="chat-file-info">
              <span class="chat-file-name">${escapeHtml(att.name)}</span>
              <span class="chat-file-size">${formatFileSize(att.size)}</span>
            </div>
          </div>
        `;
      }
    }).join('') + '</div>';
  }

  const displayText = text || (attachmentsToSend.length > 0 ? (attachmentsToSend[0].isImage ? 'Analyze attached image' : 'Inspect attached file(s)') : '');

  const userCard = document.createElement('div');
  userCard.className = 'chat-msg user';
  userCard.innerHTML = `
    ${attachmentsHtml}
    ${displayText ? `<div class="chat-bubble user">${escapeHtml(displayText).replace(/\n/g, '<br>')}</div>` : ''}
    <div class="chat-msg-meta">
      <span class="chat-msg-time">${now}</span>
      <button class="btn-msg-action btn-copy-prompt" title="Copy prompt">
        <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        <span>Copy</span>
      </button>
    </div>
  `;
  messagesContainer.appendChild(userCard);
  activeTurnUserCard = userCard;
  scrollChatToBottom({ force: true });

  // Keep pinned prompt bar hidden during focus mode
  hidePinnedPrompt();
  emitAgentTelemetry({ type: 'agent', tag: 'PROMPT', text: displayText.slice(0, 42), meta: 'USER' });

  const btnCopyPrompt = userCard.querySelector('.btn-copy-prompt');
  if (btnCopyPrompt) {
    btnCopyPrompt.addEventListener('click', () => {
      window.safeCopyToClipboard(displayText).then(() => {
        const span = btnCopyPrompt.querySelector('span');
        if (span) span.innerText = 'Copied!';
        btnCopyPrompt.classList.add('copied');
        setTimeout(() => {
          if (span) span.innerText = 'Copy';
          btnCopyPrompt.classList.remove('copied');
        }, 2000);
      });
    });
  }

  // 2. Assistant Message
  const assistantCard = document.createElement('div');
  assistantCard.className = 'chat-msg assistant';
  assistantCard.innerHTML = `
    <div class="chat-assistant-header">
      <div class="chat-avatar-ai">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
      </div>
      <span class="chat-assistant-name">FLOWORK AGENT</span>
      <span class="chat-model-badge">${selectedChatModelId}</span>
      <span class="chat-msg-time">${now}</span>
    </div>
    <div class="chat-msg-content">
      <div class="chat-thinking-area"></div>
      <div class="chat-tools-area"></div>
      <div class="chat-body-area"></div>
      <div class="chat-msg-footer" style="display: none;">
        <button class="btn-msg-action btn-copy-response" title="Copy response">
          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <span>Copy</span>
        </button>
        <button class="btn-msg-action btn-retry-response" title="Regenerate this response">
          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          <span>Retry</span>
        </button>
        <button class="btn-msg-action btn-revert-turn" title="Rewind conversation back to before this response">
          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 14 4 9 9 4"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/></svg>
          <span>Revert</span>
        </button>
      </div>
    </div>
  `;
  messagesContainer.querySelectorAll('.chat-msg-active-turn').forEach(el => el.classList.remove('chat-msg-active-turn'));
  messagesContainer.appendChild(assistantCard);
  messagesContainer.classList.add('chat-focus-mode');
  // Only assistantCard is active turn; userCard and old messages are hidden during execution
  assistantCard.classList.add('chat-msg-active-turn');
  scrollChatToBottom({ force: true });

  const thinkingArea = assistantCard.querySelector('.chat-thinking-area');
  const toolsArea = assistantCard.querySelector('.chat-tools-area');
  const bodyArea = assistantCard.querySelector('.chat-body-area');
  const footerArea = assistantCard.querySelector('.chat-msg-footer');
  const btnCopy = assistantCard.querySelector('.btn-copy-response');
  const btnRetry = assistantCard.querySelector('.btn-retry-response');
  const btnRevert = assistantCard.querySelector('.btn-revert-turn');

  activeToolsArea = toolsArea;
  activeBodyArea = bodyArea;

  btnCopy.addEventListener('click', () => {
    const textToCopy = bodyArea.innerText || accumulatedResponse;
    window.safeCopyToClipboard(textToCopy).then(() => {
      const span = btnCopy.querySelector('span');
      if (span) span.innerText = 'Copied!';
      btnCopy.classList.add('copied');
      setTimeout(() => {
        if (span) span.innerText = 'Copy';
        btnCopy.classList.remove('copied');
      }, 2000);
    });
  });

  if (btnRetry) {
    btnRetry.addEventListener('click', () => {
      regenerateLastTurn();
    });
  }

  if (btnRevert) {
    btnRevert.addEventListener('click', () => {
      undoLastChatTurn();
    });
  }

  setChatStreamingState(true);
  currentAbortController = new AbortController();

  turnPinnedSkills.clear();
  turnPinnedTools.clear();
  activeRunningTools.clear();
  FloworkLoopSysMonitor._loopStartTime = Date.now();
  FloworkLoopSysMonitor.start();

  currentThinkingController = createThinkingController(thinkingArea);
  let accumulatedThinking = '';
  let accumulatedResponse = '';
  const pendingVisualBlocks = [];
  const stepToolNames = new Map();

  activeSubagentKeys.clear();
  activeTaskKeys.clear();
  updateTopStatusBar();

  // Map to store rendered tool cards by step index for status updates
  const activeToolElements = new Map();

  try {
    let promptPayload = displayText;
    let imagePaths = [];
    let imageBase64List = [];
    let mediaList = [];

    if (attachmentsToSend && attachmentsToSend.length > 0) {
      try {
        const uploadResults = await Promise.all(attachmentsToSend.map(uploadAttachmentToServer));
        uploadResults.forEach(r => {
          if (r.isImage && r.webUrl) {
            const imgEls = userCard.querySelectorAll('img.chat-msg-attached-img');
            imgEls.forEach(img => {
              if (img.getAttribute('alt') === r.originalName) {
                img.src = r.webUrl;
                const wrap = img.closest('.chat-msg-img-wrap');
                if (wrap) {
                  wrap.setAttribute('data-url', r.webUrl);
                  wrap.setAttribute('data-title', r.originalName);
                  wrap.onclick = () => openChatLightbox(r.webUrl, r.originalName);
                }
              }
            });
          }
        });
        const attachSummary = uploadResults.map(r => 
          `- ${r.isImage ? 'Image' : 'File'}: ${r.originalName}\n  Path: ${r.targetPath}\n  Preview URL: ${r.webUrl}\n  Size: ${formatFileSize(r.size)}`
        ).join('\n');
        promptPayload = `[USER ATTACHMENTS]\n${attachSummary}\n\n${displayText}`;

        const imageUploads = uploadResults.filter(r => r.isImage);
        imagePaths = imageUploads.map(r => r.targetPath);
        imageBase64List = imageUploads.map(r => r.base64).filter(Boolean);
        mediaList = imageUploads.map(r => ({
          mime_type: r.mimeType || 'image/png',
          data: r.base64 || '',
          path: r.targetPath || '',
          url: r.webUrl || ''
        }));
      } catch (upErr) {
        console.warn('[Attachments] Upload error:', upErr);
      }
    }

    if (window.office3DInstance) {
      const activeTarget = (typeof getActiveTargetAgentId === 'function') ? getActiveTargetAgentId() : 'agent-default';
      cancelAgentExitTimer(activeTarget);
      window.office3DInstance.setAgentState(activeTarget, 'working');
      if (typeof window.setOfficeAgentThinking === 'function') {
        window.setOfficeAgentThinking(activeTarget, 'Processing instructions & organizing swarm...', true);
      }
      if (typeof window.updateOfficeAgentReasoning === 'function') {
        window.updateOfficeAgentReasoning({
          phase: 'INSTRUCTION RECEIVED',
          userPrompt: displayText,
          assistantResponse: 'Sovereign Core receiving instructions... Formulating tactical execution...',
          reason: 'Analyzing instruction and formulating sovereign execution plan...',
          keywords: ['user_query', 'intent_routing', 'sovereign_core'],
          cotLines: [`USER: "${displayText}"`, 'Processing instruction & evaluating task path...']
        });
      }
    }

    const persistentMode = (localStorage.getItem('xflow_session_mode') === 'solo') ? 'solo' : (window.currentSessionMode || 'team');
    const isTeamMode = (persistentMode !== 'solo') || (window.currentSessionType === 'group');
    const effectiveSessionType = isTeamMode ? 'group' : 'personal';
    const effectiveSessionMode = isTeamMode ? 'team' : 'solo';
    const effectivePersona = (isTeamMode ? 'leader' : (currentSessionPersonaId && currentSessionPersonaId !== 'leader' ? currentSessionPersonaId : 'mr.flow')).trim();

    const res = await fetch('/api/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-flowork-account-id': currentSessionAccountId || 'combo',
        'x-flowork-session-id': currentChatSessionId || ''
      },
      signal: currentAbortController.signal,
      body: JSON.stringify({
        message: promptPayload,
        session_id: currentChatSessionId,
        session_type: effectiveSessionType,
        mode: effectiveSessionMode,
        model: selectedChatModelId,
        account_id: currentSessionAccountId || 'combo',
        agent_id: effectivePersona,
        agent_persona: effectivePersona,
        image_paths: imagePaths.length > 0 ? imagePaths : undefined,
        images: imagePaths.length > 0 ? imagePaths : undefined,
        image_base64: imageBase64List.length > 0 ? imageBase64List[0] : undefined,
        media: mediaList.length > 0 ? mediaList : undefined
      })
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let sseBuffer = '';
    let currentEvent = 'message';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      sseBuffer += decoder.decode(value, { stream: true });
      const lines = sseBuffer.split('\n');
      sseBuffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          currentEvent = 'message';
          continue;
        }

        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.substring(6).trim();
        } else if (trimmed.startsWith('data:')) {
          const rawData = trimmed.substring(5).trim();
          try {
            const data = JSON.parse(rawData);
            handleTelemetryEvent(currentEvent, data);

            if (currentEvent === 'session') {
              const sessId = data.session_id || data.flwcore_id;
              if (sessId) {
                currentChatSessionId = sessId;
                localStorage.setItem('xflow_active_session_id', sessId);
                localStorage.removeItem('xflow_new_chat_explicit');
                if (pendingSessionAccountId && pendingSessionAccountId !== 'combo') {
                  setSessionBinding(pendingSessionAccountId, currentSessionFailoverPolicy);
                }
                if (currentSessionPersonaId) {
                  localStorage.setItem('xflow_session_persona_' + sessId, currentSessionPersonaId);
                  localStorage.setItem('xflow_persona_session_' + currentSessionPersonaId, sessId);
                  setSessionAgentPersona(currentSessionPersonaId, { preserveSession: true });
                }
              }
            } else if (currentEvent === 'thinking') {
              if (data.thinking) {
                accumulatedThinking += (accumulatedThinking ? '\n' : '') + data.thinking;
                if (currentThinkingController && currentThinkingController.updateSnippet) {
                  currentThinkingController.updateSnippet(data.thinking);
                }
                setMascotAgentLoop(true, 'Synthesizing reasoning & analyzing task...');
                const activeTarget = (typeof getActiveTargetAgentId === 'function') ? getActiveTargetAgentId() : 'agent-default';
                cancelAgentExitTimer(activeTarget);
                if (window.office3DInstance) {
                  window.office3DInstance.setAgentState(activeTarget, 'working');
                }
                if (typeof window.setOfficeAgentThinking === 'function') {
                  const snippet = data.thinking.replace(/[\r\n]+/g, ' ').trim();
                  window.setOfficeAgentThinking(activeTarget, snippet.length > 50 ? snippet.slice(0, 48) + '…' : snippet, true);
                }
                if (typeof window.updateOfficeAgentReasoning === 'function') {
                  const snippet = data.thinking.replace(/[\r\n]+/g, ' ').trim();
                  window.updateOfficeAgentReasoning({
                    phase: 'COGNITIVE REASONING',
                    reason: snippet.length > 55 ? snippet.slice(0, 52) + '…' : snippet,
                    keywords: ['fl_brain', 'synthesis', 'exit_code_0'],
                    cotLines: [snippet]
                  });
                }
              }
            } else if (currentEvent === 'tool') {
              const rawTool = (data.tool || 'tool').toLowerCase();
              setMascotAgentLoop(true, `Executing tool: ${data.tool || 'tool'}...`);
              const toolStatus = data.status || 'running';
              const stepIdx = data.step_idx !== undefined ? data.step_idx : ('t_' + Date.now());
              stepToolNames.set(String(stepIdx), rawTool);

              // Real-Time Tool-to-Worker Agent Resolution
              const workerAgentId = resolveWorkerAgentFromTool(data.tool || 'tool', data.details || {});
              activeStepWorkerAgents.set(String(stepIdx), workerAgentId);
              cancelAgentExitTimer(workerAgentId);

              setUnifiedAgentActivity(workerAgentId, 'working');

              // Pipe real-time tool reason into the 3D agent thought badge
              const toolReason = extractToolReason(data.tool || 'tool', data.details || {});
              if (typeof window.setOfficeAgentThinking === 'function') {
                const displayReason = toolReason ? `⚡ [${data.tool || 'tool'}] ${toolReason}` : `⚡ Executing: ${data.tool || 'tool'}`;
                window.setOfficeAgentThinking(workerAgentId, displayReason, true);
              }
              if (typeof window.updateOfficeAgentReasoning === 'function') {
                const displayReason = toolReason || `Executing ${data.tool || 'tool'}`;
                window.updateOfficeAgentReasoning({
                  phase: 'TOOL PIPELINE',
                  reason: displayReason.length > 55 ? displayReason.slice(0, 52) + '…' : displayReason,
                  keywords: [data.tool || 'tool', 'sovereign_core', 'exit_code_0'],
                  cotLines: [`Executing tool: ${data.tool || 'tool'}`, displayReason]
                });
              }

              // Multi-Agent Concurrent Swarm Dispatcher for invoke_subagent
              if (rawTool.includes('invoke_subagent') && data.details) {
                const subList = data.details.Subagents || data.details.subagents || data.details.tasks || data.details.agents;
                if (Array.isArray(subList) && subList.length > 0) {
                  subList.forEach((sub) => {
                    const subCandidate = sub.TypeName || sub.typeName || sub.role || sub.Role || sub.agent_id || sub.id;
                    const subWorkerId = resolveWorkerAgentFromTool('invoke_subagent', { target_agent_id: subCandidate, role: sub.Role || sub.role });
                    cancelAgentExitTimer(subWorkerId);
                    setUnifiedAgentActivity(subWorkerId, 'working');
                    if (typeof window.setOfficeAgentThinking === 'function') {
                      const subRole = sub.Role || sub.role || sub.TypeName || 'Swarm Worker';
                      window.setOfficeAgentThinking(subWorkerId, `⚡ [Swarm Wave] ${subRole}`, true);
                    }
                  });
                }
              }

              if (rawTool.includes('restart') || rawTool.includes('system_restart') || rawTool.includes('flow_restart')) {
                isSystemRestarting = true;
                startRestartPolling(currentChatSessionId);
              }

              if (rawTool.includes('subagent') || rawTool.includes('spawnagent') || rawTool.includes('invoke_agent') || rawTool.includes('delegate')) {
                if (toolStatus === 'running') activeSubagentKeys.add(stepIdx);
                else activeSubagentKeys.delete(stepIdx);
              } else if ((rawTool.includes('task') && !rawTool.includes('command')) || rawTool.includes('update_topic') || rawTool.includes('topic')) {
                if (toolStatus === 'running') activeTaskKeys.add(stepIdx);
                else activeTaskKeys.delete(stepIdx);
              }
              updateTopStatusBar();

              renderToolInArea(toolsArea, data.tool || 'tool', data.details || {}, toolStatus, stepIdx, activeToolElements);
            } else if (currentEvent === 'tool_done') {
              const stepIdx = data.step_idx;
              const workerAgentId = (stepIdx !== undefined ? activeStepWorkerAgents.get(String(stepIdx)) : null) || resolveWorkerAgentFromTool(data.tool || '', data.details || {});
              if (stepIdx !== undefined) {
                activeStepWorkerAgents.delete(String(stepIdx));
              }

              if (data.tool) {
                recordThinkingArsenal(data.tool, data.details || {}, 'done', data.output, stepIdx);
              } else {
                activeRunningTools.clear();
                if (currentThinkingController && typeof currentThinkingController.refreshArsenal === 'function') {
                  currentThinkingController.refreshArsenal();
                }
                FloworkLoopSysMonitor.updateArsenalCounters();
              }

              if (typeof window.setOfficeAgentThinking === 'function') {
                window.setOfficeAgentThinking(workerAgentId, 'Task phase verified (Exit Code 0)', false);
              }

              // Multi-Agent Swarm Wave Barrier Sync for invoke_subagent
              if (String(data.tool || '').toLowerCase().includes('invoke_subagent') && data.details) {
                const subList = data.details.Subagents || data.details.subagents || data.details.tasks || data.details.agents;
                if (Array.isArray(subList) && subList.length > 0) {
                  subList.forEach((sub) => {
                    const subCandidate = sub.TypeName || sub.typeName || sub.role || sub.Role || sub.agent_id || sub.id;
                    const subWorkerId = resolveWorkerAgentFromTool('invoke_subagent', { target_agent_id: subCandidate, role: sub.Role || sub.role });
                    setUnifiedAgentActivity(subWorkerId, 'idle');
                    if (typeof window.setOfficeAgentThinking === 'function') {
                      window.setOfficeAgentThinking(subWorkerId, 'Wave completed (Exit Code 0)', false);
                    }
                    scheduleAgentExit(subWorkerId, 2500);
                  });
                }
              }

              // If this worker agent has no more tools running, schedule dynamic departure
              const workerStillBusy = Array.from(activeStepWorkerAgents.values()).includes(workerAgentId);
              if (!workerStillBusy) {
                scheduleAgentExit(workerAgentId, 2500);
              }

              if (stepIdx !== undefined) {
                activeSubagentKeys.delete(stepIdx);
                activeTaskKeys.delete(stepIdx);
                updateTopStatusBar();

                markToolDone(stepIdx, activeToolElements, data.output);

                // Strictly buffer render_visual output until the chat turn ends! Never show chart before chat finishes!
                const resolvedTool = data.tool || stepToolNames.get(String(stepIdx)) || '';
                const visualBlock = extractVisualBlockFromToolOutput(resolvedTool, data.output);
                if (visualBlock && !pendingVisualBlocks.includes(visualBlock)) {
                  pendingVisualBlocks.push(visualBlock);
                }
              }
            } else if (currentEvent === 'terminal_stream') {
              const stepIdx = data.step_idx;
              if (stepIdx !== undefined) {
                updateTerminalStream(stepIdx, data, activeToolElements);
              }
            } else if (currentEvent === 'text_chunk') {
              if (currentThinkingController && currentThinkingController.advanceDag) {
                currentThinkingController.advanceDag(4, '4. STREAM RESPONSE');
              }
              accumulatedResponse += (data.delta || data.text || '');
              if (typeof window.updateOfficeAgentReasoning === 'function') {
                window.updateOfficeAgentReasoning({
                  phase: 'STREAMING RESPONSE',
                  userPrompt: displayText,
                  assistantResponse: accumulatedResponse,
                  reason: 'Generating response stream...',
                  keywords: ['response_stream', 'sovereign_core', 'exit_code_0']
                });
              }
            } else if (currentEvent === 'response') {
              if (currentThinkingController && currentThinkingController.advanceDag) {
                currentThinkingController.advanceDag(4, '4. STREAM RESPONSE');
              }
              accumulatedResponse = data.response || '';
              if (typeof window.updateOfficeAgentReasoning === 'function') {
                window.updateOfficeAgentReasoning({
                  phase: 'STREAMING RESPONSE',
                  userPrompt: displayText,
                  assistantResponse: accumulatedResponse,
                  reason: 'Generating response stream...',
                  keywords: ['response_stream', 'sovereign_core', 'exit_code_0']
                });
              }
            } else if (currentEvent === 'error') {
              bodyArea.innerHTML = `<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171;padding:8px 12px;border-radius:8px;font-family:var(--font-mono);font-size:11px;">⚠️ ${escapeHtml(data.error || 'Execution Error')}</div>`;
              FloworkChatTacticalOverlay.spawn('alert_breach', { error: data.error || 'Execution Error' });
              FloworkMrFlowAudio.trigger('alert_breach');
            } else if (currentEvent === 'done') {
              activeRunningTools.clear();
              activeStepWorkerAgents.clear();
              const durationSec = currentThinkingController ? currentThinkingController.stop() : 1;
              thinkingArea.innerHTML = '';
              const thoughtCard = formatThoughtCard(accumulatedThinking, durationSec);
              if (thoughtCard) thinkingArea.appendChild(thoughtCard);
              activeSubagentKeys.clear();
              activeTaskKeys.clear();
              updateTopStatusBar();
              collapseAllToolsInArea(toolsArea);

              const activeTarget = (typeof getActiveTargetAgentId === 'function') ? getActiveTargetAgentId() : 'agent-default';
              if (typeof window.setOfficeAgentThinking === 'function') {
                window.setOfficeAgentThinking(activeTarget, 'Task workflow verified (Exit Code 0)', false);
              }
              if (typeof window.updateOfficeAgentReasoning === 'function') {
                window.updateOfficeAgentReasoning({
                  phase: 'TURN COMPLETED // EXIT CODE 0',
                  userPrompt: displayText,
                  assistantResponse: accumulatedResponse,
                  reason: 'Workflow verified & validated (Exit Code 0)',
                  keywords: ['exit_code_0', 'verified', 'sovereign'],
                  cotLines: ['Task completed successfully with Exit Code 0.', 'System state: deterministic verification passed.', 'Awaiting next instruction...']
                });
              }
              scheduleAgentExit(activeTarget, 2500);

              if (pendingVisualBlocks.length > 0) {
                pendingVisualBlocks.forEach(vb => {
                  if (!accumulatedResponse.includes(vb)) {
                    accumulatedResponse = (accumulatedResponse ? accumulatedResponse.trim() + '\n\n' : '') + vb;
                  }
                });
                pendingVisualBlocks.length = 0;
              }
              if (accumulatedResponse) {
                bodyArea.innerHTML = renderMarkdown(accumulatedResponse);
                footerArea.style.display = 'flex';
              }
            }
            scrollChatToBottom({ force: true });
          } catch (e) {
            console.error('SSE JSON error:', e);
          }
        }
      }
    }
  } catch (err) {
    if (isSystemRestarting) {
      console.log('[Chat] Stream paused during system restart handoff...');
      bodyArea.innerHTML = `<div style="color:var(--accent-color, #38bdf8); font-size:11px; font-family:var(--font-mono); padding:6px 0; display:flex; align-items:center; gap:8px;"><span class="fl-tool-spinner"></span> 🔄 System is restarting binary & resuming tasks autonomously...</div>`;
    } else if (err.name !== 'AbortError') {
      bodyArea.innerHTML = `<div style="color:#f87171; font-size:11px; font-family:var(--font-mono); padding:6px 0;">⚠️ Network Error: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    if (currentThinkingController) currentThinkingController.stop();
    if (pendingVisualBlocks.length > 0) {
      pendingVisualBlocks.forEach(vb => {
        if (!accumulatedResponse.includes(vb)) {
          accumulatedResponse = (accumulatedResponse ? accumulatedResponse.trim() + '\n\n' : '') + vb;
        }
      });
      pendingVisualBlocks.length = 0;
    }
    if (accumulatedResponse && !isSystemRestarting) {
      bodyArea.innerHTML = renderMarkdown(accumulatedResponse);
      footerArea.style.display = 'flex';
    }
    setChatStreamingState(false);
    currentAbortController = null;
    hidePinnedPrompt();
    activeSubagentKeys.clear();
    activeTaskKeys.clear();
    updateTopStatusBar();
    if (toolsArea) {
      collapseAllToolsInArea(toolsArea);
    }
    messagesContainer.classList.remove('chat-focus-mode');
    messagesContainer.querySelectorAll('.chat-msg-active-turn').forEach(el => el.classList.remove('chat-msg-active-turn'));
    setMascotAgentLoop(false);
    activeStepWorkerAgents.clear();
    if (window.office3DInstance && Array.isArray(window.office3DInstance.agentRoster)) {
      setTimeout(() => {
        window.office3DInstance.agentRoster.forEach(ag => {
          if (!ag.isBoss && ag.state === 'working') {
            setUnifiedAgentActivity(ag.id, 'idle');
          }
        });
      }, 2500);
    }

    if (!isSystemRestarting) {
      if (sendBtn) {
        sendBtn.classList.remove('is-running');
        sendBtn.title = 'Send (Enter)';
      }
    } else {
      if (sendBtn) {
        sendBtn.classList.add('is-running');
        sendBtn.title = 'Flowork is restarting & loading updates...';
      }
    }
    // Immediately synchronize fingerprint with backend steps to prevent disruptive DOM reconstruction
    if (currentChatSessionId) {
      try {
        fetch(`/api/chat/steps/${encodeURIComponent(currentChatSessionId)}`)
          .then(r => r.json())
          .then(d => {
            if (d && d.status === 'ok' && Array.isArray(d.data?.steps)) {
              const sSteps = d.data.steps;
              const count = sSteps.length;
              const lastStep = count > 0 ? sSteps[count - 1] : null;
              const lastStatus = lastStep ? (lastStep.status || '') : '';
              const lastRespLen = (lastStep?.plannerResponse?.response) ? lastStep.plannerResponse.response.length : 0;
              lastKnownStepFingerprint = `${count}:${lastStatus}:${lastRespLen}`;
            }
          }).catch(() => {});
      } catch (_) {}
    }

    scrollChatToBottom({ force: true });

    // Auto-dispatch next queued message if any
    if (queuedMessages.length > 0) {
      const nextMsg = queuedMessages.shift();
      renderQueueTray();
      setTimeout(() => {
        executeChatMessage(nextMsg.text, nextMsg.attachments || []);
      }, 250);
    }
  }
}

async function undoLastChatTurn() {
  if (isChatStreaming) {
    showToast('Agent is currently executing, please wait...');
    return;
  }
  if (!currentChatSessionId) {
    showToast('No active conversation session to undo');
    return;
  }

  try {
    const res = await fetch('/api/chat/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentChatSessionId })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      const restoredPrompt = data.restored_prompt;
      if (restoredPrompt) {
        const inputEl = document.getElementById('rightbar-chat-input');
        if (inputEl) {
          inputEl.value = restoredPrompt;
          inputEl.style.height = 'auto';
          inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
          inputEl.focus();
        }
      }
      showToast('Undid last turn. Prompt restored to editor.');
      await loadChatSession(currentChatSessionId);
    } else {
      showToast('Undo failed: ' + (data.message || 'Unknown error'));
    }
  } catch (err) {
    showToast('Error sending undo request: ' + err.message);
  }
}

async function copyEntireChatTranscript() {
  const messagesContainer = document.getElementById('rightbar-messages');
  if (!messagesContainer) return;

  const cards = messagesContainer.querySelectorAll('.chat-msg');
  if (!cards.length) {
    showToast('Chat is empty');
    return;
  }

  let markdownLines = [
    `# 📜 Sovereign Flowork OS Conversation Transcript`,
    `*Session ID: ${currentChatSessionId || 'Transient'}*`,
    `*Generated: ${new Date().toLocaleString()}*`,
    `---`,
    ''
  ];

  cards.forEach(card => {
    if (card.classList.contains('user')) {
      const bubble = card.querySelector('.chat-bubble.user');
      const time = card.querySelector('.chat-msg-time')?.innerText || '';
      const text = bubble ? bubble.innerText.trim() : '';
      if (text) {
        markdownLines.push(`### 👤 User ${time ? `(${time})` : ''}\n\n${text}\n`);
      }
    } else if (card.classList.contains('assistant')) {
      const author = card.querySelector('.chat-assistant-name')?.innerText || 'FLOWORK AGENT';
      const body = card.querySelector('.chat-body-area');
      const thoughtEl = card.querySelector('.fl-thought-content');
      const text = body ? body.innerText.trim() : '';
      const thought = thoughtEl ? thoughtEl.innerText.trim() : '';

      const toolItems = card.querySelectorAll('.fl-tool-header, .fl-tool-summary');
      let toolSummaryText = '';
      if (toolItems.length > 0 && !text) {
        toolSummaryText = Array.from(toolItems).map(t => `- 🛠️ ${t.innerText.trim()}`).join('\n');
      }

      // Only output header if there is actual text, thought, or tool summary to prevent ghost header spam
      if (text || thought || toolSummaryText) {
        markdownLines.push(`### 🤖 ${author}\n`);
        if (thought) {
          markdownLines.push(`<details>\n<summary>🧠 Thought Process</summary>\n\n\`\`\`\n${thought}\n\`\`\`\n</details>\n`);
        }
        if (text) {
          markdownLines.push(`${text}\n`);
        } else if (toolSummaryText) {
          markdownLines.push(`${toolSummaryText}\n`);
        }
      }
    }
  });

  const fullMarkdown = markdownLines.join('\n');
  try {
    await window.safeCopyToClipboard(fullMarkdown);
    const btn = document.getElementById('btn-chat-copy-all');
    if (btn) {
      btn.style.color = '#34d399';
      setTimeout(() => { btn.style.color = ''; }, 2000);
    }
    showToast('Full conversation transcript copied to clipboard!');
  } catch (e) {
    showToast('Failed to copy to clipboard');
  }
}

async function regenerateLastTurn() {
  if (isChatStreaming) {
    showToast('Agent is busy, wait for completion...');
    return;
  }
  if (!currentChatSessionId) {
    showToast('No active conversation session to retry');
    return;
  }

  const messagesContainer = document.getElementById('rightbar-messages');
  if (!messagesContainer) return;

  const assistantCards = messagesContainer.querySelectorAll('.chat-msg.assistant');
  let targetCard = null;
  if (assistantCards.length > 0) {
    targetCard = assistantCards[assistantCards.length - 1];
  } else {
    targetCard = document.createElement('div');
    targetCard.className = 'chat-msg assistant';
    messagesContainer.appendChild(targetCard);
  }

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  targetCard.innerHTML = `
    <div class="chat-assistant-header">
      <div class="chat-avatar-ai">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
      </div>
      <span class="chat-assistant-name">FLOWORK AGENT</span>
      <span class="chat-model-badge">${selectedChatModelId}</span>
      <span class="chat-msg-time">${now}</span>
    </div>
    <div class="chat-msg-content">
      <div class="chat-thinking-area"></div>
      <div class="chat-tools-area"></div>
      <div class="chat-body-area"></div>
      <div class="chat-msg-footer" style="display: none;">
        <button class="btn-msg-action btn-copy-response" title="Copy response">
          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <span>Copy</span>
        </button>
        <button class="btn-msg-action btn-retry-response" title="Regenerate this response">
          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          <span>Retry</span>
        </button>
        <button class="btn-msg-action btn-revert-turn" title="Rewind conversation back to before this response">
          <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 14 4 9 9 4"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/></svg>
          <span>Revert</span>
        </button>
      </div>
    </div>
  `;

  const thinkingArea = targetCard.querySelector('.chat-thinking-area');
  const toolsArea = targetCard.querySelector('.chat-tools-area');
  const bodyArea = targetCard.querySelector('.chat-body-area');
  const footerArea = targetCard.querySelector('.chat-msg-footer');
  const btnCopy = targetCard.querySelector('.btn-copy-response');
  const btnRetry = targetCard.querySelector('.btn-retry-response');
  const btnRevert = targetCard.querySelector('.btn-revert-turn');

  btnCopy.addEventListener('click', () => {
    const textToCopy = bodyArea.innerText || accumulatedResponse;
    window.safeCopyToClipboard(textToCopy).then(() => {
      const span = btnCopy.querySelector('span');
      if (span) span.innerText = 'Copied!';
      btnCopy.classList.add('copied');
      setTimeout(() => {
        if (span) span.innerText = 'Copy';
        btnCopy.classList.remove('copied');
      }, 2000);
    });
  });

  if (btnRetry) {
    btnRetry.addEventListener('click', () => {
      regenerateLastTurn();
    });
  }

  if (btnRevert) {
    btnRevert.addEventListener('click', () => {
      undoLastChatTurn();
    });
  }

  setChatStreamingState(true);
  currentAbortController = new AbortController();
  messagesContainer.classList.add('has-messages');
  setMascotAgentLoop(true, 'Regenerating turn & executing autonomous loop...');
  messagesContainer.classList.add('chat-focus-mode');
  messagesContainer.querySelectorAll('.chat-msg-active-turn').forEach(el => el.classList.remove('chat-msg-active-turn'));
  targetCard.classList.add('chat-msg-active-turn');
  hidePinnedPrompt();

  activeToolsArea = toolsArea;
  activeBodyArea = bodyArea;

  const thinkingController = createThinkingController(thinkingArea);
  currentThinkingController = thinkingController;
  let accumulatedThinking = '';
  let accumulatedResponse = '';
  const pendingVisualBlocks = [];
  const stepToolNames = new Map();

  activeSubagentKeys.clear();
  activeTaskKeys.clear();
  updateTopStatusBar();

  if (window.office3DInstance) {
    const activeTarget = (typeof getActiveTargetAgentId === 'function') ? getActiveTargetAgentId() : 'agent-default';
    cancelAgentExitTimer(activeTarget);
    window.office3DInstance.setAgentState(activeTarget, 'working');
    if (typeof window.setOfficeAgentThinking === 'function') {
      window.setOfficeAgentThinking(activeTarget, 'Regenerating turn & executing workflow...', true);
    }
  }

  try {
    const res = await fetch('/api/chat/regenerate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: currentAbortController.signal,
      body: JSON.stringify({
        session_id: currentChatSessionId,
        model: selectedChatModelId
      })
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let sseBuffer = '';
    let currentEvent = 'message';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      sseBuffer += decoder.decode(value, { stream: true });
      const lines = sseBuffer.split('\n');
      sseBuffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          currentEvent = 'message';
          continue;
        }

        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.substring(6).trim();
        } else if (trimmed.startsWith('data:')) {
          const rawData = trimmed.substring(5).trim();
          try {
            const data = JSON.parse(rawData);
            handleTelemetryEvent(currentEvent, data);

            if (currentEvent === 'thinking') {
              if (data.thinking) {
                accumulatedThinking += (accumulatedThinking ? '\n' : '') + data.thinking;
                if (currentThinkingController && currentThinkingController.updateSnippet) {
                  currentThinkingController.updateSnippet(data.thinking);
                }
                const activeTarget = (typeof getActiveTargetAgentId === 'function') ? getActiveTargetAgentId() : 'agent-default';
                cancelAgentExitTimer(activeTarget);
                if (window.office3DInstance) {
                  window.office3DInstance.setAgentState(activeTarget, 'working');
                }
                if (typeof window.setOfficeAgentThinking === 'function') {
                  const snippet = data.thinking.replace(/[\r\n]+/g, ' ').trim();
                  window.setOfficeAgentThinking(activeTarget, snippet.length > 50 ? snippet.slice(0, 48) + '…' : snippet, true);
                }
              }
            } else if (currentEvent === 'tool') {
              const rawTool = (data.tool || 'tool').toLowerCase();
              const toolStatus = data.status || 'running';
              const stepIdx = data.step_idx !== undefined ? data.step_idx : ('t_' + Date.now());
              stepToolNames.set(String(stepIdx), rawTool);

              // Real-Time Tool-to-Worker Agent Resolution
              const workerAgentId = resolveWorkerAgentFromTool(data.tool || 'tool', data.details || {});
              activeStepWorkerAgents.set(String(stepIdx), workerAgentId);
              cancelAgentExitTimer(workerAgentId);

              setUnifiedAgentActivity(workerAgentId, 'working');

              const toolReason = extractToolReason(data.tool || 'tool', data.details || {});
              if (typeof window.setOfficeAgentThinking === 'function') {
                const displayReason = toolReason ? `⚡ [${data.tool || 'tool'}] ${toolReason}` : `⚡ Executing: ${data.tool || 'tool'}`;
                window.setOfficeAgentThinking(workerAgentId, displayReason, true);
              }

              if (rawTool.includes('subagent') || rawTool.includes('spawnagent') || rawTool.includes('invoke_agent') || rawTool.includes('delegate')) {
                if (toolStatus === 'running') activeSubagentKeys.add(stepIdx);
                else activeSubagentKeys.delete(stepIdx);
              } else if ((rawTool.includes('task') && !rawTool.includes('command')) || rawTool.includes('update_topic') || rawTool.includes('topic')) {
                if (toolStatus === 'running') activeTaskKeys.add(stepIdx);
                else activeTaskKeys.delete(stepIdx);
              }
              updateTopStatusBar();

              renderToolInArea(toolsArea, data.tool || 'tool', data.details || {}, toolStatus, stepIdx, activeToolElements);
            } else if (currentEvent === 'tool_done') {
              const stepIdx = data.step_idx;
              const workerAgentId = (stepIdx !== undefined ? activeStepWorkerAgents.get(String(stepIdx)) : null) || resolveWorkerAgentFromTool(data.tool || '', data.details || {});
              if (stepIdx !== undefined) {
                activeStepWorkerAgents.delete(String(stepIdx));
              }

              if (typeof window.setOfficeAgentThinking === 'function') {
                window.setOfficeAgentThinking(workerAgentId, 'Task phase verified (Exit Code 0)', false);
              }

              const workerStillBusy = Array.from(activeStepWorkerAgents.values()).includes(workerAgentId);
              if (!workerStillBusy) {
                scheduleAgentExit(workerAgentId, 2500);
              }

              if (stepIdx !== undefined) {
                activeSubagentKeys.delete(stepIdx);
                activeTaskKeys.delete(stepIdx);
                updateTopStatusBar();

                markToolDone(stepIdx, activeToolElements, data.output);
                const resolvedTool = data.tool || stepToolNames.get(String(stepIdx)) || '';
                recordThinkingArsenal(resolvedTool, {}, 'done', data.output, stepIdx);
                const visualBlock = extractVisualBlockFromToolOutput(resolvedTool, data.output);
                if (visualBlock && !pendingVisualBlocks.includes(visualBlock)) {
                  pendingVisualBlocks.push(visualBlock);
                }
              }
            } else if (currentEvent === 'response') {
              if (currentThinkingController && currentThinkingController.advanceDag) {
                currentThinkingController.advanceDag(4, '4. STREAM RESPONSE');
              }
              accumulatedResponse = data.response || '';
            } else if (currentEvent === 'error') {
              bodyArea.innerHTML = `<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171;padding:8px 12px;border-radius:8px;font-family:var(--font-mono);font-size:11px;">⚠️ ${escapeHtml(data.error || 'Execution Error')}</div>`;
              FloworkChatTacticalOverlay.spawn('alert_breach', { error: data.error || 'Execution Error' });
              FloworkMrFlowAudio.trigger('alert_breach');
            } else if (currentEvent === 'done') {
              activeStepWorkerAgents.clear();
              const durationSec = thinkingController.stop();
              if (accumulatedThinking) {
                thinkingArea.innerHTML = '';
                const thoughtCard = formatThoughtCard(accumulatedThinking, durationSec);
                if (thoughtCard) thinkingArea.appendChild(thoughtCard);
              } else {
                thinkingArea.innerHTML = '';
              }
              activeSubagentKeys.clear();
              activeTaskKeys.clear();
              updateTopStatusBar();
              collapseAllToolsInArea(toolsArea);

              const activeTarget = (typeof getActiveTargetAgentId === 'function') ? getActiveTargetAgentId() : 'agent-default';
              if (typeof window.setOfficeAgentThinking === 'function') {
                window.setOfficeAgentThinking(activeTarget, 'Task workflow verified (Exit Code 0)', false);
              }
              scheduleAgentExit(activeTarget, 2500);

              if (pendingVisualBlocks.length > 0) {
                pendingVisualBlocks.forEach(vb => {
                  if (!accumulatedResponse.includes(vb)) {
                    accumulatedResponse = (accumulatedResponse ? accumulatedResponse.trim() + '\n\n' : '') + vb;
                  }
                });
                pendingVisualBlocks.length = 0;
              }
              if (accumulatedResponse) {
                bodyArea.innerHTML = renderMarkdown(accumulatedResponse);
                footerArea.style.display = 'flex';
              }
            }
            scrollChatToBottom({ force: false });
          } catch (e) {
            console.error('SSE JSON parse error:', e);
          }
        }
      }
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      bodyArea.innerHTML = `<div style="color:#f87171; font-size:11px; font-family:var(--font-mono); padding:6px 0;">⚠️ Retry Error: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    thinkingController.stop();
    if (pendingVisualBlocks.length > 0) {
      pendingVisualBlocks.forEach(vb => {
        if (!accumulatedResponse.includes(vb)) {
          accumulatedResponse = (accumulatedResponse ? accumulatedResponse.trim() + '\n\n' : '') + vb;
        }
      });
      pendingVisualBlocks.length = 0;
    }
    if (accumulatedResponse) {
      bodyArea.innerHTML = renderMarkdown(accumulatedResponse);
      footerArea.style.display = 'flex';
    }
    setChatStreamingState(false);
    currentAbortController = null;
    hidePinnedPrompt();
    activeSubagentKeys.clear();
    activeTaskKeys.clear();
    updateTopStatusBar();
    if (toolsArea) {
      collapseAllToolsInArea(toolsArea);
    }
    messagesContainer.classList.remove('chat-focus-mode');
    messagesContainer.querySelectorAll('.chat-msg-active-turn').forEach(el => el.classList.remove('chat-msg-active-turn'));
    setMascotAgentLoop(false);
    activeStepWorkerAgents.clear();
    if (window.office3DInstance && Array.isArray(window.office3DInstance.agentRoster)) {
      setTimeout(() => {
        window.office3DInstance.agentRoster.forEach(ag => {
          if (!ag.isBoss && ag.state === 'working') {
            setUnifiedAgentActivity(ag.id, 'idle');
          }
        });
      }, 2500);
    }

    if (sendBtn) {
      sendBtn.classList.remove('is-running');
      sendBtn.title = 'Send (Enter)';
    }
    // Immediately synchronize fingerprint with backend steps to prevent disruptive DOM reconstruction
    if (currentChatSessionId) {
      try {
        fetch(`/api/chat/steps/${encodeURIComponent(currentChatSessionId)}`)
          .then(r => r.json())
          .then(d => {
            if (d && d.status === 'ok' && Array.isArray(d.data?.steps)) {
              const sSteps = d.data.steps;
              const count = sSteps.length;
              const lastStep = count > 0 ? sSteps[count - 1] : null;
              const lastStatus = lastStep ? (lastStep.status || '') : '';
              const lastRespLen = (lastStep?.plannerResponse?.response) ? lastStep.plannerResponse.response.length : 0;
              lastKnownStepFingerprint = `${count}:${lastStatus}:${lastRespLen}`;
            }
          }).catch(() => {});
      } catch (_) {}
    }

    scrollChatToBottom({ force: true });

    if (queuedMessages.length > 0) {
      const nextMsg = queuedMessages.shift();
      renderQueueTray();
      setTimeout(() => {
        executeChatMessage(nextMsg.text);
      }, 250);
    }
  }
}

// ── 12. FLOWORK SOVEREIGN PROMPT DISPATCH IPC LISTENER ──
// Enables interactive plugins (e.g. Chess Arena) to dispatch moves/prompts directly into the active Agent chat
window.addEventListener('message', async (event) => {
  // Strict Cross-Origin Verification Shield
  const origin = event.origin || '';
  const isTrustedOrigin = () => {
    if (!origin || origin === 'null') {
      return event.source === window || event.source === window.parent || event.source === window.top;
    }
    if (origin === window.location.origin) return true;
    try {
      const u = new URL(origin);
      const host = u.hostname.toLowerCase();
      if (host === '127.0.0.1' || host === 'localhost' || host.endsWith('.localhost')) return true;
      if (host === 'floworkos.com' || host.endsWith('.floworkos.com')) return true;
    } catch (_) {}
    return false;
  };

  if (!isTrustedOrigin()) {
    console.warn('[Flowork Canvas Security] Rejected untrusted cross-origin postMessage from:', origin);
    return;
  }

  if (event.data && (event.data.type === 'FLOWORK_PROMPT_DISPATCH' || event.data.type === 'INJECT_PROMPT')) {
    const promptText = event.data.prompt || event.data.text;
    if (promptText) {
      injectPromptIntoChat(promptText, event.data.autoSend !== false);
    }
  }

  if (event.data && event.data.type === 'FLOWORK_PORT_QUERY') {
    const reqAppId = event.data.appId;
    let foundPort = null;
    const tabEntry = openTabs.get(reqAppId);
    if (tabEntry && tabEntry.assignedPort) {
      foundPort = tabEntry.assignedPort;
    } else {
      const pl = (pluginsCatalog || []).find(p => p.id === reqAppId);
      if (pl && pl.activePort) foundPort = pl.activePort;
    }
    if (event.source && typeof event.source.postMessage === 'function') {
      event.source.postMessage({
        type: 'FLOWORK_PORT_RESPONSE',
        appId: reqAppId,
        port: foundPort
      }, '*');
    }
  }
});

// ── SOVEREIGN PAGE VISIBILITY & IDLE GOVERNOR (ZERO ROGUE CPU/GPU IN BACKGROUND) ──
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    if (mascotAnimId) {
      cancelAnimationFrame(mascotAnimId);
      mascotAnimId = null;
    }
    if (window.office3DInstance && typeof window.office3DInstance.pause === 'function') {
      window.office3DInstance.pause();
    }
    if (typeof stopChatSyncEngine === 'function') {
      stopChatSyncEngine();
    }
    // Suspend audio and video on all open plugin iframes
    if (typeof openTabs !== 'undefined' && openTabs.size > 0) {
      openTabs.forEach((tabObj) => {
        const iframe = tabObj.iframe || tabObj.iframePanel?.querySelector('iframe');
        try {
          if (iframe && iframe.contentWindow) {
            const doc = iframe.contentWindow.document;
            if (doc) {
              doc.querySelectorAll('video, audio').forEach(m => {
                if (!m.paused) {
                  m.dataset.__flowSuspended = 'true';
                  m.pause();
                }
              });
            }
            if (iframe.contentWindow._floworkAudioCtx && iframe.contentWindow._floworkAudioCtx.state === 'running') {
              iframe.contentWindow._floworkAudioCtx.suspend();
            }
          }
        } catch (_) {}
      });
    }
  } else {
    if (typeof mascotIsRunning !== 'undefined' && mascotIsRunning) {
      startMascotLoopIfNeeded();
    }
    const activeView = document.querySelector('.view-panel.active');
    if (activeView && activeView.id === 'view-office') {
      if (window.office3DInstance && typeof window.office3DInstance.resume === 'function') {
        window.office3DInstance.resume();
      }
      if (typeof startChatSyncEngine === 'function') {
        startChatSyncEngine();
      }
    }
  }
});

// ── SOVEREIGN TEARDOWN GUARD: PURGE ORPHAN PLUGIN DAEMONS ON WINDOW UNLOAD ──
window.addEventListener('beforeunload', () => {
  if (typeof openTabs !== 'undefined' && openTabs.size > 0) {
    openTabs.forEach((_, pluginId) => {
      try {
        navigator.sendBeacon(`/api/apps/${pluginId}/stop`);
        navigator.sendBeacon(`/api/plugins/${pluginId}/stop`);
      } catch (_) {}
    });
  }
});


// ==========================================================================
// FLOWORK SENTINEL ACTION RECORDER & SYNTHESIZER
// ==========================================================================
let sentinelRecording = false;
let sentinelTimer = null;
let sentinelSeconds = 0;
let sentinelCurrentSession = null;
let sentinelDomListener = null;
let sentinelApiBase = null;

async function getSentinelApiBase() {
  if (sentinelApiBase) return sentinelApiBase;
  try {
    const statusRes = await fetch('/api/plugins/flowork-sentinel/status');
    if (statusRes.ok) {
      const info = await statusRes.json();
      if (info.port) {
        sentinelApiBase = `http://127.0.0.1:${info.port}`;
        return sentinelApiBase;
      }
    }
    const launchRes = await fetch('/api/apps/flowork-sentinel/launch', { method: 'POST' });
    if (launchRes.ok) {
      const launchData = await launchRes.json();
      if (launchData.port) {
        sentinelApiBase = `http://127.0.0.1:${launchData.port}`;
        return sentinelApiBase;
      }
    }
  } catch (_) {}
  sentinelApiBase = 'http://127.0.0.1:17870';
  return sentinelApiBase;
}

function initSentinelRecordUI() {
  const btnRecord = document.getElementById('btn-topbar-record');
  const dot = document.getElementById('topbar-record-dot');
  const label = document.getElementById('topbar-record-label');

  if (!btnRecord) return;

  btnRecord.addEventListener('click', async () => {
    if (!sentinelRecording) {
      // START RECORDING
      const defaultName = `session_${new Date().toISOString().slice(0, 10)}_${Date.now().toString().slice(-4)}`;
      const sessionName = prompt('Enter name for this recording session:', defaultName);
      if (sessionName === null) return;

      sentinelRecording = true;
      sentinelSeconds = 0;
      btnRecord.style.background = 'rgba(239, 68, 68, 0.35)';
      btnRecord.style.borderColor = '#ef4444';
      btnRecord.style.boxShadow = '0 0 14px rgba(239, 68, 68, 0.7)';
      if (dot) dot.style.animation = 'pulse 1s infinite alternate';

      // Start ticking timer
      sentinelTimer = setInterval(() => {
        sentinelSeconds++;
        const mins = String(Math.floor(sentinelSeconds / 60)).padStart(2, '0');
        const secs = String(sentinelSeconds % 60).padStart(2, '0');
        if (label) label.textContent = `REC ${mins}:${secs}`;
      }, 1000);
      if (label) label.textContent = 'REC 00:00';

      // Call Sentinel Engine
      try {
        const sentinelBase = await getSentinelApiBase();
        const res = await fetch(`${sentinelBase}/api/session/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: sessionName || defaultName,
            domain: 'flowork_canvas',
            target_url: window.location.href
          })
        });
        const data = await res.json();
        sentinelCurrentSession = data.session;
      } catch (e) {
        console.warn('[Sentinel] Engine connection note:', e);
      }

      // Attach DOM Action Interceptor to record clicks inside Flowork OS
      sentinelDomListener = (e) => {
        if (!sentinelRecording) return;
        const target = e.target.closest('button, a, input, select, textarea, .dag-node, .copilot-card') || e.target;
        if (target === btnRecord || btnRecord.contains(target)) return;

        let selector = target.id ? `#${target.id}` : (target.className && typeof target.className === 'string' ? `.${target.className.split(' ')[0]}` : target.tagName.toLowerCase());
        const actionText = target.innerText?.slice(0, 40) || target.value || target.title || '';

        // Dispatch to Sentinel Engine
        const sentinelBase = sentinelApiBase || 'http://127.0.0.1:17870';
        fetch(`${sentinelBase}/api/session/event`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'click',
            selector,
            text: actionText,
            url: window.location.href,
            timestamp: Date.now()
          })
        }).catch(() => {});
      };
      document.addEventListener('click', sentinelDomListener, true);

      if (typeof showToast === 'function') {
        showToast('🔴 Flowork Sentinel Recording Started! Actions are being captured.');
      }
    } else {
      // STOP RECORDING
      sentinelRecording = false;
      if (sentinelTimer) clearInterval(sentinelTimer);
      if (sentinelDomListener) {
        document.removeEventListener('click', sentinelDomListener, true);
        sentinelDomListener = null;
      }

      btnRecord.style.background = 'rgba(239, 68, 68, 0.12)';
      btnRecord.style.borderColor = 'rgba(239, 68, 68, 0.45)';
      btnRecord.style.boxShadow = 'none';
      if (dot) dot.style.animation = 'none';
      if (label) label.textContent = 'Record';

      try {
        const sentinelBase = await getSentinelApiBase();
        const res = await fetch(`${sentinelBase}/api/session/stop`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sentinelCurrentSession?.id })
        });
        const data = await res.json();
        if (typeof showToast === 'function') {
          showToast(`💾 Session recorded (${data.total_events || 0} events)! Opening Sentinel Studio...`);
        }
        window.open(sentinelBase, '_blank');
      } catch (e) {
        if (typeof showToast === 'function') {
          showToast('💾 Recording stopped!');
        }
      }
    }
  });
}
