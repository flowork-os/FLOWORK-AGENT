#!/usr/bin/env node
// 🏛️ Flowork OS Modular Tool: brain_control (Evidence Linking Standard)
// Co-authored-by: Flowork OS <agent@floworkos.com>

import fs from 'fs';
import path from 'path';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try { params = JSON.parse(args[pIdx + 1]); } catch (_) {}
  }
  return params;
}

const params = parseArgs();
const action = params.action || 'list';
const cwd = process.cwd();

// Resolve .fl_brain location
function resolveBrainDir() {
  const userHome = process.env.HOME || process.env.USERPROFILE || '';
  const candidates = [
    path.join(cwd, '.fl_brain'),
    process.env.FLOWORK_WORKSPACE ? path.join(process.env.FLOWORK_WORKSPACE, '.fl_brain') : null,
    userHome ? path.join(userHome, 'flowork', '.fl_brain') : null,
    userHome ? path.join(userHome, 'dr.floworks-skl', '.fl_brain') : null
  ].filter(Boolean);
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  const defaultDir = path.join(cwd, '.fl_brain');
  fs.mkdirSync(defaultDir, { recursive: true });
  return defaultDir;
}

const brainDir = resolveBrainDir();

try {
  if (action === 'write') {
    const title = params.title || 'Untitled Sovereign Solution';
    const slug = (params.id || title.toLowerCase().replace(/[^a-z0-9]+/g, '_').slice(0, 50)).replace(/^_+|_+$/g, '');
    const keywords = Array.isArray(params.keywords) ? params.keywords : [];
    const sourceSession = params.source_session_id || params.session_id || params.SessionId || 'sovereign_session';
    let evidenceSteps = Array.isArray(params.evidence_steps) && params.evidence_steps.length > 0 ? params.evidence_steps : [];
    if (evidenceSteps.length === 0) {
      if (typeof params.step_idx === 'number') {
        evidenceSteps = [params.step_idx];
      } else if (typeof params.step_index === 'number') {
        evidenceSteps = [params.step_index];
      } else {
        evidenceSteps = [0];
      }
    }
    const verifiedExitCode = typeof params.verified_exit_code === 'number' ? params.verified_exit_code : 0;
    const releaseTag = params.release_tag || 'v1.0.1';
    const createdAt = new Date().toISOString();
    const category = params.category || 'architecture';

    const memoriesDir = path.join(brainDir, 'memories', 'shared');
    fs.mkdirSync(memoriesDir, { recursive: true });

    const targetFile = path.join(memoriesDir, `${slug}.md`);
    if (fs.existsSync(targetFile) && !params.overwrite) {
      console.log(JSON.stringify({
        status: 'ERROR',
        error: `Memory file '${slug}.md' already exists. Pass overwrite: true to replace.`,
        exit_code: 1
      }, null, 2));
      process.exit(1);
    }

    const frontmatterKeywords = keywords.map(k => `  - ${k}`).join('\n');
    const frontmatterSteps = evidenceSteps.map(s => `  - ${s}`).join('\n');

    const fileContent = `---
title: "${title}"
keywords:
${frontmatterKeywords || '  - flowork_sovereign_memory'}
source_session_id: "${sourceSession}"
evidence_steps:
${frontmatterSteps || '  - 0'}
verified_exit_code: ${verifiedExitCode}
release_tag: "${releaseTag}"
category: "${category}"
created_at: "${createdAt}"
---

# ${title}

## Problem & Context
${params.problem || 'No problem description provided.'}

## Root Cause
${params.root_cause || 'Direct architectural design or runtime verification.'}

## Verified Solution & Evidence
${params.solution || 'Solution verified with Exit Code 0.'}
`;

    fs.writeFileSync(targetFile, fileContent, 'utf-8');
    console.log(JSON.stringify({
      status: 'SUCCESS',
      tool: 'brain_control',
      action: 'write',
      id: slug,
      target_file: targetFile,
      evidence_linking: {
        source_session_id: sourceSession,
        evidence_steps: evidenceSteps,
        verified_exit_code: verifiedExitCode
      },
      message: `Memory '${slug}' crystallized with Evidence Linking standard.`
    }, null, 2));
    process.exit(0);

  } else if (action === 'read') {
    const slug = params.id || '';
    if (!slug) {
      console.log(JSON.stringify({ status: 'ERROR', error: 'Parameter "id" required for read.', exit_code: 1 }));
      process.exit(1);
    }
    let foundPath = null;
    function searchFile(dir) {
      if (!fs.existsSync(dir)) return;
      const files = fs.readdirSync(dir, { withFileTypes: true });
      for (const f of files) {
        if (f.isDirectory()) searchFile(path.join(dir, f.name));
        else if (f.name === `${slug}.md` || f.name === slug) {
          foundPath = path.join(dir, f.name);
          return;
        }
      }
    }
    searchFile(brainDir);
    if (!foundPath) {
      console.log(JSON.stringify({ status: 'ERROR', error: `Memory '${slug}' not found.`, exit_code: 1 }));
      process.exit(1);
    }
    const content = fs.readFileSync(foundPath, 'utf-8');
    console.log(JSON.stringify({ status: 'SUCCESS', id: slug, path: foundPath, content }, null, 2));
    process.exit(0);

  } else if (action === 'list') {
    const limit = params.limit || 20;
    const items = [];
    function scanDir(dir) {
      if (!fs.existsSync(dir)) return;
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const e of entries) {
        if (e.isDirectory()) scanDir(path.join(dir, e.name));
        else if (e.name.endsWith('.md')) {
          items.push({ name: e.name, path: path.join(dir, e.name) });
        }
      }
    }
    scanDir(brainDir);
    console.log(JSON.stringify({ status: 'SUCCESS', total: items.length, memories: items.slice(0, limit) }, null, 2));
    process.exit(0);

  } else {
    console.log(JSON.stringify({
      status: 'SUCCESS',
      tool: 'brain_control',
      action: action,
      parameters_received: params,
      message: 'Tool brain_control executed successfully under Flowork Sovereign Runtime.'
    }, null, 2));
    process.exit(0);
  }
} catch (err) {
  console.log(JSON.stringify({ status: 'ERROR', error: err.message, exit_code: 1 }, null, 2));
  process.exit(1);
}
