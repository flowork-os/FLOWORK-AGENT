// @lock: CONECTION/prompt_injector.js (SOVEREIGN LOCKED COMPONENT)
const fs = require('fs');
const path = require('path');

class FloworkOSPromptInjector {
    static getPortableHome() {
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
        return path.resolve(__dirname, '..', 'portable-home');
    }

    static getVaultData() {
        const portableRoot = this.getPortableHome();
        const candidatePaths = [
            path.join(portableRoot, '.flowork', 'auth_vault.json'),
            path.join(process.cwd(), '.flowork', 'auth_vault.json'),
            path.join(process.cwd(), 'portable-home', '.flowork', 'auth_vault.json'),
            path.resolve(__dirname, '..', '.flowork', 'auth_vault.json'),
            path.resolve(__dirname, '..', 'portable-home', '.flowork', 'auth_vault.json'),
            path.join(process.env.HOME || '', '.flowork', 'auth_vault.json')
        ];

        for (const vPath of candidatePaths) {
            if (fs.existsSync(vPath)) {
                try {
                    const raw = fs.readFileSync(vPath, 'utf8');
                    const parsed = JSON.parse(raw);
                    if (parsed && typeof parsed === 'object') {
                        return parsed;
                    }
                } catch (_) {}
            }
        }
        return null;
    }

