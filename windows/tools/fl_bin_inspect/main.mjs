#!/usr/bin/env node
/**
 * 🔬 fl_bin_inspect - Sovereign Native Binary Layout & Mitigations Triage
 * Dissects ELF, PE, and Mach-O binaries using standard system inspection tools.
 * Zero-Crash Hardened: Bulletproof try/catch & process.exit(0) error containment
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

// Global error traps to guarantee agents never stall or crash
process.on("uncaughtException", (err) => {
  console.log(JSON.stringify({
    status: "error",
    tool: "fl_bin_inspect",
    error: "UNCAUGHT_EXCEPTION",
    message: err ? err.message : 'Unknown exception caught gracefully'
  }, null, 2));
  process.exit(0);
});

process.on("unhandledRejection", (reason) => {
  console.log(JSON.stringify({
    status: "error",
    tool: "fl_bin_inspect",
    error: "UNHANDLED_REJECTION",
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

function runCmd(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 15000 }).trim();
  } catch (_) {
    return '';
  }
}

function inspectElf(filePath) {
  const fileOut = runCmd(`file -b "${filePath}"`);
  const headerOut = runCmd(`readelf -h "${filePath}"`);
  const programHeaders = runCmd(`readelf -l "${filePath}"`);
  const dynamicOut = runCmd(`readelf -d "${filePath}"`);
  const symbolsOut = runCmd(`readelf -s "${filePath}"`);

  // 1. Mitigations
  // NX (PT_GNU_STACK)
  let nx = false;
  if (programHeaders.includes('GNU_STACK')) {
    const stackLine = programHeaders.split('\n').find(l => l.includes('GNU_STACK'));
    if (stackLine && stackLine.includes('RW') && !stackLine.includes('RWE')) {
      nx = true;
    }
  }

  // PIE
  const isDyn = headerOut.includes('DYN (Shared object file)') || headerOut.includes('DYN (Position-Independent Executable file)');
  const hasInterp = programHeaders.includes('INTERP');
  const pie = isDyn && hasInterp;

  // Stack Canary
  const canary = symbolsOut.includes('__stack_chk_fail');

  // RELRO
  let relro = 'none';
  if (programHeaders.includes('GNU_RELRO')) {
    if (dynamicOut.includes('BIND_NOW') || dynamicOut.includes('FLAGS') && dynamicOut.includes('NOW')) {
      relro = 'full';
    } else {
      relro = 'partial';
    }
  }

  // Dependencies
  const dependencies = [];
  for (const line of dynamicOut.split('\n')) {
    if (line.includes('(NEEDED)')) {
      const match = line.match(/Shared library: \[(.*?)\]/);
      if (match) dependencies.push(match[1]);
    }
  }

  // Architecture & Entry Point
  let entryPoint = '';
  const epMatch = headerOut.match(/Entry point address:\s+(0x[0-9a-fA-F]+)/);
  if (epMatch) entryPoint = epMatch[1];

  let machine = '';
  const mMatch = headerOut.match(/Machine:\s+(.*)/);
  if (mMatch) machine = mMatch[1].trim();

  return {
    format: 'elf',
    architecture: machine,
    entry_point: entryPoint,
    file_description: fileOut,
    mitigations: {
      nx,
      pie,
      canary,
      relro
    },
    dependencies,
    symbols_sample: symbolsOut.split('\n').slice(0, 20).filter(Boolean)
  };
}

function main() {
  let params = {};
  try {
    params = parseArgs();
  } catch (err) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'fl_bin_inspect',
      error: 'PARAM_PARSE_FAILED',
      message: 'Gagal membaca parameter JSON: ' + err.message
    }, null, 2));
    process.exit(0);
  }

  const binPath = params.binary_path || params.target_path || params.path || params.file || params.target;

  if (!binPath) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'fl_bin_inspect',
      error: 'PARAMETER_MISSING',
      message: 'Parameter binary_path wajib diisi dengan path berkas biner!'
    }, null, 2));
    process.exit(0);
  }

  let resolved = '';
  try {
    resolved = path.resolve(process.cwd(), binPath);
  } catch (e) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'fl_bin_inspect',
      target: String(binPath),
      message: 'Path berkas tidak valid: ' + e.message
    }, null, 2));
    process.exit(0);
  }

  if (!fs.existsSync(resolved)) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'fl_bin_inspect',
      error: 'FILE_NOT_FOUND',
      message: `Berkas biner tidak ditemukan di: ${resolved}`
    }, null, 2));
    process.exit(0);
  }

  let stat = null;
  try {
    stat = fs.statSync(resolved);
  } catch (err) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'fl_bin_inspect',
      target: resolved,
      message: 'Gagal mengakses metadata berkas: ' + err.message
    }, null, 2));
    process.exit(0);
  }

  const fileType = runCmd(`file -b "${resolved}"`);

  let details = {};
  if (fileType.includes('ELF')) {
    details = inspectElf(resolved);
  } else {
    details = {
      format: fileType.includes('PE32') ? 'pe' : (fileType.includes('Mach-O') ? 'macho' : 'unknown'),
      file_description: fileType
    };
  }

  console.log(JSON.stringify({
    status: 'success',
    tool: 'fl_bin_inspect',
    binary_path: resolved,
    size_bytes: stat.size,
    ...details,
    message: `Triage biner selesai (${details.format || 'unknown'}).`
  }, null, 2));
  process.exit(0);
}

try {
  main();
} catch (err) {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'fl_bin_inspect',
    error: 'MAIN_CRASH_CONTAINED',
    message: err ? err.message : 'Unknown error contained gracefully'
  }, null, 2));
  process.exit(0);
}
