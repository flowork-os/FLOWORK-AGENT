// [FLOWORKOS:SOVEREIGN-LOCKED] Central Sovereign Switchboard & Request Router

const http = require('http');
const https = require('https');
const url = require('url');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { spawn } = require('child_process');

function isAllowedOrigin(origin) {
    if (!origin) return false;
    try {
        const u = new url.URL(origin);
        const host = u.hostname.toLowerCase();
        if (host === 'localhost' || host === '127.0.0.1' || host.endsWith('.localhost')) return true;
        if (host === 'floworkos.com' || host.endsWith('.floworkos.com')) return true;
        if (u.protocol === 'file:' || u.protocol === 'vscode-file:' || u.protocol === 'electron:') return true;
    } catch (_) {}
    return false;
}

function openUrlInBrowser(targetUrl) {
    if (!targetUrl || typeof targetUrl !== 'string') return false;
    
    // Strict URL validation: protocol must be http or https, no control characters or shell injection
    let parsed;
    try {
        parsed = new url.URL(targetUrl.trim());
    } catch (_) {
        console.warn('[Flowork Switchboard] 🛑 Blocked invalid URL format:', targetUrl);
        return false;
    }

    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        console.warn('[Flowork Switchboard] 🛑 Blocked disallowed protocol:', parsed.protocol);
        return false;
    }

    // Anti-Command Injection: Strictly reject shell metacharacters in URL on Windows & POSIX
    if (/[&|^%"`$\r\n\t<>]/.test(targetUrl)) {
        console.warn('[Flowork Switchboard] 🛑 Blocked URL containing shell metacharacters:', targetUrl);
        return false;
    }

    const safeUrl = parsed.href;
    console.log(`[Flowork Switchboard] 🌐 Opening validated URL in active browser: ${safeUrl}`);
    const realHome = (function() { try { return require('os').userInfo().homedir; } catch(_) { return process.env.HOME; } })();

    try {
        if (process.platform === 'win32') {
            // Use explorer.exe directly to launch the default browser without cmd.exe shell expansion risk
            spawn('explorer.exe', [safeUrl], { detached: true, stdio: 'ignore' }).unref();
        } else if (process.platform === 'darwin') {
            spawn('open', [safeUrl], { detached: true, stdio: 'ignore' }).unref();
        } else {
            const display = process.env.DISPLAY || ':0';
            const env = { ...process.env, HOME: realHome, DISPLAY: display };
            const child = spawn('xdg-open', [safeUrl], { detached: true, stdio: 'ignore', env });
            child.on('exit', () => {});
            child.on('close', () => {});
            child.on('error', () => {
                const fallback = spawn('gio', ['open', safeUrl], { detached: true, stdio: 'ignore', env });
                fallback.on('exit', () => {});
                fallback.on('close', () => {});
                fallback.on('error', () => {
                    const sb = spawn('sensible-browser', [safeUrl], { detached: true, stdio: 'ignore', env });
                    sb.on('exit', () => {});
                    sb.on('close', () => {});
                    sb.unref();
                });
                fallback.unref();
            });
            child.unref();
        }
        return true;
    } catch (err) {
        console.warn('[Flowork Switchboard] Failed to open browser safely:', err.message);
        return false;
    }
}

const sovereignGate = require('./sovereign_gate');
const toolVirtualizer = require('./tool_virtualizer');
const responseSanitizer = require('./response_sanitizer');
const accountRotator = require('./antygravity/account_rotator');
const canvasAppHost = require('./canvas_app_host');
let skillSeeder = null;
try {
    skillSeeder = require('./skill_seeder');
} catch (_) {}
const antygravity = require('./antygravity');
const bridgeDispatcher = require('./bridge/bridge_dispatcher');

// Register Sovereign Antygravity AI Engine
const providers = {
    sovereign: antygravity,
    antygravity: antygravity,
    google: antygravity
};

function getDynamicRouterPort() {
    if (process.env.FLOWORK_ROUTER_PORT) {
        const p = parseInt(process.env.FLOWORK_ROUTER_PORT, 10);
        if (!isNaN(p) && p > 0) return p;
    }
    const lsPort = process.env.FLOWORK_PORT;
    if (lsPort) {
        const lsP = parseInt(lsPort, 10);
        if (!isNaN(lsP) && lsP > 0) return lsP - 1987 + 9099;
    }
    return 9099;
}

const DEFAULT_PORT = getDynamicRouterPort();
const DEFAULT_HOST = '127.0.0.1';

/**
 * Sovereign Router State & Configuration
 */
let routerState = {
    authMode: 'flowork_passport',
    sovereignAuthUrl: 'https://auth.floworkos.com',
    appId: 'app_flw_482494a3e7d9',
    activeSessionToken: ''
};

function getPortableHome() {
    if (process.env.FLOWORK_PORTABLE_ROOT && typeof process.env.FLOWORK_PORTABLE_ROOT === 'string') {
        const pRoot = path.resolve(process.env.FLOWORK_PORTABLE_ROOT);
        const target = path.basename(pRoot) === 'portable-home' ? pRoot : path.join(pRoot, 'portable-home');
        if (!fs.existsSync(target)) {
            try { fs.mkdirSync(target, { recursive: true }); } catch (_) {}
        }
        return target;
    }
    if (process.env.FLOWORK_APP_DIR && typeof process.env.FLOWORK_APP_DIR === 'string') {
        const candidate = path.resolve(process.env.FLOWORK_APP_DIR, 'portable-home');
        if (!fs.existsSync(candidate)) {
            try { fs.mkdirSync(candidate, { recursive: true }); } catch (_) {}
        }
        return candidate;
    }
    const localCandidate = path.resolve(__dirname, '..', 'portable-home');
    if (!fs.existsSync(localCandidate)) {
        try { fs.mkdirSync(localCandidate, { recursive: true }); } catch (_) {}
    }
    return localCandidate;
}

