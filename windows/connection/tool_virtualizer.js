// [FLOWORKOS:NANO-PLUG] - tool_virtualizer.js
// Module: FloworkOSToolVirtualizer (Universal Tool Virtualizer & Schema Bridge)
// Doctrine: Agnostic Manifest, Plug & Play Circuit-Breaker, Nano-Modular, Multi-OS
// Bridges Flowork Universal Surgical Tools <-> Native Host Runtimes & FlowAI Engine

const fs = require('fs');
const path = require('path');

// Active detected client mode stored on global to prevent desync across require() calls
if (!global.__FLOWORK_CLIENT_MODE__) {
    global.__FLOWORK_CLIENT_MODE__ = 'flowork';
}

// Mapping for FlowAI CLI Engine (x-agent / flowai.js)
const FLOWAI_NATIVE_MAP = {
    run_command: 'run_shell_command',
    view_file: 'read_file',
    write_to_file: 'write_file',
    replace_file_content: 'replace',
    multi_replace_file_content: 'replace',
    list_dir: 'list_directory',
    search_web: 'flowos_web_search',
    read_url_content: 'web_fetch',
    ask_question: 'ask_user',
    invoke_subagent: 'invoke_subagent',
    schedule: 'schedule',
    manage_task: 'manage_task',
    generate_image: 'generate_image',
    send_message: 'send_message',
    search_tools: 'search_tools',
    canvas_control: 'canvas_control'
};

// Legacy alias mapping: maps old flow_* names to Universal Standard Tools
const LEGACY_FLOW_TO_STANDARD_MAP = {
    flow_exec: 'run_command',
    flow_inspect: 'view_file',
    flow_forge: 'write_to_file',
    flow_splice: 'replace_file_content',
    flow_multi_splice: 'replace_file_content',
    flow_tree: 'run_command',
    flow_locate: 'run_command',
    flow_recon: 'search_web',
    flow_ingest: 'read_url_content',
    flow_consult: 'ask_question',
    flow_delegate: 'invoke_subagent',
    flow_architect: 'define_subagent',
    flow_swarm: 'manage_subagents',
    flow_chronos: 'schedule',
    flow_schedule: 'schedule',
    flow_taskmaster: 'manage_task',
    flow_canvas: 'generate_image',
    flow_dispatch: 'send_message',
    flow_screenshot: 'screenshot',
    flow_send_media: 'send_media',
    flow_sys_health: 'sys_health',
    flow_search_tools: 'search_tools',
    flow_audit_portability: 'audit_portability',
    flow_audit_security: 'audit_security'
};

// Reverse map: maps any alternative or legacy name -> Universal Standard Tool names
const REVERSE_MAP = {
    // FlowAI CLI tools -> Standard tools
    run_shell_command: 'run_command',
    read_file: 'view_file',
    write_file: 'write_to_file',
    replace: 'replace_file_content',
    list_directory: 'run_command',
    flowos_web_search: 'search_web',
    web_fetch: 'read_url_content',
    ask_user: 'ask_question',

    // Other common aliases
    run_shell_cmd: 'run_command',
    edit_file: 'replace_file_content',
    create_file: 'write_to_file',
    multi_replace_file_content: 'replace_file_content',
    grep_search: 'run_command',
    grep: 'run_command',
    list_dir: 'run_command',
    glob: 'run_command',
    web_search: 'search_web',

    // Legacy Flowork aliases -> Standard tools
    ...LEGACY_FLOW_TO_STANDARD_MAP
};

