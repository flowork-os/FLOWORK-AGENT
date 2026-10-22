# 📚 FLOWORK OS — SOVEREIGN SKILLS REGISTRY & DUAL-WING SKILL RADAR ARCHITECTURE (`skills/`)

> **Doktrin Kedaulatan Flowork OS:** *Micro-Kernel murni berfungsi sebagai "Papan Kosong Abadi". Seluruh keahlian khusus, SOP domain, dan runbook bersemayam 100% di luar biner pada direktori `skills/` secara modular, hot-reload, dan zero-bloat.*  
> **Co-authored-by:** Flowork OS <agent@floworkos.com>

---

## 📌 1. Prinsip Fundamental Arsitektur Skills

Folder `skills/` adalah repositori keahlian khusus on-demand (*Runbook / SOP*) dalam ekosistem Flowork OS.
Setiap kali agen menerima tugas yang memerlukan keahlian mendalam (misalnya: Reverse Engineering, Web Traffic SEO, Security Audit, Portability Enforcement):
1. **Refleks Wajib Baca (`view_file`):** Agen WAJIB membaca berkas `skills/<nama_skill>/SKILL.md` menggunakan `view_file` sebelum mengambil tindakan teknis.
2. **Pencegahan Halusinasi & Trial-Error:** Agen dilarang menebak alur kerja rumit; seluruh langkah eksekusi wajib berpedoman pada runbook resmi.
3. **Mandatori Pinned Skill (Tier 1-4):** Agen wajib memasang (*pin*) skill relevan ke dalam sesi aktif melalui `skill_control(action: "pin", skill_id: "...")` sebelum mengeksekusi operasi non-anchor.

---

## 🎯 2. Standar Format YAML Frontmatter: Tepat 20 Kata Kunci Bahasa Inggris

Setiap berkas `SKILL.md` diwajibkan memiliki YAML Frontmatter di baris teratas dengan spesifikasi ketat:

```yaml
---
name: "Web Traffic & SEO Specialist"
description: "Standard operating procedure for web traffic analysis, technical SEO auditing, search engine indexation footprinting, backlink discovery, and Core Web Vitals profiling."
keywords: ["seo","traffic","backlinks","ranking","indexing","analytics","sitemap","robots","serp","keywords","performance","lighthouse","crawling","canonical","open_graph","schema_org","json_ld","ttfb","core_web_vitals","pageviews"]
exclude_keywords: ["youtube.com", "youtube,com", "youtube", "youtu.be", "yt spy"]
provenance: "Engineered under 4-Tier Sovereign Acquisition Hierarchy. Verified with Exit Code 0 proof."
---
```

### Hukum Besi Standar & Pembuatan Skill:
1. **WAJIB TEPAT 20 KATA KUNCI BAHASA INGGRIS (`keywords`):**
   - Field `keywords` WAJIB memuat **PERSIS 20 KATA KUNCI** dalam Bahasa Inggris formal.
   - Skill dengan kurang dari 20 atau lebih dari 20 kata kunci dianggap **CACAT (INVALID)** dan akan ditolak oleh *Preflight Gatekeeper*, `skill_control`, serta *Runtime Skill Radar*!
2. **MANDATORI KATA KUNCI & EXCLUDE DALAM BAHASA INGGRIS:**
   - Seluruh kata kunci (`keywords`), kata kunci eksklusi (`exclude_keywords`), nama (`name`), dan deskripsi (`description`) wajib 100% Bahasa Inggris formal. Kata kunci Bahasa Indonesia seperti `analisa`, `koding`, `buat`, `cari` dilarang keras.
3. **MANDATORI KONTEN SKILL (BODY TEXT) WAJIB 100% BAHASA INGGRIS (STRICT ENGLISH):**
   - **Hukum Besi Pembuatan Skill:** Saat agen membuat atau menyusun berkas `SKILL.md`, **BAIK KATA KUNCI MAUPUN SELURUH KONTEN/ISI DOKUMEN ITU SENDIRI WAJIB 100% BAHASA INGGRIS (STRICT ENGLISH)**.
   - Seluruh bab (Overview, Standard Execution Flow, Edge Cases & Recovery, Empirical QC Exit Code 0), petunjuk operasional, penjelasan SOP, dan contoh perintah di dalam `SKILL.md` HARAM menggunakan Bahasa Indonesia (Zero Indonesian Markers).
   - Standar ekosistem Flowork OS menuntut portabilitas global tanpa bias lokal agar seluruh modul keahlian dapat dieksekusi secara universal oleh berbagai model dan runtime di seluruh dunia.

