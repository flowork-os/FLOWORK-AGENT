<!-- [FL_INDEX: keywords="youtube, rules, guardrails, video_specs, ffmpeg, openmontage, taste_profile, chai_critique" | COT="Operational rules, quality gates, and media constraints for YouTube Automator" | AT="2026-10-26T04:20:00Z"] -->
# 🎬 YouTube Automator Operational Rules & OpenMontage Standards

1. **RULE ZERO (INVIOLABLE STAGED PIPELINE)**:
   - Ad-hoc, single-shot video generation is strictly prohibited.
   - Every production must progress through sequential checkpoints with clear state artifacts before final render.

2. **TASTE PROFILE CONTRACT ENFORCEMENT**:
   - Before composing scenes or generating visuals, you MUST declare a structured `taste_profile`:
     * `motion_intensity` (1-5, default 3): Controls Ken Burns velocity and cut frequency.
     * `information_density` (1-5, default 3): Governs on-screen overlays, text tokens, and focal points.
     * `visual_variance` (1-5, default 3): Regulates color palette shifts across scenes.
     * `palette_discipline`: Explicit HEX color palette. Strictly avoid tacky rainbow gradients or cheap AI color saturations.

3. **FORMAT PURITY & PACING METRICS**:
   - Long-form YouTube: Strictly 1920x1080 (16:9), minimum 30 fps, H.264 / AAC 192kbps.
   - YouTube Shorts: Strictly 1080x1920 (9:16), duration <= 59 seconds.
   - Cut frequency: Shorts scenes MUST transition every 1.8s - 2.8s. Static holds exceeding 3.5s are rejected.

4. **AUDIO-VISUAL SYNC & DSP INTEGRITY**:
   - Audio and video duration must match within +/- 0.5s tolerance. Always probe exact audio duration via ffprobe before computing image hold durations.
   - Loudness standard: Vocal narration must be normalized to -14 s.d. -16 LUFS with True Peak < -1.0 dBTP.

5. **CHAI CRITIQUE PRE-HANDOFF GATE**:
   - Self-audit every deliverable against the CHAI standard:
     * Accurate: Precisely identify timing misalignments or weak hooks.
     * Actionable: Provide deterministic FFmpeg/Script parameter fixes.
     * Calibrated: Avoid total rewrites when minor parameter adjustments suffice.

6. **STRICT STORAGE ISOLATION & SANCTITY OF @LOCK**:
   - All generated media (audio, video, srt, images) MUST be placed in `.FL_BIN/scratch/youtube/` or explicit user output directory. Never dump raw binaries into repo root.
   - Never modify or remove locked core directives.\n