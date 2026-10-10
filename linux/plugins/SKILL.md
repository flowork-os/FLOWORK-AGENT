---
name: sovereign_canvas_plugin_architecture
description: Authoritative SOP and engineering specification for creating interactive Flowork Canvas plugins, implementing Dual-Wing triggers, dynamic port binding, human-in-the-loop co-creation, and dedicated plugin SKILL.md runbooks.
author: "@awenkaudico"
version: "1.0.0"
keywords:
  - plugins
  - canvas_ui
  - plugin_manifest
  - human_in_the_loop
  - co_creation
  - dynamic_port
  - microservice
  - rest_api
  - server_sent_events
  - websocket
  - interactive_webview
  - dual_wing_trigger
  - exclude_keywords
  - runbook_sop
  - zero_zombie
  - strict_english_ui
  - process_lifecycle
  - multi_os_portability
  - exit_code_zero
  - flowork_sovereignty
exclude_keywords:
  - internal_tool
  - cli_only
  - background_worker
---

# 🧩 SOVEREIGN CANVAS PLUGIN ARCHITECTURE (FLOWORK OS)

> **AUTHORITY**: AWENK AUDICO & TEGUHFX (LEVEL 99 SUPER ADMIN).  
> **CORE DOCTRINE**: HUMAN-IN-THE-LOOP CO-CREATION, DEDICATED CANVAS WORKBENCH, DUAL-WING MANIFEST CONTRACT, ZERO-ZOMBIE PROCESS MANAGEMENT, AND EMPIRICAL EXIT CODE 0 VERIFICATION.  
> **CO-AUTHORED-BY**: Flowork OS <agent@floworkos.com>

---

## 1. Executive Philosophy & Fundamental Distinction: Tools vs Plugins

In the Flowork OS Sovereign Architecture, **Tools** and **Plugins** serve distinctly different purposes:

1. **Perkakas Internal (Tools)**:
   - Instruments of autonomous execution for the AI Agent (e.g. `run_command`, `view_file`, `write_to_file`, `replace_file_content`, `search_tools`).
   - Run purely under agent discretion to inspect, analyze, edit files, and execute commands behind the scenes.
   - Output directly to agent context or render inline visual summaries.

2. **Modul Aplikasi Canvas (Plugins)**:
   - Interactive, visual workbench applications hosted on the Flowork Canvas UI stage.
   - **Tujuan Utama: Kolaborasi Manusia & Agen (Human-in-the-Loop & Interactive Co-Creation)**.
   - Tempat User dan Agent bekerja bersama secara real-time (contoh: Chess Arena duel, YouTube Downloader & Audio Studio, Video Editor, Diagram/Form Co-creator).
   - Agent memiliki kesadaran penuh terhadap plugin yang sedang dibuka oleh User, dapat membaca statusnya, mengirim perintah/langkah, dan memicu pembaruan antarmuka secara instan.

---

## 2. Directory Layout & Isolated Plugin Architecture

Setiap plugin terisolasi sepenuhnya di dalam direktori `plugins/<plugin_id>/`:

```
plugins/<plugin_id>/
├── plugin.manifest.json       # [MANDATORI] Kontrak plugin, pemicu Dual-Wing (keywords & exclude), entrypoint, GUI
├── SKILL.md                   # [MANDATORI] Runbook SOP interaksi plugin (API endpoints, payload schema, live state)
├── server.js                  # [MANDATORI] Backend microservice (Node.js, Python, atau Go/Rust binary)
└── gui/                       # [OPSIONAL] Dedicated Canvas UI webview
    ├── index.html             # Entry markup (100% Strict English UI)
    ├── style.css              # Scoped stylesheet (Inherit Dark Mode, isolasi CSS)
    └── app.js                 # Frontend state manager dan SSE/WebSocket client
```

### 🎨 Aturan Tampilan Antarmuka Canvas UI
1. **100% Strict English UI**: Seluruh tombol, label, modal, tooltip, dan pesan log wajib menggunakan Bahasa Inggris formal.
2. **Pewarisan Tema Flowork Dark Mode**: Gunakan variabel CSS standar (`--bg-primary`, `--bg-secondary`, `--text-primary`, `--accent-cyan`, dll) agar selaras dengan Canvas Host.
3. **Isolasi Penuh**: Semua selektor CSS wajib diisolasi di bawah namespace `#<plugin_id>-root` untuk mencegah tabrakan style dengan platform host.

---

## 3. Spesifikasi Kontrak `plugin.manifest.json` (Dual-Wing Trigger)

Setiap plugin **WAJIB** memiliki berkas `plugin.manifest.json` yang mendefinisikan identitas, kemampuan, dan pemicu dua sayap:

```json
{
  "$schema": "https://floworkos.com/schemas/plugin.manifest.json",
  "id": "chess",
  "name": "Sovereign Chess Arena",
  "version": "1.0.0",
  "author": "@awenkaudico",
  "description": "Interactive dual-sovereignty chess arena for live Human vs Agent matches on Flowork Canvas.",
  "category": "Games & Simulation",
  "keywords": [
    "chess",
    "catur",
    "chessboard",
    "grandmaster",
    "fen",
    "pgn",
    "board game"
  ],
  "exclude_keywords": [
    "chinese chess",
    "xiangqi",
    "checkers"
  ],
  "entrypoint": {
    "engine": "node",
    "script": "server.js"
  },
  "gui": {
    "enabled": true,
    "entry": "gui/index.html",
    "width": 960,
    "height": 640
  },
  "skill": "SKILL.md",
  "ipc": {
    "port_env": "FLOWORK_APP_PORT",
    "default_port": 17820
  },
  "permissions": {
    "network": true,
    "filesystem_read": ["."]
  }
}
```

