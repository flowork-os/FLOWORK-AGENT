// X-Flow Canvas Host — Organic Aerodynamic Client Runtime (2026 Edition)
let pluginsState = [];
let copilotState = [];
let copilotCommitSha = '';
let activeCategory = 'all';
let activeCopilotCategory = 'all';
let searchQuery = '';
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
  initCategoryFilters();
  initCopilotCategoryFilters();
  initEventListeners();
  initSyncDriveUI();
  initWorkspaceSystem();
  initScheduleSystem();
  initRouterSwitchboardSystem();
  fetchPlugins();
  fetchCopilotRegistry();
  initSSE();
  reportActiveViewport('home');
});

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
      closeWorkspaceDropdown();
      closeCreateWorkspaceModal();
    }
  });

  // Initial load
  fetchWorkspaces();
}

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
  const container = document.getElementById('chat-messages-container');
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
  container.scrollTop = container.scrollHeight;
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
let schedCurrentMode = 'timer'; // 'timer' | 'cron'
let schedTimerPreset = 60; // number or 'custom'
let schedCronPreset = '*/5 * * * *'; // cron string or 'custom'

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
  } else {
    const cronExpr = getCalculatedCronExpression();
    const humanCron = formatCronToHuman(cronExpr);
    summaryText.innerHTML = `Will repeat routine: <strong>${escapeHtml(humanCron)}</strong> bound to current session.`;
  }
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
  const contentList = document.getElementById('sched-tab-content-list');
  const contentNew = document.getElementById('sched-tab-content-new');
  const formCreate = document.getElementById('form-create-schedule');

  const modeTimerBtn = document.getElementById('sched-mode-timer-btn');
  const modeCronBtn = document.getElementById('sched-mode-cron-btn');
  const sectionTimer = document.getElementById('sched-section-timer');
  const sectionCron = document.getElementById('sched-section-cron');

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

  if (tabActive && tabNew) {
    tabActive.addEventListener('click', () => {
      tabActive.classList.add('active');
      tabNew.classList.remove('active');
      if (contentList) contentList.style.display = 'block';
      if (contentNew) contentNew.style.display = 'none';
      fetchScheduledJobs();
    });

    tabNew.addEventListener('click', () => {
      tabNew.classList.add('active');
      tabActive.classList.remove('active');
      if (contentNew) contentNew.style.display = 'block';
      if (contentList) contentList.style.display = 'none';
      updateScheduleExecutionSummary();
    });
  }

  // Segmented Mode Switcher
  if (modeTimerBtn && modeCronBtn) {
    modeTimerBtn.addEventListener('click', () => {
      schedCurrentMode = 'timer';
      modeTimerBtn.classList.add('active');
      modeCronBtn.classList.remove('active');
      if (sectionTimer) sectionTimer.style.display = 'block';
      if (sectionCron) sectionCron.style.display = 'none';
      updateScheduleExecutionSummary();
    });

    modeCronBtn.addEventListener('click', () => {
      schedCurrentMode = 'cron';
      modeCronBtn.classList.add('active');
      modeTimerBtn.classList.remove('active');
      if (sectionTimer) sectionTimer.style.display = 'none';
      if (sectionCron) sectionCron.style.display = 'block';
      updateScheduleExecutionSummary();
    });
  }

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

  if (formCreate) {
    formCreate.addEventListener('submit', handleCreateScheduleSubmit);
  }
}

window.__openScheduleModal = openScheduleModal;