    static parseJwtClaims(token) {
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

    static resolveAuthData() {
        const vault = this.getVaultData() || {};
        const u = vault.flowork_user || {};
        const token = vault.flowork_token || vault.upstream_flowork_token || null;
        const claims = this.parseJwtClaims(token) || {};

        // Pure dynamic identity sourced 100% from auth.floworkos.com via auth_vault.json
        const username = claims.username || u.username || 'guest';
        const role = (claims.role || u.role || (username === 'guest' ? 'GUEST' : 'USER')).toUpperCase();
        const tier = (claims.tier || u.tier || (role === 'SUPER_ADMIN' ? 'enterprise' : 'free')).toLowerCase();
        const level = claims.level !== undefined ? claims.level : (u.level !== undefined ? u.level : (role === 'SUPER_ADMIN' ? 99 : 1));
        const badge = claims.badge || u.badge || (role === 'SUPER_ADMIN' ? '👑 Sovereign Master' : '👤 User');
        const rank = claims.rank || u.rank || (role === 'SUPER_ADMIN' ? 'Supreme Architect' : 'Standard User');
        const issuer = claims.iss || 'https://auth.floworkos.com';
        const sub = claims.sub || (username !== 'guest' ? `usr_${username}` : null);
        const machineId = claims.machine_id || vault.machine_id || null;

        return {
            username,
            name: claims.name || u.name || u.displayName || username,
            role,
            tier,
            level,
            badge,
            rank,
            permissions: claims.permissions || u.permissions || (role === 'SUPER_ADMIN' ? ['*.*'] : ['read', 'write']),
            issuer,
            sub,
            machineId,
            activeProvider: vault.active_provider || 'sovereign',
            isLoggedOut: !!vault.is_logged_out,
            lastUpdated: vault.last_updated || null
        };
    }

    static formatDateTime() {
        const now = new Date();
        const daysId = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
        const daysEn = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const monthsId = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
        const monthsEn = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

        const dayNameId = daysId[now.getDay()];
        const dayNameEn = daysEn[now.getDay()];
        const day = String(now.getDate()).padStart(2, '0');
        const monthId = monthsId[now.getMonth()];
        const monthEn = monthsEn[now.getMonth()];
        const year = now.getFullYear();

        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');

        return {
            dayId: dayNameId,
            dayEn: dayNameEn,
            dateId: `${day} ${monthId} ${year}`,
            dateEn: `${day} ${monthEn} ${year}`,
            isoDate: `${year}-${String(now.getMonth() + 1).padStart(2, '0')}-${day}`,
            time: `${hours}:${minutes}:${seconds}`,
            timezone: 'WIB (Asia/Jakarta • UTC+7)',
            fullId: `${dayNameId}, ${day} ${monthId} ${year} ${hours}:${minutes}:${seconds} WIB`
        };
    }

    static extractWorkspaceFromPayload(payload) {
        if (!payload) return null;
        try {
            if (typeof payload === 'object') {
                if (payload.workspaceUri && typeof payload.workspaceUri === 'string') {
                    const clean = decodeURIComponent(payload.workspaceUri.replace(/^file:\/\//, '').trim());
                    if (clean.includes('outside-of-project')) return clean;
                    if (fs.existsSync(clean) && fs.statSync(clean).isDirectory()) return clean;
                }
                if (payload.request && payload.request.workspaceUri && typeof payload.request.workspaceUri === 'string') {
                    const clean = decodeURIComponent(payload.request.workspaceUri.replace(/^file:\/\//, '').trim());
                    if (clean.includes('outside-of-project')) return clean;
                    if (fs.existsSync(clean) && fs.statSync(clean).isDirectory()) return clean;
                }
            }

            const rawStr = typeof payload === 'string' ? payload : JSON.stringify(payload);
            const str = rawStr.replace(/\\n/g, '\n').replace(/\\r/g, '\r');

            const mapMatch = str.match(/\[URI\]\s*->\s*\[CorpusName\]:\s*([^\s\r\n\->]+)/i) ||
                             str.match(/The user has \d+ active workspaces[^\n]*\n([^\s\r\n\->]+)/i) ||
                             str.match(/Active Workspace:\s*([^\r\n<]+)/i) ||
                             str.match(/workspaceUri["']?\s*:\s*["']file:\/\/([^"']+)["']/i);
            if (mapMatch && mapMatch[1]) {
                const clean = decodeURIComponent(mapMatch[1].replace(/^file:\/\//, '').trim());
                if (fs.existsSync(clean) && fs.statSync(clean).isDirectory()) {
                    return clean;
                }
            }
        } catch (_) {}
        return null;
    }

    static resolveWorkspacePath(payload = {}) {
        if (process.env.FLOWORK_WORKSPACE && fs.existsSync(process.env.FLOWORK_WORKSPACE)) {
            return path.resolve(process.env.FLOWORK_WORKSPACE);
        }
        if (process.env.FLOWORK_PROJECT_PATH && fs.existsSync(process.env.FLOWORK_PROJECT_PATH)) {
            return path.resolve(process.env.FLOWORK_PROJECT_PATH);
        }

        const fromPayload = this.extractWorkspaceFromPayload(payload);
        if (fromPayload) {
            return path.resolve(fromPayload);
        }

        return process.env.FLOWORK_APP_DIR || process.cwd();
    }

    /**
     * Constructs ONLY the caller awareness metadata context.
     * ZERO prompt bloat, NO pillars dump, NO operational directives.
     * Informs the agent who it is speaking to, authority level, current date/time,
     * and auth data from auth.floworkos.com sourced from auth_vault.json.
     */
    static buildCallerContext(auth, workspacePath) {
        const dt = this.formatDateTime();
        const block = [
            `<!-- [FLOWORK_CALLER_AWARENESS:START] -->`,
            `<CALLER_CONTEXT>`,
            `- Current User : ${auth.username} (${auth.badge || auth.name})`,
            `- Role & Level : ${auth.role} (Level ${auth.level})`,
            `- Rank & Tier  : ${auth.rank} [${auth.tier}]`,
            `- Auth Issuer  : ${auth.issuer} (auth_vault.json)`,
            ...(auth.sub ? [`- Subject ID   : ${auth.sub}`] : []),
            `- Current Date : ${dt.dayId} / ${dt.dayEn}, ${dt.dateId}`,
            `- Real Time    : ${dt.time} ${dt.timezone}`,
            `- Workspace    : ${workspacePath || process.cwd()}`,
            `</CALLER_CONTEXT>`,
            `<!-- [FLOWORK_CALLER_AWARENESS:END] -->`
        ];
        return block.join('\n');
    }

    /**
     * Pass-through: Zero MITM prompt injection in CONECTOR.
     * All context awareness and prompts are natively constructed within AGENT.
     */
    static injectIntoPayload(payload) {
        return payload;
    }
}

module.exports = FloworkOSPromptInjector;
