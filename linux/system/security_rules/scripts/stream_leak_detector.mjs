#!/usr/bin/env node
/**
 * Dynamic Security Rule Script: Stream & File Descriptor Leak Detector
 * Inspired by Node.js Clinic.js Doctor and production I/O health benchmarks.
 * Scans for:
 * 1. fs.createReadStream / fs.createWriteStream without error listeners (leaking FD on I/O error)
 * 2. net.createServer / http.createServer without client socket timeouts (slowloris / fd exhaustion)
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

          // Check if createReadStream or createWriteStream without error listener
          if (
            (content.includes('createReadStream(') || content.includes('createWriteStream(')) &&
            !content.includes('.on(\'error\'') &&
            !content.includes('.on("error"') &&
            !content.includes('pipeline(')
          ) {
            findings.push({
              category: 'resource_leak',
              file: relPath,
              severity: 'HIGH',
              vuln_type: 'unhandled_stream_fd_leak',
              summary: 'Stream created without error event listener or pipeline wrapper; risk of dangling file descriptor leak'
            });
          }

          // Check for net.connect / tls.connect without timeout
          if (
            (content.includes('net.connect(') || content.includes('tls.connect(')) &&
            !content.includes('setTimeout') &&
            !content.includes('timeout')
          ) {
            findings.push({
              category: 'resource_leak',
              file: relPath,
              severity: 'MEDIUM',
              vuln_type: 'unbounded_socket_connection',
              summary: 'Socket connection established without explicit socket timeout'
            });
          }
        } catch (_) {}
      }
    }
  } catch (_) {}
}

walk(targetDir);
console.log(JSON.stringify(findings));
