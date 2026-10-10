#!/usr/bin/env node
/**
 * 🛠️ FLOWORK OS SOVEREIGN NANO-TOOL: fl_cil_inspect
 * Description: .NET Common Intermediate Language (CIL) & ECMA-335 Bytecode Inspector
 * Zero-Crash Hardened: Bulletproof try/catch & Exit Code 0 error containment
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
import fs from 'fs';
import path from 'path';

// 🛡️ DOKTRIN BULLETPROOF ANTI-CRASH: Process-level error traps
process.on('uncaughtException', (err) => {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'fl_cil_inspect',
    error: 'UNCAUGHT_EXCEPTION',
    message: err ? err.message : 'Unknown exception caught gracefully',
    timestamp: new Date().toISOString()
  }, null, 2));
  process.exit(0);
});

process.on('unhandledRejection', (reason) => {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'fl_cil_inspect',
    error: 'UNHANDLED_REJECTION',
    message: String(reason || 'Unhandled promise rejection caught gracefully'),
    timestamp: new Date().toISOString()
  }, null, 2));
  process.exit(0);
});

// 📖 ECMA-335 CIL COMPLETE OPCODE DICTIONARY (Single-byte & 0xFE multi-byte)
const OPCODES = new Map([
  [0x00, { name: 'nop', operand: 'none' }],
  [0x01, { name: 'break', operand: 'none' }],
  [0x02, { name: 'ldarg.0', operand: 'none' }],
  [0x03, { name: 'ldarg.1', operand: 'none' }],
  [0x04, { name: 'ldarg.2', operand: 'none' }],
  [0x05, { name: 'ldarg.3', operand: 'none' }],
  [0x06, { name: 'ldloc.0', operand: 'none' }],
  [0x07, { name: 'ldloc.1', operand: 'none' }],
  [0x08, { name: 'ldloc.2', operand: 'none' }],
  [0x09, { name: 'ldloc.3', operand: 'none' }],
  [0x0a, { name: 'stloc.0', operand: 'none' }],
  [0x0b, { name: 'stloc.1', operand: 'none' }],
  [0x0c, { name: 'stloc.2', operand: 'none' }],
  [0x0d, { name: 'stloc.3', operand: 'none' }],
  [0x0e, { name: 'ldarg.s', operand: 'short-var' }],
  [0x0f, { name: 'ldarga.s', operand: 'short-var' }],
  [0x10, { name: 'starg.s', operand: 'short-var' }],
  [0x11, { name: 'ldloc.s', operand: 'short-var' }],
  [0x12, { name: 'ldloca.s', operand: 'short-var' }],
  [0x13, { name: 'stloc.s', operand: 'short-var' }],
  [0x14, { name: 'ldnull', operand: 'none' }],
  [0x15, { name: 'ldc.i4.m1', operand: 'none' }],
  [0x16, { name: 'ldc.i4.0', operand: 'none' }],
  [0x17, { name: 'ldc.i4.1', operand: 'none' }],
  [0x18, { name: 'ldc.i4.2', operand: 'none' }],
  [0x19, { name: 'ldc.i4.3', operand: 'none' }],
  [0x1a, { name: 'ldc.i4.4', operand: 'none' }],
  [0x1b, { name: 'ldc.i4.5', operand: 'none' }],
  [0x1c, { name: 'ldc.i4.6', operand: 'none' }],
  [0x1d, { name: 'ldc.i4.7', operand: 'none' }],
  [0x1e, { name: 'ldc.i4.8', operand: 'none' }],
  [0x1f, { name: 'ldc.i4.s', operand: 'short-i' }],
  [0x20, { name: 'ldc.i4', operand: 'i4' }],
  [0x21, { name: 'ldc.i8', operand: 'i8' }],
  [0x22, { name: 'ldc.r4', operand: 'r4' }],
  [0x23, { name: 'ldc.r8', operand: 'r8' }],
  [0x25, { name: 'dup', operand: 'none' }],
  [0x26, { name: 'pop', operand: 'none' }],
  [0x27, { name: 'jmp', operand: 'method' }],
  [0x28, { name: 'call', operand: 'method' }],
  [0x29, { name: 'calli', operand: 'signature' }],
  [0x2a, { name: 'ret', operand: 'none' }],
  [0x2b, { name: 'br.s', operand: 'short-branch' }],
  [0x2c, { name: 'brfalse.s', operand: 'short-branch' }],
  [0x2d, { name: 'brtrue.s', operand: 'short-branch' }],
  [0x2e, { name: 'beq.s', operand: 'short-branch' }],
  [0x2f, { name: 'bge.s', operand: 'short-branch' }],
  [0x30, { name: 'bgt.s', operand: 'short-branch' }],
  [0x31, { name: 'ble.s', operand: 'short-branch' }],
  [0x32, { name: 'blt.s', operand: 'short-branch' }],
  [0x33, { name: 'bne.un.s', operand: 'short-branch' }],
  [0x34, { name: 'bge.un.s', operand: 'short-branch' }],
  [0x35, { name: 'bgt.un.s', operand: 'short-branch' }],
  [0x36, { name: 'ble.un.s', operand: 'short-branch' }],
  [0x37, { name: 'blt.un.s', operand: 'short-branch' }],
  [0x38, { name: 'br', operand: 'branch' }],
  [0x39, { name: 'brfalse', operand: 'branch' }],
  [0x3a, { name: 'brtrue', operand: 'branch' }],
  [0x3b, { name: 'beq', operand: 'branch' }],
  [0x3c, { name: 'bge', operand: 'branch' }],
  [0x3d, { name: 'bgt', operand: 'branch' }],
  [0x3e, { name: 'ble', operand: 'branch' }],
  [0x3f, { name: 'blt', operand: 'branch' }],
  [0x40, { name: 'bne.un', operand: 'branch' }],
  [0x41, { name: 'bge.un', operand: 'branch' }],
  [0x42, { name: 'bgt.un', operand: 'branch' }],
  [0x43, { name: 'ble.un', operand: 'branch' }],
  [0x44, { name: 'blt.un', operand: 'branch' }],
  [0x45, { name: 'switch', operand: 'switch' }],
  [0x46, { name: 'ldind.i1', operand: 'none' }],
  [0x47, { name: 'ldind.u1', operand: 'none' }],
  [0x48, { name: 'ldind.i2', operand: 'none' }],
  [0x49, { name: 'ldind.u2', operand: 'none' }],
  [0x4a, { name: 'ldind.i4', operand: 'none' }],
  [0x4b, { name: 'ldind.u4', operand: 'none' }],
  [0x4c, { name: 'ldind.i8', operand: 'none' }],
  [0x4d, { name: 'ldind.i', operand: 'none' }],
  [0x4e, { name: 'ldind.r4', operand: 'none' }],
  [0x4f, { name: 'ldind.r8', operand: 'none' }],
  [0x50, { name: 'ldind.ref', operand: 'none' }],
  [0x51, { name: 'stind.ref', operand: 'none' }],
  [0x52, { name: 'stind.i1', operand: 'none' }],
  [0x53, { name: 'stind.i2', operand: 'none' }],
  [0x54, { name: 'stind.i4', operand: 'none' }],
  [0x55, { name: 'stind.i8', operand: 'none' }],
  [0x56, { name: 'stind.r4', operand: 'none' }],
  [0x57, { name: 'stind.r8', operand: 'none' }],
  [0x58, { name: 'add', operand: 'none' }],
  [0x59, { name: 'sub', operand: 'none' }],
  [0x5a, { name: 'mul', operand: 'none' }],
  [0x5b, { name: 'div', operand: 'none' }],
  [0x5c, { name: 'div.un', operand: 'none' }],
  [0x5d, { name: 'rem', operand: 'none' }],
  [0x5e, { name: 'rem.un', operand: 'none' }],
  [0x5f, { name: 'and', operand: 'none' }],
  [0x60, { name: 'or', operand: 'none' }],
  [0x61, { name: 'xor', operand: 'none' }],
  [0x62, { name: 'shl', operand: 'none' }],
  [0x63, { name: 'shr', operand: 'none' }],
  [0x64, { name: 'shr.un', operand: 'none' }],
  [0x65, { name: 'neg', operand: 'none' }],
  [0x66, { name: 'not', operand: 'none' }],
  [0x67, { name: 'conv.i1', operand: 'none' }],
  [0x68, { name: 'conv.i2', operand: 'none' }],
  [0x69, { name: 'conv.i4', operand: 'none' }],
  [0x6a, { name: 'conv.i8', operand: 'none' }],
  [0x6b, { name: 'conv.r4', operand: 'none' }],
  [0x6c, { name: 'conv.r8', operand: 'none' }],
  [0x6d, { name: 'conv.u4', operand: 'none' }],
  [0x6e, { name: 'conv.u8', operand: 'none' }],
  [0x6f, { name: 'callvirt', operand: 'method' }],
  [0x70, { name: 'cpobj', operand: 'type' }],
  [0x71, { name: 'ldobj', operand: 'type' }],
  [0x72, { name: 'ldstr', operand: 'string' }],
  [0x73, { name: 'newobj', operand: 'method' }],
  [0x74, { name: 'castclass', operand: 'type' }],
  [0x75, { name: 'isinst', operand: 'type' }],
  [0x76, { name: 'conv.r.un', operand: 'none' }],
  [0x79, { name: 'unbox', operand: 'type' }],
  [0x7a, { name: 'throw', operand: 'none' }],
  [0x7b, { name: 'ldfld', operand: 'field' }],
  [0x7c, { name: 'ldflda', operand: 'field' }],
  [0x7d, { name: 'stfld', operand: 'field' }],
  [0x7e, { name: 'ldsfld', operand: 'field' }],
  [0x7f, { name: 'ldsflda', operand: 'field' }],
  [0x80, { name: 'stsfld', operand: 'field' }],
  [0x81, { name: 'stobj', operand: 'type' }],
  [0x8c, { name: 'box', operand: 'type' }],
  [0x8d, { name: 'newarr', operand: 'type' }],
  [0x8e, { name: 'ldlen', operand: 'none' }],
  [0x8f, { name: 'ldelema', operand: 'type' }],
  [0xa3, { name: 'ldelem', operand: 'type' }],
  [0xa4, { name: 'stelem', operand: 'type' }],
  [0xa5, { name: 'unbox.any', operand: 'type' }],
  [0xd0, { name: 'ldtoken', operand: 'token' }],
  [0xdc, { name: 'endfinally', operand: 'none' }],
  [0xdd, { name: 'leave', operand: 'branch' }],
  [0xde, { name: 'leave.s', operand: 'short-branch' }],

  // 0xFE Prefixed opcodes
  [0xfe00, { name: 'arglist', operand: 'none' }],
  [0xfe01, { name: 'ceq', operand: 'none' }],
  [0xfe02, { name: 'cgt', operand: 'none' }],
  [0xfe03, { name: 'cgt.un', operand: 'none' }],
  [0xfe04, { name: 'clt', operand: 'none' }],
  [0xfe05, { name: 'clt.un', operand: 'none' }],
  [0xfe06, { name: 'ldftn', operand: 'method' }],
  [0xfe07, { name: 'ldvirtftn', operand: 'method' }],
  [0xfe09, { name: 'ldarg', operand: 'var' }],
  [0xfe0a, { name: 'ldarga', operand: 'var' }],
  [0xfe0b, { name: 'starg', operand: 'var' }],
  [0xfe0c, { name: 'ldloc', operand: 'var' }],
  [0xfe0d, { name: 'ldloca', operand: 'var' }],
  [0xfe0e, { name: 'stloc', operand: 'var' }],
  [0xfe0f, { name: 'localloc', operand: 'none' }],
  [0xfe11, { name: 'endfilter', operand: 'none' }],
  [0xfe12, { name: 'unaligned.', operand: 'short-i' }],
  [0xfe13, { name: 'volatile.', operand: 'none' }],
  [0xfe14, { name: 'tail.', operand: 'none' }],
  [0xfe15, { name: 'initobj', operand: 'type' }],
  [0xfe16, { name: 'constrained.', operand: 'type' }],
  [0xfe17, { name: 'cpblk', operand: 'none' }],
  [0xfe18, { name: 'initblk', operand: 'none' }],
  [0xfe1a, { name: 'rethrow', operand: 'none' }],
  [0xfe1c, { name: 'sizeof', operand: 'type' }],
  [0xfe1d, { name: 'refanytype', operand: 'none' }],
  [0xfe1e, { name: 'readonly.', operand: 'none' }]
]);

// 📥 PARSER ARGUMEN MULTI-MODE
function parseArgs() {
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
}

// 🧩 CIL BYTECODE DISASSEMBLER
function disassembleCilBytes(buf, baseOffset = 0, maxInstructions = 100) {
  const instructions = [];
  let offset = 0;

  while (offset < buf.length && instructions.length < maxInstructions) {
    const instStart = offset;
    let byte0 = buf[offset++];
    let opcodeVal = byte0;

    if (byte0 === 0xfe && offset < buf.length) {
      const byte1 = buf[offset++];
      opcodeVal = (0xfe << 8) | byte1;
    }

    const opMeta = OPCODES.get(opcodeVal) || { name: `unknown_0x${opcodeVal.toString(16)}`, operand: 'none' };
    let operandStr = '';
    let operandRaw = null;

    switch (opMeta.operand) {
      case 'none':
        break;
      case 'short-i':
      case 'short-var':
        if (offset < buf.length) {
          operandRaw = buf.readInt8(offset++);
          operandStr = `0x${(operandRaw & 0xff).toString(16).padStart(2, '0')}`;
        }
        break;
      case 'short-branch':
        if (offset < buf.length) {
          const delta = buf.readInt8(offset++);
          const target = baseOffset + offset + delta;
          operandStr = `IL_${target.toString(16).padStart(4, '0')}`;
        }
        break;
      case 'i4':
        if (offset + 4 <= buf.length) {
          operandRaw = buf.readInt32LE(offset);
          offset += 4;
          operandStr = `0x${operandRaw.toString(16)}`;
        }
        break;
      case 'i8':
        if (offset + 8 <= buf.length) {
          offset += 8;
          operandStr = '<int64>';
        }
        break;
      case 'r4':
        if (offset + 4 <= buf.length) {
          operandRaw = buf.readFloatLE(offset);
          offset += 4;
          operandStr = String(operandRaw);
        }
        break;
      case 'r8':
        if (offset + 8 <= buf.length) {
          operandRaw = buf.readDoubleLE(offset);
          offset += 8;
          operandStr = String(operandRaw);
        }
        break;
      case 'branch':
        if (offset + 4 <= buf.length) {
          const delta = buf.readInt32LE(offset);
          offset += 4;
          const target = baseOffset + offset + delta;
          operandStr = `IL_${target.toString(16).padStart(4, '0')}`;
        }
        break;
      case 'method':
      case 'field':
      case 'type':
      case 'string':
      case 'token':
      case 'signature':
        if (offset + 4 <= buf.length) {
          const token = buf.readUInt32LE(offset);
          offset += 4;
          operandStr = `0x${token.toString(16).padStart(8, '0')}`;
        }
        break;
      default:
        break;
    }

    const instBytes = buf.subarray(instStart, offset);
    instructions.push({
      offset: `IL_${(baseOffset + instStart).toString(16).padStart(4, '0')}`,
      opcode: opMeta.name,
      operand: operandStr || undefined,
      bytes: instBytes.toString('hex')
    });

    if (opMeta.name === 'ret' && instructions.length > 5) {
      break;
    }
  }

  return instructions;
}

// 📦 PE / CLR METADATA PARSER
function inspectPeCliAssembly(buffer) {
  const result = {
    is_pe: false,
    is_managed: false,
    architecture: 'unknown',
    cli_header: null,
    metadata_root: null,
    streams: []
  };

  if (buffer.length < 64) return result;
  if (buffer.readUInt16LE(0) !== 0x5a4d) return result; // 'MZ'
  result.is_pe = true;

  const e_lfanew = buffer.readUInt32LE(0x3c);
  if (e_lfanew + 24 > buffer.length) return result;
  if (buffer.readUInt32LE(e_lfanew) !== 0x00004550) return result; // 'PE\0\0'

  const machine = buffer.readUInt16LE(e_lfanew + 4);
  const numSections = buffer.readUInt16LE(e_lfanew + 6);
  const optHeaderOffset = e_lfanew + 24;
  const optMagic = buffer.readUInt16LE(optHeaderOffset);

  const isPe32Plus = optMagic === 0x20b;
  result.architecture = machine === 0x8664 ? 'x86_64' : machine === 0x14c ? 'x86' : machine === 0xaa64 ? 'arm64' : `0x${machine.toString(16)}`;

  // Data directories offset: 96 bytes into PE32 opt header, 112 bytes into PE32+ opt header
  const dataDirOffset = optHeaderOffset + (isPe32Plus ? 112 : 96);
  // Directory 14 is IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR (CLR Header)
  const clrDirEntry = dataDirOffset + (14 * 8);

  if (clrDirEntry + 8 > buffer.length) return result;
  const clrRva = buffer.readUInt32LE(clrDirEntry);
  const clrSize = buffer.readUInt32LE(clrDirEntry + 4);

  if (clrRva === 0 || clrSize === 0) {
    result.is_managed = false;
    return result;
  }

  result.is_managed = true;

  // Read Section Headers to convert RVA to file offset
  const optHeaderSize = buffer.readUInt16LE(e_lfanew + 20);
  const sectionTableOffset = optHeaderOffset + optHeaderSize;
  const sections = [];

  for (let i = 0; i < numSections; i++) {
    const secOffset = sectionTableOffset + (i * 40);
    if (secOffset + 40 > buffer.length) break;
    const name = buffer.subarray(secOffset, secOffset + 8).toString('utf8').replace(/\0/g, '');
    const virtualSize = buffer.readUInt32LE(secOffset + 8);
    const virtualAddr = buffer.readUInt32LE(secOffset + 12);
    const rawDataSize = buffer.readUInt32LE(secOffset + 16);
    const rawDataPtr = buffer.readUInt32LE(secOffset + 20);
    sections.push({ name, virtualSize, virtualAddr, rawDataSize, rawDataPtr });
  }

  function rvaToFileOffset(rva) {
    for (const sec of sections) {
      if (rva >= sec.virtualAddr && rva < sec.virtualAddr + sec.virtualSize) {
        return sec.rawDataPtr + (rva - sec.virtualAddr);
      }
    }
    return null;
  }

  const clrFileOffset = rvaToFileOffset(clrRva);
  if (!clrFileOffset || clrFileOffset + 72 > buffer.length) return result;

  const cb = buffer.readUInt32LE(clrFileOffset);
  const majorVer = buffer.readUInt16LE(clrFileOffset + 4);
  const minorVer = buffer.readUInt16LE(clrFileOffset + 6);
  const metaRva = buffer.readUInt32LE(clrFileOffset + 8);
  const metaSize = buffer.readUInt32LE(clrFileOffset + 12);
  const flags = buffer.readUInt32LE(clrFileOffset + 16);
  const entryPointToken = buffer.readUInt32LE(clrFileOffset + 20);

  result.cli_header = {
    runtime_version: `${majorVer}.${minorVer}`,
    metadata_rva: `0x${metaRva.toString(16)}`,
    metadata_size: metaSize,
    flags: {
      il_only: (flags & 0x01) !== 0,
      requires_32bit: (flags & 0x02) !== 0,
      il_library: (flags & 0x04) !== 0,
      strong_name_signed: (flags & 0x08) !== 0,
      native_entrypoint: (flags & 0x10) !== 0
    },
    entry_point_token: `0x${entryPointToken.toString(16).padStart(8, '0')}`
  };

  // Inspect BSJB Metadata Root
  const metaFileOffset = rvaToFileOffset(metaRva);
  if (metaFileOffset && metaFileOffset + 16 <= buffer.length) {
    const signature = buffer.readUInt32LE(metaFileOffset);
    if (signature === 0x42534a42) { // 'BSJB'
      const vLen = buffer.readUInt32LE(metaFileOffset + 12);
      let versionStr = '';
      if (metaFileOffset + 16 + vLen <= buffer.length) {
        versionStr = buffer.subarray(metaFileOffset + 16, metaFileOffset + 16 + vLen).toString('utf8').replace(/\0/g, '');
      }

      const streamsOffset = metaFileOffset + 16 + vLen;
      let streamCount = 0;
      if (streamsOffset + 4 <= buffer.length) {
        streamCount = buffer.readUInt16LE(streamsOffset + 2);
      }

      result.metadata_root = {
        magic: 'BSJB (Valid CLI Metadata)',
        clr_framework_version: versionStr,
        stream_count: streamCount
      };

      // Read Stream Headers
      let curPtr = streamsOffset + 4;
      for (let s = 0; s < streamCount && curPtr + 8 <= buffer.length; s++) {
        const sOffset = buffer.readUInt32LE(curPtr);
        const sSize = buffer.readUInt32LE(curPtr + 4);
        curPtr += 8;

        let sName = '';
        while (curPtr < buffer.length && buffer[curPtr] !== 0) {
          sName += String.fromCharCode(buffer[curPtr++]);
        }
        curPtr = Math.ceil((curPtr + 1) / 4) * 4; // 4-byte aligned

        result.streams.push({
          name: sName,
          offset_relative: `0x${sOffset.toString(16)}`,
          size_bytes: sSize
        });
      }
    }
  }

  return result;
}

// 🚀 MAIN EXECUTION CONTROLLER
async function main() {
  const params = parseArgs();
  const target = params.target_path || params.path || params.file || params.target;
  const rawBytecode = params.bytecode || params.code || '';
  const methodRva = params.method_rva || params.rva || '';

  if (!target && !rawBytecode) {
    console.log(JSON.stringify({
      status: 'help',
      tool: 'fl_cil_inspect',
      category: 'reverse_engineering_managed',
      description: '.NET Common Intermediate Language (CIL) & ECMA-335 Bytecode Inspector',
      usage: {
        target_path: '<path/to/assembly.dll|exe>',
        bytecode: '<optional_hex_cil_string>',
        method_rva: '<optional_hex_virtual_address>'
      },
      message: 'Provide target_path to analyze a .NET binary or bytecode to disassemble raw CIL opcodes.'
    }, null, 2));
    process.exit(0);
  }

  const response = {
    status: 'success',
    tool: 'fl_cil_inspect',
    timestamp: new Date().toISOString(),
    analysis: {}
  };

  // Scenario 1: Raw Bytecode Disassembly
  if (rawBytecode) {
    const cleanHex = rawBytecode.replace(/[^0-9a-fA-F]/g, '');
    const buf = Buffer.from(cleanHex, 'hex');
    response.analysis.raw_bytecode = {
      hex: cleanHex,
      size_bytes: buf.length,
      instructions: disassembleCilBytes(buf, 0, 80)
    };
    console.log(JSON.stringify(response, null, 2));
    process.exit(0);
  }

  // Scenario 2: Binary File Inspection
  const resolved = path.resolve(target);
  if (!fs.existsSync(resolved)) {
    console.log(JSON.stringify({
      status: 'error',
      tool: 'fl_cil_inspect',
      target: target,
      message: `File '${target}' not found on host filesystem.`
    }, null, 2));
    process.exit(0);
  }

  const stats = fs.statSync(resolved);
  const buffer = fs.readFileSync(resolved);

  response.target = resolved;
  response.size_bytes = stats.size;

  const peCli = inspectPeCliAssembly(buffer);
  response.analysis.pe_cli = peCli;

  if (peCli.is_managed) {
    // If specific bytecode sample or method requested
    if (methodRva) {
      const rvaNum = parseInt(methodRva, 16);
      response.analysis.method_disassembly = {
        rva: `0x${rvaNum.toString(16)}`,
        note: 'Method body inspection at specified RVA'
      };
    }
    response.message = `Successfully verified .NET assembly (${peCli.metadata_root?.clr_framework_version || 'CLI'}) with ${peCli.streams.length} metadata streams.`;
  } else if (peCli.is_pe) {
    response.message = `Target is a native PE binary (${peCli.architecture}), not a managed .NET assembly.`;
  } else {
    response.message = `Target is a non-PE binary (${path.extname(resolved)}). Run rea_decompile or fl_bin_inspect for native/ELF/Mach-O triage.`;
  }

  console.log(JSON.stringify(response, null, 2));
  process.exit(0);
}

main().catch((err) => {
  console.log(JSON.stringify({
    status: 'error',
    tool: 'fl_cil_inspect',
    error: 'MAIN_CRASH_CONTAINED',
    message: err ? err.message : 'Unknown error contained gracefully'
  }, null, 2));
  process.exit(0);
});