function getVaultPath() {
    const pHome = getPortableHome();
    const floworkDir = path.join(pHome, '.flowork');
    if (!fs.existsSync(floworkDir)) {
        try { fs.mkdirSync(floworkDir, { recursive: true }); } catch (_) {}
    }
    return path.join(floworkDir, 'auth_vault.json');
}

function getAuthVaultCandidates() {
    const pHome = getPortableHome();
    const cwd = process.cwd();
    const up1 = path.resolve(__dirname, '..');
    const up2 = path.resolve(__dirname, '..', '..');
    const home = process.env.HOME || process.env.USERPROFILE || '';

    const candidates = [
        path.join(pHome, '.flowork', 'auth_vault.json'),
        path.join(pHome, '..', '.flowork', 'auth_vault.json'),
        path.join(cwd, 'portable-home', '.flowork', 'auth_vault.json'),
        path.join(cwd, '.flowork', 'auth_vault.json'),
        path.join(up1, 'portable-home', '.flowork', 'auth_vault.json'),
        path.join(up1, '.flowork', 'auth_vault.json'),
        path.join(up2, 'portable-home', '.flowork', 'auth_vault.json'),
        path.join(up2, '.flowork', 'auth_vault.json'),
        path.join(home, 'portable-home', '.flowork', 'auth_vault.json'),
        path.join(home, '.flowork', 'auth_vault.json')
    ];
    return [...new Set(candidates.filter(Boolean))];
}

const DEFAULT_VAULT = {
    active_provider: 'sovereign',
    providers: {
        sovereign: {
            connected: false,
            model: 'gemini-3.8-flash-high'
        }
    },
    flowork_token: '',
    flowork_user: null
};

function loadVault() {
    const vPath = getVaultPath();
    let vault = { ...DEFAULT_VAULT };
    let hasValidToken = false;

    if (fs.existsSync(vPath)) {
        try {
            const raw = fs.readFileSync(vPath, 'utf8');
            if (raw.trim()) {
                const parsed = JSON.parse(raw);
                vault = { ...DEFAULT_VAULT, ...parsed };
                if (vault.flowork_token && typeof vault.flowork_token === 'string' && vault.flowork_token.trim().length > 10) {
                    hasValidToken = true;
                }
            }
        } catch (_) {}
    }

    if (!hasValidToken) {
        const candidates = getAuthVaultCandidates();
        for (const cPath of candidates) {
            if (cPath === vPath || !fs.existsSync(cPath)) continue;
            try {
                const raw = fs.readFileSync(cPath, 'utf8');
                if (!raw.trim()) continue;
                const parsed = JSON.parse(raw);
                if (parsed && parsed.flowork_token && typeof parsed.flowork_token === 'string' && parsed.flowork_token.trim().length > 10) {
                    vault = { ...DEFAULT_VAULT, ...parsed };
                    hasValidToken = true;
                    // Auto-sync into active primary vault path
                    saveVault(vault);
                    console.log(`[Flowork Switchboard] 🔄 Auto-synced active sovereign session from: ${cPath} -> ${vPath}`);
                    break;
                }
            } catch (_) {}
        }
    }

    return vault;
}

