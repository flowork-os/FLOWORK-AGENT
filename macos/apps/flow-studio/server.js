// [FL_INDEX: keywords="flow_studio_server, video_editor_backend, ffmpeg_export, media_streaming, real_video_render" | purpose="Production microserver for Flow Studio NLE Engine with real FFmpeg video rendering engine"]
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

const PORT = parseInt(process.env.CONCAT_PORT || process.env.APP_PORT || '18012', 10);
const GUI_ROOT = path.join(__dirname, 'gui');
const OUTPUTS_DIR = path.join(__dirname, 'exports');

if (!fs.existsSync(OUTPUTS_DIR)) {
  fs.mkdirSync(OUTPUTS_DIR, { recursive: true });
}

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
  '.ogg': 'audio/ogg'
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

// In-memory job tracker
const renderJobs = {};

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

  // Static GUI serving for Video Studio Web Interface
  if (req.method === 'GET' && (pathname === '/' || pathname === '/index.html' || pathname.startsWith('/gui/'))) {
    const rel = (pathname === '/' || pathname === '/index.html') ? 'gui/index.html' : pathname.replace(/^\//, '');
    const targetPath = path.join(__dirname, rel);
    if (fs.existsSync(targetPath) && fs.statSync(targetPath).isFile()) {
      const ext = path.extname(targetPath).toLowerCase();
      res.writeHead(200, {
        'Content-Type': MIME_TYPES[ext] || 'text/html; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
      });
      const stream = fs.createReadStream(targetPath);
      stream.on('error', (err) => {
        if (!res.headersSent) {
          res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
        }
        res.end('Stream Error');
      });
      return stream.pipe(res);
    }
  }

  // Health & Status API
  if (pathname === '/api/health' || pathname === '/health' || pathname === '/api/status') {
    return sendJson(res, 200, {
      status: 'ok',
      service: 'flow-studio',
      name: 'Flow Studio',
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
        text: 'FLOW STUDIO',
        color: '#cf5a99'
      }
    ];
    return sendJson(res, 200, { status: 'success', samples });
  }

  // Real FFmpeg Video Export Endpoint
  if (pathname === '/api/project/export' && req.method === 'POST') {
    const body = await parseJsonBody(req);
    const { projectName, resolution, fps, duration, titleText, color } = body;

    const jobId = 'render_' + Math.random().toString(36).substring(2, 9);
    const outFilename = `${jobId}.mp4`;
    const outFilePath = path.join(OUTPUTS_DIR, outFilename);
    const downloadUrl = `/exports/${outFilename}`;

    const renderDuration = Math.min(Math.max(parseInt(duration || '5', 10), 1), 60);
    const videoFps = parseInt(fps || '30', 10);
    const bannerText = (titleText || projectName || 'FLOWORK CONCAT STUDIO').replace(/[:\']/g, ' ');
    const baseColor = color || '0x151d2f';

    // Parse resolution
    let width = 1280;
    let height = 720;
    if (resolution === '1080p' || resolution === '16-9') {
      width = 1920; height = 1080;
    } else if (resolution === '9-16') {
      width = 1080; height = 1920;
    } else if (resolution === '1-1') {
      width = 1080; height = 1080;
    } else if (resolution === '4-5') {
      width = 1080; height = 1350;
    }

    renderJobs[jobId] = {
      jobId,
      status: 'processing',
      progress: 0,
      filename: outFilename,
      url: downloadUrl,
      startedAt: Date.now()
    };

    // If FFmpeg is available, generate actual synthetic video with audio tones
    if (hasFFmpeg) {
      const vfFilters = [
        `color=c=black:s=${width}x${height}:d=${renderDuration}:r=${videoFps}`,
        `drawbox=x=40:y=40:w=${width-80}:h=${height-80}:color=0xcbf53f@0.4:t=3`,
        `drawtext=text='${bannerText}':fontsize=${Math.floor(height/18)}:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-40:shadowcolor=black:shadowx=2:shadowy=2`,
        `drawtext=text='FLOWORK OS NLE STUDIO':fontsize=${Math.floor(height/32)}:fontcolor=0xcbf53f:x=(w-text_w)/2:y=(h-text_h)/2+40`,
        `drawtext=text='%{pts\\:hms}':fontsize=${Math.floor(height/28)}:fontcolor=0x8892b0:x=(w-text_w)/2:y=h-80`
      ].join(',');

      const args = [
        '-y',
        '-f', 'lavfi', '-i', vfFilters,
        '-f', 'lavfi', '-i', `sine=frequency=440:duration=${renderDuration}`,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'ultrafast',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-t', `${renderDuration}`,
        outFilePath
      ];

      const proc = spawn('ffmpeg', args);
      proc.on('close', (code) => {
        if (code === 0 && fs.existsSync(outFilePath)) {
          const stats = fs.statSync(outFilePath);
          renderJobs[jobId] = {
            jobId,
            status: 'completed',
            progress: 100,
            fileSize: stats.size,
            filename: outFilename,
            url: downloadUrl,
            completedAt: Date.now()
          };
        } else {
          renderJobs[jobId] = {
            jobId,
            status: 'failed',
            error: `FFmpeg exited with code ${code}`
          };
        }
      });

      return sendJson(res, 202, {
        status: 'queued',
        jobId,
        message: 'FFmpeg render pipeline launched',
        url: downloadUrl,
        details: { width, height, fps: videoFps, duration: renderDuration, outFilename }
      });
    } else {
      // Fallback dummy file
      fs.writeFileSync(outFilePath, Buffer.from('FLOWORK_DUMMY_VIDEO_STREAM'));
      renderJobs[jobId] = { jobId, status: 'completed', progress: 100, filename: outFilename, url: downloadUrl };
      return sendJson(res, 200, {
        status: 'success',
        jobId,
        message: 'Simulated file created',
        url: downloadUrl
      });
    }
  }

  // Job Status API
  if (pathname.startsWith('/api/project/status/')) {
    const jobId = pathname.replace('/api/project/status/', '');
    const job = renderJobs[jobId];
    if (!job) {
      return sendJson(res, 404, { status: 'error', message: 'Job not found' });
    }
    return sendJson(res, 200, { status: 'success', job });
  }

  // Static File Serving (including exports/)
  let reqPath = pathname === '/' ? '/index.html' : pathname;
  const safePath = path.normalize(reqPath).replace(/^(\.\.[\\/])+/, '');

  let filePath;
  if (safePath.startsWith('/exports/') || safePath.startsWith('exports/')) {
    filePath = path.join(__dirname, safePath);
  } else {
    filePath = path.join(GUI_ROOT, safePath);
  }

  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      if (!safePath.startsWith('/exports') && !safePath.startsWith('/api')) {
        filePath = path.join(GUI_ROOT, 'index.html');
      } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        return res.end('File Not Found');
      }
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    // Support video streaming / range requests
    const range = req.headers.range;
    if (range && stats && stats.isFile()) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : stats.size - 1;
      const chunkSize = (end - start) + 1;
      const file = fs.createReadStream(filePath, { start, end });
      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${stats.size}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunkSize,
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*'
      });
      return file.pipe(res);
    }

    res.writeHead(200, {
      'Content-Type': contentType,
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-cache'
    });
    fs.createReadStream(filePath).pipe(res);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[Concat Video Studio] running on http://0.0.0.0:${PORT}`);
  console.log(`[Concat Video Studio] FFmpeg engine ready: ${hasFFmpeg}`);
});
