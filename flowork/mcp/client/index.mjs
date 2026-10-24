/**
 * ⚡ FLOWORK OS — MODEL CONTEXT PROTOCOL (MCP)
 * Module: Sovereign Universal MCP Client Manager & Orchestrator
 * Specification: Anthropic Model Context Protocol Client (2024-11-05)
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  buildInitializePayload,
  buildInitializedNotification,
  buildListToolsRequest,
  buildCallToolRequest,
  buildPingRequest
} from './protocol.mjs';

import { StdioTransport } from './transports/stdio.mjs';
import { SseTransport } from './transports/sse.mjs';
import { LegacySidecarAdapter } from './transports/legacy.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SCRIPT_DIR = path.resolve(__dirname, '..');
const PROJECT_ROOT = path.resolve(SCRIPT_DIR, '..');

export class McpClientManager {
  constructor(options = {}) {
    this.projectRoot = options.projectRoot || PROJECT_ROOT;
    this.transports = new Map();
    this.serverMeta = new Map();
    this.cachedToolRegistry = new Map();
    this.legacyAdapter = new LegacySidecarAdapter({ projectRoot: this.projectRoot });
  }

  /**
   * Resolves the active mcp_servers.json configuration file
   */
  resolveConfigFile() {
    const candidates = [
      path.join(this.projectRoot, 'portable-home', '.flowork', 'mcp_servers.json'),
      path.join(this.projectRoot, 'mcp', 'mcp_servers.json'),
      path.join(SCRIPT_DIR, 'mcp_servers.json')
    ];

    for (const p of candidates) {
      if (fs.existsSync(p)) return p;
    }
    return candidates[0];
  }

  /**
   * Load mcpServers map from configuration
   */
  loadConfig() {
    const cfgPath = this.resolveConfigFile();
    if (!fs.existsSync(cfgPath)) {
      return { mcpServers: {} };
    }
    try {
      const raw = fs.readFileSync(cfgPath, 'utf8');
      const parsed = JSON.parse(raw);
      return parsed && parsed.mcpServers ? parsed : { mcpServers: parsed || {} };
    } catch (err) {
      console.error(`[MCP Manager] Failed to parse config ${cfgPath}: ${err.message}`);
      return { mcpServers: {} };
    }
  }

  /**
   * Connect and initialize a specific MCP server
   */
  async connectServer(serverName, serverConfig = null) {
    if (this.transports.has(serverName)) {
      return this.transports.get(serverName);
    }

    if (!serverConfig) {
      const config = this.loadConfig();
      serverConfig = config.mcpServers[serverName];
      if (!serverConfig) {
        throw new Error(`[MCP Manager] Server '${serverName}' not found in configuration.`);
      }
    }

    let transport = null;

    // 1. Internal Legacy Adapter
    if (serverConfig.type === 'internal-sidecar' || serverConfig.type === 'legacy') {
      transport = this.legacyAdapter;
      this.transports.set(serverName, transport);
      this.serverMeta.set(serverName, { name: serverName, type: 'legacy', capabilities: { tools: {} } });
      return transport;
    }

    // 2. SSE Transport
    if (serverConfig.url) {
      transport = new SseTransport({
        name: serverName,
        url: serverConfig.url,
        headers: serverConfig.headers || {},
        timeoutMs: serverConfig.timeoutMs || 25000
      });
    }
    // 3. Stdio Transport
    else if (serverConfig.command) {
      transport = new StdioTransport({
        name: serverName,
        command: serverConfig.command,
        args: serverConfig.args || [],
        env: serverConfig.env || {},
        cwd: serverConfig.cwd ? path.resolve(this.projectRoot, serverConfig.cwd) : this.projectRoot,
        timeoutMs: serverConfig.timeoutMs || 25000
      });
    } else {
      throw new Error(`[MCP Manager] Server '${serverName}' must specify either 'command' (stdio) or 'url' (sse).`);
    }

    // Start transport
    await transport.start();

    // Perform MCP Handshake: initialize
    const initReq = buildInitializePayload({ name: 'Flowork-Sovereign-MCP-Client' });
    const initResult = await transport.send(initReq);

    // Send notifications/initialized
    const initNotify = buildInitializedNotification();
    transport.notify(initNotify);

    this.transports.set(serverName, transport);
    this.serverMeta.set(serverName, {
      name: serverName,
      type: serverConfig.url ? 'sse' : 'stdio',
      serverInfo: initResult?.serverInfo || {},
      capabilities: initResult?.capabilities || {}
    });

    return transport;
  }

  /**
   * Queries tools/list from a server
   */
  async listServerTools(serverName) {
    const transport = await this.connectServer(serverName);

    if (transport === this.legacyAdapter) {
      const legacyTools = await this.legacyAdapter.listTools();
      return legacyTools.map(t => ({
        ...t,
        server: serverName
      }));
    }

    const listReq = buildListToolsRequest();
    const result = await transport.send(listReq);
    const tools = (result && Array.isArray(result.tools)) ? result.tools : [];

    return tools.map(t => ({
      ...t,
      server: serverName
    }));
  }

  /**
   * Enumerate all tools across all configured MCP servers
   */
  async listAllTools() {
    const config = this.loadConfig();
    const servers = Object.keys(config.mcpServers || {});
    const catalog = [];

    // Always include internal sidecars if not explicitly excluded
    if (!servers.includes('canvas-legacy')) {
      const legacyTools = await this.legacyAdapter.listTools();
      for (const lt of legacyTools) {
        catalog.push({ ...lt, server: 'canvas-legacy' });
      }
    }

    for (const sName of servers) {
      try {
        const tools = await this.listServerTools(sName);
        for (const t of tools) {
          catalog.push(t);
          this.cachedToolRegistry.set(t.name, sName);
          this.cachedToolRegistry.set(`${sName}_${t.name}`, sName);
        }
      } catch (err) {
        console.warn(`[MCP Manager] Failed to list tools from server '${sName}': ${err.message}`);
      }
    }

    return catalog;
  }

  /**
   * Execute a tool call on an MCP server
   */
  async callTool(toolName, args = {}, explicitServer = null) {
    // 1. Direct Legacy Sidecar check
    if (!explicitServer && this.legacyAdapter.isLegacyTool(toolName)) {
      return await this.legacyAdapter.callTool(toolName, args);
    }

    // 2. Resolve Server
    let targetServer = explicitServer;
    let actualToolName = toolName;

    if (!targetServer) {
      // Check cache
      if (this.cachedToolRegistry.has(toolName)) {
        targetServer = this.cachedToolRegistry.get(toolName);
      } else {
        // Refresh catalog once
        await this.listAllTools();
        if (this.cachedToolRegistry.has(toolName)) {
          targetServer = this.cachedToolRegistry.get(toolName);
        }
      }
    }

    // Try splitting prefix (e.g., sqlite_read_query -> server: sqlite, tool: read_query)
    if (!targetServer && toolName.includes('_')) {
      const parts = toolName.split('_');
      const possibleServer = parts[0];
      const config = this.loadConfig();
      if (config.mcpServers && config.mcpServers[possibleServer]) {
        targetServer = possibleServer;
        actualToolName = parts.slice(1).join('_');
      }
    }

    if (!targetServer) {
      // Fallback: if tool is legacy app
      if (this.legacyAdapter.isLegacyTool(actualToolName)) {
        return await this.legacyAdapter.callTool(actualToolName, args);
      }
      throw new Error(`[MCP Manager] No MCP server found for tool: '${toolName}'`);
    }

    const transport = await this.connectServer(targetServer);

    if (transport === this.legacyAdapter) {
      return await this.legacyAdapter.callTool(actualToolName, args);
    }

    const callReq = buildCallToolRequest(actualToolName, args);
    const result = await transport.send(callReq);

    return result;
  }

  /**
   * Ping an MCP server to verify alive state
   */
  async ping(serverName) {
    const transport = await this.connectServer(serverName);
    if (transport === this.legacyAdapter) return { ok: true, type: 'legacy' };
    const pingReq = buildPingRequest();
    return await transport.send(pingReq);
  }

  /**
   * Close all active transports gracefully
   */
  async closeAll() {
    for (const [name, transport] of this.transports) {
      try {
        if (typeof transport.close === 'function') {
          await transport.close();
        }
      } catch (_) {}
    }
    this.transports.clear();
    this.serverMeta.clear();
  }
}
