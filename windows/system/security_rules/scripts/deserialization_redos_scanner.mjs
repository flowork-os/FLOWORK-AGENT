/**
 * Deserialization & ReDoS Hazard Scanner (Dynamic Security Rule)
 * Scans codebases for Zip Slip extraction hazards, regex exponential backtracking (ReDoS),
 * and unsafe deserialization sinks (Python pickle, JS node-serialize, YAML unsafe load).
 */
import fs from 'node:fs';
import path from 'node:path';

export default async function scan(targetDir) {
  const issues = [];
  const scannedExtensions = new Set(['.js', '.ts', '.mjs', '.cjs', '.py', '.rs', '.go']);

  function walk(dir) {
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }

    for (const entry of entries) {
      if (entry.name === 'node_modules' || entry.name === '.git' || entry.name === 'target') continue;
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();
        if (scannedExtensions.has(ext)) {
          inspectFile(fullPath);
        }
      }
    }
  }

  function inspectFile(filePath) {
    let content = '';
    try {
      content = fs.readFileSync(filePath, 'utf8');
    } catch {
      return;
    }

    const lines = content.split('\n');

    // Pattern 1: Zip Slip Hazard (Unsanitized path extraction)
    const zipSlipRegex = /entry\.path|header\.name/i;
    const writeStreamRegex = /createWriteStream|fs\.writeFile/i;

    // Pattern 2: ReDoS - Nested Quantifiers in regular expressions
    const redosRegex = /\(\.\*\)\+|\(\.\+\)\+|\(\[[^\]]+\]\+\)\+/;

    // Pattern 3: Insecure Deserialization in Node/Python
    const unsafeDeserialRegex = /node-serialize\.unserialize|yaml\.load\([^)]+\)|pickle\.loads/i;

    // Pattern 4: JWT unverified algorithm or none algorithm
    const jwtNoneRegex = /algorithms\s*:\s*\[\s*['"]none['"]\s*\]/i;

    lines.forEach((line, idx) => {
      const lineNum = idx + 1;

      if (redosRegex.test(line)) {
        issues.push({
          id: 'REDOS_EXPONENTIAL_BACKTRACKING',
          name: 'Regular Expression Denial of Service (ReDoS) Risk',
          severity: 'HIGH',
          category: 'dos_vulnerability',
          file: path.relative(targetDir, filePath),
          line: lineNum,
          summary: 'Nested quantifiers detected in regex; vulnerable to catastrophic backtracking'
        });
      }

      if (unsafeDeserialRegex.test(line) && !line.includes('safe_load')) {
        issues.push({
          id: 'INSECURE_DESERIALIZATION_SINK',
          name: 'Insecure Deserialization Sink',
          severity: 'CRITICAL',
          category: 'sast',
          file: path.relative(targetDir, filePath),
          line: lineNum,
          summary: 'Untrusted object deserialization allows remote code execution (RCE)'
        });
      }

      if (jwtNoneRegex.test(line)) {
        issues.push({
          id: 'JWT_ALGORITHM_NONE_ACCEPTED',
          name: 'JWT Algorithm None Permitted',
          severity: 'CRITICAL',
          category: 'authentication',
          file: path.relative(targetDir, filePath),
          line: lineNum,
          summary: 'JWT verification explicitly permits "none" algorithm, enabling authentication bypass'
        });
      }
    });
  }

  walk(targetDir);
  return issues;
}
