// @lock: CONECTION/antygravity/router.js (SOVEREIGN LOCKED COMPONENT)

const https = require('https');
const url = require('url');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const googleServer = require('./google_server');
const config = googleServer.loadConfig();

const FLOW_CLIENT_ID = '[MANAGED_AT_EDGE_BY_FLOWORKOS]';
const ANTIGRAVITY_CLIENT_SECRET = '[MANAGED_BY_AUTH_FLOWORKOS_COM]';

function getFloworkToken() {
    try {
        const pHome = getPortableHome();
        const avPath = path.join(pHome, '.flowork', 'auth_vault.json');
        if (fs.existsSync(avPath)) {
            const av = JSON.parse(fs.readFileSync(avPath, 'utf8'));
            if (av.flowork_token) return av.flowork_token;
            if (av.flowork_user && av.flowork_user.token) return av.flowork_user.token;
        }
    } catch (_) {}
    return '';
}

// In-Memory PKCE Session Registry (state -> { verifier, provider, createdAt })
const pendingPkceSessions = new Map();

function getPortableHome() {
    if (process.env.FLOWORK_PORTABLE_ROOT) {
        const pRoot = path.resolve(process.env.FLOWORK_PORTABLE_ROOT);
        const target = path.basename(pRoot) === 'portable-home' ? pRoot : path.join(pRoot, 'portable-home');
        if (!fs.existsSync(target)) {
            try { fs.mkdirSync(target, { recursive: true }); } catch (_) {}
        }
        return target;
    }
    if (process.env.FLOWORK_APP_DIR) {
        const candidate = path.resolve(process.env.FLOWORK_APP_DIR, 'portable-home');
        if (!fs.existsSync(candidate)) {
            try { fs.mkdirSync(candidate, { recursive: true }); } catch (_) {}
        }
        return candidate;
    }
    const localCandidate = path.resolve(__dirname, '..', '..', 'portable-home');
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
    return path.join(floworkDir, 'account_pool.json');
}

function loadVault() {
    const vPath = getVaultPath();
    let vault = {
        active_provider: 'google',
        providers: {
            google: {
                access_token: '',
                refresh_token: '',
                expires_at: 0,
                client_id: FLOW_CLIENT_ID,
                user_email: '',
                upstream_endpoint: 'https://auth.floworkos.com/api/connector/proxy/cloudcode',
                connected: false
            }
        }
    };

    if (fs.existsSync(vPath)) {
        try {
            const raw = fs.readFileSync(vPath, 'utf8');
            vault = { ...vault, ...JSON.parse(raw) };
        } catch (_) {}
    }

    return vault;
}

function saveVault(vaultData) {
    const vPath = getVaultPath();
    try {
        const toSave = {
            ...vaultData,
            last_updated: new Date().toISOString()
        };
        fs.writeFileSync(vPath, JSON.stringify(toSave, null, 2), { encoding: 'utf8', mode: 0o600 });
        try { fs.chmodSync(vPath, 0o600); } catch (_) {}

        // Sync back to flowrk-standalone-oauth-token (matching binary flow string)
        const gAuth = toSave.providers?.google;
        if (gAuth && (gAuth.access_token || gAuth.refresh_token)) {
            const pHome = getPortableHome();
            const jContent = JSON.stringify({
                token: {
                    access_token: gAuth.access_token || '',
                    token_type: 'Bearer',
                    refresh_token: gAuth.refresh_token || '',
                    expiry: gAuth.expires_at ? new Date(gAuth.expires_at).toISOString() : new Date(Date.now() + 3600000).toISOString()
                },
                auth_method: 'consumer'
            }, null, 2);

            const candidateDirs = [
                path.join(pHome, '.flowork')
            ];

            for (const d of candidateDirs) {
                try {
                    if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
                    const tPath = path.join(d, 'flowrk-standalone-oauth-token');
                    fs.writeFileSync(tPath, jContent, { encoding: 'utf8', mode: 0o600 });
                    try { fs.chmodSync(tPath, 0o600); } catch (_) {}
                    const oldJ = path.join(d, 'jetski-standalone-oauth-token');
                    if (fs.existsSync(oldJ)) {
                        try { fs.unlinkSync(oldJ); } catch (_) {}
                    }
                } catch (_) {}
            }
        }
        return true;
    } catch (err) {
        console.error('[Antigravity Router] Failed to save vault:', err.message);
        return false;
    }
}