class FloworkOSToolVirtualizer {
    /**
     * Translates tool names in outbound LLM payload to Universal Standard Tools
     */
    static virtualizeToolsInPayload(payload) {
        if (!payload || typeof payload !== 'object') return payload;
        try {
            const reqObj = payload.request || payload;
            if (Array.isArray(reqObj.tools)) {
                const declaredNames = new Set();

                for (const toolGroup of reqObj.tools) {
                    if (Array.isArray(toolGroup.functionDeclarations)) {
                        for (const decl of toolGroup.functionDeclarations) {
                            if (!decl || !decl.name) continue;

                            // 1. Auto-detect client type based on declared tool names
                            if (decl.name.startsWith('flow_')) {
                                global.__FLOWORK_CLIENT_MODE__ = 'flowork';
                            } else if (decl.name === 'view_file' || decl.name === 'run_command' || decl.name === 'write_to_file' || decl.name === 'replace_file_content') {
                                global.__FLOWORK_CLIENT_MODE__ = 'standard';
                            } else if (decl.name === 'read_file' || decl.name === 'run_shell_command' || decl.name === 'replace') {
                                global.__FLOWORK_CLIENT_MODE__ = 'flowai';
                            }

                            // 2. Auto-detect client type based on parameter schema (only if not already detected as sovereign flowork)
                            if (global.__FLOWORK_CLIENT_MODE__ !== 'flowork' && decl.parameters && decl.parameters.properties) {
                                const props = Object.keys(decl.parameters.properties);
                                if (props.includes('AbsolutePath') || props.includes('CommandLine') || props.includes('TargetFile')) {
                                    global.__FLOWORK_CLIENT_MODE__ = 'standard';
                                } else if (props.includes('file_path') || (props.includes('command') && props.includes('dir_path')) || props.includes('old_string')) {
                                    global.__FLOWORK_CLIENT_MODE__ = 'flowai';
                                }
                            }

                            if (REVERSE_MAP[decl.name]) {
                                decl.name = REVERSE_MAP[decl.name];
                            }
                        }

                        // Filter out duplicate declarations across all groups
                        toolGroup.functionDeclarations = toolGroup.functionDeclarations.filter(decl => {
                            if (!decl || !decl.name) return false;
                            if (declaredNames.has(decl.name)) return false;
                            declaredNames.add(decl.name);
                            return true;
                        });
                    }
                }

                // Ensure invoke_subagent is present exactly once across all tool groups
                if (!declaredNames.has('invoke_subagent') && !declaredNames.has('flow_delegate')) {
                    if (!reqObj.tools[0]) reqObj.tools[0] = { functionDeclarations: [] };
                    if (!Array.isArray(reqObj.tools[0].functionDeclarations)) reqObj.tools[0].functionDeclarations = [];
                    reqObj.tools[0].functionDeclarations.push({
                        name: 'invoke_subagent',
                        description: 'Invokes one or more subagents by name with a single tool call. Each subagent runs in the background with its own prompt and reports back when done.',
                        parameters: {
                            type: 'OBJECT',
                            properties: {
                                Subagents: {
                                    type: 'ARRAY',
                                    items: {
                                        type: 'OBJECT',
                                        properties: {
                                            TypeName: { type: 'STRING', description: 'The type name of the subagent to invoke.' },
                                            Role: { type: 'STRING', description: 'A 2-5 word description of the subagent role.' },
                                            Prompt: { type: 'STRING', description: 'A clear, actionable task description for the subagent.' },
                                            Model: { type: 'STRING', description: 'Model to use ("inherit", "flash", "pro"). Default: "inherit".' }
                                        },
                                        required: ['TypeName', 'Role', 'Prompt']
                                    }
                                }
                            },
                            required: ['Subagents']
                        }
                    });
                    declaredNames.add('invoke_subagent');
                }

                // Ensure flow_lock is present exactly once across all tool groups
                if (!declaredNames.has('flow_lock')) {
                    if (!reqObj.tools[0]) reqObj.tools[0] = { functionDeclarations: [] };
                    if (!Array.isArray(reqObj.tools[0].functionDeclarations)) reqObj.tools[0].functionDeclarations = [];
                    reqObj.tools[0].functionDeclarations.push({
                        name: 'flow_lock',
                        description: 'Penguncian presisi gembok @lock / @frozen pada berkas atau blok kode untuk menjaga kesucian kode dari modifikasi atau rollback yang tidak disetujui.',
                        parameters: {
                            type: 'OBJECT',
                            properties: {
                                action: {
                                    type: 'STRING',
                                    description: 'Operasi gembok: "lock_file" (kunci seluruh file), "lock_block" (kunci bagian kode tertentu), "unlock" (buka gembok dengan otorisasi), "check" (periksa status gembok file), "list" (daftar seluruh file terkunci).'
                                },
                                target_file: {
                                    type: 'STRING',
                                    description: 'Jalur berkas yang akan dikunci, diperiksa, atau dibuka.'
                                },
                                target_content: {
                                    type: 'STRING',
                                    description: 'Potongan kode spesifik yang akan dibungkus gembok @lock ... @endlock (saat action="lock_block").'
                                },
                                reason: {
                                    type: 'STRING',
                                    description: 'Alasan penegakan gembok @lock (contoh: "Doktrin Kedaulatan Flowork OS", "Core Router Stabil").'
                                },
                                passcode: {
                                    type: 'STRING',
                                    description: 'Kata sandi otorisasi saat melakukan aksi "unlock".'
                                }
                            },
                            required: ['action']
                        }
                    });
                    declaredNames.add('flow_lock');
                }

                // Ensure search_tools is present exactly once across all tool groups
                if (!declaredNames.has('search_tools') && !declaredNames.has('flow_search_tools')) {
                    if (!reqObj.tools[0]) reqObj.tools[0] = { functionDeclarations: [] };
                    if (!Array.isArray(reqObj.tools[0].functionDeclarations)) reqObj.tools[0].functionDeclarations = [];
                    reqObj.tools[0].functionDeclarations.push({
                        name: 'search_tools',
                        description: 'Search and discover available external tools created by users in tools/ directory before declaring incapacity or writing ad-hoc scripts.',
                        parameters: {
                            type: 'OBJECT',
                            properties: {
                                query: {
                                    type: 'STRING',
                                    description: 'Keywords describing the required capability, file format, or action (e.g. "pdf extractor", "crypto price", "docker deploy")'
                                },
                                category: {
                                    type: 'STRING',
                                    description: 'Optional category filter (e.g. "utility", "devops", "document", "finance", "media")'
                                },
                                detail_level: {
                                    type: 'STRING',
                                    description: 'Detail level: "summary" (fast overview) or "full" (includes execution parameters and command schema)'
                                }
                            },
                            required: ['query']
                        }
                    });
                    declaredNames.add('search_tools');
                }
            }
        } catch (_) {}
        return FloworkOSToolVirtualizer.pruneOversizedToolOutputs(payload);
    }