---

## ⚡ 3. Arsitektur Dual-Wing Skill Radar (Keywords & Negative Exclude)

Untuk mencegah **Tabrakan Skill (Skill Collision)** dan **Kepadatan Konteks (Context Bloat)**, *Sovereign Skill Radar* (`core/src/trigger.rs`) mengevaluasi kebutuhan skill melalui **Arsitektur Pemicu Dua Sayap (Dual-Wing Architecture)**:

```
                              ┌────────────────────────────────────────┐
                              │       INTENT / QUERY KATA KUNCI        │
                              │    (contoh: "youtube,com" / "seo")     │
                              └───────────────────┬────────────────────┘
                                                  │
                               [Case-Insensitive Substring Scan]
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
               [Negative Exclusion Wing]                         [Positive Keyword Wing]
                `query_lower.contains(&ex)`                       `query_lower.contains(&kw)`
                         │                                                 │
              Apakah query mengandung exclude?                  Apakah query mengandung keyword?
              (contoh: "youtube" pd skill SEO)                  (contoh: "traffic" atau "ranking")
                         │                                                 │
                 ┌───────┴───────┐                                 ┌───────┴───────┐
                 │ YA            │ TIDAK                           │ YA            │ TIDAK
                 ▼               ▼                                 ▼               ▼
            [DISQUALIFIED]   [Lolos ke Positive]               [RECOMMENDED]   [PASS / IGNORE]
             Score = -1000   (Hitung Skor Positif)             (Top-3 Radar    (Skor 0 / Skip)
            (Short-Circuit)                                     Banner HUD)
```

### A. Substring Contains Matching Principle
Pencocokan pemicu beroperasi secara **case-insensitive substring contains** (`query.to_lowercase().contains(&kw)`):
* **Mengapa Substring?**
  - **URL & TLD:** Input domain seperti `example.com` atau `tokped.com` langsung cocok dengan keyword `.com` atau `domain`.
  - **Toleransi Typo Koma:** Pengguna atau agen yang mengetik `youtube,com` (koma sebagai pengganti titik) tetap terdeteksi secara akurat oleh substring `youtube`.
  - **Sub-jalur:** `watch?v=`, `shorts/`, atau `@handle` cocok secara instan tanpa regex rapuh.

### B. Evaluasi Pengecualian Singkat (Short-Circuit Negative Rejection)
Pengecekan eksklusi dieksekusi **PERTAMA KALI** sebelum menghitung skor positif:
```rust
// 0. EXCLUSION CHECK (Short-circuit): Substring matching
let exclude_vals = skill.get("exclude_keywords")
    .or_else(|| skill.get("exclude"))
    .or_else(|| skill.get("excludes"));
if let Some(arr) = exclude_vals.and_then(|v| v.as_array()) {
    for ex in arr {
        if let Some(ex_str) = ex.as_str() {
            let ex_clean = ex_str.trim().to_lowercase();
            if !ex_clean.is_empty() && query_lower.contains(&ex_clean) {
                return -1000; // DISKUALIFIKASI MUTLAK!
            }
        }
    }
}
```
Jika kata kunci eksklusi cocok, skor langsung jatuh ke `-1000`, menggugurkan skill tersebut dari daftar rekomendasi.

### C. Matriks Penghindaran Tabrakan Nyata:
* **Kasus SEO Web Traffic vs. YouTube Intelligence:**
  - `web_traffic_seo_auditor`: Memiliki keyword `seo`, `traffic`, `ranking`, `domain`. Namun menambahkan `exclude_keywords: ["youtube.com", "youtube,com", "youtube", "youtu.be"]`.
  - Saat pengguna meminta analisa trafik `tokped.com`: Skill SEO dipicu dan direkomendasikan.
  - Saat pengguna meminta analisa `youtube.com/watch?v=123` atau `youtube,com`: Skill SEO **SEKETIKA DIDISKUALIFIKASI**, menyerahkan tugas ke tool/skill YouTube khusus (`youtube_spy_*` / `beat_synced_video_director`).

