# Flowork OS Sovereign Plugins Repository (Linux)

Official repository for verified polyglot extensions and sovereign plugins for Flowork OS on Linux.

## Verified Sovereign Plugins

| Plugin | ID | Version | Category | Description | Port |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sovereign Chess Arena** | `chess` | `1.0.0` | Games & Strategy | Dual-Actor Chess Arena: Human vs Agent AI in real-time. | `17820` |
| **Diffusion Video Studio** | `video-editor` | `1.0.0` | Media & Video | Multi-Track WebCodecs & FFmpeg Video Editor with AI Editing Agent. | `5174` |
| **X-Cutter Video Studio** | `x-cutter` | `1.0.0` | Media & Video | High-performance Non-Linear Video Editor & Lossless Studio. | `17898` |
| **X-Studio DAW** | `x-studio` | `1.0.1` | Media & Audio | Professional Digital Audio Workstation, Multitrack Mixer & DSP Suite. | `17897` |
| **YouTube Downloader & Suno Studio** | `yt-downloader` | `1.2.0` | Media & Network | Sovereign YouTube Video/Audio Extractor with 59s Suno DSP ramp. | `17895` |

## Plugin Architecture

Each plugin follows the Flowork OS Sovereign Nano-Modular Plugin Specification:
- **`plugin.manifest.json`**: Agnostic manifest defining entry points, IPC, and capabilities.
- **`SKILL.md`**: Runbook and SOP for AI agent integration.
- **IPC Protocol**: Dynamic port allocation via `$FLOWORK_APP_PORT`.
- **Zero Zombie**: Graceful shutdown on host termination signals.

---
Co-authored-by: Flowork OS <agent@floworkos.com>
