# 🛠️ FLOWORK OS — DYNAMIC EXTERNAL TOOLS REGISTRY & DUAL-WING MANIFEST SPECIFICATION (`tools/`)

> **Doktrin Kedaulatan Flowork OS:** *Micro-Kernel murni bertindak sebagai "Papan Kosong Abadi". Seluruh perkakas eksternal beroperasi sebagai nano-plug independen di luar biner pada direktori `tools/`, berkomunikasi murni melalui kontrak Manifest JSON dan stdin/stdout, serta dapat dipasang (mounted) secara on-demand.*  
> **Co-authored-by:** Flowork OS <agent@floworkos.com>

---

## 📌 1. Prinsip Fundamental Arsitektur External Tools

Direktori `tools/` adalah gerbang ekspansi alat bantu (tools) kedaulatan di luar Blackbox Binary:
1. **Dynamic Tool Mounting (Anchor vs. Session Tools):**
   - **Anchor Tools:** Kumpulan perkakas inti permanen yang selalu aktif di setiap sesi (`run_command`, `view_file`, `write_to_file`, `replace_file_content`, `ask_question`, `search_tools`, dll).
   - **Dynamic Modular Tools:** Seluruh tool di direktori `tools/<nama_tool>/` bersifat on-demand. Tool ini dapat dicari via `search_tools(action: 'search')` dan dipasang ke sesi aktif via `search_tools(action: 'mount', tools: ['<nama_tool>'])`.
2. **Nol Polusi Konteks (Anti-Bloat Prompt):**
   - Hanya tool yang secara eksplisit di-*mount* yang akan didaftarkan ke skema function declaration LLM. Tool yang tidak aktif tidak membebani token context window.
3. **Standar Nano-Plug (1 Folder 1 Tool):**
   - Setiap tool terisolasi di dalam foldernya: `tools/<nama_tool>/` dengan entrypoint mandiri (Node.js `.mjs`, Python `.py`, Shell `.sh`, atau biner mandiri).

---

## ⚙️ 2. Spesifikasi Standar Kontrak `manifest.json`

Setiap tool di dalam `tools/<nama_tool>/` **WAJIB** menyertakan berkas `manifest.json` berstandar OpenAPI Object Schema:

```json
{
  "name": "website_intelligence",
  "category": "osint",
  "description": "Target website intelligence extraction: monthly traffic estimation, global and country rankings, traffic channel distribution (SimilarWeb), web archive snapshot history (Wayback Machine CDX), and on-page technical SEO health (Meta tags, OpenGraph, Canonical, Headings, Robots.txt).",
  "command": "node tools/website_intelligence/main.mjs",
  "entry": "main.mjs",
  "author": "Flowork Sovereign Core",
  "version": "1.0.0",
  "keywords": [
    ".com",
    ".net",
    ".org",
    "website",
    "domain",
    "url",
    "traffic",
    "ranking",
    "seo",
    "web intelligence",
    "website_intelligence"
  ],
  "exclude_keywords": [
    "youtube.com",
    "youtube,com",
    "youtube",
    "youtu.be"
  ],
  "tags": [
    "website_intelligence",
    "osint",
    "flowork",
    "modular",
    "zero_corner",
    "nano_plug"
  ],
  "ui": {
    "css": "style.css",
    "zero_corner": true,
    "theme": "cyber_matrix"
  },
  "parameters": {
    "domain": {
      "description": "Target domain or website URL to analyze (e.g. 'apple.com', 'tokopedia.com').",
      "type": "STRING"
    },
    "keywords": {
      "description": "Mandatory on the first tool call of a turn: Comma-separated technical domain keywords in English (e.g. 'sqlite wal concurrency' or 'canvas ui animation'). Used by Sovereign Skill Radar to search relevant skills across local storage and the official Flowork OS repository, presenting up to 3 candidates for optional pinning.",
      "type": "STRING"
    },
    "reason": {
      "description": "MANDATORY ON EVERY TOOL CALL: Clear, concise technical rationale explaining WHY you are calling this tool right now and what specific action it performs (displayed live to the user on every tool HUD and used on the first call to recall up to 3 memories from .fl_brain).",
      "type": "STRING"
    }
  }
}
```

---

## 🎯 3. Arsitektur Dual-Wing Trigger pada External Tools (Keywords & Negative Exclude)

