---
name: openreel_video_editor
title: OpenReel Sovereign Video Editor Architecture & Operational Standard
description: Authoritative SOP and engineering specification for OpenReel Video Editor, timeline sequencing, visual motion effects, audio mixing, and FFmpeg render pipelines.
author: "floworkos.com"
version: "1.0.0"
keywords:
  - openreel
  - video_editor
  - timeline_engine
  - multi_track
  - video_sequencing
  - motion_graphics
  - ffmpeg
  - ffprobe
  - canvas_stage
  - sticky_overlay
  - audio_mixing
  - render_pipeline
  - frame_accuracy
  - timecode_scrubbing
  - clip_slicing
  - media_pool
  - rest_api
  - dynamic_port
  - strict_english_ui
  - zero_zombie
---

# OpenReel Video Editor: Canvas Engineering Runbook

## 1. Architectural Overview
OpenReel Video Editor bridges a lightweight, responsive browser-based canvas timeline UI (`gui/index.html`) with a sovereign Node.js / FFmpeg background rendering server (`engine/server.mjs`).

## 2. Capabilities
- **Multi-Track Timeline**: Visual tracks for Video (V1, V2), Audio (A1, A2), and Text/Subtitles (T1).
- **Asset Ingestion**: Ingests local video, audio, and image files safely within Flowork OS workspace.
- **Real-Time Preview**: Frame-accurate preview with play/pause, scrub, playback rate, and split controls.
- **FFmpeg Render Engine**: Native backend concatenation, slicing, transition overlays, and H.264/AAC MP4 export.
- **RESTful Control API**: Endpoints for asset probing (`/api/probe`), project state sync (`/api/project`), and rendering jobs (`/api/render`).

## 3. Server Endpoints
- `GET /api/status`: Health check and system capabilities (FFmpeg status).
- `POST /api/probe`: Probe media duration, codecs, resolution via `ffprobe`.
- `POST /api/render`: Dispatch background video export job via `ffmpeg`.
- `GET /api/jobs/:id`: Query progress percentage and export status of render jobs.

## 4. Verification Protocol
- Run security audit using `audit_security`.
- Verify UI rendering using `screenshot`.
- Verify Exit Code 0 on all engine actions.
