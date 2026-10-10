---
id: plugin-architect-microservice-backend
persona: plugin-architect
target: prompt
priority: 85
cmd: ["/wire-backend", "/backend"]
file_patterns: ["plugins/**/server.js", "plugins/**/server.mjs", "plugins/**/server.py", "plugins/**/main.py"]
trigger:
  keywords: ["wire-backend", "microservice", "server.js", "dynamic port", "rest api", "sse", "websocket", "zero zombie", "health check", "backend plugin"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 🔌 MICROSERVICE BACKEND & ZERO-ZOMBIE LIFECYCLE

Ketika membangun atau merevisi backend microservice plugin (`server.js`), patuhi arsitektur nir-zombie dan resolusi port dinamis berikut:

---

### 1. DYNAMIC PORT RESOLUTION (HARAM HARDCODE PORT)
Flowork Canvas Host meluncurkan microservice plugin dengan mengoper argumen `--port <PORT>` atau menetapkan variabel lingkungan `PORT`.
Backend wajib mengekstrak port secara fleksibel:

```javascript
import http from 'http';
import fs from 'fs';
import path from 'path';

function getPort() {
  const args = process.argv.slice(2);
  const pIdx = args.indexOf('--port');
  if (pIdx !== -1 && args[pIdx + 1]) {
    return parseInt(args[pIdx + 1], 10);
  }
  if (process.env.PORT) {
    return parseInt(process.env.PORT, 10);
  }
  return 0; // 0 = alokasi port otomatis oleh kernel OS jika tidak ditentukan!
}
```

---

### 2. ENDPOINT MANDATORI KEDAULATAN
Setiap backend plugin wajib menyediakan endpoint standar berikut:

1. **`GET /health`**:
   Digunakan oleh Flowork Host untuk memastikan backend siap menerima request sebelum merender tab di Canvas UI:
   ```json
   {
     "status": "ok",
     "plugin": "chess",
     "uptime_seconds": 12.4,
     "version": "1.0.0"
   }
   ```
2. **`GET /api/state`**:
   Mengembalikan data status aktif saat ini (board, job status, playlist, dokumen, dll.).
3. **`POST /api/action`**:
   Menerima payload mutasi dari GUI atau dari AI Agent yang bertindak atas nama pengguna.
4. **`GET /api/events` (SSE Stream)**:
   Kanal Server-Sent Events untuk menyiarkan pembaruan state ke antarmuka `gui/app.js` secara instan.

---

### 3. PROTOKOL ZERO-ZOMBIE CLEANUP (SIGINT / SIGTERM)
Untuk mencegah proses backend tertinggal di background saat tab plugin ditutup atau sistem direstart:

```javascript
function gracefulShutdown(signal) {
  console.log(`[Plugin Backend] Received ${signal}, shutting down gracefully...`);
  server.close(() => {
    console.log('[Plugin Backend] HTTP server closed cleanly. Exiting with code 0.');
    process.exit(0);
  });

  // Force exit fallback setelah 3 detik jika ada socket yang menggantung
  setTimeout(() => {
    console.warn('[Plugin Backend] Force exit timeout reached.');
    process.exit(0);
  }, 3000).unref();
}

process.on('SIGINT', () => gracefulShutdown('SIGINT'));
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
```
