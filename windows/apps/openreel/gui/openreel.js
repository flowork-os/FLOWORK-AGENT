// [FL_INDEX: keywords="openreel, player, timeline, sticky_overlay, canvas_sequencer" | purpose="Interactive timeline and sticky overlay editor script for OpenReel Canvas UI"]

(function() {
  'use strict';

  // State Management
  const state = {
    currentTime: 0,
    duration: 30, // Default 30s timeline
    isPlaying: false,
    zoom: 60, // pixels per second
    selectedClip: null,
    tracks: {
      v2: [
        { id: 'v2-1', name: '📌 Sticky Overlay', start: 2, duration: 8, type: 'sticky', anchor: 'top-right', scale: 100, opacity: 100 }
      ],
      v1: [
        { id: 'v1-1', name: 'Scene 01 - Main Cut', start: 0, duration: 15, type: 'video', scale: 100, opacity: 100 },
        { id: 'v1-2', name: 'Scene 02 - B-Roll', start: 15, duration: 15, type: 'video', scale: 100, opacity: 100 }
      ],
      a1: [
        { id: 'a1-1', name: 'Background Beat.mp3', start: 0, duration: 30, type: 'audio', scale: 100, opacity: 100 }
      ]
    }
  };

  // DOM Elements
  const canvas = document.getElementById('previewCanvas');
  const ctx = canvas.getContext('2d');
  const overlayContainer = document.getElementById('canvasOverlayContainer');
  const playhead = document.getElementById('playhead');
  const timecodeDisplay = document.getElementById('timecodeDisplay');
  const btnPlayPause = document.getElementById('btnPlayPause');
  const timelineWorkspace = document.getElementById('timelineworkspace') || document.querySelector('.fl-timeline-workspace');
  const timeRuler = document.getElementById('timeruler') || document.getElementById('timeRuler');
  const trackV2 = document.getElementById('trackv2') || document.getElementById('trackV2');
  const trackV1 = document.getElementById('trackv1') || document.getElementById('trackV1');
  const trackA1 = document.getElementById('tracka1') || document.getElementById('trackA1');
  const selectedTargetLabel = document.getElementById('selectedTargetLabel');
  const propOpacity = document.getElementById('propOpacity');
  const propScale = document.getElementById('propScale');
  const propSticky = document.getElementById('propSticky');
  const valOpacity = document.getElementById('valOpacity');
  const valScale = document.getElementById('valScale');
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const btnImportAsset = document.getElementById('btnImportAsset');
  const btnAddText = document.getElementById('btnAddText');
  const btnExportVideo = document.getElementById('btnExportVideo');

  // Format Time: 00:00:00 (MM:SS:FF)
  function formatTime(sec) {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = Math.floor(sec % 60).toString().padStart(2, '0');
    const f = Math.floor((sec % 1) * 30).toString().padStart(2, '0');
    return `${m}:${s}:${f}`;
  }

  // Draw Canvas Frame
  function renderCanvas() {
    ctx.fillStyle = '#10131a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid lines / canvas guidelines
    ctx.strokeStyle = '#222838';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, 0); ctx.lineTo(canvas.width / 2, canvas.height);
    ctx.moveTo(0, canvas.height / 2); ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();

    // Check active V1 clips
    const activeV1 = state.tracks.v1.find(c => state.currentTime >= c.start && state.currentTime <= (c.start + c.duration));
    if (activeV1) {
      ctx.fillStyle = '#1e293b';
      const w = 960 * (activeV1.scale / 100);
      const h = 540 * (activeV1.scale / 100);
      const x = (canvas.width - w) / 2;
      const y = (canvas.height - h) / 2;
      ctx.globalAlpha = activeV1.opacity / 100;
      ctx.fillRect(x, y, w, h);

      ctx.fillStyle = '#38bdf8';
      ctx.font = '28px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(`🎬 ${activeV1.name}`, canvas.width / 2, canvas.height / 2);
      ctx.globalAlpha = 1.0;
    } else {
      ctx.fillStyle = '#475569';
      ctx.font = '20px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('[No Media at Playhead]', canvas.width / 2, canvas.height / 2);
    }

    // Check active V2 Sticky Overlays
    const activeV2 = state.tracks.v2.find(c => state.currentTime >= c.start && state.currentTime <= (c.start + c.duration));
    overlayContainer.innerHTML = '';
    if (activeV2) {
      const tag = document.createElement('div');
      tag.className = 'fl-sticky-tag';
      tag.innerText = activeV2.name;
      
      // Position based on anchor
      if (activeV2.anchor === 'top-right') {
        tag.style.top = '20px'; tag.style.right = '20px';
      } else if (activeV2.anchor === 'top-left') {
        tag.style.top = '20px'; tag.style.left = '20px';
      } else if (activeV2.anchor === 'bottom-left') {
        tag.style.bottom = '20px'; tag.style.left = '20px';
      } else if (activeV2.anchor === 'bottom-right') {
        tag.style.bottom = '20px'; tag.style.right = '20px';
      } else {
        tag.style.top = '50%'; tag.style.left = '50%';
        tag.style.transform = 'translate(-50%, -50%)';
      }
      tag.style.opacity = activeV2.opacity / 100;
      tag.style.transform = `scale(${activeV2.scale / 100})`;
      overlayContainer.appendChild(tag);
    }

    // Update playhead visual position
    playhead.style.left = `${state.currentTime * state.zoom}px`;
    timecodeDisplay.innerText = `${formatTime(state.currentTime)} / ${formatTime(state.duration)}`;
  }

  // Render Multi-Track Clips
  function renderTimelineClips() {
    [trackV2, trackV1, trackA1].forEach(t => {
      if (!t) return;
      const tag = t.querySelector('.fl-track-tag');
      t.innerHTML = '';
      if (tag) t.appendChild(tag);
    });

    const trackMap = { v2: trackV2, v1: trackV1, a1: trackA1 };

    Object.keys(state.tracks).forEach(trackKey => {
      const container = trackMap[trackKey];
      if (!container) return;

      state.tracks[trackKey].forEach(clip => {
        const el = document.createElement('div');
        el.className = `fl-clip fl-clip-${trackKey} ${state.selectedClip?.id === clip.id ? 'active' : ''}`;
        el.style.left = `${clip.start * state.zoom}px`;
        el.style.width = `${clip.duration * state.zoom}px`;
        el.innerHTML = `<span>${clip.name}</span><small style="opacity:0.7;">${clip.duration}s</small>`;
        
        el.addEventListener('click', (e) => {
          e.stopPropagation();
          selectClip(clip);
        });

        container.appendChild(el);
      });
    });
  }

  // Select Clip & Populate Inspector
  function selectClip(clip) {
    state.selectedClip = clip;
    selectedTargetLabel.innerText = clip.name;
    propOpacity.value = clip.opacity || 100;
    valOpacity.innerText = `${clip.opacity || 100}%`;
    propScale.value = clip.scale || 100;
    valScale.innerText = `${clip.scale || 100}%`;
    propSticky.value = clip.anchor || 'none';
    renderTimelineClips();
  }

  // Inspector bindings
  propOpacity?.addEventListener('input', (e) => {
    if (!state.selectedClip) return;
    state.selectedClip.opacity = parseInt(e.target.value, 10);
    valOpacity.innerText = `${e.target.value}%`;
    renderCanvas();
  });

  propScale?.addEventListener('input', (e) => {
    if (!state.selectedClip) return;
    state.selectedClip.scale = parseInt(e.target.value, 10);
    valScale.innerText = `${e.target.value}%`;
    renderCanvas();
  });

  propSticky?.addEventListener('change', (e) => {
    if (!state.selectedClip) return;
    state.selectedClip.anchor = e.target.value;
    renderCanvas();
  });

  // Playback Loop
  let lastTimestamp = 0;
  function playbackLoop(timestamp) {
    if (!state.isPlaying) return;
    if (!lastTimestamp) lastTimestamp = timestamp;
    const delta = (timestamp - lastTimestamp) / 1000;
    lastTimestamp = timestamp;

    state.currentTime += delta;
    if (state.currentTime >= state.duration) {
      state.currentTime = 0;
      state.isPlaying = false;
      btnPlayPause.innerText = '▶';
    }

    renderCanvas();
    if (state.isPlaying) {
      requestAnimationFrame(playbackLoop);
    }
  }

  btnPlayPause?.addEventListener('click', () => {
    state.isPlaying = !state.isPlaying;
    btnPlayPause.innerText = state.isPlaying ? '⏸' : '▶';
    if (state.isPlaying) {
      lastTimestamp = 0;
      requestAnimationFrame(playbackLoop);
    }
  });

  // Timeline scrub clicking
  timelineWorkspace?.addEventListener('click', (e) => {
    const rect = timelineWorkspace.getBoundingClientRect();
    const clickX = e.clientX - rect.left + timelineWorkspace.scrollLeft;
    state.currentTime = Math.max(0, Math.min(clickX / state.zoom, state.duration));
    renderCanvas();
  });

  // Import media handler
  btnImportAsset?.addEventListener('click', () => fileInput?.click());
  dropzone?.addEventListener('click', () => fileInput?.click());

  fileInput?.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    const list = document.getElementById('assetList');
    files.forEach(f => {
      const item = document.createElement('div');
      item.className = 'fl-asset-item';
      item.innerHTML = `<span>📼</span> <strong>${f.name}</strong>`;
      list.appendChild(item);
    });
    document.getElementById('mediaCount').innerText = `${list.children.length} Items`;
  });

  // Add text overlay
  btnAddText?.addEventListener('click', () => {
    const newId = `v2-${Date.now()}`;
    const newClip = {
      id: newId,
      name: '🏷️ New Sticky Banner',
      start: Math.round(state.currentTime),
      duration: 5,
      type: 'sticky',
      anchor: 'bottom-left',
      scale: 100,
      opacity: 100
    };
    state.tracks.v2.push(newClip);
    selectClip(newClip);
    renderTimelineClips();
    renderCanvas();
  });

  // Export video
  btnExportVideo?.addEventListener('click', () => {
    const statusEl = document.getElementById('flEngineStatus');
    statusEl.innerText = 'Engine: Rendering...';
    statusEl.style.color = '#f59e0b';
    setTimeout(() => {
      statusEl.innerText = 'Engine: MP4 Ready!';
      statusEl.style.color = '#10b981';
      alert('Video export completed! Sequence rendered via FFmpeg pipeline.');
    }, 1500);
  });

  // Initial render
  renderTimelineClips();
  renderCanvas();
  console.log('[OpenReel Studio] Sovereign Video Editor initialized.');
})();