function parseJwtClaims(token) {
    if (!token || typeof token !== 'string') return null;
    try {
        const parts = token.split('.');
        if (parts.length >= 2) {
            const rawPayload = Buffer.from(parts[1], 'base64url').toString('utf8');
            return JSON.parse(rawPayload);
        }
    } catch (_) {}
    return null;
}

async function refreshGoogleTokenIfNeeded() {
    const vault = loadVault();
    const gAuth = vault.providers?.google;
    if (!gAuth || !gAuth.refresh_token) {
        return { refreshed: false, reason: 'NO_REFRESH_TOKEN' };
    }

    const now = Date.now();
    if (gAuth.expires_at && gAuth.expires_at - now > 5 * 60 * 1000) {
        return { refreshed: false, reason: 'TOKEN_STILL_VALID', access_token: gAuth.access_token };
    }

    return new Promise((resolve) => {
        // 1. Resolve Sovereign Session Passport Token
        let floworkToken = vault.flowork_token || '';
        if (!floworkToken) {
            try {
                const pHome = getPortableHome();
                const avPath = path.join(pHome, '.flowork', 'auth_vault.json');
                if (fs.existsSync(avPath)) {
                    const av = JSON.parse(fs.readFileSync(avPath, 'utf8'));
                    floworkToken = av.flowork_token || '';
                }
            } catch (_) {}
        }

        // 2. Route refresh via auth.floworkos.com (Zero Secret in Client)
        const postData = JSON.stringify({
            refreshToken: gAuth.refresh_token,
            provider: 'antigravity'
        });

        const req = https.request('https://auth.floworkos.com/api/auth/oauth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData),
                ...(floworkToken ? { 'Authorization': `Bearer ${floworkToken}` } : {})
            },
            timeout: 15000
        }, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(body);
                    if (json.success && (json.accessToken || json.access_token)) {
                        gAuth.access_token = json.accessToken || json.access_token;
                        gAuth.expires_at = Date.now() + (((json.expiresIn || json.expires_in) || 3600) * 1000);
                        saveVault(vault);
                        console.log('[Antigravity Router] ✅ Autonomous Google token refreshed via auth.floworkos.com.');
                        resolve({ refreshed: true, access_token: gAuth.access_token });
                    } else {
                        console.error('[Antigravity Router] Refresh token error response from auth.floworkos.com:', json);
                        resolve({ refreshed: false, error: json.error || json.message });
                    }
                } catch (e) {
                    resolve({ refreshed: false, error: e.message });
                }
            });
        });

        req.on('error', (err) => {
            console.error('[Antigravity Router] Request refresh token error:', err.message);
            resolve({ refreshed: false, error: err.message });
        });

        req.write(postData);
        req.end();
    });
}

async function exchangeGoogleOAuthCode(code, verifier, redirectUri) {
    // Sovereign Edge Broker Exchange (auth.floworkos.com)
    return new Promise((resolve) => {
        const floworkToken = getFloworkToken();

        const postData = JSON.stringify({
            code: code,
            verifier: verifier || "",
            code_verifier: verifier || "",
            provider: 'antigravity',
            redirectUri: redirectUri || 'http://localhost:8080/callback'
        });

        const req = https.request('https://auth.floworkos.com/api/auth/oauth/exchange', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData),
                ...(floworkToken ? { 'Authorization': `Bearer ${floworkToken}` } : {})
            },
            timeout: 15000
        }, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(body);
                    if (json.success && (json.accessToken || json.access_token)) {
                        return resolve({ success: true, tokens: {
                            access_token: json.accessToken || json.access_token,
                            refresh_token: json.refreshToken || json.refresh_token,
                            expires_in: json.expiresIn || 3600
                        } });
                    }
                    resolve({ success: false, error: json.error || 'Token exchange failed' });
                } catch (e) {
                    resolve({ success: false, error: e.message });
                }
            });
        });

        req.on('error', (err) => {
            resolve({ success: false, error: err.message });
        });

        req.write(postData);
        req.end();
    });
}

