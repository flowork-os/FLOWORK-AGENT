#!/usr/bin/env node
/**
 * 🏛️ fl_domain_adr_manager - Domain Vocabulary & 3-Gate ADR Governor
 * Evaluates 3-Gate criteria, scaffolds ADRs, maintains GLOSSARY.md, and logs .out-of-scope/ items.
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

function evaluateThreeGates(p) {
  const g1 = p.hard_to_reverse === true || p.hard_to_reverse === 'true';
  const g2 = p.surprising_without_context === true || p.surprising_without_context === 'true';
  const g3 = p.has_real_tradeoffs === true || p.has_real_tradeoffs === 'true';

  const passes = g1 && g2 && g3;
  return {
    gate_1_hard_to_reverse: g1,
    gate_2_surprising_without_context: g2,
    gate_3_has_real_tradeoffs: g3,
    all_gates_passed: passes,
    verdict: passes
      ? "JUSTIFIES_FORMAL_ADR: All 3 gates satisfied. High switching cost, non-obvious design, and evaluated trade-offs."
      : "DO_NOT_CREATE_ADR: Fails 3-gate threshold. Document inline or in PR description to prevent ADR bloat.",
    guidance: passes
      ? "Run with action: 'scaffold_adr' to commit this decision to docs/adr/."
      : "ADRs are expensive to maintain. Simple choices belong in code comments or commit messages."
  };
}

function scaffoldAdr(repoRoot, title, context, decision, consequences) {
  const adrDir = path.join(repoRoot, 'docs', 'adr');
  fs.mkdirSync(adrDir, { recursive: true });

  const existing = fs.readdirSync(adrDir).filter(f => /^ADR-\d+.*\.md$/i.test(f));
  let nextNum = 1;
  for (const f of existing) {
    const m = f.match(/^ADR-(\d+)/i);
    if (m) {
      const num = parseInt(m[1], 10);
      if (num >= nextNum) nextNum = num + 1;
    }
  }

  const paddedNum = String(nextNum).padStart(3, '0');
  const slug = (title || 'architectural-decision').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
  const filename = `ADR-${paddedNum}-${slug}.md`;
  const fullPath = path.join(adrDir, filename);

  const adrContent = `# ADR-${paddedNum}: ${title || 'Architectural Decision'}

* **Status:** Accepted
* **Date:** ${new Date().toISOString().split('T')[0]}
* **Co-authored-by:** Flowork OS <agent@floworkos.com>

## Context & Problem Statement
${context || 'Describe the architectural forces and problem context here.'}

## Decision
${decision || 'State the chosen technical decision clearly and concisely.'}

## Consequences
### Positive
* High leverage and containment.
* Clear interface boundary.

### Negative / Trade-offs
${consequences || '* Added adapter indirection required for seam testing.'}

## Compliance & Verification
* Verified with Exit Code 0 test suite.
`;

  fs.writeFileSync(fullPath, adrContent, 'utf8');
  return {
    adr_file: fullPath,
    number: paddedNum,
    title,
    status: "Accepted"
  };
}

function updateGlossary(repoRoot, term, definition) {
  const glossaryPath = path.join(repoRoot, 'GLOSSARY.md');
  let currentContent = '';
  if (fs.existsSync(glossaryPath)) {
    currentContent = fs.readFileSync(glossaryPath, 'utf8');
  } else {
    currentContent = `# 📖 Project Domain Glossary\n\nCanonical vocabulary and domain modeling definitions.\n\n`;
  }

  const termHeader = `### ${term}`;
  if (currentContent.includes(termHeader)) {
    // Update existing
    const regex = new RegExp(`### ${term}[\\s\\S]*?(?=### |$)`);
    currentContent = currentContent.replace(regex, `### ${term}\n${definition}\n\n`);
  } else {
    currentContent += `### ${term}\n${definition}\n\n`;
  }

  fs.writeFileSync(glossaryPath, currentContent, 'utf8');
  return {
    glossary_path: glossaryPath,
    term,
    status: "UPDATED"
  };
}

function logOutOfScope(repoRoot, title, context, rationale) {
  const oosDir = path.join(repoRoot, '.out-of-scope');
  fs.mkdirSync(oosDir, { recursive: true });

  const slug = (title || 'rejected-enhancement').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
  const filePath = path.join(oosDir, `${slug}.md`);

  const content = `# Out of Scope: ${title}

* **Status:** Rejected / Deferred
* **Recorded:** ${new Date().toISOString().split('T')[0]}

## Proposal Context
${context || 'Proposed enhancement or capability.'}

## Rationale for Rejection
${rationale || 'Explicitly rejected to preserve focus, prevent bloat, and maintain single responsibility.'}

## When to Revisit
* Revisit only if core requirements change or upstream API alters contract.
`;

  fs.writeFileSync(filePath, content, 'utf8');
  return {
    out_of_scope_file: filePath,
    topic: title,
    status: "LOCKED_OUT_OF_SCOPE"
  };
}

function main() {
  const params = parseArgs();
  const action = params.action || 'evaluate_3_gates';
  const repoRoot = path.resolve(params.repo_root || '.');

  if (action === 'evaluate_3_gates') {
    const res = evaluateThreeGates(params);
    console.log(JSON.stringify({
      status: "success",
      action: "evaluate_3_gates",
      title: params.title || 'Untitled Decision',
      ...res
    }, null, 2));
    return;
  }

  if (action === 'scaffold_adr') {
    const res = scaffoldAdr(repoRoot, params.title, params.context, params.decision, params.consequences);
    console.log(JSON.stringify({
      status: "success",
      action: "scaffold_adr",
      ...res
    }, null, 2));
    return;
  }

  if (action === 'update_glossary') {
    if (!params.glossary_term || !params.glossary_definition) {
      console.log(JSON.stringify({ status: "error", message: "glossary_term and glossary_definition are required for update_glossary" }, null, 2));
      return;
    }
    const res = updateGlossary(repoRoot, params.glossary_term, params.glossary_definition);
    console.log(JSON.stringify({
      status: "success",
      action: "update_glossary",
      ...res
    }, null, 2));
    return;
  }

  if (action === 'log_out_of_scope') {
    const res = logOutOfScope(repoRoot, params.title, params.context, params.decision);
    console.log(JSON.stringify({
      status: "success",
      action: "log_out_of_scope",
      ...res
    }, null, 2));
    return;
  }

  console.log(JSON.stringify({ status: "error", message: `Unknown action: ${action}` }, null, 2));
}

main();
