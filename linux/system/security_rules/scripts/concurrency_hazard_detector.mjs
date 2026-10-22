#!/usr/bin/env node
/**
 * Dynamic Security Rule Script: Concurrency Hazard & TOCTOU Detector
 * Detects:
 * 1. Time-of-Check to Time-of-Use (TOCTOU) file race conditions (existsSync followed by read/unlink without error guards)
 * 2. Unhandled Promise.all / Promise.allSettled concurrency sinks
 */

import fs from 'node:fs';
import path from 'node:path';

const targetDir = process.argv[2] || '.';
const findings = [];

function walk(dir) {
  try {
    const list = fs.readdirSync(dir, { withFileTypes: true });
    for (const item of list) {
      if (item.name.startsWith('.') || item.name === 'node_modules' || item.name === 'target' || item.name === '.FL_BIN') {
        continue;
      }
      const fullPath = path.join(dir, item.name);
      if (item.isDirectory()) {
        walk(fullPath);
      } else if (item.isFile() && /\.(js|mjs|ts|cjs)$/.test(item.name)) {
        try {
          const content = fs.readFileSync(fullPath, 'utf8');
          const relPath = path.relative(process.cwd(), fullPath);

          // Check for Promise.all without .catch and without try/catch
          if (
            content.includes('Promise.all(') &&
            !content.includes('.catch(') &&
            !content.includes('try {')
          ) {
            findings.push({
              category: 'concurrency',
              file: relPath,
              severity: 'MEDIUM',
              vuln_type: 'unhandled_promise_all_race',
              summary: 'Promise.all dispatched without try-catch or .catch rejection handler; risks fast-fail crash'
            });
          }

          // Check for classic TOCTOU anti-pattern
          if (
            content.includes('existsSync(') &&
            (content.includes('readFileSync(') || content.includes('unlinkSync(')) &&
            !content.includes('try {')
          ) {
            findings.push({
              category: 'concurrency',
              file: relPath,
              severity: 'LOW',
              vuln_type: 'toctou_filesystem_race',
              summary: 'Filesystem exists check precedes operation without atomic error guard (TOCTOU race condition)'
            });
          }
        } catch (_) {}
      }
    }
  } catch (_) {}
}

walk(targetDir);
console.log(JSON.stringify(findings));