    /**
     * Flowork Context Shield: Proactive & Reactive Trajectory Compaction
     * Prevents exceeding 1,048,576 token hard ceiling on Gemini upstream.
     * Truncates oversized tool outputs, arrays, and multiline dumps while preserving
     * structure, summary, health score, and top findings.
     */
    static pruneOversizedToolOutputs(payload, options = {}) {
        if (!payload || typeof payload !== 'object') return payload;
        const aggressive = !!options.aggressive;
        const maxArrayLen = aggressive ? 8 : 25;
        const maxStrLen = aggressive ? 6000 : 20000;
        const maxRawStrLen = aggressive ? 10000 : 30000;

        try {
            const reqObj = payload.request || payload;
            if (!Array.isArray(reqObj.contents)) return payload;

            const truncateStrWithHeadTail = (str, limit) => {
                if (typeof str !== 'string' || str.length <= limit) return str;
                const headLen = Math.floor(limit * 0.65);
                const tailLen = Math.floor(limit * 0.35);
                const truncatedCount = str.length - (headLen + tailLen);
                return str.slice(0, headLen) + 
                    `\n\n... [Flowork Context Shield: Truncated ${truncatedCount} characters to preserve 1M token budget] ...\n\n` + 
                    str.slice(str.length - tailLen);
            };

            for (let cIdx = 0; cIdx < reqObj.contents.length; cIdx++) {
                const item = reqObj.contents[cIdx];
                if (!item || !Array.isArray(item.parts)) continue;

                for (let pIdx = 0; pIdx < item.parts.length; pIdx++) {
                    const part = item.parts[pIdx];
                    if (!part) continue;

                    if (part.functionResponse) {
                        const resp = part.functionResponse.response;
                        if (typeof resp === 'string') {
                            part.functionResponse.response = truncateStrWithHeadTail(resp, maxRawStrLen);
                        } else if (resp && typeof resp === 'object') {
                            const pruneObj = (obj, depth = 0) => {
                                if (depth > 6 || !obj || typeof obj !== 'object') return;
                                for (const key of Object.keys(obj)) {
                                    const val = obj[key];
                                    if (Array.isArray(val)) {
                                        if (val.length > maxArrayLen) {
                                            const origCount = val.length;
                                            obj[key] = val.slice(0, maxArrayLen);
                                            obj[`_${key}_flowork_shield`] = `[Flowork Context Shield] Preserved top ${maxArrayLen} of ${origCount} items. Full count retained in metrics.`;
                                        }
                                        for (const sub of obj[key]) {
                                            if (sub && typeof sub === 'object') pruneObj(sub, depth + 1);
                                        }
                                    } else if (typeof val === 'string') {
                                        if (val.length > maxStrLen) {
                                            obj[key] = truncateStrWithHeadTail(val, maxStrLen);
                                        }
                                    } else if (val && typeof val === 'object') {
                                        pruneObj(val, depth + 1);
                                    }
                                }
                            };
                            pruneObj(resp);
                        }
                    } else if (part.text && typeof part.text === 'string') {
                        // Older assistant/user turns: if giant dump (>40,000 chars)
                        if (cIdx < reqObj.contents.length - 2 && part.text.length > 40000) {
                            part.text = truncateStrWithHeadTail(part.text, 35000);
                        }
                    }
                }
            }

            // Secondary safeguard: if total JSON payload size is still > 1.5MB (~400k-500k tokens),
            // aggressively compact older function responses (everything except the last 2 turns)
            let rawSize = Buffer.byteLength(JSON.stringify(payload));
            if (rawSize > 1500000 && reqObj.contents.length > 3) {
                console.warn(`[Flowork Context Shield] ⚠️ Payload size (${rawSize} bytes) still high. Compacting older history...`);
                for (let cIdx = 0; cIdx < reqObj.contents.length - 2; cIdx++) {
                    const item = reqObj.contents[cIdx];
                    if (!item || !Array.isArray(item.parts)) continue;
                    for (const part of item.parts) {
                        if (part && part.functionResponse) {
                            const resp = part.functionResponse.response;
                            if (typeof resp === 'string') {
                                part.functionResponse.response = truncateStrWithHeadTail(resp, 5000);
                            } else if (resp && typeof resp === 'object') {
                                for (const k of Object.keys(resp)) {
                                    if (Array.isArray(resp[k]) && resp[k].length > 5) {
                                        resp[k] = resp[k].slice(0, 5);
                                    } else if (typeof resp[k] === 'string' && resp[k].length > 3000) {
                                        resp[k] = truncateStrWithHeadTail(resp[k], 3000);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } catch (err) {
            console.warn('[Flowork Context Shield] Prune error:', err.message);
        }
        return payload;
    }

    /**
     * Normalizes a functionCall object's name and arguments based on active client mode
     */
    static normalizeFunctionCall(fc, activeMode) {
        if (!fc || typeof fc !== 'object') return;

        // 1. Normalize name to standard if aliased
        if (fc.name && REVERSE_MAP[fc.name]) {
            fc.name = REVERSE_MAP[fc.name];
        }

        const args = fc.args;
        if (!args || typeof args !== 'object') return;

        if (activeMode === 'flowai') {
            // FLOWAI Mode: convert to snake_case
            if (fc.name === 'view_file' || fc.name === 'read_file') {
                fc.name = 'read_file';
                const p = args.file_path || args.AbsolutePath || args.absolute_path || args.path || args.TargetFile || args.target_file;
                if (p !== undefined) args.file_path = p;
                delete args.AbsolutePath; delete args.absolute_path; delete args.path; delete args.TargetFile; delete args.target_file;
                if ('StartLine' in args) { args.start_line = args.StartLine; delete args.StartLine; }
                if ('EndLine' in args) { args.end_line = args.EndLine; delete args.EndLine; }
            } else if (fc.name === 'run_command' || fc.name === 'run_shell_command') {
                fc.name = 'run_shell_command';
                const cmd = args.command || args.CommandLine || args.command_line || args.cmd;
                if (cmd !== undefined) args.command = cmd;
                delete args.CommandLine; delete args.command_line; delete args.cmd;
                const cwd = args.dir_path || args.Cwd || args.cwd || args.DirectoryPath || args.directory_path;
                if (cwd !== undefined) args.dir_path = cwd;
                delete args.Cwd; delete args.cwd; delete args.DirectoryPath; delete args.directory_path;
            } else if (fc.name === 'write_to_file' || fc.name === 'write_file') {
                fc.name = 'write_file';
                const p = args.file_path || args.TargetFile || args.target_file || args.path || args.AbsolutePath || args.absolute_path;
                if (p !== undefined) args.file_path = p;
                delete args.TargetFile; delete args.target_file; delete args.path; delete args.AbsolutePath; delete args.absolute_path;
                const c = args.content !== undefined ? args.content : (args.CodeContent !== undefined ? args.CodeContent : args.code_content);
                if (c !== undefined) args.content = c;
                delete args.CodeContent; delete args.code_content;
            } else if (fc.name === 'replace_file_content' || fc.name === 'replace') {
                fc.name = 'replace';
                const p = args.file_path || args.TargetFile || args.target_file || args.path;
                if (p !== undefined) args.file_path = p;
                delete args.TargetFile; delete args.target_file; delete args.path;
                const oldS = args.old_string !== undefined ? args.old_string : (args.TargetContent !== undefined ? args.TargetContent : (args.target_content !== undefined ? args.target_content : args.find));
                if (oldS !== undefined) args.old_string = oldS;
                delete args.TargetContent; delete args.target_content; delete args.find;
                const newS = args.new_string !== undefined ? args.new_string : (args.ReplacementContent !== undefined ? args.ReplacementContent : (args.replacement_content !== undefined ? args.replacement_content : args.replacement));
                if (newS !== undefined) args.new_string = newS;
                delete args.ReplacementContent; delete args.replacement_content; delete args.replacement;
                if ('AllowMultiple' in args) { args.allow_multiple = args.AllowMultiple; delete args.AllowMultiple; }
            } else if (fc.name === 'search_web' || fc.name === 'flowos_web_search') {
                fc.name = 'flowos_web_search';
                const q = args.query || args.SearchQuery || args.search_query;
                if (q !== undefined) args.query = q;
                delete args.SearchQuery; delete args.search_query;
            } else if (fc.name === 'read_url_content' || fc.name === 'web_fetch') {
                fc.name = 'web_fetch';
            }
            return;
        }

        // Standard Universal System Mode (Default)
        // Normalize parameter keys to PascalCase standard
        if (fc.name === 'run_command') {
            const cmd = args.CommandLine || args.command || args.command_line || args.cmd;
            if (cmd !== undefined) args.CommandLine = cmd;
            delete args.command; delete args.command_line; delete args.cmd;
            const cwd = args.Cwd || args.dir_path || args.cwd || args.DirectoryPath || args.directory_path;
            if (cwd !== undefined) args.Cwd = cwd;
            delete args.dir_path; delete args.cwd; delete args.DirectoryPath; delete args.directory_path;
        } else if (fc.name === 'view_file') {
            const p = args.AbsolutePath || args.file_path || args.absolute_path || args.path || args.TargetFile || args.target_file;
            if (p !== undefined) args.AbsolutePath = p;
            delete args.file_path; delete args.absolute_path; delete args.path; delete args.TargetFile; delete args.target_file;
            if ('start_line' in args) { args.StartLine = args.start_line; delete args.start_line; }
            if ('end_line' in args) { args.EndLine = args.end_line; delete args.end_line; }
        } else if (fc.name === 'write_to_file') {
            const p = args.TargetFile || args.file_path || args.target_file || args.path || args.AbsolutePath || args.absolute_path;
            if (p !== undefined) args.TargetFile = p;
            delete args.file_path; delete args.target_file; delete args.path; delete args.AbsolutePath; delete args.absolute_path;
            const c = args.CodeContent !== undefined ? args.CodeContent : (args.content !== undefined ? args.content : args.code_content);
            if (c !== undefined) args.CodeContent = c;
            delete args.content; delete args.code_content;
        } else if (fc.name === 'replace_file_content') {
            const p = args.TargetFile || args.file_path || args.target_file || args.path;
            if (p !== undefined) args.TargetFile = p;
            delete args.file_path; delete args.target_file; delete args.path;
            const oldS = args.TargetContent !== undefined ? args.TargetContent : (args.old_string !== undefined ? args.old_string : (args.target_content !== undefined ? args.target_content : args.find));
            if (oldS !== undefined) args.TargetContent = oldS;
            delete args.old_string; delete args.target_content; delete args.find;
            const newS = args.ReplacementContent !== undefined ? args.ReplacementContent : (args.new_string !== undefined ? args.new_string : (args.replacement_content !== undefined ? args.replacement_content : args.replacement));
            if (newS !== undefined) args.ReplacementContent = newS;
            delete args.new_string; delete args.replacement_content; delete args.replacement;
            if ('allow_multiple' in args) { args.AllowMultiple = args.allow_multiple; delete args.allow_multiple; }
        } else if (fc.name === 'read_url_content') {
            const u = args.Url || args.url;
            if (u !== undefined) args.Url = u;
            delete args.url;
        } else if (fc.name === 'search_web') {
            const q = args.query || args.SearchQuery || args.search_query;
            if (q !== undefined) args.query = q;
        }
    }

    /**
     * Translates Flowork Sovereign tool calls in incoming response chunks back to native names
     * Ensures native language server binary or FlowAI engine executes commands with zero schema rejection
     */
    static translateChunkToNative(chunk) {
        if (!chunk) return chunk;
        try {
            const isBuffer = Buffer.isBuffer(chunk);
            let text = isBuffer ? chunk.toString('utf8') : String(chunk);

            // 1. Strip default_api: or any other namespace prefix in tool names
            if (text.includes('default_api:')) {
                text = text.replace(/(["']name["']\s*:\s*["'])default_api:([^"']+)(["'])/g, '$1$2$3');
            }

            const activeMode = FloworkOSToolVirtualizer.getClientMode();

            // 1b. Structured JSON AST Translation (Handles SSE format and complete JSON chunks)
            let handledStructured = false;

            if (text.includes('data: ')) {
                const lines = text.split('\n');
                let modified = false;
                const newLines = lines.map(line => {
                    if (line.startsWith('data: ')) {
                        const jsonPart = line.slice(6).trim();
                        try {
                            const data = JSON.parse(jsonPart);
                            let touched = false;
                            const candidates = data.candidates || [];
                            for (const c of candidates) {
                                const parts = c.content?.parts || [];
                                for (const p of parts) {
                                    if (p.functionCall) {
                                        FloworkOSToolVirtualizer.normalizeFunctionCall(p.functionCall, activeMode);
                                        touched = true;
                                    }
                                }
                            }
                            if (touched) {
                                modified = true;
                                return 'data: ' + JSON.stringify(data);
                            }
                        } catch (_) {}
                    }
                    return line;
                });
                if (modified) {
                    text = newLines.join('\n');
                    handledStructured = true;
                }
            } else if (text.trim().startsWith('{')) {
                try {
                    const data = JSON.parse(text);
                    let touched = false;
                    const candidates = data.candidates || [];
                    for (const c of candidates) {
                        const parts = c.content?.parts || [];
                        for (const p of parts) {
                            if (p.functionCall) {
                                FloworkOSToolVirtualizer.normalizeFunctionCall(p.functionCall, activeMode);
                                touched = true;
                            }
                        }
                    }
                    if (touched) {
                        text = JSON.stringify(data);
                        handledStructured = true;
                    }
                } catch (_) {}
            }

            if (handledStructured) {
                return text;
            }
            if (activeMode !== 'flowai') {
                // In Flowork Universal Mode (Default), ensure legacy names are normalized to standard tools
                for (const [legacyTool, standardTool] of Object.entries(LEGACY_FLOW_TO_STANDARD_MAP)) {
                    if (text.includes(legacyTool)) {
                        const jsonRegex = new RegExp(`(["']name["']\\s*:\\s*["'])(?:default_api:)?${legacyTool}(["'])`, 'g');
                        text = text.replace(jsonRegex, `$1${standardTool}$2`);
                    }
                }
                // Adapt parameter names to Universal PascalCase standard
                text = text.replace(/(["']name["']\s*:\s*["']run_command["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']command["']|["']cmd["'])(\s*:\s*)/g, '$1"CommandLine"$3');
                text = text.replace(/(["']name["']\s*:\s*["']run_command["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']dir_path["']|["']cwd["'])(\s*:\s*)/g, '$1"Cwd"$3');
                text = text.replace(/(["']name["']\s*:\s*["']view_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']file_path["']|["']path["'])(\s*:\s*)/g, '$1"AbsolutePath"$3');
                text = text.replace(/(["']name["']\s*:\s*["']view_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']start_line["'])(\s*:\s*)/g, '$1"StartLine"$3');
                text = text.replace(/(["']name["']\s*:\s*["']view_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']end_line["'])(\s*:\s*)/g, '$1"EndLine"$3');
                text = text.replace(/(["']name["']\s*:\s*["']write_to_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']file_path["']|["']path["'])(\s*:\s*)/g, '$1"TargetFile"$3');
                text = text.replace(/(["']name["']\s*:\s*["']write_to_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']content["'])(\s*:\s*)/g, '$1"CodeContent"$3');
                text = text.replace(/(["']name["']\s*:\s*["']replace_file_content["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']file_path["']|["']path["'])(\s*:\s*)/g, '$1"TargetFile"$3');
                text = text.replace(/(["']name["']\s*:\s*["']replace_file_content["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']old_string["']|["']target_content["'])(\s*:\s*)/g, '$1"TargetContent"$3');
                text = text.replace(/(["']name["']\s*:\s*["']replace_file_content["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']new_string["']|["']replacement["'])(\s*:\s*)/g, '$1"ReplacementContent"$3');
                text = text.replace(/(["']name["']\s*:\s*["']read_url_content["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']url["'])(\s*:\s*)/g, '$1"Url"$3');
            } else {
                // Translate standard tools to FlowAI native tools
                for (const [sourceTool, nativeTool] of Object.entries(FLOWAI_NATIVE_MAP)) {
                    if (text.includes(sourceTool)) {
                        const jsonRegex = new RegExp(`(["']name["']\\s*:\\s*["'])(?:default_api:)?${sourceTool}(["'])`, 'g');
                        text = text.replace(jsonRegex, `$1${nativeTool}$2`);
                    }
                }
            }

            // 3. Schema Parameter Adaptation for FlowAI Client (PascalCase / Snake_case Bridge)
            if (activeMode === 'flowai') {
                // Adapt read_file args: AbsolutePath/path -> file_path, StartLine -> start_line, EndLine -> end_line
                if (text.includes('read_file')) {
                    text = text.replace(/(["']name["']\s*:\s*["']read_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']AbsolutePath["']|["']path["'])(\s*:\s*)/g, '$1"file_path"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']read_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']StartLine["'])(\s*:\s*)/g, '$1"start_line"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']read_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']EndLine["'])(\s*:\s*)/g, '$1"end_line"$3');
                }

                // Adapt run_shell_command args: CommandLine/cmd -> command, Cwd -> dir_path
                if (text.includes('run_shell_command')) {
                    text = text.replace(/(["']name["']\s*:\s*["']run_shell_command["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']CommandLine["']|["']cmd["'])(\s*:\s*)/g, '$1"command"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']run_shell_command["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']Cwd["']|["']cwd["'])(\s*:\s*)/g, '$1"dir_path"$3');
                }

                // Adapt write_file args: TargetFile/path -> file_path, CodeContent/content -> content
                if (text.includes('write_file')) {
                    text = text.replace(/(["']name["']\s*:\s*["']write_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']TargetFile["']|["']path["'])(\s*:\s*)/g, '$1"file_path"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']write_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']CodeContent["'])(\s*:\s*)/g, '$1"content"$3');
                }

                // Adapt replace args: TargetFile -> file_path, TargetContent -> old_string, ReplacementContent -> new_string
                if (text.includes('replace')) {
                    text = text.replace(/(["']name["']\s*:\s*["']replace["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']TargetFile["']|["']path["'])(\s*:\s*)/g, '$1"file_path"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']replace["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']TargetContent["'])(\s*:\s*)/g, '$1"old_string"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']replace["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']ReplacementContent["'])(\s*:\s*)/g, '$1"new_string"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']replace["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']AllowMultiple["'])(\s*:\s*)/g, '$1"allow_multiple"$3');
                }

                // Adapt list_directory args: DirectoryPath/path -> dir_path
                if (text.includes('list_directory')) {
                    text = text.replace(/(["']name["']\s*:\s*["']list_directory["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']DirectoryPath["']|["']path["'])(\s*:\s*)/g, '$1"dir_path"$3');
                }

                // Adapt flowos_web_search args: SearchQuery -> query
                if (text.includes('flowos_web_search')) {
                    text = text.replace(/(["']name["']\s*:\s*["']flowos_web_search["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']SearchQuery["'])(\s*:\s*)/g, '$1"query"$3');
                }
            }

            // 3b. Schema Parameter Adaptation for Universal Standard Engine (Snake_case to PascalCase Bridge)
            if (activeMode === 'standard' || activeMode === 'flowork') {
                // Adapt view_file args: file_path/path -> AbsolutePath, start_line -> StartLine, end_line -> EndLine
                if (text.includes('view_file')) {
                    text = text.replace(/(["']name["']\s*:\s*["']view_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']file_path["']|["']path["'])(\s*:\s*)/g, '$1"AbsolutePath"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']view_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']start_line["'])(\s*:\s*)/g, '$1"StartLine"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']view_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']end_line["'])(\s*:\s*)/g, '$1"EndLine"$3');
                }

                // Adapt run_command args: command/cmd -> CommandLine, dir_path/cwd -> Cwd
                if (text.includes('run_command')) {
                    text = text.replace(/(["']name["']\s*:\s*["']run_command["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']command["']|["']cmd["'])(\s*:\s*)/g, '$1"CommandLine"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']run_command["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']dir_path["']|["']cwd["'])(\s*:\s*)/g, '$1"Cwd"$3');
                }

                // Adapt write_to_file args: file_path/path -> TargetFile, content -> CodeContent
                if (text.includes('write_to_file')) {
                    text = text.replace(/(["']name["']\s*:\s*["']write_to_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']file_path["']|["']path["'])(\s*:\s*)/g, '$1"TargetFile"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']write_to_file["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']content["'])(\s*:\s*)/g, '$1"CodeContent"$3');
                }

                // Adapt replace_file_content args: file_path/path -> TargetFile, old_string/target_content -> TargetContent, new_string/replacement -> ReplacementContent
                if (text.includes('replace_file_content')) {
                    text = text.replace(/(["']name["']\s*:\s*["']replace_file_content["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']file_path["']|["']path["'])(\s*:\s*)/g, '$1"TargetFile"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']replace_file_content["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']old_string["']|["']target_content["'])(\s*:\s*)/g, '$1"TargetContent"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']replace_file_content["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']new_string["']|["']replacement["'])(\s*:\s*)/g, '$1"ReplacementContent"$3');
                    text = text.replace(/(["']name["']\s*:\s*["']replace_file_content["'][\s\S]*?["']args["']\s*:\s*\{[^}]*?)(["']allow_multiple["'])(\s*:\s*)/g, '$1"AllowMultiple"$3');
                }
            }

            // 4. Adapt subagent arguments: ensure Subagents array exists for Go binary schema validation
            if (text.includes('invoke_subagent') && text.includes('subagent_name') && !text.includes('Subagents')) {
                text = text.replace(
                    /(["']name["']\s*:\s*["']invoke_subagent["'][\s\S]*?["']args["']\s*:\s*\{)([^}]*?)(["']subagent_name["']\s*:\s*["']([^"']+)["'])([^}]*?)(["']prompt["']\s*:\s*["']((?:[^"'\\]|\\.)*)["'])([^}]*?\})/g,
                    '$1"Subagents":[{"TypeName":"$4","Role":"$4","Prompt":"$7"}]$8'
                );
                text = text.replace(
                    /(["']name["']\s*:\s*["']invoke_subagent["'][\s\S]*?["']args["']\s*:\s*\{)([^}]*?)(["']prompt["']\s*:\s*["']((?:[^"'\\]|\\.)*)["'])([^}]*?)(["']subagent_name["']\s*:\s*["']([^"']+)["'])([^}]*?\})/g,
                    '$1"Subagents":[{"TypeName":"$7","Role":"$7","Prompt":"$4"}]$8'
                );
            }

            // 5. Adapt search_tools tool call to native runner
            if (text.includes('search_tools')) {
                const searchToolsScript = path.resolve(__dirname, 'search_tools.js').replace(/\\/g, '/');
                const cwdPath = (process.env.FLOWORK_WORKSPACE || process.cwd()).replace(/\\/g, '/');
                const safeEscape = (s) => `"${String(s || '').replace(/["\\$`]/g, '\\$&')}"`;
                text = text.replace(
                    /(["']name["']\s*:\s*["'])(?:default_api:)?(?:flow_)?search_tools(["'][\s\S]*?["']args["']\s*:\s*\{)([^}]*?)(\})/g,
                    (match, p1, p2, innerArgs, p3) => {
                        let q = '';
                        let cat = '';
                        let det = 'full';
                        const qMatch = innerArgs.match(/["']query["']\s*:\s*["']([^"']+)["']/);
                        if (qMatch) q = qMatch[1];
                        const catMatch = innerArgs.match(/["']category["']\s*:\s*["']([^"']+)["']/);
                        if (catMatch) cat = catMatch[1];
                        const detMatch = innerArgs.match(/["']detail_level["']\s*:\s*["']([^"']+)["']/);
                        if (detMatch) det = detMatch[1];

                        const cmd = `node "${searchToolsScript}" ${safeEscape(q)} ${safeEscape(cat)} ${safeEscape(det)}`;
                        if (activeMode === 'flowai') {
                            return `${p1}run_shell_command${p2}"command":${JSON.stringify(cmd)},"dir_path":${JSON.stringify(cwdPath)},"description":"Searching external tools"${p3}`;
                        } else {
                            return `${p1}run_command${p2}"CommandLine":${JSON.stringify(cmd)},"Cwd":${JSON.stringify(cwdPath)},"WaitMsBeforeAsync":8000,"toolAction":"Searching external tools","toolSummary":"Search external tools"${p3}`;
                        }
                    }
                );
            }

            // 6. Adapt flow_lock tool call to native runner
            if (text.includes('flow_lock')) {
                const flowLockScript = path.resolve(__dirname, 'flow_lock.js').replace(/\\/g, '/');
                const cwdPath = (process.env.FLOWORK_WORKSPACE || process.cwd()).replace(/\\/g, '/');
                const safeEscape = (s) => `"${String(s || '').replace(/["\\$`]/g, '\\$&')}"`;
                text = text.replace(
                    /(["']name["']\s*:\s*["'])(?:default_api:)?(?:flow_)?flow_lock(["'][\s\S]*?["']args["']\s*:\s*\{)([^}]*?)(\})/g,
                    (match, p1, p2, innerArgs, p3) => {
                        let action = 'check';
                        let targetFile = '';
                        let passcode = '';
                        let targetContent = '';
                        const actMatch = innerArgs.match(/["']action["']\s*:\s*["']([^"']+)["']/);
                        if (actMatch) action = actMatch[1];
                        const tfMatch = innerArgs.match(/["']target_file["']\s*:\s*["']([^"']+)["']/);
                        if (tfMatch) targetFile = tfMatch[1];
                        const pcMatch = innerArgs.match(/["']passcode["']\s*:\s*["']([^"']+)["']/);
                        if (pcMatch) passcode = pcMatch[1];
                        const tcMatch = innerArgs.match(/["']target_content["']\s*:\s*["']([^"']+)["']/);
                        if (tcMatch) targetContent = tcMatch[1];

                        const cmd = `node "${flowLockScript}" ${safeEscape(action)} ${safeEscape(targetFile)} "" "" ${safeEscape(passcode)} ${safeEscape(targetContent)}`;
                        if (activeMode === 'flowai') {
                            return `${p1}run_shell_command${p2}"command":${JSON.stringify(cmd)},"dir_path":${JSON.stringify(cwdPath)},"description":"Executing flow_lock"${p3}`;
                        } else {
                            return `${p1}run_command${p2}"CommandLine":${JSON.stringify(cmd)},"Cwd":${JSON.stringify(cwdPath)},"WaitMsBeforeAsync":8000,"toolAction":"Executing flow_lock","toolSummary":"Flow lock operation"${p3}`;
                        }
                    }
                );
            }

            return isBuffer ? Buffer.from(text, 'utf8') : text;
        } catch (_) {
            return chunk; // Circuit-breaker: return intact on error
        }
    }

    static getToolMap() {
        const activeMode = FloworkOSToolVirtualizer.getClientMode();
        return (activeMode === 'flowai') ? { ...FLOWAI_NATIVE_MAP } : {};
    }

    static getReverseMap() {
        return { ...REVERSE_MAP };
    }

    static getClientMode() {
        return global.__FLOWORK_CLIENT_MODE__ || 'flowork';
    }

    static setClientMode(mode) {
        if (mode === 'flowork' || mode === 'flowai') {
            global.__FLOWORK_CLIENT_MODE__ = mode;
        }
    }
}

module.exports = FloworkOSToolVirtualizer;
