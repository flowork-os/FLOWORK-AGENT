---
trigger_id: "PLUGIN-YT-DOWNLOADER-TRIGGER"
name: "YouTube & Suno Downloader Ambient Trigger"
scopes:
  - "universal_all"
events:
  - "media_download"
  - "video_extraction"
  - "youtube_rip"
categories:
  - "CAT-010"
keywords:
  - "youtube"
  - "download"
  - "yt-dlp"
  - "mp3"
  - "mp4"
  - "suno"
  - "audio_extractor"
  - "media_rip"
exclude_keywords:
  - "screen_record"
  - "canvas_draw"
conditions:
  - key: "env.is_headless"
    op: "=="
    val: false
---

# YouTube & Suno Downloader Ambient Activation Trigger
<!-- Co-authored-by: Flowork OS <agent@floworkos.com> -->

This trigger manages the ambient recommendation and automated mounting of the YouTube Downloader & Suno Studio Canvas plugin when media downloading or audio extraction workflows are detected.
