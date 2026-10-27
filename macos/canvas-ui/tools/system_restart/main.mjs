#!/usr/bin/env node
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
const resumePrompt = params.resume_prompt || 'Resuming after system restart';
const binDir = path.resolve(process.cwd(), '.FL_BIN');
if (!fs.existsSync(binDir)) fs.mkdirSync(binDir, { recursive: true });

fs.writeFileSync(path.join(binDir, 'restart_resume.json'), JSON.stringify({
  resume_prompt: resumePrompt,
  restarted_at: new Date().toISOString()
}, null, 2), 'utf8');

const result = {
  status: 'SUCCESS',
  action: 'restart_scheduled',
  resume_prompt: resumePrompt,
  message: 'System restart signal dispatched with auto-resume state preserved.'
};

console.log(JSON.stringify(result, null, 2));
process.exit(0);
