#!/usr/bin/env node
// [FL_INDEX: keywords="semantic_search, fastembed, vector_search, onnx, cli_wrapper" | purpose="CLI entry point for Flowork OS sovereign semantic search engine"]

import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Dynamic relative resolution for release binary across platforms and build directories
function findBinary() {
  const isWindows = process.platform === 'win32';
  const isMac = process.platform === 'darwin';
  const isArm = process.arch === 'arm64';

  const candidates = [
    path.resolve(__dirname, 'target/release/flowork-semantic'),
    path.resolve(__dirname, 'bin/flowork-semantic'),
  ];

  if (isWindows) {
    candidates.unshift(
      path.resolve(__dirname, 'target/release/flowork-semantic.exe'),
      path.resolve(__dirname, 'bin/flowork-semantic.exe')
    );
  } else if (isMac) {
    if (isArm) {
      candidates.unshift(
        path.resolve(__dirname, 'bin/flowork-semantic-darwin-arm64'),
        path.resolve(__dirname, 'target/aarch64-apple-darwin/release/flowork-semantic')
      );
    } else {
      candidates.unshift(
        path.resolve(__dirname, 'bin/flowork-semantic-darwin-x86_64'),
        path.resolve(__dirname, 'target/x86_64-apple-darwin/release/flowork-semantic')
      );
    }
  }

  for (const cand of candidates) {
    if (fs.existsSync(cand)) {
      return cand;
    }
  }
  return null;
}

const binaryPath = findBinary();

if (!binaryPath) {
  console.error(JSON.stringify({
    error: `flowork-semantic binary not found. Please run cargo build --release in tools/semantic_search.`,
    exit_code: 1
  }));
  process.exit(1);
}

// Parse args or --params JSON
const rawArgs = process.argv.slice(2);
let params = {
  query: '',
  target: '.fl_brain',
  model: 'bge-small',
  top_k: 5,
  min_score: 0.50,
  include_chat: false,
  recency_decay: 50.0,
  rebuild_cache: false
};

const paramsIdx = rawArgs.indexOf('--params');
if (paramsIdx !== -1 && rawArgs[paramsIdx + 1]) {
  try {
    const raw = rawArgs[paramsIdx + 1];
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
    Object.assign(params, parsed);
  } catch (_) {}
} else {
  for (let i = 0; i < rawArgs.length; i++) {
    if (rawArgs[i] === '--query' || rawArgs[i] === '-q') params.query = rawArgs[++i] || '';
    else if (rawArgs[i] === '--target' || rawArgs[i] === '-t') params.target = rawArgs[++i] || '.fl_brain';
    else if (rawArgs[i] === '--model' || rawArgs[i] === '-m') params.model = rawArgs[++i] || 'bge-small';
    else if (rawArgs[i] === '--top-k' || rawArgs[i] === '-k') params.top_k = parseInt(rawArgs[++i], 10) || 5;
    else if (rawArgs[i] === '--min-score' || rawArgs[i] === '-s') params.min_score = parseFloat(rawArgs[++i]) || 0.50;
    else if (rawArgs[i] === '--include-chat' || rawArgs[i] === '-c') params.include_chat = true;
    else if (rawArgs[i] === '--rebuild-cache') params.rebuild_cache = true;
    else if (rawArgs[i] === '--recency-decay') params.recency_decay = parseFloat(rawArgs[++i]) || 50.0;
    else if (!rawArgs[i].startsWith('-') && !params.query) params.query = rawArgs[i];
  }
}

if (!params.query) {
  console.log(JSON.stringify([]));
  process.exit(0);
}

const spawnArgs = [
  '--query', params.query,
  '--target', params.target,
  '--model', params.model,
  '--top-k', String(params.top_k),
  '--min-score', String(params.min_score)
];

if (params.rebuild_cache) {
  spawnArgs.push('--rebuild-cache');
}

if (params.include_chat) {
  spawnArgs.push('--include-chat');
  spawnArgs.push('--recency-decay', String(params.recency_decay));
}

const child = spawn(binaryPath, spawnArgs, {
  env: {
    ...process.env,
    FLOWORK_PORTABLE_ROOT: process.env.FLOWORK_PORTABLE_ROOT || path.resolve(process.cwd(), 'portable-home')
  }
});

let stdout = '';
let stderr = '';

child.stdout.on('data', chunk => { stdout += chunk; });
child.stderr.on('data', chunk => { stderr += chunk; });

child.on('close', code => {
  if (code !== 0) {
    console.error(JSON.stringify({ error: stderr.trim() || 'Binary failed', exit_code: code }));
    process.exit(code);
  }
  // Print exact stdout JSON from binary
  process.stdout.write(stdout);
});
