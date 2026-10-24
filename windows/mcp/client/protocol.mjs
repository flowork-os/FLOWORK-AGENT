/**
 * ⚡ FLOWORK OS — MODEL CONTEXT PROTOCOL (MCP)
 * Module: JSON-RPC 2.0 & Official Anthropic MCP Protocol Engine
 * Standard: Model Context Protocol (Anthropic Specification 2024-11-05)
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */

export const PROTOCOL_VERSION = '2024-11-05';
export const CLIENT_NAME = 'Flowork-Sovereign-MCP';
export const CLIENT_VERSION = '2.0.0';

export const JSONRPC_ERRORS = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
  SERVER_NOT_INITIALIZED: -32002,
  UNKNOWN_ERROR: -32001
};

let _nextId = 1;

export function getNextRequestId() {
  return _nextId++;
}

/**
 * Creates standard JSON-RPC 2.0 Request
 */
export function createRequest(method, params = {}, id = null) {
  return {
    jsonrpc: '2.0',
    id: id !== null ? id : getNextRequestId(),
    method,
    params
  };
}

/**
 * Creates standard JSON-RPC 2.0 Notification (no id, fire-and-forget)
 */
export function createNotification(method, params = {}) {
  return {
    jsonrpc: '2.0',
    method,
    params
  };
}

/**
 * Creates standard JSON-RPC 2.0 Success Response
 */
export function createResponse(id, result) {
  return {
    jsonrpc: '2.0',
    id,
    result
  };
}

/**
 * Creates standard JSON-RPC 2.0 Error Response
 */
export function createErrorResponse(id, code, message, data = null) {
  const res = {
    jsonrpc: '2.0',
    id,
    error: {
      code,
      message
    }
  };
  if (data !== null) {
    res.error.data = data;
  }
  return res;
}

/**
 * Builds MCP initialize handshake payload
 */
export function buildInitializePayload(customClientInfo = {}) {
  return createRequest('initialize', {
    protocolVersion: PROTOCOL_VERSION,
    capabilities: {
      roots: { listChanged: true },
      sampling: {}
    },
    clientInfo: {
      name: customClientInfo.name || CLIENT_NAME,
      version: customClientInfo.version || CLIENT_VERSION
    }
  });
}

/**
 * Builds MCP notifications/initialized payload
 */
export function buildInitializedNotification() {
  return createNotification('notifications/initialized', {});
}

/**
 * Builds MCP ping request
 */
export function buildPingRequest() {
  return createRequest('ping', {});
}

/**
 * Builds MCP tools/list request
 */
export function buildListToolsRequest(cursor = null) {
  const params = cursor ? { cursor } : {};
  return createRequest('tools/list', params);
}

/**
 * Builds MCP tools/call request
 */
export function buildCallToolRequest(name, args = {}) {
  return createRequest('tools/call', {
    name,
    arguments: args
  });
}

/**
 * Builds MCP resources/list request
 */
export function buildListResourcesRequest(cursor = null) {
  const params = cursor ? { cursor } : {};
  return createRequest('resources/list', params);
}

/**
 * Builds MCP prompts/list request
 */
export function buildListPromptsRequest(cursor = null) {
  const params = cursor ? { cursor } : {};
  return createRequest('prompts/list', params);
}

/**
 * Safely parse incoming line or message buffer into JSON-RPC object
 */
export function parseJsonRpcMessage(rawString) {
  const trimmed = rawString.trim();
  if (!trimmed) return null;
  try {
    const parsed = JSON.parse(trimmed);
    if (parsed && typeof parsed === 'object' && parsed.jsonrpc === '2.0') {
      return parsed;
    }
    return null;
  } catch (_) {
    return null;
  }
}