Untuk mencegah **Tabrakan Panggilan Alat (Tool Collision)**, seluruh manifest tools eksternal wajib menerapkan **Arsitektur Dua Sayap (Dual-Wing Architecture)**:

```
                              ┌────────────────────────────────────────┐
                              │       INTENT / QUERY PENCARIAN         │
                              │    (contoh: "youtube,com" / ".com")    │
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
              (contoh: "youtube" pd web intel)                  (contoh: ".com" atau "youtube")
                         │                                                 │
                 ┌───────┴───────┐                                 ┌───────┴───────┐
                 │ YA            │ TIDAK                           │ YA            │ TIDAK
                 ▼               ▼                                 ▼               ▼
            [DISQUALIFIED]   [Lolos ke Positive]               [MATCHED / FOUND]   [IGNORE]
            (Short-Circuit)  (Cek Kecocokan Keyword)           (Masuk ke Hasil     (Skip)
             Tool Digugurkan                                    search_tools)
```

### A. Substring Contains Matching Principle
Pencarian katalog tools (`core/src/tools.rs` -> `execute_flow_search_tools`) menerapkan pencocokan **case-insensitive substring contains**:
* **Toleransi URL & Domain Lengkap:** Input `https://example.com/api` secara otomatis memicu tool dengan keyword `.com` atau `domain`.
* **Toleransi Typo Koma (`youtube,com`):** Pengguna atau agen yang mengetik `youtube,com` (menggunakan koma) tetap memicu tool dengan keyword `youtube`, dan secara bersamaan mengecualikan tool umum seperti `website_intelligence`.
* **Kueri Jalur Dalam:** Segmentasi URL seperti `watch?v=` atau `channel/UC...` dapat dikenali tanpa memerlukan regex kompleks.

### B. Evaluasi Singkat Eksklusi (Short-Circuit Rejection)
Evaluasi negative exclusion dijalankan **SEBELUM** evaluasi teks pencarian:
```rust
// 0. EXCLUSION CHECK (Short-circuit): Substring matching
// If query contains any of tool's exclude_keywords, disqualify immediately!
if !query_lower.is_empty() {
    if let Some(ex_arr) = t.get("exclude_keywords").or_else(|| t.get("exclude")).and_then(|v| v.as_array()) {
        for ex in ex_arr {
            if let Some(ex_str) = ex.as_str() {
                let ex_clean = ex_str.trim().to_lowercase();
                if !ex_clean.is_empty() && query_lower.contains(&ex_clean) {
                    return false; // Tool gugur seketika!
                }
            }
        }
    }
}
```

### C. Matriks Penghindaran Tabrakan Nyata:
* **Kasus Web Recon (`website_intelligence`) vs. YouTube Spy (`youtube_spy_video`):**
  - Tool `website_intelligence` memiliki keyword: `[".com", ".net", ".org", "website", "domain", "traffic", "ranking"]`.
  - Tool `website_intelligence` memiliki exclude: `["youtube.com", "youtube,com", "youtube", "youtu.be"]`.
  - Tool `youtube_spy_video` memiliki keyword: `["youtube", "youtu.be", "youtube.com", "youtube,com", "video deepscan"]`.
  - **Hasil Evaluasi:**
    | Input Kueri | `website_intelligence` | `youtube_spy_video` | Tool yang Muncul |
    | :--- | :--- | :--- | :--- |
    | `"cek trafik tokped.com"` | ✅ Cocok (`.com`) | ❌ Tidak cocok | **`website_intelligence`** |
    | `"buka url https://youtube.com/watch?v=123"` | 🛑 **Gugur (Excluded)** | ✅ Cocok (`youtube`) | **`youtube_spy_video`** |
    | `"analisa channel youtube,com yang ini"` | 🛑 **Gugur (Excluded)** | ✅ Cocok (`youtube`) | **`youtube_spy_video`** |

---

## 🔒 4. Skema Intercept Gate Wajib (`reason` & `keywords`)

Setiap tool eksternal yang di-*resolve* oleh biner Flowork OS secara otomatis disuntikkan skema parameter Intercept Gate:
1. **`reason` (WAJIB DI SETIAP CALL):** Nalar teknis Bahasa Inggris yang menjelaskan MENGAPA tool ini dipanggil dan aksi apa yang sedang dilakukan. Ditampilkan live pada HUD pengguna.
2. **`keywords` (WAJIB DI CALL PERTAMA GILIRAN):** Minimal 5 kata kunci teknis Bahasa Inggris yang digunakan oleh *Sovereign Skill Radar* untuk merekomendasikan skill relevan dari repositori.

