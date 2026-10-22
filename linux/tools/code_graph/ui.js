// [FL_INDEX: keywords="code_graph, repomap, canvas_ui, holographic_interface" | purpose="Interactive Canvas UI controller for code_graph tool"]
/**
 * 🗺️ FLOWORK OS — CODE GRAPH CANVAS UI
 */
export function mountLive(container, options = {}) {
  const root = document.createElement('div');
  root.className = 'fl-code-graph-container';

  // 1. Header
  const header = document.createElement('div');
  header.className = 'fl-code-graph-header';

  const title = document.createElement('div');
  title.className = 'fl-code-graph-title';
  const iconSpan = document.createElement('span');
  iconSpan.textContent = '🗺️';
  const textSpan = document.createElement('span');
  textSpan.textContent = 'Flowork Sovereign Code Graph';
  title.appendChild(iconSpan);
  title.appendChild(textSpan);

  const stats = document.createElement('div');
  stats.className = 'fl-code-graph-stats';
  const tokenBadge = document.createElement('span');
  tokenBadge.className = 'fl-code-graph-badge';
  tokenBadge.id = 'cg-token-badge';
  tokenBadge.textContent = 'Tokens: 0 / 1024';
  const filesBadge = document.createElement('span');
  filesBadge.className = 'fl-code-graph-badge';
  filesBadge.id = 'cg-files-badge';
  filesBadge.textContent = 'Files: 0';
  stats.appendChild(tokenBadge);
  stats.appendChild(filesBadge);

  header.appendChild(title);
  header.appendChild(stats);
  root.appendChild(header);

  // 2. Toolbar
  const toolbar = document.createElement('div');
  toolbar.className = 'fl-code-graph-toolbar';

  const queryInput = document.createElement('input');
  queryInput.type = 'text';
  queryInput.className = 'fl-code-graph-input';
  queryInput.id = 'cg-query-input';
  queryInput.placeholder = 'Search symbols, functions, or filter path...';

  const refreshBtn = document.createElement('button');
  refreshBtn.className = 'fl-code-graph-btn';
  refreshBtn.id = 'cg-refresh-btn';
  refreshBtn.textContent = 'Generate Map';

  toolbar.appendChild(queryInput);
  toolbar.appendChild(refreshBtn);
  root.appendChild(toolbar);

  // 3. Content area
  const outputEl = document.createElement('div');
  outputEl.className = 'fl-code-graph-content';
  outputEl.id = 'cg-map-output';
  outputEl.textContent = 'Code Graph ready. Click "Generate Map" to analyze repository.';
  root.appendChild(outputEl);

  container.appendChild(root);

  async function fetchMap(query = '') {
    outputEl.textContent = 'Analyzing AST symbols and computing PageRank...';
    try {
      if (window.Flowork && window.Flowork.executeTool) {
        const res = await window.Flowork.executeTool('code_graph', {
          action: query ? 'query' : 'map',
          query: query || undefined,
          max_tokens: 1024
        });
        if (res && res.repo_map) {
          outputEl.textContent = res.repo_map;
          tokenBadge.textContent = `Tokens: ${res.actual_tokens || 0} / ${res.max_tokens || 1024}`;
          filesBadge.textContent = `Files: ${res.included_files || res.total_files || 0}`;
        } else {
          outputEl.textContent = JSON.stringify(res, null, 2);
        }
      } else {
        outputEl.textContent = '🗺️ CODE GRAPH & REPO MAP READY\n(Connect to Flowork OS runtime to stream live repo telemetry)';
      }
    } catch (err) {
      outputEl.textContent = 'Failed to generate code graph: ' + (err.message || String(err));
    }
  }

  refreshBtn.addEventListener('click', () => fetchMap(queryInput.value.trim()));
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') fetchMap(queryInput.value.trim());
  });

  return {
    unmount: () => {
      root.remove();
    }
  };
}
