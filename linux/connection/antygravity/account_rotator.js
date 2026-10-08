const https = require('https');
const url = require('url');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const googleServer = require('./google_server');
const config = googleServer.loadConfig();

const FLOW_CLIENT_ID = '[MANAGED_AT_EDGE_BY_FLOWORKOS]';
const ANTIGRAVITY_CLIENT_SECRET = '[MANAGED_BY_AUTH_FLOWORKOS_COM]';

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

function getAuthVaultCandidates() {
    const pHome = getPortableHome();
    const cwd = process.cwd();
    const up2 = path.resolve(__dirname, '..', '..');
    const up1 = path.resolve(__dirname, '..');
    const home = process.env.HOME || process.env.USERPROFILE || '';

    const candidates = [
        path.join(pHome, '.flowork', 'auth_vault.json'),
        path.join(pHome, '..', '.flowork', 'auth_vault.json'),
        path.join(cwd, 'portable-home', '.flowork', 'auth_vault.json'),
        path.join(cwd, '.flowork', 'auth_vault.json'),
        path.join(up2, 'portable-home', '.flowork', 'auth_vault.json'),
        path.join(up2, '.flowork', 'auth_vault.json'),
        path.join(up1, '.flowork', 'auth_vault.json'),
        path.join(home, '.flowork', 'auth_vault.json')
    ];
    return [...new Set(candidates.filter(Boolean))];
}

function getAuthVaultPath() {
    const candidates = getAuthVaultCandidates();
    for (const c of candidates) {
        if (fs.existsSync(c)) return c;
    }
    const pHome = getPortableHome();
    return path.join(pHome, '.flowork', 'auth_vault.json');
}

function getFloworkToken() {
    try {
        const avPath = getAuthVaultPath();
        if (fs.existsSync(avPath)) {
            const av = JSON.parse(fs.readFileSync(avPath, 'utf8'));
            if (av.flowork_token) return av.flowork_token;
            if (av.flowork_user && av.flowork_user.token) return av.flowork_user.token;
        }
        const vPath = getVaultPath();
        if (fs.existsSync(vPath)) {
            const v = JSON.parse(fs.readFileSync(vPath, 'utf8'));
            if (v.flowork_token) return v.flowork_token;
        }
    } catch (_) {}
    return '';
}

function getTombstonesPath() {
    const pHome = getPortableHome();
    const configDir = path.join(pHome, '.flowork', 'config');
    if (!fs.existsSync(configDir)) {
        try { fs.mkdirSync(configDir, { recursive: true }); } catch (_) {}
    }
    return path.join(configDir, 'sync_tombstones.json');
}

function loadTombstones() {
    const tPath = getTombstonesPath();
    if (fs.existsSync(tPath)) {
        try {
            return JSON.parse(fs.readFileSync(tPath, 'utf8'));
        } catch (_) {}
    }
    return { deleted_accounts: {} };
}

function saveTombstones(tb) {
    try {
        fs.writeFileSync(getTombstonesPath(), JSON.stringify(tb, null, 2), 'utf8');
        return true;
    } catch (_) {
        return false;
    }
}

function recordTombstone(accountId) {
    if (!accountId) return;
    try {
        const tb = loadTombstones();
        if (!tb.deleted_accounts) tb.deleted_accounts = {};
        tb.deleted_accounts[accountId] = Date.now();
        const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
        for (const [id, ts] of Object.entries(tb.deleted_accounts)) {
            if (ts < thirtyDaysAgo) delete tb.deleted_accounts[id];
        }
        saveTombstones(tb);
    } catch (e) {
        console.warn('[Account Rotator] Failed to record tombstone:', e.message);
    }
}

function removeTombstone(accountId) {
    if (!accountId) return;
    try {
        const tb = loadTombstones();
        if (tb.deleted_accounts && tb.deleted_accounts[accountId]) {
            delete tb.deleted_accounts[accountId];
            saveTombstones(tb);
        }
    } catch (_) {}
}

function isTombstoned(accountId) {
    if (!accountId) return false;
    const tb = loadTombstones();
    return Boolean(tb.deleted_accounts && tb.deleted_accounts[accountId]);
}

const MAX_ACCOUNTS = 100;
const COOLDOWN_DURATION_MS = 60 * 1000; // 60s cooldown on 429

// In-Memory PKCE Session Registry for Multi-Account (state -> { verifier, createdAt })
const pendingPkceSessions = new Map();

/**
 * Robust timestamp parser supporting epoch milliseconds, string numbers, and ISO 8601 strings.
 * Prevents NaN comparisons when cloud sync sends ISO dates.
 */
function parseTimestamp(ts) {
    if (!ts) return 0;
    if (typeof ts === 'number') return Number.isFinite(ts) ? ts : 0;
    if (typeof ts === 'string') {
        const parsedNum = Number(ts);
        if (!isNaN(parsedNum) && parsedNum > 0) return parsedNum;
        const parsedDate = Date.parse(ts);
        if (!isNaN(parsedDate) && parsedDate > 0) return parsedDate;
    }
    return 0;
}

function getVaultPath() {
    const pHome = getPortableHome();
    const floworkDir = path.join(pHome, '.flowork');
    if (!fs.existsSync(floworkDir)) {
        try { fs.mkdirSync(floworkDir, { recursive: true }); } catch (_) {}
    }
    return path.join(floworkDir, 'account_pool.json');
}

function getSessionBindingsPath() {
    const pHome = getPortableHome();
    const configDir = path.join(pHome, '.flowork', 'config');
    if (!fs.existsSync(configDir)) {
        try { fs.mkdirSync(configDir, { recursive: true }); } catch (_) {}
    }
    return path.join(configDir, 'session_bindings.json');
}

function loadSessionBindings() {
    const bPath = getSessionBindingsPath();
    if (fs.existsSync(bPath)) {
        try {
            return JSON.parse(fs.readFileSync(bPath, 'utf8'));
        } catch (_) {}
    }
    return {};
}

function saveSessionBindings(bindings) {
    const bPath = getSessionBindingsPath();
    try {
        fs.writeFileSync(bPath, JSON.stringify(bindings, null, 2), 'utf8');
        return true;
    } catch (e) {
        console.error('[Account Rotator] Failed to save session bindings:', e.message);
        return false;
    }
}

function getBindingForSession(sessionId) {
    if (!sessionId) return null;
    const bindings = loadSessionBindings();
    return bindings[sessionId] || null;
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
        },
        accounts: [],
        active_account_id: '',
        rotation_mode: 'failover' // 'failover' | 'round_robin'
    };

    if (fs.existsSync(vPath)) {
        try {
            const raw = fs.readFileSync(vPath, 'utf8');
            vault = { ...vault, ...JSON.parse(raw) };
        } catch (_) {}
    }

    ensureInitialized(vault);
    return vault;
}

function ensureInitialized(vault) {
    if (!Array.isArray(vault.accounts)) {
        vault.accounts = [];
    }
    if (!vault.rotation_mode) {
        vault.rotation_mode = 'failover';
    }

    // Auto-migrate legacy single account into accounts pool if empty
    const gAuth = vault.providers?.google;
    if (vault.accounts.length === 0 && gAuth && (gAuth.refresh_token || gAuth.access_token)) {
        const legacyEmail = gAuth.user_email || 'primary@floworkos.com';
        vault.accounts.push({
            id: 'acc_1',
            email: legacyEmail,
            name: legacyEmail.split('@')[0],
            access_token: gAuth.access_token || '',
            refresh_token: gAuth.refresh_token || '',
            expires_at: gAuth.expires_at || 0,
            client_id: gAuth.client_id || FLOW_CLIENT_ID,
            client_secret: gAuth.client_secret || ANTIGRAVITY_CLIENT_SECRET,
            status: 'active',
            cooldown_until: 0,
            requests_count: 0,
            errors_count: 0,
            added_at: new Date().toISOString(),
            last_used_at: new Date().toISOString()
        });
        vault.active_account_id = 'acc_1';
    }

    if (!vault.active_account_id && vault.accounts.length > 0) {
        vault.active_account_id = vault.accounts[0].id;
    }
}

function saveVault(vaultData, syncToCloud = false) {
    const vPath = getVaultPath();
    try {
        const toSave = {
            ...vaultData,
            last_updated: new Date().toISOString()
        };
        fs.writeFileSync(vPath, JSON.stringify(toSave, null, 2), { encoding: 'utf8', mode: 0o600 });
        try { fs.chmodSync(vPath, 0o600); } catch (_) {}

        // Sync active account to standalone token files
        syncActiveAccountTokens(toSave);

        // ONLY push to Cloudflare Sovereign Vault if structurally requested (account added/deleted)
        if (syncToCloud) {
            scheduleCloudPush();
        }

        return true;
    } catch (err) {
        console.error('[Account Rotator] Failed to save vault:', err.message);
        return false;
    }
}

let isPushingCloud = false;
let pendingCloudPush = false;
let cloudPushDebounceTimer = null;
let lastCloudPushErrorTime = 0;
const CLOUD_PUSH_BACKOFF_MS = 30000;

function scheduleCloudPush(delayMs = 2500) {
    if (cloudPushDebounceTimer) clearTimeout(cloudPushDebounceTimer);
    cloudPushDebounceTimer = setTimeout(() => {
        pushCloudVault();
    }, delayMs);
}

let syncDriveWatchTimer = null;

function getSyncDrivePath() {
    const pHome = getPortableHome();
    const floworkDir = path.join(pHome, '.flowork');
    if (!fs.existsSync(floworkDir)) {
        try { fs.mkdirSync(floworkDir, { recursive: true }); } catch (_) {}
    }
    return path.join(floworkDir, 'sync_drive.json');
}

function loadSyncDrive() {
    const sPath = getSyncDrivePath();
    if (fs.existsSync(sPath)) {
        try {
            return JSON.parse(fs.readFileSync(sPath, 'utf8'));
        } catch (_) {}
    }
    return { accounts: [], folders: [], status: 'unauthenticated' };
}

function saveSyncDrive(data, syncToCloud = false) {
    const sPath = getSyncDrivePath();
    try {
        fs.writeFileSync(sPath, JSON.stringify(data, null, 2), { encoding: 'utf8', mode: 0o600 });
        try { fs.chmodSync(sPath, 0o600); } catch (_) {}
        if (syncToCloud) {
            scheduleCloudPush();
        }
        return true;
    } catch (e) {
        console.error('[Sync Drive] Failed to save sync_drive.json:', e.message);
        return false;
    }
}

function getFloworkAuthToken() {
    return getFloworkToken();
}

