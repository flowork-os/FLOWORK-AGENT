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

  if (pillTitle) pillTitle.textContent = 'CONECTION';
  if (pillModel) pillModel.style.display = 'none';
  if (topbarPill) {
    const count = routerSwitchboardState.totalAccounts;
    topbarPill.title = `CONECTION Switchboard (:${rPort}) • ${count} Accounts • ${selectedChatModelId}`;
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

  const repoLabel = document.getElementById('copilot-repo-label');
  const repoLink = document.getElementById('copilot-repo-link');
  if (data.registry.repo_name || data.registry.repo) {
    const repoName = data.registry.repo_name || data.registry.repo;
    const repoUrl = data.registry.repo_url || `https://github.com/${repoName}`;
    if (repoLabel) repoLabel.textContent = repoName;
    if (repoLink) repoLink.href = repoUrl;
  }

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
// FLOWORK OS — SOVEREIGN COSMIC STARFIELD ENGINE (Zero-CPU, Full-Viewport)
// =============================================================================
function initStarfieldBackground() {
  const canvas = document.getElementById('flw-starfield-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  function renderStars() {
    const width = (canvas.width = window.innerWidth);
    const height = (canvas.height = window.innerHeight);

    ctx.clearRect(0, 0, width, height);

    const STAR_COUNT = 340;
    const starColors = [
      'rgba(0, 229, 255, ',    // Electric Cyan
      'rgba(56, 189, 248, ',   // Sky Blue
      'rgba(192, 132, 252, ',  // Soft Violet
      'rgba(255, 255, 255, ',  // Pure White
      'rgba(0, 242, 254, '    // Neon Turquoise
    ];

    for (let i = 0; i < STAR_COUNT; i++) {
      const x = Math.random() * width;
      const y = Math.random() * height;
      const size = Math.random() * 1.8 + 0.4;
      const color = starColors[Math.floor(Math.random() * starColors.length)];
      const alpha = Math.random() * 0.75 + 0.2;

      ctx.fillStyle = color + alpha + ')';
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fill();

      // Sparkle cross glint for prominent cosmic stars
      if (size > 1.3 && alpha > 0.45) {
        ctx.strokeStyle = color + (alpha * 0.5) + ')';
        ctx.lineWidth = 0.8;
        ctx.beginPath();
        ctx.moveTo(x - 3.5, y); ctx.lineTo(x + 3.5, y);
        ctx.moveTo(x, y - 3.5); ctx.lineTo(x, y + 3.5);
        ctx.stroke();
      }
    }
  }

  renderStars();

  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(renderStars, 150);
  }, { passive: true });
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
  const heroModelBadge = document.querySelector('.ag-hero-model');
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
      <div class="ag-queue-row" data-qid="${q.id}">
        <span class="ag-queue-row-text" title="${escapeHtml(q.text)}">${escapeHtml(q.text)}</span>
        <div class="ag-queue-actions">
          <button class="ag-queue-btn btn-send-now" data-send-qid="${q.id}" title="Send now">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </button>
          <button class="ag-queue-btn btn-edit-queue" data-edit-qid="${q.id}" title="Edit message">
            <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
          </button>
          <button class="ag-queue-btn btn-delete-queue" data-del-qid="${q.id}" title="Delete from queue">
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
    stoppedDiv.className = 'ag-stopped-banner';
    stoppedDiv.innerHTML = '<span class="ag-stopped-icon">⏹</span> Generation stopped by user';
    activeBodyArea.appendChild(stoppedDiv);
  }

  activeSubagentKeys.clear();
  activeTaskKeys.clear();
  updateTopStatusBar();
  hidePinnedPrompt();

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
  if (!u.startsWith('/') && !u.startsWith('http://') && !u.startsWith('https://') && !u.startsWith('data:')) {
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
  const items = Array.isArray(data) ? data : (data.data || data.items || []);
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

  const centerMain = options.centerText || (total > 0 ? String(total) : '0');
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
  const series = payload.series || payload.candles || payload.data || [];
  if (!series.length) return '';
  const symbol = payload.symbol || payload.pair || 'FLOW/USDT';
  const timeframe = payload.timeframe || payload.tf || '1H';
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
  const items = payload.data || payload.items || [];
  let labels = payload.labels || [];
  let values = payload.values || [];
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
  let labels = payload.labels || [];
  let values = payload.values || [];
  if (payload.data && Array.isArray(payload.data)) {
    if (!values.length) values = payload.data.map(d => typeof d === 'number' ? d : Number(d.value || 0));
    if (!labels.length) labels = payload.data.map((d, i) => d.label || d.time || String(i + 1));
  }
  if (!values.length) return '';
  const w = 480, h = 200;
  const padTop = 25, padBottom = 35, padLeft = 20, padRight = 30;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;
  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  const range = (maxV - minV) || 1;
  const scaleY = v => padTop + plotH - ((v - minV) / range) * plotH;
  const colW = plotW / Math.max(1, values.length - 1);

  const points = values.map((v, i) => ({ x: padLeft + i * colW, y: scaleY(v), val: v, lbl: labels[i] || '' }));
  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaD = `${pathD} L ${points[points.length - 1].x} ${padTop + plotH} L ${points[0].x} ${padTop + plotH} Z`;
  const strokeCol = payload.color || '#00f0ff';
  const dots = points.map(p => `<circle cx="${p.x}" cy="${p.y}" r="3" fill="#080e1e" stroke="${strokeCol}" stroke-width="2"><title>${p.lbl}: ${p.val}</title></circle>`).join('');

  return `
    <div class="tactical-line-container">
      <svg viewBox="0 0 ${w} ${h}" class="tactical-line-svg" width="100%">
        <defs>
          <linearGradient id="line-area-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${strokeCol}" stop-opacity="0.35" />
            <stop offset="100%" stop-color="${strokeCol}" stop-opacity="0.0" />
          </linearGradient>
        </defs>
        <path d="${areaD}" fill="url(#line-area-grad)" />
        <path d="${pathD}" fill="none" stroke="${strokeCol}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        ${dots}
      </svg>
    </div>
  `;
}

