---
id: tool-architect-runtime-craft
persona: tool-architect
target: prompt
priority: 91
cmd: ["/forge-tool", "/scaffold-tool"]
trigger:
  keywords: ["buat tool", "bikin tool", "forge tool", "scaffold tool", "runtime tool", "node tool", "python tool", "polyglot tool", "nano plug"]
  exclude_keywords: ["forex", "trading crypto"]
---

# ⚙️ ARSITEKTUR RUNTIME NANO-PLUG POLYGLOT

Tool eksternal di Flowork OS bersifat **Polyglot & Agnostic**. Host runner mengeksekusi tool via perintah biner sistem (`command` di `manifest.json`), berkomunikasi murni melalui Command Line Arguments, STDIN (opsional), dan STDOUT (wajib valid JSON).

---

### 📦 1. BLUEPRINT RUNTIME NODE.JS ESM (`main.mjs`)

Gunakan blueprint resmi ini saat merekayasa tool berbasis JavaScript / Node.js ESM:

```javascript
#!/usr/bin/env node
/**
 * 🛠️ FLOWORK OS SOVEREIGN NANO-TOOL
 * Tool: <nama_tool>
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
import fs from 'fs';
import path from 'path';

// 🛡️ DOKTRIN BULLETPROOF ANTI-CRASH: Tangkap seluruh uncaught exception di root
process.on('uncaughtException', (err) => {
    console.log(JSON.stringify({
        status: "ERROR",
        error: err.message || String(err),
        stack: err.stack,
        timestamp: new Date().toISOString()
    }));
    process.exit(0); // WAJIB Exit Code 0 agar host runner tidak meledak!
});

process.on('unhandledRejection', (reason) => {
    console.log(JSON.stringify({
        status: "ERROR",
        error: reason?.message || String(reason),
        timestamp: new Date().toISOString()
    }));
    process.exit(0);
});

// 📥 PARSER ARGUMEN MULTI-MODE (CLI Flags & JSON Payload)
function parseArgs() {
    const rawArgs = process.argv.slice(2);
    const params = {};

    for (let i = 0; i < rawArgs.length; i++) {
        const arg = rawArgs[i];
        if (arg.startsWith('--')) {
            const key = arg.slice(2);
            const nextVal = rawArgs[i + 1];
            if (nextVal && !nextVal.startsWith('--')) {
                params[key] = nextVal;
                i++;
            } else {
                params[key] = true;
            }
        } else if (arg.startsWith('{') && arg.endsWith('}')) {
            try {
                Object.assign(params, JSON.parse(arg));
            } catch (_) {}
        }
    }
    return params;
}

// 🚀 LOGIKA EKSEKUTIF INTI (1 File 1 Logika, 20-80 baris)
async function main() {
    const args = parseArgs();
    const target = args.target || args.domain || args.query || '';

    if (!target) {
        console.log(JSON.stringify({
            status: "ERROR",
            error: "Missing required argument: 'target' or 'domain'",
            help: "Provide --target <value> or JSON payload in CLI",
            timestamp: new Date().toISOString()
        }));
        process.exit(0);
    }

    try {
        // [Tempat logika spesifik tool dijalankan]
        const result = {
            target: target,
            processed: true,
            records: []
        };

        // Output akhir WAJIB JSON murni ke STDOUT
        console.log(JSON.stringify({
            status: "SUCCESS",
            data: result,
            timestamp: new Date().toISOString()
        }, null, 2));
    } catch (err) {
        console.log(JSON.stringify({
            status: "ERROR",
            error: err.message,
            timestamp: new Date().toISOString()
        }));
    }
    process.exit(0);
}

main();
```

---

### 🐍 2. BLUEPRINT RUNTIME PYTHON 3 (`main.py`)

Gunakan blueprint resmi ini saat merekayasa tool berbasis Python 3:

```python
#!/usr/bin/env python3
"""
🛠️ FLOWORK OS SOVEREIGN NANO-TOOL
Tool: <nama_tool>
Co-authored-by: Flowork OS <agent@floworkos.com>
"""
import sys
import json
import argparse
from datetime import datetime, timezone

def main():
    parser = argparse.ArgumentParser(description="Flowork Sovereign Nano-Tool")
    parser.add_argument("--target", "-t", type=str, default="", help="Target entity")
    parser.add_argument("--payload", "-p", type=str, default="{}", help="Optional JSON payload")
    parser.add_argument("--reason", type=str, default="", help="Technical rationale")
    parser.add_argument("--keywords", type=str, default="", help="Skill radar keywords")

    try:
        args, unknown = parser.parse_known_args()
        target = args.target

        # Fallback to positional JSON or unknown args
        if not target and unknown:
            for item in unknown:
                if item.startswith("{") and item.endswith("}"):
                    try:
                        parsed = json.loads(item)
                        target = parsed.get("target", "")
                    except Exception:
                        pass

        if not target:
            print(json.dumps({
                "status": "ERROR",
                "error": "Missing required parameter: --target",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
            sys.exit(0) # WAJIB Exit Code 0!

        # [Tempat logika spesifik tool dijalankan]
        output = {
            "status": "SUCCESS",
            "target": target,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        sys.exit(0)

if __name__ == "__main__":
    main()
```
