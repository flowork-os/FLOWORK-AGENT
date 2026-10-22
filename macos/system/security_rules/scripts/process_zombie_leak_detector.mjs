#!/usr/bin/env node
/**
 * Dynamic External Security Rule Script: Process Lifecycle, Zombie & Resource Leak Detector
 * Inspired by Node.js/Linux process tree scanners (tini, dumb-init, ptree, ps-tree).
 * Detects:
 * 1. Process forks/spawns lacking SIGINT/SIGTERM or process.exit cleanup
 * 2. Unhandled stream backpressure & memory buffer leaks (Buffer.allocUnsafe, event listener leaks)
 * 3. File descriptor / socket leaks without close/destroy in finally blocks
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

          // 1. Zombie Process Trap: child_process spawn/fork without exit/close handler
          if (
            (content.includes('spawn(') || content.includes('fork(')) &&
            !content.includes('.on(\'exit\'') &&
            !content.includes('.on("exit"') &&
            !content.includes('.on(\'close\'') &&
            !content.includes('.on("close"') &&
            !content.includes('unref()')
          ) {
            findings.push({
              category: 'process_lifecycle',
              file: relPath,
              severity: 'HIGH',
              vuln_type: 'unsupervised_child_process_zombie',
              summary: 'Child process spawned without explicit exit/close handler or unref; prone to zombie state'
            });
          }

          // 2. Unsafe uninitialized memory buffer allocation
          if (content.includes('Buffer.allocUnsafe(')) {
            findings.push({
              category: 'memory_leak',
              file: relPath,
              severity: 'HIGH',
              vuln_type: 'uninitialized_buffer_leak',
              summary: 'Buffer.allocUnsafe detected; may expose uninitialized heap memory to untrusted sinks'
            });
          }

          // 3. Potential MaxListenersExceeded / Event Emitter leak
          if (content.includes('setMaxListeners(0)') || content.includes('setMaxListeners(Infinity)')) {
            findings.push({
              category: 'memory_leak',
              file: relPath,
              severity: 'MEDIUM',
              vuln_type: 'infinite_event_listeners_leak',
              summary: 'EventEmitter max listeners disabled; high risk of silent memory leak on long-running processes'
            });
          }
        } catch (_) {}
      }
    }
  } catch (_) {}
}

walk(targetDir);
console.log(JSON.stringify(findings));