### ⚡ Pemicu Dua Sayap (Dual-Wing Triggering):
- **Positive Keywords (`keywords`)**: Kata kunci teknis dalam Bahasa Inggris yang memicu rekomendasi plugin saat relevan dengan intensi user.
- **Negative Exclusions (`exclude_keywords`)**: Kata kunci eksklusi untuk mencegah tabrakan atau kesalahan pemicuan saat intensi user berbeda domain (contoh: mengecualikan catur cina / checkers pada plugin catur standar).

---

## 4. Dynamic Port Allocation & Manajemen Proses Zero-Zombie

1. **Injeksi Port Dinamis (`$FLOWORK_APP_PORT`)**:
   - Backend plugin dilarang keras meng-hardcode port tunggal yang rentan konflik `EADDRINUSE`.
   - Supervisor runtime X-Flow menyuntikkan port dinamis bebas via environment variable:
     ```javascript
     const PORT = process.env.FLOWORK_APP_PORT || process.env.PORT || 17820;
     server.listen(PORT, '127.0.0.1', () => {
       console.log(`[Plugin:chess] Listening on 127.0.0.1:${PORT}`);
     });
     ```
2. **Zero-Zombie Lifecycle**:
   - Supervisor mencatat PID proses backend saat diluncurkan.
   - Saat tab plugin ditutup atau sesi berganti, sinyal `SIGTERM` (atau terminate proses pada Windows) dikirim untuk memastikan proses bersih dan memori RAM terbebas sepenuhnya.

---

## 5. Mandatori Baca `plugins/<plugin_id>/SKILL.md` Sebelum Interaksi

> 🚨 **HUKUM BESI OPERASIONAL**:  
> **DILARANG KERAS MENERKA ENDPOINT, PARAMETER, ATAU FORMAT PAYLOAD API PLUGIN!**

Setiap kali agen perlu berinteraksi dengan plugin tertentu (mengirim langkah catur, mengekstrak video, memperbarui visual):
1. **Wajib Baca `view_file`**: Buka dan pelajari `plugins/<plugin_id>/SKILL.md`.
2. **Periksa Endpoint Resmi**: Baca endpoint REST API (`GET /api/state`, `POST /api/action`), parameter header, dan tipe data JSON yang disyaratkan.
3. **Eksekusi Presisi**: Eksekusi via `run_command` (curl / node) atau HTTP client sesuai spesifikasi dokumen tanpa coba-coba (trial-and-error).

---

## 6. Kesadaran Telemetri Sesi & `<CALLER_CONTEXT>`

Kernel runtime menginjeksi informasi real-time ke dalam `<CALLER_CONTEXT>` sistem prompt:
- `- Active Chat ID: {session_id}` : Mengidentifikasi sesi chat aktif tempat interaksi berlangsung.
- `- Open Plugins: {open_plugins}` : Mengidentifikasi plugin mana saja yang sedang terbuka di antarmuka Canvas pengguna saat ini beserta port aktifnya (misal: `chess (port 17820)`).

Dengan telemetri ini, agen secara otomatis sadar kapan harus bertindak sebagai lawan main catur, asisten audio studio, atau editor video bersama pengguna!

---

## 7. Pre-Publish Quality Control (QC Checklist)

Sebelum mempublikasikan atau menyelesaikan pengembangan plugin baru:
1. **Portability Audit**: Verifikasi tidak ada hardcoded path absolut; gunakan path relatif multi-OS (Linux, macOS, Windows).
2. **Dynamic Port Proof**: Verifikasi backend menghormati `process.env.FLOWORK_APP_PORT`.
3. **Strict English UI**: 100% teks antarmuka GUI, label, dan log teknis menggunakan Bahasa Inggris.
4. **Mandatori `SKILL.md`**: Plugin menyertakan `SKILL.md` lengkap dengan dokumentasi endpoint dan contoh curl (100% Strict English).
5. **Exit Code 0 Verification**: Uji coba backend dan pastikan lolos validasi tanpa error.

---

## 🚀 8. Mandatori Kontribusi Plugin Teruji ke GitHub Resmi (`flowork-os/FLOWAGENT-*-PLUGIN`)

Setiap kali agen selesai merekayasa atau membuat Plugin Canvas baru:
1. **Verifikasi Mandiri (Exit Code 0)**: Microservice plugin wajib diuji, port dinamis berjalan bersih, dan Webview UI lolos QC tanpa error.
2. **Mandatori Upload ke Repositori Resmi**: Setelah terbukti jalan, agen **WAJIB MEMPUBLIKASIKAN PLUGIN KE REPOSITORI GITHUB RESMI** (`flowork-os/FLOWAGENT-LINUX-PLUGIN` atau `flowork-os/FLOWAGENT-WINDOWS-PLUGIN`) menggunakan:
   ```bash
   plugin_publish(plugin_id: "<nama_plugin>", target_os: "linux", notes: "feat: add <nama_plugin> canvas app")
   ```
   Atau mendelegasikannya ke subagent terisolasi: `request_publish_gatekeeper(bundle_type: "plugin", bundle_id: "<nama_plugin>")`.
3. **Pertumbuhan Komunitas Kedaulatan**: Seluruh pengguna Flowork OS di berbagai belahan dunia dapat langsung mengunduh dan menikmati modul kolaborasi yang telah kamu ciptakan.
4. **Benteng Attestation Guard (Integritas Hash)**: Kernel otomatis memverifikasi SHA-256 binary lokal dan core UI terhadap `release_checksums.json` GitHub. Jika hash termodifikasi atau tidak sah, upload otomatis diblokir.
