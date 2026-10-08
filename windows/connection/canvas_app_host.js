// [FLOWORKOS:NANO-PLUG] Canvas App Host & CDP Prompt Dispatcher
// Manages micro-apps in /app and dispatches prompts directly into active chat.

const fs = require('fs');
const path = require('path');
const os = require('os');
const http = require('http');
const crypto = require('crypto');
const { spawn } = require('child_process');

// Ephemeral intra-process dispatch secret (Strict zero-cross-site prompt injection guard)
const INTERNAL_DISPATCH_SECRET = crypto.randomBytes(32).toString('hex');
const CANDIDATE_APPS_ROOT = [
    process.env.FLOWORK_PLUGINS_ROOT,
    process.env.FLOWORK_APPS_ROOT,
    path.resolve(__dirname, '..', 'plugins'),
    path.resolve(__dirname, '..', 'app')
].filter(Boolean);
let APPS_ROOT = CANDIDATE_APPS_ROOT[0];
for (const cand of CANDIDATE_APPS_ROOT) {
    if (fs.existsSync(cand)) {
        APPS_ROOT = cand;
        break;
    }
}
const runningEngines = new Map(); // appId -> childProcess
const appSseClients = new Set();
let appWatchDebounce = null;

function getAppsRoot() {
    return APPS_ROOT;
}

function listApps() {
    if (!fs.existsSync(APPS_ROOT)) return [];
    const entries = fs.readdirSync(APPS_ROOT, { withFileTypes: true });
    const apps = [];
    for (const ent of entries) {
        if (!ent.isDirectory() || ent.name.startsWith('.') || ent.name.startsWith('_')) continue;
        const appDir = path.join(APPS_ROOT, ent.name);
        
        // Scan for potential manifests
        let manifest = null;
        const candidateManifests = [
            path.join(appDir, 'app.manifest.json'),
            path.join(appDir, 'manifest.json'),
            path.join(appDir, 'package.json')
        ];
        for (const mPath of candidateManifests) {
            if (fs.existsSync(mPath)) {
                try {
                    manifest = JSON.parse(fs.readFileSync(mPath, 'utf8'));
                    break;
                } catch (_) {}
            }
        }

        // Detect GUI entry
        let entryGui = null;
        if (manifest && manifest.entry && manifest.entry.gui) {
            entryGui = `/apps/${ent.name}/${manifest.entry.gui.replace(/^\.?\//, '')}`;
        } else if (fs.existsSync(path.join(appDir, 'gui', 'index.html'))) {
            entryGui = `/apps/${ent.name}/gui/index.html`;
        } else if (fs.existsSync(path.join(appDir, 'index.html'))) {
            entryGui = `/apps/${ent.name}/index.html`;
        } else {
            entryGui = `/apps/${ent.name}/gui/index.html`;
        }

        const id = (manifest && manifest.id) || ent.name;
        const name = (manifest && manifest.name) || ent.name.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        const desc = (manifest && (manifest.description || manifest.desc)) || 'Sovereign Plug & Play Micro-App';
        const category = (manifest && manifest.category) || 'Plug & Play';
        const icon = (manifest && manifest.icon) || '⚡';
        const port = (manifest && manifest.ipc && (manifest.ipc.default_port || manifest.ipc.port)) || null;
        const runtime = (manifest && manifest.runtime) || 'native';
        const wasmBinary = (manifest && manifest.wasm_binary) || null;
        const url = `http://127.0.0.1:17700${entryGui}`;

        apps.push({
            id,
            dir: ent.name,
            name,
            icon,
            description: desc,
            desc,
            category,
            port,
            runtime,
            wasm_binary: wasmBinary,
            entryGui,
            url
        });
    }
    return apps;
}

function broadcastAppsChanged() {
    const apps = listApps();
    const payload = JSON.stringify({ type: 'APPS_CHANGED', count: apps.length, apps });
    for (const client of appSseClients) {
        try {
            client.write(`data: ${payload}\n\n`);
        } catch (_) {
            appSseClients.delete(client);
        }
    }
}

// ⚡ Active Real-Time Filesystem Watcher on /app
if (fs.existsSync(APPS_ROOT)) {
    try {
        fs.watch(APPS_ROOT, { recursive: false }, (eventType, filename) => {
            if (filename && (filename.startsWith('.') || filename.startsWith('_'))) return;
            clearTimeout(appWatchDebounce);
            appWatchDebounce = setTimeout(() => {
                console.log(`[Canvas App Host] ⚡ Real-time filesystem change in /app: ${eventType} -> ${filename}`);
                broadcastAppsChanged();
            }, 100);
        });
        console.log(`[Canvas App Host] 👁️ Real-time watcher active on ${APPS_ROOT}`);
    } catch (err) {
        console.warn(`[Canvas App Host] Watcher warning: ${err.message}`);
    }
}

const net = require('net');

function isPortActive(port) {
    return new Promise((resolve) => {
        if (!port) return resolve(false);
        const s = net.createConnection({ port, host: '127.0.0.1', timeout: 350 });
        s.once('connect', () => { s.destroy(); resolve(true); });
        s.once('timeout', () => { s.destroy(); resolve(false); });
        s.once('error', () => { resolve(false); });
    });
}

