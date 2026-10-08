/**
 * 🔍 FLOWORK OS — SOVEREIGN EXTERNAL TOOLS DISCOVERY ENGINE
 * =========================================================
 * Doktrin: On-Demand External Tool Search & Anti-Laziness Guard
 * Flowork Sovereign OS
 */
'use strict';

const fs = require('fs');
const path = require('path');

function getWorkspaceRoot() {
  if (process.env.FLOWORK_WORKSPACE && fs.existsSync(process.env.FLOWORK_WORKSPACE)) {
    return process.env.FLOWORK_WORKSPACE;
  }
  let curr = process.cwd();
  for (let i = 0; i < 5; i++) {
    if (fs.existsSync(path.join(curr, 'tools')) || fs.existsSync(path.join(curr, 'skill')) || fs.existsSync(path.join(curr, 'connection')) || fs.existsSync(path.join(curr, 'CONECTION'))) {
      return curr;
    }
    const parent = path.dirname(curr);
    if (parent === curr) break;
    curr = parent;
  }
  return path.resolve(__dirname, '..');
}

function searchTools(query = '', category = '', detailLevel = 'summary') {
  const root = getWorkspaceRoot();
  const toolsDir = path.join(root, 'tools');

  if (!fs.existsSync(toolsDir)) {
    return {
      status: 'NO_TOOLS_DIRECTORY',
      total_found: 0,
      tools: [],
      message: 'External tools directory (tools/) does not exist yet. You may propose crafting a new tool using /TOOL_MAKER.'
    };
  }

  const queryTokens = (query || '').toLowerCase().split(/[\s,_\-]+/).filter(Boolean);
  const targetCategory = (category || '').toLowerCase().trim();

  let entries = [];
  try {
    entries = fs.readdirSync(toolsDir, { withFileTypes: true });
  } catch (err) {
    return { status: 'ERROR', message: `Failed to read tools directory: ${err.message}` };
  }

  const matches = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const toolFolder = path.join(toolsDir, entry.name);
    const manifestPath = path.join(toolFolder, 'manifest.json');

    if (!fs.existsSync(manifestPath)) continue;

    try {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
      const toolName = (manifest.name || entry.name).toLowerCase();
      const toolDesc = (manifest.description || '').toLowerCase();
      const toolCat = (manifest.category || 'general').toLowerCase();
      const toolTags = Array.isArray(manifest.tags) ? manifest.tags.map(t => String(t).toLowerCase()) : [];

      if (targetCategory && toolCat !== targetCategory && !toolTags.includes(targetCategory)) {
        continue;
      }

      let score = 0;
      if (queryTokens.length === 0) {
        score = 1; // Return all if query is empty
      } else {
        for (const token of queryTokens) {
          if (toolName.includes(token)) score += 5;
          if (toolTags.some(tag => tag.includes(token))) score += 4;
          if (toolCat.includes(token)) score += 3;
          if (toolDesc.includes(token)) score += 2;
        }
      }

      if (score > 0) {
        const item = {
          name: manifest.name || entry.name,
          category: manifest.category || 'utility',
          description: manifest.description || 'No description provided.',
          path: path.relative(root, toolFolder),
          entry: manifest.entry || 'index.js',
          command: manifest.command || `node ${manifest.entry || 'index.js'}`,
          match_score: score
        };

        if (detailLevel === 'full' || detailLevel === 'full_schema') {
          item.parameters = manifest.parameters || {};
          item.author = manifest.author || 'User';
          item.version = manifest.version || '1.0.0';
        }

        matches.push(item);
      }
    } catch (_) {}
  }

  // Sort descending by match score
  matches.sort((a, b) => b.match_score - a.match_score);

  if (matches.length === 0) {
    return {
      status: 'NO_MATCHING_TOOLS',
      query,
      category: targetCategory || 'any',
      total_found: 0,
      tools: [],
      message: `No external tool found matching query "${query}". You are now authorized to provide a custom solution or offer to build one via /TOOL_MAKER.`
    };
  }

  return {
    status: 'SUCCESS',
    query,
    total_found: matches.length,
    tools: matches,
    message: `Found ${matches.length} matching external tool(s). Inspect the command/parameters to execute.`
  };
}

// CLI Direct Invocation Support
if (require.main === module) {
  const query = process.argv[2] || '';
  const category = process.argv[3] || '';
  const detail = process.argv[4] || 'full';

  const result = searchTools(query, category, detail);
  console.log(JSON.stringify(result, null, 2));
}

module.exports = {
  searchTools,
  getWorkspaceRoot
};