async function fetchGoogleUserInfo(accessToken) {
    return new Promise((resolve) => {
        const floworkToken = getFloworkToken();
        const req = https.request('https://auth.floworkos.com/api/connector/proxy/google/oauth2/v2/userinfo', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${floworkToken}`,
                'x-goog-access-token': accessToken,
                'User-Agent': 'FloworkOS/2.16.0'
            },
            timeout: 10000
        }, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(body);
                    resolve({ success: true, user: json });
                } catch (e) {
                    resolve({ success: false, error: e.message });
                }
            });
        });

        req.on('error', (err) => {
            resolve({ success: false, error: err.message });
        });

        req.end();
    });
}
// [FLOWORKOS:NANO-PLUG]
// Path: core/router/antigravity_router.js (Snippet Integration)
// Description: Updated handleAntigravityRequest with Sovereign Core aliases and model switcher.

async function handleAntigravityRequest(req, res, parsedUrl, pathname, serverPort = 9099) {
    // 1. Sovereign / Antigravity Auth Status
    if (pathname === '/auth/sovereign/status' || pathname === '/auth/antigravity/status' || pathname === '/auth/antigravity-status' ||
        (pathname === '/auth/provider/status' && (parsedUrl.query.provider === 'google' || parsedUrl.query.provider === 'sovereign' || !parsedUrl.query.provider))) {
        const vault = loadVault();
        const provData = vault.providers?.google || {};
        const isConnected = provData.connected !== false && !!(provData.refresh_token || provData.access_token);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            connected: isConnected,
            provider: 'sovereign',
            name: 'Sovereign Core',
            user_email: provData.user_email || '',
            has_token: !!provData.access_token,
            has_refresh_token: !!provData.refresh_token,
            expires_at: provData.expires_at || 0,
            model: provData.model || 'gemini-3.8-flash-high',
            providers: {
                google: {
                    name: 'Sovereign Core Upstream',
                    connected: isConnected,
                    user_email: provData.user_email || ''
                }
            }
        }));
        return true;
    }

    // 2. Sovereign / Antigravity Disconnect
    if ((pathname === '/auth/sovereign/disconnect' || pathname === '/auth/antigravity/disconnect' || pathname === '/auth/disconnect' ||
        (pathname === '/auth/provider/disconnect' && (parsedUrl.query.provider === 'google' || parsedUrl.query.provider === 'sovereign'))) &&
        (req.method === 'POST' || req.method === 'GET')) {
        const vault = loadVault();
        if (!vault.providers) vault.providers = {};
        if (!vault.providers.google) vault.providers.google = {};
        vault.providers.google.connected = false;
        vault.providers.google.access_token = '';
        vault.providers.google.refresh_token = '';
        vault.providers.google.expires_at = 0;
        saveVault(vault);
        console.log('[Antigravity Router] 🔴 Sovereign Core disconnected by user.');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            success: true,
            connected: false,
            provider: 'sovereign',
            message: 'Sovereign Core disconnected successfully'
        }));
        return true;
    }

    // 3. Sovereign / Antigravity Connect (Quick Reconnect)
    if ((pathname === '/auth/sovereign/connect' || pathname === '/auth/antigravity/connect' || pathname === '/auth/connect' ||
        (pathname === '/auth/provider/connect' && (parsedUrl.query.provider === 'google' || parsedUrl.query.provider === 'sovereign'))) &&
        (req.method === 'POST' || req.method === 'GET')) {
        const vault = loadVault();
        if (!vault.providers) vault.providers = {};
        if (!vault.providers.google) vault.providers.google = {};
        vault.providers.google.connected = true;
        if (vault.providers.google.refresh_token) {
            try {
                await refreshGoogleTokenIfNeeded();
            } catch (_) {}
        }
        saveVault(vault);
        console.log('[Antigravity Router] 🟢 Sovereign Core connected by user.');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            success: true,
            connected: true,
            provider: 'sovereign',
            message: 'Sovereign Core connected successfully'
        }));
        return true;
    }

    // 3.1 Sovereign Model Switcher
    if (pathname === '/auth/sovereign/model' || pathname === '/auth/antigravity/model') {
        const modelId = parsedUrl.query.model;
        if (modelId) {
            const vault = loadVault();
            if (!vault.providers) vault.providers = {};
            if (!vault.providers.google) vault.providers.google = {};
            vault.providers.google.model = modelId;
            saveVault(vault);
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: true, model: modelId }));
            return true;
        }
    }

    // 3.2 Dynamic Model Catalog Provider for UI & Extensions
    if (pathname === '/auth/router/models' || pathname === '/api/router/models' || pathname === '/api/models') {
        const catalog = googleServer.getModelCatalog();
        const vault = loadVault();
        const activeModel = vault.providers?.google?.model || catalog.defaultOverride || 'gemini-3.8-flash-high';
        res.writeHead(200, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        });
        res.end(JSON.stringify({
            success: true,
            active_model: activeModel,
            models: catalog.catalog || []
        }));
        return true;
    }

    // 4. Sovereign / Antigravity OAuth PKCE Login URL
    if (pathname === '/auth/sovereign/login-url' || pathname === '/auth/antigravity/login-url' || pathname === '/auth/google/login-url' ||
        (pathname === '/auth/provider/login-url' && (parsedUrl.query.provider === 'google' || parsedUrl.query.provider === 'sovereign' || !parsedUrl.query.provider))) {
        const verifier = crypto.randomBytes(32).toString('base64url');
        const challenge = crypto.createHash('sha256').update(verifier).digest('base64url');
        const state = 'flw_oa_' + serverPort + '_' + Date.now().toString(36) + '_' + crypto.randomBytes(8).toString('hex');

        pendingPkceSessions.set(state, {
            verifier: verifier,
            provider: 'google',
            createdAt: Date.now()
        });

        const vault = loadVault();
        if (!vault.pending_oauth_sessions) vault.pending_oauth_sessions = {};
        vault.pending_oauth_sessions[state] = {
            verifier: verifier,
            provider: 'google',
            createdAt: Date.now()
        };
        saveVault(vault);

        const redirectUri = `http://localhost:${serverPort}/auth/callback`;
        const loginUrl = `https://auth.floworkos.com/api/auth/oauth/init?provider=antygravity&state=${encodeURIComponent(state)}&redirectUri=${encodeURIComponent(redirectUri)}&codeChallenge=${encodeURIComponent(challenge)}`;
        console.log(`[Antigravity Router] 🔑 Generated Google OAuth2 PKCE URL on port ${serverPort}.`);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            success: true,
            provider: 'google',
            loginUrl: loginUrl,
            state: state
        }));
        return true;
    }

    // 5. Antigravity OAuth Callback
    const isAntigravityCallback = pathname === '/auth/callback' && (
        (parsedUrl.query.state && String(parsedUrl.query.state).startsWith('flw_oa_')) ||
        (parsedUrl.query.state && pendingPkceSessions.has(String(parsedUrl.query.state))) ||
        (parsedUrl.query.code && !parsedUrl.query.token)
    );

    if (isAntigravityCallback && req.method === 'GET') {
        const rawState = String(parsedUrl.query.state || '');
        const portMatch = rawState.match(/^flw_oa_(\d+)_/);
        if (portMatch) {
            const targetPort = parseInt(portMatch[1], 10);
            if (targetPort && targetPort !== serverPort) {
                console.log(`[Antigravity Router] 🔀 Relaying OAuth callback from port ${serverPort} to target instance port ${targetPort}...`);
                res.writeHead(302, { 'Location': `http://localhost:${targetPort}${req.url}` });
                res.end();
                return true;
            }
        }

        const errorParam = parsedUrl.query.error || parsedUrl.query.error_description;
        if (errorParam) {
            console.warn('[Antigravity Router] ⚠️ OAuth callback error:', errorParam);
            const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Flowork OS — Authorization Aborted</title>
  <style>
    body { margin: 0; background: #080205; color: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
    .card { background: #0d101d; border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 20px; padding: 40px 48px; text-align: center; box-shadow: 0 16px 40px -4px rgba(0, 0, 0, 0.85); max-width: 440px; width: 90%; }
    h1 { font-size: 20px; color: #EF4444; margin: 0 0 10px; font-weight: 700; }
    p { font-size: 14px; color: #94a3b8; line-height: 1.6; margin: 0 0 20px; }
    .btn { background: #15192c; color: #FFFFFF; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.1); padding: 10px 28px; border-radius: 9999px; cursor: pointer; font-size: 13px; }
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size: 40px; margin-bottom: 12px;">⚠️</div>
    <h1>Authorization Aborted</h1>
    <p>${errorParam}</p>
    <button class="btn" onclick="window.close()">Close Window</button>
  </div>
</body>
</html>`;
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
            res.end(html);
            return true;
        }

        const code = parsedUrl.query.code;
        const state = parsedUrl.query.state;

        if (!code) {
            res.writeHead(400, { 'Content-Type': 'text/plain' });
            res.end('Missing authorization code');
            return true;
        }

        const vault = loadVault();
        const session = pendingPkceSessions.get(state) || vault.pending_oauth_sessions?.[state];
        const verifier = session?.verifier || '';

        pendingPkceSessions.delete(state);
        if (vault.pending_oauth_sessions && vault.pending_oauth_sessions[state]) {
            delete vault.pending_oauth_sessions[state];
        }

        const redirectUri = `http://localhost:${serverPort}/auth/callback`;
        console.log(`[Antigravity Router] 🔄 Exchanging OAuth code with PKCE verifier...`);

        const exchangeResult = await exchangeGoogleOAuthCode(code, verifier, redirectUri);
        if (!exchangeResult.success || !exchangeResult.tokens?.access_token) {
            console.error('[Antigravity Router] ❌ OAuth exchange failed:', exchangeResult.error);
            const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Flowork OS — Token Exchange Failed</title>
  <style>
    body { margin: 0; background: #080205; color: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
    .card { background: #0d101d; border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 20px; padding: 40px 48px; text-align: center; box-shadow: 0 16px 40px -4px rgba(0, 0, 0, 0.85); max-width: 440px; width: 90%; }
    h1 { font-size: 20px; color: #EF4444; margin: 0 0 10px; font-weight: 700; }
    p { font-size: 14px; color: #94a3b8; line-height: 1.6; margin: 0 0 20px; }
    .btn { background: #15192c; color: #FFFFFF; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.1); padding: 10px 28px; border-radius: 9999px; cursor: pointer; font-size: 13px; }
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size: 40px; margin-bottom: 12px;">❌</div>
    <h1>Token Exchange Failed</h1>
    <p>${exchangeResult.error || 'Verification error encountered during sovereign gateway authentication.'}</p>
    <button class="btn" onclick="window.close()">Close Window</button>
  </div>
</body>
</html>`;
            res.writeHead(500, { 'Content-Type': 'text/html; charset=utf-8' });
            res.end(html);
            return true;
        }

        const tokens = exchangeResult.tokens;
        let userEmail = '';
        if (tokens.id_token) {
            const claims = parseJwtClaims(tokens.id_token);
            if (claims?.email) userEmail = claims.email;
        }
        if (!userEmail) {
            const userInfoResult = await fetchGoogleUserInfo(tokens.access_token);
            if (userInfoResult.success && userInfoResult.user?.email) {
                userEmail = userInfoResult.user.email;
            }
        }
        if (!userEmail) {
            userEmail = vault.providers?.google?.user_email || 'google_user@flowork.cloud';
        }

        if (!vault.providers) vault.providers = {};
        if (!vault.providers.google) vault.providers.google = {};

        vault.providers.google.connected = true;
        vault.providers.google.access_token = tokens.access_token;
        if (tokens.refresh_token) {
            vault.providers.google.refresh_token = tokens.refresh_token;
        }
        vault.providers.google.expires_at = Date.now() + ((tokens.expires_in || 3600) * 1000);
        vault.providers.google.user_email = userEmail;
        vault.providers.google.client_id = FLOW_CLIENT_ID;
        vault.active_provider = 'google';

        saveVault(vault);
        console.log(`[Antigravity Router] 🟢 OAuth Login Successful! User: ${userEmail}`);

        const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Flowork OS — Cloud Core AI Matrix Connected</title>
  <style>
    body { margin: 0; background: #080205; color: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; overflow: hidden; }
    .card { background: #0d101d; border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 20px; padding: 40px 48px; text-align: center; box-shadow: 0 16px 40px -4px rgba(0, 0, 0, 0.85); max-width: 460px; width: 90%; }
    .badge { font-size: 44px; margin-bottom: 12px; }
    h1 { font-size: 22px; color: #f59e0b; margin: 0 0 10px; font-weight: 700; letter-spacing: -0.02em; }
    p { font-size: 14px; color: #94a3b8; line-height: 1.6; margin: 0 0 20px; }
    .status-pill { display: inline-flex; align-items: center; gap: 8px; padding: 6px 16px; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 9999px; color: #f8fafc; font-size: 12px; font-weight: 600; margin-bottom: 24px; }
    .status-dot { width: 6px; height: 6px; background: #f59e0b; border-radius: 50%; box-shadow: 0 0 8px #f59e0b; }
    .btn { background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; font-weight: 700; border: none; padding: 10px 28px; border-radius: 9999px; cursor: pointer; font-size: 13px; transition: all 0.2s ease; outline: none; }
    .btn:hover { transform: scale(1.02); }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">⚡</div>
    <h1>Cloud Core AI Matrix Connected</h1>
    <div class="status-pill"><span class="status-dot"></span> Sovereign OAuth2 Verified</div>
    <p>Identity: <b style="color:#f59e0b;">${userEmail}</b><br>Session credentials successfully synchronized to Flowork OS.</p>
    <p style="font-size: 12px; color: #64748b; margin-bottom: 20px;">Return to Flowork OS workspace.<br>This window will close automatically.</p>
    <button class="btn" onclick="window.close()">Close Window</button>
  </div>
  <script>setTimeout(() => { try { window.close(); } catch(_) {} }, 2500);</script>
</body>
</html>`;
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(html);
        return true;
    }

    // 6. Cloud Code PA Mock Engine: loadCodeAssist
    if (pathname.includes(':loadCodeAssist')) {
        const vault = loadVault();
        const gAuth = vault.providers?.google || {};
        const isConnected = gAuth.connected !== false;

        if (!isConnected && !vault.flowork_token) {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                allowed: false,
                currentTier: null,
                reason: 'PROVIDER_DISCONNECTED'
            }));
            return true;
        }

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            allowed: true,
            cloudaicompanionProject: 'aicode-consumers',
            currentTier: {
                id: 'enterprise-tier',
                name: 'Flowork Enterprise Sovereign',
                description: 'Level 99 Super Admin Sovereign Surgery Suite',
                isDefault: true
            },
            allowedTiers: [
                {
                    id: 'enterprise-tier',
                    name: 'Flowork Enterprise Sovereign',
                    description: 'Level 99 Super Admin Sovereign Surgery Suite',
                    isDefault: true
                }
            ],
            gcpManaged: false,
            manageSubscriptionUri: 'https://auth.floworkos.com'
        }));
        return true;
    }

    // 7. Cloud Code PA Mock Engine: retrieveUserQuota & UserQuotaSummary
    if (pathname.includes(':retrieveUserQuota') || pathname.includes('UserQuotaSummary')) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            dailyQuota: '999999999',
            remainingQuota: '999999999',
            resetTime: '2099-01-01T00:00:00Z',
            allowed: true
        }));
        return true;
    }

    // 8. Cloud Code PA Mock Engine: listExperiments & NUXes
    if (pathname.includes(':listExperiments')) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            experimentIds: [],
            flags: []
        }));
        return true;
    }

    if (pathname.includes('/flwcoreNux') || pathname.includes('Nuxes') || pathname.includes('SurgeonNux')) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ flwcoreNuxes: [], flwcore_nuxes: [], nuxes: [] }));
        return true;
    }

    // 7.5 Local Model Catalog Dispatcher (:fetchAvailableModels / :listModels)
    if (pathname.includes(':fetchAvailableModels') || pathname.includes(':listModels')) {
        const vault = loadVault();
        const catalog = googleServer.getModelCatalog();
        const modelsMap = {};
        for (const m of (catalog.catalog || [])) {
            modelsMap[m.id] = {
                model_id: m.id,
                display_name: m.name || m.id,
                description: m.description || ''
            };
        }
        const activeModel = vault.providers?.google?.model || catalog.defaultOverride || 'gemini-3.8-flash-high';
        res.writeHead(200, { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        });
        res.end(JSON.stringify({
            models: modelsMap,
            default_agent_model_id: activeModel
        }));
        return true;
    }

    // 7.6 User Info Mock Dispatcher (:fetchUserInfo)
    if (pathname.includes(':fetchUserInfo') || pathname.includes('/fetchUserInfo')) {
        const vault = loadVault();
        const email = vault.providers?.google?.user_email || vault.providers?.google?.email || vault.providers?.sovereign?.user_email || vault.providers?.sovereign?.email || vault.flowork_user?.email || (vault.flowork_user?.username ? `${vault.flowork_user.username}@floworkos.com` : 'user@floworkos.com');
        const name = vault.flowork_user?.name || vault.flowork_user?.username || 'Flowork Operator';
        const tier = vault.flowork_user?.tier ? `${vault.flowork_user.tier}-tier` : 'enterprise-tier';
        res.writeHead(200, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        });
        res.end(JSON.stringify({
            user: {
                email: email,
                name: name,
                tier: tier
            }
        }));
        return true;
    }

    // 8. Upstream AI Gateway Reverse Proxy (Cloud Code PA & Gemini)
    const isUpstreamAiRequest = pathname.startsWith('/v1internal') ||
                                pathname.startsWith('/v1beta') ||
                                pathname.startsWith('/v1/') ||
                                pathname.includes('GenerateContent') ||
                                pathname.includes('generate') ||
                                pathname.includes('predict') ||
                                pathname.includes('/models/');

    if (isUpstreamAiRequest) {
        let vault = loadVault();
        let gAuth = vault.providers?.google || {};

        if (gAuth.connected === false && (!gAuth.access_token && !gAuth.refresh_token)) {
            try {
                const accountRotator = require('./account_rotator');
                await accountRotator.pullCloudVault();
                vault = loadVault();
                gAuth = vault.providers?.google || {};
            } catch (_) {}
        }

        if (gAuth.connected === false && (!gAuth.access_token && !gAuth.refresh_token)) {
            console.warn('[Antigravity Router] ⚠️ Request rejected: Antigravity is DISCONNECTED.');
            res.writeHead(503, { 
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            });
            res.end(JSON.stringify({
                error: {
                    code: 503,
                    message: 'Antigravity is currently disconnected. Reconnect via bottom profile menu.',
                    status: 'UNAVAILABLE'
                }
            }));
            return true;
        }

        let bearerToken = gAuth.access_token || '';
        if ((!bearerToken || (gAuth.expires_at && gAuth.expires_at - Date.now() < 60000)) && gAuth.refresh_token) {
            try {
                const refResult = await refreshGoogleTokenIfNeeded();
                if (refResult.access_token) {
                    bearerToken = refResult.access_token;
                }
            } catch (_) {}
        }

        const targetBaseUrl = (gAuth.upstream_endpoint && gAuth.upstream_endpoint.includes('auth.floworkos.com'))
            ? gAuth.upstream_endpoint
            : 'https://auth.floworkos.com/api/connector/proxy/cloudcode';
        const [rawSubPath, rawQuery] = (req.url || '').split('?');
        const targetUrl = new URL(targetBaseUrl);
        targetUrl.pathname = targetUrl.pathname.replace(/\/+$/, '') + '/' + (rawSubPath || '').replace(/^\/+/, '');
        if (rawQuery) targetUrl.search = '?' + rawQuery;

        const floworkToken = getFloworkToken();
        const proxyHeaders = { ...req.headers };
        proxyHeaders.host = targetUrl.host;
        proxyHeaders['user-agent'] = 'antigravity/2.8.1';
        if (targetBaseUrl.includes('auth.floworkos.com')) {
            if (floworkToken) {
                proxyHeaders['authorization'] = `Bearer ${floworkToken}`;
            }
            if (bearerToken) {
                proxyHeaders['x-goog-access-token'] = bearerToken;
            }
        } else if (bearerToken) {
            proxyHeaders['authorization'] = `Bearer ${bearerToken}`;
        }
        delete proxyHeaders['content-length'];
        delete proxyHeaders['accept-encoding'];
        delete proxyHeaders['x-goog-api-key'];

        let bodyChunks = [];
        req.on('data', chunk => bodyChunks.push(chunk));
        req.on('end', () => {
            let reqBody = Buffer.concat(bodyChunks);

            // Auto-inject project: "aicode-consumers" for fetchAvailableModels or listExperiments
            if (req.url.includes('fetchAvailableModels') || req.url.includes('listExperiments')) {
                try {
                    let p = reqBody.length > 0 ? JSON.parse(reqBody.toString('utf8')) : {};
                    if (!p.project) {
                        p.project = 'aicode-consumers';
                        reqBody = Buffer.from(JSON.stringify(p), 'utf8');
                    }
                } catch (_) {}
            }

            // Native engine request: inject sovereign user profile & active workspace into prompt
            if (/generatecontent/i.test(req.url) && reqBody.length > 0) {
                try {
                    let payload = JSON.parse(reqBody.toString('utf8'));
                    if (payload.request && !payload.project) {
                        payload.project = 'aicode-consumers';
                    }
                    // Zero MITM prompt injection: CONECTOR is 100% pass-through proxy

                    // Guarantee maxOutputTokens is at least 65536 to prevent premature MAX_TOKENS cutoff
                    const reqObj = payload.request || payload;
                    if (!reqObj.generationConfig) reqObj.generationConfig = {};
                    if (!reqObj.generationConfig.maxOutputTokens || reqObj.generationConfig.maxOutputTokens < 32768) {
                        reqObj.generationConfig.maxOutputTokens = 65536;
                    }

                    reqBody = Buffer.from(JSON.stringify(payload), 'utf8');
                } catch (_) {}
            }

            // Auto-adapt /v1beta/models/... standard Gemini API requests to Cloud Code PA format
            const v1betaMatch = req.url.match(/\/v1beta\/models\/([^:?]+):([^?]+)(\?.*)?/);
            const isV1Beta = !!v1betaMatch;
            let isV1BetaStream = false;
            let upstreamPath = req.url;

            if (isV1Beta) {
                let reqModel = v1betaMatch[1];
                const action = v1betaMatch[2];
                const qs = v1betaMatch[3] || '';
                isV1BetaStream = action.includes('stream');
                upstreamPath = `/v1internal:${action}${qs}`;
                function normalizeUpstreamModel(modelName) {
                    if (!modelName) return 'gemini-3.8-flash-high';
                    const m = String(modelName).toLowerCase();
                    if (m.startsWith('gemini-') || m.startsWith('claude-') || m.startsWith('gpt-')) {
                        return m;
                    }
                    return 'gemini-3.8-flash-high';
                }
                reqModel = normalizeUpstreamModel(reqModel);

                try {
                    let p = JSON.parse(reqBody.toString('utf8'));
                    if (!p.request) {
                        p = {
                            project: 'aicode-consumers',
                            model: reqModel,
                            request: {
                                contents: p.contents || [],
                                generationConfig: Object.assign({ maxOutputTokens: 65536 }, p.generationConfig),
                                systemInstruction: p.systemInstruction,
                                tools: p.tools,
                                toolConfig: p.toolConfig,
                                safetySettings: p.safetySettings
                            }
                        };
                        reqBody = Buffer.from(JSON.stringify(p), 'utf8');
                    }
                } catch (_) {}
            }

            proxyHeaders['content-length'] = reqBody.length;

            targetUrl = new URL(upstreamPath, targetBaseUrl);
            const proxyReq = https.request(targetUrl, {
                method: req.method,
                headers: proxyHeaders,
                timeout: 60000
            }, (proxyRes) => {
                const responseHeaders = { ...proxyRes.headers };
                responseHeaders['access-control-allow-origin'] = '*';
                responseHeaders['access-control-allow-methods'] = 'GET, POST, OPTIONS, PUT, DELETE';
                responseHeaders['access-control-allow-headers'] = '*';

                if (isV1Beta) {
                    delete responseHeaders['content-length'];
                    res.writeHead(proxyRes.statusCode, responseHeaders);

                    if (isV1BetaStream) {
                        proxyRes.on('data', chunk => {
                            const text = chunk.toString('utf8');
                            const unwrapped = text.replace(/^data:\s*(.*)$/gm, (match, jsonStr) => {
                                try {
                                    const obj = JSON.parse(jsonStr);
                                    if (obj && obj.response) {
                                        return 'data: ' + JSON.stringify(obj.response);
                                    }
                                } catch (_) {}
                                return match;
                            });
                            res.write(unwrapped);
                        });
                        proxyRes.on('end', () => res.end());
                    } else {
                        let respData = '';
                        proxyRes.on('data', c => { respData += c; });
                        proxyRes.on('end', () => {
                            try {
                                const parsed = JSON.parse(respData);
                                if (parsed && parsed.response) {
                                    return res.end(JSON.stringify(parsed.response));
                                }
                            } catch (_) {}
                            res.end(respData);
                        });
                    }
                } else {
                    res.writeHead(proxyRes.statusCode, responseHeaders);
                    proxyRes.pipe(res);
                }
            });

            proxyReq.on('error', (err) => {
                console.error('[Antigravity Router] Upstream request error:', err.message);
                if (!res.headersSent) {
                    res.writeHead(502, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: { code: 502, message: err.message, status: 'BAD_GATEWAY' } }));
                }
            });

            if (reqBody.length > 0) {
                proxyReq.write(reqBody);
            }
            proxyReq.end();
        });

        return true;
    }

    // 10. Google Telemetry & Mendel Flags Sinkhole
    if (pathname.startsWith('/v1/experiments') || pathname.startsWith('/log') || pathname.startsWith('/analytics') || pathname.includes('clearcut')) {
        res.writeHead(204, { 'Content-Type': 'application/json' });
        res.end();
        return true;
    }

    return false;
}

module.exports = {
    handleRequest: handleAntigravityRequest,
    loadVault,
    saveVault,
    refreshGoogleTokenIfNeeded,
    exchangeGoogleOAuthCode,
    fetchGoogleUserInfo
};
// @endlock
