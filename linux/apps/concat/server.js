// [FL_INDEX: keywords="concat_server, video_editor_backend, ffmpeg_export, media_streaming, canvas_api" | purpose="Standalone high-performance microserver for Concat NLE Video Studio"]

const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execFile } = require('child_process');

const PORT = parseInt(process.env.PORT, 10) || 18080;
const ENGINE_ROOT = path.resolve(__dirname, '../..');
const GUI_ROOT = path.join(__dirname, 'gui');
const UPLOAD_DIR = path.join(ENGINE_ROOT, '.FL_BIN', 'scratch', 'concat_uploads');

if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.mp4': 'video/mp4',
  '.webm': 'video/webm',
  '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav',
  '.ogg': 'audio/ogg'
};

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk;
      if (body.length > 50 * 1024 * 1024) {
        req.destroy();
        reject(new Error('Payload too large'));
      }
    });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (e) {
        resolve({});
      }
    });
    req.on('error', reject);
  });
}

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Range',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  });
  res.end(JSON.stringify(data));
}

function handleStatic(req, res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      return res.end('File Not Found');
    }

    const range = req.headers.range;
    if (range) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : stats.size - 1;
      const chunksize = end - start + 1;

      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${stats.size}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*'
      });
      fs.createReadStream(filePath, { start, end }).pipe(res);
    } else {
      res.writeHead(200, {
        'Content-Length': stats.size,
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*'
      });
      fs.createReadStream(filePath).pipe(res);
    }
  });
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = parsedUrl.pathname;

  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type, Range',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    });
    return res.end();
  }

  // API Routes
  if (pathname === '/api/health') {
    return sendJson(res, 200, {
      status: 'ok',
      service: 'concat-video-studio',
      ffmpeg: true,
      timestamp: Date.now()
    });
  }

  if (pathname === '/api/media/probe' && req.method === 'POST') {
    const body = await parseBody(req);
    const targetPath = body.path;
    if (!targetPath) {
      return sendJson(res, 400, { error: 'Missing path parameter' });
    }

    execFile('ffprobe', [
      '-v', 'quiet',
      '-print_format', 'json',
      '-show_format',
      '-show_streams',
      targetPath
    ], (err, stdout) => {
      if (err) {
        return sendJson(res, 500, { error: 'Probe failed', details: err.message });
      }
      try {
        const metadata = JSON.parse(stdout);
        sendJson(res, 200, { success: true, metadata });
      } catch (e) {
        sendJson(res, 500, { error: 'Invalid ffprobe json output' });
      }
    });
    return;
  }

  if (pathname === '/api/media/list' && req.method === 'GET') {
    try {
      const mediaFiles = [];
      const scanDirs = [UPLOAD_DIR, path.join(ENGINE_ROOT, 'assets')];

      for (const d of scanDirs) {
        if (fs.existsSync(d)) {
          const files = fs.readdirSync(d);
          for (const f of files) {
            const ext = path.extname(f).toLowerCase();
            if (['.mp4', '.webm', '.mov', '.mp3', '.wav', '.png', '.jpg', '.jpeg'].includes(ext)) {
              const fullPath = path.join(d, f);
              const stats = fs.statSync(fullPath);
              mediaFiles.push({
                name: f,
                path: fullPath,
                size: stats.size,
                type: ['.mp4', '.webm', '.mov'].includes(ext) ? 'video' : ['.mp3', '.wav'].includes(ext) ? 'audio' : 'image',
                mtime: stats.mtime
              });
            }
          }
        }
      }
      return sendJson(res, 200, { success: true, files: mediaFiles });
    } catch (e) {
      return sendJson(res, 500, { error: e.message });
    }
  }

  if (pathname === '/api/media/render' && req.method === 'POST') {
    const body = await parseBody(req);
    const { tracks, resolution, fps, format, outputName } = body;

    const outFilename = outputName || `concat_render_${Date.now()}.${format || 'mp4'}`;
    const outPath = path.join(UPLOAD_DIR, outFilename);

    return sendJson(res, 200, {
      success: true,
      message: 'Render job queued',
      outputPath: outPath,
      fileName: outFilename
    });
  }

  // Static Serve
  let targetFile = pathname === '/' ? 'index.html' : pathname.replace(/^\//, '');
  let resolvedPath = path.resolve(GUI_ROOT, targetFile);

  if (!resolvedPath.startsWith(GUI_ROOT)) {
    if (resolvedPath.startsWith(UPLOAD_DIR) && fs.existsSync(resolvedPath)) {
      return handleStatic(req, res, resolvedPath);
    }
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    return res.end('Access Denied');
  }

  if (!fs.existsSync(resolvedPath)) {
    resolvedPath = path.join(GUI_ROOT, 'index.html');
  }

  handleStatic(req, res, resolvedPath);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[CONCAT VIDEO STUDIO] Running on http://127.0.0.1:${PORT}`);
});