async function ensureAppEngine(appId) {
    const appDir = path.join(APPS_ROOT, appId);
    const manifestPath = path.join(appDir, 'app.manifest.json');
    let defaultPort = null;
    if (fs.existsSync(manifestPath)) {
        try {
            const m = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
            defaultPort = m.ipc?.default_port || null;
        } catch (_) {}
    }

    if (defaultPort && await isPortActive(defaultPort)) {
        return true;
    }

    if (runningEngines.has(appId)) {
        const proc = runningEngines.get(appId);
        if (!proc.killed && proc.exitCode === null) return true;
    }

    const serverMjs = path.join(appDir, 'engine', 'server.mjs');
    if (!fs.existsSync(serverMjs)) return false;

    console.log(`[Canvas App Host] 🚀 Auto-launching engine for '${appId}'...`);
    try {
        const child = spawn(process.execPath, [serverMjs], {
            cwd: path.join(appDir, 'engine'),
            detached: true,
            stdio: 'ignore',
            env: { ...process.env, FLOWORK_SIDECAR_HOST_PORT: '17700' }
        });
        child.unref();
        runningEngines.set(appId, child);
        return true;
    } catch (err) {
        console.warn(`[Canvas App Host] Failed to launch engine for ${appId}:`, err.message);
        return false;
    }
}

function getFloworkDir() {
    const root = path.resolve(__dirname, '..');
    const possible = [
        path.join(process.env.FLOWORK_PORTABLE_ROOT || '', '.flowork'),
        path.join(root, 'portable-home', '.flowork'),
        path.join(root, '.flowork')
    ];
    for (const p of possible) {
        if (p && fs.existsSync(p)) return p;
    }
    const fallback = path.join(root, 'portable-home', '.flowork');
    try { fs.mkdirSync(fallback, { recursive: true }); } catch (_) {}
    return fallback;
}

function getActiveAppFilePath() {
    return path.join(getFloworkDir(), 'canvas_active_app.json');
}

function getActiveAppState() {
    try {
        const fp = getActiveAppFilePath();
        if (fs.existsSync(fp)) {
            return JSON.parse(fs.readFileSync(fp, 'utf8'));
        }
    } catch (_) {}
    return { id: null, name: 'None', view: 'closed', updatedAt: new Date().toISOString() };
}

function setActiveAppState(appId, view = 'app') {
    let state = {
        id: null,
        name: 'None',
        icon: '',
        category: '',
        port: null,
        view: view || 'closed',
        updatedAt: new Date().toISOString()
    };
    if (view === 'app' && appId) {
        const manifestPath = path.join(APPS_ROOT, appId, 'app.manifest.json');
        let m = {};
        if (fs.existsSync(manifestPath)) {
            try { m = JSON.parse(fs.readFileSync(manifestPath, 'utf8')); } catch (_) {}
        }
        state = {
            id: appId,
            name: m.name || appId,
            icon: m.icon || '📦',
            category: m.category || 'tool',
            port: m.ipc?.default_port || null,
            view: 'app',
            updatedAt: new Date().toISOString()
        };
    } else if (view === 'store') {
        state = {
            id: null,
            name: 'App Store',
            icon: '🛒',
            category: 'catalog',
            port: null,
            view: 'store',
            updatedAt: new Date().toISOString()
        };
    }
    try {
        const fp = getActiveAppFilePath();
        fs.writeFileSync(fp, JSON.stringify(state, null, 2), 'utf8');
    } catch (err) {
        console.error('[Canvas Host] Failed writing active app state:', err.message);
    }
    return state;
}

async function getActiveCdpPort() {
    // 1. Scan portable-home/.config, process.env.FLOWORK_PORTABLE_ROOT, ~/.config, etc.
    const searchDirs = [
        path.join(process.env.FLOWORK_PORTABLE_ROOT || '', '.config'),
        path.resolve(__dirname, '..', 'portable-home', '.config'),
        path.resolve(os.homedir(), 'Documents', 'MR.FLOWORK', 'portable-home', '.config'),
        path.resolve(os.homedir(), 'FLOWORK', 'portable-home', '.config'),
        path.join(os.homedir(), '.config')
    ];

    const candidateFiles = [];
    for (const d of searchDirs) {
        if (!d || !fs.existsSync(d)) continue;
        try {
            const entries = fs.readdirSync(d, { withFileTypes: true });
            for (const ent of entries) {
                if (ent.isDirectory()) {
                    const dtPath = path.join(d, ent.name, 'DevToolsActivePort');
                    if (fs.existsSync(dtPath) && !candidateFiles.includes(dtPath)) {
                        candidateFiles.push(dtPath);
                    }
                }
            }
        } catch (_) {}
    }

    // Sort candidate files by mtimeMs descending (most recently created/modified first)
    candidateFiles.sort((a, b) => {
        try { return fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs; } catch (_) { return 0; }
    });

    const candidatePorts = [];
    if (process.env.FLOWORK_CDP_PORT) {
        const p = Number(process.env.FLOWORK_CDP_PORT);
        if (!isNaN(p) && p > 0) candidatePorts.push(p);
    }

    for (const f of candidateFiles) {
        try {
            const line = fs.readFileSync(f, 'utf8').trim().split('\n')[0];
            const p = Number(line);
            if (!isNaN(p) && p > 0 && !candidatePorts.includes(p)) candidatePorts.push(p);
        } catch (_) {}
    }

    for (const p of candidatePorts) {
        try {
            const ctrl = new AbortController();
            const timer = setTimeout(() => ctrl.abort(), 400);
            const res = await fetch(`http://127.0.0.1:${p}/json/version`, { signal: ctrl.signal });
            clearTimeout(timer);
            if (res.ok) return p;
        } catch (_) {}
    }

    return candidatePorts[0] || 40327;
}

let dispatchLock = Promise.resolve();
let lastCdpDispatchedPrompt = null;
let lastCdpDispatchedTime = 0;

