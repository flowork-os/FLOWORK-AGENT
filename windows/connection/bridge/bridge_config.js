/**
 * ⚡ FLOWORK OS — UNIVERSAL BRIDGE CONFIGURATION
 * ============================================
 * Component: CONECTION/bridge/bridge_config.js
 * Authority: awenkaudico & teguhfx (Level 99 Super Admin)
 * Purpose  : Manage router mode (default vs custom) and provider settings.
 */

const fs = require('fs');
const path = require('path');

function loadEnv() {
    const candidates = [
        process.env.FLOWORK_ENV_PATH,
        path.join(process.cwd(), '.env'),
        path.join(__dirname, '..', '..', '.env'),
        path.join(__dirname, '..', '.env'),
        path.join(__dirname, '.env')
    ].filter(Boolean);

    for (const p of candidates) {
        if (fs.existsSync(p)) {
            try {
                const lines = fs.readFileSync(p, 'utf8').split('\n');
                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed || trimmed.startsWith('#')) continue;
                    const eqIdx = trimmed.indexOf('=');
                    if (eqIdx !== -1) {
                        const key = trimmed.slice(0, eqIdx).trim();
                        let val = trimmed.slice(eqIdx + 1).trim();
                        if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
                            val = val.slice(1, -1);
                        }
                        if (process.env[key] === undefined) {
                            process.env[key] = val;
                        }
                    }
                }
                break;
            } catch (_) {}
        }
    }
}

function isCustomMode() {
    loadEnv();
    const mode = (process.env.FLOWORK_ROUTER_MODE || 'default').toLowerCase().trim();
    return mode === 'custom';
}

function getConfig() {
    loadEnv();
    const mode = (process.env.FLOWORK_ROUTER_MODE || 'default').toLowerCase().trim();
    const provider = (process.env.FLOWORK_CUSTOM_PROVIDER || 'deepseek').toLowerCase().trim();
    
    // Default URL and Model mapping per provider
    let defaultBaseUrl = 'https://api.deepseek.com/v1';
    let defaultModel = 'deepseek-chat';
    
    if (provider === 'openai') {
        defaultBaseUrl = 'https://api.openai.com/v1';
        defaultModel = 'gpt-4o';
    } else if (provider === 'ollama') {
        defaultBaseUrl = 'http://127.0.0.1:11434/v1';
        defaultModel = 'deepseek-r1:14b';
    } else if (provider === 'openrouter') {
        defaultBaseUrl = 'https://openrouter.ai/api/v1';
        defaultModel = 'deepseek/deepseek-chat';
    } else if (provider === 'groq') {
        defaultBaseUrl = 'https://api.groq.com/openai/v1';
        defaultModel = 'llama-3.3-70b-versatile';
    }

    const baseUrl = process.env.FLOWORK_CUSTOM_BASE_URL || defaultBaseUrl;
    const apiKey = process.env.FLOWORK_CUSTOM_API_KEY || (provider === 'ollama' ? 'ollama' : '');
    const model = process.env.FLOWORK_CUSTOM_MODEL || defaultModel;

    return {
        mode,
        provider,
        baseUrl: baseUrl.replace(/\/+$/, ''),
        apiKey,
        model
    };
}

module.exports = {
    loadEnv,
    isCustomMode,
    getConfig
};
