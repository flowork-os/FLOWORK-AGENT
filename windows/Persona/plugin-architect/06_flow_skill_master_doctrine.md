---
id: plugin-architect-flow-skill-master
persona: plugin-architect
target: prompt
priority: 90
cmd: ["/flow-skill", "/sop-plugin", "/doktrin-plugin"]
trigger:
  keywords: ["flow_skill", "flow skill", "sop plugin", "standar plugin", "arsitektur plugin", "doktrin plugin", "polyglot plugin", "passport kedaulatan", "process supervisor", "real username"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 📖 MASTER RUNBOOK & DOKTRIN LENGKAP FLOW_SKILL.MD

Panduan operasional resmi berstandar otoritas tertinggi untuk merancang, membangun, dan menguji plugin dalam ekosistem Flowork OS (X-Flow):

---

### 🏛️ 1. 7 DOKTRIN FUNDAMENTAL ARSITEKTUR PLUGIN
1. **Nano-Modular & 1 File 1 Fungsi (Anti-Domino Effect)**:
   - Pecah fungsionalitas menjadi modul-modul kecil dan ringkas (kisaran 20–80 baris per fungsi/file).
   - Menghindari pembuatan berkas monolitik raksasa yang rentan memicu halusinasi AI saat pemeliharaan kode.
   - Kerusakan pada satu unit logika tidak boleh merambat ke unit logika lainnya.
2. **Polyglot & Language Agnostic (Bebas Bahasa Pemrograman)**:
   - Core Host X-Flow (Rust) bersifat sepenuhnya agnostik terhadap bahasa pemrograman plugin.
   - Backend plugin bebas ditulis menggunakan **Node.js / ECMAScript (`.mjs`/`.js`)**, **Python (`.py`)**, **Shell/Batch (`.bat`/`.cmd`)**, biner native terkompilasi (**Rust, Go, C/C++, Zig**), maupun client-side **WebAssembly (`.wasm`)**.
   - Penghubung kedaulatan hanyalah kontrak `plugin.manifest.json` dan IPC berbasis HTTP/SSE.
3. **Zero-Trust Inter-Component Isolation**:
   - Setiap plugin beroperasi di dalam ruang terisolasi miliknya sendiri (`plugins/<plugin-id>/`).
   - Dilarang membuat shared mutable state atau ketergantungan liar antar plugin tanpa kontrak data eksplisit.
   - Frontend GUI berjalan di dalam Webview terproteksi dan berkomunikasi dengan backend melalui REST API / SSE menggunakan port dinamis yang dialokasikan Host.
4. **Dynamic Port Injection (Pantang Hardcode Port)**:
   - Core Host mengalokasikan port jaringan bebas secara dinamis saat peluncuran plugin (`PortManager::allocate_free_port()`).
   - Host menyuntikkan port tersebut ke variabel lingkungan (*Environment Variables*):
     - `$FLOWORK_APP_PORT`
     - `$FLOWORK_PLUGIN_PORT`
     - `$PORT`
   - Backend plugin **WAJIB** membaca variabel lingkungan ini saat mengikat (*bind/listen*) socket jaringan. Backend dilarang keras meng-hardcode port statis.
5. **Zero-Zombie Process Lifecycle Management**:
   - Engine backend diluncurkan di bawah kontrol `ProcessSupervisor` dengan process group mandiri (`process_group(0)` di Unix).
   - Saat tab plugin ditutup atau Core Host shutdown, Host membasmi seluruh pohon proses secara tuntas (`kill -9 -PID` di Unix, `taskkill /F /T /PID` di Windows).
   - Backend wajib merespons sinyal terminasi (`SIGINT`, `SIGTERM`) dan dilarang meninggalkan *orphaned process* atau *zombie worker*.
6. **Hot-Plug & Autonomic Discovery**:
   - Direktori `plugins/` dipantau secara real-time oleh Core Host via `notify` watcher.
   - Penambahan folder plugin baru, pembaruan manifest, atau penghapusan plugin akan dideteksi dan disinkronkan secara otomatis tanpa perlu me-restart Core Host X-Flow.
7. **Real Username & Identitas Paspor Kedaulatan (Haram Placeholder "User/Human")**:
   - Seluruh plugin, label antarmuka GUI, badge pemain, obrolan, dan injeksi prompt **WAJIB menggunakan Real Username** yang diekstrak langsung dari cryptographic passport `.flowork/auth_vault.json` (atau endpoint Host `/api/auth/status`).
   - Dilarang keras menggunakan kata placeholder anonim generik seperti `"User"`, `"Human"`, `"User (White)"`, atau `"Pengguna"`.
   - Gunakan format `@<username>` resmi (contoh: `@awenkaudico` dengan badge `👑 Sovereign Master`).

---

### 📂 2. TOPOGRAFI DIREKTORI STANDAR PLUGIN
```
plugins/<plugin-id>/
├── plugin.manifest.json          # [MANDATORI] Kontrak baku metadata, entry point & pemicu Dual-Wing
├── SKILL.md                   # [MANDATORI] Runbook SOP interaksi agen (TEPAT 20 kata kunci English)
├── gui/                          # [KONDISIONAL] Antarmuka Grafis (Frontend)
│   ├── index.html                # Entry point utama antarmuka (100% Strict English UI)
│   ├── main.css                  # Berkas styling antarmuka (Scoped CSS di bawah #<plugin_id>-root)
│   └── app.js                    # Logika klien & jembatan IPC ke backend
└── engine/                       # [KONDISIONAL] Logika Mesin (Backend Service)
    ├── server.mjs                # Skrip peladen Node.js/ESM
    │   # ATAU main.py            # Skrip peladen Python
    │   # ATAU worker (biner)     # Biner native hasil kompilasi (Rust/Go/C)
    └── wasm/                     # Modul WebAssembly (opsional)
```

---

### ⚙️ 3. KONTRAK BAKU `plugin.manifest.json`
```json
{
  "id": "my-sample-plugin",
  "name": "Sample Audio Processor",
  "version": "1.0.0",
  "author": "Flowork Sovereign Core",
  "description": "High-performance modular audio DSP and waveform filter plugin.",
  "category": "Media & Audio",
  "icon": "🎛️",
  "entry": {
    "gui": "gui/index.html",
    "backend": "engine/server.mjs"
  },
  "ipc": {
    "port_env": "FLOWORK_APP_PORT",
    "default_port": 17896
  },
  "keywords": ["audio", "dsp", "waveform", "filter", "sound"],
  "exclude_keywords": ["video", "crypto", "forex"]
}
```

---

### 🔌 4. BLUEPRINT BACKEND POLYGLOT DENGAN DYNAMIC PORT
Host secara otomatis menentukan runtime berdasarkan ekstensi berkas di `entry.backend`:

#### A. Node.js / ESM (`engine/server.mjs`):
```javascript
import http from 'node:http';

const PORT = parseInt(process.env.FLOWORK_APP_PORT || process.env.PORT || '17894', 10);
const HOST = '127.0.0.1';

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
  if (req.url === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', port: PORT }));
    return;
  }
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Endpoint not found' }));
});

server.listen(PORT, HOST, () => {
  console.log(`[Plugin Backend] Engine listening on http://${HOST}:${PORT}`);
});
```

#### B. Python 3 (`engine/server.py`):
```python
import os, sys, json
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("FLOWORK_APP_PORT", os.environ.get("PORT", 17894)))
HOST = "127.0.0.1"

class PluginHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "port": PORT}).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), PluginHandler)
    print(f"[Plugin Python] Engine listening on http://{HOST}:{PORT}", file=sys.stderr)
    server.serve_forever()
```

---

### 🌐 5. JEMBATAN IPC GUI KE BACKEND (`gui/app.js`)
Host secara otomatis menyuntikkan `<base href="/plugins/<plugin-id>/gui/">` ke dokumen HTML.
Antarmuka GUI menghubungkan diri ke backend engine melalui API Host:
```javascript
async function initializePluginBackend(pluginId) {
  try {
    // 1. Minta Host meluncurkan backend engine dan mengembalikan port aktif
    const response = await fetch(`/api/plugins/${pluginId}/launch`, { method: 'POST' });
    const data = await response.json();

    if (data.status === 'ok') {
      const backendBaseUrl = `http://127.0.0.1:${data.port}`;
      console.log(`[Plugin GUI] Backend connected at: ${backendBaseUrl}`);

      // 2. Hubungi endpoint kesehatan backend engine
      const healthCheck = await fetch(`${backendBaseUrl}/api/health`);
      const healthData = await healthCheck.json();
      console.log('[Plugin GUI] Engine Health:', healthData);

      return backendBaseUrl;
    }
  } catch (err) {
    console.error('[Plugin GUI] IPC Connection Error:', err);
  }
}
```

---

### 🛂 6. INTEGRASI PASPOR KEDAULATAN (REAL USERNAME)
Dilarang menampilkan `"User"` anonim di antarmuka! Ambil identitas resmi pengguna dari Host:
```javascript
async function loadSovereignIdentity() {
  try {
    const res = await fetch('/api/auth/status');
    const auth = await res.json();
    if (auth.status === 'authenticated' && auth.user) {
      const username = auth.user.username; // Contoh: "awenkaudico"
      document.getElementById('user-badge').textContent = `@${username}`;
      return username;
    }
  } catch (_) {}
  return 'Sovereign Master';
}
```

---

### 🛡️ 7. PRE-FLIGHT CHECKLIST (VERIFIKASI EXIT CODE 0)
Sebelum menyatakan pembuatan plugin selesai:
1. Jalankan `detect_hardcode(target_dir: "plugins/<plugin-id>")` -> Wajib 0 temuan absolute path!
2. Periksa `plugins/<plugin-id>/SKILL.md` -> Wajib TEPAT 20 kata kunci Bahasa Inggris!
3. Uji peluncuran via `plugin_control(action: "launch", id: "<plugin-id>")` -> Port dialokasikan, `/api/health` merespons 200 OK!
4. Matikan dengan bersih via `plugin_control(action: "stop", id: "<plugin-id>")` -> Tidak ada proses zombie tersisa!