async function dispatchPromptToMainChat(promptText, requestedChatId = null) {
    if (!promptText || typeof promptText !== 'string') {
        return { success: false, error: 'EMPTY_PROMPT' };
    }

    // 1. Debounce rapid duplicate prompts within 1200ms
    const now = Date.now();
    if (lastCdpDispatchedPrompt === promptText && (now - lastCdpDispatchedTime) < 1200) {
        console.log('[Canvas App Host] ⏳ Debouncing identical prompt dispatch via CDP');
        return { success: true, debounced: true };
    }
    lastCdpDispatchedPrompt = promptText;
    lastCdpDispatchedTime = now;

    // 2. Sequential execution lock: strictly one CDP dispatch at a time
    const execute = async () => {
        return internalDispatchPromptToMainChat(promptText, requestedChatId);
    };

    const currentPromise = dispatchLock.then(execute, execute);
    dispatchLock = currentPromise.catch(() => {});
    return currentPromise;
}

async function internalDispatchPromptToMainChat(promptText, requestedChatId = null) {
    const cdpPort = await getActiveCdpPort();
    console.log(`[Canvas App Host] 🎯 Dispatching prompt via CDP (Port ${cdpPort})...`);
    
    let list;
    try {
        const res = await fetch(`http://127.0.0.1:${cdpPort}/json/list`);
        list = await res.json();
    } catch (err) {
        throw new Error(`Cannot connect to CDP on port ${cdpPort}: ${err.message}`);
    }

    // Find the main chat window/page
    let page = null;
    if (requestedChatId) {
        page = list.find(t => t.type === 'page' && t.webSocketDebuggerUrl && t.url && t.url.includes(requestedChatId));
    }
    if (!page) {
        page = list.find(t => t.type === 'page' && t.webSocketDebuggerUrl && (t.url.includes('/c/') || t.url.includes(':1989') || !t.url.startsWith('chrome-devtools')));
    }
    if (!page) {
        page = list.find(t => t.type === 'page' && t.webSocketDebuggerUrl);
    }
    if (!page) {
        throw new Error('No active IDE page target found via CDP');
    }

    return new Promise((resolve, reject) => {
        const ws = new WebSocket(page.webSocketDebuggerUrl);
        let finished = false;

        const timer = setTimeout(() => {
            if (!finished) {
                finished = true;
                try { ws.close(); } catch (_) {}
                reject(new Error('CDP prompt dispatch timed out after 8000ms'));
            }
        }, 8000);

        function send(method, params = {}) {
            return new Promise((res, rej) => {
                const id = Math.floor(Math.random() * 1000000);
                const handler = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.id === id) {
                            ws.removeEventListener('message', handler);
                            if (data.error) rej(new Error(data.error.message || JSON.stringify(data.error)));
                            else res(data.result);
                        }
                    } catch (_) {}
                };
                ws.addEventListener('message', handler);
                ws.send(JSON.stringify({ id, method, params }));
            });
        }

        ws.onopen = async () => {
            try {
                // 1. Detect currently active chat ID from the page URL/DOM
                const activeChatEval = await send('Runtime.evaluate', {
                    expression: `(() => {
                        const str = window.location.pathname + ' ' + window.location.href;
                        const m = str.match(/\\/c\\/([a-zA-Z0-9_-]{8,})/);
                        return m ? m[1] : null;
                    })()`,
                    returnByValue: true
                });
                const activeChatId = activeChatEval?.result?.value || null;
                console.log(`[Canvas App Host] 📍 Active open chat ID: ${activeChatId || 'global'}`);

                // 2. Focus message input element, cleanly clear old buffer, and establish selection Range
                const focusEval = await send('Runtime.evaluate', {
                    expression: `(() => {
                        const input = document.querySelector('div[aria-label="Message input"]') ||
                                      document.querySelector('[contenteditable="true"]') ||
                                      document.querySelector('textarea');
                        if (!input) return { ok: false, error: 'NO_INPUT' };
                        input.focus();
                        try {
                            const sel = window.getSelection();
                            sel.removeAllRanges();
                            const range = document.createRange();
                            range.selectNodeContents(input);
                            sel.addRange(range);
                            document.execCommand('delete', false, null);

                            sel.removeAllRanges();
                            const newRange = document.createRange();
                            newRange.selectNodeContents(input);
                            newRange.collapse(false);
                            sel.addRange(newRange);
                        } catch (_) {}
                        return { ok: true, tagName: input.tagName };
                    })()`,
                    returnByValue: true
                });

                if (!focusEval?.result?.value?.ok) {
                    throw new Error('Chat message input element not found in active view');
                }

                // 3. Native CDP Input.insertText (types prompt directly, activating Lexical and React state)
                await send('Input.insertText', { text: promptText });

                // Wait briefly for React state & button activation
                await new Promise(r => setTimeout(r, 150));

                // 4. Submit the message
                let submitted = false;
                for (let i = 0; i < 15; i++) {
                    const submitEval = await send('Runtime.evaluate', {
                        expression: `(() => {
                            // Method A: Click active send button
                            const btn = document.querySelector('button[data-tooltip-id="input-send-button-send-tooltip"]') ||
                                        document.querySelector('button[data-testid="send-button"]') ||
                                        document.querySelector('button[aria-label="Send message"]') ||
                                        document.querySelector('button[data-tooltip-id*="send-button"]:not([data-tooltip-id*="cancel"])') ||
                                        document.querySelector('button[title="Send"]') ||
                                        document.querySelector('button[type="submit"]') ||
                                        document.querySelector('button.send-btn');
                            if (btn && !btn.disabled) {
                                btn.click();
                                return { submitted: true, method: 'button_click' };
                            }

                            // Method B: React Fiber submit() invocation
                            const editable = document.querySelector('div[aria-label="Message input"]') ||
                                             document.querySelector('[contenteditable="true"]');
                            if (editable) {
                                const fKey = Object.keys(editable).find(k => k.startsWith('__reactFiber'));
                                let f = editable[fKey];
                                while (f) {
                                    if (f.memoizedProps && typeof f.memoizedProps.submit === 'function') {
                                        try {
                                            f.memoizedProps.submit();
                                            return { submitted: true, method: 'fiber_submit' };
                                        } catch (_) {}
                                    }
                                    f = f.return;
                                }
                            }

                            return { submitted: false };
                        })()`,
                        returnByValue: true
                    });

                    if (submitEval?.result?.value?.submitted) {
                        submitted = true;
                        break;
                    }
                    await new Promise(r => setTimeout(r, 120));
                }

                if (!submitted) {
                    console.log('[Canvas App Host] Dispatching Enter key via CDP fallback...');
                    await send('Input.dispatchKeyEvent', {
                        type: 'rawKeyDown',
                        windowsVirtualKeyCode: 13,
                        key: 'Enter',
                        code: 'Enter'
                    });
                    await send('Input.dispatchKeyEvent', {
                        type: 'char',
                        text: '\r'
                    });
                    await send('Input.dispatchKeyEvent', {
                        type: 'keyUp',
                        windowsVirtualKeyCode: 13,
                        key: 'Enter',
                        code: 'Enter'
                    });
                }

                const handshakeDir = path.resolve(__dirname, '..', 'portable-home', '.flowork');
                if (fs.existsSync(handshakeDir)) {
                    try {
                        const hs = {
                            chat_id: activeChatId,
                            active_tab: 'canvas',
                            timestamp: new Date().toISOString(),
                            status: 'CONNECTED'
                        };
                        fs.writeFileSync(path.join(handshakeDir, 'active_chat.json'), JSON.stringify(hs, null, 2));
                        fs.writeFileSync(path.join(handshakeDir, 'active_handshake.json'), JSON.stringify(hs, null, 2));
                    } catch (_) {}
                }

                // Restore clean Lexical focus for the user to continue typing freely
                try {
                    await send('Runtime.evaluate', {
                        expression: `(() => {
                            const input = document.querySelector('div[aria-label="Message input"]');
                            if (input && input.__lexicalEditor) {
                                try { input.__lexicalEditor.focus(); } catch (_) {}
                            }
                        })()`
                    });
                } catch (_) {}

                finished = true;
                clearTimeout(timer);
                ws.close();
                resolve({ success: true, dispatched: true, chatId: activeChatId });
            } catch (err) {
                if (!finished) {
                    finished = true;
                    clearTimeout(timer);
                    try { ws.close(); } catch (_) {}
                    reject(err);
                }
            }
        };

        ws.onerror = (err) => {
            if (!finished) {
                finished = true;
                clearTimeout(timer);
                reject(err);
            }
        };
    });
}

