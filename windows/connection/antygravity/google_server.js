// @lock: CONECTION/antygravity/google_server.js (SOVEREIGN LOCKED COMPONENT)
const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG_PATH = path.join(__dirname, 'endpoints.json');

/**
 * Loads configuration freshly from disk to ensure external updates take immediate effect
 */
function loadConfig() {
    try {
        const raw = fs.readFileSync(CONFIG_PATH, 'utf-8');
        return JSON.parse(raw);
    } catch (err) {
        console.error('[CONECTION/antygravity] Failed to read endpoints.json:', err.message);
        return {};
    }
}

/**
 * Returns API endpoints for the engine
 */
function getGoogleEndpoints() {
    const config = loadConfig();
    const api = config.api || {};
    return {
        apiServerUrl: api.serverUrl || '',
        cloudCodeEndpoint: api.cloudCodeEndpoint || '',
        generativeServiceAddr: api.generativeServiceAddr || '',
        analyticsServerUrl: api.analyticsServerUrl || '',
        inferenceApiServerUrl: api.inferenceApiServerUrl || '',
        publicArtifactBaseUrl: api.publicArtifactBaseUrl || '',
        updaterBaseUrl: api.updaterBaseUrl || '',
        ideUpdaterBaseUrl: api.ideUpdaterBaseUrl || '',
        docsUrl: api.docsUrl || '',
        modelApiClientType: api.modelApiClientType || 'ccpa',
        overrideModelName: api.overrideModelName || '',
        floworkDir: api.floworkDir || api.geminiDir || '.flowork',
        configDir: api.configDir || 'config',
        allowedSchemes: api.allowedSchemes || ['https:', 'http:', 'antigravity-ide:', 'flowork:']
    };
}

/**
 * Returns header identities (IDE Name, User-Agent, Subclient Type)
 */
function getIdentityHeaders() {
    const config = loadConfig();
    const id = config.identity || {};
    return {
        ideName: id.ideName || 'Flowork OS',
        userAgentName: id.userAgentName || 'FloworkOS',
        subclientType: id.subclientType || 'hub',
        ideVersion: id.ideVersion || '2.16.0',
        headers: id.headers || {}
    };
}

/**
 * Returns authentication configuration
 */
function getAuthConfig() {
    const config = loadConfig();
    const auth = config.auth || {};
    return {
        clientId: auth.clientId || '',
        clientSecret: auth.clientSecret || '',
        businessClientId: auth.businessClientId || '',
        businessClientSecret: auth.businessClientSecret || '',
        authUrl: auth.authUrl || '',
        tokenUrl: auth.tokenUrl || '',
        userInfoUrl: auth.userInfoUrl || '',
        scopes: auth.scopes || [],
        authPattern: new RegExp(auth.authPatternRegex || '^https:\\/\\/auth\\.floworkos\\.com\\/api\\/auth\\/oauth\\S+')
    };
}

/**
 * Generates the full set of CLI arguments for the flow binary
 * so the engine binary doesn't rely on hardcoded defaults
 */
