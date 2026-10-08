/**
 * ⚡ FLOWORK OS — OPENAI COMPATIBLE UPSTREAM DRIVER
 * =================================================
 * Component: CONECTION/bridge/providers/openai_driver.js
 * Authority: awenkaudico & teguhfx (Level 99 Super Admin)
 * Purpose  : Stream HTTP/HTTPS requests to OpenAI, DeepSeek, Ollama, Groq, OpenRouter.
 */

const http = require('http');
const https = require('https');
const { URL } = require('url');

function sendChatCompletionStream(config, payload, onStreamReady, onError) {
    try {
        const endpointUrl = new URL(`${config.baseUrl}/chat/completions`);
        const isHttps = endpointUrl.protocol === 'https:';
        const client = isHttps ? https : http;

        const bodyData = Buffer.from(JSON.stringify(payload), 'utf8');

        const headers = {
            'Content-Type': 'application/json',
            'Content-Length': bodyData.length,
            'User-Agent': 'FloworkOS-UniversalBridge/2.16.0'
        };

        if (config.apiKey) {
            headers['Authorization'] = `Bearer ${config.apiKey}`;
        }

        const reqOptions = {
            method: 'POST',
            hostname: endpointUrl.hostname,
            port: endpointUrl.port || (isHttps ? 443 : 80),
            path: endpointUrl.pathname + endpointUrl.search,
            headers,
            timeout: 120000 // 2 minutes timeout for thinking models
        };

        const upstreamReq = client.request(reqOptions, (upstreamRes) => {
            if (upstreamRes.statusCode && upstreamRes.statusCode >= 400) {
                let errBody = '';
                upstreamRes.on('data', d => { errBody += d.toString('utf8'); });
                upstreamRes.on('end', () => {
                    const err = new Error(`[Custom Bridge] Upstream error HTTP ${upstreamRes.statusCode}: ${errBody}`);
                    err.statusCode = upstreamRes.statusCode;
                    onError(err);
                });
                return;
            }

            onStreamReady(upstreamRes);
        });

        upstreamReq.on('error', (err) => {
            onError(new Error(`[Custom Bridge] Connection failure to ${config.baseUrl}: ${err.message}`));
        });

        upstreamReq.on('timeout', () => {
            upstreamReq.destroy();
            onError(new Error(`[Custom Bridge] Connection timed out after 120s to ${config.baseUrl}`));
        });

        upstreamReq.write(bodyData);
        upstreamReq.end();

    } catch (err) {
        onError(err);
    }
}

module.exports = {
    sendChatCompletionStream
};
