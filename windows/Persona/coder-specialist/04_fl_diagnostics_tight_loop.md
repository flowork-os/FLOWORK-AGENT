---
id: fl-coder-diagnostics
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-diagnose
    - /fl-red-loop
  tool_stalled:
    run_command:
      consecutive_failures: 1
---

# 🔍 DIAGNOSTIK DETERMINISTIK & LOOP MERAH EMPIRIS

<EMPIRICAL_DIAGNOSTICS_DOCTRINE>
1. **DOKTRIN LOOP MERAH DETERMINISTIK:**
   - Dilarang keras menatap kode atau mengajukan spekulasi perbaikan tanpa memiliki satu perintah otomatis yang membuktikan kegagalan secara deterministik (Exit Code ≠ 0).
   - Validasi kegagalan sebelum menyentuh kode via `fl_diagnostic_tracer` aksi `verify_repro`.

2. **REDUKSI KASUS UJI LOAD-BEARING:**
   - Perkecil kode reproduksi hingga setiap baris yang tersisa bersifat *load-bearing*. Jika menghapus satu baris tidak menghilangkan bug, hapus baris tersebut.

3. **INSTRUMENTASI BERLABEL `[DEBUG-xxxx]` & PEMBERSIHAN ATOMIK:**
   - Suntikkan probe diagnostik berlabel tag acak unik (`// [DEBUG-xxxx]`) via tool `fl_diagnostic_tracer` aksi `inject_probe`.
   - Pasca-solusi terbukti hijau: Jalankan aksi `clean_probes` untuk memastikan 100% sisa log debug terangkat tanpa jejak.

4. **UJI REGRESI PERMANEN:**
   - Konversikan kasus reproduksi merah menjadi unit/integration test permanen sebelum menganggap pekerjaan selesai.
</EMPIRICAL_DIAGNOSTICS_DOCTRINE>
