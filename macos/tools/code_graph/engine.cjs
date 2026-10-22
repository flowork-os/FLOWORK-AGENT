/**
 * [FL_INDEX: keywords="code_graph, repomap, ast_parsing, token_budget, pagerank, sovereign_tool" | purpose="Zero-dependency sovereign code graph, repo map, and token-budgeted codebase intelligence engine"]
 * 
 * 🗺️ FLOWORK OS — SOVEREIGN CODE GRAPH & REPO MAP ENGINE
 * ========================================================
 * Implements strict Token Ceiling, bounded memory (< 250 MB),
 * Secret Shield, and Multi-OS portability.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const IGNORED_DIRS = new Set([
  '.git', 'node_modules', 'target', 'vendor', '.FL_BIN', 'dist', 'build',
  '.next', '.nuxt', 'coverage', '.cache', 'out', 'bin', 'obj', '.svn', '.hg'
]);

const IGNORED_FILES = new Set([
  'package-lock.json', 'cargo.lock', 'yarn.lock', 'pnpm-lock.yaml',
  'auth_vault.json', 'credentials.json', '.DS_Store', 'thumbs.db'
]);

const SECRET_PATTERNS = [
  /^\.env/i,
  /\.key$/i,
  /\.pem$/i,
  /\.p12$/i,
  /\.kdbx$/i,
  /\.secret/i,
  /id_rsa/i,
  /id_ed25519/i,
  /token/i,
  /password/i
];

const BINARY_EXTS = new Set([
  '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp', '.pdf',
  '.exe', '.dll', '.so', '.dylib', '.zip', '.tar', '.gz', '.7z',
  '.woff', '.woff2', '.ttf', '.eot', '.wasm', '.bin', '.db', '.sqlite'
]);

const CODE_EXTS = new Set([
  '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx',
  '.rs', '.py', '.go', '.sh', '.bash', '.c', '.cpp', '.h', '.hpp',
  '.html', '.css', '.scss', '.json', '.toml', '.yaml', '.yml', '.md'
]);

function estimateTokens(text) {
  if (!text) return 0;
  // Conservative token estimator: 1 token ~= 3.7 characters for code
  return Math.ceil(text.length / 3.7);
}

function normalizePath(p) {
  return p.replace(/\\/g, '/');
}

function isSecretOrBinary(filename) {
  const base = path.basename(filename);
  if (IGNORED_FILES.has(base)) return true;
  for (const pat of SECRET_PATTERNS) {
    if (pat.test(base)) return true;
  }
  const ext = path.extname(base).toLowerCase();
  if (BINARY_EXTS.has(ext)) return true;
  return false;
}

class CodeGraphEngine {
  constructor(options = {}) {
    this.rootDir = path.resolve(options.target_dir || process.env.FLOWORK_WORKSPACE || process.cwd());
    this.maxTokens = Math.max(100, Number(options.max_tokens) || 1024);
    this.focusFiles = Array.isArray(options.focus_files) ? options.focus_files.map(normalizePath) : [];
    this.maxDepth = Math.max(1, Number(options.depth) || 5);
    this.detailLevel = options.detail_level || 'compact'; // outline, compact, full
    this.files = new Map(); // relPath -> { symbols: [], imports: [], size: number }
    this.graph = new Map(); // relPath -> Set of imported relPaths
    this.reverseGraph = new Map(); // relPath -> Set of dependent relPaths
    this.ranks = new Map(); // relPath -> PageRank score
  }

  scanFiles() {
    const queue = [{ dir: this.rootDir, depth: 0 }];

    while (queue.length > 0) {
      const { dir, depth } = queue.shift();
      if (depth > this.maxDepth) continue;

      let entries;
      try {
        entries = fs.readdirSync(dir, { withFileTypes: true });
      } catch (_) {
        continue;
      }

      for (const entry of entries) {
        const name = entry.name;
        if (name.startsWith('.') && name !== '.flowork' && name !== '.fl_brain') {
          if (IGNORED_DIRS.has(name) || name === '.git') continue;
        }
        if (IGNORED_DIRS.has(name)) continue;

        const fullPath = path.join(dir, name);
        const relPath = normalizePath(path.relative(this.rootDir, fullPath));

        if (entry.isDirectory()) {
          queue.push({ dir: fullPath, depth: depth + 1 });
        } else if (entry.isFile()) {
          if (isSecretOrBinary(name)) continue;
          const ext = path.extname(name).toLowerCase();
          if (!CODE_EXTS.has(ext)) continue;

          try {
            const stat = fs.statSync(fullPath);
            if (stat.size > 512 * 1024) continue; // Skip huge files > 512KB to protect RAM
            this.files.set(relPath, {
              fullPath,
              size: stat.size,
              ext,
              symbols: [],
              imports: []
            });
          } catch (_) {}
        }
      }
    }
  }

  parseSymbols(relPath, fileInfo) {
    let content;
    try {
      content = fs.readFileSync(fileInfo.fullPath, 'utf8');
    } catch (_) {
      return;
    }

    const ext = fileInfo.ext;
    const lines = content.split('\n');
    const symbols = [];
    const imports = [];

    // AST / Heuristic Symbol Extraction per language
    if (['.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx'].includes(ext)) {
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        // Imports
        const impMatch = line.match(/(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\(['"]([^'"]+)['"]\))/);
        if (impMatch) {
          const mod = impMatch[1] || impMatch[2];
          if (mod) imports.push(mod);
        }
        // Functions & Methods
        const fnMatch = line.match(/(?:async\s+)?function\s*([a-zA-Z0-9_$]+)\s*\(/) ||
                        line.match(/(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\(/) ||
                        line.match(/(?:export\s+(?:default\s+)?)?(?:async\s+)?([a-zA-Z0-9_$]+)\s*\([^)]*\)\s*\{/);
        if (fnMatch && fnMatch[1] && !['if', 'for', 'while', 'switch', 'catch'].includes(fnMatch[1])) {
          symbols.push({ type: 'fn', name: fnMatch[1], line: i + 1 });
        }
        // Classes & Interfaces
        const classMatch = line.match(/(?:export\s+)?(?:class|interface|type)\s+([a-zA-Z0-9_$]+)/);
        if (classMatch && classMatch[1]) {
          symbols.push({ type: 'class', name: classMatch[1], line: i + 1 });
        }
      }
    } else if (ext === '.rs') {
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        // Use
        const useMatch = line.match(/^use\s+([^;]+);/);
        if (useMatch) imports.push(useMatch[1]);
        // Fn
        const fnMatch = line.match(/(?:pub(?:\([^)]+\))?\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)/);
        if (fnMatch) symbols.push({ type: 'fn', name: fnMatch[1], line: i + 1 });
        // Struct / Enum / Trait
        const typeMatch = line.match(/(?:pub(?:\([^)]+\))?\s+)?(struct|enum|trait)\s+([a-zA-Z0-9_]+)/);
        if (typeMatch) symbols.push({ type: typeMatch[1], name: typeMatch[2], line: i + 1 });
        // Impl
        const implMatch = line.match(/^impl(?:\s*<[^>]+>)?\s+([a-zA-Z0-9_]+)/);
        if (implMatch) symbols.push({ type: 'impl', name: implMatch[1], line: i + 1 });
      }
    } else if (ext === '.py') {
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        // Imports
        const impMatch = line.match(/^(?:from\s+([a-zA-Z0-9_.]+)\s+import|import\s+([a-zA-Z0-9_.]+))/);
        if (impMatch) imports.push(impMatch[1] || impMatch[2]);
        // Def
        const defMatch = line.match(/(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(/);
        if (defMatch) symbols.push({ type: 'fn', name: defMatch[1], line: i + 1 });
        // Class
        const clsMatch = line.match(/^class\s+([a-zA-Z0-9_]+)/);
        if (clsMatch) symbols.push({ type: 'class', name: clsMatch[1], line: i + 1 });
      }
    } else if (ext === '.go') {
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        // Func
        const fnMatch = line.match(/^func\s+(?:\([^)]+\)\s+)?([a-zA-Z0-9_]+)\s*\(/);
        if (fnMatch) symbols.push({ type: 'fn', name: fnMatch[1], line: i + 1 });
        // Type struct / interface
        const typeMatch = line.match(/^type\s+([a-zA-Z0-9_]+)\s+(struct|interface)/);
        if (typeMatch) symbols.push({ type: typeMatch[2], name: typeMatch[1], line: i + 1 });
      }
    }

    fileInfo.symbols = symbols;
    fileInfo.imports = imports;
  }

  buildGraph() {
    for (const [relPath, fileInfo] of this.files.entries()) {
      this.parseSymbols(relPath, fileInfo);
      this.graph.set(relPath, new Set());
      if (!this.reverseGraph.has(relPath)) {
        this.reverseGraph.set(relPath, new Set());
      }
    }

    // Connect edges
    for (const [relPath, fileInfo] of this.files.entries()) {
      const fileDir = path.dirname(relPath);
      for (const imp of fileInfo.imports) {
        // Resolve relative import
        if (imp.startsWith('.')) {
          const resolvedRel = normalizePath(path.normalize(path.join(fileDir, imp)));
          for (const candidateExt of ['', '.js', '.ts', '.mjs', '.tsx', '/index.js', '/index.ts']) {
            const fullTarget = resolvedRel + candidateExt;
            if (this.files.has(fullTarget)) {
              this.graph.get(relPath).add(fullTarget);
              if (!this.reverseGraph.has(fullTarget)) this.reverseGraph.set(fullTarget, new Set());
              this.reverseGraph.get(fullTarget).add(relPath);
              break;
            }
          }
        } else {
          // Check matching module name
          for (const existingFile of this.files.keys()) {
            if (existingFile.includes(imp)) {
              this.graph.get(relPath).add(existingFile);
              if (!this.reverseGraph.has(existingFile)) this.reverseGraph.set(existingFile, new Set());
              this.reverseGraph.get(existingFile).add(relPath);
            }
          }
        }
      }
    }
  }

  calculatePageRank(iterations = 10, d = 0.85) {
    const totalFiles = this.files.size;
    if (totalFiles === 0) return;

    const baseRank = 1.0 / totalFiles;
    for (const file of this.files.keys()) {
      // Priority boost for focusFiles
      const isFocus = this.focusFiles.some(f => f.includes(file) || file.includes(f));
      this.ranks.set(file, isFocus ? baseRank * 3.0 : baseRank);
    }

    for (let it = 0; it < iterations; it++) {
      const nextRanks = new Map();
      for (const [file, info] of this.files.entries()) {
        const inEdges = this.reverseGraph.get(file) || new Set();
        let rankSum = 0;
        for (const incoming of inEdges) {
          const outDegree = (this.graph.get(incoming) || new Set()).size || 1;
          rankSum += (this.ranks.get(incoming) || baseRank) / outDegree;
        }
        let rank = (1 - d) / totalFiles + d * rankSum;
        // Keep focus file boosted
        if (this.focusFiles.some(f => f.includes(file) || file.includes(f))) {
          rank *= 1.5;
        }
        nextRanks.set(file, rank);
      }
      this.ranks = nextRanks;
    }
  }

  generateMap() {
    this.scanFiles();
    this.buildGraph();
    this.calculatePageRank();

    // Sort files by rank descending
    const sortedFiles = Array.from(this.files.keys()).sort((a, b) => {
      return (this.ranks.get(b) || 0) - (this.ranks.get(a) || 0);
    });

    // Render tree within strict token budget (actual <= maxTokens)
    const header = `🗺️ CODE GRAPH & REPO MAP [Root: ${path.basename(this.rootDir)} | Files: ${this.files.size}]\n`;
    let currentTokens = estimateTokens(header);
    const includedEntries = [];

    for (const relFile of sortedFiles) {
      const fileInfo = this.files.get(relFile);
      const symbolNames = (fileInfo.symbols || []).map(s => `${s.type} ${s.name}`).slice(0, 8);
      const symbolStr = symbolNames.length > 0 ? ` ── (${symbolNames.join(', ')})` : '';
      const line = `📄 ${relFile}${symbolStr}\n`;
      const lineTokens = estimateTokens(line);

      // Strict Token Ceiling check (Hard invariant: current + line <= maxTokens)
      if (currentTokens + lineTokens > this.maxTokens) {
        // If single line exceeds remaining budget, stop to guarantee actual <= budget
        break;
      }

      includedEntries.push(line);
      currentTokens += lineTokens;
    }

    const outputText = header + includedEntries.join('');
    const actualTokens = estimateTokens(outputText);

    return {
      status: 'SUCCESS',
      exit_code: 0,
      root: normalizePath(this.rootDir),
      total_files: this.files.size,
      included_files: includedEntries.length,
      max_tokens: this.maxTokens,
      actual_tokens: actualTokens,
      under_budget: actualTokens <= this.maxTokens,
      repo_map: outputText
    };
  }

  querySymbol(symbolQuery) {
    this.scanFiles();
    this.buildGraph();

    const q = (symbolQuery || '').toLowerCase();
    const matches = [];

    for (const [relFile, fileInfo] of this.files.entries()) {
      for (const sym of fileInfo.symbols) {
        if (sym.name.toLowerCase().includes(q)) {
          matches.push({
            file: relFile,
            type: sym.type,
            name: sym.name,
            line: sym.line,
            dependents_count: (this.reverseGraph.get(relFile) || new Set()).size
          });
        }
      }
    }

    return {
      status: 'SUCCESS',
      exit_code: 0,
      query: symbolQuery,
      matches_found: matches.length,
      results: matches.slice(0, 30)
    };
  }

  analyzeImpact(targetFile) {
    this.scanFiles();
    this.buildGraph();

    const normalizedTarget = normalizePath(targetFile);
    let matchedFile = null;
    for (const file of this.files.keys()) {
      if (file === normalizedTarget || file.endsWith(normalizedTarget)) {
        matchedFile = file;
        break;
      }
    }

    if (!matchedFile) {
      return {
        status: 'FILE_NOT_FOUND',
        exit_code: 1,
        target: targetFile,
        message: `File ${targetFile} not indexed in code graph.`
      };
    }

    const directDependents = Array.from(this.reverseGraph.get(matchedFile) || []);
    const dependencies = Array.from(this.graph.get(matchedFile) || []);

    return {
      status: 'SUCCESS',
      exit_code: 0,
      target_file: matchedFile,
      blast_radius_score: directDependents.length,
      direct_dependents: directDependents,
      dependencies: dependencies,
      symbols_exposed: (this.files.get(matchedFile) || {}).symbols || []
    };
  }
}

// CLI and module export
function main() {
  const args = process.argv.slice(2);
  let options = { action: 'map', max_tokens: 1024 };

  if (args.includes('--params') && args[args.indexOf('--params') + 1]) {
    try {
      options = Object.assign(options, JSON.parse(args[args.indexOf('--params') + 1]));
    } catch (_) {}
  } else {
    if (args[0] && !args[0].startsWith('--')) options.action = args[0];
    if (args[1] && !args[1].startsWith('--')) options.target_dir = args[1];
    if (args[2] && !args[2].startsWith('--')) options.max_tokens = Number(args[2]);
  }

  const engine = new CodeGraphEngine(options);
  let result;

  switch (options.action) {
    case 'query':
      result = engine.querySymbol(options.query);
      break;
    case 'impact':
      result = engine.analyzeImpact(options.query || options.target_file || options.target_dir);
      break;
    case 'overview':
    case 'map':
    default:
      result = engine.generateMap();
      break;
  }

  console.log(JSON.stringify(result, null, 2));
}

if (require.main === module) {
  main();
}

module.exports = CodeGraphEngine;
