// [FL_INDEX: keywords="concat_server, video_editor_backend, ffmpeg_export, media_streaming, canvas_api" | purpose="Standalone high-performance microserver for Concat NLE Video Studio"]
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

const PORT = parseInt(process.env.CONCAT_PORT || process.env.APP_PORT || '18012', 10);
const GUI_ROOT = path.join(__dirname, 'gui');
const ENGINE_ROOT = path.resolve(__dirname, '..', '..');

// Check FFmpeg availability
let hasFFmpeg = false;
try {
  execSync('ffmpeg -version', { stdio: 'ignore' });
  hasFFmpeg = true;
} catch (e) {
  hasFFmpeg = false;
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.mp4': 'video/mp4',
  '.webm': 'video/webm',
  '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav',
  '.woff2': 'font/woff2'
};

function parseJsonBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (e) {
        resolve({});
      }
    });
  });
}

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  });
  res.end(JSON.stringify(payload));
}

const server = http.createServer(async (req, res) => {
  // CORS Preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    });
    return res.end();
  }

  const parsedUrl = new URL(req.url, `http://localhost:${PORT}`);
  const pathname = parsedUrl.pathname;

  // Health API
  if (pathname === '/api/health') {
    return sendJson(res, 200, {
      status: 'ok',
      service: 'concat-video-studio',
      ffmpeg_installed: hasFFmpeg,
      version: '1.0.0',
      timestamp: Date.now()
    });
  }

  // System & Sample Media Library API
  if (pathname === '/api/media/samples') {
    const samples = [
      {
        id: 'sample_cyber_city',
        name: 'Cyberpunk Metropolis.mp4',
        type: 'video',
        duration: 12.5,
        width: 1920,
        height: 1080,
        fps: 30,
        color: '#3373d1',
        url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4'
      },
      {
        id: 'sample_nature_flow',
        name: 'Mountain Stream Flow.mp4',
        type: 'video',
        duration: 15.0,
        width: 1920,
        height: 1080,
        fps: 30,
        color: '#2bb3a8',
        url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4'
      },
      {
        id: 'sample_audio_synth',
        name: 'Ambient Electronic Beat.mp3',
        type: 'audio',
        duration: 20.0,
        color: '#34c46f',
        url: 'https://actions.google.com/sounds/v1/science_fiction/alien_hum.ogg'
      },
      {
        id: 'sample_overlay_title',
        name: 'Kinetic Intro Title',
        type: 'text',
        duration: 5.0,
        text: 'CONCAT VIDEO STUDIO',
        color: '#cf5a99'
      }
    ];
    return sendJson(res, 200, { status: 'success', samples });
  }

  // Project Export Simulation / Render Endpoint
  if (pathname === '/api/project/export' && req.method === 'POST') {
    const body = await parseJsonBody(req);
    const { projectName, resolution, fps, tracks, format } = body;

    // Simulate render pipeline job ID
    const jobId = 'render_' + Math.random().toString(36).substring(2, 9);
    return sendJson(res, 200, {
      status: 'success',
      jobId,
      message: 'Render pipeline initialized',
      details: {
        projectName: projectName || 'Untitled Project',
        resolution: resolution || '1080p',
        fps: fps || 30,
        format: format || 'mp4',
        trackCount: (tracks || []).length,
        ffmpeg_available: hasFFmpeg
      }
    });
  }

  // Static File Serving from GUI directory
  let reqPath = pathname === '/' ? '/index.html' : pathname;
  // Security path traversal check
  const safePath = path.normalize(reqPath).replace(/^(\.\.[\\/])+/, '');
  let filePath = path.join(GUI_ROOT, safePath);

  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      filePath = path.join(GUI_ROOT, 'index.html');
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    fs.readFile(filePath, (readErr, data) => {
      if (readErr) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        return res.end('Internal Server Error');
      }
      res.writeHead(200, {
        'Content-Type': contentType,
        'Cache-Control': 'no-cache'
      });
      res.end(data);
    });
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[Concat Video Studio] running on http://0.0.0.0:${PORT}`);
  console.log(`[Concat Video Studio] FFmpeg engine ready: ${hasFFmpeg}`);
});
