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
      filesScanned++;
      try {
        const content = fs.readFileSync(full, 'utf8');
        const lines = content.split('\n');
        for (let i = 0; i < lines.length; i++) {
          const l = lines[i];
          if (/(\/bin\/bash|\/bin\/sh)/.test(l) && !full.endsWith('.sh')) {
            issues.push({ file: path.relative(process.cwd(), full), line: i + 1, rule: 'hardcoded_shebang' });
          }
          if (/[A-Z]:\\/.test(l)) {
            issues.push({ file: path.relative(process.cwd(), full), line: i + 1, rule: 'windows_drive_letter' });
          }
        }
      } catch (_) {}
    }
  }
}

walk(targetDir);

const result = {
  status: 'SUCCESS',
  target: targetDir,
  files_scanned: filesScanned,
  portability_score: Math.max(0, 100 - issues.length * 5),
  total_issues: issues.length,
  issues: issues.slice(0, 30)
};

console.log(JSON.stringify(result, null, 2));
process.exit(0);
