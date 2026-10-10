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
const strict = Boolean(params.strict_mode);

const hardcodedPatterns = [
  /\/home\/[a-zA-Z0-9_\-]+/,
  /\/tmp\/[a-zA-Z0-9_\-]+/,
  /[C-Z]:\\[a-zA-Z0-9_\-]+/i,
  /[C-Z]:\/[a-zA-Z0-9_\-]+/i
];

const issues = [];
let scannedCount = 0;

function walk(dir) {
  if (scannedCount > 1000) return;
  let entries = [];
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return; }

  for (const entry of entries) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === 'target') continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full);
    } else if (entry.isFile()) {
      scannedCount++;
      try {
        const text = fs.readFileSync(full, 'utf8');
        const lines = text.split('\n');
        for (let i = 0; i < lines.length; i++) {
          for (const pat of hardcodedPatterns) {
            if (pat.test(lines[i])) {
              issues.push({
                file: path.relative(process.cwd(), full),
                line: i + 1,
                match: lines[i].trim().slice(0, 100)
              });
              break;
            }
          }
        }
      } catch (_) {}
    }
  }
}

walk(targetDir);

const result = {
  status: 'SUCCESS',
  scanned_files: scannedCount,
  total_issues: issues.length,
  is_clean: issues.length === 0,
  issues: issues.slice(0, 50)
};

console.log(JSON.stringify(result, null, 2));
process.exit(0);