function getAppBundle(appId) {
    const guiDir = path.join(APPS_ROOT, appId, 'gui');
    const indexHtmlPath = path.join(guiDir, 'index.html');
    if (!fs.existsSync(indexHtmlPath)) return null;

    let html = fs.readFileSync(indexHtmlPath, 'utf8');

    // Inline all CSS
    html = html.replace(/<link\s+[^>]*rel=["']stylesheet["'][^>]*href=["']([^"']+)["'][^>]*\/?>/gi, (match, href) => {
        const cssPath = path.join(guiDir, href.split('?')[0]);
        if (fs.existsSync(cssPath)) {
            return `<style>/* inlined ${href} */\n${fs.readFileSync(cssPath, 'utf8')}\n</style>`;
        }
        return match;
    });

    // Inline all JS
    html = html.replace(/<script\s+[^>]*src=["']([^"']+)["'][^>]*><\/script>/gi, (match, src) => {
        const jsPath = path.join(guiDir, src.split('?')[0]);
        if (fs.existsSync(jsPath)) {
            return `<script>/* inlined ${src} */\n${fs.readFileSync(jsPath, 'utf8')}\n</script>`;
        }
        return match;
    });

    // Prepend Sovereign App Enclave Shim
    const shim = `
    <script>
      window.__FLOWORK_APP_ID__ = "${appId}";
      window.__FLOWORK_SIDECAR_PORT__ = 17700;
      window.__FLOWORK_CHAT_ID__ = function() {
        try {
          const m = window.parent.location.pathname.match(/\\/c\\/([a-zA-Z0-9_-]+)/);
          return m ? m[1] : null;
        } catch (_) {
          return null;
        }
      };
      const _origFetch = window.fetch;
      window.fetch = function(url, opts) {
        opts = opts || {};
        if (typeof url === 'string') {
          if (url.startsWith('/api/') && !url.startsWith('/api/prompt-dispatch') && !url.startsWith('/api/user') && !url.startsWith('/api/apps') && !url.startsWith('/api/active-chat')) {
            url = 'http://127.0.0.1:17700/apps/' + window.__FLOWORK_APP_ID__ + url;
          } else if (url.startsWith('/api/')) {
            url = 'http://127.0.0.1:17700' + url;
          }
          if (url.includes('/api/prompt-dispatch') && (opts.method || 'GET').toUpperCase() === 'POST') {
            opts.headers = opts.headers || {};
            if (typeof opts.headers.set === 'function') {
              opts.headers.set('X-Flowork-Dispatch-Key', '${INTERNAL_DISPATCH_SECRET}');
            } else {
              opts.headers['X-Flowork-Dispatch-Key'] = '${INTERNAL_DISPATCH_SECRET}';
            }
            try {
              const bodyObj = JSON.parse(opts.body || '{}');
              if (!bodyObj.chatId) {
                bodyObj.chatId = window.__FLOWORK_CHAT_ID__();
                opts.body = JSON.stringify(bodyObj);
              }
            } catch (_) {}
          }
        }
        return _origFetch.call(this, url, opts);
      };
    </script>
    `;
    if (html.includes('<head>')) {
        html = html.replace('<head>', '<head>' + shim);
    } else {
        html = shim + html;
    }

    return html;
}

function handleRequest(req, res, pathname, loadVault) {
    pathname = pathname || (req.url || '/').split('?')[0];
    // 0. Transparent Sovereign Gateway Proxy (/auth/*) -> Route to Router Port (e.g. 9100)
    if (pathname.startsWith('/auth/')) {
        const localPort = req.socket?.localPort;
        const currentRouterPort = parseInt(process.env.FLOWORK_ROUTER_PORT || '9099', 10);
        // If we are already running on the router port itself, never loop back to avoid infinite recursive deadlock
        if (localPort === 9099 || localPort === currentRouterPort) {
            return false;
        }

        const candidatePorts = [
            process.env.FLOWORK_ROUTER_PORT,
            process.env.FLOWORK_PORT ? (parseInt(process.env.FLOWORK_PORT, 10) - 1987 + 9099).toString() : null,
            '9100',
            '9099'
        ].filter(Boolean);
        const portsToTry = Array.from(new Set(candidatePorts));

        function proxyToPort(idx) {
            if (res.headersSent) return;
            if (idx >= portsToTry.length) {
                if (!res.headersSent) {
                    try {
                        res.writeHead(502, { 'Content-Type': 'application/json', 'access-control-allow-origin': '*' });
                        res.end(JSON.stringify({ success: false, error: '[Proxy Error] No active router responding on candidate ports: ' + portsToTry.join(', ') }));
                    } catch (_) {}
                }
                return;
            }
            const routerPort = parseInt(portsToTry[idx], 10);
            if (localPort && routerPort === localPort) {
                return proxyToPort(idx + 1);
            }

            const headers = { ...req.headers, host: `127.0.0.1:${routerPort}` };
            delete headers['sec-fetch-site'];
            delete headers['sec-fetch-mode'];
            delete headers['sec-fetch-dest'];

            let movedNext = false;
            const moveNext = () => {
                if (!movedNext) {
                    movedNext = true;
                    proxyToPort(idx + 1);
                }
            };

            const proxyReq = http.request({
                hostname: '127.0.0.1',
                port: routerPort,
                path: req.url,
                method: req.method,
                headers: headers,
                timeout: 3000
            }, (proxyRes) => {
                if (res.headersSent) return;
                try {
                    const respHeaders = { ...proxyRes.headers };
                    respHeaders['access-control-allow-origin'] = '*';
                    respHeaders['access-control-allow-methods'] = 'GET, POST, OPTIONS, PUT, DELETE';
                    respHeaders['access-control-allow-headers'] = 'Content-Type, Authorization, X-Requested-With';
                    res.writeHead(proxyRes.statusCode, respHeaders);
                    proxyRes.pipe(res);
                } catch (_) {}
            });

            proxyReq.on('error', () => {
                moveNext();
            });
            proxyReq.on('timeout', () => {
                try { proxyReq.destroy(); } catch (_) {}
                moveNext();
            });

            req.pipe(proxyReq);
        }

        proxyToPort(0);
        return true;
    }

    // 1. GET /api/apps (Catalog - 100% Plug & Play Dynamic)
    if (req.method === 'GET' && pathname === '/api/apps') {
        const apps = listApps();
        res.writeHead(200, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '0'
        });
        res.end(JSON.stringify({ success: true, count: apps.length, apps }));
        return true;
    }

    // 1e. GET /api/apps-stream (Server-Sent Events for Real-Time Instant Discovery)
    if (req.method === 'GET' && pathname === '/api/apps-stream') {
        res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        });
        const currentApps = listApps();
        res.write(`data: ${JSON.stringify({ type: 'INIT', count: currentApps.length, apps: currentApps })}\n\n`);

        appSseClients.add(res);
        req.on('close', () => {
            appSseClients.delete(res);
        });
        return true;
    }

    // 1b. GET /api/app-bundle/:appId (Self-contained inlined bundle for Canvas iframe)
    if (req.method === 'GET' && pathname.startsWith('/api/app-bundle/')) {
        const appId = pathname.replace(/^\/api\/app-bundle\//, '').trim();
        ensureAppEngine(appId);
        setActiveAppState(appId, 'app');
        const bundle = getAppBundle(appId);
        if (bundle) {
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
            res.end(bundle);
        } else {
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, error: 'App bundle not found: ' + appId }));
        }
        return true;
    }

    // 1c. GET /api/active-app & POST /api/active-app (Canvas App State Telemetry)
    if (pathname === '/api/active-app') {
        if (req.method === 'GET') {
            const current = getActiveAppState();
            res.writeHead(200, { 'Content-Type': 'application/json', 'access-control-allow-origin': '*' });
            res.end(JSON.stringify({ success: true, activeApp: current }));
            return true;
        }
        if (req.method === 'POST') {
            let body = '';
            req.on('data', chunk => { body += chunk; });
            req.on('end', () => {
                try {
                    const parsed = JSON.parse(body || '{}');
                    const updated = setActiveAppState(parsed.appId, parsed.view || (parsed.appId ? 'app' : 'closed'));
                    res.writeHead(200, { 'Content-Type': 'application/json', 'access-control-allow-origin': '*' });
                    res.end(JSON.stringify({ success: true, activeApp: updated }));
                } catch (err) {
                    res.writeHead(400, { 'Content-Type': 'application/json', 'access-control-allow-origin': '*' });
                    res.end(JSON.stringify({ success: false, error: err.message }));
                }
            });
            return true;
        }
    }

    // 1d. GET /api/active-chat (Inspect currently open chat in IDE)
    if (req.method === 'GET' && pathname === '/api/active-chat') {
        getActiveCdpPort().then(cdpPort => {
            fetch(`http://127.0.0.1:${cdpPort}/json/list`)
                .then(r => r.json())
                .then(list => {
                    const page = list.find(t => t.type === 'page' && t.webSocketDebuggerUrl);
                    const activeChatId = page ? ((page.url || '').match(/\/c\/([a-zA-Z0-9_-]+)/) || [])[1] || null : null;
                    res.writeHead(200, { 'Content-Type': 'application/json', 'access-control-allow-origin': '*' });
                    res.end(JSON.stringify({ success: true, activeChatId, pageUrl: page ? page.url : null }));
                })
                .catch(err => {
                    res.writeHead(500, { 'Content-Type': 'application/json', 'access-control-allow-origin': '*' });
                    res.end(JSON.stringify({ success: false, error: err.message }));
                });
        }).catch(err => {
            res.writeHead(500, { 'Content-Type': 'application/json', 'access-control-allow-origin': '*' });
            res.end(JSON.stringify({ success: false, error: err.message }));
        });
        return true;
    }

    // 2. GET /api/user (Profile Pipeline - SKILL_APP.md SSOT)
    if (req.method === 'GET' && (pathname === '/api/user' || pathname === '/api/sovereign-user')) {
        const root = path.resolve(__dirname, '..');
        const home = process.env.HOME || process.env.USERPROFILE || '';
        const possiblePaths = [
            path.join(root, 'portable-home', '.flowork', 'auth_vault.json'),
            path.join(root, '.flowork', 'auth_vault.json'),
            path.join(home, 'portable-home', '.flowork', 'auth_vault.json'),
            path.join(home, '.flowork', 'auth_vault.json')
        ];
        let user = { username: 'user', name: 'User', role: 'USER', tier: 'free', level: 1, badge: '👤 User', rank: 'User' };
        for (const p of possiblePaths) {
            if (fs.existsSync(p)) {
                try {
                    const vault = JSON.parse(fs.readFileSync(p, 'utf8'));
                    let claims = {};
                    if (vault.flowork_token) {
                        try {
                            const payloadB64 = vault.flowork_token.split('.')[1];
                            claims = JSON.parse(Buffer.from(payloadB64, 'base64url').toString('utf8'));
                        } catch (_) {}
                    }
                    const rawU = vault.flowork_user || {};
                    const role = (claims.role || rawU.role || 'USER').toUpperCase();
                    user = {
                        id: claims.sub || rawU.id || rawU.idunik || 'usr_' + (claims.username || rawU.username || 'user'),
                        username: claims.username || rawU.username || 'user',
                        name: rawU.name || rawU.displayName || claims.name || claims.username || rawU.username || 'User',
                        role: role,
                        tier: (claims.tier || rawU.tier || (role === 'SUPER_ADMIN' ? 'enterprise' : 'free')).toLowerCase(),
                        level: claims.level !== undefined ? claims.level : (rawU.level !== undefined ? rawU.level : (role === 'SUPER_ADMIN' ? 99 : 1)),
                        badge: claims.badge || rawU.badge || (role === 'SUPER_ADMIN' ? '👑 Admin' : '👤 User'),
                        rank: claims.rank || rawU.rank || (role === 'SUPER_ADMIN' ? 'Administrator' : 'User')
                    };
                    break;
                } catch (_) {}
            }
        }
        res.writeHead(200, { 'Content-Type': 'application/json', 'access-control-allow-origin': '*' });
        res.end(JSON.stringify({ success: true, user }));
        return true;
    }

    // Strict Origin Protection: Reject cross-site origin attacks on canvas control and prompt dispatch
    if (pathname === '/api/canvas/action' || pathname === '/api/canvas-ctl' || pathname === '/api/prompt-dispatch') {
        if (req.headers['sec-fetch-site'] === 'cross-site') {
            res.writeHead(403, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, error: '[FLOWORKOS:ERR_FORBIDDEN_ORIGIN] Cross-site request rejected.' }));
            return true;
        }
        const reqOrigin = req.headers.origin || req.headers.referer;
        if (reqOrigin) {
            try {
                const parsedOrigin = new URL(reqOrigin);
                const host = parsedOrigin.hostname.toLowerCase();
                const isLocal = host === 'localhost' || host === '127.0.0.1' || host === '::1' || host.endsWith('.localhost');
                const isFlowork = host === 'floworkos.com' || host.endsWith('.floworkos.com');
                if (!isLocal && !isFlowork) {
                    res.writeHead(403, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: false, error: '[FLOWORKOS:ERR_FORBIDDEN_ORIGIN] Unauthorized cross-origin request rejected.' }));
                    return true;
                }
            } catch (_) {
                res.writeHead(403, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: '[FLOWORKOS:ERR_FORBIDDEN_ORIGIN] Malformed origin header.' }));
                return true;
            }
        }
    }

    // 2b. POST /api/canvas/action (MCP Canvas Control Bridge - SKILL_APP.md)
    if (req.method === 'POST' && pathname === '/api/canvas/action') {
        let body = '';
        req.on('data', chunk => (body += chunk));
        req.on('end', async () => {
            try {
                const payload = JSON.parse(body || '{}');
                const action = payload.action;
                const cdpPort = await getActiveCdpPort();
                const resList = await fetch(`http://127.0.0.1:${cdpPort}/json/list`);
                const list = await resList.json();
                const page = list.find(t => t.type === 'page' && t.webSocketDebuggerUrl);

                if (!page) throw new Error('No active IDE page found via CDP');

                let expr = '';
                const safeAppId = String(payload.app_id || 'chess').replace(/[^a-zA-Z0-9_-]/g, '');
                if (action === 'open' || action === 'switch') {
                    expr = `window.openSovereignCanvas && window.openSovereignCanvas('app', ${JSON.stringify(safeAppId)})`;
                } else if (action === 'close') {
                    expr = `window.closeSovereignCanvas && window.closeSovereignCanvas()`;
                } else if (action === 'store' || action === 'list') {
                    expr = `window.openSovereignCanvas && window.openSovereignCanvas('store')`;
                }

                if (expr) {
                    const ws = new WebSocket(page.webSocketDebuggerUrl);
                    await new Promise((resolve) => {
                        ws.onopen = async () => {
                            const id = Math.floor(Math.random() * 1000000);
                            ws.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression: expr } }));
                            setTimeout(() => { ws.close(); resolve(); }, 300);
                        };
                        ws.onerror = () => resolve();
                    });
                }

                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: true, action, app_id: payload.app_id }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: err.message }));
            }
        });
        return true;
    }

    // 3. POST /api/prompt-dispatch (Direct In-Chat Bridge)
    if (req.method === 'POST' && pathname === '/api/prompt-dispatch') {
        const dispatchKey = req.headers['x-flowork-dispatch-key'];
        const authHeader = req.headers['authorization'] || '';
        const bearerToken = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : '';

        const isKeyValid = Boolean(dispatchKey && dispatchKey === INTERNAL_DISPATCH_SECRET);
        let isTokenValid = false;
        if (bearerToken) {
            try {
                const sg = require('./sovereign_gate');
                const v = sg.verifySovereignToken(bearerToken);
                if (v && v.valid) isTokenValid = true;
            } catch (_) {}
        }

        if (!isKeyValid && !isTokenValid) {
            res.writeHead(401, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: false,
                error: '[FLOWORKOS:ERR_AUTH_REQUIRED] Prompt dispatch requires valid dispatch key or authenticated sovereign session token.'
            }));
            return true;
        }

        let body = '';
        req.on('data', chunk => (body += chunk));
        req.on('end', async () => {
            try {
                const parsed = JSON.parse(body || '{}');
                const prompt = parsed.prompt || parsed.text || '';
                if (!prompt) throw new Error('No prompt text supplied in payload');
                
                const result = await dispatchPromptToMainChat(prompt, parsed.chatId);
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                    success: true,
                    message: 'Prompt dispatched directly to active chat.',
                    activeChatId: result.chatId
                }));
            } catch (err) {
                console.warn('[Canvas App Host] Prompt dispatch failure:', err.message);
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: err.message }));
            }
        });
        return true;
    }

    // 4. Static Apps GUI Serving: /apps/:appId/*
    if (pathname.startsWith('/apps/')) {
        const parts = pathname.replace(/^\/apps\//, '').split('/');
        const appId = parts[0];
        if (appId) {
            ensureAppEngine(appId);

            const relPath = parts.slice(1).join('/') || 'gui/index.html';
            const safeRelPath = path.normalize(relPath).replace(/^(\.\.[\/\\])+/, '');
            const targetFile = path.join(APPS_ROOT, appId, safeRelPath);

            if (fs.existsSync(targetFile) && fs.statSync(targetFile).isFile()) {
                const ext = path.extname(targetFile).toLowerCase();
                const mimeTypes = {
                    '.html': 'text/html; charset=utf-8',
                    '.css': 'text/css; charset=utf-8',
                    '.js': 'application/javascript; charset=utf-8',
                    '.json': 'application/json',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.svg': 'image/svg+xml',
                    '.ico': 'image/x-icon'
                };
                res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
                fs.createReadStream(targetFile).pipe(res);
                return true;
            }
        }
    }

    return false;
}

