#!/usr/bin/env node
/**
 * 🏛️ FLOWORK OS SOVEREIGN TOOL: YOUTUBE AUDIO MIXER & MASTERING ENGINE
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 *
 * Implements broadcast-grade automated audio mixing for YouTube:
 * 1. Vocal Conditioning (80Hz High-Pass + Clarity Peak EQ)
 * 2. Sidechain Ducking (Auto-attenuates BGM when dialogue is active)
 * 3. EBU R128 YouTube Loudness Normalization (-14.0 LUFS, -1.0 dBTP True Peak)
 * 4. Zero Re-encode Video Multiplexing (-c:v copy)
 */
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

function parseParams() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try {
      params = JSON.parse(args[pIdx + 1]);
    } catch (e) {
      console.error(JSON.stringify({ status: 'ERROR', error: `Invalid JSON in --params: ${e.message}` }));
      process.exit(1);
    }
  }
  return params;
}

async function runCommand(cmd, args) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', chunk => { stdout += chunk.toString('utf8'); });
    proc.stderr.on('data', chunk => { stderr += chunk.toString('utf8'); });

    proc.on('close', code => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(`Process exited with code ${code}: ${stderr || stdout}`));
      }
    });

    proc.on('error', err => {
      reject(err);
    });
  });
}

function resolveDuckingConfig(depth) {
  switch ((depth || '').toLowerCase()) {
    case 'mild':
      return { threshold: '0.03', ratio: '4', attack: '20', release: '350' };
    case 'deep':
      return { threshold: '0.015', ratio: '8', attack: '10', release: '250' };
    case 'standard':
    default:
      return { threshold: '0.02', ratio: '6', attack: '15', release: '300' };
  }
}

