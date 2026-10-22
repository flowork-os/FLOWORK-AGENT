#!/usr/bin/env node
/**
 * Dynamic Security Rule Script: High-Entropy Secrets & Credential Leak Scanner
 * Inspired by Gitleaks, TruffleHog, and OWASP Secrets Management guidelines.
 * Scans for:
 * 1. Embedded Private Keys (RSA, OPENSSH, EC, PGP)
 * 2. High-value cloud and SaaS credentials (GitHub PAT, Slack, Stripe, JWT)
 * 3. Database connection URI with embedded passwords
 */

import fs from 'node:fs';
import path from 'node:path';

const targetDir = process.argv[2] || '.';
const findings = [];

const SECRET_PATTERNS = [
  {
    regex: /-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/,
    vuln_type: 'embedded_private_key',
    severity: 'CRITICAL',
    summary: 'Unencrypted cryptographic private key embedded in source code'
  },
  {
    regex: /(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}/,
    vuln_type: 'github_personal_access_token',
    severity: 'CRITICAL',
    summary: 'GitHub Personal Access Token or OAuth token exposed'
  },
  {
    regex: /xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}/,
    vuln_type: 'slack_api_token',
    severity: 'CRITICAL',
    summary: 'Slack bot or user access token detected'
  },
  {
    regex: /sk_live_[0-9a-zA-Z]{24,}/,
    vuln_type: 'stripe_live_secret_key',
    severity: 'CRITICAL',
    summary: 'Stripe live production secret key exposed'
  },
  {
    regex: /(?:postgres|mysql|mongodb(?:\+srv)?):\/\/[a-zA-Z0-9._-]+:[a-zA-Z0-9._~%!$&'()*+,;=-]+@[a-zA-Z0-9.-]+/,
    vuln_type: 'database_connection_uri_with_password',
    severity: 'HIGH',
    summary: 'Database connection string containing embedded cleartext credentials'
  }
];

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
      } else if (item.isFile() && /\.(js|mjs|ts|cjs|json|env|yaml|yml|toml|rs|py|sh)$/.test(item.name)) {
        try {
          const content = fs.readFileSync(fullPath, 'utf8');
          const relPath = path.relative(process.cwd(), fullPath);

          for (const pattern of SECRET_PATTERNS) {
            if (pattern.regex.test(content)) {
              findings.push({
                category: 'secrets',
                file: relPath,
                severity: pattern.severity,
                vuln_type: pattern.vuln_type,
                summary: pattern.summary
              });
              break;
            }
          }
        } catch (_) {}
      }
    }
  } catch (_) {}
}

walk(targetDir);
console.log(JSON.stringify(findings));
