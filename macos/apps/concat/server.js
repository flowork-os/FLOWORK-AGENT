// [FL_INDEX: keywords="concat_server, http_microservice, repository_packer, token_estimator, visual_canvas_backend" | purpose="Standalone microserver for Concat Visual Canvas App on port 18005"]
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = parseInt(process.env.FLOWORK_APP_PORT || '18005', 10);
const APP_DIR = __dirname;
const GUI_DIR = path.join(APP_DIR, 'gui');
const ENGINE_ROOT = path.resolve(APP_DIR, '../..');

function serveStatic(req, res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.svg': 'image/svg+xml'
  };
  const contentType = mimeTypes[ext] || 'application/octet-stream';
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  });
}

function parseJsonBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (err) {
        reject(err);
      }
    });
  });
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

  // Health endpoint
  if (pathname === '/health' || pathname === '/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'running', port: PORT, app: 'concat' }));
    return;
  }

  // API: Directory Listing / Tree Explorer
  if (pathname === '/api/tree' && req.method === 'GET') {
    const targetPath = parsedUrl.query.path ? path.resolve(ENGINE_ROOT, parsedUrl.query.path) : ENGINE_ROOT;
    try {
      const items = fs.readdirSync(targetPath, { withFileTypes: true });
      const results = items
        .filter(item => !['.git', 'node_modules', '.FL_BIN', '.fl_brain'].includes(item.name))
        .map(item => ({
          name: item.name,
          isDirectory: item.isDirectory(),
          path: path.relative(ENGINE_ROOT, path.join(targetPath, item.name))
        }));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', root: path.relative(ENGINE_ROOT, targetPath), items: results }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'error', message: err.message }));
    }
    return;
  }

  // API: Concat Files
  if (pathname === '/api/concat' && req.method === 'POST') {
    try {
      const payload = await parseJsonBody(req);
      const filePaths = payload.files || [];
      const format = payload.format || 'markdown'; // 'markdown' or 'xml'
      const customSeparator = payload.separator || '\n---\n';

      let concatenated = '';
      let totalFiles = 0;
      let totalBytes = 0;
      let processedList = [];

      for (const relPath of filePaths) {
        const fullPath = path.resolve(ENGINE_ROOT, relPath);
        if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
          const content = fs.readFileSync(fullPath, 'utf8');
          totalFiles++;
          totalBytes += content.length;
          processedList.push({ path: relPath, size: content.length });

          if (format === 'xml') {
            concatenated += `<file path="${relPath}">\n${content}\n</file>\n\n`;
          } else {
            concatenated += `## File: ${relPath}\n\`\`\`\n${content}\n\`\`\`\n${customSeparator}\n`;
          }
        }
      }

      // Fast deterministic LLM token estimation (average 4 chars per token)
      const estimatedTokens = Math.ceil(concatenated.length / 4);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'ok',
        total_files: totalFiles,
        total_chars: concatenated.length,
        estimated_tokens: estimatedTokens,
        processed_files: processedList,
        output: concatenated
      }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'error', message: err.message }));
    }
    return;
  }

  // Static File Serving for GUI
  let safePath = pathname === '/' ? '/index.html' : pathname;
  let targetFile = path.join(GUI_DIR, safePath);
  if (fs.existsSync(targetFile) && fs.statSync(targetFile).isFile()) {
    serveStatic(req, res, targetFile);
  } else {
    serveStatic(req, res, path.join(GUI_DIR, 'index.html'));
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[Concat App] Server running at http://127.0.0.1:${PORT}`);
});
