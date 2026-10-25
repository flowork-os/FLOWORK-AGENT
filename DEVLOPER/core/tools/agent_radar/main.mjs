#!/usr/bin/env node
/**
 * 📡 Flowork Sovereign Subagent Radar & JIT Dispatcher
 * Discovers and ranks optimal subagents for incoming task intents.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
let query = '';

if (args.includes('--params') && args[args.indexOf('--params') + 1]) {
  try {
    const p = JSON.parse(args[args.indexOf('--params') + 1]);
    query = p.query || p.task || p.task_description || '';
  } catch (_) {}
} else if (args[0] && !args[0].startsWith('--')) {
  try {
    const p = JSON.parse(args.join(' '));
    query = p.task_description || p.query || p.task || args.join(' ');
  } catch (_) {
    query = args.join(' ');
  }
}

const searchPaths = [
  path.resolve(__dirname, '../../system/subagent/agent_registry.json'),
  path.resolve(process.cwd(), 'system/subagent/agent_registry.json'),
  path.resolve(process.cwd(), 'flowork/system/subagent/agent_registry.json')
];

let registry = null;
for (const p of searchPaths) {
  if (fs.existsSync(p)) {
    try { registry = JSON.parse(fs.readFileSync(p, 'utf8')); break; } catch (_) {}
  }
}

if (!registry || !Array.isArray(registry.agents)) {
  console.log(JSON.stringify({ status: 'ERROR', error: 'agent_registry.json missing', candidates: [] }, null, 2));
  process.exit(0);
}

const tokens = (query || '').toLowerCase().replace(/[^a-z0-9_-]/g, ' ').split(/\s+/).filter(Boolean);
const scored = registry.agents.map((agent) => {
  let score = 0;
  const kws = agent.trigger_keywords || [];
  const desc = (agent.description || '').toLowerCase().split(/\s+/);
  const role = (agent.role || '').toLowerCase().split(/\s+/);

  for (const t of tokens) {
    if (kws.includes(t)) score += 3.0;
    else if (kws.some(k => k.includes(t) || t.includes(k))) score += 1.5;
    if (role.includes(t)) score += 1.0;
    if (desc.includes(t)) score += 0.5;
  }

  const normalized = tokens.length > 0 ? Math.min(1.0, Number((score / (tokens.length * 3.0)).toFixed(2))) : 0;
  return {
    id: agent.id, name: agent.name, role: agent.role, icon: agent.icon || '🤖',
    department: agent.department, relevance_score: normalized,
    model_preference: agent.model_preference || 'pro',
    territory: agent.territory || {}, contracts: agent.contracts || {},
    recommended_subagent_call: { TypeName: agent.id, Role: agent.role, Model: agent.model_preference || 'pro' }
  };
}).sort((a, b) => b.relevance_score - a.relevance_score);

const topCandidates = scored.filter(c => c.relevance_score > 0.05).slice(0, 3);
console.log(JSON.stringify({
  status: 'SUCCESS', exit_code: 0, query: query || '(empty)',
  total_agents_evaluated: registry.agents.length, matched_count: topCandidates.length,
  top_match: topCandidates[0] || null,
  candidates: topCandidates.length > 0 ? topCandidates : scored.slice(0, 2)
}, null, 2));
process.exit(0);