async function pullCloudVault(explicitToken = null) {
    const token = explicitToken || getFloworkAuthToken();
    if (!token) return null;

    try {
        const result = await new Promise((resolve) => {
            const req = https.request('https://auth.floworkos.com/api/connector/vault', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'User-Agent': 'Flowork-Connector-Local/1.0'
                },
                timeout: 7000
            }, (res) => {
                let data = '';
                res.on('data', c => data += c);
                res.on('end', () => {
                    try { resolve(JSON.parse(data)); } catch (_) { resolve(null); }
                });
            });
            req.on('error', () => resolve(null));
            req.on('timeout', () => { req.destroy(); resolve(null); });
            req.end();
        });

        if (result && result.success && result.exists && result.vault) {
            const tombstones = loadTombstones();
            const deletedMap = tombstones.deleted_accounts || {};

            // Merge remote tombstones
            if (result.vault.tombstones && typeof result.vault.tombstones === 'object') {
                let tbChanged = false;
                for (const [tId, tTime] of Object.entries(result.vault.tombstones)) {
                    if (!deletedMap[tId]) {
                        deletedMap[tId] = tTime;
                        tbChanged = true;
                    }
                }
                if (tbChanged) {
                    saveTombstones(tombstones);
                }
            }

            const rawCloudAccounts = Array.isArray(result.vault.accounts) ? result.vault.accounts : [];
            const cloudAccounts = rawCloudAccounts.filter(a => a && a.id && !deletedMap[a.id]);
            const localVault = loadVault();
            const now = Date.now();
            let cooldownsUpdated = false;

            // Multi-Device Cooldown Merge: If another machine placed an account on cooldown, respect it locally
            if (Array.isArray(localVault.accounts) && localVault.accounts.length > 0) {
                for (const lAcc of localVault.accounts) {
                    const cAcc = cloudAccounts.find(c => c.id === lAcc.id);
                    if (cAcc && cAcc.cooldown_until) {
                        const cCool = parseTimestamp(cAcc.cooldown_until);
                        const lCool = parseTimestamp(lAcc.cooldown_until);
                        if (cCool > now) {
                            if (!lCool || lCool < cCool) {
                                lAcc.cooldown_until = cCool;
                                lAcc.status = 'cooldown';
                                cooldownsUpdated = true;
                            }
                        }
                    }
                }
                if (cooldownsUpdated) {
                    localVault.accounts.sort((a, b) => {
                        const aCool = (parseTimestamp(a.cooldown_until) > now) ? 1 : 0;
                        const bCool = (parseTimestamp(b.cooldown_until) > now) ? 1 : 0;
                        return aCool - bCool;
                    });
                }
            }

            let vaultUpdated = false;
            // 1. Restore Antigravity accounts if local accounts are empty
            if ((!Array.isArray(localVault.accounts) || localVault.accounts.length === 0) && cloudAccounts.length > 0) {
                console.log(`[Account Rotator] ☁️ Pulled & restored ${cloudAccounts.length} Antigravity accounts from Sovereign Cloud for @${result.userId}.`);
                localVault.accounts = cloudAccounts;
                localVault.active_account_id = result.vault.active_account_id || cloudAccounts[0]?.id || '';
                localVault.rotation_mode = result.vault.rotation_mode || localVault.rotation_mode || 'failover';
                
                if (!localVault.providers) localVault.providers = {};
                if (!localVault.providers.google) localVault.providers.google = {};
                localVault.providers.google.connected = true;
                localVault.providers.google.access_token = cloudAccounts[0]?.access_token || '';
                localVault.providers.google.refresh_token = cloudAccounts[0]?.refresh_token || '';
                localVault.providers.google.user_email = cloudAccounts[0]?.email || '';
                localVault.providers.google.upstream_endpoint = 'https://auth.floworkos.com/api/connector/proxy/cloudcode';

                // Sync to auth_vault.json
                try {
                    const avPath = getAuthVaultPath();
                    if (fs.existsSync(avPath)) {
                        const av = JSON.parse(fs.readFileSync(avPath, 'utf8'));
                        if (!av.providers) av.providers = {};
                        if (!av.providers.google) av.providers.google = {};
                        av.providers.google.connected = true;
                        av.providers.google.access_token = cloudAccounts[0]?.access_token || '';
                        av.providers.google.refresh_token = cloudAccounts[0]?.refresh_token || '';
                        av.providers.google.user_email = cloudAccounts[0]?.email || '';
                        fs.writeFileSync(avPath, JSON.stringify(av, null, 2), 'utf8');
                    }
                } catch (_) {}

                vaultUpdated = true;
            } else if (Array.isArray(localVault.accounts) && localVault.accounts.length > 0) {
                // Prune any accounts that are tombstoned
                const initialLen = localVault.accounts.length;
                localVault.accounts = localVault.accounts.filter(a => a && a.id && !deletedMap[a.id]);
                if (localVault.accounts.length !== initialLen) {
                    vaultUpdated = true;
                }
            } else if (cooldownsUpdated) {
                vaultUpdated = true;
            }

            if (vaultUpdated) {
                saveVault(localVault, false);
            }

            // 2. Restore Google Drive accounts
            try {
                const cloudDrive = result.vault.sync_drive || (Array.isArray(result.vault.gdrive_accounts) ? { accounts: result.vault.gdrive_accounts } : null);
                if (cloudDrive && Array.isArray(cloudDrive.accounts) && cloudDrive.accounts.length > 0) {
                    const driveAccounts = cloudDrive.accounts.filter(a => a && a.id && !deletedMap[a.id] && !deletedMap[a.email]);
                    const localSync = loadSyncDrive();
                    if (!localSync.accounts || localSync.accounts.length === 0) {
                        if (driveAccounts.length > 0) {
                            console.log(`[Sync Drive] ☁️ Pulled & restored ${driveAccounts.length} Google Drive accounts from Sovereign Cloud for @${result.userId}.`);
                            localSync.accounts = driveAccounts;
                            if (Array.isArray(cloudDrive.backup_folders)) localSync.backup_folders = cloudDrive.backup_folders;
                            if (Array.isArray(cloudDrive.folders)) localSync.folders = cloudDrive.folders;
                            localSync.status = 'active';
                            saveSyncDrive(localSync, false);
                        }
                    } else {
                        // Prune any drive accounts that are tombstoned
                        const initialDriveLen = localSync.accounts.length;
                        localSync.accounts = localSync.accounts.filter(a => a && a.id && !deletedMap[a.id] && !deletedMap[a.email]);
                        if (localSync.accounts.length !== initialDriveLen) {
                            saveSyncDrive(localSync, false);
                        }
                    }
                }
            } catch (dErr) {
                console.warn('[Sync Drive] Cloud drive restoration notice:', dErr.message);
            }

            // Asynchronously pull latest Cloud SOUL & Directives
            setImmediate(() => pullCloudSoul());
            return localVault;
        }
    } catch (e) {
        console.warn('[Account Rotator] Cloud vault pull skipped:', e.message);
    }
    return null;
}

async function pullCloudSoul() {
    try {
        const result = await new Promise((resolve) => {
            const req = https.request('https://auth.floworkos.com/api/connector/soul', {
                method: 'GET',
                headers: { 'User-Agent': 'Flowork-Connector-Local/1.0' },
                timeout: 5000
            }, (res) => {
                let data = '';
                res.on('data', c => data += c);
                res.on('end', () => {
                    try { resolve(JSON.parse(data)); } catch (_) { resolve(null); }
                });
            });
            req.on('error', () => resolve(null));
            req.on('timeout', () => { req.destroy(); resolve(null); });
            req.end();
        });
        if (result && result.success && Array.isArray(result.constitution)) {
            const pHome = getPortableHome();
            const sPath = path.join(pHome, '.flowork', 'cloud_soul.json');
            fs.writeFileSync(sPath, JSON.stringify(result, null, 2), 'utf8');
            return result;
        }
    } catch (_) {}
    return null;
}

function notifyCloudCooldown(accountId, cooldownUntil) {
    const token = getFloworkAuthToken();
    if (!token || !accountId) return;
    try {
        const payload = JSON.stringify({ account_id: accountId, cooldown_until: cooldownUntil });
        const req = https.request('https://auth.floworkos.com/api/connector/cooldown', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payload),
                'User-Agent': 'Flowork-Connector-Local/1.0'
            },
            timeout: 3000
        });
        req.on('error', () => {});
        req.write(payload);
        req.end();
    } catch (_) {}
}

function notifyCloudUsage(provider = 'google', model = 'gemini-3.8-flash-high', count = 1) {
    const token = getFloworkAuthToken();
    if (!token) return;
    try {
        const payload = JSON.stringify({ provider, model, count });
        const req = https.request('https://auth.floworkos.com/api/connector/usage', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payload),
                'User-Agent': 'Flowork-Connector-Local/1.0'
            },
            timeout: 3000
        });
        req.on('error', () => {});
        req.write(payload);
        req.end();
    } catch (_) {}
}

