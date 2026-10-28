#!/usr/bin/env node
// 🏛️ Flowork OS Sovereign Tool: app_publish
// Automated, standard App Store publisher & registry synchronizer
// Co-authored-by: Flowork OS <agent@floworkos.com>

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try { params = JSON.parse(args[pIdx + 1]); } catch (_) {}
  }
  return params;
}

async function main() {
  const params = parseArgs();
  const appId = params.app_id || params.app || params.id;
  if (!appId) {
    console.error(JSON.stringify({
      status: 'ERROR',
      exit_code: 1,
      message: "Parameter 'app_id' is required"
    }, null, 2));
    process.exit(1);
  }

  const rootDir = process.env.FLOWORK_DIR || path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
  const appSourceDir = path.resolve(rootDir, 'apps', appId);
  if (!fs.existsSync(appSourceDir)) {
    console.error(JSON.stringify({
      status: 'ERROR',
      exit_code: 1,
      message: `App directory not found: ${appSourceDir}`
    }, null, 2));
    process.exit(1);
  }

  const stagingDir = path.resolve(rootDir, '.FL_BIN/scratch/apps_staging');
  const pythonScript = path.resolve(rootDir, '.FL_BIN/flow_app_publisher.py');

  const child = spawn('python3', [pythonScript, stagingDir, appSourceDir], {
    stdio: 'inherit'
  });

  child.on('close', (code) => {
    if (code === 0) {
      console.log(JSON.stringify({
        status: 'SUCCESS',
        exit_code: 0,
        app_id: appId,
        message: `App ${appId} successfully staged and indexed.`
      }, null, 2));
      process.exit(0);
    } else {
      console.error(JSON.stringify({
        status: 'ERROR',
        exit_code: code,
        message: `Publish tool failed with exit code ${code}`
      }, null, 2));
      process.exit(code);
    }
  });
}

main();
