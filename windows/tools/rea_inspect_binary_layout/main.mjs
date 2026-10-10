#!/usr/bin/env node
/**
 * 🔬 rea_inspect_binary_layout - Sovereign Reverse Engineering Nano-Plug
 * Command: inspect-binary-layout (native)
 * Description: Inspect binary file/linked layout without executing the selected object
 * Zero-Crash Hardened: Bulletproof try/catch & process.exit(0) error containment
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

// Global error traps to guarantee agents never stall or crash
process.on('uncaughtException', (err) => {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'rea_inspect_binary_layout',
    error: 'UNCAUGHT_EXCEPTION',
    message: err ? err.message : 'Unknown exception caught gracefully'
  }, null, 2));
  process.exit(0);
});

process.on('unhandledRejection', (reason) => {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'rea_inspect_binary_layout',
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

async function main() {
  let params = {};
  try {
    params = parseArgs();
  } catch (err) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'rea_inspect_binary_layout',
      error: 'PARAM_PARSE_FAILED',
      message: 'Gagal membaca parameter JSON: ' + err.message
    }, null, 2));
    process.exit(0);
  }

  const target = params.target_path || params.path || params.file || params.binary_path || params.target;

  if (!target) {
    console.log(JSON.stringify({
      status: 'help',
      tool: 'rea_inspect_binary_layout',
      command: 'inspect-binary-layout',
      cluster: 'native',
      description: "Inspect binary file/linked layout without executing the selected object",
      usage: {
        target_path: '<path/to/target>',
        symbol: '<optional_symbol>',
        address: '<optional_hex_address>'
      },
      message: 'Parameter target_path wajib diisi untuk menganalisis berkas.'
    }, null, 2));
    process.exit(0);
  }

  let resolved = '';
  try {
    resolved = path.resolve(target);
  } catch (e) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'rea_inspect_binary_layout',
      target: String(target),
      message: 'Path berkas tidak valid: ' + e.message
    }, null, 2));
    process.exit(0);
  }

  if (!fs.existsSync(resolved)) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'rea_inspect_binary_layout',
      target: target,
      message: `Berkas '${target}' tidak ditemukan di sistem host.`
    }, null, 2));
    process.exit(0);
  }

  let stats = null;
  try {
    stats = fs.statSync(resolved);
  } catch (err) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'rea_inspect_binary_layout',
      target: resolved,
      message: 'Gagal mengakses metadata berkas: ' + err.message
    }, null, 2));
    process.exit(0);
  }

  let fileType = '';
  try {
    fileType = runCommandSafe(`file -b "${resolved}"`);
  } catch (_) {
    fileType = 'unknown/binary';
  }

  const result = {
    status: 'success',
    tool: 'rea_inspect_binary_layout',
    command: 'inspect-binary-layout',
    cluster: 'native',
    target: resolved,
    size_bytes: stats.size,
    file_type: fileType,
    analysis: {}
  };

  const cluster = 'native';
  const symbol = params.symbol || '';
  const addr = params.address || '';

  try {
    if (cluster === 'native' || cluster === 'macho' || cluster === 'managed') {
      if (fileType.includes('ELF') || fileType.includes('Mach-O') || fileType.includes('PE32')) {
        if ('inspect-binary-layout'.includes('decompile') || 'inspect-binary-layout'.includes('instructions')) {
          const disasmCmd = symbol 
            ? `objdump -d -M intel --no-show-raw-insn "${resolved}" 2>/dev/null | grep -A 50 "<.*\${symbol}\.*>:" | head -n 60`
            : `objdump -d -M intel --no-show-raw-insn "${resolved}" 2>/dev/null | head -n 60`;
          result.analysis.disassembly = runCommandSafe(disasmCmd).split('\n').filter(Boolean);
        } else if ('inspect-binary-layout'.includes('xrefs') || 'inspect-binary-layout'.includes('search') || 'inspect-binary-layout'.includes('function')) {
          const nmCmd = symbol ? `nm -C "${resolved}" 2>/dev/null | grep -i "${symbol}" | head -n 40` : `nm -C "${resolved}" 2>/dev/null | head -n 40`;
          result.analysis.symbols = runCommandSafe(nmCmd).split('\n').filter(Boolean);
        } else {
          const headerCmd = `readelf -h "${resolved}" 2>/dev/null | head -n 30`;
          result.analysis.headers = runCommandSafe(headerCmd).split('\n').filter(Boolean);
        }
      } else {
        result.analysis.strings_sample = runCommandSafe(`strings -n 6 "${resolved}" 2>/dev/null | head -n 30`).split('\n').filter(Boolean);
      }
    } else if (cluster === 'android') {
      result.analysis.zip_contents = runCommandSafe(`unzip -l "${resolved}" 2>/dev/null | head -n 40`).split('\n').filter(Boolean);
    } else if (cluster === 'web' || cluster === 'electron') {
      if (stats.size < 5 * 1024 * 1024) {
        try {
          const content = fs.readFileSync(resolved, 'utf8');
          result.analysis.has_sourcemap_ref = content.includes('sourceMappingURL=');
          result.analysis.lines_count = content.split('\n').length;
          result.analysis.sample_preview = content.slice(0, 300);
        } catch (_) {}
      }
    } else if (cluster === 'evm') {
      try {
        const raw = fs.readFileSync(resolved, 'utf8').trim().replace(/^0x/, '');
        result.analysis.bytecode_length = raw.length;
        result.analysis.initial_bytes = raw.slice(0, 64);
      } catch (_) {}
    } else {
      result.analysis.summary = `Analisis ${cluster} untuk '${path.basename(resolved)}' berhasil dieksekusi.`;
    }
  } catch (err) {
    result.analysis.warning = 'Operasi analisis parsial: ' + err.message;
  }

  result.message = `Analisis inspect-binary-layout selesai dengan sukses.`;
  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}

main().catch(err => {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'rea_inspect_binary_layout',
    error: 'MAIN_CRASH_CONTAINED',
    message: err ? err.message : 'Unknown error contained gracefully'
  }, null, 2));
  process.exit(0);
});
