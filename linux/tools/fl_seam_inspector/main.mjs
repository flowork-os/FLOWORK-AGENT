#!/usr/bin/env node
/**
 * 🏛️ fl_seam_inspector - Ousterhout Deep Module & Seam Architecture Analyzer
 * Evaluates Depth Ratio, verifies Multi-Adapter Seams, and scores the Deletion Test.
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

function collectFiles(dirPath, extFilter = ['.ts', '.js', '.mjs', '.rs', '.py', '.go']) {
  const files = [];
  function traverse(current) {
    if (!fs.existsSync(current)) return;
    const stat = fs.statSync(current);
    if (stat.isDirectory()) {
      if (['node_modules', '.git', 'target', 'dist', 'build', '.fl_bin', '.flowork_spam'].includes(path.basename(current))) {
        return;
      }
      for (const item of fs.readdirSync(current)) {
        traverse(path.join(current, item));
      }
    } else if (stat.isFile()) {
      const ext = path.extname(current).toLowerCase();
      if (extFilter.includes(ext)) {
        files.push(current);
      }
    }
  }
  traverse(dirPath);
  return files;
}

function analyzeFileDepth(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const totalLines = lines.length;
  let codeLines = 0;
  let interfaceLines = 0;
  let exportCount = 0;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('#')) {
      continue;
    }
    codeLines++;

    // Interface / Export signature detection
    if (/^(export\s+(type|interface|class|function|const|let|enum)|pub\s+(fn|struct|enum|trait)|def\s+\w+)/.test(trimmed)) {
      exportCount++;
      interfaceLines++;
    }
  }

  const implementationLines = Math.max(codeLines - interfaceLines, 1);
  const depthRatio = interfaceLines === 0 ? codeLines : Number((implementationLines / interfaceLines).toFixed(2));

  let classification = "BALANCED";
  if (depthRatio >= 6.0) {
    classification = "DEEP_MODULE (High Leverage)";
  } else if (depthRatio < 2.0 && totalLines > 20) {
    classification = "SHALLOW_MODULE (Pass-Through Risk)";
  }

  return {
    file: path.basename(filePath),
    path: filePath,
    total_loc: totalLines,
    effective_loc: codeLines,
    interface_loc: interfaceLines,
    implementation_loc: implementationLines,
    export_count: exportCount,
    depth_ratio: depthRatio,
    classification
  };
}

function auditAdaptersAndSeams(files) {
  const adapters = [];
  const seamCandidates = new Map();

  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    const filename = path.basename(file);

    // Look for classes or objects named Adapter, Client, Repository
    const matches = content.matchAll(/\b(class|struct|interface|type)\s+([A-Za-z0-9_]+(Adapter|Client|Repository|Gateway|Driver))\b/g);
    for (const match of matches) {
      const symbolName = match[2];
      const kind = match[3]; // e.g. Adapter
      const baseTarget = symbolName.replace(/(Adapter|Client|Repository|Gateway|Driver)$/, '');

      adapters.push({
        file: filename,
        symbol: symbolName,
        kind,
        target_seam: baseTarget
      });

      if (!seamCandidates.has(baseTarget)) {
        seamCandidates.set(baseTarget, []);
      }
      seamCandidates.get(baseTarget).push({ file: filename, symbol: symbolName });
    }
  }

  const evaluatedSeams = [];
  for (const [seamName, instances] of seamCandidates.entries()) {
    const count = instances.length;
    evaluatedSeams.push({
      seam_name: seamName,
      adapter_count: count,
      adapters: instances,
      status: count >= 2 ? "VERIFIED_SEAM (Production + Test/Alt verified)" : "UNVERIFIED_SEAM_HYPOTHESIS (1 adapter: indirection without polymorphism)",
      recommendation: count >= 2
        ? "Valid architectural seam. Retain abstraction boundary."
        : "Only 1 adapter detected. If no mock or in-memory adapter exists, consider collapsing to direct implementation."
    });
  }

  return {
    total_adapters: adapters.length,
    total_seams: evaluatedSeams.length,
    seams: evaluatedSeams
  };
}

function evaluateDeletionTest(targetPath, workspaceFiles) {
  const targetName = path.basename(targetPath).replace(/\.[^.]+$/, '');
  let callerReferences = 0;
  const callers = [];

  for (const file of workspaceFiles) {
    if (path.resolve(file) === path.resolve(targetPath)) continue;
    try {
      const content = fs.readFileSync(file, 'utf8');
      if (content.includes(targetName)) {
        callerReferences++;
        callers.push(path.basename(file));
      }
    } catch (_) {}
  }

  return {
    target: targetName,
    callers_count: callerReferences,
    callers_sample: callers.slice(0, 10),
    blast_radius: callerReferences > 10 ? "HIGH_BLAST_RADIUS" : callerReferences > 3 ? "MODERATE" : "ISOLATED",
    deletion_test_verdict: callerReferences === 0
      ? "Dead code candidate: Module has 0 references in workspace."
      : callerReferences <= 3
      ? "Clean Seam: Narrow coupling surface, easy to delete or replace."
      : "Wide Blast Radius: Module is entangled across multiple callers. Deepen interface."
  };
}

function main() {
  const params = parseArgs();
  const action = params.action || 'analyze_depth';
  const targetPath = params.target_path ? path.resolve(params.target_path) : process.cwd();

  if (!fs.existsSync(targetPath)) {
    console.log(JSON.stringify({ status: "error", message: `Target path does not exist: ${targetPath}` }, null, 2));
    return;
  }

  const isFile = fs.statSync(targetPath).isFile();
  const files = isFile ? [targetPath] : collectFiles(targetPath);

  if (action === 'analyze_depth') {
    const analyses = files.slice(0, 50).map(analyzeFileDepth);
    const avgDepth = Number((analyses.reduce((a, b) => a + b.depth_ratio, 0) / (analyses.length || 1)).toFixed(2));
    const shallowModules = analyses.filter(a => a.classification.startsWith("SHALLOW"));
    const deepModules = analyses.filter(a => a.classification.startsWith("DEEP"));

    console.log(JSON.stringify({
      status: "success",
      action: "analyze_depth",
      target: targetPath,
      total_inspected_files: analyses.length,
      average_depth_ratio: avgDepth,
      deep_modules_count: deepModules.length,
      shallow_modules_count: shallowModules.length,
      shallow_warnings: shallowModules.map(s => ({ file: s.file, ratio: s.depth_ratio, advice: "Consider absorbing pass-through logic into caller or deepening the implementation." })),
      top_deep_modules: deepModules.slice(0, 5),
      architectural_health: avgDepth >= 4.0 ? "HEALTHY (Deep Modules Prevail)" : "MODERATE (Pass-through abstraction detected)"
    }, null, 2));
    return;
  }

  if (action === 'audit_seams') {
    const seamAudit = auditAdaptersAndSeams(files);
    console.log(JSON.stringify({
      status: "success",
      action: "audit_seams",
      target: targetPath,
      ...seamAudit
    }, null, 2));
    return;
  }

  if (action === 'deletion_test') {
    const workspaceRoot = isFile ? path.dirname(targetPath) : targetPath;
    const allFiles = collectFiles(workspaceRoot);
    const deletionResult = evaluateDeletionTest(targetPath, allFiles);
    console.log(JSON.stringify({
      status: "success",
      action: "deletion_test",
      ...deletionResult
    }, null, 2));
    return;
  }

  console.log(JSON.stringify({ status: "error", message: `Unknown action: ${action}` }, null, 2));
}

main();
