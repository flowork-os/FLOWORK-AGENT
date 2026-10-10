#!/usr/bin/env node
/**
 * 🔬 rea_decompile - Sovereign Reverse Engineering Nano-Plug
 * Command: decompile (native)
 * Description: Read one part of an app as code (Hybrid Socket Bridge + POSIX Fallback)
 * Zero-Crash Hardened: Bulletproof try/catch & process.exit(0) error containment
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
import fs from 'fs';
import path from 'path';
import net from 'net';
import { execSync } from 'child_process';

// 🛡️ DOKTRIN BULLETPROOF ANTI-CRASH: Process-level error traps
process.on('uncaughtException', (err) => {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'rea_decompile',
    error: 'UNCAUGHT_EXCEPTION',
    message: err ? err.message : 'Unknown exception caught gracefully'
  }, null, 2));
  process.exit(0);
});

process.on('unhandledRejection', (reason) => {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'rea_decompile',
    error: 'UNHANDLED_REJECTION',
    message: String(reason || 'Unhandled promise rejection caught gracefully')
  }, null, 2));
  process.exit(0);
});

function parseArgs() {
  try {
    const args = process.argv.slice(2);
    let params = {};
    const pIdx = args.indexOf('--params');
    if (pIdx !== -1 && args[pIdx + 1]) {
      try { params = JSON.parse(args[pIdx + 1]); } catch (_) {}
    } else if (args[0] && args[0].startsWith('{')) {
      try { params = JSON.parse(args[0]); } catch (_) {}
    } else {
      for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg.startsWith('--')) {
          const key = arg.slice(2);
          const next = args[i + 1];
          if (next && !next.startsWith('--')) {
            params[key] = next;
            i++;
          } else {
            params[key] = true;
          }
        }
      }
    }
    return params;
  } catch (_) {
    return {};
  }
}

function runCommandSafe(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'], timeout: 15000 }).trim();
  } catch (err) {
    return err.stdout ? err.stdout.trim() : '';
  }
}

// 🔌 HYBRID SOVEREIGN SOCKET BRIDGE DETECTOR (Ghidra, Hopper, IDA, Jadx)
async function tryQuerySocketBridge(targetPath, symbol, address, timeoutMs = 250) {
  return new Promise((resolve) => {
    const candidates = [];
    if (process.env.REA_SOCKET && fs.existsSync(process.env.REA_SOCKET)) {
      candidates.push({ path: process.env.REA_SOCKET });
    }
    for (const s of ['/tmp/rea-ghidra.sock', '/tmp/rea-hopper.sock', '/tmp/rea-ida.sock']) {
      if (fs.existsSync(s)) candidates.push({ path: s });
    }

    if (candidates.length === 0) {
      return resolve(null); // No socket candidates found, immediate fallback
    }

    const targetSocket = candidates[0];
    let settled = false;

    const timer = setTimeout(() => {
      if (!settled) {
        settled = true;
        try { client.destroy(); } catch (_) {}
        resolve(null);
      }
    }, timeoutMs);

    const client = net.createConnection(targetSocket, () => {
      const payload = JSON.stringify({
        action: 'decompile',
        target_path: targetPath,
        symbol: symbol || undefined,
        address: address || undefined
      }) + '\n';
      client.write(payload);
    });

    let incomingData = '';
    client.on('data', (chunk) => {
      incomingData += chunk.toString('utf8');
      if (incomingData.includes('\n')) {
        if (!settled) {
          settled = true;
          clearTimeout(timer);
          client.end();
          try {
            const parsed = JSON.parse(incomingData.trim());
            resolve(parsed);
          } catch (_) {
            resolve(null);
          }
        }
      }
    });

    client.on('error', () => {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        resolve(null);
      }
    });
  });
}

async function main() {
  let params = {};
  try {
    params = parseArgs();
  } catch (err) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'rea_decompile',
      error: 'PARAM_PARSE_FAILED',
      message: 'Failed to parse JSON parameters: ' + err.message
    }, null, 2));
    process.exit(0);
  }

  const target = params.target_path || params.path || params.file || params.binary_path || params.target;

  if (!target) {
    console.log(JSON.stringify({
      status: 'help',
      tool: 'rea_decompile',
      command: 'decompile',
      cluster: 'native',
      description: 'Read one part of an app as code (Hybrid Socket Bridge + POSIX Fallback)',
      usage: {
        target_path: '<path/to/target>',
        symbol: '<optional_symbol>',
        address: '<optional_hex_address>'
      },
      message: "Parameter 'target_path' is required to analyze a binary."
    }, null, 2));
    process.exit(0);
  }

  let resolved = '';
  try {
    resolved = path.resolve(target);
  } catch (e) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'rea_decompile',
      target: String(target),
      message: 'Invalid file path: ' + e.message
    }, null, 2));
    process.exit(0);
  }

  if (!fs.existsSync(resolved)) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'rea_decompile',
      target: target,
      message: `File '${target}' not found on host filesystem.`
    }, null, 2));
    process.exit(0);
  }

  let stats = null;
  try {
    stats = fs.statSync(resolved);
  } catch (err) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'rea_decompile',
      target: resolved,
      message: 'Failed to access file metadata: ' + err.message
    }, null, 2));
    process.exit(0);
  }

  let fileType = '';
  try {
    fileType = runCommandSafe(`file -b "${resolved}"`);
  } catch (_) {
    fileType = 'unknown/binary';
  }

  const symbol = params.symbol || '';
  const addr = params.address || '';

  const result = {
    status: 'success',
    tool: 'rea_decompile',
    command: 'decompile',
    cluster: 'native',
    target: resolved,
    size_bytes: stats.size,
    file_type: fileType,
    analysis: {}
  };

  try {
    // 1. Try Hybrid Socket Bridge Query (Ghidra / Hopper / IDA daemon)
    const bridgeResult = await tryQuerySocketBridge(resolved, symbol, addr);

    if (bridgeResult && (bridgeResult.pseudocode || bridgeResult.disassembly)) {
      result.analysis.provider = bridgeResult.provider || 'socket_bridge';
      result.analysis.pseudocode = bridgeResult.pseudocode || null;
      if (bridgeResult.disassembly) {
        result.analysis.disassembly = bridgeResult.disassembly;
      }
      result.message = `Decompilation analysis completed via ${result.analysis.provider}.`;
      console.log(JSON.stringify(result, null, 2));
      process.exit(0);
    }

    // 2. Sovereign Graceful Fallback: POSIX Disassembly
    result.analysis.provider = 'posix_objdump_fallback';

    if (fileType.includes('ELF') || fileType.includes('Mach-O') || fileType.includes('PE32')) {
      const disasmCmd = symbol 
        ? `objdump -d -M intel --no-show-raw-insn "${resolved}" 2>/dev/null | grep -A 50 "<.*\ ${symbol}\ .*>:" | head -n 60`
        : `objdump -d -M intel --no-show-raw-insn "${resolved}" 2>/dev/null | head -n 60`;
      
      const disasmOut = runCommandSafe(disasmCmd);
      if (disasmOut) {
        result.analysis.disassembly = disasmOut.split('\n').filter(Boolean);
      } else {
        // Fallback to nm symbols
        const nmCmd = symbol ? `nm -C "${resolved}" 2>/dev/null | grep -i "${symbol}" | head -n 40` : `nm -C "${resolved}" 2>/dev/null | head -n 40`;
        result.analysis.symbols = runCommandSafe(nmCmd).split('\n').filter(Boolean);
      }
    } else {
      result.analysis.strings_sample = runCommandSafe(`strings -n 6 "${resolved}" 2>/dev/null | head -n 30`).split('\n').filter(Boolean);
    }
    result.message = `Decompilation analysis completed via ${result.analysis.provider}.`;
  } catch (err) {
    result.analysis.warning = 'Partial analysis operation: ' + err.message;
  }

  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}

main().catch(err => {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'rea_decompile',
    error: 'MAIN_CRASH_CONTAINED',
    message: err ? err.message : 'Unknown error contained gracefully'
  }, null, 2));
  process.exit(0);
});