function saveVault(vaultData) {
    const vPath = getVaultPath();
    const tmpPath = `${vPath}.${process.pid}.${Date.now()}.${Math.random().toString(36).slice(2, 8)}.tmp`;
    try {
        const toSave = {
            ...vaultData,
            last_updated: new Date().toISOString()
        };
        const dir = path.dirname(vPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(tmpPath, JSON.stringify(toSave, null, 2), { encoding: 'utf8', mode: 0o600 });
        try { fs.chmodSync(tmpPath, 0o600); } catch (_) {}
        fs.renameSync(tmpPath, vPath);
        try { fs.chmodSync(vPath, 0o600); } catch (_) {}
        return true;
    } catch (err) {
        try { if (fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath); } catch (_) {}
        console.error('[Flowork Switchboard Error]: Failed to save auth vault:', err.message);
        return false;
    }
}

/**
 * Validates sovereign engine authentication gate.
 * If token is an unverified cloud session from auth.floworkos.com, securely introspects
 * with upstream and exchanges it for a hardware/machine-locked local passport.
 */
async function ensureAuthenticatedGate(vault) {
    if (!vault) vault = loadVault();
    let gate = sovereignGate.checkEngineGate(vault);

    // If quarantine due to NO_TOKEN or invalid, re-check candidates once more
    if (!gate.authenticated && (!vault.flowork_token || gate.code === "NO_TOKEN")) {
        const freshVault = loadVault();
        if (freshVault.flowork_token && freshVault.flowork_token !== vault.flowork_token) {
            Object.assign(vault, freshVault);
            gate = sovereignGate.checkEngineGate(vault);
        }
    }

    if (!gate.authenticated && vault.flowork_token && vault.is_logged_out !== true) {
        try {
            const rawToken = vault.upstream_flowork_token || vault.flowork_token;
            const res = await fetch("https://auth.floworkos.com/api/auth/verify", {
                headers: { "Authorization": `Bearer ${rawToken}` },
                signal: AbortSignal.timeout(5000)
            });
            if (res.ok) {
                const data = await res.json();
                if (data && data.valid && data.user) {
                    const localPassport = sovereignGate.issueLocalSessionPassport(data.user);
                    vault.upstream_flowork_token = rawToken;
                    vault.flowork_token = localPassport;
                    vault.flowork_user = data.user;
                    saveVault(vault);
                    gate = sovereignGate.checkEngineGate(vault);
                    console.log(`[Flowork Switchboard] 🔑 Exchanged upstream cloud session for local machine passport (@${data.user.username}).`);
                }
            }
        } catch (_) {}
    }
    return gate;
}

// ── 🎫 OPAQUE SESSION TICKET MANAGEMENT (ZERO INFO-LEAK) ──
const sessionTickets = new Map();

function createSessionTicket(authUrl = '', targetPort = DEFAULT_PORT, customTicket = '') {
    const ticket = customTicket || ('flw_' + crypto.randomBytes(16).toString('hex'));
    const entry = {
        auth_url: authUrl || '',
        port: targetPort,
        created_at: Date.now(),
        expires_at: Date.now() + (30 * 60 * 1000)
    };
    sessionTickets.set(ticket, entry);
    try {
        const vault = loadVault();
        if (!vault.session_tickets) vault.session_tickets = {};
        vault.session_tickets[ticket] = entry;
        const now = Date.now();
        for (const [k, v] of Object.entries(vault.session_tickets)) {
            if (v.expires_at && v.expires_at < now) {
                delete vault.session_tickets[k];
            }
        }
        saveVault(vault);
    } catch (_) {}
    return ticket;
}

function resolveSessionTicket(ticket) {
    if (!ticket) return null;
    if (sessionTickets.has(ticket)) {
        const entry = sessionTickets.get(ticket);
        sessionTickets.delete(ticket);
        return entry;
    }
    try {
        const vault = loadVault();
        if (vault.session_tickets && vault.session_tickets[ticket]) {
            const entry = vault.session_tickets[ticket];
            delete vault.session_tickets[ticket];
            saveVault(vault);
            return entry;
        }
    } catch (_) {}
    return null;
}

/**
 * Creates Sovereign Router Server
 */
function createSovereignRouter(options = {}) {
    let port = options.port || DEFAULT_PORT;
    const host = options.host || DEFAULT_HOST;

    const server = http.createServer(async (req, res) => {
        const parsedUrl = url.parse(req.url, true);
        const pathname = parsedUrl.pathname;

        // Anti-DNS Rebinding: Validate Host Header strictly
        const hostHeader = (req.headers.host || '').split(':')[0].toLowerCase();
        if (hostHeader && hostHeader !== '127.0.0.1' && hostHeader !== 'localhost' && !hostHeader.endsWith('.localhost')) {
            res.writeHead(403, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({
                success: false,
                error: '[FLOWORKOS:ERR_FORBIDDEN_HOST] Invalid Host header for loopback router service.'
            }));
        }

        // Strict Origin Resolution & CORS Protection
        const reqOrigin = req.headers.origin;
        const originAllowed = isAllowedOrigin(reqOrigin);
        const secFetchSite = req.headers['sec-fetch-site'];
        const secFetchMode = req.headers['sec-fetch-mode'];
        const secFetchDest = req.headers['sec-fetch-dest'];

        if (reqOrigin) {
            if (originAllowed) {
                res.setHeader('Access-Control-Allow-Origin', reqOrigin);
                res.setHeader('Vary', 'Origin');
                if (req.headers['access-control-request-private-network']) {
                    res.setHeader('Access-Control-Allow-Private-Network', 'true');
                }
            } else {
                res.setHeader('Access-Control-Allow-Origin', 'null');
            }
        }
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');
        if (req.headers['access-control-request-private-network']) {
            res.setHeader('Access-Control-Allow-Private-Network', 'true');
        }

        if (req.method === 'OPTIONS') {
            res.writeHead((originAllowed || !reqOrigin) ? 200 : 403);
            return res.end();
        }

        // Strict Origin Protection: Reject unauthorized cross-origin requests targeting sensitive auth/control endpoints
        const isCallbackRoute = pathname === '/auth/flowork-callback' || pathname === '/auth/callback';
        const isTopLevelNavigation = (secFetchMode === 'navigate' || secFetchDest === 'document') && req.method === 'GET';

        if (!isCallbackRoute) {
            if ((reqOrigin && !originAllowed) || (secFetchSite === 'cross-site' && !originAllowed && !isTopLevelNavigation)) {
                if (pathname.startsWith('/auth/') || pathname.startsWith('/api/') || pathname.startsWith('/services/')) {
                    res.writeHead(403, { 'Content-Type': 'application/json' });
                    return res.end(JSON.stringify({
                        success: false,
                        error: '[FLOWORKOS:ERR_FORBIDDEN_ORIGIN] Unauthorized cross-origin request rejected.'
                    }));
                }
            }
        } else {
            // Callback routes: If Origin header is explicitly sent (e.g. CORS/fetch), ensure it is authorized
            if (reqOrigin && !originAllowed) {
                res.writeHead(403, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({
                    success: false,
                    error: '[FLOWORKOS:ERR_FORBIDDEN_ORIGIN] Unauthorized callback origin rejected.'
                }));
            }
        }

        // ========================================================
        // 1. TELEMETRY & AUTO-UPDATER SINKHOLES
        // ========================================================
        if (pathname.includes('/telemetry') || pathname.includes('/metrics') || pathname.includes('/stats') || pathname.includes('/error-report')) {
            res.writeHead(204, { 'Content-Type': 'application/json' });
            return res.end();
        }

        if (pathname.includes('/check-update') || pathname.includes('/updates/api') || pathname.includes('/release-notes')) {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({
                hasUpdate: false,
                version: '2.16.0',
                message: 'Flowork OS is running in sovereign pinned build mode.'
            }));
        }

        // ========================================================
        // 2. SOVEREIGN GATEKEEPER & PASSPORT AUTH ROUTES
        // ========================================================
        if (pathname === '/auth/status' || pathname === '/api/auth/status') {
            const vault = loadVault();
            const gate = await ensureAuthenticatedGate(vault);
            const folderName = process.env.FLOWORK_APP_NAME || 
                (process.env.FLOWORK_APP_DIR ? path.basename(process.env.FLOWORK_APP_DIR) : path.basename(path.resolve(__dirname, '..')));
            const folderSlug = process.env.FLOWORK_FOLDER_SLUG || folderName.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({
                authenticated: gate.authenticated,
                status: gate.status,
                token: vault.flowork_token || null,
                user: vault.flowork_user || gate.user || null,
                active_provider: vault.active_provider || 'sovereign',
                folder_name: folderName,
                folder_slug: folderSlug
            }));
        }

        if (pathname === '/system/info' || pathname === '/api/system/info') {
            const folderName = process.env.FLOWORK_APP_NAME || 
                (process.env.FLOWORK_APP_DIR ? path.basename(process.env.FLOWORK_APP_DIR) : path.basename(path.resolve(__dirname, '..')));
            const folderSlug = process.env.FLOWORK_FOLDER_SLUG || folderName.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({
                folder_name: folderName,
                folder_slug: folderSlug,
                app_dir: process.env.FLOWORK_APP_DIR || path.resolve(__dirname, '..')
            }));
        }

        // ========================================================
        // 2B. SOVEREIGN DYNAMIC SKILLS REGISTRY (1 Skill = 1 Folder)
        // ========================================================
        if (pathname === '/api/skills/list' || pathname === '/skills/list') {
            const candidateSkillDirs = [
                process.env.FLOWORK_SKILL_DIR,
                path.resolve(__dirname, '..', 'skills'),
                path.resolve(__dirname, '..', 'skill')
            ].filter(Boolean);
            let skillBaseDir = candidateSkillDirs[0];
            for (const cand of candidateSkillDirs) {
                if (fs.existsSync(cand)) {
                    skillBaseDir = cand;
                    break;
                }
            }
            try {
                if (!fs.existsSync(skillBaseDir) && skillSeeder && typeof skillSeeder.ensureSkillsSeeded === 'function') {
                    skillSeeder.ensureSkillsSeeded(skillBaseDir);
                }
            } catch (_) {}
            const results = [];
            if (fs.existsSync(skillBaseDir)) {
                try {
                    const skillFolderBase = path.basename(skillBaseDir);
                    const entries = fs.readdirSync(skillBaseDir, { withFileTypes: true });
                    for (const entry of entries) {
                        if (entry.isDirectory()) {
                            const manifestPath = path.join(skillBaseDir, entry.name, 'manifest.json');
                            let name = entry.name.toUpperCase();
                            let description = `Flowork Sovereign Skill: ${entry.name}`;
                            let runbook = 'SKILL.md';
                            if (fs.existsSync(manifestPath)) {
                                try {
                                    const m = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
                                    if (m.name) name = m.name.toUpperCase();
                                    if (m.description) description = m.description;
                                    if (m.runbook) runbook = m.runbook;
                                } catch (_) {}
                            }
                            results.push({
                                $typeName: "exa.flwctx_pb.WorkflowSpec",
                                name: name,
                                description: description,
                                path: `${skillFolderBase}/${entry.name}`,
                                content: `[FLOWORK_SKILL: /${name}]\nTarget Runbook: ${skillFolderBase}/${entry.name}/${runbook}\n\nOperational Instructions:\nRead and execute the complete SOP skill runbook from the Flowork OS directory: ${skillFolderBase}/${entry.name}/${runbook}.`
                            });
                        }
                    }
                } catch (scanErr) {
                    console.error('[Flowork Switchboard] Error scanning skills:', scanErr);
                }
            }
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify(results));
        }

        // ========================================================
        // 2C. SOVEREIGN ENGINE STATUS & PROVIDER CATALOG
        // ========================================================
        if (pathname === '/api/sys-pulse' || pathname === '/sys-pulse') {
            const pulse = (canvasAppHost && typeof canvasAppHost.getMultiOsSysPulse === 'function')
                ? canvasAppHost.getMultiOsSysPulse()
                : { success: true, timestamp: Date.now() };
            res.writeHead(200, {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
            });
            return res.end(JSON.stringify(pulse));
        }

        if (pathname === '/api/providers' || pathname === '/providers') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({
                success: true,
                active_provider: 'antygravity',
                providers: [{
                    id: 'antygravity',
                    alias: 'sovereign',
                    name: 'Antygravity Pro (Sovereign)',
                    category: 'official',
                    description: 'Official Sovereign Multi-Account Engine with Failover & Fair Rotator',
                    is_configured: true
                }]
            }));
        }

        if (pathname === '/auth/login-url' || pathname === '/auth/ticket' || pathname === '/api/auth/ticket' || (pathname === '/auth/ticket' && (req.method === 'POST' || req.method === 'GET'))) {
            const ticket = 'flw_tkt_' + Date.now().toString(36) + '_' + crypto.randomBytes(8).toString('hex');
            createSessionTicket('', port, ticket);
            const gateUrl = `https://auth.floworkos.com/?ticket=${ticket}&port=${port}`;

            const vault = loadVault();
            vault.last_ticket = ticket;
            vault.latest_oauth_request = {
                gate_url: gateUrl,
                port: port,
                ticket: ticket,
                timestamp: new Date().toISOString()
            };
            saveVault(vault);

            console.log(`[Flowork Switchboard] 🎫 Sovereign session ticket created: ${ticket}`);
            console.log(`    Gate URL : ${gateUrl}`);

            if (req.method === 'GET' && !parsedUrl.query.no_open && pathname !== '/api/auth/ticket') {
                openUrlInBrowser(gateUrl);
            }

            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({
                status: 'STARTED',
                ticket: ticket,
                gate_url: gateUrl,
                url: gateUrl,
                login_url: gateUrl,
                port: port
            }));
        }

        if (pathname === '/auth/open-browser') {
            if ((reqOrigin && !originAllowed) || (secFetchSite === 'cross-site' && !originAllowed)) {
                res.writeHead(403, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({ success: false, error: '[FLOWORKOS:ERR_FORBIDDEN_ORIGIN] Unauthorized open-browser request.' }));
            }
            const targetUrl = parsedUrl.query.url;
            const opened = openUrlInBrowser(targetUrl);
            if (!opened) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({ success: false, error: '[FLOWORKOS:ERR_INVALID_URL] Invalid URL or insecure protocol rejected.' }));
            }
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({ success: true, opened: targetUrl }));
        }

        if (pathname === '/auth/set-token' && req.method === 'POST') {
            let body = '';
            req.on('data', chunk => { body += chunk; });
            req.on('end', async () => {
                try {
                    const payload = JSON.parse(body || '{}');
                    const rawInput = (payload.flowork_token || payload.token || '').trim();
                    if (!rawInput) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        return res.end(JSON.stringify({ success: false, error: 'Token missing' }));
                    }

                    let verifyResult = sovereignGate.verifySovereignToken(rawInput);
                    if (!verifyResult.valid) {
                        try {
                            const introspectRes = await fetch("https://auth.floworkos.com/api/auth/verify", {
                                headers: { "Authorization": `Bearer ${rawInput}` },
                                signal: AbortSignal.timeout(5000)
                            });
                            if (introspectRes.ok) {
                                const verifyData = await introspectRes.json();
                                if (verifyData && verifyData.valid && verifyData.user) {
                                    const verifiedUser = verifyData.user;
                                    const localToken = sovereignGate.issueLocalSessionPassport(verifiedUser);
                                    verifyResult = {
                                        valid: true,
                                        user: verifiedUser,
                                        localPassportToken: localToken
                                    };
                                }
                            }
                        } catch (_) {}
                    }

                    if (!verifyResult.valid) {
                        res.writeHead(401, { 'Content-Type': 'application/json' });
                        return res.end(JSON.stringify({
                            success: false,
                            error: 'Invalid Sovereign Passport Token. Authentication failed.'
                        }));
                    }

                    const vault = loadVault();
                    vault.is_logged_out = false;
                    vault.flowork_token = verifyResult.localPassportToken || rawInput;
                    vault.upstream_flowork_token = rawInput;
                    vault.flowork_user = verifyResult.user;
                    saveVault(vault);
                    routerState.activeSessionToken = vault.flowork_token;

                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    return res.end(JSON.stringify({ 
                        success: true, 
                        message: 'Token verified and saved to sovereign vault', 
                        token: vault.flowork_token,
                        user: verifyResult.user
                    }));
                } catch (e) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    return res.end(JSON.stringify({ success: false, error: e.message }));
                }
            });
            return;
        }

        if (pathname === '/auth/logout') {
            if (req.method !== 'POST') {
                res.writeHead(405, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({ success: false, error: 'Method Not Allowed. Use POST.' }));
            }
            const vault = loadVault();
            vault.is_logged_out = true;
            vault.flowork_token = '';
            vault.flowork_user = null;
            if (vault.pending_oauth_sessions) {
                vault.pending_oauth_sessions = {};
            }
            saveVault(vault);
            routerState.activeSessionToken = '';

            try {
                const pHome = getPortableHome();
                const tokenCandidates = [
                    path.join(pHome, '.flowork', 'flowrk-standalone-oauth-token'),
                    path.join(pHome, '.flowork', 'dr.flow', 'flowrk-standalone-oauth-token')
                ];
                for (const jf of tokenCandidates) {
                    if (fs.existsSync(jf)) {
                        try { fs.unlinkSync(jf); } catch (_) {}
                    }
                }
            } catch (_) {}

            console.log('[Flowork Switchboard] 🚪 Logged out cleanly. Sovereign auth & tokens wiped.');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({ success: true, message: 'Sovereign session cleared and auth deleted' }));
        }

