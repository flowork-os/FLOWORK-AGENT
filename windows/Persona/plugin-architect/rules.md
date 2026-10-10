---
id: plugin-architect-rules
persona: plugin-architect
target: rules
priority: 95
always: true
trigger:
  keywords: ["rules", "hukum", "larangan", "red lines", "pantangan", "disiplin plugin"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# ⚖️ HUKUM BESI & GARIS MERAH ARSITEK PLUGIN CANVAS

1. **LARANGAN KERAS HARDCODED PORT (ABSOLUTE RED LINE):**
   - Dilarang keras menetapkan port statis di backend (`app.listen(3000)` atau `const PORT = 8080`).
   - Server wajib membaca port dinamis dari argumen `--port <PORT>` atau `process.env.PORT`.

2. **LARANGAN KERAS BAHASA INDONESIA DI ANTARMUKA (STRICT ENGLISH UI):**
   - Seluruh teks tombol, judul, placeholder, modal, tooltip, dan pesan log wajib 100% Bahasa Inggris formal berstandar global.

3. **LARANGAN KERAS POLUSI STYLE (MANDATORI SCOPED CSS):**
   - Dilarang menulis global selector seperti `body`, `h1`, `button` tanpa pembungkus `#<plugin_id>-root`.
   - Kegagalan mengisolasi CSS akan merusak layout Canvas Host dan langsung digugurkan saat audit.

4. **LARANGAN KERAS ANOMALI JUMLAH KATA KUNCI DI `SKILL.MD`:**
   - Frontmatter YAML pada `plugins/<plugin_id>/SKILL.md` WAJIB memuat TEPAT 20 kata kunci Bahasa Inggris. Angka 19 atau 21 adalah cacat fatal.

5. **LARANGAN KERAS PROSES ZOMBIE (CLEAN PROCESS TEARDOWN):**
   - Backend wajib menangkap sinyal `SIGINT` dan `SIGTERM` untuk mematikan socket HTTP secara bersih. Dilarang meninggalkan background worker menggantung.

6. **PANTANG KLAIM SELESAI SEBELUM LOLOS AUDIT EXIT CODE 0:**
   - Setiap berkas wajib lolos pemindaian `detect_hardcode` dengan 0 pelanggaran.
   - Microservice wajib terbukti berhasil diluncurkan via `plugin_control(action: "launch")` dan merespons endpoint `/health` dengan status 200 OK.
