/**
 * ⚡ FLOWORK OS — UNIVERSAL BRIDGE DISPATCHER
 * ==========================================
 * Component: CONECTION/bridge/bridge_dispatcher.js
 * Authority: awenkaudico & teguhfx (Level 99 Super Admin)
 * Purpose  : Intercept and translate AI requests when FLOWORK_ROUTER_MODE=custom.
 */

const { isCustomMode, getConfig } = require('./bridge_config');
const { handleMockRoute } = require('./mock_engine');
const { geminiToOpenAi } = require('./translators/gemini_to_openai');
const { OpenAiToGeminiStream } = require('./translators/openai_to_gemini');
const { sendChatCompletionStream } = require('./providers/openai_driver');

function shouldHandle(pathname) {
    if (!isCustomMode()) return false;

    const isMock = pathname.includes(':loadCodeAssist') ||
                   pathname.includes(':retrieveUserQuota') ||
                   pathname.includes('UserQuotaSummary') ||
                   pathname.includes(':listExperiments') ||
                   pathname.includes('/flwcoreNux') ||
                   pathname.includes('Nuxes') ||
                   pathname.includes('SurgeonNux') ||
                   pathname.includes(':fetchAvailableModels') ||
                   pathname.includes(':listModels');

    const isAi = !isMock && (
        pathname.includes('GenerateContent') ||
        pathname.includes('generate') ||
        pathname.includes('predict')
    );

    return isMock || isAi;
}

async function handleRequest(req, res, parsedUrl, pathname, port) {
    const config = getConfig();

    const isMock = pathname.includes(':loadCodeAssist') ||
                   pathname.includes(':retrieveUserQuota') ||
                   pathname.includes('UserQuotaSummary') ||
                   pathname.includes(':listExperiments') ||
                   pathname.includes('/flwcoreNux') ||
                   pathname.includes('Nuxes') ||
                   pathname.includes('SurgeonNux') ||
                   pathname.includes(':fetchAvailableModels') ||
                   pathname.includes(':listModels');

    if (isMock) {
        return handleMockRoute(req, res, pathname, config);
    }

    // AI Inference Request
    let rawBody = '';
    req.on('data', chunk => { rawBody += chunk.toString('utf8'); });
    req.on('end', () => {
        let geminiPayload = {};
        try {
            geminiPayload = JSON.parse(rawBody || '{}');
        } catch (e) {
            res.statusCode = 400;
            return res.end(JSON.stringify({ error: 'Malformed JSON payload' }));
        }

        console.log(`[Universal Bridge] 🌉 Routing AI request to custom provider: [${config.provider.toUpperCase()}] Model: ${config.model} (${config.baseUrl})`);

        const openAiPayload = geminiToOpenAi(geminiPayload, config.model);

        // Prepare SSE Response Headers for Flowork OS
        if (res.writeHead) {
            res.writeHead(200, {
                'Content-Type': 'text/event-stream; charset=utf-8',
                'Cache-Control': 'no-cache, no-transform',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'X-Flowork-Bridge-Provider': config.provider,
                'X-Flowork-Bridge-Model': config.model
            });
        }

        const transformer = new OpenAiToGeminiStream({ modelName: config.model });

        transformer.on('data', chunk => {
            if (res.write) res.write(chunk);
        });

        transformer.on('end', () => {
            if (res.end) res.end();
        });

        transformer.on('error', err => {
            console.error('[Universal Bridge] Transformer error:', err.message);
            if (res.end) res.end();
        });

        sendChatCompletionStream(
            config,
            openAiPayload,
            (upstreamStream) => {
                upstreamStream.pipe(transformer);
            },
            (err) => {
                console.error(`[Universal Bridge] ❌ Upstream failure:`, err.message);
                const errorChunk = {
                    candidates: [
                        {
                            content: {
                                role: 'model',
                                parts: [
                                    {
                                        text: `\n\n⚠️ **[FLOWORK OS BRIDGE ERROR]**\nGagal terhubung ke custom provider \`${config.provider}\` (${config.baseUrl}):\n\`\`\`\n${err.message}\n\`\`\`\n*Periksa FLOWORK_CUSTOM_API_KEY atau koneksi model di .env.*`
                                    }
                                ]
                            },
                            finishReason: 'STOP'
                        }
                    ]
                };
                if (res.write) res.write(`data: ${JSON.stringify(errorChunk)}\n\n`);
                if (res.end) res.end();
            }
        );
    });
}

module.exports = {
    isCustomMode,
    getConfig,
    shouldHandle,
    handleRequest
};
