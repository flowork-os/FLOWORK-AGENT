/**
 * ⚡ FLOWORK OS — GEMINI TO OPENAI PROTOCOL TRANSLATOR
 * ===================================================
 * Component: CONECTION/bridge/translators/gemini_to_openai.js
 * Authority: awenkaudico & teguhfx (Level 99 Super Admin)
 * Purpose  : Convert Google CCPA/Gemini AST request payload to OpenAI Chat Completion payload.
 */

const { sanitizeSchema } = require('./schema_sanitizer');

function geminiToOpenAi(geminiPayload, targetModel) {
    const rawReq = geminiPayload.request || geminiPayload;
    const contents = rawReq.contents || [];
    const systemInstruction = rawReq.systemInstruction;
    const tools = rawReq.tools || [];
    const genConfig = rawReq.generationConfig || {};

    const messages = [];
    let toolCallCounter = 0;
    const pendingToolCalls = new Map(); // functionName -> latest call_id

    // 1. Process System Instruction
    if (systemInstruction && systemInstruction.parts) {
        const sysText = systemInstruction.parts
            .filter(p => p.text)
            .map(p => p.text)
            .join('\n\n')
            .trim();
        if (sysText) {
            messages.push({
                role: 'system',
                content: sysText
            });
        }
    }

    // 2. Process Contents (User, Model, Tool Call, Tool Response)
    for (const turn of contents) {
        const role = turn.role === 'model' ? 'assistant' : 'user';
        const parts = turn.parts || [];

        let textAccumulator = '';
        const toolCalls = [];
        const toolResponses = [];

        for (const part of parts) {
            if (part.text) {
                textAccumulator += (textAccumulator ? '\n' : '') + part.text;
            }

            if (part.functionCall) {
                toolCallCounter++;
                const callId = `call_flw_${toolCallCounter}_${Date.now().toString(36)}`;
                pendingToolCalls.set(part.functionCall.name, callId);

                toolCalls.push({
                    id: callId,
                    type: 'function',
                    function: {
                        name: part.functionCall.name,
                        arguments: typeof part.functionCall.args === 'string'
                            ? part.functionCall.args
                            : JSON.stringify(part.functionCall.args || {})
                    }
                });
            }

            if (part.functionResponse) {
                const fnName = part.functionResponse.name;
                const callId = pendingToolCalls.get(fnName) || `call_flw_reply_${toolCallCounter}`;
                const rawResp = part.functionResponse.response;
                const resultVal = rawResp?.result !== undefined ? rawResp.result : rawResp;
                const contentStr = typeof resultVal === 'string'
                    ? resultVal
                    : JSON.stringify(resultVal || {});

                toolResponses.push({
                    role: 'tool',
                    tool_call_id: callId,
                    name: fnName,
                    content: contentStr
                });
            }
        }

        // Add assistant message
        if (role === 'assistant') {
            const msg = { role: 'assistant' };
            if (textAccumulator) msg.content = textAccumulator;
            if (toolCalls.length > 0) msg.tool_calls = toolCalls;
            if (!msg.content && (!msg.tool_calls || msg.tool_calls.length === 0)) {
                msg.content = '';
            }
            messages.push(msg);
        } else {
            // User message or Tool responses
            if (textAccumulator) {
                messages.push({
                    role: 'user',
                    content: textAccumulator
                });
            }
            for (const tr of toolResponses) {
                messages.push(tr);
            }
        }
    }

    // 3. Process Function Declarations (Tools)
    const openAiTools = [];
    for (const toolGroup of tools) {
        const declarations = toolGroup.functionDeclarations || [];
        for (const decl of declarations) {
            openAiTools.push({
                type: 'function',
                function: {
                    name: decl.name,
                    description: decl.description || '',
                    parameters: sanitizeSchema(decl.parameters || { type: 'object', properties: {} })
                }
            });
        }
    }

    // 4. Construct Final OpenAI Chat Completion Payload
    const openAiPayload = {
        model: targetModel,
        messages,
        stream: true
    };

    if (openAiTools.length > 0) {
        openAiPayload.tools = openAiTools;
        openAiPayload.tool_choice = 'auto';
    }

    if (genConfig.temperature !== undefined) {
        openAiPayload.temperature = genConfig.temperature;
    }

    if (genConfig.maxOutputTokens !== undefined) {
        openAiPayload.max_tokens = genConfig.maxOutputTokens;
    }

    return openAiPayload;
}

module.exports = {
    geminiToOpenAi
};
