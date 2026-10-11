#!/usr/bin/env node
/**
 * 🛡️ fl_code_review - Two-Axis Independent Code Review Engine
 * Evaluates changes along Axis 1 (Standards & Fowler Smells) and Axis 2 (Spec Conformance).
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
import { execSync } from 'child_process';

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

function detectFowlerSmells(codeContent, filename) {
  const smells = [];
  const lines = codeContent.split('\n');

  let currentIndent = 0;
  let maxIndent = 0;
  let maxIndentLine = 0;
  let functionStartLine = 0;
  let currentFunctionLines = 0;
  let inFunction = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    const lineNum = i + 1;

    // Skip full comment lines for TODO and DEBUG checks
    if (trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('*') || trimmed.startsWith('#')) {
      continue;
    }

    // 1. Secret / Credential Leakage Smell
    if (/(api[_-]?key|secret|password|token)\s*[:=]\s*["'][A-Za-z0-9_\-]{8,}["']/i.test(trimmed)) {
      smells.push({
        type: 'HARDCODED_SECRET_SUSPECT',
        severity: 'CRITICAL',
        line: lineNum,
        message: 'Suspected hardcoded secret or token found in source code.',
        snippet: trimmed.substring(0, 80)
      });
    }

    // 2. Debug Residual Smell (ignore when inside tool runner console.log of JSON output)
    if (/console\.(debug|trace)|debugger;/i.test(trimmed)) {
      smells.push({
        type: 'DEBUG_RESIDUAL',
        severity: 'MEDIUM',
        line: lineNum,
        message: 'Debug statement left in code. Remove before production.',
        snippet: trimmed
      });
    }

    // 3. TODO / Unfinished Debt Smell
    if (/\b(TODO|FIXME|HACK|XXX)\b/i.test(trimmed) && !trimmed.includes('smells.push')) {
      smells.push({
        type: 'UNFINISHED_DEBT',
        severity: 'LOW',
        line: lineNum,
        message: 'Unresolved TODO/FIXME annotation present in diff.',
        snippet: trimmed
      });
    }

    // 4. Excessive Nesting Depth (Arrow Anti-Pattern)
    const matchIndent = line.match(/^(\s+)/);
    const indentDepth = matchIndent ? Math.floor(matchIndent[1].length / 2) : 0;
    if (indentDepth > 4) {
      smells.push({
        type: 'EXCESSIVE_NESTING',
        severity: 'HIGH',
        line: lineNum,
        message: `Deep nesting detected (level ${indentDepth} > 4). Refactor to early returns or guard clauses.`,
        snippet: trimmed
      });
    }

    // 5. Long Function Tracker
    if (/function\s+\w+|\b(def|fn)\s+\w+|\w+\s*=\s*\([^)]*\)\s*=>/i.test(trimmed) && trimmed.includes('{')) {
      inFunction = true;
      functionStartLine = lineNum;
      currentFunctionLines = 0;
    } else if (inFunction) {
      currentFunctionLines++;
      if (trimmed === '}' || trimmed.startsWith('}')) {
        if (currentFunctionLines > 60) {
          smells.push({
            type: 'LONG_FUNCTION',
            severity: 'MEDIUM',
            line: functionStartLine,
            message: `Function starting at line ${functionStartLine} exceeds 60 lines (${currentFunctionLines} lines). Violates single responsibility principle.`,
            snippet: lines[functionStartLine - 1]?.trim()
          });
        }
        inFunction = false;
      }
    }
  }

  return smells;
}

function evaluateSpecConformance(diffFiles, diffContent, specPath) {
  const specFindings = {
    verified_criteria: [],
    potential_missing: [],
    potential_scope_creep: [],
    passed: true
  };

  if (!specPath || !fs.existsSync(specPath)) {
    return {
      note: 'No spec provided or spec file does not exist. Spec axis evaluated in pass-through mode.',
      passed: true
    };
  }

  const specContent = fs.readFileSync(specPath, 'utf8');
  const specLines = specContent.split('\n');

  // Extract checklist items
  const criteria = [];
  for (const line of specLines) {
    const match = line.match(/^\s*-\s*\[([ xX])\]\s*(.*)/);
    if (match) {
      criteria.push({
        done: match[1].toLowerCase() === 'x',
        text: match[2].trim()
      });
    }
  }

  // Cross-reference diff content with criteria keywords
  for (const item of criteria) {
    const keywords = item.text.toLowerCase().replace(/[^a-z0-9_]/g, ' ').split(/\s+/).filter(w => w.length > 3);
    const matches = keywords.some(k => diffContent.toLowerCase().includes(k));
    if (matches) {
      specFindings.verified_criteria.push({
        criterion: item.text,
        evidence: 'Keywords match modified diff hunks'
      });
    } else {
      specFindings.potential_missing.push({
        criterion: item.text,
        warning: 'No relevant keywords from this criterion found in the diff.'
      });
    }
  }

  if (specFindings.potential_missing.length > 0) {
    specFindings.passed = false;
  }

  return specFindings;
}

function main() {
  const params = parseArgs();
  const action = params.action || 'review_diff';
  const repoPath = path.resolve(params.repo_path || '.');
  const fixedPoint = params.fixed_point || 'HEAD~1';
  const specPath = params.spec_path ? path.resolve(params.spec_path) : null;
  const standardsPath = params.standards_path ? path.resolve(params.standards_path) : null;

  if (action === 'review_file') {
    if (!params.target_file) {
      console.log(JSON.stringify({ status: "error", message: "target_file parameter is required for review_file" }, null, 2));
      return;
    }
    const targetPath = path.resolve(params.target_file);
    if (!fs.existsSync(targetPath)) {
      console.log(JSON.stringify({ status: "error", message: `File not found: ${targetPath}` }, null, 2));
      return;
    }
    const content = fs.readFileSync(targetPath, 'utf8');
    const smells = detectFowlerSmells(content, path.basename(targetPath));
    console.log(JSON.stringify({
      status: "success",
      action: "review_file",
      target_file: targetPath,
      smell_count: smells.length,
      smells,
      passed: smells.filter(s => s.severity === 'CRITICAL' || s.severity === 'HIGH').length === 0
    }, null, 2));
    return;
  }

  // Action: review_diff
  let diffOutput = '';
  let changedFiles = [];
  try {
    diffOutput = execSync(`git -C "${repoPath}" diff ${fixedPoint}...HEAD 2>/dev/null || git -C "${repoPath}" diff ${fixedPoint} 2>/dev/null`, { encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 });
    const nameOnly = execSync(`git -C "${repoPath}" diff --name-only ${fixedPoint}...HEAD 2>/dev/null || git -C "${repoPath}" diff --name-only ${fixedPoint} 2>/dev/null`, { encoding: 'utf8' });
    changedFiles = nameOnly.split('\n').filter(Boolean);
  } catch (err) {
    console.log(JSON.stringify({
      status: "error",
      message: `Failed to execute git diff against ref '${fixedPoint}': ${err.message}`
    }, null, 2));
    return;
  }

  if (!diffOutput.trim()) {
    console.log(JSON.stringify({
      status: "success",
      message: `Empty diff between ${fixedPoint} and HEAD. No changes detected to review.`,
      changed_files_count: 0
    }, null, 2));
    return;
  }

  // Axis 1: Standards & Smells
  const allSmells = [];
  for (const relFile of changedFiles) {
    const fullPath = path.join(repoPath, relFile);
    if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
      try {
        const fileContent = fs.readFileSync(fullPath, 'utf8');
        const fileSmells = detectFowlerSmells(fileContent, relFile);
        if (fileSmells.length > 0) {
          allSmells.push({
            file: relFile,
            smells: fileSmells
          });
        }
      } catch (_) {}
    }
  }

  // Axis 2: Spec Conformance
  const specFindings = evaluateSpecConformance(changedFiles, diffOutput, specPath);

  const totalSmells = allSmells.reduce((acc, f) => acc + f.smells.length, 0);
  const criticalSmells = allSmells.reduce((acc, f) => acc + f.smells.filter(s => s.severity === 'CRITICAL').length, 0);
  const standardsPassed = criticalSmells === 0;

  console.log(JSON.stringify({
    status: "success",
    action: "review_diff",
    fixed_point: fixedPoint,
    changed_files_count: changedFiles.length,
    changed_files: changedFiles,
    standards_axis: {
      status: standardsPassed ? "PASSED" : "FAILED",
      total_smells: totalSmells,
      critical_smells: criticalSmells,
      files_with_smells: allSmells
    },
    spec_axis: specFindings,
    verdict: {
      standards: standardsPassed ? "PASS" : "FAIL",
      spec: specFindings.passed ? "PASS" : "FAIL",
      summary: standardsPassed && specFindings.passed
        ? "Both Standards and Spec axes passed with flying colors."
        : "Discrepancies identified. Review findings before merging."
    }
  }, null, 2));
}

main();
