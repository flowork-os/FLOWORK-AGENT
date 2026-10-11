#!/usr/bin/env node
import os from 'os';
import { execSync } from 'child_process';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try { params = JSON.parse(args[pIdx + 1]); } catch (_) {}
  }
  return params;
}

const params = parseArgs();
const cpus = os.cpus();
const totalMem = os.totalmem();
const freeMem = os.freemem();
const usedMem = totalMem - freeMem;

let diskInfo = 'N/A';
try {
  if (process.platform === 'win32') {
    diskInfo = execSync('wmic logicaldisk get caption,freespace,size', { encoding: 'utf8' }).trim();
  } else {
    diskInfo = execSync('df -h / | tail -n 1', { encoding: 'utf8' }).trim();
  }
} catch (_) {}

const result = {
  status: 'SUCCESS',
  exit_code: 0,
  platform: process.platform,
  arch: process.arch,
  hostname: os.hostname(),
  uptime_hours: Number((os.uptime() / 3600).toFixed(2)),
  cpu: {
    model: cpus.length ? cpus[0].model : 'Generic CPU',
    cores: cpus.length,
    speed_mhz: cpus.length ? cpus[0].speed : 0
  },
  memory: {
    total_mb: Math.round(totalMem / (1024 * 1024)),
    free_mb: Math.round(freeMem / (1024 * 1024)),
    used_mb: Math.round(usedMem / (1024 * 1024)),
    used_pct: Number(((usedMem / totalMem) * 100).toFixed(1))
  },
  load_average: os.loadavg(),
  disk_snapshot: diskInfo,
  timestamp: new Date().toISOString()
};

console.log(JSON.stringify(result, null, 2));
process.exit(0);
