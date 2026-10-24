/**
 * ⚡ FLOWORK OS — MODEL CONTEXT PROTOCOL (MCP)
 * Module: Stdio Subprocess Transport Engine
 * Specification: Standard stdio communication stream for MCP servers
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */

import { spawn } from 'node:child_process';
import readline from 'node:readline';

export class StdioTransport {
  constructor(options = {}) {
    this.name = options.name || 'stdio-server';
    this.command = options.command;
    this.args = Array.isArray(options.args) ? options.args : [];
    this.env = options.env || {};
    this.cwd = options.cwd || process.cwd();
    this.timeoutMs = options.timeoutMs || 25000;

    this.process = null;
    this.pendingRequests = new Map();
    this.isClosed = false;
    this.rl = null;
  }

  /**
   * Start the external server process and bind stdin/stdout streams
   */
  async start() {
    if (!this.command) {
      throw new Error(`[MCP Stdio: ${this.name}] No command specified.`);
    }

    const mergedEnv = {
      ...process.env,
      ...this.env,
      NODE_NO_WARNINGS: '1'
    };

    try {
      this.process = spawn(this.command, this.args, {
        cwd: this.cwd,
        env: mergedEnv,
        stdio: ['pipe', 'pipe', 'pipe']
      });
    } catch (err) {
      throw new Error(`[MCP Stdio: ${this.name}] Failed to spawn process '${this.command}': ${err.message}`);
    }

    this.process.on('error', (err) => {
      this._handleProcessError(err);
    });

    this.process.on('exit', (code, signal) => {
      this._handleProcessExit(code, signal);
    });

    // Pipe stderr safely to prevent buffer deadlocks
    this.process.stderr.on('data', (chunk) => {
      const errStr = chunk.toString().trim();
      if (errStr && (process.env.FLOWORK_MCP_DEBUG === '1' || process.env.DEBUG === '1')) {
        console.error(`[MCP Server ${this.name} stderr]: ${errStr}`);
      }
    });

    // Read newline-delimited JSON-RPC from stdout
    this.rl = readline.createInterface({
      input: this.process.stdout,
      terminal: false
    });

    this.rl.on('line', (line) => {
      this._handleIncomingLine(line);
    });

    return true;
  }

  /**
   * Send a JSON-RPC request and wait for the correlated response
   */
  async send(requestPayload, timeoutMs = null) {
    if (this.isClosed || !this.process || !this.process.stdin.writable) {
      throw new Error(`[MCP Stdio: ${this.name}] Server process is not running or stdin is closed.`);
    }

    const reqId = requestPayload.id;
    const effectiveTimeout = timeoutMs || this.timeoutMs;

    return new Promise((resolve, reject) => {
      let timeoutHandle = null;
      if (reqId !== undefined && reqId !== null) {
        timeoutHandle = setTimeout(() => {
          this.pendingRequests.delete(reqId);
          reject(new Error(`[MCP Stdio: ${this.name}] Request timeout (${effectiveTimeout}ms) for method '${requestPayload.method}' [id: ${reqId}]`));
        }, effectiveTimeout);

        this.pendingRequests.set(reqId, { resolve, reject, timeoutHandle, method: requestPayload.method });
      }

      try {
        const payloadString = JSON.stringify(requestPayload) + '\n';
        this.process.stdin.write(payloadString, 'utf8', (err) => {
          if (err) {
            if (timeoutHandle) clearTimeout(timeoutHandle);
            this.pendingRequests.delete(reqId);
            reject(new Error(`[MCP Stdio: ${this.name}] Failed to write to stdin: ${err.message}`));
          } else if (reqId === undefined || reqId === null) {
            // Notification: resolve immediately
            resolve(true);
          }
        });
      } catch (err) {
        if (timeoutHandle) clearTimeout(timeoutHandle);
        this.pendingRequests.delete(reqId);
        reject(err);
      }
    });
  }

  /**
   * Send a notification (fire-and-forget)
   */
  notify(notificationPayload) {
    if (this.isClosed || !this.process || !this.process.stdin.writable) {
      return false;
    }
    try {
      this.process.stdin.write(JSON.stringify(notificationPayload) + '\n');
      return true;
    } catch (_) {
      return false;
    }
  }

  _handleIncomingLine(line) {
    const trimmed = line.trim();
    if (!trimmed) return;

    let message = null;
    try {
      message = JSON.parse(trimmed);
    } catch (_) {
      // Ignore non-JSON output from subprocess
      return;
    }

    if (!message || message.jsonrpc !== '2.0') {
      return;
    }

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

  _handleProcessError(err) {
    for (const [id, req] of this.pendingRequests) {
      if (req.timeoutHandle) clearTimeout(req.timeoutHandle);
      req.reject(new Error(`[MCP Stdio: ${this.name}] Process error: ${err.message}`));
    }
    this.pendingRequests.clear();
  }

  _handleProcessExit(code, signal) {
    this.isClosed = true;
    for (const [id, req] of this.pendingRequests) {
      if (req.timeoutHandle) clearTimeout(req.timeoutHandle);
      req.reject(new Error(`[MCP Stdio: ${this.name}] Process exited with code ${code} (${signal || 'terminated'})`));
    }
    this.pendingRequests.clear();
  }

  /**
   * Gracefully terminate the transport
   */
  async close() {
    this.isClosed = true;
    if (this.rl) {
      try { this.rl.close(); } catch (_) {}
    }
    if (this.process) {
      try {
        this.process.stdin.end();
      } catch (_) {}
      try {
        this.process.kill('SIGTERM');
      } catch (_) {}
      setTimeout(() => {
        try {
          if (this.process && !this.process.killed) {
            this.process.kill('SIGKILL');
          }
        } catch (_) {}
      }, 500);
    }
  }
}
