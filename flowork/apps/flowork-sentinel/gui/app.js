// Flowork Sentinel Dashboard Controller
document.addEventListener('DOMContentLoaded', () => {
  let sessions = [];
  let selectedSessionId = null;
  let currentSynthesizedData = null;

  const sessionsContainer = document.getElementById('sessions-container');
  const sessionCountEl = document.getElementById('session-count');
  const activeTitle = document.getElementById('active-session-title');
  const activeDomain = document.getElementById('active-session-domain');
  const timelineContainer = document.getElementById('timeline-container');
  const eventStats = document.getElementById('event-stats');
  const btnSynthesize = document.getElementById('btn-synthesize');
  const btnDeploy = document.getElementById('btn-deploy');
  const btnRefresh = document.getElementById('btn-refresh-sessions');

  const codeSkillPreview = document.getElementById('code-skill-preview');
  const codeScriptPreview = document.getElementById('code-script-preview');
  const tabSkillContent = document.getElementById('tab-skill-content');
  const tabScriptContent = document.getElementById('tab-script-content');

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tab = btn.dataset.tab;
      if (tab === 'skill') {
        tabSkillContent.style.display = 'block';
        tabScriptContent.style.display = 'none';
      } else {
        tabSkillContent.style.display = 'none';
        tabScriptContent.style.display = 'block';
      }
    });
  });

  // Fetch Sessions
  async function loadSessions() {
    try {
      const res = await fetch('/api/sessions');
      const data = await res.json();
      sessions = data.sessions || [];
      sessionCountEl.textContent = sessions.length;
      renderSessionList();
    } catch (err) {
      console.warn('Failed to load sessions:', err);
    }
  }

  function renderSessionList() {
    sessionsContainer.innerHTML = '';
    if (sessions.length === 0) {
      sessionsContainer.innerHTML = '<div class="empty-state">No sessions recorded yet. Start one via the browser extension!</div>';
      return;
    }

    sessions.forEach(sess => {
      const card = document.createElement('div');
      card.className = `session-card ${sess.id === selectedSessionId ? 'active' : ''}`;
      card.innerHTML = `
        <div class="card-title">${sess.name}</div>
        <div class="card-meta">
          <span class="card-domain">🌐 ${sess.domain || 'web'}</span>
          <span>⚡ ${sess.event_count || 0} events</span>
        </div>
      `;
      card.addEventListener('click', () => selectSession(sess.id));
      sessionsContainer.appendChild(card);
    });
  }

  async function selectSession(id) {
    selectedSessionId = id;
    renderSessionList();

    const sess = sessions.find(s => s.id === id);
    if (!sess) return;

    activeTitle.textContent = sess.name;
    activeDomain.textContent = `Target Domain: ${sess.domain || 'web'}`;
    btnSynthesize.disabled = false;
    btnDeploy.disabled = true;

    // Fetch full session details
    try {
      const res = await fetch(`/api/sessions`);
      // Re-fetch to find session with events
      timelineContainer.innerHTML = '<div class="empty-timeline">Loading captured events...</div>';
      
      // Request synthesis preview if already exists
      renderTimelineForSession(sess);
    } catch (err) {
      console.error(err);
    }
  }

  function renderTimelineForSession(sess) {
    // If the session has event list
    const events = sess.events || [];
    eventStats.textContent = `${events.length} actions captured`;
    timelineContainer.innerHTML = '';

    if (events.length === 0) {
      timelineContainer.innerHTML = '<div class="empty-timeline">Tidak ada aksi tercatat dalam sesi ini.</div>';
      return;
    }

    events.forEach((ev, idx) => {
      const item = document.createElement('div');
      const typeClass = ev.type === 'network_request' ? 'network' : (ev.type === 'input' ? 'input' : '');
      item.className = `timeline-item ${typeClass}`;
      item.innerHTML = `
        <div class="item-header">
          <span class="item-badge ${typeClass}">#${idx + 1} [${ev.type}]</span>
          <span>${new Date(ev.timestamp).toLocaleTimeString()}</span>
        </div>
        <div class="item-body">
          ${ev.selector ? `<span class="item-selector">${ev.selector}</span>` : ''}
          ${ev.value ? ` Value: <strong>"${ev.value}"</strong>` : ''}
          ${ev.text ? ` Text: <em>"${ev.text}"</em>` : ''}
          ${ev.url ? ` <br><small style="color: #64748b">${ev.url}</small>` : ''}
        </div>
      `;
      timelineContainer.appendChild(item);
    });
  }

  // Synthesize Action
  btnSynthesize.addEventListener('click', async () => {
    if (!selectedSessionId) return;
    btnSynthesize.disabled = true;
    btnSynthesize.textContent = '⚡ Synthesizing Intent & Steps...';

    try {
      const res = await fetch(`/api/synthesize/${selectedSessionId}`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'ok') {
        currentSynthesizedData = data;
        codeSkillPreview.textContent = data.preview_skill;
        codeScriptPreview.textContent = data.preview_script;
        btnDeploy.disabled = false;
        alert(`Synthesis Complete! Extracted ${data.summary.steps} steps & ${data.summary.network_calls} network endpoints.`);
      } else {
        alert(data.message || 'Synthesis failed');
      }
    } catch (err) {
      alert('Synthesis request error: ' + err.message);
    } finally {
      btnSynthesize.disabled = false;
      btnSynthesize.textContent = '⚡ Synthesize to SKILL.md';
    }
  });

  // Deploy Action
  btnDeploy.addEventListener('click', async () => {
    if (!selectedSessionId || !currentSynthesizedData) return;
    btnDeploy.disabled = true;
    btnDeploy.textContent = '🚀 Deploying...';

    try {
      const sess = sessions.find(s => s.id === selectedSessionId);
      const cleanName = (sess?.name || selectedSessionId).toLowerCase().replace(/[^a-z0-9_]/g, '_');

      const res = await fetch('/api/deploy-skill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: selectedSessionId,
          skill_name: cleanName
        })
      });
      const data = await res.json();
      if (data.status === 'ok') {
        alert(`SUCCESS! Skill deployed to Flowork OS:\n${data.target_dir}/SKILL.md\n\nYour autonomous agents can now execute this skill!`);
      } else {
        alert(data.message || 'Deploy failed');
      }
    } catch (err) {
      alert('Deploy error: ' + err.message);
    } finally {
      btnDeploy.disabled = false;
      btnDeploy.textContent = '🚀 Deploy to Flowork Skills';
    }
  });

  btnRefresh.addEventListener('click', loadSessions);

  // Auto poll sessions
  loadSessions();
  setInterval(loadSessions, 5000);
});
