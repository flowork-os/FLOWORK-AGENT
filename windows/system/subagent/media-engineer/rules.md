<!-- [FL_INDEX: keywords="media_engineer, video_rules, audio_dsp, nle_editor, ffmpeg, canvas_guardrails" | purpose="Iron rules and operational boundaries for Flowork OS Media Engineer Subagent"] -->
# 🎞️ MEDIA & CREATIVE ENGINEER IRON RULES & OPERATIONAL GUARDRAILS

<REASON_DISPATCH_TABLE>
| Trigger Keywords | Action Domain | Target SOP Runbook |
| :--- | :--- | :--- |
| video, timeline, track, preview | NLE Video Studio | {engine_root}/apps/flow-studio/ |
| audio, mastering, dsp, eq, limiter | Audio Engineering | {engine_root}/apps/kamidi-mastering/ |
| ffmpeg, transcode, speedramp, extract | FFmpeg Pipeline | {engine_root}/apps/yt-downloader/ |
| canvas, webaudio, smpte, playback | Media Core | {engine_root}/skills/qa/SKILL.md |
</REASON_DISPATCH_TABLE>

### 1. LOGIC & CANVAS SYNCHRONIZATION SACRED RULE
- Video track clips and canvas preview frames MUST always maintain bidirectional synchronization: modifying a track clip updates the canvas frame instantly; dragging or resizing a clip in the canvas preview immediately updates clip transform properties (`scale`, `posX`, `posY`, `rotation`).
- Timeline state changes (drag, split, delete, add) MUST trigger an immediate automatic debounced auto-save to persistent storage so refreshes and reloads never cause state desynchronization.

### 2. DIGITAL SIGNAL PROCESSING (DSP) & WEBAUDIO INTEGRITY
- Audio filtergraphs must prevent clipping (0 dBFS ceiling strictly enforced with lookahead brickwall limiters).
- Parameter updates (cutoff frequency, Q factor, gain, compression threshold) must use WebAudio `setTargetAtTime` or ramp smoothing to eliminate audible clicks or pops.

### 3. FFMPEG PIPELINE & HARDWARE ACCELERATION
- Rendering pipelines must provide clean progress parsing (frame, fps, timecode, bitrate, progress percentage).
- Always ensure temporary render scratch files are isolated in `.FL_BIN/scratch/` and automatically unlinked after completion or on render abort.

### 4. STRICT MULTI-OS PORTABILITY & ZERO HARDCODING
- Strictly zero hardcoded host paths. All media asset URIs and render output targets must be dynamically resolved relative to workspace root or application storage.

### 5. SANCTITY OF @LOCK BOUNDARIES
- Preserved code regions tagged `@lock` or `@freez` must remain strictly untouched.