function getCliArgs() {
    const endpoints = getGoogleEndpoints();
    const identity = getIdentityHeaders();
    const auth = getAuthConfig();
    const config = loadConfig();
    const args = [];

    if (identity.ideName) args.push(`--override_ide_name=${identity.ideName}`);
    if (identity.subclientType) args.push(`--subclient_type=${identity.subclientType}`);
    if (identity.ideVersion) args.push(`--override_ide_version=${identity.ideVersion}`);
    if (identity.userAgentName) args.push(`--override_user_agent_name=${identity.userAgentName}`);

    if (endpoints.apiServerUrl) args.push(`--api_server_url=${endpoints.apiServerUrl}`);
    if (endpoints.cloudCodeEndpoint) args.push(`--cloud_code_endpoint=${endpoints.cloudCodeEndpoint}`);
    if (endpoints.generativeServiceAddr) args.push(`--generative_service_addr=${endpoints.generativeServiceAddr}`);
    if (endpoints.floworkDir || endpoints.flowaiDir || endpoints.geminiDir) args.push(`--flowai_dir=${endpoints.floworkDir || endpoints.flowaiDir || endpoints.geminiDir}`);
    if (endpoints.configDir) args.push(`--config_dir=${endpoints.configDir}`);
    if (endpoints.analyticsServerUrl) args.push(`--analytics_server_url=${endpoints.analyticsServerUrl}`);
    if (endpoints.inferenceApiServerUrl) args.push(`--inference_api_server_url=${endpoints.inferenceApiServerUrl}`);
    if (endpoints.modelApiClientType) args.push(`--model_api_client_type=${endpoints.modelApiClientType}`);
    if (endpoints.overrideModelName) args.push(`--override_model_name=${endpoints.overrideModelName}`);

    if (auth.clientId && !auth.clientId.includes("[MANAGED")) args.push(`--override_oauth_client_id=${auth.clientId}`);
    if (auth.clientSecret && !auth.clientSecret.includes("[MANAGED")) args.push(`--override_oauth_client_secret=${auth.clientSecret}`);
    if (auth.businessClientId && !auth.businessClientId.includes("[MANAGED")) args.push(`--override_business_oauth_client_id=${auth.businessClientId}`);
    if (auth.businessClientSecret && !auth.businessClientSecret.includes("[MANAGED")) args.push(`--override_business_oauth_client_secret=${auth.businessClientSecret}`);

    if (Array.isArray(config.flags)) {
        for (const flag of config.flags) {
            if (flag && typeof flag === 'string') {
                args.push(flag);
            }
        }
    }

    // Whitelabel Sovereign Web Bundle GUI Resolution
    const hasWebBundle = args.some(a => typeof a === 'string' && a.startsWith('--web_bundle_path='));
    if (!hasWebBundle) {
        const guiCandidates = [
            process.env.FLOWORK_GUI_DIR,
            config.webBundleDir ? path.resolve(__dirname, config.webBundleDir) : null,
            path.resolve(__dirname, '..', '..', 'canvas-ui'),
            path.resolve(__dirname, '..', 'canvas-ui'),
            path.resolve(process.cwd(), 'canvas-ui'),
            process.env.FLOWORK_PORTABLE_ROOT ? path.resolve(process.env.FLOWORK_PORTABLE_ROOT, '..', 'canvas-ui') : null,
            process.env.FLOWORK_PORTABLE_ROOT ? path.resolve(process.env.FLOWORK_PORTABLE_ROOT, 'canvas-ui') : null,
        ].filter(Boolean);
        const resolvedGuiDir = guiCandidates.find(p => fs.existsSync(p));
        if (resolvedGuiDir) {
            args.push(`--web_bundle_path=${resolvedGuiDir}`);
        }
    }

    return args;
}

/**
 * Returns updater configuration (feed URL & headers)
 */
function getUpdaterConfig() {
    const endpoints = getGoogleEndpoints();
    const identity = getIdentityHeaders();
    return {
        updaterBaseUrl: endpoints.updaterBaseUrl,
        ideUpdaterBaseUrl: endpoints.ideUpdaterBaseUrl,
        headers: identity.headers
    };
}

/**
 * Check connectivity to Google Server endpoints
 */
async function testConnectivity() {
    const endpoints = getGoogleEndpoints();
    return new Promise((resolve) => {
        if (!endpoints.apiServerUrl) {
            resolve({ online: false, error: 'No apiServerUrl configured' });
            return;
        }
        const req = https.get(endpoints.apiServerUrl, { timeout: 3000 }, (res) => {
            resolve({ online: true, statusCode: res.statusCode });
        });
        req.on('error', (err) => {
            resolve({ online: false, error: err.message });
        });
    });
}

/**
 * Returns externalized custom links (docs, changelog, pricing, etc.)
 */
function getCustomLinks() {
    const config = loadConfig();
    return config.customLinks || {};
}

/**
 * Returns sound files configuration
 */
function getSoundFiles() {
    const config = loadConfig();
    return config.soundFiles || {};
}

/**
 * Returns feedback submission configuration
 */
function getFeedbackConfig() {
    const config = loadConfig();
    return config.feedback || { enabled: false, feedbackUrl: '' };
}

/**
 * Returns model catalog and default configuration (Resolves Embedded vs Custom via .env)
 */
function getModelCatalog() {
    try {
        const modelResolver = require('../model_resolver');
        return modelResolver.getModelCatalog();
    } catch (_) {
        const config = loadConfig();
        return config.models || { defaultOverride: 'gemini-3.8-flash-high', catalog: [] };
    }
}

module.exports = {
    loadConfig,
    getGoogleEndpoints,
    getIdentityHeaders,
    getAuthConfig,
    getCliArgs,
    getUpdaterConfig,
    getCustomLinks,
    getSoundFiles,
    getFeedbackConfig,
    getModelCatalog,
    testConnectivity
};
Object.defineProperty(module.exports, 'config', {
    get: loadConfig,
    enumerable: true,
    configurable: true
});
// @endlock
