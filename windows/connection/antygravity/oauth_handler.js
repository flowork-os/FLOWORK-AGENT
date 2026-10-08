// @lock: CONECTION/antygravity/oauth_handler.js (SOVEREIGN LOCKED COMPONENT)
const googleServer = require('./google_server');

/**
 * Generates Google OAuth2 authorization URL
 */
function buildAuthUrl({ codeChallenge, state, redirectUri }) {
    const config = googleServer.loadConfig();
    const auth = config.auth || {};
    const effectiveClientId = (auth.clientId && !auth.clientId.includes('MANAGED')) ? auth.clientId : '[MANAGED_AT_EDGE_BY_FLOWORKOS]';
    const params = new URLSearchParams({
        access_type: 'offline',
        client_id: effectiveClientId,
        code_challenge: codeChallenge || '',
        code_challenge_method: 'S256',
        prompt: 'consent',
        redirect_uri: redirectUri,
        response_type: 'code',
        scope: (auth.scopes || []).join(' '),
        state: state
    });
    return `${auth.authUrl || ''}?${params.toString()}`;
}

/**
 * Validates Google OAuth callback parameters
 */
function validateCallback(query) {
    if (query.error) {
        return { success: false, error: query.error };
    }
    if (!query.code) {
        return { success: false, error: 'Missing authorization code' };
    }
    return { success: true, code: query.code, state: query.state };
}

module.exports = {
    buildAuthUrl,
    validateCallback
};
// @endlock