function syncStandaloneTokens() {
    try {
        const pHome = getPortableHome();
        const aVaultPath = path.join(pHome, '.flowork', 'account_pool.json');
        const fallbackVaultPath = path.join(__dirname, 'antygravity', 'vault.json');
        const targetPath = fs.existsSync(aVaultPath) ? aVaultPath : fallbackVaultPath;
        if (!fs.existsSync(targetPath)) return;
        const aVault = JSON.parse(fs.readFileSync(targetPath, 'utf8'));
        const gAuth = aVault.providers?.google || aVault.providers?.sovereign;
        if (!gAuth || !gAuth.access_token) return;

        const tokenPayload = {
            token: {
                access_token: gAuth.access_token,
                token_type: "Bearer",
                refresh_token: gAuth.refresh_token || "",
                expiry: gAuth.expires_at ? new Date(gAuth.expires_at).toISOString() : new Date(Date.now() + 3600000).toISOString()
            },
            auth_method: "consumer"
        };

        const targets = [
            path.join(pHome, '.flowork', 'flowrk-standalone-oauth-token'),
            path.join(pHome, '.flowork', 'dr.flow', 'flowrk-standalone-oauth-token'),
            path.join(pHome, '.flowork', 'drflow', 'flowrk-standalone-oauth-token'),
            path.join(pHome, '.flowork', 'profile_drflow_3', 'flowrk-standalone-oauth-token')
        ];

        for (const t of targets) {
            const dir = path.dirname(t);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
            fs.writeFileSync(t, JSON.stringify(tokenPayload, null, 2), { encoding: 'utf8', mode: 0o600 });
            try { fs.chmodSync(t, 0o600); } catch (_) {}
        }

        const v = loadVault();
        if (!v.providers) v.providers = {};
        v.providers.sovereign = {
            connected: true,
            email: gAuth.user_email || '',
            user_email: gAuth.user_email || '',
            access_token: gAuth.access_token,
            refresh_token: gAuth.refresh_token || '',
            model: gAuth.model || 'gemini-3.8-flash-high'
        };
        saveVault(v);
    } catch (e) {
        console.warn('[Flowork Switchboard] Failed to sync standalone tokens:', e.message);
    }
}

        // ========================================================
        // 2.5 MULTI-ACCOUNT ROUTER & TOKEN ROTATOR API
        // ========================================================
        if (pathname.startsWith('/auth/router/') || pathname.startsWith('/api/router/')) {
            const currentVault = loadVault();
            const gate = await ensureAuthenticatedGate(currentVault);
            if (!gate.authenticated) {
                res.writeHead(401, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({
                    error: {
                        code: 401,
                        status: 'UNAUTHENTICATED',
                        message: `[FLOWORKOS:ERR_AUTH_REQUIRED] ${gate.reason}`,
                        login_url: `http://127.0.0.1:${port}/auth/login-url`
                    }
                }));
            }
            const handled = await accountRotator.handleRouterRequest(req, res, parsedUrl, pathname, port);
            if (handled) return;
        }

        if (pathname === '/auth/callback' && parsedUrl.query.state && String(parsedUrl.query.state).startsWith('flw_multi_')) {
            const handled = await accountRotator.handleOAuthCallback(req, res, parsedUrl, port);
            if (handled) return;
        }

        // ========================================================
        // 3. PROVIDER MANAGEMENT ROUTES
        // ========================================================
        if (pathname === '/auth/providers' || pathname === '/auth/provider/list') {
            const currentVault = loadVault();
            const gate = await ensureAuthenticatedGate(currentVault);
            if (!gate.authenticated) {
                res.writeHead(401, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({
                    error: {
                        code: 401,
                        status: 'UNAUTHENTICATED',
                        message: `[FLOWORKOS:ERR_AUTH_REQUIRED] ${gate.reason}`,
                        login_url: `http://127.0.0.1:${port}/auth/login-url`
                    }
                }));
            }
            syncStandaloneTokens();
            const vault = loadVault();
            const aVault = (function() {
                try {
                    const pHome = getPortableHome();
                    const poolPath = path.join(pHome, '.flowork', 'account_pool.json');
                    if (fs.existsSync(poolPath)) return JSON.parse(fs.readFileSync(poolPath, 'utf8'));
                    const p = path.join(__dirname, 'antygravity', 'vault.json');
                    if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8'));
                } catch (_) {}
                return {};
            })();
            const gAuth = aVault.providers?.google || aVault.providers?.sovereign || vault.providers?.sovereign || {};
            const isSovConn = !!(gAuth.connected && (gAuth.access_token || gAuth.refresh_token));
            const sovEmail = gAuth.user_email || gAuth.email || '';
            const sovModel = gAuth.model || vault.providers?.sovereign?.model || 'gemini-3.8-flash-high';
            const active = 'sovereign';

            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({
                active_provider: 'sovereign',
                providers: {
                    sovereign: {
                        name: '⚡ Flowork Sovereign Core',
                        connected: isSovConn,
                        active: true,
                        email: sovEmail,
                        user_email: sovEmail,
                        model: sovModel
                    }
                }
            }));
        }

        if (pathname === '/auth/switch-provider' || pathname === '/auth/provider/switch') {
            const vault = loadVault();
            let target = (parsedUrl.query.provider || 'sovereign').toLowerCase();
            if (target === 'antygravity') target = 'sovereign';
            if (providers[target]) {
                vault.active_provider = target;
                saveVault(vault);
                console.log(`[Flowork Switchboard] 🔄 Switched active provider to: ${vault.active_provider}`);
                res.writeHead(200, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({
                    success: true,
                    active_provider: vault.active_provider,
                    message: `Active provider set to ${vault.active_provider}`
                }));
            } else {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({
                    success: false,
                    error: `Unknown provider: ${target}`
                }));
            }
        }

        // Check if route is specifically intended for Sovereign provider
        if (pathname.startsWith('/auth/sovereign/') || pathname.startsWith('/auth/provider/') || pathname.startsWith('/auth/upstream/')) {
            const activeMod = providers.sovereign;
            if (activeMod && typeof activeMod.handleRequest === 'function') {
                try {
                    const handled = await activeMod.handleRequest(req, res, parsedUrl, pathname, port);
                    if (handled) return;
                } catch (err) {
                    console.error('[Flowork Switchboard] Sovereign Core provider error:', err.message);
                }
            }
        }

        // Check OAuth Callback route (Supports both /auth/flowork-callback and /auth/callback)
        if (pathname === '/auth/flowork-callback' || pathname === '/auth/callback') {
            const floworkToken = parsedUrl.query.token || parsedUrl.query.flowork_token;
            const floworkUsername = parsedUrl.query.username || '';
            const ticket = parsedUrl.query.ticket || '';
            let continueTarget = parsedUrl.query.continue || '';

            if (ticket) {
                const sessionEntry = resolveSessionTicket(ticket);
                if (sessionEntry && sessionEntry.auth_url) {
                    continueTarget = sessionEntry.auth_url;
                    console.log(`[Flowork Switchboard] 🎫 Session ticket ${ticket} resolved to continue target.`);
                }
            }

            if (floworkToken) {
                let verifyResult = sovereignGate.verifySovereignToken(floworkToken);

                // Online Token Introspection with auth.floworkos.com (RFC 7662)
                // If local offline cryptographic check failed (e.g. HS256 issued by Cloudflare Auth Worker),
                // verify token authenticity authoritatively directly with auth.floworkos.com
                if (!verifyResult.valid) {
                    try {
                        const introspectRes = await fetch("https://auth.floworkos.com/api/auth/verify", {
                            headers: { "Authorization": `Bearer ${floworkToken}` },
                            signal: AbortSignal.timeout(5000)
                        });
                        if (introspectRes.ok) {
                            const verifyData = await introspectRes.json();
                            if (verifyData && verifyData.valid && verifyData.user) {
                                const verifiedUser = verifyData.user;
                                // Issue local machine-bound session passport so subsequent engine operations are 100% offline verified
                                const localToken = sovereignGate.issueLocalSessionPassport(verifiedUser);
                                verifyResult = {
                                    valid: true,
                                    user: verifiedUser,
                                    localPassportToken: localToken
                                };
                                console.log(`[Flowork Switchboard] 🌐 Online Token Verification SUCCESS with auth.floworkos.com for @${verifiedUser.username} (${verifiedUser.role})`);
                            }
                        }
                    } catch (introspectErr) {
                        console.warn("[Flowork Switchboard] Online token verification failed:", introspectErr.message);
                    }
                }

                if (verifyResult.valid) {
                    const vault = loadVault();
                    vault.is_logged_out = false;
                    // Prefer local Ed25519 passport for fail-closed offline kernel gate, preserve upstream token
                    vault.flowork_token = verifyResult.localPassportToken || floworkToken;
                    vault.upstream_flowork_token = floworkToken;
                    vault.flowork_user = verifyResult.user;
                    saveVault(vault);
                    routerState.activeSessionToken = vault.flowork_token;

                    // Sync to local provider pool if exists
                    try {
                        const pHome = getPortableHome();
                        const localPoolPath = path.join(pHome, '.flowork', 'account_pool.json');
                        if (fs.existsSync(localPoolPath)) {
                            const aVault = JSON.parse(fs.readFileSync(localPoolPath, 'utf8'));
                            aVault.flowork_token = floworkToken;
                            aVault.flowork_user = verifyResult.user;
                            fs.writeFileSync(localPoolPath, JSON.stringify(aVault, null, 2), { encoding: 'utf8', mode: 0o600 });
                            try { fs.chmodSync(localPoolPath, 0o600); } catch (_) {}
                        }
                    } catch (_) {}

                    console.log(`[Flowork Switchboard] ✅ Sovereign Passport verified for @${verifyResult.user.username} (${verifyResult.user.role})`);

                    // Trigger cloud vault pull on passport verification (instant sync on new machines)
                    if (accountRotator && typeof accountRotator.pullCloudVault === 'function') {
                        setImmediate(() => accountRotator.pullCloudVault());
                    }

                    if (continueTarget) {
                        res.writeHead(302, { 'Location': continueTarget });
                        return res.end();
                    }

                    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
                    return res.end(`<!DOCTYPE html><html><head><meta charset="utf-8"><title>Flowork OS Sovereign Passport</title><style>body{margin:0;background:#080B11;color:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;overflow:hidden}.card{background:#0F172A;border:1px solid rgba(239,68,68,0.4);border-radius:20px;padding:36px 44px;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.6),0 0 24px rgba(239,68,68,0.2);max-width:420px}h2{color:#EF4444;font-size:22px;font-weight:800;margin:0 0 8px}p{color:#94A3B8;font-size:13px;line-height:1.6;margin:0 0 16px}.user{color:#FFFFFF;font-weight:700}.badge{display:inline-block;background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.4);border-radius:999px;padding:4px 14px;font-size:11px;font-weight:700;color:#FCA5A5;margin-bottom:12px}</style></head><body><div class="card"><div class="badge">FLOWORK SOVEREIGN PASSPORT</div><h2>Sovereign Passport Verified!</h2><p>Welcome, <span class="user">@${verifyResult.user.username}</span>.<br>DR. FLOW engine session is now authenticated & active.<br>This window will close automatically.</p></div><script>setTimeout(() => window.close(), 1500);</script></body></html>`);
                } else {
                    console.warn(`[Flowork Switchboard] ⚠️ Sovereign token invalid:`, verifyResult.message);
                    res.writeHead(400, { "Content-Type": "application/json" });
                    return res.end(JSON.stringify({
                        success: false,
                        error: `[FLOWORKOS:ERR_TOKEN_INVALID] ${verifyResult.message}`
                    }));
                }
            }

            // Delegate external OAuth callback to Sovereign provider
            const activeMod = providers.sovereign;
            if (activeMod && typeof activeMod.handleRequest === 'function') {
                try {
                    const handled = await activeMod.handleRequest(req, res, parsedUrl, pathname, port);
                    if (handled) {
                        syncStandaloneTokens();
                        return;
                    }
                } catch (err) {
                    console.error('[Flowork Switchboard] OAuth callback dispatch error:', err.message);
                }
            }
        }

        // ========================================================
        // 4. MODULAR PROVIDER DISPATCHER & SOVEREIGN GATEKEEPER
        // ========================================================
        const currentVault = loadVault();

        // [FLOWORKOS:SOVEREIGN_GATE] Fail-Closed Auth Guard: Wajib login aktif auth.floworkos.com via portable-home.
        // Bebas level/tier: User, Free, Pro, Admin, Super_Admin semuanya lolos jika terotentikasi resmi.
        const gate = await ensureAuthenticatedGate(currentVault);
        if (!gate.authenticated) {
            console.warn(`[Flowork Switchboard] 🛑 Request to ${pathname} rejected: ${gate.reason}`);
            res.writeHead(401, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({
                error: {
                    code: 401,
                    status: 'UNAUTHENTICATED',
                    message: `[FLOWORKOS:ERR_AUTH_REQUIRED] ${gate.reason}`,
                    login_url: `http://127.0.0.1:${port}/auth/login-url`
                }
            }));
        }
        // Check for Custom Provider Bridge (:loadCodeAssist, GenerateContent, etc.)
        if (bridgeDispatcher.shouldHandle(pathname)) {
            try {
                return await bridgeDispatcher.handleRequest(req, res, parsedUrl, pathname, port);
            } catch (bridgeErr) {
                console.error('[Flowork Switchboard] Error in Custom Bridge Dispatcher:', bridgeErr.message);
            }
        }

        // Check for Cloud Code PA Mock Engine routes (handled by providers.sovereign directly)
        const isMockRoute = pathname.includes(':loadCodeAssist') ||
                            pathname.includes(':retrieveUserQuota') ||
                            pathname.includes('UserQuotaSummary') ||
                            pathname.includes(':listExperiments') ||
                            pathname.includes('/flwcoreNux') ||
                            pathname.includes('Nuxes') ||
                            pathname.includes('SurgeonNux') ||
                            pathname.includes(':fetchAvailableModels') ||
                            pathname.includes(':fetchUserInfo') ||
                            pathname.includes(':listModels');

        // Only actual AI generation calls should be dispatched to failover/rotation
        const isAiInference = !isMockRoute && (
            pathname.includes('GenerateContent') ||
            pathname.includes('generate') ||
            pathname.includes('predict') ||
            pathname.includes('countTokens')
        );
        if (isAiInference) {
            req.headers['accept-encoding'] = 'identity';
            const origWrite = res.write.bind(res);
            const origEnd = res.end.bind(res);

            res.write = function(chunk, encoding, callback) {
                if (chunk) {
                    try {
                        chunk = toolVirtualizer.translateChunkToNative(chunk);
                    } catch (_) {}
                    chunk = responseSanitizer.sanitizeStreamChunk(chunk);
                }
                return origWrite(chunk, encoding, callback);
            };

            res.end = function(chunk, encoding, callback) {
                if (chunk) {
                    try {
                        chunk = toolVirtualizer.translateChunkToNative(chunk);
                    } catch (_) {}
                    chunk = responseSanitizer.sanitizeStreamChunk(chunk);
                }
                return origEnd(chunk, encoding, callback);
            };
        }

        // Active Provider First
        const activeProviderKey = currentVault.active_provider || 'sovereign';
        if ((activeProviderKey === 'sovereign' || activeProviderKey === 'google') && isAiInference) {
            try {
                const handled = await accountRotator.handleAiRequestWithFailover(req, res, parsedUrl, pathname, port);
                if (handled) return;
            } catch (rotErr) {
                console.warn('[Flowork Switchboard] Account rotator failover notice, falling back to direct provider:', rotErr.message);
            }
        }

        const activeMod = providers[activeProviderKey] || providers.sovereign;
        if (activeMod && typeof activeMod.handleRequest === 'function') {
            try {
                const handled = await activeMod.handleRequest(req, res, parsedUrl, pathname, port);
                if (handled) return;
            } catch (err) {
                console.error(`[Flowork Switchboard] Error in active provider '${activeProviderKey}':`, err.message);
            }
        }

        // ========================================================
        // 4b. CANVAS MICRO-APPS & PROMPT DISPATCHER
        // ========================================================
        if (canvasAppHost.handleRequest(req, res, pathname, loadVault)) {
            return;
        }

        // ========================================================
        // 5. DEFAULT FALLBACK
        // ========================================================
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            floworkRouter: 'ACTIVE',
            route: pathname,
            message: 'Endpoint not handled by any registered provider in Flowork OS Switchboard.'
        }));
    });

    return {
        server,
        start: () => {
            return new Promise((resolve, reject) => {
                const tryListen = (targetPort) => {
                    const onError = (err) => {
                        if (err.code === 'EADDRINUSE') {
                            server.removeListener('error', onError);
                            const nextPort = targetPort + 1;
                            console.warn(`[Flowork Switchboard] Port ${targetPort} in use! Binding to next isolated port ${nextPort}...`);
                            tryListen(nextPort);
                        } else {
                            reject(err);
                        }
                    };
                    server.once('error', onError);
                    server.listen(targetPort, host, () => {
                        server.removeListener('error', onError);
                        port = targetPort;
                        console.log(`[Flowork Switchboard] Listening on http://${host}:${port}`);
                        resolve({ host, port });
                    });
                };
                tryListen(port);
            });
        },
        getState: () => ({ ...routerState }),
        setAuthMode: (mode) => { routerState.authMode = mode; }
    };
}

if (require.main === module) {
    const dynamicPort = getDynamicRouterPort();
    const inst = createSovereignRouter({ port: dynamicPort });
    inst.start().then(({ host, port }) => {
        console.log(`[Flowork Switchboard Standalone] Ready on http://${host}:${port}`);
    }).catch(err => {
        console.error('[Flowork Switchboard Standalone] Startup error:', err);
    });
}

module.exports = {
    createSovereignRouter,
    DEFAULT_PORT,
    DEFAULT_HOST,
    loadVault,
    saveVault,
    providers,
    refreshTokenIfNeeded: async (providerKey) => {
        const vault = loadVault();
        const pKey = providerKey || vault.active_provider || 'sovereign';
        const p = providers[pKey] || providers.sovereign;
        if (p && typeof p.refreshTokenIfNeeded === 'function') {
            return p.refreshTokenIfNeeded();
        }
    }
};
