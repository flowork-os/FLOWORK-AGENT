#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — UNIVERSAL SOVEREIGN MCP NANO-TOOL RUNNER & DISPATCHER
 * ====================================================================
 * Specification: Anthropic Model Context Protocol (MCP) Standard Client
 * Backwards Compatible: Fully supports legacy local Canvas micro-apps
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */

import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { McpClientManager } from './client/index.mjs';
import { McpToolSyncer } from './bridge/tool_syncer.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..');

const clientManager = new McpClientManager({ projectRoot: PROJECT_ROOT });

async function printHelp() {
  console.log(`
⚡ FLOWORK OS — UNIVERSAL MODEL CONTEXT PROTOCOL (MCP) RUNNER
============================================================
Standard: Anthropic MCP JSON-RPC 2.0 (stdio & sse) + Canvas Legacy

USAGE (Agent Tool Invocation):
  node mcp/run.mjs <tool_name> [json_payload]

ADMIN & DISCOVERY COMMANDS:
  node mcp/run.mjs --list               List all tools across active MCP servers
  node mcp/run.mjs --sync               Sync external MCP tools into tools/ registry
  node mcp/run.mjs --ping [server]      Verify server handshake & latency
  node mcp/run.mjs --call <srv> <tool>  Execute tool on specific MCP server
  node mcp/run.mjs --help               Show this manual

EXAMPLES:
  node mcp/run.mjs canvas_control '{"action": "focus_window"}'
  node mcp/run.mjs system_status '{"verbose": true}'
  node mcp/run.mjs --call flowork-system system_status '{}'
`);
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    await printHelp();
    process.exit(0);
  }

  const firstArg = args[0];

  // 1. Discovery Command: --list / list
  if (firstArg === '--list' || firstArg === 'list') {
    try {
      console.log('🔍 Querying active MCP Servers & Dynamic Tools...\n');
      const catalog = await clientManager.listAllTools();
      if (catalog.length === 0) {
        console.log('ℹ️ No tools discovered. Configure servers in portable-home/.flowork/mcp_servers.json');
      } else {
        console.log(`Found ${catalog.length} available tools:`);
        console.log('------------------------------------------------------------');
        for (const t of catalog) {
          console.log(`• [${t.server}] \x1b[36m${t.name}\x1b[0m`);
          if (t.description) console.log(`  └─ ${t.description}`);
        }
        console.log('------------------------------------------------------------');
      }
      await clientManager.closeAll();
      process.exit(0);
    } catch (err) {
      console.error(`❌ Failed to list MCP tools: ${err.message}`);
      await clientManager.closeAll();
      process.exit(1);
    }
  }

  // 2. Sync Command: --sync / sync
  if (firstArg === '--sync' || firstArg === 'sync') {
    try {
      const syncer = new McpToolSyncer({ projectRoot: PROJECT_ROOT });
      await syncer.syncTools();
      process.exit(0);
    } catch (err) {
      console.error(`❌ Failed to sync MCP tools: ${err.message}`);
      process.exit(1);
    }
  }

  // 3. Ping Command: --ping / ping
  if (firstArg === '--ping' || firstArg === 'ping') {
    const targetServer = args[1] || 'flowork-system';
    try {
      console.log(`📡 Pinging MCP server [${targetServer}]...`);
      const start = Date.now();
      const res = await clientManager.ping(targetServer);
      const elapsed = Date.now() - start;
      console.log(`✅ Handshake OK (${elapsed}ms). Response:`, res);
      await clientManager.closeAll();
      process.exit(0);
    } catch (err) {
      console.error(`❌ Ping failed for [${targetServer}]: ${err.message}`);
      await clientManager.closeAll();
      process.exit(1);
    }
  }

  // 4. Explicit Call: --call <server> <tool> [json_args]
  if (firstArg === '--call') {
    const serverName = args[1];
    const toolName = args[2];
    let payload = {};
    if (args[3]) {
      try {
        payload = JSON.parse(args[3]);
      } catch (e) {
        console.error(JSON.stringify({ error: `Invalid JSON payload: ${e.message}` }));
        process.exit(1);
      }
    }

    try {
      const result = await clientManager.callTool(toolName, payload, serverName);
      console.log(JSON.stringify(result, null, 2));
      await clientManager.closeAll();
      process.exit(0);
    } catch (err) {
      console.error(JSON.stringify({ error: `Tool call failed: ${err.message}` }));
      await clientManager.closeAll();
      process.exit(1);
    }
  }

  // 5. Standard Agent Tool Invocation: node mcp/run.mjs <tool_name> [json_args]
  const toolName = firstArg;
  const rawPayload = args[1] || '{}';
  let payload = {};

  try {
    payload = JSON.parse(rawPayload);
  } catch (e) {
    console.error(JSON.stringify({ error: `Invalid JSON payload: ${e.message}` }));
    process.exit(1);
  }

  try {
    const result = await clientManager.callTool(toolName, payload);
    // If output is standard MCP content array, print cleanly
    if (result && Array.isArray(result.content) && result.content[0]?.text) {
      try {
        // Pretty-print if inner text is JSON
        const innerJson = JSON.parse(result.content[0].text);
        console.log(JSON.stringify(innerJson, null, 2));
      } catch (_) {
        console.log(result.content[0].text);
      }
    } else {
      console.log(JSON.stringify(result, null, 2));
    }
    await clientManager.closeAll();
    process.exit(0);
  } catch (err) {
    console.error(JSON.stringify({ error: err.message }, null, 2));
    await clientManager.closeAll();
    process.exit(1);
  }
}

main().catch(async (err) => {
  console.error(JSON.stringify({ error: `Fatal MCP Runner Error: ${err.message}` }, null, 2));
  try {
    await clientManager.closeAll();
  } catch (_) {}
  process.exit(1);
});
