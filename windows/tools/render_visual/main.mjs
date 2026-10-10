#!/usr/bin/env node
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
const widgetType = params.widget_type || params.type || 'kpi_deck';
const title = params.title || 'Visual Telemetry';
const subtitle = params.subtitle || '';
const data = params.data || {};
const options = params.options || {};

const result = {
  status: 'SUCCESS',
  action: 'rendered',
  widget_type: widgetType,
  title,
  subtitle,
  rendered_at: new Date().toISOString(),
  data,
  options,
  ui_channel: 'canvas_hologram'
};

console.log(JSON.stringify(result, null, 2));
process.exit(0);
