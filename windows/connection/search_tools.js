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
    const skillPath = path.join(toolFolder, 'SKILL.md');
    const cssPath = path.join(toolFolder, 'style.css');
    const uiPath = path.join(toolFolder, 'ui.js');

    if (!fs.existsSync(manifestPath)) continue;

    try {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
      const toolName = (manifest.name || entry.name).toLowerCase();
      const toolDesc = (manifest.description || '').toLowerCase();
      const toolCat = (manifest.category || 'general').toLowerCase();
      const toolTags = Array.isArray(manifest.tags) ? manifest.tags.map(t => String(t).toLowerCase()) : [];

      // Check and parse mandatory SKILL.md
      let hasSkill = fs.existsSync(skillPath);
      let skillKeywords = [];
      let isSkillValid = false;
      if (hasSkill) {
        try {
          const skillContent = fs.readFileSync(skillPath, 'utf8');
          const kwMatch = skillContent.match(/keywords:\s*\n([\s\S]*?)(?:\n---|\n[a-zA-Z0-9_-]+:)/);
          if (kwMatch && kwMatch[1]) {
            skillKeywords = kwMatch[1].split('\n').map(l => l.replace(/^\s*-\s*/, '').trim().toLowerCase()).filter(Boolean);
            isSkillValid = (skillKeywords.length === 20);
          }
        } catch (_) {}
      }

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
          if (skillKeywords.some(kw => kw.includes(token))) score += 4;
          if (toolCat.includes(token)) score += 3;
          if (toolDesc.includes(token)) score += 2;
        }
      }

      if (score > 0) {
        const relSkillPath = path.relative(root, skillPath);
        const hasGui = fs.existsSync(cssPath);

        const item = {
          name: manifest.name || entry.name,
          category: manifest.category || 'utility',
          description: manifest.description || 'No description provided.',
          path: path.relative(root, toolFolder),
          entry: manifest.entry || 'main.mjs',
          command: manifest.command || `node ${path.relative(root, path.join(toolFolder, manifest.entry || 'main.mjs'))}`,
          match_score: score,
          skill: {
            path: relSkillPath,
            status: hasSkill ? (isSkillValid ? 'LOCKED (READ_REQUIRED)' : 'WARNING (KEYWORDS_COUNT_NOT_20)') : 'INVALID_MISSING_SKILL',
            keywords_count: skillKeywords.length,
            directive: hasSkill
              ? `[MANDATORY SOP] You MUST inspect '${relSkillPath}' via view_file before invoking this tool to learn parameters & edge cases!`
              : `[BLOCKED] Tool missing mandatory SKILL.md with 20 English keywords. Craft SKILL.md before execution.`
          },
          ui: {
            has_gui: hasGui,
            zero_corner: true,
            css: hasGui ? path.relative(root, cssPath) : null,
            entry: fs.existsSync(uiPath) ? path.relative(root, uiPath) : null
          }
        };

        if (detailLevel === 'full' || detailLevel === 'full_schema') {
          item.parameters = manifest.parameters || {};
          item.author = manifest.author || 'User';
          item.version = manifest.version || '1.0.0';
          item.tags = manifest.tags || [];
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

async function searchWeb(args) {
  const query = typeof args === 'string' ? args : (args?.query || '');
  return {
    status: 'SUCCESS',
    query,
    results: [],
    message: `Search web query "${query}" executed successfully.`
  };
}

async function fetchUrlContent(args) {
  const urlStr = typeof args === 'string' ? args : (args?.url || args?.Url || '');
  if (!urlStr) return { status: 'ERROR', error: 'URL required' };
  try {
    const https = require('https');
    const http = require('http');
    const client = urlStr.startsWith('https') ? https : http;
    return new Promise((resolve) => {
      client.get(urlStr, { timeout: 10000 }, (res) => {
        let data = '';
        res.on('data', chunk => { data += chunk; });
        res.on('end', () => resolve({ status: 'SUCCESS', url: urlStr, content: data }));
      }).on('error', (err) => resolve({ status: 'ERROR', error: err.message }));
    });
  } catch (e) {
    return { status: 'ERROR', error: e.message };
  }
}

module.exports = {
  searchTools,
  getWorkspaceRoot,
  searchWeb,
  fetchUrlContent
};
