#!/usr/bin/env node
/**
 * 🔒 FLOWORK SOVEREIGN LOCK (flow_lock.js)
 * =======================================
 * Enforces Rule #10: Kesucian Gembok @lock
 * Prevents unauthorized mutation, removal, or rollback of locked code lines.
 *
 * Usage:
 *   node flow_lock.js <action> [target_file] [start_line] [end_line] [passcode] [target_content]
 *
 * Actions:
 *   - check / verify: Scans target file for locked lines (@lock or // @lock)
 *   - lock / lock_file: Adds @lock tag to file
 *   - lock_block: Locks specific block by line range or target content
 *   - unlock: Unlocks lines if requested
 *   - list: Lists all files with @lock directives in the workspace
 *   - status: Reports overall lock integrity across workspace
 */

'use strict';

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const rawAction = (args[0] || 'check').toLowerCase();
const action = rawAction === 'lock_file' ? 'lock' : rawAction;
const targetFile = args[1] || '';
const startLine = parseInt(args[2], 10) || 0;
const endLine = parseInt(args[3], 10) || 0;
const passcode = args[4] || '';
const targetContent = args[5] || '';

function respond(status, data) {
    console.log(JSON.stringify({
        status,
        action: rawAction,
        target_file: targetFile,
        timestamp: new Date().toISOString(),
        ...data
    }, null, 2));
    process.exit(0);
}

function errorOut(message) {
    console.error(JSON.stringify({
        status: 'error',
        action: rawAction,
        target_file: targetFile,
        error: message
    }, null, 2));
    process.exit(0);
}

if (!targetFile && action !== 'status' && action !== 'list') {
    errorOut('Target file path required for action: ' + rawAction);
}

const resolvedPath = targetFile ? path.resolve(process.cwd(), targetFile) : '';

switch (action) {
    case 'check':
    case 'verify': {
        if (!fs.existsSync(resolvedPath)) {
            errorOut(`File not found: ${targetFile}`);
        }
        const content = fs.readFileSync(resolvedPath, 'utf8');
        const lines = content.split('\n');
        const lockedLines = [];

        lines.forEach((line, idx) => {
            if (line.includes('@lock')) {
                lockedLines.push({
                    line_number: idx + 1,
                    text: line.trim()
                });
            }
        });

        respond('ok', {
            is_locked: lockedLines.length > 0,
            locked_count: lockedLines.length,
            locked_lines: lockedLines,
            message: lockedLines.length > 0 
                ? `File contains ${lockedLines.length} protected @lock directive(s). Do not modify locked lines.`
                : 'No @lock directives found in target file.'
        });
        break;
    }

    case 'lock_block':
    case 'lock': {
        if (!fs.existsSync(resolvedPath)) {
            errorOut(`File not found: ${targetFile}`);
        }
        let content = fs.readFileSync(resolvedPath, 'utf8');
        let lines = content.split('\n');

        if (action === 'lock_block' && targetContent) {
            // Normalize line endings for robust matching
            const normContent = content.replace(/\r\n/g, '\n');
            const normTarget = targetContent.replace(/\r\n/g, '\n');
            if (normContent.includes(normTarget)) {
                const isCRLF = content.includes('\r\n');
                const sep = isCRLF ? '\r\n' : '\n';
                const lockedBlock = `// @lock START${sep}${normTarget}${sep}// @lock END`;
                let updated = normContent.replace(normTarget, lockedBlock);
                if (isCRLF) updated = updated.replace(/\n/g, '\r\n');
                fs.writeFileSync(resolvedPath, updated, 'utf8');
                respond('ok', {
                    message: `Successfully locked target block in ${targetFile}`,
                    modified: true
                });
                break;
            } else {
                errorOut(`Target content not found in ${targetFile}. Ensure exact line and whitespace match.`);
            }
        }

        if (startLine > 0 && endLine >= startLine) {
            for (let i = startLine - 1; i < Math.min(endLine, lines.length); i++) {
                if (!lines[i].includes('@lock')) {
                    lines[i] = lines[i] + ' // @lock';
                }
            }
        } else {
            // Prepend header lock if whole file
            if (!content.includes('@lock')) {
                lines.unshift('// @lock Flowork Sovereign Protected Block');
            }
        }

        fs.writeFileSync(resolvedPath, lines.join('\n'), 'utf8');
        respond('ok', {
            message: `Successfully locked target in ${targetFile}`,
            modified: true
        });
        break;
    }

    case 'unlock': {
        if (!fs.existsSync(resolvedPath)) {
            errorOut(`File not found: ${targetFile}`);
        }
        let content = fs.readFileSync(resolvedPath, 'utf8');
        let lines = content.split('\n');

        let unlockedCount = 0;
        lines = lines.map(line => {
            if (line.includes('@lock')) {
                unlockedCount++;
                return line.replace(/\/\/\s*@lock[^\n]*/g, '').replace(/@lock/g, '');
            }
            return line;
        });

        fs.writeFileSync(resolvedPath, lines.join('\n'), 'utf8');
        respond('ok', {
            message: `Successfully unlocked ${unlockedCount} directive(s) in ${targetFile}`,
            unlocked_count: unlockedCount
        });
        break;
    }

    case 'list': {
        const rootDir = process.cwd();
        const lockedFiles = [];
        const ignored = new Set(['node_modules', '.git', 'target', '.flowork_spam', 'dist', 'build']);

        function walk(dir) {
            let entries = [];
            try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return; }
            for (const ent of entries) {
                if (ignored.has(ent.name)) continue;
                const fullPath = path.join(dir, ent.name);
                if (ent.isDirectory()) {
                    walk(fullPath);
                } else if (ent.isFile()) {
                    try {
                        const fileContent = fs.readFileSync(fullPath, 'utf8');
                        if (fileContent.includes('@lock')) {
                            const rel = path.relative(rootDir, fullPath);
                            const count = (fileContent.match(/@lock/g) || []).length;
                            lockedFiles.push({ file: rel, count });
                        }
                    } catch (_) {}
                }
            }
        }

        walk(rootDir);
        respond('ok', {
            locked_files_count: lockedFiles.length,
            locked_files: lockedFiles,
            message: `Found ${lockedFiles.length} file(s) with @lock directives.`
        });
        break;
    }

    case 'status':
    default: {
        respond('ok', {
            engine: 'Flowork Sovereign Lock System',
            doctrine: 'RULE #10: Kesucian Gembok @lock',
            status: 'active'
        });
        break;
    }
}
