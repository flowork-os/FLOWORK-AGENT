/**
 * ⚡ FLOWORK OS — OPENAI TO GEMINI SSE STREAM TRANSFORMER
 * ======================================================
 * Component: CONECTION/bridge/translators/openai_to_gemini.js
 * Authority: awenkaudico & teguhfx (Level 99 Super Admin)
 * Purpose  : Transform real-time OpenAI/DeepSeek/Ollama SSE stream to Gemini SSE format for Flowork OS.
 */

const { Transform } = require('stream');

class OpenAiToGeminiStream extends Transform {
    constructor(options = {}) {
        super(options);
        this.buffer = '';
        this.activeToolCalls = new Map(); // index -> { id, name, argsBuffer }
        this.hasEmittedContent = false;
        this.modelName = options.modelName || 'flowork-custom-model';
    }

    _transform(chunk, encoding, callback) {
        this.buffer += chunk.toString('utf8');
        const lines = this.buffer.split('\n');
        this.buffer = lines.pop() || ''; // Keep partial line in buffer

        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith(':')) continue; // Comment or empty line

            if (trimmed.startsWith('data:')) {
                const dataStr = trimmed.slice(5).trim();
                if (dataStr === '[DONE]') {
                    this._flushToolCalls();
                    this._emitStop();
                    continue;
                }

                try {
                    const parsed = JSON.parse(dataStr);
                    this._processOpenAiChunk(parsed);
                } catch (e) {
                    // Ignore malformed partial JSON chunks
                }
            }
        }
        callback();
    }

    _flush(callback) {
        if (this.buffer.trim()) {
            const line = this.buffer.trim();
            if (line.startsWith('data:')) {
                const dataStr = line.slice(5).trim();
                if (dataStr !== '[DONE]') {
                    try {
                        const parsed = JSON.parse(dataStr);
                        this._processOpenAiChunk(parsed);
                    } catch (_) {}
                }
            }
        }
        this._flushToolCalls();
        this._emitStop();
        callback();
    }

    _processOpenAiChunk(chunk) {
        const choice = chunk.choices?.[0];
        if (!choice) return;

        const delta = choice.delta || {};

        // 1. Handle Text Content
        if (delta.content) {
            this.hasEmittedContent = true;
            const geminiChunk = {
                candidates: [
                    {
                        content: {
                            role: 'model',
                            parts: [{ text: delta.content }]
                        },
                        finishReason: null
                    }
                ]
            };
            this.push(`data: ${JSON.stringify(geminiChunk)}\n\n`);
        }

        // 2. Accumulate Tool Calls
        if (Array.isArray(delta.tool_calls)) {
            for (const tc of delta.tool_calls) {
                const idx = tc.index ?? 0;
                if (!this.activeToolCalls.has(idx)) {
                    this.activeToolCalls.set(idx, {
                        id: tc.id || `call_${idx}`,
                        name: tc.function?.name || '',
                        argsBuffer: tc.function?.arguments || ''
                    });
                } else {
                    const existing = this.activeToolCalls.get(idx);
                    if (tc.id) existing.id = tc.id;
                    if (tc.function?.name) existing.name += tc.function.name;
                    if (tc.function?.arguments) existing.argsBuffer += tc.function.arguments;
                }
            }
        }

        // 3. Check Finish Reason
        if (choice.finish_reason === 'tool_calls' || choice.finish_reason === 'stop') {
            this._flushToolCalls();
        }
    }

    _flushToolCalls() {
        if (this.activeToolCalls.size === 0) return;

        for (const [idx, tc] of this.activeToolCalls.entries()) {
            let parsedArgs = {};
            try {
                parsedArgs = JSON.parse(tc.argsBuffer);
            } catch (_) {
                // If arguments were unparsed string, wrap or pass as is
                parsedArgs = { raw: tc.argsBuffer };
            }

            const toolChunk = {
                candidates: [
                    {
                        content: {
                            role: 'model',
                            parts: [
                                {
                                    functionCall: {
                                        name: tc.name,
                                        args: parsedArgs
                                    }
                                }
                            ]
                        },
                        finishReason: null
                    }
                ]
            };
            this.push(`data: ${JSON.stringify(toolChunk)}\n\n`);
        }
        this.activeToolCalls.clear();
    }

    _emitStop() {
        const stopChunk = {
            candidates: [
                {
                    content: {
                        role: 'model',
                        parts: []
                    },
                    finishReason: 'STOP'
                }
            ],
            usageMetadata: {
                promptTokenCount: 0,
                candidatesTokenCount: 0,
                totalTokenCount: 0
            }
        };
        this.push(`data: ${JSON.stringify(stopChunk)}\n\n`);
    }
}

module.exports = {
    OpenAiToGeminiStream
};