async function pushCloudVault(vaultData) {
    const token = getFloworkAuthToken();
    if (!token) return;

    if (isPushingCloud) {
        pendingCloudPush = true;
        return;
    }

    // Circuit Breaker: Avoid hammering Cloudflare if recent network/rate-limit error occurred
    if (Date.now() - lastCloudPushErrorTime < CLOUD_PUSH_BACKOFF_MS) {
        return;
    }

    isPushingCloud = true;

    try {
        const localVault = vaultData || loadVault();
        const syncDriveData = loadSyncDrive();
        const accountsList = Array.isArray(localVault.accounts) ? localVault.accounts : [];
        const driveAccountsList = Array.isArray(syncDriveData.accounts) ? syncDriveData.accounts : [];
        const tombstones = loadTombstones();
        const hasTombstones = Object.keys(tombstones.deleted_accounts || {}).length > 0;

        // Protection Guard: Never wipe remote cloud vault on a fresh uninitialized install (no accounts & no tombstones)
        if (accountsList.length === 0 && driveAccountsList.length === 0 && !hasTombstones) {
            console.log('[Account Rotator] 🛡️ Guard: Local accounts list is empty and no tombstones found, skipping push to avoid wiping cloud vault on fresh install.');
            return;
        }

        // Keep remote cloud payload lean and secure: Cloudflare D1 only needs refresh_token and metadata
        const sanitizedAccounts = accountsList.map(a => ({
            id: a.id,
            email: a.email,
            name: a.name,
            refresh_token: a.refresh_token,
            client_id: a.client_id || FLOW_CLIENT_ID,
            status: a.status || 'active',
            added_at: a.added_at,
            last_used_at: a.last_used_at
        }));

        const sanitizedDriveAccounts = driveAccountsList.map(a => ({
            id: a.id,
            email: a.email,
            name: a.name,
            refresh_token: a.refresh_token,
            status: a.status || 'active'
        }));

        const remoteVault = {
            active_provider: localVault.active_provider || 'google',
            rotation_mode: localVault.rotation_mode || 'failover',
            active_account_id: localVault.active_account_id || (accountsList[0]?.id || ''),
            accounts: sanitizedAccounts,
            sync_drive: {
                ...syncDriveData,
                accounts: sanitizedDriveAccounts
            },
            gdrive_accounts: sanitizedDriveAccounts,
            tombstones: tombstones.deleted_accounts || {},
            last_updated: new Date().toISOString()
        };

        const payload = JSON.stringify({ vault: remoteVault });
        await new Promise((resolve) => {
            const req = https.request('https://auth.floworkos.com/api/connector/vault', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(payload),
                    'User-Agent': 'Flowork-Connector-Local/1.0'
                },
                timeout: 8000
            }, (res) => {
                let data = '';
                res.on('data', c => data += c);
                res.on('end', () => {
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.success) {
                            lastCloudPushErrorTime = 0;
                            console.log(`[Account Rotator] ☁️ Sovereign Cloud synchronized (${accountsList.length} Antigravity, ${driveAccountsList.length} GDrive accounts).`);
                        } else {
                            console.warn('[Account Rotator] Cloud push notice:', parsed.error || data);
                        }
                    } catch (_) {}
                    resolve();
                });
            });
            req.on('error', (err) => {
                lastCloudPushErrorTime = Date.now();
                console.warn('[Account Rotator] Cloud push network error:', err.message);
                resolve();
            });
            req.on('timeout', () => {
                lastCloudPushErrorTime = Date.now();
                req.destroy();
                resolve();
            });
            req.write(payload);
            req.end();
        });
    } catch (e) {
        lastCloudPushErrorTime = Date.now();
        console.warn('[Account Rotator] Cloud push exception:', e.message);
    } finally {
        isPushingCloud = false;
        if (pendingCloudPush) {
            pendingCloudPush = false;
            scheduleCloudPush(2000);
        }
    }
}

let knownDriveAccountIds = new Set();
try {
    const initSync = loadSyncDrive();
    if (Array.isArray(initSync.accounts)) {
        initSync.accounts.forEach(a => { if (a && a.id) knownDriveAccountIds.add(a.id); });
    }
} catch (_) {}

function setupSyncDriveWatcher() {
    const sPath = getSyncDrivePath();
    const pDir = path.dirname(sPath);
    if (!fs.existsSync(pDir)) {
        try { fs.mkdirSync(pDir, { recursive: true }); } catch (_) {}
    }
    try {
        fs.watch(pDir, (eventType, filename) => {
            if (filename === 'sync_drive.json' || !filename) {
                if (syncDriveWatchTimer) clearTimeout(syncDriveWatchTimer);
                syncDriveWatchTimer = setTimeout(() => {
                    const currentSync = loadSyncDrive();
                    const currentAccounts = Array.isArray(currentSync.accounts) ? currentSync.accounts : [];
                    const currentIds = new Set(currentAccounts.map(a => a.id).filter(Boolean));
                    
                    // Detect if any drive accounts were deleted
                    let deletionsFound = false;
                    for (const oldId of knownDriveAccountIds) {
                        if (!currentIds.has(oldId)) {
                            recordTombstone(oldId);
                            deletionsFound = true;
                        }
                    }
                    knownDriveAccountIds = currentIds;

                    const token = getFloworkAuthToken();
                    if (token) {
                        scheduleCloudPush(deletionsFound ? 1000 : 2500);
                    }
                }, 1200);
            }
        });
    } catch (e) {
        console.warn('[Sync Drive] Watcher notice:', e.message);
    }
}

let lastKnownAuthToken = '';
let authVaultWatchTimer = null;

function setupAuthVaultWatcher() {
    const candidates = getAuthVaultCandidates();
    const watchedDirs = new Set();

    const onAuthVaultChange = () => {
        if (authVaultWatchTimer) clearTimeout(authVaultWatchTimer);
        authVaultWatchTimer = setTimeout(async () => {
            const currentToken = getFloworkToken();
            if (!currentToken) return;

            const localVault = loadVault();
            const localSync = loadSyncDrive();
            const isEmpty = (!localVault.accounts || localVault.accounts.length === 0) ||
                            (!localSync.accounts || localSync.accounts.length === 0);

            if (currentToken !== lastKnownAuthToken || isEmpty) {
                lastKnownAuthToken = currentToken;
                console.log('[Account Rotator] 🔑 Sovereign Passport authenticated! Checking & restoring accounts from cloud...');
                await pullCloudVault(currentToken);
            }
        }, 1000);
    };

    for (const cPath of candidates) {
        const dir = path.dirname(cPath);
        if (watchedDirs.has(dir)) continue;
        watchedDirs.add(dir);

        if (!fs.existsSync(dir)) {
            try { fs.mkdirSync(dir, { recursive: true }); } catch (_) {}
        }
        try {
            fs.watch(dir, (eventType, filename) => {
                if (!filename || filename === 'auth_vault.json') {
                    onAuthVaultChange();
                }
            });
        } catch (_) {}
    }
}

// Arm real-time file watchers
setupSyncDriveWatcher();
setupAuthVaultWatcher();

// On initial startup: If local accounts are empty and authenticated, pull once
setTimeout(() => {
    try {
        const localVault = loadVault();
        const localSync = loadSyncDrive();
        const isAntigravityEmpty = !localVault.accounts || localVault.accounts.length === 0;
        const isDriveEmpty = !localSync.accounts || localSync.accounts.length === 0;
        const token = getFloworkAuthToken();
        if ((isAntigravityEmpty || isDriveEmpty) && token) {
            pullCloudVault(token);
        }
    } catch (_) {}
}, 1000);

