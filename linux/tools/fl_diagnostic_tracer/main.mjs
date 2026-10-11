#!/usr/bin/env node
/**
 * 🔍 fl_diagnostic_tracer - Empirical Red-Loop Diagnostics & Probe Engine
 * Verifies deterministic test failures, injects tagged probes, and guarantees clean removal.
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
process.on("uncaughtException", (err) => {
  console.log(JSON.stringify({ status: "error", error: "UNCAUGHT_EXCEPTION", message: err.message }, null, 2));
  process.exit(0);
});
process.on("unhandledRejection", (reason) => {
  console.log(JSON.stringify({ status: "error", error: "UNHANDLED_REJECTION", message: String(reason) }, null, 2));
  process.exit(0);
});

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { spawnSync } from 'child_process';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try { params = JSON.parse(args[pIdx + 1]); } catch (_) {}
  } else if (args[0] && args[0].startsWith('{')) {
    try { params = JSON.parse(args[0]); } catch (_) {}
  }
  return params;
}

function verifyReproCommand(cmd, cwd) {
  const startTime = Date.now();
  const res = spawnSync(cmd, {
    shell: true,
    cwd: cwd || process.cwd(),
    encoding: 'utf8',
    maxBuffer: 5 * 1024 * 1024,
    timeout: 60000
  });
  const durationMs = Date.now() - startTime;
  const exitCode = res.status !== null ? res.status : -1;
  const isRed = exitCode !== 0;

  return {
    command: cmd,
    exit_code: exitCode,
    duration_ms: durationMs,
    is_deterministic_red: isRed,
    verdict: isRed
      ? "VALID_RED_REPRO: Command fails deterministically. Safe to proceed with hypothesis & surgical fix."
      : "INVALID_GREEN_REPRO: Command passed with exit code 0! This does NOT reproduce the bug. Adjust repro test before editing production code.",
    stdout_sample: (res.stdout || '').substring(0, 1000),
    stderr_sample: (res.stderr || '').substring(0, 1000)
  };
}

function injectProbe(filePath, lineNum, probeCode, customTag) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }
  const tag = customTag || crypto.randomBytes(3).toString('hex');
  const ext = path.extname(filePath).toLowerCase();
  const isHashComment = ['.py', '.sh', '.bash', '.rb', '.yaml', '.yml'].includes(ext);

  const prefix = isHashComment ? `# [DEBUG-${tag}]` : `// [DEBUG-${tag}]`;
  const probeLine = `${prefix} ${probeCode}`;

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');

  const insertIdx = Math.max(0, Math.min(lineNum - 1, lines.length));
  lines.splice(insertIdx, 0, probeLine);

  fs.writeFileSync(filePath, lines.join('\n'), 'utf8');

  return {
    file: filePath,
    injected_line: insertIdx + 1,
    tag: `DEBUG-${tag}`,
    probe: probeLine
  };
}

function cleanProbesInFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const cleaned = [];
  let removedCount = 0;

  for (const line of lines) {
    if (/\[DEBUG-[A-Za-z0-9_-]+\]/.test(line)) {
      removedCount++;
    } else {
      cleaned.push(line);
    }
  }

  if (removedCount > 0) {
    fs.writeFileSync(filePath, cleaned.join('\n'), 'utf8');
  }
  return removedCount;
}

function cleanProbes(targetPath) {
  if (!fs.existsSync(targetPath)) return { cleaned_files: 0, removed_probes: 0 };
  const stat = fs.statSync(targetPath);
  let totalCleanedFiles = 0;
  let totalRemoved = 0;

  if (stat.isFile()) {
    const count = cleanProbesInFile(targetPath);
    return { cleaned_files: count > 0 ? 1 : 0, removed_probes: count, details: [{ file: targetPath, removed: count }] };
  }

  const details = [];
  function walk(dir) {
    for (const item of fs.readdirSync(dir)) {
      if (['node_modules', '.git', 'target', 'dist'].includes(item)) continue;
      const full = path.join(dir, item);
      const s = fs.statSync(full);
      if (s.isDirectory()) {
        walk(full);
      } else if (s.isFile()) {
        const count = cleanProbesInFile(full);
        if (count > 0) {
          totalCleanedFiles++;
          totalRemoved += count;
          details.push({ file: full, removed: count });
        }
      }
    }
  }
  walk(targetPath);
  return { cleaned_files: totalCleanedFiles, removed_probes: totalRemoved, details };
}

function listProbes(targetPath) {
  if (!fs.existsSync(targetPath)) return { active_probes: [] };
  const stat = fs.statSync(targetPath);
  const probes = [];

  function scanFile(filePath) {
    const lines = fs.readFileSync(filePath, 'utf8').split('\n');
    for (let i = 0; i < lines.length; i++) {
      const match = lines[i].match(/\[(DEBUG-[A-Za-z0-9_-]+)\]\s*(.*)/);
      if (match) {
        probes.push({
          file: filePath,
          line: i + 1,
          tag: match[1],
          code: match[2]
        });
      }
    }
  }

  if (stat.isFile()) {
    scanFile(targetPath);
  } else {
    function walk(dir) {
      for (const item of fs.readdirSync(dir)) {
        if (['node_modules', '.git', 'target', 'dist'].includes(item)) continue;
        const full = path.join(dir, item);
        const s = fs.statSync(full);
        if (s.isDirectory()) walk(full);
        else if (s.isFile()) scanFile(full);
      }
    }
    walk(targetPath);
  }
  return { active_probes_count: probes.length, active_probes: probes };
}

function main() {
  const params = parseArgs();
  const action = params.action || 'verify_repro';

  if (action === 'verify_repro') {
    if (!params.command) {
      console.log(JSON.stringify({ status: "error", message: "command parameter is required for verify_repro" }, null, 2));
      return;
    }
    const result = verifyReproCommand(params.command, params.cwd);
    console.log(JSON.stringify({
      status: "success",
      action: "verify_repro",
      ...result
    }, null, 2));
    return;
  }

  if (action === 'inject_probe') {
    if (!params.target_path || !params.probe_code) {
      console.log(JSON.stringify({ status: "error", message: "target_path and probe_code are required for inject_probe" }, null, 2));
      return;
    }
    const lineNum = parseInt(params.line_number, 10) || 1;
    const res = injectProbe(path.resolve(params.target_path), lineNum, params.probe_code, params.probe_tag);
    console.log(JSON.stringify({
      status: "success",
      action: "inject_probe",
      ...res
    }, null, 2));
    return;
  }

  if (action === 'clean_probes') {
    const target = path.resolve(params.target_path || '.');
    const res = cleanProbes(target);
    console.log(JSON.stringify({
      status: "success",
      action: "clean_probes",
      target,
      ...res
    }, null, 2));
    return;
  }

  if (action === 'list_probes') {
    const target = path.resolve(params.target_path || '.');
    const res = listProbes(target);
    console.log(JSON.stringify({
      status: "success",
      action: "list_probes",
      target,
      ...res
    }, null, 2));
    return;
  }

  console.log(JSON.stringify({ status: "error", message: `Unknown action: ${action}` }, null, 2));
}

main();
