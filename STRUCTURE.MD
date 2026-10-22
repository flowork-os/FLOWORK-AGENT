<!-- [FL_INDEX: keywords="flowork os, directory structure, distribution specification, sovereign blueprint, system organs" | purpose="Comprehensive architectural distribution map and directory layout specification for Flowork OS"] -->
# 🏛️ FLOWORK OS DISTRIBUTION SPECIFICATION & ARCHITECTURAL BLUEPRINT
<!-- Co-authored-by: Flowork OS <agent@floworkos.com> -->

Dokumen ini mendefinisikan peta struktur direktori resmi (*Canonical Directory Layout*), peran masing-masing organ sistem, serta demarkasi kedaulatan antara tubuh Flowork OS dan workspace proyek pengguna.

---

## 🗺️ 1. Hierarki Direktori Resmi (Engine Root)

```text
flowork/                                # Engine Root & Body of Flowork OS
├── README.MD                           # Arsitektur umum, visi, dan manual komprehensif sistem
├── STRUCTURE.MD                        # Spesifikasi distribusi & peta arsitektur direktori (Dokumen ini)
├── VERSION                             # Versi rilis distribusi Flowork OS
│
├── flowork.sh                          # Skrip peluncur native Linux/macOS
├── flowork.bat                         # Skrip peluncur native Windows (CMD / PowerShell)
├── run.sh                              # Runtime bootstrap launcher Linux
├── run.bat                             # Runtime bootstrap launcher Windows
│
├── system/                             # Organ Inti Sistem Flowork OS
│   ├── config.json                     # Konfigurasi batas turn, JIT, dan visibilitas perkakas
│   ├── pipeline_dag.json               # Definisi DAG orkestrasi alur kerja multi-agen
│   ├── security_rules/                 # Aturan guardrail keamanan dinamis & AST validator
│   ├── subagent/                       # Spesialisasi agen otonom & peran swarm
│   │   ├── leader/                     # Komandan mode grup & orchestrator utama
│   │   ├── mr.flow/                    # Arsitek eksekutif & diplomat kedaulatan utama
│   │   ├── backend-engineer/           # Spesialis logika server, API, dan sistem
│   │   ├── frontend-engineer/          # Spesialis antarmuka pengguna & interaksi visual
│   │   ├── quality-control/            # Gatekeeper verifikasi empiris (Exit Code 0)
│   │   └── security-auditor/           # Auditor celah keamanan, sanitasi, dan SAST
│   ├── system_promp/                   # Passive Environmental Triggers (Sensory Ambient)
│   │   ├── triggers.json               # Peta registrasi trigger pasif
│   │   ├── rules/                      # Logika evaluasi kondisi ambient (*.rs)
│   │   ├── promp/                      # Payload prompt panduan perilaku (*.md)
│   │   └── SKILL.md                    # Runbook SOP arsitektur trigger pasif
│   └── triger/                         # Active Watchdog Triggers (Push-based canvas nodes)
│       ├── SKILL.md                    # Runbook SOP arsitektur trigger aktif
│       ├── bitcoin_threshold/          # Contoh trigger aktif monitor harga crypto
│       └── webhook_receiver/           # Contoh trigger aktif penangkap event webhook
│
├── apps/                               # Aplikasi Visual Flowork Canvas (Port 18000-18999)
│   ├── apps.json                       # Katalog aplikasi visual aktif
│   ├── rules.md                        # Aturan baku arsitektur hybrid aplikasi canvas
│   ├── SKILL.MD                        # Runbook authoritative pembangunan aplikasi visual
│   ├── trigger.md                      # Keyword heuristic pengaktifan aplikasi
│   └── <app_id>/                       # Direktori aplikasi canvas individual
│
├── tools/                              # Perkakas Otonom Eksternal (CLI / Headless execution)
│   ├── README.md                       # Panduan sistem registry perkakas dinamis
│   ├── rules.md                        # Invarian baku perkakas eksternal
│   ├── SKILL.MD                        # Runbook SOP authoring alat bantu eksternal
│   ├── trigger.md                      # Pemicu keyword radar perkakas
│   └── <tool_id>/                      # Direktori tool eksternal (manifest.json, script)
│
├── skills/                             # Kumpulan SOP & Runbook Keahlian Spesialis On-Demand
│   ├── README.md                       # Panduan sovereign skills registry & dual-wing radar
│   ├── rules.md                        # Invarian 20-keyword & nano-modular standard
│   ├── SKILL.MD                        # Runbook utama kurasi & authoring SOP skill
│   ├── trigger.md                      # Peta trigger radar skill
│   └── <skill_id>/                     # Direktori paket skill (00_overview, rules, references)
│
├── connector/                          # Universal AI Switchboard Gateway (Port 127.0.0.1:9099)
│   └── readme.md                       # Panduan switchboard: Ollama, 9Router, Cloud Engine
│
├── canvas-ui/                          # Antarmuka Visual Pengguna (Webview & Canvas Desktop)
│   ├── index.html                      # Root layout canvas Flowork
│   ├── styles/                         # CSS styling antarmuka bertema Flowork Sovereign
│   └── js/                             # Logika interaktif frontend canvas
│
├── hooks/                              # Interceptor Siklus Hidup Perkakas & Sesi
│   ├── pre_tool.sh                     # Interceptor sebelum eksekusi perkakas (keamanan/guardrail)
│   ├── post_tool.sh                    # Interceptor setelah eksekusi perkakas (indexing/audit)
│   ├── block-dangerous-git.sh          # Pelindung dari operasi git destruktif
│   └── link-skills.sh                  # Manajemen symlink skill
│
├── mcp/                                # Model Context Protocol integrations
│   └── README.MD                       # Dokumentasi integrasi MCP
│
├── portable-home/                      # Home Directory Portabel (Isolasi data sesi pengguna)
│   └── .flowork/chat_sessions/         # Log histori percakapan (terisolasi di luar workspace)
│
├── .fl_brain/                          # Sovereign Memory Vault (Kubah Ingatan Abadi)
│   └── memories/                       # Kristalisasi solusi terverifikasi (Exit Code 0)
│
└── .FL_BIN/                            # Biner Pendukung & Scratchpad Sementara
    └── scratch/                        # Direktori sandbox isolasi file uji coba
```

