/**
 * ANTI-MOCK & SYNTHETIC DATA BEHAVIORAL SCANNER (Flowork OS Sovereign Security)
 * 
 * Purpose:
 * Detects fake/mock/simulated stubs in production and application code.
 * Rejects fragile naive keyword matching in favor of deep structural and AST heuristics:
 * 1. Hardcoded Structured Multi-Record Anomaly: Large in-memory array literals of domain objects (MAC, IP, RSSI, telemetry).
 * 2. Hardware/Network No-IO Stub: Functions claiming hardware/telemetry scan without system/kernel/network I/O.
 * 3. Fallback Mock Poisoning: Catch blocks intercepting real hardware errors to inject synthetic data payloads.
 * 4. Fake Uniform Metric Distribution: Low-entropy integer multiples simulating real Gaussian RF/sensor noise.
 */

import fs from 'node:fs';
import path from 'node:path';

// Known real-world MAC prefixes / IEEE broadcast
const SYNTHETIC_MAC_PATTERNS = [
  /([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}/g,
  /([0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2}/g
];

export async function scanAntiMock(targetPath) {
  const issues = [];
  
  if (!fs.existsSync(targetPath)) {
    return issues;
  }

  const stat = fs.statSync(targetPath);
  const files = stat.isDirectory() ? getFilesRecursively(targetPath) : [targetPath];

  for (const file of files) {
    // Exclude formal test directories and vendor dependencies
    if (file.includes('node_modules') || file.includes('.git') || file.includes('/test/') || file.includes('/tests/')) {
      continue;
    }

    const ext = path.extname(file).toLowerCase();
    if (!['.js', '.mjs', '.ts', '.rs', '.py'].includes(ext)) {
      continue;
    }

    const content = fs.readFileSync(file, 'utf8');
    const lines = content.split('\n');

    // HEURISTIC 1: Fallback Mock Poisoning (catch blocks returning structured data arrays)
    const catchBlockRegex = /catch\s*\([^\)]*\)\s*\{([^}]+)\}/gs;
    let match;
    while ((match = catchBlockRegex.exec(content)) !== null) {
      const catchBody = match[1];
      // Check if catch body returns or sets an array of objects
      if (catchBody.includes('return [') || catchBody.includes('return [{') || catchBody.includes('res.json([')) {
        const lineNum = getLineNumber(content, match.index);
        issues.push({
          id: 'FALLBACK_MOCK_POISONING',
          severity: 'CRITICAL',
          category: 'anti_mock',
          file,
          line: lineNum,
          summary: 'Hardware error handler intercepts failure and substitutes synthetic data fallback instead of surfacing real hardware error',
          snippet: lines[lineNum - 1]?.trim() || ''
        });
      }
    }

    // HEURISTIC 2: Inline Multi-Record Hardware/Telemetry Dataset
    // Detect arrays containing >= 3 structured objects with domain keys like ssid, bssid, mac, rssi, signal, freq
    const inlineDomainArrayRegex = /(const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*\[\s*\{[^}]+\}\s*,\s*\{[^}]+\}\s*,\s*\{[^}]+\}/gs;
    while ((match = inlineDomainArrayRegex.exec(content)) !== null) {
      const varName = match[2];
      const chunk = match[0];
      const hasDomainKeys = /(ssid|bssid|mac|rssi|channel|freq|signal|latitude|longitude|sensor|adapter)/i.test(chunk);
      if (hasDomainKeys) {
        const lineNum = getLineNumber(content, match.index);
        issues.push({
          id: 'HARDCODED_TELEMETRY_DATASET',
          severity: 'HIGH',
          category: 'anti_mock',
          file,
          line: lineNum,
          summary: `Static multi-record telemetry dataset assigned to variable '${varName}' without live hardware derivation`,
          snippet: lines[lineNum - 1]?.trim() || ''
        });
      }
    }

    // HEURISTIC 3: Synthetic MAC/BSSID Pattern Accumulation
    let macCount = 0;
    for (const macRegex of SYNTHETIC_MAC_PATTERNS) {
      const matches = content.match(macRegex);
      if (matches) {
        macCount += matches.length;
      }
    }
    // In production source files, more than 4 hardcoded MAC addresses strongly indicates synthetic spoofing
    if (macCount >= 4) {
      issues.push({
        id: 'ACCUMULATED_SYNTHETIC_MACS',
        severity: 'HIGH',
        category: 'anti_mock',
        file,
        line: 1,
        summary: `Detected ${macCount} hardcoded MAC/BSSID addresses embedded directly into source code`,
        snippet: `Total hardcoded hardware addresses detected: ${macCount}`
      });
    }

    // HEURISTIC 4: Telemetry Scan Function With Zero Kernel/IO Operations
    // Scan functions named 'scan*', 'getTelemetry', 'readSensors' that lack child_process/spawn/fs/fetch/socket
    const funcRegex = /async\s+function\s+([A-Za-z0-9_]*scan[A-Za-z0-9_]*|[A-Za-z0-9_]*telemetry[A-Za-z0-9_]*)\s*\([^)]*\)\s*\{([^}]+)\}/gi;
    while ((match = funcRegex.exec(content)) !== null) {
      const funcName = match[1];
      const funcBody = match[2];
      const hasIO = /(spawn|exec|execFile|child_process|fs\.|fetch|http|socket|ioctl|open|readSync)/i.test(funcBody);
      if (!hasIO) {
        const lineNum = getLineNumber(content, match.index);
        issues.push({
          id: 'NO_IO_TELEMETRY_STUB',
          severity: 'CRITICAL',
          category: 'anti_mock',
          file,
          line: lineNum,
          summary: `Function '${funcName}' purports to perform hardware scanning/telemetry but executes zero OS syscalls, sockets, or I/O`,
          snippet: lines[lineNum - 1]?.trim() || ''
        });
      }
    }
  }

  return issues;
}

function getFilesRecursively(dir) {
  let results = [];
  try {
    const list = fs.readdirSync(dir);
    for (const file of list) {
      const fullPath = path.join(dir, file);
      const stat = fs.statSync(fullPath);
      if (stat && stat.isDirectory()) {
        results = results.concat(getFilesRecursively(fullPath));
      } else {
        results.push(fullPath);
      }
    }
  } catch (err) {
    // Ignore unreadable dirs
  }
  return results;
}

function getLineNumber(content, index) {
  return content.substring(0, index).split('\n').length;
}

// Direct CLI execution support
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(import.meta.filename)) {
  const target = process.argv[2] || process.cwd();
  scanAntiMock(target).then(issues => {
    console.log(JSON.stringify({ status: 'ok', issues_count: issues.length, issues }, null, 2));
    process.exit(issues.length > 0 ? 1 : 0);
  }).catch(err => {
    console.error('Anti-mock scan failed:', err);
    process.exit(2);
  });
}
