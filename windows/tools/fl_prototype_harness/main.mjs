#!/usr/bin/env node
/**
 * 🔬 fl_prototype_harness - Zero-Dependency Throwaway Logic & UI Spike Generator
 * Generates self-contained HTML harnesses with in-memory reducers, interactive triggers, and state inspectors.
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

function generateSpikeHtml(title, initialState, actions) {
  const actionsList = Array.isArray(actions) && actions.length > 0 ? actions : ['INITIALIZE', 'EXECUTE_STEP', 'HANDLE_ERROR', 'RESET'];
  const stateObj = initialState && typeof initialState === 'object' ? initialState : { status: "IDLE", count: 0, log: [] };

  const buttonsHtml = actionsList.map(a => `      <button class="btn" onclick="dispatch({ type: '${a}' })">${a}</button>`).join('\n');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>🔬 Spike Harness: ${title || 'State Exploration'}</title>
  <style>
    body { font-family: monospace; background: #0d1117; color: #c9d1d9; margin: 0; padding: 24px; }
    h1 { color: #58a6ff; font-size: 1.25rem; border-bottom: 1px solid #30363d; padding-bottom: 8px; }
    .controls { margin: 16px 0; display: flex; gap: 8px; flex-wrap: wrap; }
    .btn { background: #21262d; color: #58a6ff; border: 1px solid #30363d; padding: 8px 14px; cursor: pointer; font-family: inherit; font-size: 13px; }
    .btn:hover { background: #30363d; color: #79c0ff; }
    .state-panel { background: #161b22; border: 1px solid #30363d; padding: 16px; margin-top: 16px; border-radius: 4px; }
    pre { margin: 0; color: #7ee787; font-size: 13px; overflow-x: auto; }
    .history { margin-top: 16px; border-top: 1px solid #30363d; padding-top: 12px; font-size: 12px; color: #8b949e; }
  </style>
</head>
<body>
  <h1>🔬 ${title || 'Prototype Spike Harness'}</h1>
  <p style="color: #8b949e;">Interactive in-memory reducer spike. Test actions and verify state transitions before committing to production architecture.</p>

  <div class="controls">
${buttonsHtml}
  </div>

  <div class="state-panel">
    <div style="font-weight: bold; margin-bottom: 8px; color: #58a6ff;">Current State:</div>
    <pre id="stateDisplay"></pre>
  </div>

  <div class="history">
    <div style="font-weight: bold; margin-bottom: 4px;">Transition Ledger:</div>
    <ul id="historyList" style="padding-left: 20px;"></ul>
  </div>

  <script>
    let state = ${JSON.stringify(stateObj, null, 2)};
    const historyList = [];

    function reducer(prevState, action) {
      switch (action.type) {
        ${actionsList.map(a => `case '${a}':
          return { ...prevState, last_action: '${a}', timestamp: new Date().toISOString() };`).join('\n        ')}
        default:
          return prevState;
      }
    }

    function dispatch(action) {
      const nextState = reducer(state, action);
      historyList.unshift(\`[\${new Date().toLocaleTimeString()}] Action: \${action.type}\`);
      state = nextState;
      render();
    }

    function render() {
      document.getElementById('stateDisplay').textContent = JSON.stringify(state, null, 2);
      const ul = document.getElementById('historyList');
      ul.innerHTML = historyList.slice(0, 10).map(h => '<li>' + h + '</li>').join('');
    }

    render();
  </script>
</body>
</html>
`;
}

function main() {
  const params = parseArgs();
  const title = params.title || 'Throwaway Logic Spike';
  const outputPath = path.resolve(params.output_file || './prototype_spike.html');

  let stateObj = {};
  if (params.state_fields_json) {
    try {
      stateObj = typeof params.state_fields_json === 'string' ? JSON.parse(params.state_fields_json) : params.state_fields_json;
    } catch (_) {}
  }

  let actions = [];
  if (params.actions_json) {
    try {
      actions = typeof params.actions_json === 'string' ? JSON.parse(params.actions_json) : params.actions_json;
    } catch (_) {}
  }

  const html = generateSpikeHtml(title, stateObj, actions);
  fs.writeFileSync(outputPath, html, 'utf8');

  console.log(JSON.stringify({
    status: "success",
    action: "scaffold_logic_spike",
    title,
    output_path: outputPath,
    is_standalone_html: true,
    file_size_bytes: Buffer.byteLength(html),
    usage: `Open file directly in browser or use run_command with xdg-open/explorer.exe/open.`
  }, null, 2));
}

main();
