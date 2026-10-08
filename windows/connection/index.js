// Master Connection Dispatcher & Gateway for Flowork OS CONECTION
// Centralized switchboard managing sovereign auth, web gateways, prompt loading, wire interceptor, and isolated AI providers.
const fs = require('fs');
const path = require('path');

if (!process.env.FLOWORK_PORT) {
    try {
        const { execFileSync } = require('child_process');
        const script = `
            const net = require('net');
            function check(p) {
                if (p > 2037) { process.stdout.write('1987'); process.exit(0); }
                const s = net.createServer();
                s.once('error', () => check(p + 1));
                s.once('listening', () => { s.close(() => { process.stdout.write(String(p)); process.exit(0); }); });
                s.listen(p, '127.0.0.1');
            }
            check(1987);
        `;
        process.env.FLOWORK_PORT = execFileSync(process.execPath, ['-e', script], { encoding: 'utf8', timeout: 1500 }).trim() || '1987';
    } catch (_) {
        process.env.FLOWORK_PORT = '1987';
    }
}

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

const antygravity = require('./antygravity');
const providers = {
    sovereign: antygravity,
    antygravity: antygravity,
    google: antygravity
};

function getActiveProviderKey() {
    return 'antygravity';
}

function getActiveProvider() {
    return antygravity;
}

const router = require('./router');

module.exports = {
    // Modular Sovereign Provider Registry
    providers,
    getActiveProviderKey,
    getActiveProvider,

    // Agnostic Switchboard Delegation to Active Provider
    loadConfig: () => {
        const active = getActiveProvider();
        const cfg = active && active.loadConfig ? active.loadConfig() : {};
        const rPort = getDynamicRouterPort();
        if (rPort === 9099) return cfg;
        try {
            const str = JSON.stringify(cfg).replace(/127\.0\.0\.1:9099/g, `127.0.0.1:${rPort}`);
            return JSON.parse(str);
        } catch (_) {
            return cfg;
        }
    },
    getEndpoints: () => {
        const active = getActiveProvider();
        const ep = (active && active.getEndpoints) ? active.getEndpoints() : {};
        const rPort = getDynamicRouterPort();
        if (rPort === 9099) return ep;
        const res = {};
        for (const [k, v] of Object.entries(ep)) {
            res[k] = typeof v === 'string' ? v.replace(/127\.0\.0\.1:9099/g, `127.0.0.1:${rPort}`) : v;
        }
        return res;
    },
    getIdentityHeaders: () => {
        const active = getActiveProvider();
        return active && active.getIdentityHeaders ? active.getIdentityHeaders() : { headers: { 'User-Agent': 'FloworkOS/2.16.0' } };
    },
    getAuthConfig: () => {
        const active = getActiveProvider();
        return active && active.getAuthConfig ? active.getAuthConfig() : {};
    },
    getCliArgs: () => {
        const active = getActiveProvider();
        const rawArgs = active && active.getCliArgs ? active.getCliArgs() : [];
        const rPort = getDynamicRouterPort();
        
        // Strip sensitive credentials and leaks from process args (ps aux / /proc/cmdline)
        const sensitivePrefixes = [
            '--https_server_port=',
            '--override_oauth_client_id=',
            '--override_oauth_client_secret=',
            '--override_business_oauth_client_id=',
            '--override_business_oauth_client_secret=',
            '--model_api_client_type='
        ];

        return rawArgs
            .filter(a => typeof a === 'string' && !sensitivePrefixes.some(p => a.startsWith(p)))
            .map(a => typeof a === 'string' ? a.replace(/127\.0\.0\.1:9099/g, `127.0.0.1:${rPort}`) : a);
    },
    getUpdaterConfig: () => {
        const active = getActiveProvider();
        return active && active.getUpdaterConfig ? active.getUpdaterConfig() : {};
    },
    getCustomLinks: () => {
        const active = getActiveProvider();
        return active && active.getCustomLinks ? active.getCustomLinks() : {};
    },
    getSoundFiles: () => {
        const active = getActiveProvider();
        return active && active.getSoundFiles ? active.getSoundFiles() : {};
    },
    getFeedbackConfig: () => {
        const active = getActiveProvider();
        return active && active.getFeedbackConfig ? active.getFeedbackConfig() : {};
    },
    getModelCatalog: () => {
        const active = getActiveProvider();
        return active && active.getModelCatalog ? active.getModelCatalog() : [];
    },
    testConnectivity: () => {
        const active = getActiveProvider();
        return active && active.testConnectivity ? active.testConnectivity() : Promise.resolve(false);
    },
    buildAuthUrl: (...args) => {
        const active = getActiveProvider();
        return active && active.buildAuthUrl ? active.buildAuthUrl(...args) : '';
    },
    validateCallback: (...args) => {
        const active = getActiveProvider();
        return active && active.validateCallback ? active.validateCallback(...args) : Promise.resolve(null);
    },
    
    // Web Gateway & Search Tools (Delegated to Sovereign Search Tools)
    searchWeb: async (args) => {
        try {
            const searchTools = require('./search_tools');
            return await searchTools.searchWeb(args);
        } catch (_) { return { error: 'Search gateway inactive' }; }
    },
    fetchUrlContent: async (args) => {
        try {
            const searchTools = require('./search_tools');
            return await searchTools.fetchUrlContent(args);
        } catch (_) { return { error: 'Fetch gateway inactive' }; }
    },
    getWebTrafficLog: () => [],
    clearWebTrafficLog: () => ({ success: true }),
    htmlToMarkdown: (html) => String(html || ''),

    // Sovereign Provider Management (Antygravity Official)
    listProviders: () => [{ id: 'antygravity', alias: 'sovereign', name: 'Antygravity Pro', is_configured: true }],
    getProvider: () => antygravity,
    reloadProviders: () => ({ antygravity }),

    // Sovereign Wire Interceptor Proxy (Unified with Sovereign Router)
    createWireProxy: (cfg = {}) => {
        return router.createSovereignRouter({ port: getDynamicRouterPort(), ...cfg });
    },
    DEFAULT_PROXY_PORT: getDynamicRouterPort(),

    // Sovereign Switch Router
    createSovereignRouter: (opts = {}) => {
        return router.createSovereignRouter({ port: getDynamicRouterPort(), ...opts });
    },
    DEFAULT_ROUTER_PORT: getDynamicRouterPort(),
    getRouterInstance: () => defaultRouterInstance
};

// Auto-start Sovereign Switch Router singleton instance
if (!global.__FLOWORK_SOVEREIGN_ROUTER__) {
    try {
        const dynamicPort = getDynamicRouterPort();
        global.__FLOWORK_SOVEREIGN_ROUTER__ = router.createSovereignRouter({ port: dynamicPort });
        global.__FLOWORK_SOVEREIGN_ROUTER__.start().catch(e => console.warn('[CONECTION] Router auto-start notice:', e.message));
    } catch (e) {
        console.warn('[CONECTION] Router init notice:', e.message);
    }
}
let defaultRouterInstance = global.__FLOWORK_SOVEREIGN_ROUTER__;

Object.defineProperty(module.exports, 'config', {
    get: module.exports.loadConfig,
    enumerable: true,
    configurable: true
});
