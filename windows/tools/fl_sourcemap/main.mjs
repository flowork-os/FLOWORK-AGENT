#!/usr/bin/env node
/**
 * 🗺️ fl_sourcemap - Sovereign Offline Source Map Resolver
 * Pure Node.js implementation of Source Map v3 format & Base64 VLQ decoder.
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
process.on("uncaughtException", (err) => {
  console.log(JSON.stringify({ status: "error", error: "UNCAUGHT_EXCEPTION", message: err.message }, null, 2));
  process.exit(0);
});
process.on("unhandledRejection", (reason) => {
  console.log(JSON.stringify({ status: "error", error: "UNHANDLED_REJECTION", message: String(reason) }, null, 2));
  process.exit(0);
});
import fs from 'fs';
import path from 'path';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try { params = JSON.parse(args[pIdx + 1]); } catch (_) {}
  } else if (args[0] && args[0].startsWith('{')) {
    try { params = JSON.parse(args[0]); } catch (_) {}
  }
  return params;
}

const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
const B64_MAP = new Map(B64.split('').map((c, i) => [c, i]));

function decodeVLQ(str, index) {
  let result = 0;
  let shift = 0;
  let continuation = true;

  while (continuation && index.pos < str.length) {
    const char = str[index.pos++];
    const val = B64_MAP.get(char);
    if (val === undefined) break;

    continuation = (val & 32) !== 0;
    const digit = val & 31;
    result += digit << shift;
    shift += 5;
  }

  const isNeg = (result & 1) === 1;
  const num = result >> 1;
  return isNeg ? -num : num;
}

function parseMappings(mappingsStr) {
  const lines = mappingsStr.split(';');
  const decoded = [];

  let genCol = 0;
  let srcIdx = 0;
  let origLine = 0;
  let origCol = 0;
  let nameIdx = 0;

  for (let l = 0; l < lines.length; l++) {
    const lineStr = lines[l];
    genCol = 0;
    const lineSegments = [];

    if (lineStr.length > 0) {
      const segs = lineStr.split(',');
      for (const seg of segs) {
        if (!seg) continue;
        const index = { pos: 0 };
        genCol += decodeVLQ(seg, index);
        const segment = [genCol];

        if (index.pos < seg.length) {
          srcIdx += decodeVLQ(seg, index);
          origLine += decodeVLQ(seg, index);
          origCol += decodeVLQ(seg, index);
          segment.push(srcIdx, origLine, origCol);

          if (index.pos < seg.length) {
            nameIdx += decodeVLQ(seg, index);
            segment.push(nameIdx);
          }
        }
        lineSegments.push(segment);
      }
    }
    decoded.push(lineSegments);
  }
  return decoded;
}

function main() {
  const params = parseArgs();
  const mapPath = params.map_path;
  const action = (params.action || 'inspect').toLowerCase();

  if (!mapPath) {
    console.log(JSON.stringify({
      status: 'error',
      error: 'PARAMETER_MISSING',
      message: 'Parameter map_path wajib diisi dengan path ke berkas .map!'
    }, null, 2));
    process.exit(0);
  }

  const resolved = path.resolve(process.cwd(), mapPath);
  if (!fs.existsSync(resolved)) {
    console.log(JSON.stringify({
      status: 'error',
      error: 'FILE_NOT_FOUND',
      message: `Berkas source map tidak ditemukan di: ${resolved}`
    }, null, 2));
    process.exit(0);
  }

  try {
    const raw = fs.readFileSync(resolved, 'utf8');
    const mapObj = JSON.parse(raw);

    if (action === 'inspect') {
      console.log(JSON.stringify({
        status: 'success',
        action: 'inspect',
        version: mapObj.version,
        target_file: mapObj.file || 'unknown',
        total_original_sources: (mapObj.sources || []).length,
        sources: (mapObj.sources || []).slice(0, 50),
        has_source_content: !!mapObj.sourcesContent,
        total_names: (mapObj.names || []).length,
        names_sample: (mapObj.names || []).slice(0, 30),
        message: `Inspeksi source map selesai. ${(mapObj.sources || []).length} berkas sumber teridentifikasi.`
      }, null, 2));
      return;
    }

    if (action === 'resolve') {
      const targetLine = parseInt(params.line, 10);
      const targetCol = parseInt(params.column || 0, 10);

      if (isNaN(targetLine) || targetLine < 1) {
        console.log(JSON.stringify({
          status: 'error',
          error: 'INVALID_LINE',
          message: 'Parameter line wajib diisi integer positif (1-indexed) untuk resolve!'
        }, null, 2));
        process.exit(0);
      }

      const decodedLines = parseMappings(mapObj.mappings || '');
      const lineIdx = targetLine - 1;

      if (lineIdx >= decodedLines.length) {
        console.log(JSON.stringify({
          status: 'error',
          error: 'LINE_OUT_OF_BOUNDS',
          message: `Baris ${targetLine} melebihi jumlah baris terpetakan (${decodedLines.length}).`
        }, null, 2));
        process.exit(0);
      }

      const segments = decodedLines[lineIdx];
      let bestSeg = null;

      for (const seg of segments) {
        if (seg[0] <= targetCol) {
          bestSeg = seg;
        } else {
          break;
        }
      }

      if (!bestSeg && segments.length > 0) {
        bestSeg = segments[0];
      }

      if (!bestSeg || bestSeg.length < 4) {
        console.log(JSON.stringify({
          status: 'error',
          error: 'MAPPING_NOT_FOUND',
          message: `Tidak ditemukan segmen pemetaan untuk baris ${targetLine}, kolom ${targetCol}.`
        }, null, 2));
        process.exit(0);
      }

      const srcIdx = bestSeg[1];
      const origLine = bestSeg[2] + 1; // 1-indexed
      const origCol = bestSeg[3];
      const originalFile = mapObj.sources[srcIdx] || 'unknown';
      let originalName = null;
      if (bestSeg.length >= 5 && mapObj.names) {
        originalName = mapObj.names[bestSeg[4]] || null;
      }

      console.log(JSON.stringify({
        status: 'success',
        action: 'resolve',
        generated: { line: targetLine, column: targetCol },
        original: {
          file: originalFile,
          line: origLine,
          column: origCol,
          name: originalName
        },
        message: `Berhasil memetakan (${targetLine}:${targetCol}) -> ${originalFile}:${origLine}:${origCol}`
      }, null, 2));
      return;
    }

    console.log(JSON.stringify({
      status: 'error',
      error: 'UNKNOWN_ACTION',
      message: `Aksi '${action}' tidak dikenali. Gunakan 'inspect' atau 'resolve'.`
    }, null, 2));
  } catch (err) {
    console.log(JSON.stringify({
      status: 'error',
      error: 'SOURCE_MAP_FAILED',
      message: `Gagal memproses source map: ${err.message}`
    }, null, 2));
    process.exit(0);
  }
}

main();
