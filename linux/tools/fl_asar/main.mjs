#!/usr/bin/env node
/**
 * 📦 fl_asar - Sovereign Electron ASAR Inspector & Extractor
 * Pure Node.js zero-dependency implementation of Chromium/Electron ASAR archive parser.
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
import fs from 'fs';
import path from 'path';

process.on("uncaughtException", (err) => {
  console.log(JSON.stringify({ status: "error", error: "UNCAUGHT_EXCEPTION", message: err.message }, null, 2));
  process.exit(0);
});
process.on("unhandledRejection", (reason) => {
  console.log(JSON.stringify({ status: "error", error: "UNHANDLED_REJECTION", message: String(reason) }, null, 2));
  process.exit(0);
});

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

function parseAsarHeader(filePath) {
  const fd = fs.openSync(filePath, 'r');
  const sizeBuf = Buffer.alloc(16);
  fs.readSync(fd, sizeBuf, 0, 16, 0);

  // Chromium pickle header format:
  // Offset 0: pickle magic (uint32)
  // Offset 4: pickle payload size (uint32)
  // Offset 8: inner payload size (uint32)
  // Offset 12: header json string length (uint32)
  const headerSize = sizeBuf.readUInt32LE(12);
  const headerBuf = Buffer.alloc(headerSize);
  fs.readSync(fd, headerBuf, 0, headerSize, 16);
  fs.closeSync(fd);

  const headerJson = headerBuf.toString('utf8');
  const header = JSON.parse(headerJson);
  const dataOffset = 16 + headerSize;

  return { header, dataOffset };
}

function traverseAsarFiles(filesObj, currentPath = '', result = []) {
  for (const [name, meta] of Object.entries(filesObj)) {
    const itemPath = currentPath ? `${currentPath}/${name}` : name;
    if (meta.files) {
      traverseAsarFiles(meta.files, itemPath, result);
    } else {
      result.push({
        path: itemPath,
        size: meta.size || 0,
        offset: meta.offset ? parseInt(meta.offset, 10) : 0,
        unpacked: !!meta.unpacked
      });
    }
  }
  return result;
}

function extractFiles(filePath, filesList, dataOffset, outDir) {
  const fd = fs.openSync(filePath, 'r');
  fs.mkdirSync(outDir, { recursive: true });
  let extractedCount = 0;
  let totalBytes = 0;

  for (const item of filesList) {
    if (item.unpacked) continue;
    const destPath = path.join(outDir, item.path);
    fs.mkdirSync(path.dirname(destPath), { recursive: true });

    if (item.size > 0) {
      const fileBuf = Buffer.alloc(item.size);
      fs.readSync(fd, fileBuf, 0, item.size, dataOffset + item.offset);
      fs.writeFileSync(destPath, fileBuf);
      totalBytes += item.size;
    } else {
      fs.writeFileSync(destPath, Buffer.alloc(0));
    }
    extractedCount++;
  }
  fs.closeSync(fd);
  return { extractedCount, totalBytes };
}

function main() {
  const params = parseArgs();
  const action = (params.action || 'inspect').toLowerCase();
  const asarPath = params.asar_path || params.path || params.target_path || params.target;

  if (!asarPath) {
    console.log(JSON.stringify({
      status: 'error',
      error: 'PARAMETER_MISSING',
      message: 'Parameter asar_path wajib diisi dengan path ke berkas app.asar!'
    }, null, 2));
    process.exit(0);
  }

  const resolvedPath = path.resolve(process.cwd(), asarPath);
  if (!fs.existsSync(resolvedPath)) {
    console.log(JSON.stringify({
      status: 'error',
      error: 'FILE_NOT_FOUND',
      message: `Berkas ASAR tidak ditemukan di: ${resolvedPath}`
    }, null, 2));
    process.exit(0);
  }

  try {
    const { header, dataOffset } = parseAsarHeader(resolvedPath);
    const filesList = traverseAsarFiles(header.files || {});
    const stat = fs.statSync(resolvedPath);

    if (action === 'extract') {
      const outDir = path.resolve(process.cwd(), params.output_dir || '.FL_BIN/scratch/unpacked_asar');
      const { extractedCount, totalBytes } = extractFiles(resolvedPath, filesList, dataOffset, outDir);

      console.log(JSON.stringify({
        status: 'success',
        action: 'extract',
        asar_path: resolvedPath,
        output_directory: outDir,
        total_files_extracted: extractedCount,
        total_unpacked_bytes: totalBytes,
        archive_size_bytes: stat.size,
        message: `Arsip ASAR berhasil dibongkar ke '${outDir}' (${extractedCount} berkas, ${totalBytes} bytes).`
      }, null, 2));
      return;
    }

    // Default: Inspect
    let packageJsonMeta = null;
    const pkgEntry = filesList.find(f => f.path === 'package.json');
    if (pkgEntry && pkgEntry.size > 0 && !pkgEntry.unpacked) {
      const fd = fs.openSync(resolvedPath, 'r');
      const pkgBuf = Buffer.alloc(pkgEntry.size);
      fs.readSync(fd, pkgBuf, 0, pkgEntry.size, dataOffset + pkgEntry.offset);
      fs.closeSync(fd);
      try { packageJsonMeta = JSON.parse(pkgBuf.toString('utf8')); } catch (_) {}
    }

    const topLevelFiles = Object.keys(header.files || {}).slice(0, 30);
    const totalSize = filesList.reduce((acc, f) => acc + f.size, 0);

    console.log(JSON.stringify({
      status: 'success',
      action: 'inspect',
      asar_path: resolvedPath,
      archive_size_bytes: stat.size,
      total_files_count: filesList.length,
      total_uncompressed_bytes: totalSize,
      header_data_offset: dataOffset,
      top_level_entries: topLevelFiles,
      package_metadata: packageJsonMeta ? {
        name: packageJsonMeta.name,
        version: packageJsonMeta.version,
        main: packageJsonMeta.main,
        dependencies_count: Object.keys(packageJsonMeta.dependencies || {}).length
      } : null,
      message: `Inspeksi ASAR selesai. Total ${filesList.length} berkas terindeks.`
    }, null, 2));
  } catch (err) {
    console.log(JSON.stringify({
      status: 'error',
      error: 'ASAR_PARSE_FAILED',
      message: `Gagal membaca arsip ASAR: ${err.message}`
    }, null, 2));
    process.exit(0);
  }
}

main();
