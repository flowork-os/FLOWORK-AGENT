#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — UNIVERSAL MCP NANO-TOOL RUNNER
 * ==============================================
 * Dispatches actions from AI Agent (Mr. Flow) to micro-app sidecar engines
 * and Canvas host as defined in SKILL_APP.md.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

const args = process.argv.slice(2);
const toolName = args[0];
const rawPayload = args[1] || '{}';

if (!toolName) {
  console.error(JSON.stringify({ error: 'Tool name required. Usage: node mcp/run.mjs <tool_name> [json_args]' }));
  process.exit(1);
}

let payload = {};
try {
  payload = JSON.parse(rawPayload);
} catch (e) {
  console.error(JSON.stringify({ error: `Invalid JSON payload: ${e.message}` }));
  process.exit(1);
}

function resolveAppPort(tool) {
  // 1. Specific well-known prefix mapping
  if (tool.startsWith('chess_')) return Number(process.env.FLOWORK_CHESS_PORT) || 17820;
  if (tool.startsWith('trade_')) return Number(process.env.FLOWORK_TRADING_PORT) || 17821;
  if (tool.startsWith('website_intel_') || tool.startsWith('intel_')) return Number(process.env.FLOWORK_WEBINTEL_PORT) || 17822;
  if (tool.startsWith('youtube_')) return Number(process.env.FLOWORK_YOUTUBE_PORT) || 17823;
  if (tool.startsWith('websec_')) return Number(process.env.FLOWORK_WEBSEC_PORT) || 17824;
  if (tool === 'canvas_control' || tool === 'flow_canvas_control') return Number(process.env.FLOWORK_SIDECAR_HOST_PORT) || 17700;

  // 2. Dynamic lookup from app.manifest.json across app/ directory
  try {
    const appsDir = path.join(projectRoot, 'app');
    if (fs.existsSync(appsDir)) {
      const dirs = fs.readdirSync(appsDir);
      for (const d of dirs) {
        const manifestPath = path.join(appsDir, d, 'app.manifest.json');
        if (fs.existsSync(manifestPath)) {
          const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
          if (manifest.id && (tool.startsWith(manifest.id + '_') || tool.startsWith('flow_' + manifest.id + '_'))) {
            return Number(manifest.ipc?.default_port) || null;
          }
        }
      }
    }
  } catch (_) {}

  return null;
}

async function main() {
  // 1. Canvas Control Tool
  if (toolName === 'canvas_control' || toolName === 'flow_canvas_control') {
    const sidecarPort = Number(process.env.FLOWORK_SIDECAR_HOST_PORT) || 17700;
    const postData = JSON.stringify(payload);

    const req = http.request({
      hostname: '127.0.0.1',
      port: sidecarPort,
      path: '/api/canvas/action',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      timeout: 5000
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          console.log(JSON.stringify(JSON.parse(body), null, 2));
        } catch (_) {
          console.log(body);
        }
      });
    });

    req.on('error', (err) => {
      console.error(JSON.stringify({ error: `Failed to connect to Canvas Host on port ${sidecarPort}: ${err.message}` }));
      process.exit(1);
    });

    req.write(postData);
    req.end();
    return;
  }

  // 2. Micro-App Actions
  const port = resolveAppPort(toolName);
  if (port) {
    const chat = payload.chat || null;
    const postData = JSON.stringify({
      action: toolName,
      payload,
      source: 'mrflow_ai',
      chat
    });

    const req = http.request({
      hostname: '127.0.0.1',
      port,
      path: '/api/action',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      timeout: 5000
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          console.log(JSON.stringify(JSON.parse(body), null, 2));
        } catch (_) {
          console.log(body);
        }
      });
    });

    req.on('error', (err) => {
      console.error(JSON.stringify({ error: `Failed to connect to micro-app engine on port ${port}: ${err.message}` }));
      process.exit(1);
    });

    req.write(postData);
    req.end();
    return;
  }

  console.error(JSON.stringify({ error: `Unknown tool: ${toolName}` }));
  process.exit(1);
}

main();
