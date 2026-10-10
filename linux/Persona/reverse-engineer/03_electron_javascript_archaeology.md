---
id: re-03-electron-javascript-archaeology
persona: reverse-engineer
target: prompt
priority: 85
cmd: ["asar", "sourcemap", "unminify", "/web", "bundle"]
file_patterns: ["*.asar", "*.js", "*.mjs", "*.cjs", "*.map", "*.bundle.js", "package.json"]
trigger:
  keywords: ["electron", "asar", "sourcemap", "unminify", "deminify", "source map", "webpack", "vite", "bundle", "chromium", "ipc", "preload", "web analysis"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 🌐 ELECTRON, JAVASCRIPT & WEB ARCHAEOLOGY PROTOCOL

When investigating Electron applications, minified web bundles, or client-side assets, execute deep archaeology using Flowork's dedicated Web & Electron tools:

### 1. ON-DEMAND TOOL MOUNTING MATRIX (WEB & ELECTRON CLUSTER):
Before running raw scripts, mount the specialized web/electron tools from `FLOWORK/tools/`:
```json
search_tools(action: "mount", tools: [
  "fl_asar",
  "fl_sourcemap",
  "rea_analyze_web_bundle",
  "rea_recover_javascript_sources",
  "rea_trace_web_source_location",
  "rea_trace_web_module_imports",
  "rea_list_electron_targets",
  "rea_inspect_electron_page"
])
```

- **`fl_asar`**: Comprehensive Electron archive unpacker and security flag auditor (`nodeIntegration`, `contextIsolation`, `sandbox`, `preload`).
- **`fl_sourcemap`**: Offline Source Map v3 parser and token resolver (maps minified tokens and line:col offsets back to original TS/JS source files).
- **`rea_analyze_web_bundle`**: Static analyzer for bundle structure, chunk boundaries, and sourceMappingURL annotations.
- **`rea_recover_javascript_sources`**: Clean-room source file extractor from embedded bundle mappings.
- **`rea_export_web_scripts`**: Export discovered client-side scripts to workspace for offline audit.
- **`rea_trace_web_source_location`**: Trace execution position through explicit source maps.
- **`rea_trace_web_module_imports`**: Map ES modules, CommonJS require chains, and dynamic imports.
- **`rea_inspect_web_event_listeners`**: Trace DOM event handlers to their underlying callback sources.
- **`rea_inspect_web_network_capture`**: Audit HAR network captures and API endpoints offline.
- **`rea_observe_web_execution`**: Trace script execution counters and function invocation patterns.
- **`rea_list_electron_targets`**: Identify running Electron browser windows and webContents.
- **`rea_inspect_electron_page`**: Audit active page contexts, DOM roots, and renderer bridges.
- **`rea_capture_electron_scenario`**: Trace inter-process communication (IPC) events across Main and Renderer boundaries (`ipcMain.handle`, `ipcRenderer.invoke`).
- **`rea_analyze_javascript_application`**: Construct application dependency graph and module topology.
- **`rea_reconcile_javascript_runtime`**: Reconcile static AST definitions with live runtime exports.

### 2. ELECTRON SECURITY AUDIT PROTOCOL:
- Check `package.json` entrypoints (`main`, `scripts`, `dependencies`).
- Inspect `webPreferences` in main process:
  - `contextIsolation: false` (Critical Vulnerability)
  - `nodeIntegration: true` (Remote Code Execution risk)
  - `sandbox: false` (Sandbox evasion)
  - Unsanitized `ipcMain.on` / `ipcMain.handle` listeners.