---

## 🔍 5. Alur Kerja Penemuan, Mounting & Unmounting (`search_tools`)

```bash
# 1. Cari tool di katalog berdasarkan kata kunci:
search_tools(action: "search", query: "traffic .com")

# 2. Pasang (mount) tool ke sesi aktif (langsung aktif di putaran berikutnya):
search_tools(action: "mount", tools: ["website_intelligence", "web_security_audit"])

# 3. Lepas (unmount) tool jika tugas telah selesai untuk menghemat konteks token:
search_tools(action: "unmount", tools: ["website_intelligence"])

# 4. Cari tool remote di repositori resmi Flowork OS (flowork-os/AGENT-TOOLS):
search_tools(action: "search_remote", query: "docker")
```

---

## 🛡️ 6. Standar Mutu & Preflight Gatekeeper Audit

Sebelum sebuah tool baru disetujui atau dipublikasikan:
1. **Mandatori Bahasa Inggris Penuh (100% Strict English):** Seluruh nilai `description`, keterangan parameter, `keywords`, dan `exclude_keywords` WAJIB dalam Bahasa Inggris formal.
2. **Authoritative Runbook `SKILL.md` (Strict English):** Jika tool menyertakan berkas `SKILL.md`, baik 20 kata kunci frontmatter maupun seluruh isi tubuh dokumen SOP wajib 100% Bahasa Inggris formal (Zero Indonesian Markers).
3. **Anti-Hardcode Portabilitas Multi-OS (`detect_hardcode`):**
   - Tool dilarang keras memuat path host absolut (`/home/...`, `C:\...`, `/root/...`).
   - Wajib lolos audit `detect_hardcode(target_dir: "tools/<nama_tool>")` dengan status **Exit Code 0**.

---

## 🚀 7. Mandatori Kontribusi Tools Teruji ke GitHub Resmi (`flowork-os/AGENT-TOOLS`)

Setiap kali agen selesai merekayasa atau membuat Tool eksternal baru:
1. **Verifikasi Mandiri (Exit Code 0):** Tool wajib diuji secara empiris melalui terminal CLI dan menghasilkan output JSON yang valid (Exit Code 0).
2. **Mandatori Upload ke Repositori Resmi:** Setelah terbukti jalan dan lolos audit `detect_hardcode`, agen **WAJIB MEMPUBLIKASIKAN TOOL KE REPOSITORI GITHUB RESMI** (`flowork-os/AGENT-TOOLS`) menggunakan:
   ```bash
   search_tools(action: "publish", tool_id: "<nama_tool>", notes: "feat: add <nama_tool> modular nano-plug")
   ```
   Atau mendelegasikannya ke subagent terisolasi: `request_publish_gatekeeper(bundle_type: "tool", bundle_id: "<nama_tool>")`.
3. **Pertumbuhan Komunitas Kedaulatan:** Tool yang telah teruji otomatis masuk ke indeks sharded registry resmi sehingga seluruh pengguna dan agen Flowork OS global dapat langsung menemukannya via `search_tools(action: "search_remote")`.
4. **Benteng Attestation Guard (Integritas Hash):** Biner kernel secara otomatis memvalidasi hash SHA-256 binary lokal dan core UI terhadap `release_checksums.json` GitHub. Jika hash termodifikasi atau tidak sah, upload akan seketika diblokir.

---

## 🔄 8. Pemulihan Mandiri Biner (Autonomous Self-Healing)

Berkas panduan spesifikasi ini (`tools/README.md`) diproteksi dan disegel di dalam **Cryptographic Bytecode Enclave** kernel biner `x-flow`:
* **Instalasi Bersih (Fresh Install):** Biner secara otomatis membangkitkan `tools/README.md` saat direktori `tools/` diinisialisasi.
* **Penghapusan Tidak Disengaja (Accidental Deletion):** Jika berkas ini terhapus oleh user atau proses eksternal, biner kernel `x-flow` mendeteksinya dan merekonstitusi berkas ini seketika dari enclave tanpa perlu restart atau download ulang!
