// @lock: CONECTION/antygravity/index.js (SOVEREIGN LOCKED COMPONENT)
const googleServer = require('./google_server');
const oauthHandler = require('./oauth_handler');
const router = require('./router');

module.exports = {
    // Identity & Config
    name: 'antygravity',
    displayName: '⚡ Antigravity (Google)',
    loadConfig: googleServer.loadConfig,
    getGoogleEndpoints: googleServer.getGoogleEndpoints,
    getIdentityHeaders: googleServer.getIdentityHeaders,
    getAuthConfig: googleServer.getAuthConfig,
    getCliArgs: googleServer.getCliArgs,
    getUpdaterConfig: googleServer.getUpdaterConfig,
    getCustomLinks: googleServer.getCustomLinks,
    getSoundFiles: googleServer.getSoundFiles,
    getFeedbackConfig: googleServer.getFeedbackConfig,
    getModelCatalog: googleServer.getModelCatalog,
    testConnectivity: googleServer.testConnectivity,

    // OAuth Handlers
    buildAuthUrl: oauthHandler.buildAuthUrl,
    validateCallback: oauthHandler.validateCallback,
    exchangeGoogleOAuthCode: router.exchangeGoogleOAuthCode,
    fetchGoogleUserInfo: router.fetchGoogleUserInfo,

    // Vault & Token Management
    loadVault: router.loadVault,
    saveVault: router.saveVault,
    refreshGoogleTokenIfNeeded: router.refreshGoogleTokenIfNeeded,
    refreshTokenIfNeeded: router.refreshGoogleTokenIfNeeded,
    getEndpoints: googleServer.getGoogleEndpoints,

    // Router Request Dispatcher
    handleRequest: router.handleRequest
};
// @endlock