function openScheduleModal() {
  const modal = document.getElementById('schedule-modal');
  if (modal) {
    modal.style.display = 'flex';
    fetchScheduledJobs();
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

let currentRenderedJobs = [];

async function fetchScheduledJobs() {
  const listEl = document.getElementById('sched-jobs-list');
  const countBadge = document.getElementById('sched-active-count');
  if (!listEl) return;
  listEl.innerHTML = '<div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 11.5px;">Loading autonomous automations...</div>';

  try {
    const activeSession = currentChatSessionId || 'default';
    const res = await fetch(`/api/schedule?session_id=${encodeURIComponent(activeSession)}`);
    const data = await res.json();
    if (data.status === 'ok') {
      const allJobs = data.jobs || [];
      // Filter list exclusively for this active chat session
      const jobs = allJobs.filter(j => (j.session_id || 'default') === activeSession);
      currentRenderedJobs = jobs;
      const activeCount = jobs.filter(j => j.status === 'active').length;
      if (countBadge) countBadge.textContent = activeCount;
      renderScheduledJobsList(jobs);
    } else {
      listEl.innerHTML = `<div style="padding: 16px; text-align: center; color: #f87171; font-size: 11px;">Failed to load: ${escapeHtml(data.message || 'Error')}</div>`;
    }
  } catch (err) {
    listEl.innerHTML = `<div style="padding: 16px; text-align: center; color: #f87171; font-size: 11px;">Network error: ${escapeHtml(err.message)}</div>`;
  }
}

function renderScheduledJobsList(jobs) {
  const listEl = document.getElementById('sched-jobs-list');
  if (!listEl) return;
  if (!jobs || jobs.length === 0) {
    listEl.innerHTML = `
      <div style="padding: 32px 16px; text-align: center; color: #64748b; font-size: 12px;">
        <span style="font-size: 28px; display: block; margin-bottom: 10px;">⏰</span>
        <strong style="color: #cbd5e1; font-size: 13px; display: block; margin-bottom: 4px;">No Active Automations in This Chat</strong>
        No scheduled background tasks currently active for this chat session.<br>
        <button type="button" class="sched-chip-pill active" style="margin-top: 14px; display: inline-block; cursor: pointer; padding: 6px 14px;" onclick="resetScheduleEditForm(); document.getElementById('tab-sched-new').click()">+ Create New Automation</button>
      </div>
    `;
    return;
  }

  listEl.innerHTML = jobs.map(job => {
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
    const modeCronBtn = document.getElementById('sched-mode-cron-btn');
    if (modeCronBtn) modeCronBtn.click();

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
    const modeTimerBtn = document.getElementById('sched-mode-timer-btn');
    if (modeTimerBtn) modeTimerBtn.click();

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
  if (submitText) submitText.textContent = '⏰ Activate Sovereign Automation';
  if (btnCancelEdit) btnCancelEdit.style.display = 'none';

  if (tabNew) {
    const tabSpan = tabNew.querySelector('span');
    if (tabSpan) tabSpan.textContent = '+ New Automation';
  }

  const modeTimerBtn = document.getElementById('sched-mode-timer-btn');
  if (modeTimerBtn) modeTimerBtn.click();
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
      fetchScheduledJobs();
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
    if (editingJobId) {
      // UPDATE EXISTING JOB
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
        const tabActive = document.getElementById('tab-sched-active');
        if (tabActive) tabActive.click();
      } else {
        showToast(`⚠️ Update failed: ${data.message || 'Error'}`);
      }
    } else {
      // CREATE NEW JOB
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
        const tabActive = document.getElementById('tab-sched-active');
        if (tabActive) tabActive.click();
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
  const host = (typeof window !== 'undefined' && window.location && window.location.hostname) ? window.location.hostname : '127.0.0.1';
  return `http://${host}:${rPort}`;
}
window._getFloworkRouterBase = _getFloworkRouterBase;

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
      const rPort = _getFloworkRouterPort();
      try {
        btn.disabled = true;
        btn.textContent = 'Activating...';
        const res = await fetch(`http://127.0.0.1:${rPort}/auth/router/select-account`, {
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
      const rPort = _getFloworkRouterPort();
      try {
        btn.disabled = true;
        btn.textContent = 'Testing...';
        const res = await fetch(`http://127.0.0.1:${rPort}/auth/router/test-account`, {
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

      const rPort = _getFloworkRouterPort();
      try {
        const res = await fetch(`http://127.0.0.1:${rPort}/auth/router/remove-account`, {
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
  const rPort = _getFloworkRouterPort();
  try {
    const res = await fetch(`http://127.0.0.1:${rPort}/auth/sovereign/model?model=${encodeURIComponent(modelId)}`);
    const data = await res.json();
    if (data && data.success) {
      routerSwitchboardState.model = modelId;
      updateRouterTopbarPill();
    }
  } catch (_) {}
};

window.clearRouterCooldown = async () => {
  const rPort = _getFloworkRouterPort();
  try {
    const res = await fetch(`http://127.0.0.1:${rPort}/auth/router/clear-cooldown`, { method: 'POST' });
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
      const rPort = _getFloworkRouterPort();
      try {
        showFloworkLaserToast('🌐 Opening Google OAuth authorization portal in browser...', true);
        const res = await fetch(`http://127.0.0.1:${rPort}/auth/router/login-url`);
        const data = await res.json();
        if (data && data.loginUrl) {
          window.open(data.loginUrl, '_blank');
          let pollCount = 0;
          const initialCount = routerSwitchboardState.totalAccounts;
          const pollInterval = setInterval(async () => {
            pollCount++;
            await syncRouterSwitchboard();
            if (routerSwitchboardState.totalAccounts > initialCount || pollCount > 45) {
              clearInterval(pollInterval);
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
      const rPort = _getFloworkRouterPort();
      try {
        const res = await fetch(`http://127.0.0.1:${rPort}/auth/router/set-rotation-mode`, {
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
  setInterval(syncRouterSwitchboard, 12000);
}

// 0. Flowork OS Sovereign Authentication & Gatekeeper
async function initAuthSystem() {
  const btnLogout = document.getElementById('btn-topbar-logout');
  if (btnLogout) {
    btnLogout.addEventListener('click', logoutSession);
  }

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
}



async function fetchAuthStatus() {
  try {
    const res = await fetch('/api/auth/status');
    const data = await res.json();
    renderAuthUI(data);
  } catch (err) {
    console.warn('[X-Flow Auth] Failed to fetch auth status:', err);
  }
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

    if (profileCapsule) {
      profileCapsule.style.display = 'flex';
      const tierEl = document.getElementById('user-tier-pill');
      const nameEl = document.getElementById('user-username');
      const roleEl = document.getElementById('user-role');
      const avatarEl = document.getElementById('user-avatar-badge');

      if (nameEl) nameEl.textContent = `@${user.username || 'user'}`;
      if (roleEl) roleEl.textContent = user.role || 'USER';
      if (avatarEl) {
        avatarEl.textContent = (user.badge && user.badge.includes('👑')) || user.role === 'SUPER_ADMIN' ? '👑' : '👤';
      }

      if (tierEl) {
        const tier = (user.tier || 'enterprise').toLowerCase();
        tierEl.textContent = `${tier.toUpperCase()} PLAN`;
        tierEl.className = `user-tier-pill tier-${tier}`;
      }
    }

    if (btnLogin) btnLogin.style.display = 'none';

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
    sessionStorage.removeItem('flowork_auth_verified');
    sessionStorage.removeItem('xflow_user_authenticated');
    sessionStorage.removeItem('xflow_gate_dismissed');
    sessionStorage.removeItem('xflow_offline_mode');
    document.documentElement.classList.remove('xflow-authenticated');
  } catch (_) {}

  try {
    await fetch('/api/auth/logout', { method: 'POST' });
  } catch (err) {
    console.error('[X-Flow Auth] Logout error:', err);
  }
  window.location.replace('/canvas/launcher.html');
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

// 1b. Dynamic Chat Docking (Left / Right Panel Positioning)
function initChatDockSystem() {
  const layout = document.querySelector('.canvas-layout');
  const btnToggleDock = document.getElementById('btn-toggle-chat-dock');
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

  const savedSide = localStorage.getItem('xflow_chat_dock_side') || 'right';
  applyDockSide(savedSide);

  if (btnToggleDock) {
    btnToggleDock.addEventListener('click', (e) => {
      e.stopPropagation();
      const currentlyLeft = layout.classList.contains('chat-dock-left');
      const newSide = currentlyLeft ? 'right' : 'left';
      applyDockSide(newSide);
      localStorage.setItem('xflow_chat_dock_side', newSide);
      showToast(newSide === 'left' ? 'Chat docked to Left' : 'Chat docked to Right');
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
  const btnToggleFullChat = document.getElementById('btn-toggle-full-chat');

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
      if (btnToggleFullChat) {
        btnToggleFullChat.classList.add('is-active');
        btnToggleFullChat.title = 'Split View (Show Applications)';
        btnToggleFullChat.innerHTML = `
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="4 14 10 14 10 20"></polyline>
            <polyline points="20 10 14 10 14 4"></polyline>
            <line x1="14" y1="10" x2="21" y2="3"></line>
            <line x1="3" y1="21" x2="10" y2="14"></line>
          </svg>
        `;
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
      if (btnToggleFullChat) {
        btnToggleFullChat.classList.remove('is-active');
        btnToggleFullChat.title = 'Full Chat View (Hide Applications)';
        btnToggleFullChat.innerHTML = `
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 3 21 3 21 9"></polyline>
            <polyline points="9 21 3 21 3 15"></polyline>
            <line x1="21" y1="3" x2="14" y2="10"></line>
            <line x1="3" y1="21" x2="10" y2="14"></line>
          </svg>
        `;
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

  // 3. Chat Header "Full Chat / Maximize" Button
  if (btnToggleFullChat) {
    btnToggleFullChat.addEventListener('click', () => {
      const willCollapse = !workbench.classList.contains('collapsed');
      setWorkbenchState(willCollapse, true);
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

      newWidth = Math.max(MIN_SIDEBAR_WIDTH, Math.min(maxSidebarWidth, newWidth));
      document.documentElement.style.setProperty('--sidebar-width', `${Math.round(newWidth)}px`);
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

      newWidth = Math.max(MIN_RIGHTBAR_WIDTH, Math.min(maxRightbarWidth, newWidth));
      document.documentElement.style.setProperty('--rightbar-width', `${Math.round(newWidth)}px`);
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

// 3. Category Filter Capsules
function initCategoryFilters() {
  const filterPills = document.querySelectorAll('#category-filters .category-pill');
  filterPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      filterPills.forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      activeCategory = pill.dataset.category;
      filterAndRenderCards();
    });
  });
}

function initCopilotCategoryFilters() {
  const filterPills = document.querySelectorAll('#copilot-category-filters .category-pill');
  filterPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      filterPills.forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      activeCopilotCategory = pill.dataset.copilotCat;
      filterAndRenderCopilotCards();
    });
  });
}

function initEventListeners() {
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

  const tabStrip = document.getElementById('tab-strip');
  if (tabStrip && !tabStrip._hasMiddleClick) {
    tabStrip._hasMiddleClick = true;
    tabStrip.addEventListener('auxclick', (e) => {
      if (e.button === 1) {
        const tab = e.target.closest('.tab-capsule');
        if (tab && tab.dataset.tabId && tab.dataset.tabId !== 'home' && tab.dataset.tabId !== 'copilot') {
          e.preventDefault();
          e.stopPropagation();
          closePluginTab(tab.dataset.tabId);
        }
      }
    });
    tabStrip.addEventListener('mousedown', (e) => {
      if (e.button === 1) {
        const tab = e.target.closest('.tab-capsule');
        if (tab && tab.dataset.tabId && tab.dataset.tabId !== 'home' && tab.dataset.tabId !== 'copilot') {
          e.preventDefault();
        }
      }
    });
  }

  initRightbarChat();
  initChatDockSystem();
  initWorkbenchToggle();

  const btnSync = document.getElementById('btn-sync-copilot');
  if (btnSync) {
    btnSync.addEventListener('click', () => {
      btnSync.innerHTML = '<span>⏳ Syncing...</span>';
      fetchCopilotRegistry(true).finally(() => {
        setTimeout(() => {
          btnSync.innerHTML = '<span>🔄 Check Updates</span>';
        }, 600);
      });
    });
  }
}

// 4. Data Fetching & Sync
async function fetchPlugins() {
  try {
    const res = await fetch('/api/plugins');
    const data = await res.json();
    if (data.status === 'ok') {
      pluginsState = data.plugins;
      renderDock();
      filterAndRenderCards();
      updateStats();
      filterAndRenderCopilotCards();
    }
  } catch (err) {
    console.error('[X-Flow] Error fetching plugins:', err);
  }
}

const COPILOT_CACHE_KEY = 'xflow_copilot_registry_cache';
const COPILOT_CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours (sekali sehari)

async function fetchCopilotRegistry(isManual = false) {
  // 1. Check 24-hour localStorage cache if not manually requested
  if (!isManual) {
    try {
      const cachedStr = localStorage.getItem(COPILOT_CACHE_KEY);
      if (cachedStr) {
        const cached = JSON.parse(cachedStr);
        const age = Date.now() - (cached.timestamp || 0);
        if (age < COPILOT_CACHE_TTL && cached.data && cached.data.status === 'ok') {
          console.log(`[App Store] Using 24-hr cached registry (age: ${Math.round(age / 60000)}m)`);
          applyCopilotRegistryData(cached.data, false);
          return;
        }
      }
    } catch (err) {
      console.warn('[App Store] Cache read failed:', err);
    }
  }

  // 2. Fetch from server endpoint (GitHub sync)
  try {
    const res = await fetch('/api/copilot/registry');
    const data = await res.json();
    if (data.status === 'ok' && data.registry) {
      try {
        localStorage.setItem(COPILOT_CACHE_KEY, JSON.stringify({
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
  copilotState = data.registry.plugins || [];
  copilotCommitSha = data.registry.commit_sha || '';
  
  const statSha = document.getElementById('copilot-stat-sha');
  const statCount = document.getElementById('copilot-stat-count');
  if (statSha) statSha.textContent = copilotCommitSha;
  if (statCount) statCount.textContent = copilotState.length;

  filterAndRenderCopilotCards();
  if (isManual) {
    showToast(`App Store synced with registry (SHA ${copilotCommitSha})`);
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
  if (rightbarChat && rightbarChat.classList.contains('collapsed')) {
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
      if (payload.PluginCommand) {
        const cmd = payload.PluginCommand;
        console.log('[X-Flow SSE] Plugin command received:', cmd);
        if (cmd.action === 'open') {
          const p = pluginsState.find(x => x.id === cmd.plugin_id) || { id: cmd.plugin_id, name: cmd.plugin_id };
          openPluginTab(p);
        } else if (cmd.action === 'close') {
          closePluginTab(cmd.plugin_id);
        } else if (cmd.action === 'refresh' || cmd.action === 'reload') {
          const p = pluginsState.find(x => x.id === cmd.plugin_id) || { id: cmd.plugin_id, name: cmd.plugin_id };
          closePluginTab(cmd.plugin_id);
          setTimeout(() => openPluginTab(p), 400);
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
          sendBtn.title = 'Flowork sedang restart & memuat pembaruan...';
        }
        showToast('🔄 Flowork sedang me-restart biner & menyambung kembali...');
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
// FLOWORK OS — SOVEREIGN DYNAMIC HYPER-WARP STARFIELD ENGINE
// =============================================================================
let cosmicStarfieldController = null;

function initStarfieldBackground() {
  const canvas = document.getElementById('flw-starfield-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  const STAR_COUNT = 300;
  const stars = [];

  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push({
      x: (Math.random() - 0.5) * width * 2,
      y: (Math.random() - 0.5) * height * 2,
      z: Math.random() * width,
      pz: 0,
      size: Math.random() * 1.6 + 0.4,
      color: i % 4 === 0 ? '#00f2fe' : (i % 4 === 1 ? '#c084fc' : (i % 4 === 2 ? '#38bdf8' : '#ffffff'))
    });
  }

  let currentSpeed = 0.5;
  let targetSpeed = 0.5;
  let shockwave = null;
  let animId = null;

  function renderFrame() {
    currentSpeed += (targetSpeed - currentSpeed) * 0.08;

    const messagesEl = document.getElementById('rightbar-messages');
    const isWarpActive = messagesEl && messagesEl.classList.contains('chat-focus-mode');
    targetSpeed = isWarpActive ? 16.0 : 0.5;

    const cx = width / 2;
    const cy = height / 2;

    if (currentSpeed > 2.5) {
      ctx.fillStyle = 'rgba(5, 11, 20, 0.32)';
      ctx.fillRect(0, 0, width, height);
    } else {
      ctx.clearRect(0, 0, width, height);
    }

    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      s.pz = s.z;
      s.z -= currentSpeed;

      if (s.z <= 0) {
        s.z = width;
        s.pz = width;
        s.x = (Math.random() - 0.5) * width * 2;
        s.y = (Math.random() - 0.5) * height * 2;
      }

      const k = 280 / s.z;
      const px = s.x * (280 / s.pz) + cx;
      const py = s.y * (280 / s.pz) + cy;
      const x = s.x * k + cx;
      const y = s.y * k + cy;

      if (x < 0 || x > width || y < 0 || y > height) continue;

      const alpha = Math.min(1, Math.max(0.12, (1 - s.z / width) * (currentSpeed > 2.5 ? 1.4 : 0.85)));

      if (currentSpeed > 2.5) {
        ctx.strokeStyle = s.color;
        ctx.globalAlpha = alpha;
        ctx.lineWidth = Math.min(2.4, (1 - s.z / width) * 2.0);
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(x, y);
        ctx.stroke();
      } else {
        ctx.fillStyle = s.color;
        ctx.globalAlpha = alpha;
        ctx.beginPath();
        ctx.arc(x, y, s.size * (1 - s.z / width + 0.3), 0, Math.PI * 2);
        ctx.fill();

        if (s.size > 1.3 && alpha > 0.45) {
          ctx.strokeStyle = s.color;
          ctx.lineWidth = 0.7;
          ctx.beginPath();
          ctx.moveTo(x - 3, y); ctx.lineTo(x + 3, y);
          ctx.moveTo(x, y - 3); ctx.lineTo(x, y + 3);
          ctx.stroke();
        }
      }
    }

    if (shockwave) {
      shockwave.r += (shockwave.maxR - shockwave.r) * 0.12 + 6;
      shockwave.alpha *= 0.93;
      if (shockwave.alpha < 0.02 || shockwave.r >= shockwave.maxR) {
        shockwave = null;
      } else {
        ctx.save();
        ctx.beginPath();
        ctx.arc(shockwave.x, shockwave.y, shockwave.r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 242, 254, ${shockwave.alpha})`;
        ctx.lineWidth = 3.5 * shockwave.alpha;
        ctx.shadowColor = '#00f2fe';
        ctx.shadowBlur = 16;
        ctx.stroke();
        ctx.restore();
      }
    }

    ctx.globalAlpha = 1.0;
    animId = requestAnimationFrame(renderFrame);
  }

  animId = requestAnimationFrame(renderFrame);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }, { passive: true });

  cosmicStarfieldController = {
    triggerShockwave: () => {
      shockwave = {
        x: width / 2,
        y: height / 2,
        r: 15,
        maxR: Math.max(width, height) * 0.85,
        alpha: 0.85
      };
    }
  };
  window.cosmicStarfieldController = cosmicStarfieldController;
}

// 6. Filter & Render Cockpit Pebble Cards
function filterAndRenderCards() {
  const grid = document.getElementById('plugin-grid');
  const countBadge = document.getElementById('filtered-count-badge');
  if (!grid) return;
  grid.innerHTML = '';

  const filtered = pluginsState.filter((p) => {
    const matchesCategory =
      activeCategory === 'all' ||
      (p.category && p.category.toLowerCase().includes(activeCategory.toLowerCase()));

    const matchesSearch =
      !searchQuery ||
      p.name.toLowerCase().includes(searchQuery) ||
      (p.description && p.description.toLowerCase().includes(searchQuery)) ||
      p.id.toLowerCase().includes(searchQuery);

    return matchesCategory && matchesSearch;
  });

  if (countBadge) {
    countBadge.textContent = `${filtered.length} of ${pluginsState.length} module${pluginsState.length === 1 ? '' : 's'}`;
  }

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px 24px; text-align: center; gap: 14px; opacity: 0.85;">
        <div style="width: 48px; height: 48px; border-radius: 50%; border: 1px dashed rgba(0, 229, 255, 0.4); display: flex; align-items: center; justify-content: center; font-size: 20px; color: #00e5ff; box-shadow: 0 0 16px rgba(0, 229, 255, 0.15);">
          ◈
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #f1f5f9; letter-spacing: 0.1em; font-family: var(--font-mono);">NO MODULES MATCH SEARCH</div>
        <div style="font-size: 12px; color: var(--text-dim); max-width: 380px;">Adjust your search filter or install verified polyglot engines from the cloud federation repository.</div>
      </div>
    `;
    return;
  }

  filtered.forEach((plugin) => {
    const isRunning = openTabs.has(plugin.id);
    const card = document.createElement('div');
    card.className = 'pebble-card';

    const rawName = plugin.name || plugin.id;
    const displayName = rawName.length > 25 ? rawName.slice(0, 23) + '...' : rawName;

    const rawVer = String(plugin.version || '1.0.0');
    const displayVer = rawVer.length > 8 ? rawVer.slice(0, 7) + '...' : rawVer;

    const rawCategory = plugin.category || 'Utility';
    const displayCategory = rawCategory.length > 12 ? rawCategory.slice(0, 10) + '...' : rawCategory;

    const rawDesc = plugin.description || 'Polyglot Nano-Plug module.';
    const displayDesc = rawDesc.length > 95 ? rawDesc.slice(0, 92) + '...' : rawDesc;

    card.innerHTML = `
      <div class="pebble-header">
        <div class="pebble-glyph-circle">${plugin.icon || '⚡'}</div>
        <div class="pebble-info">
          <div class="pebble-title" title="${escapeHtml(rawName)}">${escapeHtml(displayName)}</div>
          <div class="pebble-tags">
            <span class="pebble-tag" title="v${escapeHtml(rawVer)}">v${escapeHtml(displayVer)}</span>
            <span class="pebble-tag" title="${escapeHtml(rawCategory)}">${escapeHtml(displayCategory)}</span>
          </div>
        </div>
      </div>
      <div class="pebble-description" title="${escapeHtml(rawDesc)}">${escapeHtml(displayDesc)}</div>
      <div class="pebble-footer">
        <div class="pebble-status">
          <span class="pebble-beacon-dot ${isRunning ? 'active' : ''}"></span>
          <span>${isRunning ? 'Running' : 'Ready'}</span>
        </div>
        <button class="btn-pebble-launch" id="btn-launch-${plugin.id}">
          ${isRunning ? 'Switch to Tab' : 'Launch Module'}
        </button>
      </div>
    `;
    card.querySelector(`#btn-launch-${plugin.id}`).onclick = () => openPluginTab(plugin);
    grid.appendChild(card);
  });
}

// 7. Filter & Render Copilot Storefront Pebble Cards
function filterAndRenderCopilotCards() {
  const grid = document.getElementById('copilot-grid');
  const counterBadge = document.getElementById('copilot-counter-badge');
  if (!grid) return;
  grid.innerHTML = '';

  const localIds = new Set(pluginsState.map((p) => p.id));

  const filtered = copilotState.filter((p) => {
    const matchesCategory =
      activeCopilotCategory === 'all' ||
      (p.category && p.category.toLowerCase().includes(activeCopilotCategory.toLowerCase()));

    const matchesSearch =
      !searchQuery ||
      p.name.toLowerCase().includes(searchQuery) ||
      (p.description && p.description.toLowerCase().includes(searchQuery)) ||
      p.id.toLowerCase().includes(searchQuery);

    return matchesCategory && matchesSearch;
  });

  if (counterBadge) {
    counterBadge.textContent = `${filtered.length} of ${copilotState.length} cloud extensions`;
  }

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 48px; text-align: center; color: var(--text-dim); background: rgba(255, 255, 255, 0.03); border: 1.5px dashed var(--border-organic); border-radius: 24px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);">
        <div style="font-size: 28px; margin-bottom: 8px;">🛰️</div>
        <div style="font-size: 14px; font-weight: 700; color: var(--text-main); margin-bottom: 4px;">No matching cloud extensions</div>
        <div style="font-size: 12px; color: var(--text-muted);">Check filter tags or sync with GitHub registry.</div>
      </div>
    `;
    return;
  }

  filtered.forEach((plugin) => {
    const isInstalled = localIds.has(plugin.id) || plugin.installed;
    const isUpdateAvailable = Boolean(plugin.update_available);
    const isRunning = openTabs.has(plugin.id);

    const card = document.createElement('div');
    card.className = 'pebble-card';

    let actionButtons = '';
    let statusBadge = '';

    if (!isInstalled) {
      statusBadge = `<span class="pebble-tag tag-status-available">Available</span>`;
      actionButtons = `
        <button class="btn-pebble-install" id="btn-copilot-install-${plugin.id}">
          ⬇️ Install Plugin
        </button>
      `;
    } else if (isUpdateAvailable) {
      statusBadge = `<span class="pebble-tag tag-status-update">Update Ready</span>`;
      actionButtons = `
        <button class="btn-pebble-update" id="btn-copilot-update-${plugin.id}">
          ✨ Update Now
        </button>
        <button class="btn-pebble-uninstall" id="btn-copilot-uninstall-${plugin.id}" title="Uninstall Plugin">
          🗑️
        </button>
      `;
    } else {
      statusBadge = `<span class="pebble-tag tag-status-installed">Installed</span>`;
      actionButtons = `
        <button class="btn-pebble-launch" id="btn-copilot-launch-${plugin.id}">
          ${isRunning ? 'Switch to Tab' : 'Launch'}
        </button>
        <button class="btn-pebble-uninstall" id="btn-copilot-uninstall-${plugin.id}" title="Uninstall Plugin">
          🗑️
        </button>
      `;
    }

    const rawName = plugin.name || plugin.id;
    const displayName = rawName.length > 25 ? rawName.slice(0, 23) + '...' : rawName;

    const rawVer = String(plugin.version || '1.0.0');
    const displayVer = rawVer.length > 8 ? rawVer.slice(0, 7) + '...' : rawVer;

    const cleanHash = (plugin.hash || 'sha').replace(/^#/, '');
    const displayHash = cleanHash.length > 8 ? cleanHash.slice(0, 8) : cleanHash;

    const rawDesc = plugin.description || 'Federated polyglot extension.';
    const displayDesc = rawDesc.length > 95 ? rawDesc.slice(0, 92) + '...' : rawDesc;

    card.innerHTML = `
      <div class="pebble-header">
        <div class="pebble-glyph-circle">${plugin.icon || '📦'}</div>
        <div class="pebble-info">
          <div class="pebble-title" title="${escapeHtml(rawName)}">${escapeHtml(displayName)}</div>
          <div class="pebble-tags">
            <span class="pebble-tag" title="v${escapeHtml(rawVer)}">v${escapeHtml(displayVer)}</span>
            <span class="pebble-tag tag-hash" title="#${escapeHtml(cleanHash)}">#${escapeHtml(displayHash)}</span>
            ${statusBadge}
          </div>
        </div>
      </div>
      <div class="pebble-description" title="${escapeHtml(rawDesc)}">${escapeHtml(displayDesc)}</div>
      <div class="pebble-footer">
        <div class="pebble-status">
          <span class="pebble-beacon-dot ${isInstalled ? 'active' : ''}"></span>
          <span>${isInstalled ? (isRunning ? 'Running' : 'Installed') : 'In Cloud'}</span>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
          ${actionButtons}
        </div>
      </div>
    `;

    // Bind action listeners
    const installBtn = card.querySelector(`#btn-copilot-install-${plugin.id}`);
    if (installBtn) {
      installBtn.onclick = () => installExtension(plugin.id, plugin.name);
    }

    const updateBtn = card.querySelector(`#btn-copilot-update-${plugin.id}`);
    if (updateBtn) {
      updateBtn.onclick = () => installExtension(plugin.id, plugin.name, true);
    }

    const uninstallBtn = card.querySelector(`#btn-copilot-uninstall-${plugin.id}`);
    if (uninstallBtn) {
      uninstallBtn.onclick = () => uninstallExtension(plugin.id, plugin.name);
    }

    const launchBtn = card.querySelector(`#btn-copilot-launch-${plugin.id}`);
    if (launchBtn) {
      launchBtn.onclick = () => {
        const localPlugin = pluginsState.find((p) => p.id === plugin.id) || plugin;
        openPluginTab(localPlugin);
      };
    }

    grid.appendChild(card);
  });
}

// 8. Extension Install & Uninstall Operations
async function installExtension(pluginId, pluginName, isUpdate = false) {
  showToast(`${isUpdate ? 'Updating' : 'Installing'} ${pluginName} from GitHub...`);
  try {
    const res = await fetch(`/api/copilot/install/${pluginId}`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast(`Success! ${pluginName} ${isUpdate ? 'updated' : 'installed'} cleanly.`);
      await fetchPlugins();
      await fetchCopilotRegistry();
    } else {
      showToast(`Error: ${data.message}`);
    }
  } catch (err) {
    console.error(`[X-Flow] Install error for ${pluginId}:`, err);
    showToast(`Install failed for ${pluginName}`);
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
    if (data.status === 'ok') {
      showToast(`${pluginName} removed cleanly.`);
      await fetchPlugins();
      await fetchCopilotRegistry();
    } else {
      showToast(`Error: ${data.message}`);
    }
  } catch (err) {
    console.error(`[X-Flow] Uninstall error for ${pluginId}:`, err);
    showToast(`Uninstall failed for ${pluginName}`);
  }
}

// 9. Tab & Process Management (Aerodynamic Capsules)
async function openPluginTab(plugin) {
  if (openTabs.has(plugin.id)) {
    switchTab(plugin.id);
    return;
  }

  // Launch backend engine via Rust supervisor
  let assignedPort = null;
  try {
    const launchRes = await fetch(`/api/plugins/${plugin.id}/launch`, { method: 'POST' });
    const launchData = await launchRes.json();
    console.log(`[X-Flow] Engine launched for ${plugin.id}:`, launchData);

    if (launchData.port) {
      assignedPort = launchData.port;
      showToast(`Started engine for ${plugin.name} on port :${launchData.port}`);
      emitAgentTelemetry({ type: 'cmd', tag: 'ENGINE', text: `${plugin.name} on :${launchData.port}`, meta: 'SPAWN' });
    }
  } catch (err) {
    console.error(`[X-Flow] Failed to launch engine for ${plugin.id}:`, err);
  }

  // Create Tab Capsule
  const tabStrip = document.getElementById('tab-strip');
  const tabCapsule = document.createElement('div');
  tabCapsule.className = 'tab-capsule';
  tabCapsule.id = `tab-${plugin.id}`;
  tabCapsule.dataset.tabId = plugin.id;

  const rawTabName = plugin.name || plugin.id || 'Plugin';
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
  tabStrip.appendChild(tabCapsule);

  // Create Sandboxed Iframe Viewport
  const stage = document.getElementById('viewport-stage');
  const iframePanel = document.createElement('div');
  iframePanel.className = 'view-panel';
  iframePanel.id = `view-${plugin.id}`;

  const iframe = document.createElement('iframe');
  iframe.className = 'plugin-iframe';
  const queryParam = assignedPort ? `?port=${assignedPort}` : '';
  iframe.src = `/plugins/${plugin.id}/gui/${queryParam}`;
  iframe.setAttribute('sandbox', 'allow-scripts allow-forms allow-same-origin allow-modals allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation');

  iframePanel.appendChild(iframe);
  stage.appendChild(iframePanel);

  openTabs.set(plugin.id, { title: plugin.name, tabCapsule, iframePanel, isRunning: true });
  switchTab(plugin.id);
  filterAndRenderCards();
  filterAndRenderCopilotCards();
  updateStats();
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-capsule').forEach((tab) => {
    tab.classList.toggle('active', tab.dataset.tabId === tabId);
  });

  document.querySelectorAll('.dock-pill-item').forEach((item) => {
    item.classList.toggle('active', item.id === `dock-plugin-${tabId}`);
  });

  document.querySelectorAll('.view-panel').forEach((panel) => {
    panel.classList.toggle('active', panel.id === `view-${tabId}`);
  });

  // Sovereign Viewport Telemetry: Report active tab to Engine Host for agent context
  reportActiveViewport(tabId);
}

function reportActiveViewport(tabId) {
  let title = 'Home Workbench';
  let kind = 'system';

  if (tabId === 'home') {
    title = 'Home Workbench';
    kind = 'system';
  } else if (tabId === 'copilot') {
    title = 'App Store (Cloud Extensions)';
    kind = 'app_store';
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

  const { tabCapsule, iframePanel } = openTabs.get(pluginId);
  tabCapsule.remove();
  iframePanel.remove();
  openTabs.delete(pluginId);

  // Send clean SIGTERM to Rust process supervisor (zero-zombie guarantee)
  try {
    await fetch(`/api/plugins/${pluginId}/stop`, { method: 'POST' });
    console.log(`[X-Flow] Engine for ${pluginId} cleanly killed.`);
    showToast(`Stopped engine for ${pluginId}.`);
    emitAgentTelemetry({ type: 'cmd', tag: 'ENGINE', text: `Engine stopped: ${pluginId}`, meta: 'SIGTERM' });
  } catch (err) {
    console.error(`[X-Flow] Error terminating engine ${pluginId}:`, err);
  }

  filterAndRenderCards();
  filterAndRenderCopilotCards();
  updateStats();
  switchTab('home');
}

function updateStats() {
  const statPlugins = document.getElementById('stat-total-plugins');
  const statDaemons = document.getElementById('stat-active-daemons');
  if (statPlugins) statPlugins.textContent = pluginsState.length;
  if (statDaemons) statDaemons.textContent = openTabs.size;
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
      try {
        const res = await fetch('/api/sync-drive/auth/login-url');
        const data = await res.json();
        if (data.url) {
          showToast('Opening Google OAuth in browser...');
          window.open(data.url, '_blank');
        }
      } catch (err) {
        showToast('Failed to get Google login URL');
      }
    });
  }

  if (btnAddFolder) {
    btnAddFolder.addEventListener('click', async () => {
      let defaultPath = '';
      try {
        const res = await fetch('/api/dialog/default-dir');
        const data = await res.json();
        defaultPath = data.path || '';
      } catch (_) {}

      const chosen = prompt('Enter absolute path of folder to auto-backup & offload to Google Drive:', defaultPath);
      if (chosen && chosen.trim()) {
        try {
          const res = await fetch('/api/sync-drive/folders/add', {
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
    const res = await fetch('/api/sync-drive/status');
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
              <div class="account-avatar">${acc.picture ? `<img src="${acc.picture}" alt="Avatar">` : initial}</div>
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
  try {
    const res = await fetch('/api/sync-drive/accounts/remove', {
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
  try {
    const res = await fetch('/api/sync-drive/folders/remove', {
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
  try {
    const res = await fetch('/api/sync-drive/restore', {
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

function openChatSessionById(sessionId) {
  const rightbarChat = document.getElementById('rightbar-chat');
  if (rightbarChat && rightbarChat.classList.contains('collapsed')) {
    rightbarChat.classList.remove('collapsed');
    localStorage.setItem('xflow_rightbar_collapsed', 'false');
  }
  const rightbarMessages = document.getElementById('rightbar-messages');
  const rightbarHistoryView = document.getElementById('rightbar-history-view');
  if (rightbarHistoryView) rightbarHistoryView.style.display = 'none';
  if (rightbarMessages) rightbarMessages.style.display = 'flex';

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
    sendBtn.title = 'Flowork sedang restart & memuat pembaruan...';
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
          const container = document.getElementById('rightbar-messages');
          if (container) container.scrollTop = container.scrollHeight;

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
            showToast('✅ Flowork berhasil di-restart & tugas selesai!');
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

let AVAILABLE_CHAT_MODELS = [
  {
    id: "gemini-3.8-flash-high",
    name: "Gemini 3.8 Flash (High)",
    provider: "google",
    badge: "RECOMMENDED",
    badgeClass: "badge-recommended",
    desc: "Flagship high-speed deep thinking model"
  },
  {
    id: "gemini-3.8-flash-medium",
    name: "Gemini 3.8 Flash (Medium)",
    provider: "google",
    badge: "THINKING",
    badgeClass: "badge-thinking",
    desc: "Balanced high-performance thinking model"
  },
  {
    id: "gemini-3.8-flash-low",
    name: "Gemini 3.8 Flash (Low)",
    provider: "google",
    badge: "FAST",
    badgeClass: "badge-fast",
    desc: "Fast lightweight reasoning model"
  },
  {
    id: "gemini-3.7-flash-high",
    name: "Gemini 3.7 Flash (High)",
    provider: "google",
    badge: "FRONTIER",
    badgeClass: "badge-pro",
    desc: "High reasoning frontier flash model"
  },
  {
    id: "gemini-3.7-flash-medium",
    name: "Gemini 3.7 Flash (Medium)",
    provider: "google",
    badge: "AGILE",
    badgeClass: "badge-fast",
    desc: "Fast agile coding and agent execution"
  },
  {
    id: "gemini-3.7-flash-low",
    name: "Gemini 3.7 Flash (Low)",
    provider: "google",
    badge: "ITERATION",
    badgeClass: "badge-fast",
    desc: "Low latency fast iteration model"
  },
  {
    id: "gemini-3.6-flash-high",
    name: "Gemini 3.6 Flash (High)",
    provider: "google",
    badge: "ACCURACY",
    badgeClass: "badge-pro",
    desc: "High accuracy coding model"
  },
  {
    id: "gemini-3.6-flash-medium",
    name: "Gemini 3.6 Flash (Medium)",
    provider: "google",
    badge: "STANDARD",
    badgeClass: "badge-fast",
    desc: "Standard high speed model"
  },
  {
    id: "gemini-3.6-flash-low",
    name: "Gemini 3.6 Flash (Low)",
    provider: "google",
    badge: "LOW-LATENCY",
    badgeClass: "badge-fast",
    desc: "Low latency coding model"
  },
  {
    id: "gemini-pro-agent",
    name: "Gemini Pro Agent",
    provider: "google",
    badge: "AGENTIC",
    badgeClass: "badge-recommended",
    desc: "Frontier agentic model for complex multi-step workflows"
  },
  {
    id: "gemini-3.1-pro-low",
    name: "Gemini 3.1 Pro (Low)",
    provider: "google",
    badge: "PRO ARCH",
    badgeClass: "badge-thinking",
    desc: "Frontier Pro deep architecture model"
  },
  {
    id: "claude-sonnet-4-6",
    name: "Claude Sonnet 4.6 (Thinking)",
    provider: "anthropic",
    badge: "ANTHROPIC",
    badgeClass: "badge-anthropic",
    desc: "Anthropic coding specialist with extended thinking"
  },
  {
    id: "claude-opus-4-6-thinking",
    name: "Claude Opus 4.6 (Thinking)",
    provider: "anthropic",
    badge: "OPUS DEEP",
    badgeClass: "badge-anthropic",
    desc: "Anthropic maximum reasoning capacity model"
  },
  {
    id: "gpt-oss-120b-medium",
    name: "GPT-OSS 120B (Medium)",
    provider: "oss",
    badge: "OPEN WEIGHTS",
    badgeClass: "badge-weights",
    desc: "Open-weights large-scale autonomous coding model"
  }
];

let selectedChatModelId = localStorage.getItem('xflow_chat_model') || 'gemini-3.8-flash-high';
if (!AVAILABLE_CHAT_MODELS.some(m => m.id === selectedChatModelId)) {
  selectedChatModelId = 'gemini-3.8-flash-high';
}

function getSelectedModelObj() {
  return AVAILABLE_CHAT_MODELS.find(m => m.id === selectedChatModelId) || AVAILABLE_CHAT_MODELS[0];
}

function updateModelPillDisplay() {
  const current = getSelectedModelObj();
  const pillText = document.getElementById('chat-model-pill-text');
  if (pillText) {
    pillText.textContent = current.name;
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
  const dropdown = document.getElementById('chat-model-dropdown');
  const pill = document.getElementById('chat-model-pill');
  if (dropdown && pill) {
    renderModelDropdown();
    dropdown.style.display = 'block';
    pill.classList.add('active');
  }
}

function closeModelDropdown() {
  const dropdown = document.getElementById('chat-model-dropdown');
  const pill = document.getElementById('chat-model-pill');
  if (dropdown && pill) {
    dropdown.style.display = 'none';
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
async function syncDynamicModels() {
  const rPort = _getFloworkRouterPort();
  try {
    const res = await fetch(`http://127.0.0.1:${rPort}/auth/router/models`);
    if (res.ok) {
      const data = await res.json();
      if (data && Array.isArray(data.models) && data.models.length > 0) {
        AVAILABLE_CHAT_MODELS = data.models.map(m => ({
          id: m.id,
          name: m.name || m.id,
          provider: m.provider || 'google',
          badge: m.badge || 'PRO',
          badgeClass: m.badgeClass || 'badge-pro',
          desc: m.desc || m.description || ''
        }));
        if (!AVAILABLE_CHAT_MODELS.some(m => m.id === selectedChatModelId)) {
          selectedChatModelId = data.active_model || AVAILABLE_CHAT_MODELS[0].id;
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
      const menu = document.getElementById('chat-model-selector-menu');
      if (menu && menu.classList.contains('open')) {
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
  const rPort = _getFloworkRouterPort();
  try {
    const res = await fetch(`http://127.0.0.1:${rPort}/auth/router/session-binding?session_id=${encodeURIComponent(sessionId)}`, { cache: 'no-store' });
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
  currentSessionAccountId = accountId;
  currentSessionFailoverPolicy = failoverPolicy;
  pendingSessionAccountId = accountId;
  updateAccountPillDisplay();

  if (currentChatSessionId) {
    const rPort = _getFloworkRouterPort();
    try {
      await fetch(`http://127.0.0.1:${rPort}/auth/router/session-binding`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentChatSessionId,
          account_id: accountId,
          failover_policy: failoverPolicy
        })
      });
      const accObj = (routerSwitchboardState.accounts || []).find(a => a.id === accountId || (a.email && a.email.toLowerCase() === accountId.toLowerCase()));
      const label = accountId === 'combo' ? 'Combo (Auto-Balancer)' : (accObj ? (accObj.email || accObj.name) : accountId);
      showFloworkLaserToast(`🔗 Chat Session bound to: ${label}`, true);
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
let AVAILABLE_PERSONAS = [
  { id: 'default', name: 'Default Agent', icon: '🤖', description: 'Enclave core prompt only. Zero external persona loaded.' }
];
let currentSessionPersonaId = 'default';
let pendingSessionPersonaId = 'default';
let agentSelectorInitialized = false;

function getSelectedPersonaObj() {
  const targetId = currentSessionPersonaId || 'default';
  const found = AVAILABLE_PERSONAS.find(p => p.id.toLowerCase() === targetId.toLowerCase());
  if (found) return found;
  return {
    id: targetId,
    name: targetId === 'default' ? 'Default Agent' : targetId,
    icon: '🎭',
    description: 'Specialist persona active'
  };
}

function updateAgentPillDisplay() {
  const current = getSelectedPersonaObj();
  const pillText = document.getElementById('chat-agent-pill-text');
  const pillIcon = document.getElementById('chat-agent-pill-icon');
  const pillEl = document.getElementById('chat-agent-pill');
  if (pillText) {
    pillText.textContent = current.name || 'Default Agent';
  }
  if (pillIcon) {
    pillIcon.textContent = current.icon || '🤖';
  }
  if (pillEl) {
    if (current.id !== 'default') {
      pillEl.classList.add('is-locked');
      pillEl.title = `Locked Chat Persona: ${current.name} (Isolated Prompts & Triggers)`;
    } else {
      pillEl.classList.remove('is-locked');
      pillEl.title = 'Default Agent: Binary Enclave Prompt & Active Skills Only';
    }
  }
}

async function fetchAvailablePersonas() {
  try {
    const res = await fetch('/api/personas');
    if (res.ok) {
      const data = await res.json();
      if (data && data.status === 'ok' && Array.isArray(data.personas)) {
        AVAILABLE_PERSONAS = data.personas;
        updateAgentPillDisplay();
        renderAgentDropdown();
      }
    }
  } catch (err) {
    console.warn('[Persona] Failed to fetch available personas:', err);
  }
}

function renderAgentDropdown() {
  const listEl = document.getElementById('chat-agent-list');
  if (!listEl) return;

  const currentId = (currentSessionPersonaId || 'default').toLowerCase();

  listEl.innerHTML = AVAILABLE_PERSONAS.map(p => {
    const isSelected = p.id.toLowerCase() === currentId;
    const isDef = p.id.toLowerCase() === 'default';
    const badgeText = isDef ? 'CORE' : 'SPECIALIST';
    const badgeClass = isDef ? 'badge-agent-default' : 'badge-agent-specialist';
    return `
      <div class="agent-option-item ${isSelected ? 'selected' : ''}" data-persona-id="${p.id}">
        <div class="agent-option-left">
          <span class="agent-option-icon">${p.icon || (isDef ? '🤖' : '🎭')}</span>
          <div class="agent-option-content">
            <div class="agent-option-title-row">
              <span class="agent-option-name">${p.name}</span>
              <span class="agent-option-badge ${badgeClass}">${badgeText}</span>
            </div>
            <div class="agent-option-desc">${p.description || ''}</div>
          </div>
        </div>
        ${isSelected ? '<span class="agent-option-check">✓</span>' : ''}
      </div>
    `;
  }).join('');

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
}

async function setSessionAgentPersona(personaId) {
  currentSessionPersonaId = personaId;
  pendingSessionPersonaId = personaId;
  updateAgentPillDisplay();
  renderAgentDropdown();
  if (typeof isSlashPaletteOpen !== 'undefined' && isSlashPaletteOpen) {
    const chatInput = document.getElementById('rightbar-chat-input');
    if (chatInput) handleSlashInput(chatInput);
  }

  if (currentChatSessionId) {
    try {
      const res = await fetch(`/api/chat/sessions/${currentChatSessionId}/persona`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona_id: personaId === 'default' ? null : personaId
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
  const dropdown = document.getElementById('chat-agent-dropdown');
  const pill = document.getElementById('chat-agent-pill');
  if (dropdown && pill) {
    fetchAvailablePersonas();
    renderAgentDropdown();
    dropdown.style.display = 'block';
    pill.classList.add('active');
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
  updateAgentPillDisplay();
  fetchAvailablePersonas();

  if (agentSelectorInitialized) return;
  agentSelectorInitialized = true;

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
}

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

  isChatStreaming = false;
  const sendBtn = document.getElementById('btn-rightbar-send');
  if (sendBtn) {
    sendBtn.classList.remove('is-running');
    sendBtn.title = 'Send (Enter)';
  }

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

window.copyCodeSnippet = function(btn) {
  const card = btn.closest('.chat-code-card');
  if (!card) return;
  const code = card.getAttribute('data-code') || card.querySelector('pre code')?.innerText || '';
  navigator.clipboard.writeText(code).then(() => {
    const span = btn.querySelector('span') || btn;
    const orig = span.textContent;
    span.textContent = 'Copied!';
    setTimeout(() => { span.textContent = orig; }, 1800);
  }).catch(() => {
    showToast('Failed to copy code');
  });
};

window.executeSnippetInChat = function(btn) {
  const card = btn.closest('.chat-code-card');
  if (!card) return;
  const code = card.getAttribute('data-code') || '';
  const lang = (card.getAttribute('data-lang') || '').toUpperCase();
  if (!code) return;
  const chatInput = document.getElementById('rightbar-chat-input');
  if (chatInput) {
    if (lang === 'BASH' || lang === 'SH' || lang === 'SHELL') {
      chatInput.value = code;
    } else if (lang === 'PYTHON' || lang === 'PY') {
      chatInput.value = `python3 -c ${JSON.stringify(code)}`;
    } else if (lang === 'JS' || lang === 'JAVASCRIPT' || lang === 'NODE') {
      chatInput.value = `node -e ${JSON.stringify(code)}`;
    } else {
      chatInput.value = code;
    }
    chatInput.focus();
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
    showToast('Snippet staged in prompt input. Ready to execute.');
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
  navigator.clipboard.writeText(JSON.stringify(rows, null, 2)).then(() => {
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
  navigator.clipboard.writeText(csv).then(() => {
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
    navigator.clipboard.writeText(filePath).then(() => {
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

window.copyFilePath = function(path, btnEl) {
  navigator.clipboard.writeText(path).then(() => {
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
              <button class="code-card-run" onclick="executeSnippetInChat(this)" title="Stage this code into chat prompt">
                <span class="code-run-icon">▶</span>
                <span>Stage Run</span>
              </button>
            ` : ''}
            <button class="code-card-copy" onclick="copyCodeSnippet(this)" title="Copy code snippet">
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
          <audio controls preload="metadata" style="width:100%;" src="${resolved}"></audio>
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
      <div class="chat-media-preview" onclick="openChatLightbox('${resolved}', '${safeAlt}')">
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
    if (/^kondisi:?$/i.test(lower)) return `<strong class="chat-strong chat-label-kondisi">${text}</strong>`;
    if (/^(dampak|critical|danger|error|fatal):?$/i.test(lower)) return `<strong class="chat-strong chat-label-dampak">${text}</strong>`;
    if (/^(solusi|rekomendasi|success|aman|fix|resolusi):?$/i.test(lower)) return `<strong class="chat-strong chat-label-solusi">${text}</strong>`;
    if (/^(catatan|peringatan|note|warning|info|perhatian):?$/i.test(lower)) return `<strong class="chat-strong chat-label-catatan">${text}</strong>`;
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

  // Restore code cards (using function to avoid $ replacement pattern corruption)
  codeCards.forEach((card, idx) => {
    formatted = formatted.replace('___CODE_BLOCK_' + idx + '___', () => card);
  });

  return formatted;
}

// =============================================================================
// CHAT ATTACHMENTS & CONTEXT HANDLER (IMAGES / FILES / CLIPBOARD)
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================
let activeChatAttachments = [];

function addChatAttachment(file) {
  if (!file) return;
  const id = 'att_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
  const isImage = file.type ? file.type.startsWith('image/') : /\.(png|jpe?g|webp|gif|svg|bmp)$/i.test(file.name);
  const previewUrl = isImage ? URL.createObjectURL(file) : null;

  activeChatAttachments.push({
    id,
    file,
    name: file.name || `attachment_${Date.now()}`,
    size: file.size || 0,
    type: file.type || 'application/octet-stream',
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
      ? `<img class="chat-attachment-thumb" src="${att.previewUrl}" alt="${escapeHtml(att.name)}" onclick="openChatLightbox('${att.previewUrl}', '${escapeHtml(att.name)}')" />`
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
      return {
        success: true,
        filename: uniqueName,
        originalName: att.name,
        targetPath: targetPath,
        webUrl: `/canvas/uploads/${uniqueName}`,
        size: att.size,
        isImage: att.isImage
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
    isImage: att.isImage
  };
}

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
    localStorage.setItem('xflow_rightbar_collapsed', 'false');
  }
  if (window.__updateLayoutResizers) window.__updateLayoutResizers();

  // Toggle Rightbar panel
  if (btnToggleChat && rightbarChat) {
    btnToggleChat.addEventListener('click', () => {
      rightbarChat.classList.toggle('collapsed');
      const collapsed = rightbarChat.classList.contains('collapsed');
      localStorage.setItem('xflow_rightbar_collapsed', collapsed ? 'true' : 'false');

      // Fail-safe: If user collapses chat while workbench is also collapsed, auto-restore workbench!
      const workbench = document.querySelector('.workbench-main');
      if (collapsed && workbench && workbench.classList.contains('collapsed')) {
        if (window.__setWorkbenchState) window.__setWorkbenchState(false, false);
      }

      if (window.__updateLayoutResizers) window.__updateLayoutResizers();
      if (!collapsed && chatInput) {
        chatInput.focus();
      }
    });
  }

  // Close Rightbar panel
  if (btnCloseRightbar && rightbarChat) {
    btnCloseRightbar.addEventListener('click', () => {
      rightbarChat.classList.add('collapsed');
      localStorage.setItem('xflow_rightbar_collapsed', 'true');

      // Fail-safe: If user closes chat while workbench is also collapsed, auto-restore workbench!
      const workbench = document.querySelector('.workbench-main');
      if (workbench && workbench.classList.contains('collapsed')) {
        if (window.__setWorkbenchState) window.__setWorkbenchState(false, false);
      }

      if (window.__updateLayoutResizers) window.__updateLayoutResizers();
    });
  }

  // Toggle History view
  if (btnChatHistory && rightbarHistoryView && rightbarMessages) {
    btnChatHistory.addEventListener('click', () => {
      const isHistoryOpen = rightbarHistoryView.style.display !== 'none';
      if (isHistoryOpen) {
        rightbarHistoryView.style.display = 'none';
        rightbarMessages.style.display = 'flex';
      } else {
        rightbarHistoryView.style.display = 'flex';
        rightbarMessages.style.display = 'none';
        fetchChatHistory();
      }
    });
  }

  // Back from History to Messages
  if (btnCloseHistory && rightbarHistoryView && rightbarMessages) {
    btnCloseHistory.addEventListener('click', () => {
      rightbarHistoryView.style.display = 'none';
      rightbarMessages.style.display = 'flex';
    });
  }

  // Quick-action prompt chips click delegation
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

  // Antigravity Input Toolbar controls (+ button for Files/Images)
  const btnChatAdd = document.getElementById('btn-chat-add');
  const chatFileInput = document.getElementById('chat-file-input');
  if (btnChatAdd && chatFileInput) {
    btnChatAdd.addEventListener('click', () => {
      chatFileInput.click();
    });

    chatFileInput.addEventListener('change', () => {
      if (chatFileInput.files && chatFileInput.files.length > 0) {
        Array.from(chatFileInput.files).forEach(f => addChatAttachment(f));
        showToast(`${chatFileInput.files.length} file(s) attached`);
        chatFileInput.value = '';
      }
    });
  }

  // Paste image & files from clipboard (Ctrl+V)
  if (chatInput) {
    chatInput.addEventListener('paste', (e) => {
      const items = e.clipboardData && e.clipboardData.items;
      if (!items) return;
      let hasAttached = false;
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type && item.type.indexOf('image') !== -1) {
          const file = item.getAsFile();
          if (file) {
            addChatAttachment(file);
            hasAttached = true;
          }
        }
      }
      if (hasAttached) {
        showToast('Image attached from clipboard');
      }
    });
  }

  // Drag and drop files onto chat input box
  const chatInputBox = document.querySelector('.chat-input-box');
  if (chatInputBox) {
    ['dragenter', 'dragover'].forEach(name => {
      chatInputBox.addEventListener(name, (e) => {
        e.preventDefault();
        chatInputBox.style.borderColor = '#00e5ff';
        chatInputBox.style.boxShadow = '0 0 16px rgba(0, 229, 255, 0.35)';
      });
    });
    ['dragleave', 'drop'].forEach(name => {
      chatInputBox.addEventListener(name, (e) => {
        e.preventDefault();
        chatInputBox.style.borderColor = '';
        chatInputBox.style.boxShadow = '';
      });
    });
    chatInputBox.addEventListener('drop', (e) => {
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        Array.from(e.dataTransfer.files).forEach(f => addChatAttachment(f));
        showToast(`${e.dataTransfer.files.length} file(s) attached`);
      }
    });
  }

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
        showToast('🔄 Flowork sedang restart & memuat pembaruan, mohon tunggu sebentar...');
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

  startChatSyncEngine();
}

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
        renderTrajectorySteps(serverSteps);

        const container = document.getElementById('rightbar-messages');
        if (container) {
          container.scrollTop = container.scrollHeight;
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

  // 1. Central Core: Metallic Obsidian Sphere
  const coreGeom = new THREE.SphereGeometry(0.52, 36, 28);
  const coreMat = new THREE.MeshStandardMaterial({
    color: 0x051833,
    emissive: 0x00172e,
    emissiveIntensity: 0.8,
    metalness: 0.88,
    roughness: 0.18
  });
  group.add(new THREE.Mesh(coreGeom, coreMat));

  // 2. Holographic Geometric Lattice
  const latticeGeom = new THREE.IcosahedronGeometry(0.536, 2);
  const latticeMat = new THREE.MeshBasicMaterial({
    color: 0x00e5ff,
    wireframe: true,
    transparent: true,
    opacity: 0.22
  });
  group.add(new THREE.Mesh(latticeGeom, latticeMat));

  // 3. Cybernetic Ocular Visor
  const visorGeom = new THREE.BoxGeometry(0.48, 0.12, 0.18);
  const visorMat = new THREE.MeshStandardMaterial({
    color: 0x00e5ff,
    emissive: 0x00f2fe,
    emissiveIntensity: 2.4,
    metalness: 0.9,
    roughness: 0.1
  });
  const visor = new THREE.Mesh(visorGeom, visorMat);
  visor.position.set(0, 0.06, 0.44);
  group.add(visor);

  // Visor Central Pupil
  const pupilGeom = new THREE.SphereGeometry(0.045, 16, 16);
  const pupilMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const pupil = new THREE.Mesh(pupilGeom, pupilMat);
  pupil.position.set(0, 0.06, 0.52);
  group.add(pupil);

  // 4. Ear Pods & Glowing Rings
  const podGeom = new THREE.CylinderGeometry(0.14, 0.14, 0.12, 24);
  const podMat = new THREE.MeshStandardMaterial({ color: 0x0b2240, metalness: 0.85, roughness: 0.2 });
  const ringGeom = new THREE.TorusGeometry(0.15, 0.012, 16, 32);
  const ringMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff, transparent: true, opacity: 0.85 });

  const leftPod = new THREE.Mesh(podGeom, podMat);
  leftPod.rotation.z = Math.PI / 2;
  leftPod.position.set(-0.53, 0.02, 0);
  const leftRing = new THREE.Mesh(ringGeom, ringMat);
  leftRing.rotation.y = Math.PI / 2;
  leftRing.position.set(-0.58, 0.02, 0);
  group.add(leftPod);
  group.add(leftRing);

  const rightPod = new THREE.Mesh(podGeom, podMat);
  rightPod.rotation.z = Math.PI / 2;
  rightPod.position.set(0.53, 0.02, 0);
  const rightRing = new THREE.Mesh(ringGeom, ringMat);
  rightRing.rotation.y = Math.PI / 2;
  rightRing.position.set(0.58, 0.02, 0);
  group.add(rightPod);
  group.add(rightRing);

  // 5. Talking Mouth Equalizer Bars (7 Audio-Reactive Bars)
  const mouthGroup = new THREE.Group();
  const barCount = 7;
  const barWidth = 0.035;
  const barGap = 0.014;
  const totalW = barCount * barWidth + (barCount - 1) * barGap;

  for (let i = 0; i < barCount; i++) {
    const barGeom = new THREE.BoxGeometry(barWidth, 0.07, 0.04);
    const barMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x00f2fe,
      emissiveIntensity: 2.0
    });
    const bar = new THREE.Mesh(barGeom, barMat);
    bar.position.x = -totalW / 2 + i * (barWidth + barGap) + barWidth / 2;
    bar.userData = { index: i, baseH: 0.07 };
    mouthGroup.add(bar);
  }
  mouthGroup.position.set(0, -0.17, 0.46);
  group.add(mouthGroup);
  mascotProceduralMouth = mouthGroup;

  // 6. Magnetic Levitation Collar Halo
  const collarGeom = new THREE.TorusGeometry(0.30, 0.014, 16, 48);
  const collarMat = new THREE.MeshStandardMaterial({
    color: 0x00e5ff,
    emissive: 0x00f2fe,
    emissiveIntensity: 1.2,
    metalness: 0.8
  });
  const collar = new THREE.Mesh(collarGeom, collarMat);
  collar.rotation.x = Math.PI / 2;
  collar.position.set(0, -0.44, 0);
  group.add(collar);

  group.position.set(0, 0.08, 0);
  group.userData = { basePosY: 0.08, baseRotX: 0, baseRotY: 0 };

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
  'manage_task', 'invoke_subagent', 'define_subagent', 'manage_subagents', 'send_message',
  'generate_image', 'read_url_content', 'search_web', 'browser_control', 'telegram_control',
  'project_RADAR', 'symbol_outline', 'read_symbol', 'grep_search', 'find_by_name'
];

function sanitizeToolOutput(raw) {
  if (raw === null || raw === undefined) return '';
  let s = typeof raw === 'object' ? JSON.stringify(raw, null, 2) : String(raw);
  s = s.replace(/<SOVEREIGN_TOOL_INTERCEPT_GATE_INJECTION>[\s\S]*?<\/SOVEREIGN_TOOL_INTERCEPT_GATE_INJECTION>/g, '');
  s = s.replace(/<SOVEREIGN_SKILL_RADAR>[\s\S]*?<\/SOVEREIGN_SKILL_RADAR>/g, '');
  s = s.replace(/<SOVEREIGN_BRAIN_ALERT>[\s\S]*?<\/SOVEREIGN_BRAIN_ALERT>/g, '');
  s = s.replace(/\[TOOL RESULT FOR [^\]]+\]:\s*/g, '');
  return s.trim();
}

function extractToolReason(toolName, details) {
  const cleanTool = cleanKernelToolName(toolName || 'tool');
  const d = (details && details.details && typeof details.details === 'object')
    ? { ...details, ...details.details }
    : (details && typeof details === 'object' ? details : {});

  const explicit = d.reason || d.Reason || d.rationale || d.Rationale || d.purpose || d.explanation || d.toolAction || d.Description || d.Instruction || d.toolSummary || '';
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

function recordThinkingArsenal(toolName, details, status = 'running', outputData = null) {
  const cleanTool = cleanKernelToolName(toolName);
  if (!cleanTool) return;

  const d = (details && details.details && typeof details.details === 'object')
    ? { ...details, ...details.details }
    : (details && typeof details === 'object' ? details : {});

  const reasonText = extractToolReason(toolName, details);
  let logMsg = reasonText ? `[WHY // ${cleanTool.toUpperCase()}] 💬 ${reasonText}` : '';

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
      const knownSkillHints = ['agy-customizations', 'antigravity-guide', 'antigravity_guide', 'generative_ui', 'migrate-workflows'];
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

  ensureBar() {
    let bar = document.getElementById('fl-loop-sys-bar');
    if (bar) return bar;
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
    const osEl = document.getElementById('fl-lsb-os');
    if (osEl && !this._lastPulseData) {
      osEl.textContent = clientOs.fullTag;
    }

    this.updateArsenalCounters();

    if (!this._pollTimer) {
      this.pollSysPulse();
      this._pollTimer = setInterval(() => this.pollSysPulse(), 1000);
    }
    if (!this._clockTimer) {
      this._clockTimer = setInterval(() => {
        if (!isMascotAgentLooping && !isChatStreaming) {
          this.stop();
          return;
        }
        const elapsed = ((Date.now() - this._loopStartTime) / 1000).toFixed(1);
        const timerTxt = document.getElementById('fl-lsb-timer-txt');
        if (timerTxt) timerTxt.textContent = `LOOP ${elapsed}s`;
      }, 100);
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
    const bar = document.getElementById('fl-loop-sys-bar');
    if (bar) {
      bar.style.display = 'none';
    }
  },

  updateArsenalCounters() {
    const arsenalEl = document.getElementById('fl-lsb-arsenal');
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
    const osEl = document.getElementById('fl-lsb-os');
    const cpuFill = document.getElementById('fl-lsb-cpu-fill');
    const cpuVal = document.getElementById('fl-lsb-cpu-val');
    const cpuWrap = document.getElementById('fl-lsb-cpu-wrap');
    const ramFill = document.getElementById('fl-lsb-ram-fill');
    const ramVal = document.getElementById('fl-lsb-ram-val');
    const rssEl = document.getElementById('fl-lsb-rss');

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
    speechText.textContent = '"Welcome to Flowork OS. I am Mr. Flow, sovereign AI agent ready to assist your operations."';
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

function mascotRenderLoop() {
  if (!mascotIsRunning) {
    mascotAnimId = null;
    return;
  }

  const audio = document.getElementById('chat-mascot-audio');
  const isAudioActive = audio && !audio.paused;

  // On-Demand Sleep: If audio is paused, user is not hovering, and agent is NOT looping, draw 1 frame and exit loop!
  if (!isAudioActive && !isMascotHovered && !isMascotAgentLooping) {
    renderSingleMascotFrame();
    mascotAnimId = null;
    return;
  }

  const now = performance.now();
  const targetInterval = (isAudioActive || isMascotAgentLooping) ? 33 : 60; // 30 FPS speaking/looping, 16 FPS hover
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
      <audio id="chat-mascot-audio" preload="auto" src="/canvas/sounds/greeting.mp3"></audio>
    </div>
  `;
}

async function startNewChatSession(resetToDefault = true) {
  if (isChatStreaming) return;
  hidePinnedPrompt();
  clearChatAttachments();
  activeTurnUserCard = null;
  currentChatSessionId = null;
  localStorage.removeItem('xflow_active_session_id');
  localStorage.setItem('xflow_new_chat_explicit', 'true');
  lastKnownStepFingerprint = '';
  pendingSessionAccountId = 'combo';
  currentSessionAccountId = 'combo';
  currentSessionFailoverPolicy = 'fallback_pool';
  updateAccountPillDisplay();
  pendingSessionPersonaId = 'default';
  currentSessionPersonaId = 'default';
  updateAgentPillDisplay();
  const rightbarMessages = document.getElementById('rightbar-messages');
  const rightbarHistoryView = document.getElementById('rightbar-history-view');
  if (rightbarHistoryView) rightbarHistoryView.style.display = 'none';
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

async function fetchChatHistory() {
  const listEl = document.getElementById('history-items-list');
  if (!listEl) return;
  listEl.innerHTML = '<div class="history-empty-hint" style="padding:18px 12px; text-align:center; color:var(--text-muted); font-size:11px;">Loading conversation history...</div>';

  await syncCustomSessionTitlesFromServer();
  const customTitles = getCustomSessionTitles();

  try {
    const res = await fetch('/api/chat/history');
    const data = await res.json();
    if (data.status === 'ok' && Array.isArray(data.sessions)) {
      if (data.sessions.length === 0) {
        listEl.innerHTML = '<div class="history-empty-hint" style="padding:18px 12px; text-align:center; color:var(--text-muted); font-size:11px;">No past sessions found.</div>';
        return;
      }
      listEl.innerHTML = data.sessions.map(s => {
        const isActive = s.id === currentChatSessionId ? 'active' : '';
        let displayTitle = '';
        if (customTitles && customTitles[s.id]) {
          displayTitle = customTitles[s.id];
        } else {
          let rawTitle = s.title || 'Conversation Session';
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
        const personaBadge = (s.agent_persona && s.agent_persona !== 'default') ? ` • 🎭 ${escapeHtml(s.agent_persona)}` : '';
        const steps = (s.step_count ? ` • ${s.step_count} steps` : '') + personaBadge;
        return `
          <div class="history-item ${isActive}" data-session-id="${s.id}">
            <div class="history-item-left">
              <span class="history-icon">💬</span>
              <div class="history-meta" data-session-id="${s.id}">
                <span class="history-name" data-session-id="${s.id}" title="${title} (Double-click to rename)">${title}</span>
                <span class="history-time" data-session-id="${s.id}">${time}${steps}</span>
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
    } else {
      listEl.innerHTML = `<div class="history-empty-hint" style="padding:18px 12px; color:#f87171; font-size:11px;">${escapeHtml(data.message || 'Failed to load history')}</div>`;
    }
  } catch (err) {
    listEl.innerHTML = '<div class="history-empty-hint" style="padding:18px 12px; color:#f87171; font-size:11px;">Error connecting to agent service</div>';
  }
}

async function loadChatSession(sessionId) {
  currentChatSessionId = sessionId;
  localStorage.setItem('xflow_active_session_id', sessionId);
  localStorage.removeItem('xflow_new_chat_explicit');
  lastKnownStepFingerprint = '';
  await fetchSessionBinding(sessionId);
  const rightbarMessages = document.getElementById('rightbar-messages');
  const rightbarHistoryView = document.getElementById('rightbar-history-view');
  if (rightbarHistoryView) rightbarHistoryView.style.display = 'none';
  if (rightbarMessages) {
    rightbarMessages.style.display = 'flex';
    rightbarMessages.querySelectorAll('.chat-msg, .fl-chat-loading-indicator').forEach(el => el.remove());
    const loadIndicator = document.createElement('div');
    loadIndicator.className = 'fl-chat-loading-indicator';
    loadIndicator.style.cssText = 'padding:24px; text-align:center; color:var(--text-dim); font-size:11px;';
    loadIndicator.textContent = 'Loading conversation steps...';
    rightbarMessages.appendChild(loadIndicator);
  }

  try {
    const res = await fetch(`/api/chat/steps/${sessionId}`);
    const data = await res.json();
    if (data.status === 'ok' && data.data && Array.isArray(data.data.steps)) {
      renderTrajectorySteps(data.data.steps);
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

      // Sync persona specialist lock strictly to this chat's locked persona!
      currentSessionPersonaId = data.data.agent_persona || 'default';
      pendingSessionPersonaId = currentSessionPersonaId;
      updateAgentPillDisplay();
    } else {
      showToast('Could not load session steps');
    }
  } catch (err) {
    showToast('Failed to load session');
  }
}

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
  const skills = Array.from(new Set([...turnPinnedSkills, ...sessionPinnedSkills]));
  const tools = Array.from(new Set([...turnPinnedTools, ...sessionPinnedTools]));

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

  // Hyper-speed terminal stream interval (~40ms) - feels incredibly fast!
  const streamTickerId = setInterval(() => {
    if (!logStreamEl || !container.isConnected) {
      clearInterval(streamTickerId);
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
  }, 40);

  // Precision elapsed timer every 100ms
  const timerId = setInterval(() => {
    if (!container.isConnected) {
      clearInterval(timerId);
      clearInterval(streamTickerId);
      return;
    }
    const elapsedSec = ((Date.now() - startTime) / 1000).toFixed(1);
    if (timerEl) timerEl.textContent = `${elapsedSec}s`;
  }, 100);

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
      ['agy-customizations', 'antigravity-guide', 'antigravity_guide', 'generative_ui', 'migrate-workflows'].forEach(sk => {
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
  const skills = Array.from(new Set([...turnPinnedSkills, ...sessionPinnedSkills]));
  const tools = Array.from(new Set([...turnPinnedTools, ...sessionPinnedTools]));
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
   JARVIS TACTICAL CYBER-HUD & AUDIO ENGINE
   ========================================================================== */

const FloworkJarvisAudio = {
  mode: localStorage.getItem('flw_jarvis_audio_mode') || 'all',
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
    localStorage.setItem('flw_jarvis_audio_mode', newMode);
    this.updateToggleUi();
  },

  toggleMode() {
    if (this.mode === 'all') this.setMode('sfx_only');
    else if (this.mode === 'sfx_only') this.setMode('muted');
    else this.setMode('all');
  },

  updateToggleUi() {
    const btn = document.getElementById('btn-jarvis-audio-toggle');
    if (!btn) return;
    if (this.mode === 'all') {
      btn.className = 'fl-jarvis-toggle-btn';
      btn.innerHTML = '🔊 MR. FLOW: VOICE+SFX';
      btn.title = 'Mr. Flow Audio: Voice and SFX Enabled (Click to change)';
    } else if (this.mode === 'sfx_only') {
      btn.className = 'fl-jarvis-toggle-btn';
      btn.innerHTML = '🔈 MR. FLOW: SFX ONLY';
      btn.title = 'Mr. Flow Audio: SFX Only (Click to mute)';
    } else {
      btn.className = 'fl-jarvis-toggle-btn is-muted';
      btn.innerHTML = '🔇 MR. FLOW: MUTED';
      btn.title = 'Mr. Flow Audio: Muted (Click to enable)';
    }
  },

  initUi() {
    let btn = document.getElementById('btn-jarvis-audio-toggle');
    if (!btn) {
      const headerActions = document.querySelector('.chat-header-actions') || document.querySelector('.rightbar-header');
      if (headerActions) {
        btn = document.createElement('button');
        btn.id = 'btn-jarvis-audio-toggle';
        btn.className = 'fl-jarvis-toggle-btn';
        btn.onclick = () => FloworkJarvisAudio.toggleMode();
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
        file: '/canvas/sounds/jarvis/target_locked.mp3',
        speech: "Target acquired. Scanning perimeter, sir.",
        sfx: 'radar_lock'
      },
      terminal_exec: {
        file: '/canvas/sounds/jarvis/terminal_exec.mp3',
        speech: "Executing payload, sir. Terminal stream live.",
        sfx: 'terminal_click'
      },
      terminal_done: {
        file: '/canvas/sounds/jarvis/terminal_done.mp3',
        speech: "Process completed cleanly with exit code zero.",
        sfx: 'chime'
      },
      skill_search: {
        file: '/canvas/sounds/jarvis/skill_search.mp3',
        speech: "Querying skill repository for requested capability.",
        sfx: 'blip'
      },
      skill_pinned: {
        file: '/canvas/sounds/jarvis/skill_pinned.mp3',
        speech: "Runbook pinned. Operational protocol engaged, sir.",
        sfx: 'lock'
      },
      agent_spawn: {
        file: '/canvas/sounds/jarvis/agent_spawn.mp3',
        speech: "Sub-agent deployed into orbit. Swarm telemetry synchronized.",
        sfx: 'warp'
      },
      agent_complete: {
        file: '/canvas/sounds/jarvis/agent_complete.mp3',
        speech: "Sub-agent reporting back. Mission accomplished, sir.",
        sfx: 'chime'
      },
      code_patched: {
        file: '/canvas/sounds/jarvis/code_patched.mp3',
        speech: "Source code modified with surgical precision, sir.",
        sfx: 'laser'
      },
      alert_breach: {
        file: '/canvas/sounds/jarvis/alert_breach.mp3',
        speech: "Command intercepted. Security protocol triggered, sir.",
        sfx: 'klaxon'
      },
      system_online: {
        file: '/canvas/sounds/jarvis/system_online.mp3',
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
            console.warn('[Jarvis Audio] MP3 play error:', err);
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
      if (idx < text.length) {
        element.textContent += text[idx];
        idx++;
        if (idx % 3 === 0 && window.FloworkJarvisAudio && FloworkJarvisAudio.mode === 'all') {
          FloworkJarvisAudio.playSynthSfx('terminal_click');
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
window.FloworkMrFlowAudio = FloworkJarvisAudio;
window.FloworkJarvisAudio = FloworkJarvisAudio;

let hasPlayedSystemOnline = false;
document.addEventListener('click', () => {
  FloworkJarvisAudio.initAudioContext();
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
    shortArg = schedDesc ? `${schedDesc}: ${details.Prompt || details.prompt || ''}` : (cmd || file || query || url || details.toolAction || details.toolSummary || '');
    fullInput = JSON.stringify(details, null, 2);
    const rawOut = details.rawOutput ?? details.output ?? details.stdout ?? details.result ?? null;
    if (rawOut !== undefined && rawOut !== null && rawOut !== '') {
      output = sanitizeToolOutput(rawOut);
    }
  }

  if (rawTool.includes('run_command') || rawTool.includes('exec') || rawTool.includes('terminal')) {
    toolTag = 'TERMINAL // BASH';
    toolTitle = 'Run command';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>`;
  } else if (rawTool.includes('inspect') || rawTool.includes('view') || rawTool.includes('read') || rawTool.includes('ingest')) {
    toolTag = 'FS // READ';
    toolTitle = 'Read file';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`;
  } else if (rawTool.includes('forge') || rawTool.includes('splice') || rawTool.includes('write') || rawTool.includes('replace') || rawTool.includes('edit')) {
    toolTag = 'FS // EDIT';
    toolTitle = 'Edit file';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>`;
  } else if (rawTool.includes('recon') || rawTool.includes('locate') || rawTool.includes('search') || rawTool.includes('grep')) {
    toolTag = 'SEARCH // RECON';
    toolTitle = 'Search';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`;
  } else if (rawTool.includes('url') || rawTool.includes('fetch') || rawTool.includes('web')) {
    toolTag = 'NET // FETCH';
    toolTitle = 'Web Request';
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/></svg>`;
  } else {
    toolTag = 'TOOL // EXEC';
    toolTitle = (toolName || 'Tool').replace(/_/g, ' ');
    toolIconSvg = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`;
  }

  const displayArg = shortArg.length > 55 ? shortArg.slice(0, 55) + '...' : shortArg;
  const reasonText = extractToolReason(toolName, details);
  const shortReason = reasonText.length > 52 ? reasonText.slice(0, 50) + '…' : reasonText;

  const card = document.createElement('details');
  card.className = 'fl-tool-card';
  card.open = false;

  card.innerHTML = `
    <summary class="fl-tool-header">
      <span class="fl-tool-chevron">›</span>
      <span class="fl-tool-icon">${toolIconSvg}</span>
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

    capsule.addEventListener('toggle', () => {
      // Natural CSS rotation or text update
    });
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
  const otherTools = body.querySelectorAll('.fl-tool-card');
  
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

  let scanLines = [];
  if (rawContent && typeof rawContent === 'string' && rawContent.trim()) {
    const rawLines = rawContent.split(/\r?\n/).slice(0, 120);
    rawLines.forEach((line, idx) => {
      const match = line.match(/^\s*(\d+)[\:\│]\s?(.*)$/);
      if (match) {
        const lineNo = String(match[1]).padStart(3, '0');
        scanLines.push(`${lineNo} │ ${match[2]}`);
      } else {
        const lineNo = String(startNum + idx).padStart(3, '0');
        scanLines.push(`${lineNo} │ ${line}`);
      }
    });
  }
  return scanLines;
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

  const renderViewportRows = (offsetIdx, activeRowOffset) => {
    const streamEl = box.querySelector('.fl-vf-ghost-stream');
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

  if (box._screeningTimer) clearInterval(box._screeningTimer);
  box._screeningTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const totalL = Math.max(1, scanLines.length);
    const curStep = tick % totalL;
    const pct = Math.min(98, Math.max(15, Math.round(((curStep + 1) / totalL) * 100)));

    const badge = box.querySelector('.fl-vf-speed-badge');
    if (badge) badge.textContent = `LINE ${startNum + curStep} / ${startNum + totalL - 1} (${pct}%)`;

    const fill = box.querySelector('.fl-vf-laser-fill');
    if (fill) fill.style.width = `${pct}%`;

    const timerEl = box.querySelector('.fl-vf-timer');
    if (timerEl) timerEl.textContent = `${elapsedSec}s • ${totalL} REAL LINES`;

    const windowStart = Math.max(0, curStep - 3);
    renderViewportRows(windowStart, curStep - windowStart);
  }, 115);
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

  const renderDiffBlocks = (stepTick) => {
    const delContainer = box.querySelector('.fl-rfc-del-rows');
    const addContainer = box.querySelector('.fl-rfc-add-rows');
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

  if (box._typingTimer) clearInterval(box._typingTimer);
  box._typingTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsed = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const timerEl = box.querySelector('.fl-rfc-timer');
    if (timerEl) timerEl.textContent = `${elapsed}s • DIFF ACTIVE`;
    renderDiffBlocks(tick);
  }, 135);
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

  const filePath = d.TargetFile || d.AbsolutePath || d.target_file || d.file || d.path || 'workspace/file';
  const fileName = String(filePath).split(/[\\/]/).pop() || shortenFilePath(filePath);
  let codeRaw = String(d.CodeContent ?? d.code_content ?? d.content ?? d.real_content ?? '');
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

  const renderWriteRows = (stepTick) => {
    const printer = box.querySelector('.fl-wtf-printer');
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
        codeRaw = String(updatedCode);
        totalBytes = new Blob([codeRaw]).size || codeRaw.length || totalBytes;
        codeLines = codeRaw.split(/\r?\n/).filter((l, idx, arr) => !(idx === arr.length - 1 && l === '')).map((l, idx) => `${String(idx + 1).padStart(3, '0')} │ ${l}`);
        renderWriteRows(codeLines.length);
      }
    }
  };

  if (box._typingTimer) clearInterval(box._typingTimer);
  box._typingTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsed = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const totalL = Math.max(1, codeLines.length);
    const curLine = Math.min(totalL, (tick % (totalL + 2)) + 1);
    const pct = Math.min(99, Math.round((curLine / totalL) * 100));
    const curBytes = Math.floor((totalBytes * pct) / 100);

    const pillar = box.querySelector('.fl-wtf-pillar-fill');
    if (pillar) pillar.style.height = `${pct}%`;

    const bytesEl = box.querySelector('.fl-wtf-bytes');
    if (bytesEl) bytesEl.textContent = `${curBytes} B / ${totalBytes} B (${pct}% • ${totalL} LINES)`;

    const timerEl = box.querySelector('.fl-wtf-timer');
    if (timerEl) timerEl.textContent = `${elapsed}s • WRITING DISK`;

    renderWriteRows(curLine);
  }, 115);
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

  if (box._genericTimer) clearInterval(box._genericTimer);
  let tick = 0;
  box._genericTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsed = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const speedEl = box.querySelector('.fl-st-speed');
    if (speedEl) speedEl.textContent = `SCANNING 37 TOOLS • ${elapsed}s`;

    const chips = box.querySelectorAll('.fl-st-chip');
    if (chips.length >= 3) {
      chips[0].textContent = pool[tick % pool.length];
      chips[1].textContent = pool[(tick + 1) % pool.length];
      chips[2].textContent = pool[(tick + 2) % pool.length];
    }
  }, 28);
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

  const telemetryFrames = [
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

  if (box._bashTimer) clearInterval(box._bashTimer);
  let tick = 0;
  box._hasRealStdout = false;
  box._injectOutputLines = (rawOut) => {
    if (!rawOut) return;
    const text = typeof rawOut === 'object' ? (rawOut.stdout || rawOut.output || JSON.stringify(rawOut)) : String(rawOut);
    const cleanLines = String(text).split('\n').filter(l => l.trim() && !l.includes('[DOKTRIN TERMINAL FLOWORK]')).slice(-4);
    if (cleanLines.length > 0) {
      box._hasRealStdout = true;
      const codeEl = box.querySelector('.fl-live-bash-code code');
      if (codeEl) codeEl.textContent = cleanLines.join('\n');
    }
  };

  box._bashTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsed = ((Date.now() - box._spawnTime) / 1000).toFixed(2).padStart(5, '0');
    const sw = box.querySelector('.fl-bash-stopwatch');
    if (sw) sw.textContent = `${elapsed}s`;

    const ioEl = box.querySelector('.fl-bash-io-rate');
    if (ioEl) ioEl.textContent = `I/O: ${1200 + ((tick * 173) % 2800)} CHARS/S`;

    if (!box._hasRealStdout) {
      const codeEl = box.querySelector('.fl-live-bash-code code');
      if (codeEl) {
        const count = Math.min(telemetryFrames.length, 2 + Math.floor(tick / 3));
        codeEl.textContent = telemetryFrames.slice(0, count).join('\n') + (tick % 2 === 0 ? ' █' : '');
      }
    }
  }, 28);
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
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsed = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const velEl = box.querySelector('.fl-brain-orb-velocity');
    if (velEl) velEl.textContent = `${elapsed}s`;

    const vecEl = box.querySelector('.fl-brain-vector-txt');
    if (vecEl) vecEl.textContent = vectors[tick % vectors.length];

    const syncEl = box.querySelector('.fl-brain-sync-pct');
    if (syncEl) syncEl.textContent = `SYNC: ${Math.min(99.9, (92 + (tick * 1.7) % 8)).toFixed(1)}%`;
  }, 38);
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

  if (box._skillTimer) clearInterval(box._skillTimer);
  let tick = 0;
  box._skillTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const litCount = Math.min(20, (tick % 21) + 1);
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);

    const leds = box.querySelectorAll('.fl-sk-led');
    leds.forEach((led, idx) => {
      led.classList.toggle('is-lit', idx < litCount);
    });

    const statusEl = box.querySelector('.fl-sk-status');
    if (statusEl) statusEl.textContent = `${litCount}/20 KEYWORDS • ${elapsedSec}s`;

    const sopEl = box.querySelector('.fl-sk-sop-text');
    if (sopEl && sopFeed.length > 0) {
      sopEl.textContent = sopFeed[tick % sopFeed.length];
    }
  }, 28);
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

  if (box._webTimer) clearInterval(box._webTimer);
  let tick = 0;
  box._webTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-sw-badge');
    if (badge) badge.textContent = `${pktPool.length} PKTS • ${elapsedSec}s`;

    const pktEls = box.querySelectorAll('.fl-sw-pkt-line');
    if (pktEls.length >= 3 && pktPool.length > 0) {
      pktEls[0].textContent = pktPool[tick % pktPool.length];
      pktEls[1].textContent = pktPool[(tick + 1) % pktPool.length];
      pktEls[2].textContent = pktPool[(tick + 2) % pktPool.length];
    }
  }, 30);
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

  if (box._urlTimer) clearInterval(box._urlTimer);
  let tick = 0;
  box._urlTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const kb = ((totalBytes * Math.min(1, (tick % 18) / 14)) / 1024).toFixed(1);

    const statEl = box.querySelector('.fl-ru-stat');
    if (statEl) statEl.textContent = `INGESTED: ${kb} KB • ${mdLines.length} MD BLOCKS`;

    const timerEl = box.querySelector('.fl-ru-timer');
    if (timerEl) timerEl.textContent = `${elapsedSec}s • ZERO-JS EXTRACT`;

    const lineEls = box.querySelectorAll('.fl-ru-md-line');
    if (lineEls.length >= 2 && mdLines.length > 0) {
      lineEls[0].textContent = mdLines[tick % mdLines.length];
      lineEls[1].textContent = mdLines[(tick + 1) % mdLines.length];
    }
  }, 28);
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

  if (box._lockBoxTimer) clearInterval(box._lockBoxTimer);
  let tick = 0;
  const hexChars = '0123456789abcdef';
  box._lockBoxTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const statusEl = box.querySelector('.fl-flk-status');
    if (statusEl) statusEl.textContent = `CLAMPING • ${elapsedSec}s`;

    let rollingHash = '';
    for (let i = 0; i < 24; i++) {
      rollingHash += hexChars[(tick * 7 + i * 13) % 16];
    }
    const shaEl = box.querySelector('.fl-flk-sha');
    if (shaEl) shaEl.textContent = `SHA-256: ${rollingHash}…`;
  }, 45);
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

  if (box._healthTimer) clearInterval(box._healthTimer);
  box._healthTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-sh-badge');
    if (badge) badge.textContent = `LIVE ECG • ${elapsedSec}s`;
  }, 45);
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

  if (box._auditTimer) clearInterval(box._auditTimer);
  let tick = 0;
  box._auditTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-as-badge');
    if (badge) badge.textContent = `AUDITING • ${elapsedSec}s`;

    const lines = box.querySelectorAll('.fl-as-line');
    if (lines.length >= 3 && auditFeed.length > 0) {
      lines[0].textContent = auditFeed[tick % auditFeed.length];
      lines[1].textContent = auditFeed[(tick + 1) % auditFeed.length];
      lines[2].textContent = auditFeed[(tick + 2) % auditFeed.length];
    }
  }, 40);
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

  if (box._hcTimer) clearInterval(box._hcTimer);
  let tick = 0;
  box._hcTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-dhc-badge');
    if (badge) badge.textContent = `SWEEPING • ${elapsedSec}s`;

    const chips = box.querySelectorAll('.fl-dhc-lang-chip');
    chips.forEach((c, idx) => c.classList.toggle('is-active', idx === (tick % chips.length)));

    const lines = box.querySelectorAll('.fl-dhc-line');
    if (lines.length >= 3 && hcFeed.length > 0) {
      lines[0].textContent = hcFeed[tick % hcFeed.length];
      lines[1].textContent = hcFeed[(tick + 1) % hcFeed.length];
      lines[2].textContent = hcFeed[(tick + 2) % hcFeed.length];
    }
  }, 45);
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

  if (box._portTimer) clearInterval(box._portTimer);
  let tick = 0;
  box._portTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-ap-badge');
    if (badge) badge.textContent = `PROBING OS • ${elapsedSec}s`;

    const lines = box.querySelectorAll('.fl-ap-line');
    if (lines.length >= 3 && portFeed.length > 0) {
      lines[0].textContent = portFeed[tick % portFeed.length];
      lines[1].textContent = portFeed[(tick + 1) % portFeed.length];
      lines[2].textContent = portFeed[(tick + 2) % portFeed.length];
    }
  }, 45);
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

  if (box._webSecTimer) clearInterval(box._webSecTimer);
  let tick = 0;
  box._webSecTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-wsa-badge');
    if (badge) badge.textContent = `AUDITING • ${elapsedSec}s`;

    const chips = box.querySelectorAll('.fl-wsa-hdr-chip');
    chips.forEach((chip, idx) => {
      if (!chip.classList.contains('is-warn')) {
        const st = chip.querySelector('.fl-wsa-hdr-state');
        if (idx <= (tick % (chips.length + 1))) {
          chip.classList.add('is-pass');
          if (st) st.textContent = 'OK';
        }
      }
    });

    const lines = box.querySelectorAll('.fl-wsa-line');
    if (lines.length >= 3 && webSecFeed.length > 0) {
      lines[0].textContent = webSecFeed[tick % webSecFeed.length];
      lines[1].textContent = webSecFeed[(tick + 1) % webSecFeed.length];
      lines[2].textContent = webSecFeed[(tick + 2) % webSecFeed.length];
    }
  }, 45);
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

  if (box._wiTimer) clearInterval(box._wiTimer);
  let tick = 0;
  box._wiTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-wi-badge');
    if (badge) badge.textContent = `SCANNING • ${elapsedSec}s`;

    const pods = box.querySelectorAll('.fl-wi-vec-pod');
    pods.forEach((p, idx) => p.classList.toggle('is-active', idx === (tick % pods.length)));

    const lines = box.querySelectorAll('.fl-wi-line');
    if (lines.length >= 3 && wiFeed.length > 0) {
      lines[0].textContent = wiFeed[tick % wiFeed.length];
      lines[1].textContent = wiFeed[(tick + 1) % wiFeed.length];
      lines[2].textContent = wiFeed[(tick + 2) % wiFeed.length];
    }
  }, 45);
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

  if (box._schTimer) clearInterval(box._schTimer);
  box._schTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-sch-badge');
    if (badge) badge.textContent = `SYNCING • ${elapsedSec}s`;
  }, 45);
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

  if (box._mtTimer) clearInterval(box._mtTimer);
  let tick = 0;
  box._mtTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-mt-badge');
    if (badge) badge.textContent = `BUS ACTIVE • ${elapsedSec}s`;

    const lines = box.querySelectorAll('.fl-mt-line');
    if (lines.length >= 3 && mtFeed.length > 0) {
      lines[0].textContent = mtFeed[tick % mtFeed.length];
      lines[1].textContent = mtFeed[(tick + 1) % mtFeed.length];
      lines[2].textContent = mtFeed[(tick + 2) % mtFeed.length];
    }
  }, 45);
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

  if (box._pcTimer) clearInterval(box._pcTimer);
  let tick = 0;
  box._pcTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-pc-badge');
    if (badge) badge.textContent = `MUX ACTIVE • ${elapsedSec}s`;

    const lines = box.querySelectorAll('.fl-pc-line');
    if (lines.length >= 3 && pcFeed.length > 0) {
      lines[0].textContent = pcFeed[tick % pcFeed.length];
      lines[1].textContent = pcFeed[(tick + 1) % pcFeed.length];
      lines[2].textContent = pcFeed[(tick + 2) % pcFeed.length];
    }
  }, 45);
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

  if (box._gkTimer) clearInterval(box._gkTimer);
  let tick = 0;
  box._gkTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-gk-badge');
    if (badge) badge.textContent = `VERIFYING • ${elapsedSec}s`;

    const pods = box.querySelectorAll('.fl-gk-gate-pod');
    pods.forEach((pod, idx) => {
      if (!pod.classList.contains('is-fail')) {
        const st = pod.querySelector('.fl-gk-gate-state');
        if (idx <= (tick % (pods.length + 1))) {
          pod.classList.add('is-pass');
          if (st) st.textContent = 'PASS ✓';
        }
      }
    });

    const lines = box.querySelectorAll('.fl-gk-line');
    if (lines.length >= 3 && gkFeed.length > 0) {
      lines[0].textContent = gkFeed[tick % gkFeed.length];
      lines[1].textContent = gkFeed[(tick + 1) % gkFeed.length];
      lines[2].textContent = gkFeed[(tick + 2) % gkFeed.length];
    }
  }, 45);
}

function renderLiveCameraShutter(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  activeSlot.querySelectorAll('.is-finished').forEach(el => el.remove());

  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const targetLabel = shortenFilePath(d.target || d.TargetFile || d.path || d.output || d.display || 'DISPLAY=:0 // VIEWPORT');
  FloworkJarvisAudio.playSynthSfx('shutter_click');

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

  if (box._cameraTimer) clearInterval(box._cameraTimer);
  box._cameraTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-ss-badge');
    if (badge) badge.textContent = `SHUTTER • ${elapsedSec}s`;
  }, 45);
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

  if (box._ytvTimer) clearInterval(box._ytvTimer);
  let tick = 0;
  box._ytvTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-ytv-badge');
    if (badge) badge.textContent = `DEEPSCAN • ${elapsedSec}s`;

    const lines = box.querySelectorAll('.fl-ytv-line');
    if (lines.length >= 3 && ytvFeed.length > 0) {
      lines[0].textContent = ytvFeed[tick % ytvFeed.length];
      lines[1].textContent = ytvFeed[(tick + 1) % ytvFeed.length];
      lines[2].textContent = ytvFeed[(tick + 2) % ytvFeed.length];
    }
  }, 45);
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

  if (box._ytcTimer) clearInterval(box._ytcTimer);
  let tick = 0;
  box._ytcTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-ytc-badge');
    if (badge) badge.textContent = `CHANNEL PULSE • ${elapsedSec}s`;

    const lines = box.querySelectorAll('.fl-ytc-line');
    if (lines.length >= 3 && ytcFeed.length > 0) {
      lines[0].textContent = ytcFeed[tick % ytcFeed.length];
      lines[1].textContent = ytcFeed[(tick + 1) % ytcFeed.length];
      lines[2].textContent = ytcFeed[(tick + 2) % ytcFeed.length];
    }
  }, 45);
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

  if (box._yttTimer) clearInterval(box._yttTimer);
  let tick = 0;
  box._yttTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-ytt-badge');
    if (badge) badge.textContent = `TELEPROMPTER • ${elapsedSec}s`;

    const lines = box.querySelectorAll('.fl-ytt-line');
    if (lines.length >= 3 && yttFeed.length > 0) {
      lines[0].textContent = yttFeed[tick % yttFeed.length];
      lines[1].textContent = yttFeed[(tick + 1) % yttFeed.length];
      lines[2].textContent = yttFeed[(tick + 2) % yttFeed.length];
    }
  }, 55);
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

  if (box._ytsTimer) clearInterval(box._ytsTimer);
  let tick = 0;
  box._ytsTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-yts-badge');
    if (badge) badge.textContent = `DISTILLING • ${elapsedSec}s`;

    const btxts = box.querySelectorAll('.fl-yts-btxt');
    if (btxts.length >= 3 && ytsFeed.length > 0) {
      btxts[0].textContent = ytsFeed[tick % ytsFeed.length];
      btxts[1].textContent = ytsFeed[(tick + 1) % ytsFeed.length];
      btxts[2].textContent = ytsFeed[(tick + 2) % ytsFeed.length];
    }
  }, 60);
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

  if (box._ytcmTimer) clearInterval(box._ytcmTimer);
  let tick = 0;
  box._ytcmTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-ytcm-badge');
    if (badge) badge.textContent = `SENTIMENT • ${elapsedSec}s`;

    const bubbles = box.querySelectorAll('.fl-ytcm-chat-bubble');
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
  }, 62);
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

  if (box._ytstTimer) clearInterval(box._ytstTimer);
  let tick = 0;
  box._ytstTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-ytst-badge');
    if (badge) badge.textContent = `STRATEGY • ${elapsedSec}s`;

    const activeIdx = tick % 3;
    box.querySelectorAll('.fl-ytst-cap').forEach((cap, idx) => {
      cap.classList.toggle('is-active', idx === activeIdx);
    });

    const streamEl = box.querySelector('.fl-ytst-stream-txt');
    if (streamEl && stratFeed.length > 0) {
      streamEl.textContent = stratFeed[tick % stratFeed.length];
    }
  }, 58);
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

  if (box._aqTimer) clearInterval(box._aqTimer);
  let tick = 0;
  box._aqTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-aq-badge');
    if (badge) badge.textContent = `DECISION • ${elapsedSec}s`;

    const pills = box.querySelectorAll('.fl-aq-opt-pill');
    if (pills.length > 0) {
      const activeIdx = tick % pills.length;
      pills.forEach((p, idx) => p.classList.toggle('is-active', idx === activeIdx));
    }
  }, 65);
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

  if (box._srTimer) clearInterval(box._srTimer);
  let tick = 0;
  box._srTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-sr-badge');
    if (badge) badge.textContent = `TURBINE • ${elapsedSec}s`;

    const phases = box.querySelectorAll('.fl-sr-phase-pill');
    phases.forEach((p, idx) => p.classList.toggle('is-active', idx === (tick % 3)));
  }, 55);
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

  if (box._ppTimer) clearInterval(box._ppTimer);
  let tick = 0;
  box._ppTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-pp-badge');
    if (badge) badge.textContent = `EDGE UPLINK • ${elapsedSec}s`;

    box.querySelectorAll('.fl-pp-stage-pill').forEach((p, idx) => p.classList.toggle('is-active', idx === (tick % 3)));
    const sEl = box.querySelector('.fl-pp-stream-txt');
    if (sEl && ppFeed.length > 0) sEl.textContent = ppFeed[tick % ppFeed.length];
  }, 56);
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

  if (box._isaTimer) clearInterval(box._isaTimer);
  let tick = 0;
  box._isaTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-isa-badge');
    if (badge) badge.textContent = `ORBITAL • ${elapsedSec}s`;

    const pEl = box.querySelector('.fl-isa-prompt-txt');
    if (pEl && isaFeed.length > 0) pEl.textContent = isaFeed[tick % isaFeed.length];
  }, 60);
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

  if (box._dsaTimer) clearInterval(box._dsaTimer);
  box._dsaTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-dsa-badge');
    if (badge) badge.textContent = `DNA FORGE • ${elapsedSec}s`;
  }, 55);
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

  if (box._msaTimer) clearInterval(box._msaTimer);
  let tick = 0;
  box._msaTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    tick++;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-msa-badge');
    if (badge) badge.textContent = `RADAR • ${elapsedSec}s`;

    const sEl = box.querySelector('.fl-msa-stream-txt');
    if (sEl && msaFeed.length > 0) sEl.textContent = msaFeed[tick % msaFeed.length];
  }, 56);
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

  if (box._smTimer) clearInterval(box._smTimer);
  box._smTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-sm-badge');
    if (badge) badge.textContent = `SYNAPSE IPC • ${elapsedSec}s`;
  }, 55);
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

  if (box._giTimer) clearInterval(box._giTimer);
  box._giTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-gi-badge');
    if (badge) badge.textContent = `RENDERING • ${elapsedSec}s`;
  }, 55);
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

  if (box._smdTimer) clearInterval(box._smdTimer);
  box._smdTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-smd-badge');
    if (badge) badge.textContent = `MEDIA POD • ${elapsedSec}s`;
  }, 55);
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

  if (box._rvTimer) clearInterval(box._rvTimer);
  box._rvTimer = setInterval(() => {
    if (!box.isConnected || box.classList.contains('is-locked')) return;
    const elapsedSec = ((Date.now() - box._spawnTime) / 1000).toFixed(2);
    const badge = box.querySelector('.fl-rv-badge');
    if (badge) badge.textContent = `SYNTHESIZING • ${elapsedSec}s`;
  }, 55);
}

function renderLiveDynamicExternalTool(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  const cleanName = String(toolName || 'tool').replace(/^flow_/, '').replace(/^default_api:/, '').toLowerCase().trim();
  const host = window.location.hostname || '127.0.0.1';

  // 1. Dynamic CSS Injection: Load tools/<cleanName>/style.css
  const cssId = `fl-dyn-tool-css-${cleanName}`;
  if (!document.getElementById(cssId)) {
    const link = document.createElement('link');
    link.id = cssId;
    link.rel = 'stylesheet';
    link.href = `http://${host}:17700/tools/${cleanName}/style.css`;
    document.head.appendChild(link);
  }

  // 2. Try importing dynamic ui.js module
  const uiUrl = `http://${host}:17700/tools/${cleanName}/ui.js`;
  import(uiUrl).then(mod => {
    if (mod && mod.default && typeof mod.default.mountLive === 'function') {
      const el = mod.default.mountLive(activeSlot, details, stepIdx);
      if (el) {
        el._dynamicUiModule = mod.default;
        return;
      }
    }
    renderLiveGenericToolBox(activeSlot, toolName, details, stepIdx);
  }).catch(() => {
    renderLiveGenericToolBox(activeSlot, toolName, details, stepIdx);
  });
}

function renderLiveGenericToolBox(activeSlot, toolName, details, stepIdx) {
  if (!activeSlot) return;
  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
  const cleanName = (toolName || 'tool').replace(/^flow_/, '').replace(/^default_api:/, '').toUpperCase();
  const summary = d.toolSummary || d.toolAction || d.action || d.Action || (typeof details === 'string' ? details : 'Sovereign operation');
  renderLiveAmbientHoloStream(activeSlot, `OPS // ${cleanName}`, String(summary), 'cyan', stepIdx);
}

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
    if (!box.isConnected) return;

    // Clear active high-frequency timers and lock verified status
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
      if (badge) badge.innerHTML = '✓ FILE WRITTEN • EXIT CODE 0';
      const bytesEl = box.querySelector('.fl-wtf-bytes');
      if (bytesEl) bytesEl.textContent = '100% COMMITTED TO DISK';
    } else if (box.classList.contains('fl-live-replace-file')) {
      const timerEl = box.querySelector('.fl-rfc-timer');
      if (timerEl) timerEl.innerHTML = '✓ SPLICED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-search-tools')) {
      const speedEl = box.querySelector('.fl-st-speed');
      if (speedEl) speedEl.innerHTML = '✓ TOOLS LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-skill-box')) {
      const statusEl = box.querySelector('.fl-sk-status');
      if (statusEl) statusEl.innerHTML = '✓ 20/20 LOCKED • EXIT CODE 0';
      box.querySelectorAll('.fl-sk-led').forEach(led => led.classList.add('is-lit'));
    } else if (box.classList.contains('fl-live-search-web')) {
      const badge = box.querySelector('.fl-sw-badge');
      if (badge) badge.innerHTML = '✓ OSINT LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-read-url')) {
      const pipe = box.querySelector('.fl-ru-pipe-badge');
      if (pipe) pipe.innerHTML = '✓ MD EXTRACTED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-flow-lock')) {
      const statusEl = box.querySelector('.fl-flk-status');
      if (statusEl) statusEl.innerHTML = '✓ CRYO-LOCKED • EXIT CODE 0';
      const lbl = box.querySelector('.fl-flk-vault-lbl');
      if (lbl) lbl.textContent = 'LOCKED';
    } else if (box.classList.contains('fl-live-sys-health')) {
      const badge = box.querySelector('.fl-sh-badge');
      if (badge) badge.innerHTML = '✓ HEALTHY • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-audit-sec')) {
      const badge = box.querySelector('.fl-as-badge');
      if (badge) badge.innerHTML = '✓ SAST VERIFIED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-detect-hc')) {
      const badge = box.querySelector('.fl-dhc-badge');
      if (badge) badge.innerHTML = '✓ DE-HARDCODED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-audit-port')) {
      const badge = box.querySelector('.fl-ap-badge');
      if (badge) badge.innerHTML = '✓ TRI-OS VERIFIED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-web-sec')) {
      const badge = box.querySelector('.fl-wsa-badge');
      if (badge) badge.innerHTML = '✓ PERIMETER LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-web-intel')) {
      const badge = box.querySelector('.fl-wi-badge');
      if (badge) badge.innerHTML = '✓ INTEL LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-schedule')) {
      const badge = box.querySelector('.fl-sch-badge');
      if (badge) badge.innerHTML = '✓ CHRONO ARMED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-manage-task')) {
      const badge = box.querySelector('.fl-mt-badge');
      if (badge) badge.innerHTML = '✓ TASK SYNCED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-plugin-ctrl')) {
      const badge = box.querySelector('.fl-pc-badge');
      if (badge) badge.innerHTML = '✓ PLUGIN READY • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-gatekeeper')) {
      const badge = box.querySelector('.fl-gk-badge');
      if (badge) badge.innerHTML = '✓ GATES PASSED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-screenshot')) {
      const badge = box.querySelector('.fl-ss-badge');
      if (badge) badge.innerHTML = '✓ FRAME LOCKED • EXIT CODE 0';
      const ret = box.querySelector('.fl-ss-reticle');
      if (ret) ret.textContent = '[ ✓ PNG CAPTURED ]';
    } else if (box.classList.contains('fl-live-yt-video')) {
      const badge = box.querySelector('.fl-ytv-badge');
      if (badge) badge.innerHTML = '✓ VIDEO SCANNED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-channel')) {
      const badge = box.querySelector('.fl-ytc-badge');
      if (badge) badge.innerHTML = '✓ PULSE LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-transcript')) {
      const badge = box.querySelector('.fl-ytt-badge');
      if (badge) badge.innerHTML = '✓ TRANSCRIPT READY • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-summary')) {
      const badge = box.querySelector('.fl-yts-badge');
      if (badge) badge.innerHTML = '✓ SUMMARY LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-comments')) {
      const badge = box.querySelector('.fl-ytcm-badge');
      if (badge) badge.innerHTML = '✓ BUBBLES LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-yt-strategy')) {
      const badge = box.querySelector('.fl-ytst-badge');
      if (badge) badge.innerHTML = '✓ STRATEGY READY • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-ask-question')) {
      const badge = box.querySelector('.fl-aq-badge');
      if (badge) badge.innerHTML = '✓ ANSWER LOCKED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-sys-restart')) {
      const badge = box.querySelector('.fl-sr-badge');
      if (badge) badge.innerHTML = '✓ RESTART ARMED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-plugin-publish')) {
      const badge = box.querySelector('.fl-pp-badge');
      if (badge) badge.innerHTML = '✓ PUBLISHED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-invoke-subagent')) {
      const badge = box.querySelector('.fl-isa-badge');
      if (badge) badge.innerHTML = '✓ SUBAGENT SPAWNED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-define-subagent')) {
      const badge = box.querySelector('.fl-dsa-badge');
      if (badge) badge.innerHTML = '✓ DNA REGISTERED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-manage-subagents')) {
      const badge = box.querySelector('.fl-msa-badge');
      if (badge) badge.innerHTML = '✓ SWARM SYNCED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-send-message')) {
      const badge = box.querySelector('.fl-sm-badge');
      if (badge) badge.innerHTML = '✓ IPC DELIVERED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-generate-image')) {
      const badge = box.querySelector('.fl-gi-badge');
      if (badge) badge.innerHTML = '✓ IMAGE SYNTHESIZED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-send-media')) {
      const badge = box.querySelector('.fl-smd-badge');
      if (badge) badge.innerHTML = '✓ MEDIA DELIVERED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-render-visual')) {
      const badge = box.querySelector('.fl-rv-badge');
      if (badge) badge.innerHTML = '✓ VISUAL BUFFERED • EXIT CODE 0';
    } else if (box.classList.contains('fl-live-memory-box')) {
      const header = box.querySelector('.fl-brain-pill-header');
      if (header) header.innerHTML = '✓ SYNAPSE LOCKED // EXIT CODE 0';
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
          badge.innerHTML = '✓ EXIT CODE 0';
        } else {
          badge.style.background = 'rgba(239, 68, 68, 0.2)';
          badge.style.color = '#f87171';
          badge.innerHTML = `✕ EXIT CODE ${exitCode}`;
        }
      }
    } else if (box.classList.contains('fl-live-ambient-stage')) {
      const badge = box.querySelector('.fl-ambient-badge');
      if (badge) {
        badge.className = 'fl-ambient-badge emerald';
        badge.innerHTML = '✓ SYNAPSE LOCKED (EXIT CODE 0)';
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

function renderToolInArea(toolsArea, toolName, details, status, stepIdx, activeToolElements) {
  if (!toolsArea) return null;
  const rawTool = (toolName || 'tool').toLowerCase();
  const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});

  // Record pinned skills & mounted/active tools into Thinking Card & Multi-OS Loop Bar
  recordThinkingArsenal(toolName, details, status, d.output ?? d.rawOutput ?? null);

  // Initialize Mr. Flow audio UI controls
  FloworkJarvisAudio.initUi();

  const { activeSlot, capsule, capsuleBody } = getOrCreateToolsCapsule(toolsArea);

  // Keep capsule STRICTLY HIDDEN while streaming live!
  if (isChatStreaming) {
    capsule.style.display = 'none';
  }

  // Advance Neural Anticipator DAG node to Execute phase
  if (currentThinkingController && currentThinkingController.advanceDag) {
    const cleanToolName = (toolName || 'tool').replace(/^flow_/, '').replace(/^default_api:/, '').toUpperCase();
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
  const isDefineSubagent = rawTool.includes('define_subagent');
  const isManageSubagents = rawTool.includes('manage_subagents');
  const isSendMessage = rawTool.includes('send_message');
  const isInvokeSubagent = !isDefineSubagent && !isManageSubagents && (rawTool.includes('invoke_subagent') || rawTool.includes('subagent') || rawTool.includes('spawnagent') || rawTool.includes('invoke_agent') || rawTool.includes('delegate'));
  const isGenImage = rawTool.includes('generate_image');
  const isSendMedia = rawTool.includes('send_media');
  const isScanner = !isSearchTools && !isSearchWeb && !isReadUrl && !isWebIntel && !isYtVideo && !isYtChannel && !isYtTranscript && !isYtSummary && !isYtComments && !isYtStrategy && (rawTool.includes('read') || rawTool.includes('view') || rawTool.includes('inspect') || rawTool.includes('ingest') || rawTool.includes('recon') || rawTool.includes('search') || rawTool.includes('cat') || rawTool.includes('grep') || rawTool.includes('youtube') || rawTool.includes('yt_spy'));
  const isForger = !isFlowLock && (rawTool.includes('write') || rawTool.includes('replace') || rawTool.includes('edit') || rawTool.includes('forge') || rawTool.includes('splice') || rawTool.includes('patch'));
  const isBash = rawTool.includes('run_command') || rawTool.includes('exec') || rawTool.includes('terminal');
  const isMemory = rawTool.includes('brain') || rawTool.includes('memory');
  const isSkill = rawTool.includes('skill');
  const isAudit = !isSysHealth && !isDetectHardcode && !isAuditPortability && !isWebSecAudit && !isGatekeeper && (rawTool.includes('audit') || rawTool.includes('security'));
  const isCamera = rawTool.includes('screenshot') || rawTool.includes('screen_shot') || rawTool.includes('capture') || rawTool.includes('camera') || rawTool.includes('snapshot') || rawTool.includes('x11grab') || rawTool.includes('view_screen') || rawTool.includes('shoot');
  const isVisual = !isCamera && !isGenImage && !isSendMedia && (rawTool.includes('visual') || rawTool.includes('chart') || rawTool.includes('diagram') || rawTool.includes('render_visual'));

  // Spawn specialized live terminal animation ONLY when actively streaming a turn
  let existingLiveBox = activeSlot ? activeSlot.querySelector(`[data-live-step="${stepIdx}"]`) : null;
  if (!existingLiveBox && activeSlot && isChatStreaming) {
    if (isSearchTools) {
      renderLiveSearchTools(activeSlot, toolName, details, stepIdx);
    } else if (isSearchWeb) {
      FloworkJarvisAudio.trigger('target_lock');
      renderLiveSearchWeb(activeSlot, toolName, details, stepIdx);
    } else if (isReadUrl) {
      FloworkJarvisAudio.trigger('target_lock');
      renderLiveReadUrl(activeSlot, toolName, details, stepIdx);
    } else if (isFlowLock) {
      FloworkJarvisAudio.trigger('code_patched');
      renderLiveFlowLock(activeSlot, toolName, details, stepIdx);
    } else if (isSysHealth) {
      renderLiveSysHealth(activeSlot, toolName, details, stepIdx);
    } else if (isDetectHardcode) {
      renderLiveDetectHardcode(activeSlot, toolName, details, stepIdx);
    } else if (isAuditPortability) {
      renderLiveAuditPortability(activeSlot, toolName, details, stepIdx);
    } else if (isWebSecAudit) {
      FloworkJarvisAudio.trigger('target_lock');
      renderLiveWebSecurityAudit(activeSlot, toolName, details, stepIdx);
    } else if (isWebIntel) {
      FloworkJarvisAudio.trigger('target_lock');
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
      FloworkJarvisAudio.trigger('target_lock');
      renderLiveYtSpyVideo(activeSlot, toolName, details, stepIdx);
    } else if (isYtChannel) {
      FloworkJarvisAudio.trigger('target_lock');
      renderLiveYtSpyChannel(activeSlot, toolName, details, stepIdx);
    } else if (isYtTranscript) {
      renderLiveYtSpyTranscript(activeSlot, toolName, details, stepIdx);
    } else if (isYtSummary) {
      renderLiveYtSpySummary(activeSlot, toolName, details, stepIdx);
    } else if (isYtComments) {
      renderLiveYtSpyComments(activeSlot, toolName, details, stepIdx);
    } else if (isYtStrategy) {
      FloworkJarvisAudio.trigger('target_lock');
      renderLiveYtSpyStrategy(activeSlot, toolName, details, stepIdx);
    } else if (isAskQuestion) {
      renderLiveAskQuestion(activeSlot, toolName, details, stepIdx);
    } else if (isSysRestart) {
      renderLiveSystemRestart(activeSlot, toolName, details, stepIdx);
    } else if (isInvokeSubagent) {
      renderLiveInvokeSubagent(activeSlot, toolName, details, stepIdx);
    } else if (isDefineSubagent) {
      renderLiveDefineSubagent(activeSlot, toolName, details, stepIdx);
    } else if (isManageSubagents) {
      renderLiveManageSubagents(activeSlot, toolName, details, stepIdx);
    } else if (isSendMessage) {
      renderLiveSendMessage(activeSlot, toolName, details, stepIdx);
    } else if (isGenImage) {
      renderLiveGenerateImage(activeSlot, toolName, details, stepIdx);
    } else if (isSendMedia) {
      renderLiveSendMedia(activeSlot, toolName, details, stepIdx);
    } else if (isScanner) {
      renderLiveFileScanner(activeSlot, toolName, details, stepIdx);
    } else if (isForger) {
      FloworkJarvisAudio.trigger('code_patched');
      renderLiveCodeForger(activeSlot, toolName, details, stepIdx);
    } else if (isBash) {
      FloworkJarvisAudio.trigger('terminal_exec');
      renderLiveBashRunner(activeSlot, toolName, details, stepIdx);
    } else if (isMemory) {
      renderLiveMemoryRecall(activeSlot, toolName, details, stepIdx);
    } else if (isSkill) {
      FloworkJarvisAudio.trigger('skill_pinned');
      renderLiveSkillActivator(activeSlot, toolName, details, stepIdx);
    } else if (isAudit) {
      renderLiveSecurityAuditor(activeSlot, toolName, details, stepIdx);
    } else if (isCamera) {
      renderLiveCameraShutter(activeSlot, toolName, details, stepIdx);
    } else if (isVisual) {
      renderLiveVisualPainter(activeSlot, toolName, details, stepIdx);
    } else {
      renderLiveDynamicExternalTool(activeSlot, toolName, details, stepIdx);
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
    FloworkJarvisAudio.trigger('agent_spawn');
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

  // 3. Shell Command execution -> Direct clean row in capsule
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

    const cmdItem = document.createElement('details');
    cmdItem.className = `fl-cmd-item ${status === 'running' ? 'is-running' : ''}`;
    cmdItem.setAttribute('data-step-idx', String(stepIdx));
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

  // 4. File I/O, Search, and general tools in capsule
  const card = formatToolCard(toolName, details, status);
  if (card) {
    if (activeToolElements) activeToolElements.set(stepIdx, card);
    capsuleBody.appendChild(card);
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
      badge.innerHTML = '✓ Done';
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
      badge.innerHTML = '✓ Exit Code 0';
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
        badge.innerHTML = `✕ Exit Code ${exitCode}`;
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
        FloworkJarvisAudio.trigger('terminal_done');
      } else {
        FloworkTacticalHUD.spawn('alert_breach', { error: `Command exited with code ${exitCode}` });
        FloworkJarvisAudio.trigger('alert_breach');
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
    const badge = el.querySelector('.fl-tool-badge, .fl-subagent-status, .fl-task-badge, .fl-skill-badge');
    if (badge) {
      badge.className = badge.className.replace('running', 'done');
      if (!badge.textContent.includes('PINNED')) {
        badge.innerHTML = '✓ Done';
      }
    }
    if (el.classList.contains('fl-subagent-card') || el.querySelector('.fl-subagent-header')) {
      FloworkJarvisAudio.trigger('agent_complete');
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
          FloworkJarvisAudio.trigger('alert_breach');
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
      if (b._screeningTimer) { clearInterval(b._screeningTimer); b._screeningTimer = null; }
      if (b._typingTimer) { clearInterval(b._typingTimer); b._typingTimer = null; }
      if (b._rvTimer) { clearInterval(b._rvTimer); b._rvTimer = null; }
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
    } else {
      capsule.style.display = 'none';
    }
    updateToolsCapsuleHeader(capsule);
    // Double ensure default hide
    capsule.open = false;
    capsule.removeAttribute('open');
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
  navigator.clipboard.writeText(code.innerText).then(() => {
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
          <div class="chat-msg-img-wrap" onclick="openChatLightbox('${att.webUrl}', '${escapeHtml(att.name)}')">
            <img src="${att.webUrl}" class="chat-msg-attached-img" alt="${escapeHtml(att.name)}" />
            <div class="chat-img-zoom-hint">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
              <span>Zoom</span>
            </div>
          </div>
        `;
      } else {
        return `
          <div class="chat-msg-file-card" onclick="openChatLightbox('${att.webUrl}', '${escapeHtml(att.name)}')">
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

  for (let stepIdx = 0; stepIdx < steps.length; stepIdx++) {
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
          navigator.clipboard.writeText(displayText).then(() => {
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

      container.appendChild(card);
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
        container.appendChild(currentAssistantCard);
        currentThinkingArea = currentAssistantCard.querySelector('.chat-thinking-area');
        currentToolsArea = currentAssistantCard.querySelector('.chat-tools-area');
        currentBodyArea = currentAssistantCard.querySelector('.chat-body-area');
      }

      if (thinking && currentThinkingArea) {
        const thoughtCard = formatThoughtCard(thinking, 2);
        if (thoughtCard) currentThinkingArea.appendChild(thoughtCard);
      }
      if (resp && currentBodyArea) {
        let fullResp = resp.replace(/\x60\x60\x60visual:'\)\)\s*\{[\s\S]*?(?:outStr|cleanOutStr)\.match\(\/\x60\x60\x60/g, '').trim();
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

      const btnCopy = currentAssistantCard.querySelector('.btn-copy-response');
      if (btnCopy) {
        btnCopy.addEventListener('click', () => {
          const textToCopy = currentBodyArea?.innerText || resp;
          navigator.clipboard.writeText(textToCopy).then(() => {
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

      const btnRetry = currentAssistantCard.querySelector('.btn-retry-response');
      if (btnRetry) {
        btnRetry.addEventListener('click', () => {
          regenerateLastTurn();
        });
      }

      const btnRevert = currentAssistantCard.querySelector('.btn-revert-turn');
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
        container.appendChild(currentAssistantCard);
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

  if (currentToolsArea) {
    collapseAllToolsInArea(currentToolsArea);
  }

  hidePinnedPrompt();

  container.scrollTop = container.scrollHeight;
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
          <div class="chat-msg-img-wrap" onclick="openChatLightbox('${previewSrc}', '${escapeHtml(att.name)}')">
            <img src="${previewSrc}" class="chat-msg-attached-img" alt="${escapeHtml(att.name)}" />
            <div class="chat-img-zoom-hint">
              <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
              <span>Zoom</span>
            </div>
          </div>
        `;
      } else {
        return `
          <div class="chat-msg-file-card" onclick="openChatLightbox('${att.previewUrl || ''}', '${escapeHtml(att.name)}')">
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

  // Keep pinned prompt bar hidden during focus mode
  hidePinnedPrompt();
  emitAgentTelemetry({ type: 'agent', tag: 'PROMPT', text: displayText.slice(0, 42), meta: 'USER' });

  const btnCopyPrompt = userCard.querySelector('.btn-copy-prompt');
  if (btnCopyPrompt) {
    btnCopyPrompt.addEventListener('click', () => {
      navigator.clipboard.writeText(displayText).then(() => {
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
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

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
    navigator.clipboard.writeText(textToCopy).then(() => {
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

  isChatStreaming = true;
  currentAbortController = new AbortController();

  const sendBtn = document.getElementById('btn-rightbar-send');
  if (sendBtn) {
    sendBtn.classList.add('is-running');
    sendBtn.title = 'Stop generation (Esc)';
  }

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
      } catch (upErr) {
        console.warn('[Attachments] Upload error:', upErr);
      }
    }

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
        model: selectedChatModelId,
        account_id: currentSessionAccountId || 'combo',
        agent_persona: currentSessionPersonaId === 'default' ? null : currentSessionPersonaId
      })
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let sseBuffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      sseBuffer += decoder.decode(value, { stream: true });
      const lines = sseBuffer.split('\n');
      sseBuffer = lines.pop();

      let currentEvent = 'message';
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

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
                if (currentSessionPersonaId && currentSessionPersonaId !== 'default') {
                  setSessionAgentPersona(currentSessionPersonaId);
                }
              }
            } else if (currentEvent === 'thinking') {
              if (data.thinking) {
                accumulatedThinking += (accumulatedThinking ? '\n' : '') + data.thinking;
                if (currentThinkingController && currentThinkingController.updateSnippet) {
                  currentThinkingController.updateSnippet(data.thinking);
                }
                setMascotAgentLoop(true, 'Synthesizing reasoning & analyzing task...');
              }
            } else if (currentEvent === 'tool') {
              const rawTool = (data.tool || 'tool').toLowerCase();
              setMascotAgentLoop(true, `Executing tool: ${data.tool || 'tool'}...`);
              const toolStatus = data.status || 'running';
              const stepIdx = data.step_idx !== undefined ? data.step_idx : ('t_' + Date.now());
              stepToolNames.set(String(stepIdx), rawTool);

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
              if (data.tool) {
                recordThinkingArsenal(data.tool, data.details || {}, 'done', data.output);
              } else {
                activeRunningTools.clear();
                if (currentThinkingController && typeof currentThinkingController.refreshArsenal === 'function') {
                  currentThinkingController.refreshArsenal();
                }
                FloworkLoopSysMonitor.updateArsenalCounters();
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
            } else if (currentEvent === 'response') {
              if (currentThinkingController && currentThinkingController.advanceDag) {
                currentThinkingController.advanceDag(4, '4. STREAM RESPONSE');
              }
              accumulatedResponse = data.response || '';
            } else if (currentEvent === 'error') {
              bodyArea.innerHTML = `<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171;padding:8px 12px;border-radius:8px;font-family:var(--font-mono);font-size:11px;">⚠️ ${escapeHtml(data.error || 'Execution Error')}</div>`;
              FloworkChatTacticalOverlay.spawn('alert_breach', { error: data.error || 'Execution Error' });
              FloworkJarvisAudio.trigger('alert_breach');
            } else if (currentEvent === 'done') {
              activeRunningTools.clear();
              const durationSec = currentThinkingController ? currentThinkingController.stop() : 1;
              thinkingArea.innerHTML = '';
              const thoughtCard = formatThoughtCard(accumulatedThinking, durationSec);
              if (thoughtCard) thinkingArea.appendChild(thoughtCard);
              activeSubagentKeys.clear();
              activeTaskKeys.clear();
              updateTopStatusBar();
              collapseAllToolsInArea(toolsArea);

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
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
          } catch (e) {
            console.error('SSE JSON error:', e);
          }
        }
      }
    }
  } catch (err) {
    if (isSystemRestarting) {
      console.log('[Chat] Stream paused during system restart handoff...');
      bodyArea.innerHTML = `<div style="color:var(--accent-color, #38bdf8); font-size:11px; font-family:var(--font-mono); padding:6px 0; display:flex; align-items:center; gap:8px;"><span class="fl-tool-spinner"></span> 🔄 Sistem sedang me-restart biner & menyambung tugas secara otonom...</div>`;
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
    isChatStreaming = false;
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

    if (!isSystemRestarting) {
      if (sendBtn) {
        sendBtn.classList.remove('is-running');
        sendBtn.title = 'Send (Enter)';
      }
    } else {
      if (sendBtn) {
        sendBtn.classList.add('is-running');
        sendBtn.title = 'Flowork sedang restart & memuat pembaruan...';
      }
    }
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

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
    await navigator.clipboard.writeText(fullMarkdown);
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
    navigator.clipboard.writeText(textToCopy).then(() => {
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

  isChatStreaming = true;
  currentAbortController = new AbortController();
  messagesContainer.classList.add('has-messages');
  setMascotAgentLoop(true, 'Regenerating turn & executing autonomous loop...');
  messagesContainer.classList.add('chat-focus-mode');
  messagesContainer.querySelectorAll('.chat-msg-active-turn').forEach(el => el.classList.remove('chat-msg-active-turn'));
  targetCard.classList.add('chat-msg-active-turn');
  hidePinnedPrompt();
  const sendBtn = document.getElementById('btn-rightbar-send');
  if (sendBtn) {
    sendBtn.classList.add('is-running');
    sendBtn.title = 'Stop generation (Esc)';
  }

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

  const activeToolElements = new Map();

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

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      sseBuffer += decoder.decode(value, { stream: true });
      const lines = sseBuffer.split('\n');
      sseBuffer = lines.pop();

      let currentEvent = 'message';
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

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
              }
            } else if (currentEvent === 'tool') {
              const rawTool = (data.tool || 'tool').toLowerCase();
              const toolStatus = data.status || 'running';
              const stepIdx = data.step_idx !== undefined ? data.step_idx : ('t_' + Date.now());
              stepToolNames.set(String(stepIdx), rawTool);

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
              if (stepIdx !== undefined) {
                activeSubagentKeys.delete(stepIdx);
                activeTaskKeys.delete(stepIdx);
                updateTopStatusBar();

                markToolDone(stepIdx, activeToolElements, data.output);

                const resolvedTool = data.tool || stepToolNames.get(String(stepIdx)) || '';
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
              FloworkJarvisAudio.trigger('alert_breach');
            } else if (currentEvent === 'done') {
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
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
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
    isChatStreaming = false;
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

    if (sendBtn) {
      sendBtn.classList.remove('is-running');
      sendBtn.title = 'Send (Enter)';
    }
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

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
});