async function main() {
  const params = parseParams();
  const voiceFile = params.voice_file || params.voice;
  const bgmFile = params.bgm_file || params.bgm;
  const outputFile = params.output_file || params.output || params.out;
  const videoFile = params.video_file || params.video;
  const targetLufs = typeof params.target_lufs === 'number' ? params.target_lufs : -14.0;
  const duckingDepth = params.ducking_depth || 'standard';
  const enableVocalEq = params.enable_vocal_eq !== false;

  if (!voiceFile || !bgmFile || !outputFile) {
    console.log(JSON.stringify({
      status: 'FAILED',
      exit_code: 1,
      error: 'Missing required parameters: voice_file, bgm_file, and output_file are mandatory.'
    }, null, 2));
    process.exit(1);
  }

  // Verify input files exist
  const resolvedVoice = path.resolve(voiceFile);
  const resolvedBgm = path.resolve(bgmFile);
  const resolvedOut = path.resolve(outputFile);

  if (!fs.existsSync(resolvedVoice)) {
    console.log(JSON.stringify({
      status: 'FAILED',
      exit_code: 1,
      error: `Voice file not found: ${resolvedVoice}`
    }, null, 2));
    process.exit(1);
  }

  if (!fs.existsSync(resolvedBgm)) {
    console.log(JSON.stringify({
      status: 'FAILED',
      exit_code: 1,
      error: `Background music file not found: ${resolvedBgm}`
    }, null, 2));
    process.exit(1);
  }

  const outDir = path.dirname(resolvedOut);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  const duck = resolveDuckingConfig(duckingDepth);

  // Construct FFmpeg Filter Graph
  // [0:a] is BGM, [1:a] is Voice
  const filterParts = [];

  // 1. Vocal Conditioning (High-Pass 80Hz + Clarity EQ at 3.5kHz) & Stream Split
  if (enableVocalEq) {
    filterParts.push('[1:a]highpass=f=80,equalizer=f=3500:t=q:w=1.5:g=2,asplit=2[vocal_sc][vocal_mix]');
  } else {
    filterParts.push('[1:a]asplit=2[vocal_sc][vocal_mix]');
  }

  // 2. Sidechain Ducking: Apply sidechain compression to BGM triggered by vocal
  filterParts.push(`[0:a][vocal_sc]sidechaincompress=threshold=${duck.threshold}:ratio=${duck.ratio}:attack=${duck.attack}:release=${duck.release}[ducked_bgm]`);

  // 3. Summing & Blending (Mix ducked BGM with conditioned Vocal)
  filterParts.push('[ducked_bgm][vocal_mix]amix=inputs=2:duration=first:normalize=0[mixed_audio]');

  // 4. Mastering Limiter: YouTube Loudness Standard (-14 LUFS, -1.0 dBTP True Peak)
  filterParts.push(`[mixed_audio]loudnorm=I=${targetLufs}:TP=-1.0:LRA=11:print_format=json[master_audio]`);

  const complexFilter = filterParts.join(';');

  const ffmpegArgs = ['-y', '-i', resolvedBgm, '-i', resolvedVoice];

  let isVideoOutput = false;
  if (videoFile && fs.existsSync(path.resolve(videoFile))) {
    const resolvedVideo = path.resolve(videoFile);
    ffmpegArgs.push('-i', resolvedVideo);
    ffmpegArgs.push('-filter_complex', complexFilter);
    ffmpegArgs.push('-map', '2:v:0');
    ffmpegArgs.push('-map', '[master_audio]');
    ffmpegArgs.push('-c:v', 'copy');
    ffmpegArgs.push('-c:a', 'aac', '-b:a', '320k');
    isVideoOutput = true;
  } else {
    ffmpegArgs.push('-filter_complex', complexFilter);
    ffmpegArgs.push('-map', '[master_audio]');
    if (resolvedOut.endsWith('.mp3')) {
      ffmpegArgs.push('-c:a', 'libmp3lame', '-b:a', '320k');
    } else if (resolvedOut.endsWith('.wav')) {
      ffmpegArgs.push('-c:a', 'pcm_s24le');
    } else if (resolvedOut.endsWith('.mp4') || resolvedOut.endsWith('.m4a') || resolvedOut.endsWith('.aac')) {
      ffmpegArgs.push('-c:a', 'aac', '-b:a', '320k');
    }
  }

  ffmpegArgs.push(resolvedOut);

  const startTime = Date.now();
  try {
    const { stderr } = await runCommand('ffmpeg', ffmpegArgs);
    const durationMs = Date.now() - startTime;

    // Parse loudnorm statistics from stderr if available
    let loudnormStats = null;
    const loudnormJsonMatch = stderr.match(/\{[\s\S]*?"input_i"[\s\S]*?"output_i"[\s\S]*?\}/);
    if (loudnormJsonMatch) {
      try {
        const parsedMetrics = JSON.parse(loudnormJsonMatch[0]);
        loudnormStats = {
          input_integrated_lufs: parseFloat(parsedMetrics.input_i),
          output_integrated_lufs: parseFloat(parsedMetrics.output_i),
          output_true_peak_dbtp: parseFloat(parsedMetrics.output_tp),
          output_lra_lu: parseFloat(parsedMetrics.output_lra)
        };
      } catch (_) {}
    }

    const stat = fs.statSync(resolvedOut);

    console.log(JSON.stringify({
      status: 'SUCCESS',
      exit_code: 0,
      output_file: resolvedOut,
      output_size_bytes: stat.size,
      processing_time_ms: durationMs,
      target_standard: 'YouTube Broadcast EBU R128 (-14.0 LUFS, -1.0 dBTP)',
      integrated_lufs: targetLufs,
      ducking_configuration: {
        depth: duckingDepth,
        ...duck
      },
      vocal_enhancement: {
        high_pass: enableVocalEq ? '80 Hz' : 'disabled',
        clarity_boost: enableVocalEq ? '+2 dB @ 3.5 kHz' : 'disabled'
      },
      video_multiplexed: isVideoOutput,
      loudnorm_metrics: loudnormStats
    }, null, 2));
    process.exit(0);
  } catch (err) {
    console.log(JSON.stringify({
      status: 'FAILED',
      exit_code: 1,
      error: `FFmpeg execution error: ${err.message}`
    }, null, 2));
    process.exit(1);
  }
}

main();
