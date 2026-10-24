#!/usr/bin/env node
// [FL_INDEX: keywords="semantic_search, fastembed, vector_search, onnx, cli_wrapper" | purpose="CLI entry point for Flowork OS sovereign semantic search engine"]

import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function findBinary() {
  const isWin = process.platform === 'win32';
  const isDarwin = process.platform === 'darwin';
  const arch = process.arch;

  const binCandidates = [];

  if (isWin) {
    binCandidates.push(
      path.resolve(__dirname, 'bin/flowork-semantic.exe'),
      path.resolve(__dirname, 'target/release/flowork-semantic.exe'),
      path.resolve(__dirname, 'target/x86_64-pc-windows-gnu/release/flowork-semantic.exe'),
      path.resolve(__dirname, 'target/x86_64-pc-windows-msvc/release/flowork-semantic.exe')
    );
  } else if (isDarwin) {
    const targetTriple = arch === 'arm64' ? 'aarch64-apple-darwin' : 'x86_64-apple-darwin';
    binCandidates.push(
      path.resolve(__dirname, `bin/flowork-semantic-darwin-${arch}`),
      path.resolve(__dirname, 'bin/flowork-semantic'),
      path.resolve(__dirname, `target/${targetTriple}/release/flowork-semantic`),
      path.resolve(__dirname, 'target/release/flowork-semantic')
    );
  } else {
    // Linux / default
    binCandidates.push(
      path.resolve(__dirname, 'bin/flowork-semantic'),
      path.resolve(__dirname, 'target/release/flowork-semantic'),
      path.resolve(__dirname, 'target/x86_64-unknown-linux-gnu/release/flowork-semantic')
    );
  }

  for (const p of binCandidates) {
    if (fs.existsSync(p)) {
      return p;
    }
  }
  return null;
}

const binaryPath = findBinary();

if (!binaryPath) {
  console.error(JSON.stringify({
    error: `flowork-semantic binary not found for platform ${process.platform} (${process.arch}). Please compile via: cd ${__dirname} && cargo build --release`,
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
  include_chat: false,
  recency_decay: 50.0
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
    else if (rawArgs[i] === '--include-chat' || rawArgs[i] === '-c') params.include_chat = true;
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
  '--top-k', String(params.top_k)
];

if (params.include_chat) {
  spawnArgs.push('--include-chat');
  spawnArgs.push('--recency-decay', String(params.recency_decay));
}

function resolvePortableRoot() {
  if (process.env.FLOWORK_PORTABLE_ROOT && fs.existsSync(process.env.FLOWORK_PORTABLE_ROOT)) {
    return process.env.FLOWORK_PORTABLE_ROOT;
  }
  const candidates = [
    path.resolve(__dirname, '..', '..', 'portable-home'),
    path.resolve(__dirname, '..', '..', 'flowork', 'portable-home'),
    path.resolve(process.cwd(), 'portable-home'),
    path.resolve(process.cwd(), 'flowork', 'portable-home'),
    path.resolve(process.cwd(), 'linux', 'portable-home'),
    path.resolve(process.cwd(), 'macos', 'portable-home'),
    path.resolve(process.cwd(), 'windows', 'portable-home')
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) {
      return c;
    }
  }
  return path.resolve(__dirname, '..', '..', 'portable-home');
}

const portableRoot = resolvePortableRoot();

const child = spawn(binaryPath, spawnArgs, {
  env: {
    ...process.env,
    FLOWORK_PORTABLE_ROOT: portableRoot
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