function syncActiveAccountTokens(vault) {
    try {
        let activeAcc = null;
        if (Array.isArray(vault.accounts) && vault.accounts.length > 0) {
            activeAcc = vault.accounts.find(a => a.id === vault.active_account_id) || vault.accounts[0];
        } else if (vault.providers?.google) {
            activeAcc = vault.providers.google;
        }

        if (!activeAcc || (!activeAcc.access_token && !activeAcc.refresh_token)) return;

        // Keep providers.google synchronized
        if (!vault.providers) vault.providers = {};
        vault.providers.google = {
            access_token: activeAcc.access_token || '',
            refresh_token: activeAcc.refresh_token || '',
            expires_at: activeAcc.expires_at || 0,
            user_email: activeAcc.email || activeAcc.user_email || '',
            client_id: activeAcc.client_id || FLOW_CLIENT_ID,
            client_secret: activeAcc.client_secret || ANTIGRAVITY_CLIENT_SECRET,
            upstream_endpoint: 'https://auth.floworkos.com/api/connector/proxy/cloudcode',
            connected: true
        };

        const pHome = getPortableHome();
        const tokenContent = JSON.stringify({
            token: {
                access_token: activeAcc.access_token || '',
                token_type: 'Bearer',
                refresh_token: activeAcc.refresh_token || '',
                expiry: activeAcc.expires_at ? new Date(activeAcc.expires_at).toISOString() : new Date(Date.now() + 3600000).toISOString()
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
                fs.writeFileSync(tPath, tokenContent, { encoding: 'utf8', mode: 0o600 });
                try { fs.chmodSync(tPath, 0o600); } catch (_) {}
            } catch (_) {}
        }
    } catch (e) {
        console.warn('[Account Rotator] Token sync notice:', e.message);
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

async function exchangeGoogleOAuthCode(code, verifier, redirectUri) {
    // Sovereign Edge Broker Exchange (auth.floworkos.com)
    return new Promise((resolve) => {
        const floworkToken = getFloworkToken();

        const postData = JSON.stringify({
            code: code,
            verifier: verifier || '',
            code_verifier: verifier || '',
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

async function refreshAccountToken(account, force = false) {
    if (!account || !account.refresh_token) {
        return { refreshed: false, reason: 'NO_REFRESH_TOKEN' };
    }

    const now = Date.now();
    if (!force && account.expires_at && account.expires_at - now > 5 * 60 * 1000) {
        return { refreshed: false, reason: 'TOKEN_STILL_VALID', access_token: account.access_token };
    }

    return new Promise((resolve) => {
        let floworkToken = '';
        try {
            const pHome = getPortableHome();
            const avPath = path.join(pHome, '.flowork', 'auth_vault.json');
            if (fs.existsSync(avPath)) {
                const av = JSON.parse(fs.readFileSync(avPath, 'utf8'));
                floworkToken = av.flowork_token || '';
            }
        } catch (_) {}

        const postData = JSON.stringify({
            refreshToken: account.refresh_token,
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
                        account.access_token = json.accessToken || json.access_token;
                        if (json.refreshToken || json.refresh_token) {
                            account.refresh_token = json.refreshToken || json.refresh_token;
                        }
                        account.expires_at = Date.now() + (((json.expiresIn || json.expires_in) || 3600) * 1000);
                        account.status = 'active';
                        account.error_message = '';
                        console.log(`[Account Rotator] ✅ Token refreshed via auth.floworkos.com for ${account.email} (valid for ${(json.expiresIn || json.expires_in || 3600)}s)`);
                        resolve({ refreshed: true, access_token: account.access_token });
                    } else {
                        console.error(`[Account Rotator] Refresh error for ${account.email}:`, json);
                        account.status = 'error';
                        account.error_message = json.error || 'Refresh failed';
                        resolve({ refreshed: false, error: account.error_message });
                    }
                } catch (e) {
                    resolve({ refreshed: false, error: e.message });
                }
            });
        });

        req.on('error', (err) => {
            console.error(`[Account Rotator] Network error refreshing ${account.email}:`, err.message);
            resolve({ refreshed: false, error: err.message });
        });

        req.write(postData);
        req.end();
    });
}

/**
 * Ensures an account token is completely valid and fresh before use.
 * If token expires in less than minMarginMs (default 5m), automatically refreshes.
 */
async function ensureAccountTokenValid(account, minMarginMs = 5 * 60 * 1000) {
    if (!account) return { valid: false, reason: 'NO_ACCOUNT' };
    const now = Date.now();
    if (account.access_token && account.expires_at && (account.expires_at - now > minMarginMs)) {
        return { valid: true, access_token: account.access_token };
    }
    if (!account.refresh_token) {
        return { valid: !!account.access_token, reason: 'NO_REFRESH_TOKEN', access_token: account.access_token };
    }
    const res = await refreshAccountToken(account, true);
    return { valid: res.refreshed || !res.error, access_token: account.access_token, details: res };
}

// ── Multi-Account PKCE Login URL Generation ──
async function generateLoginUrl(serverPort) {
    const verifier = crypto.randomBytes(32).toString('base64url');
    const challenge = crypto.createHash('sha256').update(verifier).digest('base64url');
    const state = 'flw_multi_' + serverPort + '_' + Date.now().toString(36) + '_' + crypto.randomBytes(6).toString('hex');

    pendingPkceSessions.set(state, {
        verifier: verifier,
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

    try {
        const initRes = await fetch('https://auth.floworkos.com/api/auth/oauth/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: 'antygravity',
                state,
                codeChallenge: challenge,
                redirectUri
            })
        });
        const initData = await initRes.json();
        if (initData && initData.authUrl) {
            return { loginUrl: initData.authUrl, state };
        }
    } catch (err) {
        console.warn('[Account Rotator] Could not obtain OAuth URL from auth.floworkos.com:', err.message);
    }

    const fallbackUrl = `https://auth.floworkos.com/api/auth/oauth/init?provider=antygravity&state=${encodeURIComponent(state)}&redirectUri=${encodeURIComponent(redirectUri)}&codeChallenge=${encodeURIComponent(challenge)}`;
    return { loginUrl: fallbackUrl, state };
}

// ── Process Multi-Account OAuth Callback ──
async function handleOAuthCallback(req, res, parsedUrl, serverPort) {
    const state = String(parsedUrl.query.state || '');
    const code = parsedUrl.query.code;
    const errorParam = parsedUrl.query.error || parsedUrl.query.error_description;

    if (errorParam) {
        console.warn('[Account Rotator] ⚠️ OAuth callback cancelled/failed:', errorParam);
        const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Flowork Router — Login Aborted</title><style>body{margin:0;background:#080205;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh}.card{background:#0d101d;border:1px solid rgba(239,68,68,0.35);border-radius:18px;padding:32px 40px;text-align:center;max-width:420px}h1{color:#ef4444;font-size:18px}.btn{background:#15192c;color:#fff;border:1px solid rgba(255,255,255,0.1);padding:8px 24px;border-radius:999px;cursor:pointer;margin-top:16px}</style></head><body><div class="card"><h1>Authorization Aborted</h1><p>${errorParam}</p><button class="btn" onclick="window.close()">Close Window</button></div></body></html>`;
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        return res.end(html);
    }

    if (!code) {
        res.writeHead(400, { 'Content-Type': 'text/plain' });
        return res.end('Missing authorization code');
    }

    const vault = loadVault();
    const session = pendingPkceSessions.get(state) || vault.pending_oauth_sessions?.[state];
    const verifier = session?.verifier || '';

    pendingPkceSessions.delete(state);
    if (vault.pending_oauth_sessions && vault.pending_oauth_sessions[state]) {
        delete vault.pending_oauth_sessions[state];
    }

    const redirectUri = `http://localhost:${serverPort}/auth/callback`;
    const exchangeResult = await exchangeGoogleOAuthCode(code, verifier, redirectUri);

    if (!exchangeResult.success || !exchangeResult.tokens?.access_token) {
        const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Flowork Router — Exchange Failed</title><style>body{margin:0;background:#080205;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh}.card{background:#0d101d;border:1px solid rgba(239,68,68,0.35);border-radius:18px;padding:32px 40px;text-align:center;max-width:420px}h1{color:#ef4444;font-size:18px}</style></head><body><div class="card"><h1>Token Exchange Failed</h1><p>${exchangeResult.error}</p><button onclick="window.close()">Close Window</button></div></body></html>`;
        res.writeHead(500, { 'Content-Type': 'text/html; charset=utf-8' });
        return res.end(html);
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
        userEmail = `pro_account_${vault.accounts.length + 1}@floworkos.com`;
    }

    // Check if account already exists
    let existingIndex = vault.accounts.findIndex(a => a.email.toLowerCase() === userEmail.toLowerCase());
    let accountObj = null;

    if (existingIndex >= 0) {
        accountObj = vault.accounts[existingIndex];
        accountObj.access_token = tokens.access_token;
        if (tokens.refresh_token) accountObj.refresh_token = tokens.refresh_token;
        accountObj.expires_at = Date.now() + ((tokens.expires_in || 3600) * 1000);
        accountObj.status = 'active';
        accountObj.cooldown_until = 0;
        accountObj.last_used_at = new Date().toISOString();
        console.log(`[Account Rotator] 🔄 Updated credentials for existing account: ${userEmail}`);
    } else {
        if (vault.accounts.length >= MAX_ACCOUNTS) {
            const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Flowork Router — Pool Full</title><style>body{margin:0;background:#080205;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh}.card{background:#0d101d;border:1px solid rgba(239,68,68,0.35);border-radius:18px;padding:32px 40px;text-align:center;max-width:440px}h1{color:#ef4444;font-size:18px}</style></head><body><div class="card"><h1>Account Pool Limit Reached</h1><p>Maximum capacity of ${MAX_ACCOUNTS} Antigravity Pro accounts reached. Please remove an inactive account before adding another.</p><button onclick="window.close()">Close</button></div></body></html>`;
            res.writeHead(400, { 'Content-Type': 'text/html; charset=utf-8' });
            return res.end(html);
        }

        accountObj = {
            id: 'acc_' + Date.now().toString(36) + '_' + crypto.randomBytes(3).toString('hex'),
            email: userEmail,
            name: userEmail.split('@')[0],
            access_token: tokens.access_token,
            refresh_token: tokens.refresh_token || '',
            expires_at: Date.now() + ((tokens.expires_in || 3600) * 1000),
            client_id: FLOW_CLIENT_ID,
            client_secret: ANTIGRAVITY_CLIENT_SECRET,
            status: 'active',
            cooldown_until: 0,
            requests_count: 0,
            errors_count: 0,
            added_at: new Date().toISOString(),
            last_used_at: new Date().toISOString()
        };
        vault.accounts.push(accountObj);
        console.log(`[Account Rotator] 🟢 Added new Antigravity account to pool: ${userEmail} (${vault.accounts.length}/${MAX_ACCOUNTS})`);
    }

    // Clear any previous tombstones for this account
    removeTombstone(accountObj.id);
    removeTombstone(userEmail);

    if (!vault.active_account_id) {
        vault.active_account_id = accountObj.id;
    }

    saveVault(vault, true);

    const totalAcc = vault.accounts.length;
    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Flowork OS — Antigravity Account Connected</title>
  <style>
    body { margin: 0; background: #080205; color: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; overflow: hidden; }
    .card { background: #0d101d; border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 20px; padding: 36px 44px; text-align: center; box-shadow: 0 16px 40px -4px rgba(0, 0, 0, 0.85), 0 0 20px rgba(16, 185, 129, 0.2); max-width: 440px; width: 90%; }
    .badge { font-size: 40px; margin-bottom: 8px; }
    h1 { font-size: 20px; color: #10b981; margin: 0 0 8px; font-weight: 700; }
    p { font-size: 13.5px; color: #94a3b8; line-height: 1.6; margin: 0 0 16px; }
    .pill { display: inline-flex; align-items: center; gap: 8px; padding: 5px 14px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 9999px; color: #34d399; font-size: 11.5px; font-weight: 700; margin-bottom: 20px; }
    .btn { background: linear-gradient(135deg, #10b981, #059669); color: #fff; font-weight: 700; border: none; padding: 9px 24px; border-radius: 9999px; cursor: pointer; font-size: 12.5px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">🔀</div>
    <h1>Account Linked to Router Pool</h1>
    <div class="pill">Pool Status: ${totalAcc} / ${MAX_ACCOUNTS} Accounts Active</div>
    <p>Identity: <b style="color:#f8fafc;">${userEmail}</b><br>Session tokens securely anchored in Sovereign Router Matrix.</p>
    <p style="font-size: 11.5px; color: #64748b; margin-bottom: 16px;">This window will close automatically in 2 seconds.</p>
    <button class="btn" onclick="window.close()">Close Window</button>
  </div>
  <script>setTimeout(() => { try { window.close(); } catch(_) {} }, 2200);</script>
</body>
</html>`;

    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(html);
    return true;
}

// ── Move Rate-Limited / Cooldown Account to the Tail (Urutan Paling Belakang) ──
function moveAccountToEnd(vault, accountId) {
    if (!vault || !Array.isArray(vault.accounts) || vault.accounts.length <= 1) return;
    const idx = vault.accounts.findIndex(a => a.id === accountId);
    if (idx !== -1 && idx < vault.accounts.length - 1) {
        const [limitedAcc] = vault.accounts.splice(idx, 1);
        vault.accounts.push(limitedAcc);
        console.log(`[Account Rotator] ⏩ Akun limit [${limitedAcc.email || accountId}] digeser ke antrean paling belakang.`);
    }
}

// ── Select Next Available Account for Inference ──
function getNextAvailableAccount(vault, excludeId = null) {
    const now = Date.now();
    let hasExpiredCooldown = false;
    for (const a of vault.accounts) {
        const coolUntil = parseTimestamp(a.cooldown_until);
        if (coolUntil > 0 && coolUntil <= now) {
            a.cooldown_until = 0;
            if (a.status === 'cooldown' || a.status === 'rate_limited') {
                a.status = 'active';
            }
            hasExpiredCooldown = true;
        } else if (coolUntil > 0 && typeof a.cooldown_until !== 'number') {
            a.cooldown_until = coolUntil;
        }
    }
    if (hasExpiredCooldown) {
        saveVault(vault);
    }

    const readyAccounts = vault.accounts.filter(a => {
        if (excludeId && a.id === excludeId) return false;
        if (a.status === 'error' || a.status === 'validation_required') return false;
        const coolUntil = parseTimestamp(a.cooldown_until);
        if (coolUntil > now) return false;
        return !!(a.access_token || a.refresh_token);
    });

    if (readyAccounts.length === 0) return null;

    // Failover: When excludeId is provided, ALWAYS pick the next ready account in circular sequence!
    if (excludeId) {
        let excludeIdx = vault.accounts.findIndex(a => a.id === excludeId || a.email === excludeId);
        if (excludeIdx === -1) excludeIdx = 0;
        let chosen = null;
        for (let i = 1; i <= vault.accounts.length; i++) {
            const checkIdx = (excludeIdx + i) % vault.accounts.length;
            const candidate = vault.accounts[checkIdx];
            if (readyAccounts.some(r => r.id === candidate.id)) {
                chosen = candidate;
                break;
            }
        }
        if (!chosen) chosen = readyAccounts[0];
        vault.active_account_id = chosen.id;
        saveVault(vault);
        return chosen;
    }

    if (vault.rotation_mode === 'round_robin') {
        const curIdx = readyAccounts.findIndex(a => a.id === vault.active_account_id);
        const nextIdx = (curIdx + 1) % readyAccounts.length;
        const chosen = readyAccounts[nextIdx];
        vault.active_account_id = chosen.id;
        saveVault(vault);
        return chosen;
    }

    // Failover mode: Prefer active account if ready and not excluded
    const active = readyAccounts.find(a => a.id === vault.active_account_id);
    if (active) return active;

    // Active account is cooling down or not ready; pick first ready and set active
    const nextActive = readyAccounts[0];
    vault.active_account_id = nextActive.id;
    saveVault(vault);
    return nextActive;
}

/**
 * Normalizes upstream Google / proxy payloads so candidates is always present at top-level
 * and guarantees every part has non-empty text or functionCall, preventing x-flow Rust binary
 * vector parser from encountering 0 valid parts ("No valid response or tool call returned by AI model").
 */
function formatSovereignPayload(rawObj, fallbackText = '') {
    if (!rawObj || typeof rawObj !== 'object') {
        const text = fallbackText || ' ';
        return {
            candidates: [{
                content: { role: 'model', parts: [{ text }] },
                finishReason: 'STOP',
                index: 0
            }],
            response: {
                candidates: [{
                    content: { role: 'model', parts: [{ text }] },
                    finishReason: 'STOP',
                    index: 0
                }]
            }
        };
    }

    const unwrapped = rawObj.response || rawObj;
    const finalPayload = {
        ...unwrapped,
        candidates: unwrapped.candidates || (rawObj.response && rawObj.response.candidates) || [],
        response: rawObj.response || unwrapped
    };

    if (Array.isArray(finalPayload.candidates) && finalPayload.candidates.length > 0) {
        for (const c of finalPayload.candidates) {
            if (c.content && Array.isArray(c.content.parts)) {
                for (const p of c.content.parts) {
                    // Critical for x-flow Rust binary: If part has no tool call and text is falsy,
                    // ensure non-empty whitespace so Rust vector extractor finds parts > 0!
                    if (!p.functionCall && (!p.text || p.text.length === 0)) {
                        p.text = ' ';
                    }
                }
            } else if (c.content && !c.content.parts) {
                c.content.parts = [{ text: ' ' }];
            }
        }
    } else {
        const text = fallbackText || ' ';
        finalPayload.candidates = [{
            content: { role: 'model', parts: [{ text }] },
            finishReason: 'STOP',
            index: 0
        }];
        finalPayload.response = { candidates: finalPayload.candidates };
    }

    return finalPayload;
}

// ── Upstream Request Forwarding with Intelligent Failover ──
async function handleAiRequestWithFailover(req, res, parsedUrl, pathname, serverPort) {
    // 0. Cloud Code PA Mock Engine Interceptors (never forward these to Google upstream!)
    if (pathname.includes(':loadCodeAssist')) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
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
    }

    if (pathname.includes(':retrieveUserQuota') || pathname.includes('UserQuotaSummary')) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            dailyQuota: '999999999',
            remainingQuota: '999999999',
            resetTime: '2099-01-01T00:00:00Z',
            allowed: true
        }));
    }

    if (pathname.includes(':listExperiments')) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ experimentIds: [], flags: [] }));
    }

    if (pathname.includes('/flwcoreNux') || pathname.includes('Nuxes') || pathname.includes('SurgeonNux')) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ flwcoreNuxes: [], flwcore_nuxes: [], nuxes: [] }));
    }

    if (pathname.includes(':fetchUserInfo') || pathname.includes('/fetchUserInfo')) {
        const vault = loadVault();
        const activeAcc = vault.accounts?.find(a => a.id === vault.active_account_id) || vault.accounts?.[0] || {};
        const email = activeAcc.email || vault.flowork_user?.email || (vault.flowork_user?.username ? `${vault.flowork_user.username}@floworkos.com` : 'user@floworkos.com');
        const name = activeAcc.name || vault.flowork_user?.name || vault.flowork_user?.username || 'Flowork Operator';
        const tier = vault.flowork_user?.tier ? `${vault.flowork_user.tier}-tier` : 'enterprise-tier';
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            user: {
                email: email,
                name: name,
                tier: tier
            }
        }));
    }

    const vault = loadVault();

    if (pathname.includes(':fetchAvailableModels') || pathname.includes(':listModels')) {
        const googleServer = require('./google_server');
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
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            models: modelsMap,
            default_agent_model_id: activeModel
        }));
    }

    if (!vault.accounts || vault.accounts.length === 0) {
        await pullCloudVault();
        vault = loadVault();
    }

    if (!vault.accounts || vault.accounts.length === 0) {
        return false; // Fall back to default single provider handler
    }

    // Buffer incoming request body
    const bodyChunks = [];
    req.on('data', chunk => bodyChunks.push(chunk));
    req.on('end', async () => {
        let reqBody = Buffer.concat(bodyChunks);

        let parsedPayload = null;
        try {
            parsedPayload = JSON.parse(reqBody.toString('utf8'));
        } catch (_) {}

        // Check for explicit session or account pinning
        const explicitAccId = (req.headers['x-flowork-account-id'] || parsedUrl.query?.account_id || '').toString().trim();
        let explicitSessionId = (req.headers['x-flowork-session-id'] || parsedUrl.query?.session_id || '').toString().trim();
        if (!explicitSessionId && parsedPayload) {
            explicitSessionId = (
                parsedPayload.sessionId ||
                parsedPayload.session_id ||
                parsedPayload.request?.sessionId ||
                parsedPayload.request?.session_id ||
                parsedPayload.metadata?.sessionId ||
                parsedPayload.client_metadata?.sessionId ||
                ''
            ).toString().trim();
        }

        let targetAccId = explicitAccId;
        let boundPolicy = 'fallback_pool'; // 'strict' | 'fallback_pool'
        if (!targetAccId && explicitSessionId) {
            const binding = getBindingForSession(explicitSessionId);
            if (binding && binding.account_id) {
                targetAccId = binding.account_id;
                boundPolicy = binding.failover_policy || 'fallback_pool';
            }
        }

        let isPinnedAccount = false;
        let account = null;

        if (targetAccId && targetAccId !== 'combo' && targetAccId !== 'auto') {
            const found = vault.accounts.find(a => a.id === targetAccId || a.email.toLowerCase() === targetAccId.toLowerCase());
            if (found) {
                const now = Date.now();
                const coolUntil = parseTimestamp(found.cooldown_until);
                if (coolUntil > 0 && coolUntil <= now) {
                    found.cooldown_until = 0;
                    found.status = 'active';
                }
                if (found.status === 'cooldown' || (coolUntil && coolUntil > now)) {
                    if (boundPolicy === 'strict') {
                        console.warn(`[Account Rotator] 🔒 Dedicated pinned account [${found.email}] is on cooldown (strict policy).`);
                        res.writeHead(429, { 'Content-Type': 'application/json' });
                        return res.end(JSON.stringify({
                            error: {
                                code: 429,
                                message: `Dedicated Antigravity Pro account [${found.email}] is on quota cooldown until ${new Date(coolUntil).toLocaleTimeString()}. Strict policy is active.`,
                                status: 'RESOURCE_EXHAUSTED'
                            }
                        }));
                    } else {
                        console.warn(`[Account Rotator] 🔀 Dedicated account [${found.email}] is on cooldown. Falling back to pooled account...`);
                    }
                } else {
                    account = found;
                    isPinnedAccount = true;
                    console.log(`[Account Rotator] 📌 Routing session traffic via dedicated account [${account.email}] (policy: ${boundPolicy})`);
                }
            }
        }

        if (!account) {
            account = getNextAvailableAccount(vault);
            if (!account) {
                // Check if any cooldown accounts have just expired
                const now = Date.now();
                for (const a of vault.accounts) {
                    const coolUntil = parseTimestamp(a.cooldown_until);
                    if (coolUntil > 0 && coolUntil <= now) {
                        a.cooldown_until = 0;
                        a.status = 'active';
                    }
                }
                account = getNextAvailableAccount(vault);
            }
        }

        if (!account) {
            const isStream = req.url.includes('stream') || (req.headers.accept && req.headers.accept.includes('text/event-stream'));
            res.writeHead(200, { 'Content-Type': isStream ? 'text/event-stream' : 'application/json' });
            const msg = `[Flowork Engine Notice] Seluruh ${vault.accounts.length} akun inferensi sedang antre sejenak. Silakan kirim ulang pesan Anda dalam beberapa detik.`;
            const fallbackObj = formatSovereignPayload(null, msg);
            if (isStream) {
                res.write(`data: ${JSON.stringify(fallbackObj)}\n\n`);
                return res.end();
            } else {
                return res.end(JSON.stringify(fallbackObj));
            }
        }

        // Proactive Pre-Flight Token Validation (> 3 minutes remaining)
        let tokenCheck = await ensureAccountTokenValid(account, 3 * 60 * 1000);
        if (!tokenCheck.valid) {
            console.warn(`[Account Rotator] Initial account [${account.email}] token invalid/unrefreshable:`, tokenCheck.reason || tokenCheck.details?.error);
            const fallback = getNextAvailableAccount(vault, account.id);
            if (fallback) {
                account = fallback;
                await ensureAccountTokenValid(account, 3 * 60 * 1000);
            }
        }
        saveVault(vault);

        // Inject sovereign prompt & user profile if GenerateContent
        if (/generatecontent/i.test(req.url) && reqBody.length > 0) {
            try {
                let payload = JSON.parse(reqBody.toString('utf8'));
                if (payload.request && !payload.project) {
                    payload.project = 'aicode-consumers';
                }
                // Zero MITM prompt injection: CONECTOR is 100% pass-through proxy
                try {
                    const toolVirtualizer = require('../tool_virtualizer');
                    payload = toolVirtualizer.virtualizeToolsInPayload(payload);
                } catch (_) {}
                // Guarantee maxOutputTokens is at least 65536 to prevent premature MAX_TOKENS cutoff
                const reqObj = payload.request || payload;
                if (!reqObj.generationConfig) reqObj.generationConfig = {};
                if (!reqObj.generationConfig.maxOutputTokens || reqObj.generationConfig.maxOutputTokens < 32768) {
                    reqObj.generationConfig.maxOutputTokens = 65536;
                }

                reqBody = Buffer.from(JSON.stringify(payload), 'utf8');
            } catch (_) {}
        } else if ((req.url.includes('fetchAvailableModels') || req.url.includes('listExperiments')) && reqBody.length > 0) {
            try {
                let p = JSON.parse(reqBody.toString('utf8'));
                if (!p.project) {
                    p.project = 'aicode-consumers';
                    reqBody = Buffer.from(JSON.stringify(p), 'utf8');
                }
            } catch (_) {}
        }

        // Clean & sanitize ide_type so Google protobuf parser never rejects FLOWORKCORE with 400
        let bodyStr = reqBody.toString('utf8');
        if (bodyStr.includes('"ide_type"')) {
            bodyStr = bodyStr.replace(/"ide_type"\s*:\s*"[^"]*"/g, '"ide_type":"ANTIGRAVITY"');
            reqBody = Buffer.from(bodyStr, 'utf8');
        }

        // Auto-adapt /v1beta/models/... standard Gemini API requests to Cloud Code PA format
        const v1betaMatch = req.url.match(/\/v1beta\/models\/([^:?]+):([^?]+)(\?.*)?/);
        const isV1Beta = !!v1betaMatch;
        let isV1BetaStream = false;
        let upstreamPath = req.url;

        function normalizeUpstreamModel(modelName) {
            if (!modelName) return 'gemini-3.8-flash-high';
            const m = String(modelName).toLowerCase();
            if (m.startsWith('gemini-') || m.startsWith('claude-') || m.startsWith('gpt-')) {
                return m;
            }
            return 'gemini-3.8-flash-high';
        }

        if (isV1Beta) {
            let reqModel = v1betaMatch[1];
            const action = v1betaMatch[2];
            const qs = v1betaMatch[3] || '';
            isV1BetaStream = action.includes('stream');
            upstreamPath = `/v1internal:${action}${qs}`;

            try {
                let p = JSON.parse(reqBody.toString('utf8'));
                const safeModel = normalizeUpstreamModel(p.model || reqModel);
                if (!p.request) {
                    p = {
                        project: 'aicode-consumers',
                        model: safeModel,
                        request: {
                            contents: p.contents || [],
                            generationConfig: Object.assign({ maxOutputTokens: 65536 }, p.generationConfig),
                            systemInstruction: p.systemInstruction,
                            tools: p.tools,
                            toolConfig: p.toolConfig,
                            safetySettings: p.safetySettings
                        }
                    };
                } else {
                    p.model = safeModel;
                }
                reqBody = Buffer.from(JSON.stringify(p), 'utf8');
            } catch (_) {}
        } else {
            try {
                let p = JSON.parse(reqBody.toString('utf8'));
                if (p.model) {
                    p.model = normalizeUpstreamModel(p.model);
                    reqBody = Buffer.from(JSON.stringify(p), 'utf8');
                }
            } catch (_) {}
        }

        // Proactive Context Shield: Ensure payload trajectory never exceeds 1M token ceiling
        if (reqBody.length > 0) {
            try {
                const toolVirtualizer = require('../tool_virtualizer');
                let p = JSON.parse(reqBody.toString('utf8'));
                p = toolVirtualizer.pruneOversizedToolOutputs(p);
                reqBody = Buffer.from(JSON.stringify(p), 'utf8');
            } catch (_) {}
        }

        // Forward attempt function with failover
        const attemptForward = async (currentAccount, attemptCount = 0) => {
            // Guarantee token validity prior to upstream dispatch
            const tokenRes = await ensureAccountTokenValid(currentAccount, 2 * 60 * 1000);
            if (tokenRes && tokenRes.details && tokenRes.details.refreshed) {
                saveVault(vault);
            }

            const targetBaseUrl = 'https://daily-cloudcode-pa.googleapis.com';
            const [rawSubPath, rawQuery] = (upstreamPath || '').split('?');
            const targetUrl = new URL(targetBaseUrl);
            targetUrl.pathname = targetUrl.pathname.replace(/\/+$/, '') + '/' + (rawSubPath || '').replace(/^\/+/, '');
            if (rawQuery) targetUrl.search = '?' + rawQuery;
            console.log(`[Account Rotator] 📡 DISPATCHING ${req.method} ${targetUrl.href} (account: ${currentAccount.email})`);
            try {
                const dumpDir = path.join(__dirname, '..', '..', '.FL_BIN');
                if (!fs.existsSync(dumpDir)) fs.mkdirSync(dumpDir, { recursive: true });
                fs.writeFileSync(path.join(dumpDir, 'last_upstream_payload.json'), reqBody.toString('utf8'));
            } catch (_) {}

            const isStreamRequest = isV1BetaStream || req.url.includes('stream') || (req.headers.accept && req.headers.accept.includes('text/event-stream'));

            const proxyHeaders = { ...req.headers };
            proxyHeaders.host = targetUrl.host;
            proxyHeaders['user-agent'] = 'antigravity/2.8.1';
            proxyHeaders['authorization'] = `Bearer ${currentAccount.access_token || ''}`;
            proxyHeaders['content-length'] = reqBody.length;
            proxyHeaders['connection'] = 'close';
            delete proxyHeaders['accept-encoding'];
            delete proxyHeaders['x-goog-api-key'];
            delete proxyHeaders['x-goog-access-token'];

            const proxyReq = https.request(targetUrl, {
                method: req.method,
                headers: proxyHeaders,
                timeout: 60000
            }, async (proxyRes) => {
                console.log(`[Account Rotator] 📥 UPSTREAM STATUS: ${proxyRes.statusCode} for ${targetUrl.href} [${currentAccount.email}]`);
                const maxAttempts = Math.max(vault.accounts.length, 25);

                const returnGracefulFallback = (msg) => {
                    if (res.headersSent) return;
                    res.writeHead(200, { 'Content-Type': isStreamRequest ? 'text/event-stream' : 'application/json' });
                    const fb = formatSovereignPayload(null, msg);
                    if (isStreamRequest) {
                        res.write(`data: ${JSON.stringify(fb)}\n\n`);
                        res.end();
                    } else {
                        res.end(JSON.stringify(fb));
                    }
                };

                // 1. Check for HTTP 401 Unauthorized (Expired or Revoked Token)
                if (proxyRes.statusCode === 401 && attemptCount < maxAttempts) {
                    proxyRes.resume();
                    console.warn(`[Account Rotator] ⚠️ 401 Unauthorized on [${currentAccount.email}]. Forcing instant token refresh...`);
                    const ref = await refreshAccountToken(currentAccount, true);
                    if (ref.refreshed) {
                        saveVault(vault);
                        console.log(`[Account Rotator] 🔄 401 Self-Healed! Retrying request on [${currentAccount.email}]...`);
                        return attemptForward(currentAccount, attemptCount + 1);
                    } else {
                        console.error(`[Account Rotator] ❌ 401 Refresh failed for [${currentAccount.email}]:`, ref.error);
                        currentAccount.status = 'error';
                        currentAccount.error_message = ref.error || 'Token expired or revoked';
                        saveVault(vault);
                        const nextAccount = getNextAvailableAccount(vault, currentAccount.id);
                        if (nextAccount) {
                            console.log(`[Account Rotator] 🔀 401 Failover: Rotating traffic to [${nextAccount.email}]...`);
                            return attemptForward(nextAccount, attemptCount + 1);
                        } else {
                            return returnGracefulFallback('[Flowork Engine Notice] Sesi token perlu diperbarui. Silakan ulangi dalam beberapa saat.');
                        }
                    }
                }

                // 2. Check for HTTP 429 Rate Limit / Quota Exceeded
                if (proxyRes.statusCode === 429) {
                    proxyRes.resume();
                    if (isPinnedAccount && boundPolicy === 'strict') {
                        console.warn(`[Account Rotator] 🔒 Dedicated pinned account [${currentAccount.email}] hit 429 quota limit.`);
                        currentAccount.cooldown_until = Date.now() + COOLDOWN_DURATION_MS;
                        currentAccount.status = 'cooldown';
                        currentAccount.errors_count = (currentAccount.errors_count || 0) + 1;
                        notifyCloudCooldown(currentAccount.id, currentAccount.cooldown_until);
                        saveVault(vault);
                        return returnGracefulFallback(`Dedicated account [${currentAccount.email}] sedang dalam cooldown kuota.`);
                    }

                    if (attemptCount < maxAttempts) {
                        console.warn(`[Account Rotator] ⚡ Quota limit (429) hit on [${currentAccount.email}]. Shifting to cooldown...`);
                        currentAccount.cooldown_until = Date.now() + COOLDOWN_DURATION_MS;
                        currentAccount.status = 'cooldown';
                        currentAccount.errors_count = (currentAccount.errors_count || 0) + 1;
                        notifyCloudCooldown(currentAccount.id, currentAccount.cooldown_until);
                        moveAccountToEnd(vault, currentAccount.id);
                        saveVault(vault);

                        const nextAccount = getNextAvailableAccount(vault, currentAccount.id);
                        if (nextAccount) {
                            console.log(`[Account Rotator] 🔀 Rotating traffic to [${nextAccount.email}] (Attempt #${attemptCount + 1})...`);
                            vault.active_account_id = nextAccount.id;
                            saveVault(vault);
                            return attemptForward(nextAccount, attemptCount + 1);
                        } else {
                            return returnGracefulFallback('Semua akun sedang dalam batas kuota sejenak. Silakan coba kembali dalam 30 detik.');
                        }
                    }
                }

                // 3. Check for HTTP 403 Permission Denied / Validation Required
                if (proxyRes.statusCode === 403) {
                    const bodyChunks = [];
                    proxyRes.on('data', chunk => bodyChunks.push(chunk));
                    proxyRes.on('end', () => {
                        const bodyStr = Buffer.concat(bodyChunks).toString('utf8');
                        let isValReq = false;
                        let valUrl = '';
                        try {
                            const errJ = JSON.parse(bodyStr);
                            const details = errJ.error?.details || [];
                            for (const d of details) {
                                if (d.reason === 'VALIDATION_REQUIRED') {
                                    isValReq = true;
                                    valUrl = d.metadata?.validation_url || '';
                                    break;
                                }
                            }
                        } catch (_) {}

                        if (isValReq) {
                            console.warn(`[Account Rotator] 🔒 Account [${currentAccount.email}] requires validation (HTTP 403 VALIDATION_REQUIRED).`);
                            currentAccount.status = 'validation_required';
                            currentAccount.validation_url = valUrl;
                            currentAccount.error_message = 'Google requires phone/identity validation';
                        } else {
                            console.warn(`[Account Rotator] ⚠️ HTTP 403 on [${currentAccount.email}].`);
                            currentAccount.status = 'error';
                            currentAccount.error_message = 'HTTP 403 Forbidden';
                        }
                        saveVault(vault);

                        if (attemptCount < maxAttempts) {
                            const nextAccount = getNextAvailableAccount(vault, currentAccount.id);
                            if (nextAccount) {
                                console.log(`[Account Rotator] 🔀 403 Failover: Rotating traffic to [${nextAccount.email}] (Attempt #${attemptCount + 1})...`);
                                return attemptForward(nextAccount, attemptCount + 1);
                            }
                        }
                        return returnGracefulFallback('[Flowork Engine Notice] Akun memerlukan verifikasi. Silakan hubungi admin.');
                    });
                    return;
                }

                // 4. Check for HTTP 400 (Client error / Geo-location rejection / 1M Token Ceiling Overflow)
                if (proxyRes.statusCode === 400) {
                    const bodyChunks = [];
                    proxyRes.on('data', chunk => bodyChunks.push(chunk));
                    proxyRes.on('end', async () => {
                        const bodyStr = Buffer.concat(bodyChunks).toString('utf8');
                        if (bodyStr.includes('User location is not supported') || bodyStr.includes('FAILED_PRECONDITION')) {
                            if (attemptCount < maxAttempts) {
                                console.warn(`[Account Rotator] ⚠️ HTTP 400 Egress Geo-block on [${currentAccount.email}]. Cooling down 30s...`);
                                currentAccount.cooldown_until = Date.now() + 30000;
                                currentAccount.status = 'cooldown';
                                saveVault(vault);
                                await new Promise(r => setTimeout(r, 200));
                                const nextAccount = getNextAvailableAccount(vault, currentAccount.id);
                                if (nextAccount) {
                                    return attemptForward(nextAccount, attemptCount + 1);
                                }
                            }
                        }

                        // 4b. Reactive 1M Token Budget Failover
                        const isTokenOverflow = bodyStr.includes('maximum number of tokens') ||
                                                bodyStr.includes('exceeds the maximum number of tokens allowed') ||
                                                bodyStr.includes('input token count exceeds') ||
                                                bodyStr.includes('RESOURCE_EXHAUSTED');

                        if (isTokenOverflow && attemptCount < 5) {
                            console.warn(`[Account Rotator] 🛡️ 1M Token Ceiling Overflow detected upstream! Engaging emergency trajectory compaction (attempt #${attemptCount + 1})...`);
                            try {
                                const toolVirtualizer = require('../tool_virtualizer');
                                let parsedPayload = JSON.parse(reqBody.toString('utf8'));
                                parsedPayload = toolVirtualizer.pruneOversizedToolOutputs(parsedPayload, { aggressive: true });
                                reqBody = Buffer.from(JSON.stringify(parsedPayload), 'utf8');
                                console.log(`[Account Rotator] 🛡️ Payload successfully compacted to ${reqBody.length} bytes. Re-dispatching to [${currentAccount.email}]...`);
                                return attemptForward(currentAccount, attemptCount + 1);
                            } catch (compactErr) {
                                console.error('[Account Rotator] Emergency compaction error:', compactErr.message);
                            }
                        }

                        console.error(`[Account Rotator] ❌ HTTP 400 Upstream Rejection on [${currentAccount.email}]:`, bodyStr);
                        let upstreamMsg = '';
                        try {
                            const errJ = JSON.parse(bodyStr);
                            upstreamMsg = errJ.error?.message || errJ.message || '';
                        } catch (_) {}
                        const fallbackMsg = upstreamMsg
                            ? `[Flowork Engine Notice] Upstream: ${upstreamMsg}`
                            : '[Flowork Engine Notice] Permintaan inferensi tidak dapat diproses upstream. Silakan coba kembali.';
                        return returnGracefulFallback(fallbackMsg);
                    });
                    return;
                }

                // 5. Check for HTTP 5xx Server Errors (Transient upstream failure)
                if (proxyRes.statusCode >= 500 && attemptCount < 4) {
                    proxyRes.resume();
                    console.warn(`[Account Rotator] ⚠️ HTTP ${proxyRes.statusCode} Upstream Transient Error. Retrying failover attempt #${attemptCount + 1}...`);
                    await new Promise(r => setTimeout(r, 300));
                    const nextAccount = getNextAvailableAccount(vault, currentAccount.id) || currentAccount;
                    return attemptForward(nextAccount, attemptCount + 1);
                }

                // Normal response or no failover candidate available
                currentAccount.requests_count = (currentAccount.requests_count || 0) + 1;
                currentAccount.last_used_at = new Date().toISOString();
                if (proxyRes.statusCode === 200) {
                    setImmediate(() => notifyCloudUsage('google', 'gemini-3.8-flash-high', 1));
                }
                saveVault(vault);

                const responseHeaders = { ...proxyRes.headers };
                responseHeaders['access-control-allow-origin'] = '*';
                responseHeaders['access-control-allow-methods'] = 'GET, POST, OPTIONS, PUT, DELETE';
                responseHeaders['access-control-allow-headers'] = '*';

                const isStream = isStreamRequest || (proxyRes.headers['content-type'] && proxyRes.headers['content-type'].includes('text/event-stream'));
                delete responseHeaders['content-length'];
                res.writeHead(proxyRes.statusCode, responseHeaders);

                if (isStream) {
                    let streamBuffer = '';
                    let hasSentFinishReason = false;
                    let hasSentAnyContent = false;

                    proxyRes.on('data', chunk => {
                        streamBuffer += chunk.toString('utf8');
                        const lines = streamBuffer.split('\n');
                        streamBuffer = lines.pop(); // keep last incomplete line

                        for (const line of lines) {
                            const trimmed = line.trim();
                            if (trimmed.startsWith('data:')) {
                                const jsonStr = trimmed.slice(5).trim();
                                if (jsonStr) {
                                    try {
                                        const obj = JSON.parse(jsonStr);
                                        const payload = formatSovereignPayload(obj);
                                        if (payload.candidates && payload.candidates.length > 0) {
                                            const cand = payload.candidates[0];
                                            if (cand.finishReason) hasSentFinishReason = true;
                                            if (cand.content && Array.isArray(cand.content.parts) && cand.content.parts.some(p => p.functionCall || (p.text && p.text.trim().length > 0))) {
                                                hasSentAnyContent = true;
                                            }
                                        }
                                        res.write(`data: ${JSON.stringify(payload)}\n\n`);
                                        continue;
                                    } catch (_) {}
                                }
                            }
                            if (trimmed) {
                                res.write(line + '\n');
                            }
                        }
                    });

                    proxyRes.on('end', () => {
                        if (streamBuffer.trim()) {
                            const trimmed = streamBuffer.trim();
                            if (trimmed.startsWith('data:')) {
                                const jsonStr = trimmed.slice(5).trim();
                                try {
                                    const obj = JSON.parse(jsonStr);
                                    const payload = formatSovereignPayload(obj);
                                    if (payload.candidates && payload.candidates.length > 0) {
                                        const cand = payload.candidates[0];
                                        if (cand.finishReason) hasSentFinishReason = true;
                                        if (cand.content && Array.isArray(cand.content.parts) && cand.content.parts.some(p => p.functionCall || (p.text && p.text.trim().length > 0))) {
                                            hasSentAnyContent = true;
                                        }
                                    }
                                    res.write(`data: ${JSON.stringify(payload)}\n\n`);
                                    streamBuffer = '';
                                } catch (_) {}
                            }
                            if (streamBuffer) {
                                res.write(streamBuffer + '\n');
                            }
                        }

                        // Safety guarantee: If stream produced 0 content parts, synthesize clean fallback
                        if (!hasSentAnyContent) {
                            const fallbackChunk = formatSovereignPayload(null, 'Maaf, model AI upstream tidak mengembalikan respons atau terkena safety filter.');
                            res.write(`data: ${JSON.stringify(fallbackChunk)}\n\n`);
                            hasSentFinishReason = true;
                        } else if (!hasSentFinishReason) {
                            const stopChunk = formatSovereignPayload(null, ' ');
                            res.write(`data: ${JSON.stringify(stopChunk)}\n\n`);
                        }

                        res.end();
                    });
                } else {
                    let respData = '';
                    proxyRes.on('data', c => { respData += c; });
                    proxyRes.on('end', () => {
                        try {
                            const parsed = JSON.parse(respData);
                            const payload = formatSovereignPayload(parsed, 'Maaf, model AI upstream tidak mengembalikan respons atau terkena safety filter.');
                            return res.end(JSON.stringify(payload));
                        } catch (_) {}
                        res.end(respData);
                    });
                }
            });

            proxyReq.on('timeout', () => {
                console.warn(`[Account Rotator] ⏱️ Upstream request timed out (60s) on [${currentAccount.email}]. Aborting socket for failover...`);
                proxyReq.destroy(new Error('ETIMEDOUT'));
            });

            proxyReq.on('error', (err) => {
                console.error(`[Account Rotator] Upstream error on [${currentAccount.email}]:`, err.message);
                if (attemptCount < vault.accounts.length - 1) {
                    const fallback = getNextAvailableAccount(vault, currentAccount.id);
                    if (fallback) {
                        return attemptForward(fallback, attemptCount + 1);
                    }
                }
                if (!res.headersSent) {
                    const fb = formatSovereignPayload(null, `Koneksi inferensi upstream terputus (${err.message}). Silakan ulangi instruksi.`);
                    res.writeHead(200, { 'Content-Type': isStreamRequest ? 'text/event-stream' : 'application/json' });
                    if (isStreamRequest) {
                        res.write(`data: ${JSON.stringify(fb)}\n\n`);
                        res.end();
                    } else {
                        res.end(JSON.stringify(fb));
                    }
                }
            });

            if (reqBody.length > 0) {
                proxyReq.write(reqBody);
            }
            proxyReq.end();
        };

        attemptForward(account, 0);
    });

    return true;
}

// ── HTTP API Request Dispatcher for Multi-Account Router ──
async function handleRouterRequest(req, res, parsedUrl, pathname, serverPort) {
    const isGet = req.method === 'GET';
    const isPost = req.method === 'POST';

    // 1. Get Accounts List & Matrix Status
    if (pathname === '/auth/router/accounts' || pathname === '/api/router/accounts' || pathname === '/auth/router/status' || pathname === '/api/router/status' || pathname === '/auth/router/refresh-pool' || pathname === '/api/router/refresh-pool') {
        let vault = loadVault();
        if (!Array.isArray(vault.accounts) || vault.accounts.length === 0 || pathname.includes('refresh-pool') || parsedUrl.query?.refresh === '1') {
            await pullCloudVault();
            vault = loadVault();
        }
        const now = Date.now();

        // Urutkan akun: yang belum kena limit di depan, yang kena limit di paling belakang (termasuk urutan tampilan)
        if (Array.isArray(vault.accounts) && vault.accounts.length > 1) {
            vault.accounts.sort((a, b) => {
                const aLim = ((parseTimestamp(a.cooldown_until) > now) || a.status === 'cooldown' || a.status === 'error') ? 1 : 0;
                const bLim = ((parseTimestamp(b.cooldown_until) > now) || b.status === 'cooldown' || b.status === 'error') ? 1 : 0;
                return aLim - bLim;
            });
            saveVault(vault);
        }

        const accountList = vault.accounts.map(a => {
            const coolUntil = parseTimestamp(a.cooldown_until);
            const isCooldown = coolUntil > now;
            return {
                id: a.id,
                email: a.email,
                name: a.name || a.email.split('@')[0],
                status: isCooldown ? 'cooldown' : (a.status || 'active'),
                cooldown_until: isCooldown ? coolUntil : 0,
                cooldown_remaining_sec: isCooldown ? Math.ceil((coolUntil - now) / 1000) : 0,
                is_active: a.id === vault.active_account_id,
                expires_at: parseTimestamp(a.expires_at) || 0,
                has_refresh_token: !!a.refresh_token,
                requests_count: a.requests_count || 0,
                errors_count: a.errors_count || 0,
                added_at: a.added_at,
                last_used_at: a.last_used_at,
                error_message: a.error_message || '',
                validation_url: a.validation_url || ''
            };
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            success: true,
            total_accounts: accountList.length,
            max_accounts: MAX_ACCOUNTS,
            active_account_id: vault.active_account_id,
            rotation_mode: vault.rotation_mode || 'failover',
            accounts: accountList
        }));
    }

    // 2. Generate PKCE Login URL for adding an account
    if (pathname === '/auth/router/login-url' && (isGet || isPost)) {
        const result = await generateLoginUrl(serverPort);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            success: true,
            provider: 'google',
            loginUrl: result.loginUrl,
            state: result.state
        }));
    }

    // 3. Set Active Account
    if (pathname === '/auth/router/select-account' && isPost) {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                const json = JSON.parse(body || '{}');
                const targetId = json.id;
                const vault = loadVault();
                const acc = vault.accounts.find(a => a.id === targetId);
                if (!acc) {
                    res.writeHead(404, { 'Content-Type': 'application/json' });
                    return res.end(JSON.stringify({ success: false, error: 'Account not found' }));
                }

                vault.active_account_id = targetId;
                saveVault(vault);
                console.log(`[Account Rotator] 👉 Active account manually switched to [${acc.email}]`);

                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: true, active_account_id: targetId, email: acc.email }));
            } catch (e) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: e.message }));
            }
        });
        return true;
    }

    // 4. Remove Account
    if (pathname === '/auth/router/remove-account' && isPost) {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                const json = JSON.parse(body || '{}');
                const targetId = json.id;
                const vault = loadVault();
                const initLen = vault.accounts.length;
                const targetAcc = vault.accounts.find(a => a.id === targetId);
                vault.accounts = vault.accounts.filter(a => a.id !== targetId);

                if (vault.accounts.length === initLen) {
                    res.writeHead(404, { 'Content-Type': 'application/json' });
                    return res.end(JSON.stringify({ success: false, error: 'Account not found' }));
                }

                // Record tombstone to prevent resurrection
                recordTombstone(targetId);
                if (targetAcc && targetAcc.email) {
                    recordTombstone(targetAcc.email);
                }

                if (vault.active_account_id === targetId) {
                    vault.active_account_id = vault.accounts[0]?.id || '';
                }

                saveVault(vault, true);
                console.log(`[Account Rotator] 🗑️ Account [${targetId}] removed from pool. Remaining: ${vault.accounts.length}`);

                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: true, remaining: vault.accounts.length, active_account_id: vault.active_account_id }));
            } catch (e) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: e.message }));
            }
        });
        return true;
    }

    // 5. Set Rotation Strategy
    if (pathname === '/auth/router/set-rotation-mode' && isPost) {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                const json = JSON.parse(body || '{}');
                const mode = json.mode === 'round_robin' ? 'round_robin' : 'failover';
                const vault = loadVault();
                vault.rotation_mode = mode;
                saveVault(vault);
                console.log(`[Account Rotator] ⚙️ Rotation mode updated to: ${mode}`);

                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: true, rotation_mode: mode }));
            } catch (e) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: e.message }));
            }
        });
        return true;
    }

    // 6. Test & Refresh Specific Account
    if (pathname === '/auth/router/test-account' && isPost) {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
            try {
                const json = JSON.parse(body || '{}');
                const targetId = json.id;
                const vault = loadVault();
                const acc = vault.accounts.find(a => a.id === targetId);
                if (!acc) {
                    res.writeHead(404, { 'Content-Type': 'application/json' });
                    return res.end(JSON.stringify({ success: false, error: 'Account not found' }));
                }

                const refResult = await refreshAccountToken(acc);
                saveVault(vault);

                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                    success: refResult.refreshed || !refResult.error,
                    email: acc.email,
                    status: acc.status,
                    expires_at: acc.expires_at,
                    details: refResult
                }));
            } catch (e) {
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: e.message }));
            }
        });
        return true;
    }

    // 7. Clear Cooldown on Accounts
    if (pathname === '/auth/router/clear-cooldown' && isPost) {
        const vault = loadVault();
        for (const a of vault.accounts) {
            a.cooldown_until = 0;
            if (a.status === 'cooldown') a.status = 'active';
        }
        saveVault(vault);
        console.log('[Account Rotator] ⚡ Cooldown timers cleared for all accounts.');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ success: true, message: 'All cooldowns cleared' }));
    }

    // 7b. Session Bindings: Get All Bindings
    if ((pathname === '/auth/router/session-bindings' || pathname === '/api/router/session-bindings') && isGet) {
        const bindings = loadSessionBindings();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ success: true, bindings }));
    }

    // 7c. Session Binding: Get or Update Specific Session Affinity
    if (pathname === '/auth/router/session-binding' || pathname === '/api/router/session-binding') {
        if (isGet) {
            const sId = (parsedUrl.query?.session_id || '').toString().trim();
            const binding = getBindingForSession(sId) || { account_id: 'combo', failover_policy: 'fallback_pool' };
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({ success: true, session_id: sId, binding }));
        }
        if (isPost) {
            let body = '';
            req.on('data', chunk => body += chunk);
            req.on('end', () => {
                try {
                    const json = JSON.parse(body || '{}');
                    const sId = (json.session_id || '').toString().trim();
                    if (!sId) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        return res.end(JSON.stringify({ success: false, error: 'Missing session_id' }));
                    }
                    const accId = (json.account_id || 'combo').toString().trim();
                    const failoverPolicy = json.failover_policy === 'strict' ? 'strict' : 'fallback_pool';
                    const bindings = loadSessionBindings();
                    if (accId === 'combo' || accId === 'auto' || !accId) {
                        delete bindings[sId];
                    } else {
                        bindings[sId] = {
                            account_id: accId,
                            failover_policy: failoverPolicy,
                            updated_at: new Date().toISOString()
                        };
                    }
                    saveSessionBindings(bindings);
                    console.log(`[Account Rotator] 🔗 Session [${sId}] affinity updated -> account [${accId}] (policy: ${failoverPolicy})`);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    return res.end(JSON.stringify({
                        success: true,
                        session_id: sId,
                        binding: bindings[sId] || { account_id: 'combo', failover_policy: 'fallback_pool' }
                    }));
                } catch (e) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    return res.end(JSON.stringify({ success: false, error: e.message }));
                }
            });
            return true;
        }
    }

    // 8. Intercept OAuth Callback if state is multi-account
    if (pathname === '/auth/callback' && parsedUrl.query.state && String(parsedUrl.query.state).startsWith('flw_multi_')) {
        return await handleOAuthCallback(req, res, parsedUrl, serverPort);
    }

    return false;
}

