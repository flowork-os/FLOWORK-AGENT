---
id: tool-architect-error-containment
persona: tool-architect
target: prompt
priority: 93
cmd: ["/harden-tool", "/anti-crash"]
trigger:
  keywords: ["harden tool", "error containment", "anti crash", "exit code 0", "try catch", "uncaughtexception", "penanganan error", "perangkap error"]
  exclude_keywords: ["forex", "trading crypto"]
---

# 🧱 BULLETPROOF ERROR CONTAINMENT & DOKTRIN ANTI-CRASH

Ketika AI Agent mengeksekusi tool eksternal, Host Runner menembak skrip via child process. Jika tool melempar *unhandled exception*, *panic*, atau *segfault*, subproses mati dengan exit code tidak beraturan (misal: 1, 137, 255) yang dapat memicu kegagalan berantai (*domino crash*) pada sesi agen.

---

### 🛡️ 1. DOKTRIN EMAS EXIT CODE 0
> **Hukum Besi Flowork OS:** *Sekalipun sebuah tool mengalami kegagalan internal (berkas hilang, koneksi terputus, argumen salah format), skrip WAJIB mengembalikan respon JSON terstruktur dengan `"status": "ERROR"` pada STDOUT dan keluar dengan **EXIT CODE 0**.*

Dengan Exit Code 0 terstruktur, Cognitive Loop agen dapat membaca pesan error secara rasional, mengevaluasi root cause, dan mengambil langkah mitigasi secara cerdas (*course-correction*) alih-alih mengalami *hang* atau *crash*.

---

### 🏗️ 2. POLA TRIPLE-LOCK CONTAINMENT (NODE.JS)

Pastikan setiap skrip Node.js menerapkan 3 lapis perlindungan:

```javascript
// [LAPIS 1: PROCESS-LEVEL TRAP]
process.on('uncaughtException', (err) => {
    emitJsonError("UNCAUGHT_EXCEPTION", err.message || String(err));
});

process.on('unhandledRejection', (reason) => {
    emitJsonError("UNHANDLED_REJECTION", reason?.message || String(reason));
});

function emitJsonError(type, message) {
    try {
        console.log(JSON.stringify({
            status: "ERROR",
            error_type: type,
            error: message,
            timestamp: new Date().toISOString()
        }));
    } catch (_) {
        console.log('{"status":"ERROR","error":"Catastrophic failure in error emitter"}');
    }
    process.exit(0); // [KUNCI KEDAULATAN: EXIT CODE 0]
}

// [LAPIS 2: FUNCTION RUNNER TRAP]
async function runSafe() {
    try {
        // [LAPIS 3: GRANULAR INNER TRAPS UNTUK I/O]
        await executeLogic();
    } catch (innerErr) {
        emitJsonError("RUNTIME_ERROR", innerErr.message);
    }
}
```

---

### 🐍 3. POLA TRIPLE-LOCK CONTAINMENT (PYTHON 3)

```python
import sys
import json
from datetime import datetime, timezone

def emit_json_error(error_type, message):
    try:
        print(json.dumps({
            "status": "ERROR",
            "error_type": error_type,
            "error": str(message),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
    except Exception:
        print('{"status":"ERROR","error":"Catastrophic failure in error emitter"}')
    sys.exit(0) # [WAJIB EXIT CODE 0]

def global_exception_handler(exctype, value, traceback):
    emit_json_error(exctype.__name__, str(value))

sys.excepthook = global_exception_handler
```

---

### ⚡ 4. PENGUJIAN KETAHANAN TEKANAN (FUZZ TESTING)
Sebelum tool dianggap lulus audit hardening:
1. Uji tanpa argumen apapun: `node tools/<tool>/main.mjs` -> Pastikan output JSON error dan Exit Code 0.
2. Uji dengan argumen string sampah: `node tools/<tool>/main.mjs --target "!@#$%^&*()"` -> Pastikan Exit Code 0.
3. Uji dengan payload JSON korup: `node tools/<tool>/main.mjs '{"target": '` -> Pastikan Exit Code 0.
