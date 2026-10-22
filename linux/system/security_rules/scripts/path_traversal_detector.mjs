#!/usr/bin/env node
/**
 * Dynamic External Security Rule Script: Path Traversal & Unsafe File Access Detector
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
          // Check for dangerous path joins or readFileSync directly from req.params / req.query / untrusted args
          if (
            (content.includes('fs.readFileSync') || content.includes('fs.readFile')) &&
            (content.includes('req.query') || content.includes('req.params') || content.includes('req.body'))
          ) {
            const relPath = path.relative(process.cwd(), fullPath);
            findings.push({
              category: 'sast',
              file: relPath,
              severity: 'HIGH',
              vuln_type: 'path_traversal_risk',
              summary: 'Unsanitized filesystem read with request parameter sink detected'
            });
          }
        } catch (_) {}
      }
    }
  } catch (_) {}
}

walk(targetDir);
console.log(JSON.stringify(findings));