// ── Background Proactive Token Keeper Daemon ──
function startBackgroundTokenKeeper() {
    if (global.__flowork_token_keeper_active) return;
    global.__flowork_token_keeper_active = true;

    const runKeeperCycle = async () => {
        try {
            // Local sweep only: ZERO recurring cloud polls to preserve Cloudflare free quotas
            const vault = loadVault();
            if (!Array.isArray(vault.accounts) || vault.accounts.length === 0) return;
            let changed = false;
            const now = Date.now();
            for (const acc of vault.accounts) {
                if (acc.status === 'error') continue;
                if (!acc.refresh_token) continue;
                // Proactively refresh if token expires in less than 10 minutes or already expired
                const remainingMs = acc.expires_at ? (acc.expires_at - now) : 0;
                if (remainingMs < 10 * 60 * 1000) {
                    console.log(`[Token Keeper] 🔄 Proactively refreshing token for [${acc.email}] (remaining: ${Math.round(remainingMs / 1000)}s)...`);
                    const res = await refreshAccountToken(acc, true);
                    if (res.refreshed) {
                        changed = true;
                    }
                }
            }
            if (changed) {
                // Local save only: no cloud write needed as refresh_token did not change
                saveVault(vault, false);
                console.log('[Token Keeper] 💾 All proactively refreshed tokens persisted locally.');
            }
        } catch (e) {
            console.warn('[Token Keeper] Heartbeat check warning:', e.message);
        }
    };

    // Initial check after 5s, gentle recurring sweep every 15 minutes
    setTimeout(runKeeperCycle, 5000);
    setInterval(runKeeperCycle, 15 * 60 * 1000).unref();
    console.log('[Token Keeper] 🛡️ Background proactive token keeper armed (15m local sweep).');
}

// Arm daemon on module initialization
startBackgroundTokenKeeper();

module.exports = {
    loadVault,
    saveVault,
    pullCloudVault,
    pushCloudVault,
    pullCloudSoul,
    notifyCloudCooldown,
    handleRouterRequest,
    handleOAuthCallback,
    handleAiRequestWithFailover,
    generateLoginUrl,
    refreshAccountToken,
    ensureAccountTokenValid,
    startBackgroundTokenKeeper,
    getSessionBindingsPath,
    loadSessionBindings,
    saveSessionBindings,
    getBindingForSession,
    loadSyncDrive,
    saveSyncDrive,
    getSyncDrivePath,
    MAX_ACCOUNTS
};


