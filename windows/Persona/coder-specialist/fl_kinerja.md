---
id: fl-coder-kinerja
persona: coder-specialist
target: kinerja
priority: 90
trigger:
  tools_active:
    - run_command
    - replace_file_content
    - write_to_file
  file_patterns:
    - "*.rs"
    - "*.ts"
    - "*.go"
    - "*.py"
    - "Cargo.toml"
---

# 📊 PROTOKOL EVALUASI KINERJA & METRIK KEDAULATAN REKAYASA

<CODER_SPECIALIST_KINERJA>
1. **RASIO MERAH-KE-HIJAU (RED-TO-GREEN RATIO):**
   - 100% bug fixes wajib memiliki bukti eksekusi merah deterministik sebelum implementasi hijau diterapkan.

2. **BUDGET SMART ZONE (~150K TOKEN):**
   - Pembuatan spesifikasi dan tiket DAG diselesaikan dalam 1 sesi jendela awal.
   - Setiap tiket implementasi dieksekusi dalam jendela konteks baru yang segar.

3. **LEVERAGE ARSITEKTUR OUSTERHOUT:**
   - Kedalaman modul dievaluasi: Rasio baris implementasi terhadap baris antarmuka publik harus >= 4:1.

4. **INTEGRITAS COMMIT & CO-AUTHOR:**
   - Setiap perubahan lolos uji lint/typecheck dan memuat `Co-authored-by: Flowork OS <agent@floworkos.com>`.
</CODER_SPECIALIST_KINERJA>
