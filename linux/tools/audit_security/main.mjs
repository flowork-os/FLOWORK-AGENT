#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try { params = JSON.parse(args[pIdx + 1]); } catch (_) {}
  }
  return params;
}

const params = parseArgs();
const targetDir = path.resolve(process.cwd(), params.target_dir || '.');
const issues = [];
let filesScanned = 0;

const secretPatterns = [
  /-----BEGIN [A-Z]+ PRIVATE KEY-----/,
  /AKIA[0-9A-Z]{16}/,
  /(ghp|gho|ghu|ghs|ghr)_[0-9a-zA-Z]{36}/,
  /xox[baprs]-[0-9a-zA-Z]{10,48}/
];

const binaryExtensions = new Set([
  '.exe', '.bin', '.dll', '.so', '.dylib', '.wasm', '.png', '.jpg', '.jpeg', '.gif',
  '.ico', '.mp3', '.wav', '.ogg', '.flac', '.mp4', '.mkv', '.zip', '.tar', '.gz', '.7z'
]);

function isBinary(buffer) {
  const checkLen = Math.min(buffer.length, 1024);
  for (let i = 0; i < checkLen; i++) {
    if (buffer[i] === 0) return true;
  }
  return false;
}

function walk(dir) {
  if (filesScanned > 800) return;
  let entries = [];
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return; }

  for (const entry of entries) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === 'target') continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name).toLowerCase();
      if (binaryExtensions.has(ext)) continue;
      try {
        const buf = fs.readFileSync(full);
        if (isBinary(buf)) continue;
        filesScanned++;
        const content = buf.toString('utf8');
        for (const pat of secretPatterns) {
          if (pat.test(content)) {
            issues.push({
              file: path.relative(process.cwd(), full),
              severity: 'CRITICAL',
              vuln_type: 'exposed_secret_or_key'
            });
            break;
          }
        }
      } catch (_) {}
    }
  }
}

walk(targetDir);

const result = {
  status: 'SUCCESS',
  files_scanned: filesScanned,
  vulnerabilities_found: issues.length,
  safe: issues.length === 0,
  findings: issues
};

console.log(JSON.stringify(result, null, 2));
process.exit(0);
