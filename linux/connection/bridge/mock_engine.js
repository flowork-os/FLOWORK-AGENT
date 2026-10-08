/**
 * ⚡ FLOWORK OS — CUSTOM BRIDGE MOCK ENGINE
 * ========================================
 * Component: CONECTION/bridge/mock_engine.js
 * Authority: awenkaudico & teguhfx (Level 99 Super Admin)
 * Purpose  : Satisfy Flowork OS initialization routes (:loadCodeAssist, :retrieveUserQuota, etc.)
 */

function handleMockRoute(req, res, pathname, config) {
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Access-Control-Allow-Origin', '*');

    // 1. Load Code Assist / Entitlement Check
    if (pathname.includes(':loadCodeAssist')) {
        return res.end(JSON.stringify({
            allowed: true,
            currentTier: {
                id: 'enterprise-tier',
                name: `Custom Engine (${config.provider})`
            },
            cloudaicompanionProject: 'flowork-custom-bridge',
            paidTier: {
                id: 'enterprise-tier',
                name: 'Custom Provider Bridge'
            }
        }));
    }

    // 2. User Quota
    if (pathname.includes(':retrieveUserQuota') || pathname.includes('UserQuotaSummary')) {
        return res.end(JSON.stringify({
            remainingQuota: 999999999,
            totalQuota: 999999999,
            unlimited: true
        }));
    }

    // 3. Experiments / NUX
    if (pathname.includes(':listExperiments')) {
        return res.end(JSON.stringify({
            experiments: []
        }));
    }

    if (pathname.includes('/flwcoreNux') || pathname.includes('Nuxes') || pathname.includes('SurgeonNux')) {
        return res.end(JSON.stringify({
            allowed: true,
            status: 'COMPLETED'
        }));
    }

    // 4. Model Catalog
    if (pathname.includes(':fetchAvailableModels') || pathname.includes(':listModels')) {
        return res.end(JSON.stringify({
            models: [
                {
                    id: config.model,
                    name: `Custom [${config.provider.toUpperCase()}]: ${config.model}`,
                    provider: config.provider,
                    description: `Active model routed to ${config.baseUrl}`
                },
                {
                    id: 'flowork-pro',
                    name: 'Flowork Pro Sovereign (Default)',
                    provider: 'flowork',
                    description: 'Official Sovereign Multi-Account Pool'
                }
            ],
            defaultModel: config.model
        }));
    }

    // Fallback Mock
    return res.end(JSON.stringify({
        status: 'OK',
        authority: 'FloworkOS-CustomBridge'
    }));
}

module.exports = {
    handleMockRoute
};
