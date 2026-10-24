#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — OFFICIAL ANTHROPIC MCP SERVER IMPLEMENTATION (EXAMPLE)
 * Protocol: Model Context Protocol Specification (2024-11-05)
 * Transport: stdio (newline-delimited JSON-RPC 2.0)
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */

import readline from 'node:readline';
import os from 'node:os';
import fs from 'node:fs';
import path from 'node:path';

const rl = readline.createInterface({
  input: process.stdin,
  terminal: false
});

function sendResponse(id, result) {
  process.stdout.write(JSON.stringify({
    jsonrpc: '2.0',
    id,
    result
  }) + '\n');
}

function sendError(id, code, message, data = null) {
  const errObj = {
    jsonrpc: '2.0',
    id,
    error: {
      code,
      message
    }
  };
  if (data !== null) errObj.error.data = data;
  process.stdout.write(JSON.stringify(errObj) + '\n');
}

const TOOLS_MANIFEST = [
  {
    name: 'system_status',
    description: 'Retrieves sovereign host telemetry, CPU architecture, memory metrics, and OS kernel version.',
    inputSchema: {
      type: 'object',
      properties: {
        verbose: { type: 'boolean', description: 'Include deep CPU core and network interface telemetry' }
      }
    }
  },
  {
    name: 'inspect_workspace',
    description: 'Lists files and folders inside the active Flowork workspace directory.',
    inputSchema: {
      type: 'object',
      properties: {
        relative_path: { type: 'string', description: 'Relative path inside workspace (defaults to root)' },
        max_entries: { type: 'integer', description: 'Maximum directory entries to return' }
      }
    }
  }
];

rl.on('line', (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;

  let msg = null;
  try {
    msg = JSON.parse(trimmed);
  } catch (e) {
    sendError(null, -32700, `Parse error: ${e.message}`);
    return;
  }

  if (!msg || msg.jsonrpc !== '2.0') {
    sendError(msg?.id || null, -32600, 'Invalid Request: jsonrpc must be 2.0');
    return;
  }

  const { id, method, params } = msg;

  // 1. Handshake: initialize
  if (method === 'initialize') {
    return sendResponse(id, {
      protocolVersion: '2024-11-05',
      capabilities: {
        tools: { listChanged: false },
        resources: {},
        prompts: {}
      },
      serverInfo: {
        name: 'flowork-system-mcp',
        version: '1.0.0'
      }
    });
  }

  // 2. Notification: notifications/initialized
  if (method === 'notifications/initialized') {
    // Fire-and-forget notification from client
    return;
  }

  // 3. Ping
  if (method === 'ping') {
    return sendResponse(id, {});
  }

  // 4. Tools List: tools/list
  if (method === 'tools/list') {
    return sendResponse(id, {
      tools: TOOLS_MANIFEST
    });
  }

  // 5. Tools Call: tools/call
  if (method === 'tools/call') {
    const toolName = params?.name;
    const args = params?.arguments || {};

    if (toolName === 'system_status') {
      const verbose = Boolean(args.verbose);
      const data = {
        platform: os.platform(),
        arch: os.arch(),
        release: os.release(),
        uptime_seconds: Math.floor(os.uptime()),
        free_memory_mb: Math.floor(os.freemem() / (1024 * 1024)),
        total_memory_mb: Math.floor(os.totalmem() / (1024 * 1024)),
        load_average: os.loadavg()
      };
      if (verbose) {
        data.cpus = os.cpus().map(c => ({ model: c.model, speed: c.speed }));
        data.hostname = os.hostname();
      }

      return sendResponse(id, {
        content: [
          {
            type: 'text',
            text: JSON.stringify(data, null, 2)
          }
        ],
        isError: false
      });
    }

    if (toolName === 'inspect_workspace') {
      const relPath = args.relative_path || '.';
      const maxEntries = Math.min(Number(args.max_entries) || 50, 200);
      const targetDir = path.resolve(process.cwd(), relPath);

      try {
        if (!fs.existsSync(targetDir)) {
          return sendResponse(id, {
            content: [{ type: 'text', text: `Directory not found: ${relPath}` }],
            isError: true
          });
        }

        const entries = fs.readdirSync(targetDir, { withFileTypes: true }).slice(0, maxEntries).map(e => ({
          name: e.name,
          type: e.isDirectory() ? 'directory' : 'file'
        }));

        return sendResponse(id, {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ path: relPath, entries }, null, 2)
            }
          ],
          isError: false
        });
      } catch (err) {
        return sendResponse(id, {
          content: [{ type: 'text', text: `Error inspecting workspace: ${err.message}` }],
          isError: true
        });
      }
    }

    return sendError(id, -32601, `Method/Tool not found: ${toolName}`);
  }

  // Unknown method
  return sendError(id, -32601, `Method not implemented: ${method}`);
});
