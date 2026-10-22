/**
 * Crypto & TLS Hygiene Scanner (Dynamic Security Rule)
 * Scans codebases for TLS bypasses, insecure cookie headers, hardcoded PEM private keys,
 * and timing attack hazards on secret comparisons.
 */
import fs from 'node:fs';
import path from 'node:path';

export default async function scan(targetDir) {
  const issues = [];
  const scannedExtensions = new Set(['.js', '.ts', '.mjs', '.cjs', '.py', '.rs', '.go', '.json', '.env']);

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

    // Pattern 1: TLS / SSL Verification Bypass
    const tlsBypassRegex = /rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['"]?0['"]?|check_hostname\s*=\s*False/i;

    // Pattern 2: Hardcoded PEM Private Keys
    const pemKeyRegex = /-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/;

    // Pattern 3: Insecure Cookie Flags (missing secure or httpOnly)
    const insecureCookieRegex = /httpOnly\s*:\s*false|secure\s*:\s*false/i;

    // Pattern 4: Timing attack vulnerability on secret/token comparison
    const timingLeakRegex = /(token|password|secret|hash|signature)\s*===/i;

    lines.forEach((line, idx) => {
      const lineNum = idx + 1;

      if (tlsBypassRegex.test(line)) {
        issues.push({
          id: 'CRYPTO_TLS_VERIFY_DISABLED',
          name: 'TLS / SSL Certificate Verification Disabled',
          severity: 'HIGH',
          category: 'crypto_tls',
          file: path.relative(targetDir, filePath),
          line: lineNum,
          summary: 'Disabling TLS certificate verification enables Man-in-the-Middle (MITM) attacks'
        });
      }

      if (pemKeyRegex.test(line)) {
        issues.push({
          id: 'EXPOSED_PEM_PRIVATE_KEY',
          name: 'Hardcoded Cryptographic Private Key',
          severity: 'CRITICAL',
          category: 'secrets',
          file: path.relative(targetDir, filePath),
          line: lineNum,
          summary: 'Unencrypted PEM private key detected directly in source code'
        });
      }

      if (insecureCookieRegex.test(line)) {
        issues.push({
          id: 'INSECURE_SESSION_COOKIE_FLAGS',
          name: 'Insecure Session Cookie Flags',
          severity: 'MEDIUM',
          category: 'web_security',
          file: path.relative(targetDir, filePath),
          line: lineNum,
          summary: 'Cookie explicit configuration disables httpOnly or secure flag'
        });
      }

      if (timingLeakRegex.test(line) && !line.includes('timingSafeEqual')) {
        issues.push({
          id: 'TIMING_ATTACK_SECRET_COMPARISON',
          name: 'Potential Non-Constant-Time Secret Comparison',
          severity: 'LOW',
          category: 'crypto',
          file: path.relative(targetDir, filePath),
          line: lineNum,
          summary: 'Secret equality check using direct comparison operator may leak timing telemetry'
        });
      }
    });
  }

  walk(targetDir);
  return issues;
}