// ── CDP Sovereign Runtime Guardian ──
// Permanently injects layout protection and prevents text-area blocking across all restarts/reloads
async function startCdpGuardian() {
    console.log('[Canvas Guardian] 🛡️ Starting Autonomous CDP Runtime Guardian...');

    const GUARDIAN_PAYLOAD = "(function() { window.__FLOWORK_DISPATCH_SECRET__ = " + JSON.stringify(INTERNAL_DISPATCH_SECRET) + "; (" + (() => {
        // 1. Layout Protection Styles
        function ensureStyles() {
            let s = document.getElementById('flw-sovereign-layout-protection');
            if (!s) {
                s = document.createElement('style');
                s.id = 'flw-sovereign-layout-protection';
                (document.head || document.documentElement).appendChild(s);
            }
            const desired = [
                '[data-testid="running-items-panel"] { overflow: hidden !important; }',
                '[data-testid="running-items-panel"][class*="grid-rows-[0fr]"],',
                '[data-testid="running-items-panel"].grid-rows-\\[0fr\\] { pointer-events: none !important; visibility: hidden !important; overflow: hidden !important; max-height: 0px !important; height: 0px !important; }',
                '#floworkcore\\.agentSidePanelInputBox { position: relative !important; z-index: 30 !important; pointer-events: auto !important; }',
                'div[aria-label="Message input"] { pointer-events: auto !important; z-index: 31 !important; }'
            ].join('\n');
            if (s.textContent !== desired) {
                s.textContent = desired;
            }
        }
        ensureStyles();

        // 2. Direct DOM Enforcer on running-items-panel
        const panel = document.querySelector('[data-testid="running-items-panel"]');
        if (panel) {
            const isZero = (panel.className && panel.className.includes('grid-rows-[0fr]')) || panel.getBoundingClientRect().height === 0;
            if (isZero) {
                panel.style.setProperty('overflow', 'hidden', 'important');
                panel.style.setProperty('pointer-events', 'none', 'important');
                panel.style.setProperty('visibility', 'hidden', 'important');
            } else {
                panel.style.setProperty('overflow', 'hidden', 'important');
                panel.style.removeProperty('pointer-events');
                panel.style.removeProperty('visibility');
            }
        }

        // 3. Click-Redirect Guard on agentSidePanelInputBox
        const box = document.getElementById('floworkcore.agentSidePanelInputBox');
        if (box && !box.__flwFocusHooked) {
            box.__flwFocusHooked = true;
            box.addEventListener('mousedown', (e) => {
                const input = box.querySelector('div[aria-label="Message input"]');
                if (input && document.activeElement !== input) {
                    if (input.__lexicalEditor) {
                        try { input.__lexicalEditor.focus(); } catch (_) { input.focus(); }
                    } else {
                        input.focus();
                    }
                }
            }, true);
        }

        // 4. Monkey-patch window.dispatchPromptToChat to eliminate race conditions
        if (!window.__flwDispatchPatched) {
            window.__flwDispatchPatched = true;
            let lastDispatched = null;
            let lastTime = 0;
            window.dispatchPromptToChat = async function (promptText) {
                if (!promptText || typeof promptText !== 'string') return { success: false, error: 'EMPTY_PROMPT' };
                const now = Date.now();
                if (lastDispatched === promptText && (now - lastTime) < 1500) {
                    console.log('[FLOWORKOS:CANVAS] ⏳ Debounced rapid prompt dispatch');
                    return { success: true, debounced: true };
                }
                lastDispatched = promptText;
                lastTime = now;

                const activeChatId = window.getActiveChatId ? window.getActiveChatId() : null;
                try {
                    const res = await fetch('http://127.0.0.1:17700/api/prompt-dispatch', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Flowork-Dispatch-Key': window.__FLOWORK_DISPATCH_SECRET__ || ''
                        },
                        body: JSON.stringify({ prompt: promptText, chatId: activeChatId })
                    });
                    return await res.json();
                } catch (err) {
                    return { success: false, error: err.message };
                }
            };
        }
    }).toString() + ")(); })();";

    let isProcessing = false;
    async function tick() {
        if (isProcessing) return;
        isProcessing = true;
        try {
            const cdpPort = await getActiveCdpPort();
            if (!cdpPort) { isProcessing = false; return; }
            const res = await fetch("http://127.0.0.1:" + cdpPort + "/json/list");
            const list = await res.json();
            const pages = list.filter(t => t.type === 'page' && t.webSocketDebuggerUrl);

            for (const page of pages) {
                await new Promise((resolve) => {
                    try {
                        const ws = new WebSocket(page.webSocketDebuggerUrl);
                        let finished = false;
                        const done = () => {
                            if (!finished) {
                                finished = true;
                                try { ws.close(); } catch (_) {}
                                resolve();
                            }
                        };
                        const timer = setTimeout(done, 1500);

                        ws.onopen = () => {
                            let id = 1;
                            const sendCmd = (method, params = {}) => {
                                ws.send(JSON.stringify({ id: id++, method, params }));
                            };
                            sendCmd('Page.enable');
                            sendCmd('Page.addScriptToEvaluateOnNewDocument', { source: GUARDIAN_PAYLOAD });
                            sendCmd('Runtime.evaluate', { expression: GUARDIAN_PAYLOAD });
                            setTimeout(done, 300);
                        };
                        ws.onerror = done;
                    } catch (_) {
                        resolve();
                    }
                });
            }
        } catch (_) {
        } finally {
            isProcessing = false;
        }
    }

    tick();
    setInterval(tick, 2500);
}

function startStandalone(port = 17700) {
    const http = require('http');
    const server = http.createServer((req, res) => {
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Flowork-Dispatch-Key');
        if (req.method === 'OPTIONS') {
            res.writeHead(204);
            res.end();
            return;
        }
        const pathname = (req.url || '/').split('?')[0];
        if (handleRequest(req, res, pathname)) return;
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 404, error: 'Not found' }));
    });
    server.listen(port, '127.0.0.1', () => {
        console.log("[Canvas Sidecar Host] 🛸 Active on http://127.0.0.1:" + port);
        startCdpGuardian();
    });
    return server;
}

if (require.main === module) {
    startStandalone(17700);
}

module.exports = {
    getAppsRoot,
    listApps,
    ensureAppEngine,
    dispatchPromptToMainChat,
    handleRequest,
    startStandalone
};
