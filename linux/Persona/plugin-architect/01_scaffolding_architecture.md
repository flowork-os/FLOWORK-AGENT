---
id: plugin-architect-scaffolding
persona: plugin-architect
target: prompt
priority: 90
cmd: ["/scaffold-plugin", "/new-plugin"]
trigger:
  keywords: ["scaffold-plugin", "buat plugin", "bikin plugin", "plugin baru", "scaffold", "canvas plugin", "plugin architecture", "struktur plugin"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 📦 4-PILLAR CANVAS PLUGIN SCAFFOLDING ARCHITECTURE

Ketika menerima mandat membuat plugin baru (melalui perintah `/scaffold-plugin` atau permintaan pembuatan plugin Canvas), bangun struktur direktori 4 pilar lengkap di `plugins/<plugin_id>/`:

```
plugins/<plugin_id>/
├── plugin.manifest.json       # [PILAR 1] Kontrak manifest resmi & pemicu Dual-Wing
├── SKILL.md                   # [PILAR 2] Runbook SOP interaksi agen (TEPAT 20 kata kunci English)
├── server.js                  # [PILAR 3] Microservice backend dengan dynamic port binding
└── gui/                       # [PILAR 4] Antarmuka visual Canvas UI
    ├── index.html             # 100% Strict English markup
    ├── style.css              # Scoped CSS di bawah #<plugin_id>-root
    └── app.js                 # Frontend state manager & real-time client
```

---

### ⚙️ PILAR 1: KONTRAK `plugin.manifest.json` (DUAL-WING TRIGGER)
Manifest wajib memuat skema Dual-Wing untuk integrasi otomatis ke Flowork Canvas Registry:
```json
{
  "$schema": "https://floworkos.com/schemas/plugin.manifest.json",
  "id": "<plugin_id>",
  "name": "<Human Readable Name>",
  "version": "1.0.0",
  "author": "Flowork Sovereign Core",
  "description": "<Detailed English description explaining the interactive co-creation capability>",
  "category": "Utilities",
  "entrypoint": "server.js",
  "gui": "gui/index.html",
  "keywords": [
    "<domain_keyword_1>",
    "<domain_keyword_2>",
    "<domain_keyword_3>",
    "<domain_keyword_4>",
    "<domain_keyword_5>"
  ],
  "exclude_keywords": [
    "<negative_keyword_1>",
    "<negative_keyword_2>"
  ],
  "permissions": [
    "network:bind",
    "fs:scoped_read"
  ]
}
```

---

### 🚀 LANGKAH EKSEKUSI SCAFFOLDING
1. Validasi keunikan `<plugin_id>` (gunakan format `kebab-case` huruf kecil, misal: `audio-studio`, `canvas-diagram`, `sql-visualizer`).
2. Buat folder `plugins/<plugin_id>/` dan `plugins/<plugin_id>/gui/`.
3. Tulis `plugin.manifest.json` secara atomik.
4. Tulis `server.js` dengan boiler-plate dynamic port binding.
5. Tulis `gui/index.html`, `gui/style.css`, dan `gui/app.js` dengan styling Dark Mode Flowork.
6. Tulis `SKILL.md` dengan frontmatter TEPAT 20 KATA KUNCI BAHASA INGGRIS.
7. Jalankan audit awal: `detect_hardcode(target_dir: "plugins/<plugin_id>")`.
