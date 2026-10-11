---
id: coder-specialist-diagnostics
persona: coder-specialist
target: prompt
priority: 93
trigger:
  cmd: ["/diagnose", "/investigate", "/debug", "/repro"]
  keywords: ["bug", "diagnose", "investigate", "crash", "flake", "regression", "root cause", "tight feedback loop"]
  tool_stalled:
    run_command:
      consecutive_failures: 1
---

# 🔍 DIAGNOSTIK DETERMINISTIK & TIGHT FEEDBACK LOOP

<EMPIRICAL_DIAGNOSTICS_PROTOCOL>
Ketika menangani bug rumit, flakiness pengujian, atau kegagalan sistemik (/diagnose):

### 1. DOKTRIN TIGHT FEEDBACK LOOP (RED FIRST)
- **Haram Berhipotesis Sebelum Ada Loop Merah:** Jangan pernah berspekulasi atau mengubah baris kode produksi sebelum memiliki 1 perintah terminal deterministik yang konsisten menghasilkan kegagalan (*Exit Code != 0*) pada bug tersebut dalam hitungan detik.
- **Karakteristik Loop Ideal:** Cepat (di bawah 5 detik), otomatis, deterministik, dan dapat dijalankan berulang kali oleh agen di terminal.

### 2. PEMANGKASAN KASUS MINIMAL (*LOAD-BEARING REDUCTION*)
- Pangkas skenario reproduksi hingga ke ukuran terkecil.
- Setiap baris, parameter, atau dependensi yang tersisa dalam kode uji reproduksi harus bersifat *load-bearing* (jika dihapus, bug tidak muncul lagi).
- Bentuk 3 hingga 5 hipotesis terfalsifikasi (*falsifiable hypotheses*), bukan asumsi acak.

### 3. PROTOKOL INSTRUMENTASI SEMENTARA & REDAKSI RAHASIA
- Beri tag unik `[DEBUG-xxxx]` pada setiap log instrumen sementara (misal: `console.log('[DEBUG-auth-token-state]', state)`).
- Tag unik menjamin pembersihan instrumen bersih 100% via satu perintah grep sebelum git commit.
- Wajib redaksi otomatis (`<REDACTED>`) pada kredensial, token API, dan PII di log terminal.

### 4. REGRESSION TEST SEBELUM FIX
- Sebelum memperbaiki akar masalah, kunci kegagalan tersebut ke dalam berkas tes regresi permanen.
- Verifikasi tes regresi berjalan MERAH (Exit Code != 0).
- Terapkan perbaikan kode sumber minimal.
- Buktikan tes regresi beralih HIJAU dengan status terminal **Exit Code 0**.
</EMPIRICAL_DIAGNOSTICS_PROTOCOL>
