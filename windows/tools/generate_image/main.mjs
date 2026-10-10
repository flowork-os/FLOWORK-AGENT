#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

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
const prompt = params.Prompt || params.prompt || 'Design Mockup';
const imageName = params.ImageName || params.image_name || `gen_${Date.now()}`;
const targetDir = path.resolve(process.cwd(), '.FL_BIN', 'generated_images');
if (!fs.existsSync(targetDir)) fs.mkdirSync(targetDir, { recursive: true });

const targetFile = path.join(targetDir, `${imageName}.svg`);
const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <rect width="800" height="600" fill="#0b0f19"/>
  <text x="400" y="300" fill="#00ffff" font-family="monospace" font-size="20" text-anchor="middle">${prompt}</text>
</svg>`;

fs.writeFileSync(targetFile, svgContent, 'utf8');

const result = {
  status: 'SUCCESS',
  image_name: imageName,
  file_path: targetFile,
  aspect_ratio: params.AspectRatio || '1:1',
  prompt
};

console.log(JSON.stringify(result, null, 2));
process.exit(0);