---

## 📂 4. Struktur Folder Baku Modular Skill

Setiap skill bersemayam di dalam foldernya masing-masing:

```
skills/
└── <nama-skill>/
    ├── SKILL.md       # (Wajib) Frontmatter 20 keywords + SOP lengkap
    ├── scripts/       # (Opsional) Skrip helper / automation tooling
    ├── templates/     # (Opsional) Berkas template kode atau skema
    └── resources/     # (Opsional) Data referensi, CVE offline, kamus
```

---

## 🏛️ 5. Hirarki 4-Tier Akuisisi Kedaulatan & Siklus Hidup Pinned Skill

1. **Tier 1 (Local Workspace / Installed Skills):** Prioritas tertinggi. Radar memindai folder `skills/` lokal terlebih dahulu.
2. **Tier 2 (Official Flowork OS Registry):** Jika skill lokal kurang dari 3 kandidat, radar memindai katalog resmi `flowork-os/FLOWORK-SKILLS`.
3. **Tier 3 (Model Context Protocol / Community):** Adaptasi skill MCP eksternal.
4. **Tier 4 (Zero-Precedent Sovereign Crafting):** Jika tidak ada skill yang cocok, agen merancang skill baru dari nol dengan tepat 20 kata kunci Bahasa Inggris via `skill_control(action: 'create')`.

### Hukum Siklus Hidup Pinned Skill:
* Agen wajib melakukan eksplorasi manual menggunakan `view_file` sebelum memutuskan untuk me-pin skill.
* Skill aktif disematkan via `skill_control(action: "pin", skill_id: "<id>")`.
* Begitu terpasang, SOP skill tersebut disuntikkan secara dinamis ke `<PINNED_ACTIVE_SKILL>` pada giliran berikutnya.
* Pasca-tuntas, agen wajib melepas sematan via `skill_control(action: "unpin")`.

---

## 🚀 6. Mandatori Kontribusi Publikasi ke GitHub Resmi Pasca-Verifikasi (Exit Code 0)

Setiap kali agen selesai merekayasa atau menciptakan Skill baru:
1. **Verifikasi Mandiri (Exit Code 0):** Agen wajib menguji seluruh skrip, SOP, dan contoh instruksi hingga terbukti berhasil secara empiris dengan status Exit Code 0.
2. **Mandatori Upload ke Repositori Resmi:** Setelah terbukti jalan, agen **WAJIB MEMPUBLIKASIKAN & MENG-UPLOAD SKILL KE REPOSITORI GITHUB RESMI** (`flowork-os/FLOWORK-SKILLS`) menggunakan:
   ```bash
   skill_control(action: "publish", skill_id: "<nama_skill>", notes: "feat: add <nama_skill> sovereign runbook")
   ```
3. **Pertumbuhan Komunitas Kedaulatan:** Flowork OS adalah platform yang terus berevolusi. Menahan modul yang telah teruji di mesin lokal bertentangan dengan doktrin pertumbuhan kedaulatan. Setiap keahlian baru wajib dikontribusikan agar seluruh ekosistem global dapat memanfaatkannya.
4. **Benteng Attestation Guard (Integritas Hash):** Biner kernel secara otomatis memvalidasi hash SHA-256 binary lokal dan core UI terhadap `release_checksums.json` GitHub. Jika hash termodifikasi atau tidak sah, upload akan seketika diblokir.

---

## 🔄 7. Pemulihan Mandiri Biner (Autonomous Self-Healing)

Berkas dokumentasi dan tata kelola ini (`skills/README.md`) diproteksi dan disegel di dalam **Cryptographic Bytecode Enclave** kernel biner `x-flow`:
* **Instalasi Bersih (Fresh Install):** Biner secara otomatis membangkitkan `skills/README.md` jika folder `skills/` belum memilikinya.
* **Penghapusan Tidak Disengaja (Accidental Deletion):** Jika berkas ini terhapus oleh user atau proses eksternal, biner kernel `x-flow` mendeteksinya saat turn evaluasi dan merekonstitusi berkas ini seketika dari enclave tanpa perlu restart atau download ulang!