---

## 🏛️ 2. Tiga Wilayah Teritorial Sakral (Territorial Isolation)

Flowork OS menegakkan pemisahan mutlak tiga wilayah untuk menjaga kestabilan dan higienitas sistem:

1. **Tubuh Flowork OS (`flowork/`)**:
   - Berisi biner kernel (`x-flow`), engine switches, connector, sistem organ (`system/`, `apps/`, `tools/`, `skills/`), dan frontend canvas.
   - Terisolasi dari workspace pengguna.

2. **Workspace Proyek Pengguna (`{workspace}/`)**:
   - Area tempat agen bekerja memanipulasi kode dan berkas proyek yang diminta oleh pengguna.
   - Tubuh sistem Flowork OS TIDAK BOLEH dikotori oleh file temporer proyek pengguna.

3. **Kubah Sesi & Histori (`portable-home/.flowork/`)**:
   - Menyimpan jejak audit, transcript, cache model, dan riwayat obrolan secara portabel tanpa membebani disk proyek utama.

---

## ⚡ 3. Matriks Organ Kedaulatan Flowork OS

| Organ | Jalur Direktori | Peran Utama | Rujukan Doktrin |
| :--- | :--- | :--- | :--- |
| **Subagent** | `system/subagent/<id>/` | Spesialisasi peran, kepribadian, batasan peran | `system/subagent/` |
| **Passive Trigger** | `system/system_promp/` | Insting ambient nol-overhead dievaluasi saat turn | `system/system_promp/SKILL.md` |
| **Active Trigger** | `system/triger/<id>/` | Daemon watchdog yang membangunkan agen via signal | `system/triger/SKILL.md` |
| **Visual App** | `apps/<app_id>/` | Aplikasi visual interaktif human-in-the-loop (GUI) | `apps/SKILL.MD` |
| **External Tool** | `tools/<tool_id>/` | Perkakas otonom headless berbasis manifest & stdin/out | `tools/SKILL.MD` |
| **Sovereign Skill** | `skills/<skill_id>/` | SOP domain bertarget 20 keyword baku | `skills/SKILL.MD` |
| **AI Connector** | `connector/` | Switchboard gateway ke Ollama, 9Router, Cloud | `connector/readme.md` |

---

## 🛡️ 4. Invarian Penjaga Integritas (Sanctity & Portability)

1. **Zero Hardcoded Paths**: Seluruh rujukan path wajib relatif atau diselesaikan via runtime dynamic API (`process.cwd()`, `std::env::current_dir()`).
2. **Sanctity of `@lock`**: Berkas atau baris dengan penanda `@lock` atau `@frozen` tidak boleh dimodifikasi tanpa otorisasi.
3. **Empirical Proof Obligation**: Setiap perubahan pada struktur direktori atau biner wajib dibuktikan dengan uji verifikasi berstatus **Exit Code 0**.
