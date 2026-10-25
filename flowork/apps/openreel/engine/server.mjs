// [FL_INDEX: keywords="openreel, server, ffmpeg, ffprobe, video_engine" | purpose="Backend service for OpenReel video editor engine"]
import http from 'http';
import url from 'url';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const APP_ROOT = path.resolve(__dirname, '..');
const GUI_ROOT = path.join(APP_ROOT, 'gui');
const PORT = process.env.FLOWORK_APP_PORT ? parseInt(process.env.FLOWORK_APP_PORT, 10) : (process.env.PORT ? parseInt(process.env.PORT, 10) : 18090);

// In-memory render jobs tracker
const jobs = new Map();

// Helper: Run command safely returning Promise
function runCmd(cmd, args) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args);
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', d => { stdout += d.toString(); });
    proc.stderr.on('data', d => { stderr += d.toString(); });
    proc.on('close', code => {
      if (code === 0) resolve({ stdout, stderr });
      else reject(new Error(`Process exited with code ${code}: ${stderr}`));
    });
  });
}

// Media probe using ffprobe
async function probeMedia(filePath) {
  const args = [
    '-v', 'quiet',
    '-print_format', 'json',
    '-show_format',
    '-show_streams',
    filePath
  ];
  const { stdout } = await runCmd('ffprobe', args);
  return JSON.parse(stdout);
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // API Endpoints
  if (pathname === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    let ffmpegAvailable = false;
    try {
      await runCmd('ffmpeg', ['-version']);
      ffmpegAvailable = true;
    } catch (e) {
      ffmpegAvailable = false;
    }
    return res.end(JSON.stringify({
      status: 'ok',
      app: 'openreel',
      ffmpeg: ffmpegAvailable,
      active_jobs: jobs.size
    }));
  }

  if (pathname === '/api/probe' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body || '{}');
        if (!payload.filePath) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'filePath parameter is required' }));
        }
        const meta = await probeMedia(payload.filePath);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, metadata: meta }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: err.message }));
      }
    });
    return;
  }

  if (pathname === '/api/jobs' && req.method === 'GET') {
    const list = Array.from(jobs.entries()).map(([id, j]) => ({ id, ...j }));
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ jobs: list }));
  }

  // Static File Serving for GUI
  let filePath = path.join(GUI_ROOT, pathname === '/' ? 'index.html' : pathname);
  
  // Guard against directory traversal
  if (!filePath.startsWith(GUI_ROOT)) {
    res.writeHead(403);
    return res.end('Access Denied');
  }

  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.mp4': 'video/mp4'
  };

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('404 Not Found');
      } else {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Server Error');
      }
    } else {
      res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
      res.end(content);
    }
  });
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[OpenReel Video Engine] Running on http://127.0.0.1:${PORT}`);
});

process.on('SIGTERM', () => {
  server.close(() => process.exit(0));
});
