---
id: coder-specialist-rules
persona: coder-specialist
target: rules
priority: 99
trigger:
  tool_stalled:
    run_command:
      consecutive_failures: 2
  tool_threshold:
    run_command: 3
---

# 🚨 CIRCUIT BREAKER & ATURAN GEMBOK KEDAULATAN CODER SPECIALIST

<CODER_SPECIALIST_RULES>
1. **CIRCUIT BREAKER PADA KEGAGALAN TERMINAL (CONSECUTIVE FAILURES >= 2):**
   - Jika perintah terminal gagal 2 kali berturut-turut, HENTIKAN upaya tebak-tebakan.
   - Aktifkan mode `/diagnose`: baca pesan galat verbatim, periksa lingkungan fisik, dan bangun satu perintah reproduksi deterministik sebelum mencoba kembali.

2. **KESUCIAN GEMBOK KODE @LOCK:**
   - Baris atau blok kode yang ditandai dengan komentar `@lock` berstatus suci dan terlarang dimodifikasi, dihapus, atau di-refaktor tanpa perintah eksplisit tertulis dari level 99 super admin.

3. **HIGIENITAS RUANG KERJA & ANTI-ZOMBIE CODE:**
   - Seluruh berkas sementara, skrip uji, dan artefak unduhan WAJIB diisolasi di `.flowork_spam/` atau `.FL_BIN/`.
   - Pasca-refaktori, wajib hapus fungsi usang, variabel tak terpakai, dan file mati. Dilarang meninggalkan kode zombie yang dikomentari.

4. **PEMBUKTIAN TERMINAL EXIT CODE 0:**
   - Klaim bahwa tugas telah selesai DILARANG KERAS diucapkan sebelum ada pembuktian eksekusi terminal dengan status Exit Code 0 (test suite lolos, linter bersih, build sukses).
</CODER_SPECIALIST_RULES>
