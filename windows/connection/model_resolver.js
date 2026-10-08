/**
 * ⚡ FLOWORK OS — DYNAMIC MODEL RESOLVER (EMBEDDED vs CUSTOM)
 * ==========================================================
 * Component: CONECTION/model_resolver.js
 * Authority: awenkaudico & teguhfx (Level 99 Super Admin)
 * Purpose  : Resolve model catalog based on .env configuration:
 *            - "default": Use embedded Antygravity Pro catalog (14 official models) inside binary
 *            - "custom" : Use user's external endpoints.json / models.json outside binary
 */

const fs = require('fs');
const path = require('path');

// ── 1. Official Antygravity Pro Embedded Catalog (Baked In) ──
const EMBEDDED_ANTYGRAVITY_CATALOG = {
    defaultOverride: "gemini-3.8-flash-high",
    supportedClients: ["ccpa", "gemini"],
    catalog: [
        { id: "gemini-3.8-flash-high", name: "Gemini 3.8 Flash (High)", provider: "google", badge: "RECOMMENDED", badgeClass: "badge-recommended", desc: "Flagship high-speed deep thinking model", description: "Flagship high-speed deep thinking model" },
        { id: "gemini-3.8-flash-medium", name: "Gemini 3.8 Flash (Medium)", provider: "google", badge: "THINKING", badgeClass: "badge-thinking", desc: "Balanced high-performance thinking model", description: "Balanced high-performance thinking model" },
        { id: "gemini-3.8-flash-low", name: "Gemini 3.8 Flash (Low)", provider: "google", badge: "FAST", badgeClass: "badge-fast", desc: "Fast lightweight reasoning model", description: "Fast lightweight reasoning model" },
        { id: "gemini-3.7-flash-high", name: "Gemini 3.7 Flash (High)", provider: "google", badge: "FRONTIER", badgeClass: "badge-pro", desc: "High reasoning frontier flash model", description: "High reasoning frontier flash model" },
        { id: "gemini-3.7-flash-medium", name: "Gemini 3.7 Flash (Medium)", provider: "google", badge: "AGILE", badgeClass: "badge-fast", desc: "Fast agile coding and agent execution", description: "Fast agile coding and agent execution" },
        { id: "gemini-3.7-flash-low", name: "Gemini 3.7 Flash (Low)", provider: "google", badge: "ITERATION", badgeClass: "badge-fast", desc: "Low latency fast iteration model", description: "Low latency fast iteration model" },
        { id: "gemini-3.6-flash-high", name: "Gemini 3.6 Flash (High)", provider: "google", badge: "ACCURACY", badgeClass: "badge-pro", desc: "High accuracy coding model", description: "High accuracy coding model" },
        { id: "gemini-3.6-flash-medium", name: "Gemini 3.6 Flash (Medium)", provider: "google", badge: "STANDARD", badgeClass: "badge-fast", desc: "Standard high speed model", description: "Standard high speed model" },
        { id: "gemini-3.6-flash-low", name: "Gemini 3.6 Flash (Low)", provider: "google", badge: "LOW-LATENCY", badgeClass: "badge-fast", desc: "Low latency coding model", description: "Low latency coding model" },
        { id: "gemini-pro-agent", name: "Gemini Pro Agent", provider: "google", badge: "AGENTIC", badgeClass: "badge-recommended", desc: "Frontier agentic model for complex multi-step workflows", description: "Frontier agentic model for complex multi-step workflows" },
        { id: "gemini-3.1-pro-low", name: "Gemini 3.1 Pro (Low)", provider: "google", badge: "PRO ARCH", badgeClass: "badge-thinking", desc: "Frontier Pro deep architecture model", description: "Frontier Pro deep architecture model" },
        { id: "claude-sonnet-4-6", name: "Claude Sonnet 4.6 (Thinking)", provider: "anthropic", badge: "ANTHROPIC", badgeClass: "badge-anthropic", desc: "Anthropic coding specialist with extended thinking", description: "Anthropic coding specialist with extended thinking" },
        { id: "claude-opus-4-6-thinking", name: "Claude Opus 4.6 (Thinking)", provider: "anthropic", badge: "OPUS DEEP", badgeClass: "badge-anthropic", desc: "Anthropic maximum reasoning capacity model", description: "Anthropic maximum reasoning capacity model" },
        { id: "gpt-oss-120b-medium", name: "GPT-OSS 120B (Medium)", provider: "oss", badge: "OPEN WEIGHTS", badgeClass: "badge-weights", desc: "Open-weights large-scale autonomous coding model", description: "Open-weights large-scale autonomous coding model" }
    ]
};

// ── 2. Lightweight Zero-Dependency .env Loader ──
function loadEnv() {
    const candidates = [
        process.env.FLOWORK_ENV_PATH,
        path.join(process.cwd(), '.env'),
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

// ── 3. Resolve Model Catalog (Default vs Custom) ──
function getModelCatalog() {
    loadEnv();
    const mode = (process.env.FLOWORK_MODEL_MODE || 'default').toLowerCase().trim();

    if (mode === 'custom') {
        const customCandidates = process.env.FLOWORK_CUSTOM_MODELS_PATH
            ? [process.env.FLOWORK_CUSTOM_MODELS_PATH]
            : [
                path.join(process.cwd(), 'endpoints.json'),
                path.join(process.cwd(), 'models.json'),
                path.join(__dirname, '..', 'endpoints.json'),
                path.join(__dirname, 'endpoints.json')
            ];

        for (const p of customCandidates) {
            if (fs.existsSync(p)) {
                try {
                    const raw = fs.readFileSync(p, 'utf8');
                    const parsed = JSON.parse(raw);
                    
                    let catalogObj = null;
                    if (parsed.models && Array.isArray(parsed.models.catalog)) {
                        catalogObj = parsed.models;
                    } else if (Array.isArray(parsed.catalog)) {
                        catalogObj = parsed;
                    } else if (Array.isArray(parsed)) {
                        catalogObj = { defaultOverride: parsed[0]?.id || 'custom-model', catalog: parsed };
                    }

                    if (catalogObj && Array.isArray(catalogObj.catalog) && catalogObj.catalog.length > 0) {
                        return {
                            defaultOverride: catalogObj.defaultOverride || catalogObj.catalog[0]?.id || 'gemini-3.8-flash-high',
                            supportedClients: catalogObj.supportedClients || ["ccpa", "gemini"],
                            catalog: catalogObj.catalog,
                            source: 'custom',
                            path: p
                        };
                    }
                } catch (err) {
                    console.warn(`[Model Resolver] ⚠️ Failed to parse custom model file at ${p}:`, err.message);
                }
            }
        }
        console.warn('[Model Resolver] ⚠️ Mode "custom" specified but no valid file found. Falling back to default embedded catalog.');
    }

    // Default mode: Return embedded official catalog
    return {
        ...EMBEDDED_ANTYGRAVITY_CATALOG,
        source: 'default'
    };
}

module.exports = {
    getModelCatalog,
    loadEnv,
    EMBEDDED_ANTYGRAVITY_CATALOG
};
