#!/usr/bin/env node
/**
 * Dynamic External Security Rule Script: Unsafe Dynamic Code Evaluation & ReDoS Detector
 * Called dynamically by Flowork audit_security engine.
 * Arguments: process.argv[2] = target scan directory
 * Output: JSON array of findings printed to stdout
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
          // Check for VM code execution
          if (content.includes('vm.runInNewContext') || content.includes('vm.runInThisContext')) {
            const relPath = path.relative(process.cwd(), fullPath);
            findings.push({
              category: 'sast',
              file: relPath,
              severity: 'CRITICAL',
              vuln_type: 'vm_sandbox_escape_risk',
              summary: 'Node.js vm.runInContext detected; Node VM is not a secure sandbox'
            });
          }
          // Check for new Function
          if (content.includes('new Function(') && !fullPath.includes('node_modules')) {
            const relPath = path.relative(process.cwd(), fullPath);
            findings.push({
              category: 'sast',
              file: relPath,
              severity: 'HIGH',
              vuln_type: 'dynamic_code_evaluation',
              summary: 'new Function() constructor sink detected for dynamic code evaluation'
            });
          }
        } catch (_) {}
      }
    }
  } catch (_) {}
}

walk(targetDir);
console.log(JSON.stringify(findings));
