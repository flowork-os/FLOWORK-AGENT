/**
 * ⚡ FLOWORK OS — MODEL CONTEXT PROTOCOL (MCP)
 * Module: Zero-Breaking Legacy Canvas Sidecar Adapter
 * Specification: Bridges legacy local HTTP micro-apps to MCP standard
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

export class LegacySidecarAdapter {
  constructor(options = {}) {
    this.name = options.name || 'canvas-legacy';
    this.projectRoot = options.projectRoot || process.cwd();
  }

  resolveAppPort(tool) {
    if (tool.startsWith('chess_')) return Number(process.env.FLOWORK_CHESS_PORT) || 17820;
    if (tool.startsWith('trade_')) return Number(process.env.FLOWORK_TRADING_PORT) || 17821;
    if (tool.startsWith('website_intel_') || tool.startsWith('intel_')) return Number(process.env.FLOWORK_WEBINTEL_PORT) || 17822;
    if (tool.startsWith('youtube_')) return Number(process.env.FLOWORK_YOUTUBE_PORT) || 17823;
    if (tool.startsWith('websec_')) return Number(process.env.FLOWORK_WEBSEC_PORT) || 17824;
    if (tool === 'canvas_control' || tool === 'flow_canvas_control') return Number(process.env.FLOWORK_SIDECAR_HOST_PORT) || 17700;

    // Dynamic scan from apps/
    try {
      const appsDir = path.join(this.projectRoot, 'apps');
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

  isLegacyTool(toolName) {
    if (toolName === 'canvas_control' || toolName === 'flow_canvas_control') return true;
    return this.resolveAppPort(toolName) !== null;
  }

  async listTools() {
    return [
      {
        name: 'canvas_control',
        description: 'Flowork Canvas Stage & UI Supervisor. Controls widgets, layout, viewports, and interactive stage components.',
        inputSchema: {
          type: 'object',
          properties: {
            action: { type: 'string', description: 'Canvas command action' },
            payload: { type: 'object', description: 'Action payload' }
          },
          required: ['action']
        }
      },
      {
        name: 'chess_move',
        description: 'Chess Arena micro-app. Execute moves or analyze chess state.',
        inputSchema: {
          type: 'object',
          properties: {
            fen: { type: 'string', description: 'Board FEN' },
            move: { type: 'string', description: 'UCI or SAN move' }
          }
        }
      },
      {
        name: 'trade_scan',
        description: 'Quantitative Trading Engine micro-app. Scan market metrics and liquidity.',
        inputSchema: {
          type: 'object',
          properties: {
            symbol: { type: 'string', description: 'Trading pair symbol' }
          }
        }
      },
      {
        name: 'website_intel_scan',
        description: 'Website Intelligence micro-app. Deep traffic and technical analysis.',
        inputSchema: {
          type: 'object',
          properties: {
            domain: { type: 'string', description: 'Target domain' }
          },
          required: ['domain']
        }
      },
      {
        name: 'youtube_action',
        description: 'YouTube Media Studio micro-app. Stream and analyze video/audio data.',
        inputSchema: {
          type: 'object',
          properties: {
            video_id: { type: 'string', description: 'YouTube Video ID or URL' }
          }
        }
      },
      {
        name: 'websec_scan',
        description: 'Web Security Scanner micro-app. Port scan and SSL/header auditing.',
        inputSchema: {
          type: 'object',
          properties: {
            target: { type: 'string', description: 'Target IP or hostname' }
          },
          required: ['target']
        }
      }
    ];
  }

  async callTool(toolName, payload = {}) {
    const isCanvas = (toolName === 'canvas_control' || toolName === 'flow_canvas_control');
    const port = isCanvas ? (Number(process.env.FLOWORK_SIDECAR_HOST_PORT) || 17700) : this.resolveAppPort(toolName);

    if (!port) {
      throw new Error(`[Legacy Sidecar] No active port resolved for tool: ${toolName}`);
    }

    const postPath = isCanvas ? '/api/canvas/action' : '/api/action';
    const bodyObj = isCanvas ? payload : {
      action: toolName,
      payload,
      source: 'mrflow_ai',
      chat: payload.chat || null
    };

    const postData = JSON.stringify(bodyObj);

    return new Promise((resolve, reject) => {
      const req = http.request({
        hostname: '127.0.0.1',
        port,
        path: postPath,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData)
        },
        timeout: 10000
      }, (res) => {
        let resp = '';
        res.on('data', chunk => resp += chunk);
        res.on('end', () => {
          let parsed = null;
          try {
            parsed = JSON.parse(resp);
          } catch (_) {
            parsed = { raw: resp };
          }
          // Wrap in standard Anthropic MCP tool result schema
          resolve({
            content: [
              {
                type: 'text',
                text: typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2)
              }
            ],
            isError: res.statusCode >= 400
          });
        });
      });

      req.on('error', (err) => {
        reject(new Error(`Failed to connect to local sidecar on port ${port}: ${err.message}`));
      });

      req.write(postData);
      req.end();
    });
  }
}
