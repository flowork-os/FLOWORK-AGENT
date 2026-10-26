#!/usr/bin/env node
// 🏛️ Flowork OS Modular Tool: app_control
// Real-Time Canvas UI App Lifecycle Control: open, reload, close, status, list
// Co-authored-by: Flowork OS <agent@floworkos.com>

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
  const action = (params.action || params.Action || '').trim().toLowerCase();
  const appId = (params.app_id || params.plugin_id || params.id || '').trim();
  const port = process.env.FLOWORK_PORT || '19890';
  const baseUrl = `http://127.0.0.1:${port}`;

  if (!action) {
    console.error(JSON.stringify({
      status: 'ERROR',
      exit_code: 1,
      message: "Parameter 'action' is required (open, reload, close, status, list)"
    }, null, 2));
    process.exit(1);
  }

  try {
    let result = {};
    if (action === 'open' || action === 'launch') {
      if (!appId) throw new Error("Parameter 'app_id' is required for action 'open'");
      const res = await fetch(`${baseUrl}/api/apps/${appId}/open`, { method: 'POST' });
      result = await res.json();
    } else if (action === 'reload' || action === 'refresh') {
      if (!appId) throw new Error("Parameter 'app_id' is required for action 'reload'");
      const res = await fetch(`${baseUrl}/api/apps/${appId}/reload`, { method: 'POST' });
      result = await res.json();
    } else if (action === 'close' || action === 'stop') {
      if (!appId) throw new Error("Parameter 'app_id' is required for action 'close'");
      const res = await fetch(`${baseUrl}/api/apps/${appId}/close`, { method: 'POST' });
      result = await res.json();
    } else if (action === 'status') {
      if (!appId) throw new Error("Parameter 'app_id' is required for action 'status'");
      const res = await fetch(`${baseUrl}/api/apps/${appId}/status`);
      result = await res.json();
    } else if (action === 'list') {
      const res = await fetch(`${baseUrl}/api/apps`);
      result = await res.json();
    } else {
      throw new Error(`Unsupported action '${action}'. Valid actions: open, reload, close, status, list.`);
    }

    console.log(JSON.stringify({
      status: 'SUCCESS',
      exit_code: 0,
      tool: 'app_control',
      action,
      app_id: appId || undefined,
      result
    }, null, 2));
    process.exit(0);
  } catch (err) {
    console.error(JSON.stringify({
      status: 'ERROR',
      exit_code: 1,
      tool: 'app_control',
      message: err.message
    }, null, 2));
    process.exit(1);
  }
}

main();
