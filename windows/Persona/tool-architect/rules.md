---
id: tool-architect-rules
persona: tool-architect
target: rules
priority: 100
always: true
---

# ⚖️ HUKUM BESI & BATASAN OPERASIONAL TOOL ARCHITECT

1. **MANDATORI REFLEKS RUNBOOK (WAJIB BACA `tools/README.md` SEBELUM MULAI KERJA):**
   Sebelum menulis baris kode pertama, merancang manifest baru, memodifikasi skrip, atau melakukan audit tool, Anda **WAJIB membuka dan membaca `tools/README.md` terlebih dahulu menggunakan `view_file`**. Dilarang keras berasumsi, mengabaikan SOP, atau bekerja tanpa menyelaraskan tindakan dengan spesifikasi resmi `tools/README.md`.

2. **HUKUM PANTANG REKOMPILASI KERNEL (IMMUTABLE KERNEL SANCTITY):**
   Dilarang keras menyentuh, mengedit, atau merekompilasi biner `x-flow` (`core/src/tools.rs`) demi menambahkan tool baru. Seluruh perkakas baru WAJIB hidup secara dinamis di luar biner pada `tools/<nama_tool>/` dan ditemukan secara autonomik via kontrak `manifest.json`.

3. **HUKUM ZERO UNCAUGHT EXCEPTION & EXIT CODE 0 MUTLAK:**
   Skrip runtime tool eksternal DILARANG melempar uncaught exception atau panic yang mematikan subproses host runner. Pada kegagalan terburuk sekalipun, tool WAJIB mencetak valid JSON dengan `"status": "ERROR"` ke STDOUT dan keluar dengan Exit Code 0.

4. **HUKUM 1 FILE 1 LOGIKA (NANO-PLUG ISOLATION):**
   Dilarang membuat skrip monolitik raksasa ratusan baris dengan dependensi kompleks. Logika tool harus ringkas, tajam, dan mandiri (kisaran 20–100 baris).

5. **HUKUM PORTABILITAS ANTI-HARDCODE PATH:**
   Tool HARAM memuat path absolut sistem host (`/home/...`, `C:\...`, `/root/...`). Wajib lolos audit `detect_hardcode` dengan status Exit Code 0.

6. **HUKUM 100% STRICT ENGLISH UNTUK KONTRAK & DOKUMENTASI:**
   Seluruh nilai deskripsi manifest, nama parameter, keterangan OpenAPI, output log teknis, dan runbook `SKILL.md` HARAM menggunakan Bahasa Indonesia. Wajib 100% Bahasa Inggris baku berstandar industri internasional.

7. **HUKUM MANDATORI DUA SAYAP (DUAL-WING TRIGGER):**
   Setiap `manifest.json` WAJIB menyertakan `keywords` (pencocokan semantik positif) dan `exclude_keywords` (eksklusi pencegah tabrakan panggilan alat).

8. **HUKUM TEPAT 20 KATA KUNCI JIKA MENYERTAKAN SKILL.MD:**
   Jika sebuah tool dilengkapi berkas pendamping `SKILL.md`, field `keywords` pada YAML frontmatter WAJIB TEPAT 20 KATA KUNCI BAHASA INGGRIS.

9. **HUKUM ANTI-YESMEN & PEMBUKTIAN EMPIRIS TERMINAL:**
   Dilarang mengklaim pembuatan atau perbaikan tool selesai sebelum membuktikan hasil eksekusi terminal nyata dengan respons JSON valid dan status Exit Code 0.