function renderTacticalChartCard(rawCode, rawLang) {
  const lang = (rawLang || '').toLowerCase().trim();
  let chartType = 'donut';
  if (lang.includes('trading') || lang.includes('candlestick')) chartType = 'trading';
  else if (lang.includes('donut') || lang.includes('pie')) chartType = 'donut';
  else if (lang.includes('bar')) chartType = 'bar';
  else if (lang.includes('line') || lang.includes('area')) chartType = 'line';

  let parsed = null;
  try {
    parsed = JSON.parse(rawCode);
    if (parsed.type) chartType = parsed.type.toLowerCase();
  } catch (_) {
    const lines = rawCode.split('\n').map(l => l.trim()).filter(Boolean);
    const items = [];
    for (const l of lines) {
      const m = l.match(/^([^:,]+)[:=]\s*([0-9.]+)/);
      if (m) items.push({ label: m[1].trim(), value: parseFloat(m[2]) });
    }
    if (items.length) parsed = { data: items };
  }

  if (!parsed) return null;

  let bodyHtml = '';
  if (chartType === 'trading' || chartType === 'candlestick') {
    bodyHtml = generateTradingSvg(parsed);
  } else if (chartType === 'bar') {
    bodyHtml = generateBarSvg(parsed);
  } else if (chartType === 'line' || chartType === 'area') {
    bodyHtml = generateLineSvg(parsed);
  } else {
    bodyHtml = generateDonutSvg(parsed, {
      centerText: parsed.centerText,
      centerSub: parsed.centerSub || 'METRIC'
    });
  }

  if (!bodyHtml) return null;

  const title = parsed.title || `${chartType.toUpperCase()} METRICS`;
  const typeLabel = (chartType === 'trading' || chartType === 'candlestick') ? 'TRADING CANDLESTICK' : chartType.toUpperCase();

  return `
    <div class="chat-chart-card" data-chart-type="${escapeHtml(chartType)}">
      <div class="chart-card-header">
        <span class="chart-card-title">
          <span>📊</span>
          <span>[ CHART // ${escapeHtml(typeLabel)} ] ${escapeHtml(title)}</span>
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
  let formatted = textToRender.replace(/```([a-zA-Z0-9_\-\.:]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const l = lang ? lang.trim().toUpperCase() : 'CODE';
    const rawCode = code.trim();

    // Check if this is a Chart Block
    if (/^(CHART|TRADING|CANDLESTICK|DONUT|PIE|BAR|LINE|AREA)(:|$)/i.test(l)) {
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
    return `\n\n<div class="ag-callout ag-callout-${type.toLowerCase()}"><div class="ag-callout-header"><span class="ag-callout-tag">[!${type}]</span></div><div class="ag-callout-body">${cleanLines.join('<br>')}</div></div>\n\n`;
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

  // Restore code cards
  codeCards.forEach((card, idx) => {
    formatted = formatted.replace('___CODE_BLOCK_' + idx + '___', card);
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

  // Restore Rightbar collapsed preference
  const isRightbarCollapsed = localStorage.getItem('xflow_rightbar_collapsed') === 'true';
  if (isRightbarCollapsed && rightbarChat) {
    rightbarChat.classList.add('collapsed');
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
      const chip = e.target.closest('.ag-chip-btn');
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
      const activeCard = document.querySelector('.ag-subagent-card, .ag-tool-card');
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

  // Input textarea auto-height & enter-to-send / escape-to-stop
  if (chatInput) {
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });

    chatInput.addEventListener('keydown', (e) => {
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

  // On-Demand Sleep: If audio is paused and user is not hovering, draw 1 frame and exit loop!
  if (!isAudioActive && !isMascotHovered) {
    renderSingleMascotFrame();
    mascotAnimId = null;
    return;
  }

  const now = performance.now();
  const targetInterval = isAudioActive ? 33 : 60; // 30 FPS speaking, 16 FPS hover
  if (now - lastMascotRenderTime >= targetInterval) {
    lastMascotRenderTime = now;
    if (mascotClock) {
      const elapsedTime = mascotClock.getElapsedTime();

      mascotMouse.x += (mascotMouse.targetX - mascotMouse.x) * 0.05;
      mascotMouse.y += (mascotMouse.targetY - mascotMouse.y) * 0.05;

      if (mascotControls) mascotControls.update();
      updateMascotAudioEnergy();

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
    <div class="ag-empty-hero flw-mascot-hero" id="chat-empty-hero">
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
  stopChatMascot();
  hidePinnedPrompt();
  clearChatAttachments();
  activeTurnUserCard = null;
  currentChatSessionId = null;
  lastKnownStepFingerprint = '';
  pendingSessionAccountId = 'combo';
  currentSessionAccountId = 'combo';
  currentSessionFailoverPolicy = 'fallback_pool';
  updateAccountPillDisplay();
  const rightbarMessages = document.getElementById('rightbar-messages');
  const rightbarHistoryView = document.getElementById('rightbar-history-view');
  if (rightbarHistoryView) rightbarHistoryView.style.display = 'none';
  if (rightbarMessages) {
    rightbarMessages.style.display = 'flex';
    rightbarMessages.innerHTML = getEmptyHeroHtml();
    requestAnimationFrame(() => {
      initChatMascot();
    });
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
        const steps = s.step_count ? ` • ${s.step_count} steps` : '';
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
  stopChatMascot();
  currentChatSessionId = sessionId;
  lastKnownStepFingerprint = '';
  await fetchSessionBinding(sessionId);
  const rightbarMessages = document.getElementById('rightbar-messages');
  const rightbarHistoryView = document.getElementById('rightbar-history-view');
  if (rightbarHistoryView) rightbarHistoryView.style.display = 'none';
  if (rightbarMessages) {
    rightbarMessages.style.display = 'flex';
    rightbarMessages.innerHTML = '<div style="padding:24px; text-align:center; color:var(--text-dim); font-size:11px;">Loading conversation steps...</div>';
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
// ANTIGRAVITY NATIVE CHAT RENDERERS & CONTROLLERS (Zero Zombie Code)
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

function createThinkingController(container) {
  if (!container) return { stop: () => 1, updateSnippet: () => {} };
  const startTime = Date.now();
  
  container.innerHTML = `
    <div class="ag-thinking-pill">
      <span class="ag-thinking-beacon"></span>
      <span class="ag-thinking-tag">[REASONING // SYNAPSE]</span>
      <span class="ag-thinking-txt">Thinking...</span>
      <span class="ag-thinking-timer">0s</span>
      <span class="ag-thinking-snippet" style="display:none;"></span>
    </div>
  `;
  
  const timerEl = container.querySelector('.ag-thinking-timer');
  const snippetEl = container.querySelector('.ag-thinking-snippet');

  const timerId = setInterval(() => {
    const elapsed = Math.max(1, Math.round((Date.now() - startTime) / 1000));
    if (timerEl) timerEl.textContent = `${elapsed}s`;
  }, 1000);

  return {
    updateSnippet: (text) => {
      if (!snippetEl || !text) return;
      const clean = text.replace(/[\r\n\t]+/g, ' ').trim();
      if (clean.length > 3) {
        snippetEl.style.display = 'inline-block';
        snippetEl.textContent = clean.length > 35 ? clean.slice(0, 33) + '…' : clean;
      }
    },
    stop: () => {
      clearInterval(timerId);
      const totalSec = Math.max(1, Math.round((Date.now() - startTime) / 1000));
      return totalSec;
    }
  };
}

function formatThoughtCard(thinkingText, durationSec = 1) {
  if (!thinkingText || !thinkingText.trim()) return null;
  const card = document.createElement('details');
  card.className = 'ag-thought-card';
  card.innerHTML = `
    <summary class="ag-thought-summary">
      <span class="ag-thought-chevron">›</span>
      <span class="ag-thought-icon">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a8 8 0 0 0-8 8c0 3.5 2 6 4 7v3h8v-3c2-1 4-3.5 4-7a8 8 0 0 0-8-8z"/><line x1="9" y1="22" x2="15" y2="22"/></svg>
      </span>
      <span class="ag-thought-tag">[REASONING // SYNAPSE]</span>
      <span class="ag-thought-label">Thought for ${durationSec}s</span>
      <span class="ag-thought-action">View reasoning</span>
    </summary>
    <div class="ag-thought-content">
      <div class="ag-thought-inner">${escapeHtml(thinkingText.trim())}</div>
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
  card.className = 'ag-subagent-card';
  if (status === 'running') card.setAttribute('open', '');

  card.innerHTML = `
    <summary class="ag-subagent-header">
      <span class="ag-tool-chevron">›</span>
      <span class="ag-subagent-icon">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
      </span>
      <span class="ag-subagent-tag">[SUBAGENT // DISPATCH]</span>
      <span class="ag-subagent-name">${escapeHtml(role)}</span>
      ${model ? `<span class="ag-subagent-model">${escapeHtml(model)}</span>` : ''}
      <span class="ag-tool-badge ${status}">${status === 'running' ? '<span class="ag-tool-spinner"></span> Active' : '✓ Completed'}</span>
    </summary>
    <div class="ag-subagent-body">
      ${prompt ? `<div class="ag-subagent-prompt"><span class="ag-subagent-lbl">DIRECTIVE:</span> <span class="ag-subagent-txt">${escapeHtml(prompt)}</span></div>` : ''}
      ${subagentOutput ? `
      <div class="ag-tool-block">
        <div class="ag-tool-block-header"><span>AUDIT TRACE</span><button class="ag-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div>
        <pre class="ag-tool-code"><code>${escapeHtml(subagentOutput)}</code></pre>
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
  card.className = 'ag-task-card';
  if (status === 'running') card.setAttribute('open', '');

  card.innerHTML = `
    <summary class="ag-task-header">
      <span class="ag-tool-chevron">›</span>
      <span class="ag-task-icon">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      </span>
      <span class="ag-task-tag">[TASK // ${escapeHtml(actionTag)}]</span>
      <span class="ag-task-title">${escapeHtml(title)}</span>
      <span class="ag-tool-badge ${status}">${status === 'running' ? '<span class="ag-tool-spinner"></span> Running' : '✓ Done'}</span>
    </summary>
    <div class="ag-task-body">
      ${taskDetailsStr ? `
      <div class="ag-tool-block">
        <div class="ag-tool-block-header"><span>TASK CONFIG</span><button class="ag-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div>
        <pre class="ag-tool-code"><code>${escapeHtml(taskDetailsStr)}</code></pre>
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

  questions.forEach((qItem, qIdx) => {
    const qBox = document.createElement('div');
    qBox.className = 'ask-question-box';
    qBox.style.cssText = 'background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 14px 16px; display: flex; flex-direction: column; gap: 10px;';

    const qText = document.createElement('div');
    qText.style.cssText = 'font-size: 13.5px; font-weight: 600; color: #f1f5f9; line-height: 1.45;';
    qText.textContent = `${qIdx + 1}. ${qItem.question || 'Pilihan:'}`;
    qBox.appendChild(qText);

    const isMulti = Boolean(qItem.is_multi_select);
    const options = Array.isArray(qItem.options) ? qItem.options : [];
    const optList = document.createElement('div');
    optList.style.cssText = 'display: flex; flex-direction: column; gap: 7px; margin-top: 2px;';

    options.forEach((optText, optIdx) => {
      const label = document.createElement('label');
      label.style.cssText = 'display: flex; align-items: center; gap: 10px; font-size: 13px; color: #cbd5e1; cursor: pointer; padding: 6px 10px; border-radius: 8px; background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.15s;';
      label.onmouseover = () => { label.style.background = 'rgba(14, 165, 233, 0.12)'; label.style.borderColor = 'rgba(56, 189, 248, 0.35)'; };
      label.onmouseout = () => { label.style.background = 'rgba(30, 41, 59, 0.5)'; label.style.borderColor = 'rgba(255, 255, 255, 0.05)'; };

      const input = document.createElement('input');
      input.type = isMulti ? 'checkbox' : 'radio';
      input.name = `ask_q_opt_${qIdx}`;
      input.value = optText;
      input.style.accentColor = '#0ea5e9';
      if (optIdx === 0 && !isMulti) input.checked = true;

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
    writeInInput.className = 'modal-text-input';
    writeInInput.style.cssText = 'height: 32px; font-size: 12px; flex: 1; padding: 4px 10px; border-radius: 6px; background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.12); color: #fff;';
    writeInWrap.appendChild(writeInInput);
    optList.appendChild(writeInWrap);

    qBox.appendChild(optList);
    container.appendChild(qBox);
  });

  const btnClose = document.getElementById('btn-close-ask-modal');
  const btnSkip = document.getElementById('btn-skip-ask-modal');
  const btnSubmit = document.getElementById('btn-submit-ask-modal');

  const closeModal = () => {
    modal.style.display = 'none';
  };

  if (btnClose) btnClose.onclick = closeModal;
  if (btnSkip) btnSkip.onclick = closeModal;

  if (btnSubmit) {
    btnSubmit.onclick = () => {
      const answers = [];
      questions.forEach((qItem, qIdx) => {
        const isMulti = Boolean(qItem.is_multi_select);
        const checkedInputs = container.querySelectorAll(`input[name="ask_q_opt_${qIdx}"]:checked`);
        let selectedVals = Array.from(checkedInputs).map(i => i.value);
        const qBox = container.children[qIdx];
        const writeInInput = qBox ? qBox.querySelector('input[type="text"]') : null;
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

  modal.style.display = 'flex';
}

function formatAskQuestionCard(details, status = 'done') {
  const questions = extractQuestionsFromDetails(details);
  const qCount = questions.length;
  const firstQ = questions[0] ? questions[0].question : 'Interactive consultation requested';

  const card = document.createElement('div');
  card.className = 'ag-tool-card ag-ask-card';
  card.style.cssText = 'border: 1px solid rgba(14, 165, 233, 0.45); background: rgba(14, 165, 233, 0.08); border-radius: 10px; padding: 12px 14px; margin: 8px 0; display: flex; flex-direction: column; gap: 8px;';

  card.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
      <div style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #38bdf8; font-size: 13px;">
        <span style="font-size: 14px;">❓</span>
        <span>[CONSULT // ASK USER]</span>
        <span style="color: #94a3b8; font-weight: 400; font-size: 12px;">(${qCount} question${qCount > 1 ? 's' : ''})</span>
      </div>
      <button class="ag-ask-open-btn" style="background: #0284c7; color: white; border: none; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 5px;">
        <span>Open Dialog</span>
        <span>›</span>
      </button>
    </div>
    <div style="font-size: 13px; color: #e2e8f0; line-height: 1.4; padding-left: 2px;">
      ${escapeHtml(firstQ)}
    </div>
  `;

  const btnOpen = card.querySelector('.ag-ask-open-btn');
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
      output = typeof rawOut === 'object' ? JSON.stringify(rawOut, null, 2) : String(rawOut);
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

  const card = document.createElement('details');
  card.className = 'ag-tool-card';
  if (status === 'running') card.setAttribute('open', '');

  card.innerHTML = `
    <summary class="ag-tool-header">
      <span class="ag-tool-chevron">›</span>
      <span class="ag-tool-icon">${toolIconSvg}</span>
      <span class="ag-tool-tag">[${escapeHtml(toolTag)}]</span>
      <span class="ag-tool-title">${escapeHtml(toolTitle)}</span>
      ${displayArg ? `<code class="ag-tool-cmd">${escapeHtml(displayArg)}</code>` : ''}
      <span class="ag-tool-badge ${status}">${status === 'running' ? '<span class="ag-tool-spinner"></span> Running' : '✓ Done'}</span>
    </summary>
    <div class="ag-tool-details">
      ${fullInput ? `
      <div class="ag-tool-block">
        <div class="ag-tool-block-header"><span>PARAMETERS</span><button class="ag-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div>
        <pre class="ag-tool-code"><code>${escapeHtml(fullInput)}</code></pre>
      </div>` : ''}
      ${output ? `
      <div class="ag-tool-block">
        <div class="ag-tool-block-header"><span>OUTPUT</span><button class="ag-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div>
        <pre class="ag-tool-code"><code>${escapeHtml(output)}</code></pre>
      </div>` : ''}
    </div>
  `;
  return card;
}

function renderToolInArea(toolsArea, toolName, details, status, stepIdx, activeToolElements) {
  if (!toolsArea) return null;
  const rawTool = (toolName || 'tool').toLowerCase();

  // 1. Subagent Spawning -> dedicated card
  if (rawTool.includes('subagent') || rawTool.includes('spawnagent') || rawTool.includes('invoke_agent') || rawTool.includes('delegate')) {
    const card = formatSubagentCard(details, status);
    if (card) {
      if (activeToolElements) activeToolElements.set(stepIdx, card);
      toolsArea.appendChild(card);
    }
    return card;
  }

  // 2. Background Task / Topic -> dedicated card
  if ((rawTool.includes('task') && !rawTool.includes('command')) || rawTool.includes('update_topic') || rawTool.includes('topic')) {
    const card = formatTaskCard(details, status);
    if (card) {
      if (activeToolElements) activeToolElements.set(stepIdx, card);
      toolsArea.appendChild(card);
    }
    return card;
  }

  // 3. Shell Command execution -> Accordion Group (.ag-commands-group)
  if (rawTool.includes('run_command') || rawTool.includes('exec') || rawTool.includes('terminal')) {
    let group = toolsArea.querySelector('.ag-commands-group');
    if (!group) {
      group = document.createElement('details');
      group.className = 'ag-commands-group';
      if (status === 'running') group.setAttribute('open', '');
      group.innerHTML = `
        <summary class="ag-commands-summary">
          <span class="ag-commands-chevron">›</span>
          <span class="ag-commands-icon">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
          </span>
          <span class="ag-commands-tag">[TERMINAL // BASH]</span>
          <span class="ag-commands-label">Running 1 command...</span>
          <span class="ag-commands-badge running"><span class="ag-tool-spinner"></span> Running</span>
        </summary>
        <div class="ag-commands-list"></div>
      `;
      toolsArea.appendChild(group);
    }

    const list = group.querySelector('.ag-commands-list');
    let cmd = '';
    let output = '';
    if (typeof details === 'string') {
      cmd = details;
    } else if (details && typeof details === 'object') {
      cmd = details.commandLine || details.CommandLine || details.command || details.toolAction || details.toolSummary || 'Shell command';
      const rawOut = details.rawOutput ?? details.output ?? details.stdout ?? details.result ?? null;
      if (rawOut !== null && rawOut !== undefined && rawOut !== '') {
        output = typeof rawOut === 'object' ? JSON.stringify(rawOut, null, 2) : String(rawOut);
      }
    }

    const cmdItem = document.createElement('details');
    cmdItem.className = 'ag-cmd-item';
    // Individual command items remain compact (collapsed) by default
    cmdItem.setAttribute('data-step-idx', String(stepIdx));
    
    const hasOutput = output && output.trim().length > 0;
    const stdoutContent = hasOutput
      ? `
        <div class="ag-cmd-stdout-bar">
          <span class="ag-cmd-stdout-title">STDOUT // OUTPUT</span>
          <button class="ag-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button>
        </div>
        <pre class="ag-cmd-stdout"><code>${escapeHtml(output)}</code></pre>
      `
      : `<div class="ag-cmd-empty">(No standard output)</div>`;

    cmdItem.innerHTML = `
      <summary class="ag-cmd-item-header">
        <span class="ag-cmd-item-chevron">›</span>
        <span class="ag-cmd-item-prompt">$</span>
        <span class="ag-cmd-item-title">${escapeHtml(cmd)}</span>
        <span class="ag-tool-badge ${status}">${status === 'running' ? '<span class="ag-tool-spinner"></span> Running' : '✓ Done'}</span>
      </summary>
      <div class="ag-cmd-item-body">
        ${stdoutContent}
      </div>
    `;

    if (list) list.appendChild(cmdItem);
    if (activeToolElements) activeToolElements.set(stepIdx, cmdItem);
    updateCommandsGroupHeader(group);
    return cmdItem;
  }

  // 4. File I/O, Search, and general tools
  const card = formatToolCard(toolName, details, status);
  if (card) {
    if (activeToolElements) activeToolElements.set(stepIdx, card);
    toolsArea.appendChild(card);
  }
  return card;
}

function updateCommandsGroupHeader(group) {
  if (!group) return;
  const items = group.querySelectorAll('.ag-cmd-item');
  const total = items.length;
  if (total === 0) return;

  const runningBadges = group.querySelectorAll('.ag-cmd-item .ag-tool-badge.running');
  const label = group.querySelector('.ag-commands-label');
  const badge = group.querySelector('.ag-commands-badge');

  if (runningBadges.length > 0) {
    if (label) label.textContent = `Running ${total} command${total > 1 ? 's' : ''}...`;
    if (badge) {
      badge.className = 'ag-commands-badge running';
      badge.innerHTML = '<span class="ag-tool-spinner"></span> Running';
    }
  } else {
    if (label) label.textContent = `Ran ${total} terminal command${total > 1 ? 's' : ''}`;
    if (badge) {
      badge.className = 'ag-commands-badge done';
      badge.innerHTML = '✓ Done';
    }
    // Auto-collapse completed commands group once all commands finish
    group.removeAttribute('open');
  }
}

function markToolDone(stepIdx, activeToolElements, outputData) {
  if (stepIdx === undefined || !activeToolElements) return;
  const el = activeToolElements.get(stepIdx);
  if (!el) return;

  if (el.classList.contains('ag-cmd-item')) {
    const badge = el.querySelector('.ag-tool-badge');
    if (badge) {
      badge.className = 'ag-tool-badge done';
      badge.innerHTML = '✓ Done';
    }
    if (outputData !== undefined && outputData !== null) {
      let rawOut = outputData;
      if (typeof outputData === 'object') {
        rawOut = outputData.rawOutput ?? outputData.output ?? outputData.stdout ?? outputData.result ?? outputData;
      }
      const outText = typeof rawOut === 'object' ? JSON.stringify(rawOut, null, 2) : (rawOut ? String(rawOut) : '');
      const body = el.querySelector('.ag-cmd-item-body');
      if (body) {
        if (outText && outText.trim().length > 0) {
          body.innerHTML = `
            <div class="ag-cmd-stdout-bar">
              <span class="ag-cmd-stdout-title">STDOUT // OUTPUT</span>
              <button class="ag-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button>
            </div>
            <pre class="ag-cmd-stdout"><code>${escapeHtml(outText)}</code></pre>
          `;
        } else {
          body.innerHTML = `<div class="ag-cmd-empty">(No standard output)</div>`;
        }
      }
    }
    // Auto-collapse completed command item
    el.removeAttribute('open');
    const group = el.closest('.ag-commands-group');
    if (group) updateCommandsGroupHeader(group);
  } else {
    const badge = el.querySelector('.ag-tool-badge, .ag-subagent-status, .ag-task-badge');
    if (badge) {
      badge.className = badge.className.replace('running', 'done');
      badge.innerHTML = '✓ Done';
    }
    if (outputData !== undefined && outputData !== null) {
      let rawOut = outputData;
      if (typeof outputData === 'object') {
        rawOut = outputData.rawOutput ?? outputData.output ?? outputData.stdout ?? outputData.result ?? outputData;
      }
      const outText = typeof rawOut === 'object' ? JSON.stringify(rawOut, null, 2) : (rawOut ? String(rawOut) : '');
      const detailsBlock = el.querySelector('.ag-tool-details, .ag-subagent-body, .ag-task-body');
      if (detailsBlock && !detailsBlock.querySelector('.ag-tool-block:last-child .ag-tool-code')) {
        const outDiv = document.createElement('div');
        outDiv.className = 'ag-tool-block';
        outDiv.innerHTML = `<div class="ag-tool-block-header"><span>OUTPUT</span><button class="ag-cmd-copy-btn" onclick="copyToolCode(this)">Copy</button></div><pre class="ag-tool-code"><code>${escapeHtml(outText)}</code></pre>`;
        detailsBlock.appendChild(outDiv);
      }
    }
    // Auto-collapse completed tool card
    el.removeAttribute('open');
  }
}

function collapseAllToolsInArea(toolsArea) {
  if (!toolsArea) return;
  
  // Collapse commands group
  toolsArea.querySelectorAll('.ag-commands-group').forEach(group => {
    group.removeAttribute('open');
    updateCommandsGroupHeader(group);
  });
  
  // Collapse command items
  toolsArea.querySelectorAll('.ag-cmd-item').forEach(item => {
    item.removeAttribute('open');
  });

  // Collapse tool cards
  toolsArea.querySelectorAll('.ag-tool-card').forEach(card => {
    card.removeAttribute('open');
  });

  // Collapse subagent cards
  toolsArea.querySelectorAll('.ag-subagent-card').forEach(card => {
    card.removeAttribute('open');
  });

  // Collapse task cards
  toolsArea.querySelectorAll('.ag-task-card').forEach(card => {
    card.removeAttribute('open');
  });

  // Bulk toolbar with accurate step count
  const cmdItems = toolsArea.querySelectorAll('.ag-cmd-item');
  const otherTools = toolsArea.querySelectorAll('.ag-tool-card, .ag-subagent-card, .ag-task-card');
  const totalSteps = cmdItems.length + otherTools.length;
  if (totalSteps >= 1) {
    let toolbar = toolsArea.querySelector('.ag-tools-toolbar');
    if (!toolbar) {
      toolbar = document.createElement('div');
      toolbar.className = 'ag-tools-toolbar';
      toolsArea.prepend(toolbar);
    }
    toolbar.innerHTML = `
      <span class="ag-tools-count"><span class="ag-tools-dot"></span>${totalSteps} step${totalSteps > 1 ? 's' : ''} executed</span>
      <button class="ag-tools-toggle-btn" type="button" onclick="toggleAllToolsInArea(this)">Show logs</button>
    `;
  }
}

window.toggleAllToolsInArea = function(btn) {
  const toolsArea = btn.closest('.chat-tools-area');
  if (!toolsArea) return;
  const isExpanding = btn.textContent.toLowerCase().includes('show');
  
  // Expand/collapse command groups and parent tool cards.
  // Keep individual command items compact (one-line rows) so stdout does not explode!
  toolsArea.querySelectorAll('.ag-commands-group, .ag-tool-card, .ag-subagent-card, .ag-task-card').forEach(el => {
    if (isExpanding) {
      el.setAttribute('open', '');
    } else {
      el.removeAttribute('open');
    }
  });

  btn.textContent = isExpanding ? 'Hide logs' : 'Show logs';
};

window.copyToolCode = function(btn) {
  const block = btn.closest('.ag-tool-block, .ag-cmd-item-body, .ag-subagent-body, .ag-task-body');
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
  container.innerHTML = '';

  let currentAssistantCard = null;
  let currentToolsArea = null;
  let currentBodyArea = null;
  let currentThinkingArea = null;
  let lastUserPromptText = '';

  for (let stepIdx = 0; stepIdx < steps.length; stepIdx++) {
    const s = steps[stepIdx];
    const stepType = s.type || '';

    if (stepType.endsWith('USER_INPUT')) {
      currentAssistantCard = null;
      currentToolsArea = null;
      currentBodyArea = null;
      currentThinkingArea = null;

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
        currentBodyArea.innerHTML = renderMarkdown(resp);
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

  if (lastUserPromptText) {
    showPinnedPrompt(lastUserPromptText);
  }

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

async function executeChatMessage(text, attachmentsToSend = []) {
  if (isChatStreaming) return;
  const messagesContainer = document.getElementById('rightbar-messages');
  if (!messagesContainer) return;

  // Stop 3D mascot animation loop and vocal audio
  stopChatMascot();

  // Remove empty hero placeholder if present
  const emptyHero = messagesContainer.querySelector('#chat-empty-hero, .message.assistant-msg');
  if (emptyHero) emptyHero.remove();

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

  // Pin current user prompt at the top of chat panel
  showPinnedPrompt(displayText);
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
      </div>
    </div>
  `;
  messagesContainer.appendChild(assistantCard);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  const thinkingArea = assistantCard.querySelector('.chat-thinking-area');
  const toolsArea = assistantCard.querySelector('.chat-tools-area');
  const bodyArea = assistantCard.querySelector('.chat-body-area');
  const footerArea = assistantCard.querySelector('.chat-msg-footer');
  const btnCopy = assistantCard.querySelector('.btn-copy-response');
  const btnRetry = assistantCard.querySelector('.btn-retry-response');

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

  isChatStreaming = true;
  currentAbortController = new AbortController();

  const sendBtn = document.getElementById('btn-rightbar-send');
  if (sendBtn) {
    sendBtn.classList.add('is-running');
    sendBtn.title = 'Stop generation (Esc)';
  }

  currentThinkingController = createThinkingController(thinkingArea);
  let accumulatedThinking = '';
  let accumulatedResponse = '';

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
        account_id: currentSessionAccountId || 'combo'
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
                if (pendingSessionAccountId && pendingSessionAccountId !== 'combo') {
                  setSessionBinding(pendingSessionAccountId, currentSessionFailoverPolicy);
                }
              }
            } else if (currentEvent === 'thinking') {
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
              }
            } else if (currentEvent === 'response') {
              accumulatedResponse = data.response || '';
              bodyArea.innerHTML = renderMarkdown(accumulatedResponse);
              footerArea.style.display = 'flex';
            } else if (currentEvent === 'error') {
              bodyArea.innerHTML = `<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171;padding:8px 12px;border-radius:8px;font-family:var(--font-mono);font-size:11px;">⚠️ ${escapeHtml(data.error || 'Execution Error')}</div>`;
            } else if (currentEvent === 'done') {
              const durationSec = currentThinkingController ? currentThinkingController.stop() : 1;
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
            }
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
          } catch (e) {
            console.error('SSE JSON error:', e);
          }
        }
      }
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      bodyArea.innerHTML = `<div style="color:#f87171; font-size:11px; font-family:var(--font-mono); padding:6px 0;">⚠️ Network Error: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    if (currentThinkingController) currentThinkingController.stop();
    isChatStreaming = false;
    currentAbortController = null;
    hidePinnedPrompt();
    activeSubagentKeys.clear();
    activeTaskKeys.clear();
    updateTopStatusBar();
    if (toolsArea) {
      collapseAllToolsInArea(toolsArea);
    }

    if (sendBtn) {
      sendBtn.classList.remove('is-running');
      sendBtn.title = 'Send (Enter)';
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
      const thoughtEl = card.querySelector('.ag-thought-content');
      const text = body ? body.innerText.trim() : '';
      const thought = thoughtEl ? thoughtEl.innerText.trim() : '';

      const toolItems = card.querySelectorAll('.ag-tool-header, .ag-tool-summary');
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
      </div>
    </div>
  `;

  const thinkingArea = targetCard.querySelector('.chat-thinking-area');
  const toolsArea = targetCard.querySelector('.chat-tools-area');
  const bodyArea = targetCard.querySelector('.chat-body-area');
  const footerArea = targetCard.querySelector('.chat-msg-footer');
  const btnCopy = targetCard.querySelector('.btn-copy-response');
  const btnRetry = targetCard.querySelector('.btn-retry-response');

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

  isChatStreaming = true;
  currentAbortController = new AbortController();
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
              }
            } else if (currentEvent === 'tool') {
              const rawTool = (data.tool || 'tool').toLowerCase();
              const toolStatus = data.status || 'running';
              const stepIdx = data.step_idx !== undefined ? data.step_idx : ('t_' + Date.now());

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
              }
            } else if (currentEvent === 'response') {
              accumulatedResponse = data.response || '';
              bodyArea.innerHTML = renderMarkdown(accumulatedResponse);
              footerArea.style.display = 'flex';
            } else if (currentEvent === 'error') {
              bodyArea.innerHTML = `<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171;padding:8px 12px;border-radius:8px;font-family:var(--font-mono);font-size:11px;">⚠️ ${escapeHtml(data.error || 'Execution Error')}</div>`;
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
    isChatStreaming = false;
    currentAbortController = null;
    hidePinnedPrompt();
    activeSubagentKeys.clear();
    activeTaskKeys.clear();
    updateTopStatusBar();
    if (toolsArea) {
      collapseAllToolsInArea(toolsArea);
    }

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
  if (event.data && (event.data.type === 'FLOWORK_PROMPT_DISPATCH' || event.data.type === 'INJECT_PROMPT')) {
    const promptText = event.data.prompt || event.data.text;
    if (promptText) {
      injectPromptIntoChat(promptText, event.data.autoSend !== false);
    }
  }
});


