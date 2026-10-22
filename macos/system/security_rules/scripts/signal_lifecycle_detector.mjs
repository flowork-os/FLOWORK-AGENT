#!/usr/bin/env node
/**
 * Dynamic Security Rule Script: Process Signal, Daemon & Graceful Shutdown Inspector
 * Inspired by Linux init systems (tini, dumb-init, supervisor).
 * Scans for:
 * 1. Background daemon or HTTP/TCP server missing SIGTERM/SIGINT signal handling
 * 2. Ungraceful process.kill or process.exit calls causing orphaned child processes
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

          // Check if file starts a server (.listen) but has zero SIGINT/SIGTERM handlers
          if (
            (content.includes('.listen(') || content.includes('createServer(')) &&
            !content.includes('SIGTERM') &&
            !content.includes('SIGINT')
          ) {
            findings.push({
              category: 'process_lifecycle',
              file: relPath,
              severity: 'MEDIUM',
              vuln_type: 'missing_graceful_shutdown',
              summary: 'Server listens on network port without registering SIGTERM/SIGINT graceful shutdown handlers'
            });
          }

          // Ungraceful process.exit(0) without waiting for background tasks
          if (content.includes('process.exit(') && content.includes('child_process.')) {
            if (!content.includes('kill(') && !content.includes('unref()')) {
              findings.push({
                category: 'process_lifecycle',
                file: relPath,
                severity: 'HIGH',
                vuln_type: 'ungraceful_parent_exit',
                summary: 'process.exit invoked in child_process manager without terminating or detaching child PIDs'
              });
            }
          }
        } catch (_) {}
      }
    }
  } catch (_) {}
}

walk(targetDir);
console.log(JSON.stringify(findings));
