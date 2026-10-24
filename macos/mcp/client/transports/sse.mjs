/**
 * ⚡ FLOWORK OS — MODEL CONTEXT PROTOCOL (MCP)
 * Module: Server-Sent Events (SSE) HTTP Transport Engine
 * Specification: Standard SSE communication transport for MCP servers
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */

import http from 'node:http';
import https from 'node:https';
import { URL } from 'node:url';

export class SseTransport {
  constructor(options = {}) {
    this.name = options.name || 'sse-server';
    this.url = options.url;
    this.headers = options.headers || {};
    this.timeoutMs = options.timeoutMs || 25000;

    this.postEndpoint = null;
    this.pendingRequests = new Map();
    this.isClosed = false;
    this.sseReq = null;
  }

  /**
   * Connect to the SSE endpoint and await the initial 'endpoint' registration event
   */
  async start() {
    if (!this.url) {
      throw new Error(`[MCP SSE: ${this.name}] No SSE URL specified.`);
    }

    const sseUrlObj = new URL(this.url);
    const client = sseUrlObj.protocol === 'https:' ? https : http;

    return new Promise((resolve, reject) => {
      let isInitResolved = false;

      const connectTimeout = setTimeout(() => {
        if (!isInitResolved) {
          isInitResolved = true;
          this.close();
          reject(new Error(`[MCP SSE: ${this.name}] Connection timed out waiting for endpoint event (${this.timeoutMs}ms)`));
        }
      }, this.timeoutMs);

      const reqOptions = {
        hostname: sseUrlObj.hostname,
        port: sseUrlObj.port || (sseUrlObj.protocol === 'https:' ? 443 : 80),
        path: sseUrlObj.pathname + sseUrlObj.search,
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          ...this.headers
        }
      };

      this.sseReq = client.request(reqOptions, (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          clearTimeout(connectTimeout);
          if (!isInitResolved) {
            isInitResolved = true;
            reject(new Error(`[MCP SSE: ${this.name}] HTTP ${res.statusCode}: ${res.statusMessage}`));
          }
          return;
        }

        let buffer = '';
        let currentEvent = 'message';

        res.on('data', (chunk) => {
          buffer += chunk.toString();
          const lines = buffer.split('\n');
          buffer = lines.pop(); // Retain incomplete line

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) {
              currentEvent = 'message';
              continue;
            }

            if (trimmed.startsWith('event:')) {
              currentEvent = trimmed.slice(6).trim();
            } else if (trimmed.startsWith('data:')) {
              const dataStr = trimmed.slice(5).trim();
              this._handleSseEvent(currentEvent, dataStr, sseUrlObj, () => {
                if (!isInitResolved) {
                  isInitResolved = true;
                  clearTimeout(connectTimeout);
                  resolve(true);
                }
              });
            }
          }
        });

        res.on('end', () => {
          this._handleDisconnect('SSE stream closed by server');
        });

        res.on('error', (err) => {
          this._handleDisconnect(err.message);
        });
      });

      this.sseReq.on('error', (err) => {
        clearTimeout(connectTimeout);
        if (!isInitResolved) {
          isInitResolved = true;
          reject(new Error(`[MCP SSE: ${this.name}] Connection error: ${err.message}`));
        }
      });

      this.sseReq.end();
    });
  }

  _handleSseEvent(eventType, dataStr, baseSseUrl, onReady) {
    if (eventType === 'endpoint') {
      try {
        // endpoint event gives the path or full URL for sending HTTP POST requests
        if (dataStr.startsWith('http://') || dataStr.startsWith('https://')) {
          this.postEndpoint = dataStr;
        } else {
          const resolved = new URL(dataStr, baseSseUrl.origin);
          this.postEndpoint = resolved.toString();
        }
        if (onReady) onReady();
      } catch (err) {
        console.error(`[MCP SSE: ${this.name}] Invalid endpoint event payload:`, dataStr);
      }
      return;
    }

    if (eventType === 'message' || eventType === '') {
      let message = null;
      try {
        message = JSON.parse(dataStr);
      } catch (_) {
        return;
      }

      if (!message || message.jsonrpc !== '2.0') return;

      const msgId = message.id;
      if (msgId !== undefined && msgId !== null && this.pendingRequests.has(msgId)) {
        const { resolve, reject, timeoutHandle } = this.pendingRequests.get(msgId);
        if (timeoutHandle) clearTimeout(timeoutHandle);
        this.pendingRequests.delete(msgId);

        if (message.error) {
          reject(new Error(`[MCP Remote Error] ${message.error.message || 'Unknown error'} (Code: ${message.error.code})`));
        } else {
          resolve(message.result !== undefined ? message.result : message);
        }
      }
    }
  }

  _handleDisconnect(reason) {
    this.isClosed = true;
    for (const [id, req] of this.pendingRequests) {
      if (req.timeoutHandle) clearTimeout(req.timeoutHandle);
      req.reject(new Error(`[MCP SSE: ${this.name}] Disconnected: ${reason}`));
    }
    this.pendingRequests.clear();
  }

  /**
   * Send a JSON-RPC request to the POST endpoint
   */
  async send(requestPayload, timeoutMs = null) {
    if (this.isClosed || !this.postEndpoint) {
      throw new Error(`[MCP SSE: ${this.name}] Transport not connected or message endpoint missing.`);
    }

    const reqId = requestPayload.id;
    const effectiveTimeout = timeoutMs || this.timeoutMs;

    return new Promise((resolve, reject) => {
      let timeoutHandle = null;
      if (reqId !== undefined && reqId !== null) {
        timeoutHandle = setTimeout(() => {
          this.pendingRequests.delete(reqId);
          reject(new Error(`[MCP SSE: ${this.name}] Request timeout (${effectiveTimeout}ms) for method '${requestPayload.method}'`));
        }, effectiveTimeout);

        this.pendingRequests.set(reqId, { resolve, reject, timeoutHandle, method: requestPayload.method });
      }

      const postUrlObj = new URL(this.postEndpoint);
      const client = postUrlObj.protocol === 'https:' ? https : http;
      const postData = JSON.stringify(requestPayload);

      const reqOptions = {
        hostname: postUrlObj.hostname,
        port: postUrlObj.port || (postUrlObj.protocol === 'https:' ? 443 : 80),
        path: postUrlObj.pathname + postUrlObj.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData),
          ...this.headers
        }
      };

      const req = client.request(reqOptions, (res) => {
        let respBody = '';
        res.on('data', chunk => respBody += chunk);
        res.on('end', () => {
          if (res.statusCode >= 400) {
            if (timeoutHandle) clearTimeout(timeoutHandle);
            this.pendingRequests.delete(reqId);
            reject(new Error(`[MCP SSE: ${this.name}] HTTP POST ${res.statusCode}: ${respBody}`));
            return;
          }

          // If server responds directly via HTTP body instead of SSE stream
          if (respBody.trim().startsWith('{')) {
            try {
              const parsed = JSON.parse(respBody);
              if (parsed && parsed.jsonrpc === '2.0' && parsed.id === reqId) {
                if (timeoutHandle) clearTimeout(timeoutHandle);
                this.pendingRequests.delete(reqId);
                if (parsed.error) {
                  reject(new Error(`[MCP Remote Error] ${parsed.error.message} (Code: ${parsed.error.code})`));
                } else {
                  resolve(parsed.result !== undefined ? parsed.result : parsed);
                }
              }
            } catch (_) {}
          }

          if (reqId === undefined || reqId === null) {
            resolve(true);
          }
        });
      });

      req.on('error', (err) => {
        if (timeoutHandle) clearTimeout(timeoutHandle);
        this.pendingRequests.delete(reqId);
        reject(new Error(`[MCP SSE: ${this.name}] Post error: ${err.message}`));
      });

      req.write(postData);
      req.end();
    });
  }

  notify(notificationPayload) {
    if (this.isClosed || !this.postEndpoint) return false;
    this.send(notificationPayload).catch(() => {});
    return true;
  }

  close() {
    this.isClosed = true;
    if (this.sseReq) {
      try { this.sseReq.destroy(); } catch (_) {}
    }
    this._handleDisconnect('Closed by client');
  }
}
