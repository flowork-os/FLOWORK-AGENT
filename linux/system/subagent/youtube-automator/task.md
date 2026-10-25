<!-- [FL_INDEX: keywords="youtube, task, workflow, step_by_step, openmontage_pipeline, video_lifecycle" | COT="6-stage execution lifecycle for autonomous YouTube production based on OpenMontage" | AT="2026-10-26T04:20:00Z"] -->
# 🎬 YouTube Automation Execution Lifecycle (6-Stage Staged Pipeline)

1. **STAGE 1: INTAKE & REFERENCE REVERSE-ENGINEERING**
   - Ingest user prompt or reference video via `youtube_spy_video` / `youtube_spy_channel`.
   - Dissect reference hook type (curiosity gap, shock claim, contrarian premise) and calculate scene pacing.
   - Propose 2-3 original creative angles that adapt the structure without copying content.

2. **STAGE 2: TASTE PROFILE SPECIFICATION**
   - Define concrete creative parameters:
     * `design_read`, `motion_intensity` (1-5), `information_density` (1-5), `visual_variance` (1-5).
     * Set explicit color palette and typography rules.

3. **STAGE 3: SCRIPTING & RETENTION ENGINEERING**
   - Write script using `yt_script_forge` or direct synthesis:
     * First 3 seconds: Inescapable hook statement (no greetings, no intro logos).
     * Body: Micro-payoffs every 5-7 seconds to defeat drop-off.
     * Climax & Loop: Seamless outro that effortlessly loops back into the hook for Shorts.

4. **STAGE 4: NEURAL AUDIO & DSP MASTERING**
   - Synthesize narration using high-clarity Edge-TTS voices (e.g. `id-ID-ArdiNeural` / `en-US-ChristopherNeural`).
   - Extract exact audio duration and calibrate loudness to -14 LUFS.
   - Generate word-boundary aligned subtitles (`.srt` / `.ass`).

5. **STAGE 5: VIDEO COMPOSITION & STITCHING**
   - Programmatically assemble visual assets via `yt_media_forge` or native FFmpeg:
     * Dynamic Ken Burns pan/zoom scaled according to `motion_intensity`.
     * High-contrast kinetic subtitle overlays formatted to target aspect ratio.

6. **STAGE 6: CHAI REVIEWER QUALITY GATE**
   - Verify audio-video sync (<0.5s delta), loudness levels, and visual contrast.
   - Ensure render completes with Exit Code 0 and file size conforms to platform limits.\n