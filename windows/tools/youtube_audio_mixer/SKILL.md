---
name: youtube-audio-mixer
title: YouTube Audio Auto-Mixing & Broadcast Loudness SOP
version: 1.0.0
description: Standard operating procedure for automated audio mixing, sidechain ducking, speech clarity equalization, and YouTube EBU R128 loudness normalization.
keywords:
  - audio
  - mixing
  - mastering
  - youtube
  - sidechain
  - ducking
  - compression
  - loudnorm
  - broadcast
  - speech
  - voiceover
  - background
  - soundtrack
  - multiplex
  - ffmpeg
  - acoustic
  - leveler
  - equalization
  - podcast
  - normalization
---

# 🎧 YouTube Audio Auto-Mixing & Broadcast Mastering Standard

## 📌 Overview
The `youtube_audio_mixer` tool automates the complete post-production audio mastering chain for content uploaded to YouTube, podcasts, and video presentations. It eliminates the manual effort of keyframing volume faders by applying dynamic sidechain ducking and calibrated loudness normalization.

## 🎚️ Core Signal Chain
1. **Dialogue Conditioning**:
   - 80 Hz 18dB/octave high-pass filter eliminates low-frequency table rumble and wind noise.
   - 3.5 kHz bell equalization (+2.0 dB, Q=1.5) provides vocal presence and intelligibility.
2. **Dynamic Sidechain Ducking**:
   - Background music track is automatically compressed down by -12 dB to -18 dB whenever speech is detected.
   - 15 ms attack prevents cutting off initial consonants; 300 ms release smoothly restores music levels during pauses.
3. **YouTube Loudness Standard (EBU R128 / ITU-R BS.1770-4)**:
   - Target Integrated Loudness: **-14.0 LUFS**.
   - Maximum True Peak Ceiling: **-1.0 dBTP** (prevents inter-sample clipping when converted to YouTube Opus/AAC codecs).
   - Target Loudness Range (LRA): **11 LU**.
4. **Video Multiplexing**:
   - Directly combines mastered audio with video tracks via stream copy (`-c:v copy`), eliminating time-consuming video re-encoding.

## 🛠️ Usage Examples
```bash
# Mix narration with BGM to standard YouTube WAV master:
node tools/youtube_audio_mixer/main.mjs --params '{"voice_file":"voice.wav","bgm_file":"music.mp3","output_file":"master.wav"}'

# Mix audio and multiplex directly into video:
node tools/youtube_audio_mixer/main.mjs --params '{"voice_file":"voice.wav","bgm_file":"music.mp3","video_file":"raw_footage.mp4","output_file":"final_video.mp4"}'
```
