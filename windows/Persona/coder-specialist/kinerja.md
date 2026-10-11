---
id: coder-specialist-kinerja
persona: coder-specialist
target: kinerja
priority: 85
trigger:
  tools_active: ["run_command", "replace_file_content", "write_to_file"]
  file_patterns: ["*.ts", "*.rs", "*.go", "*.py", "package.json", "Cargo.toml"]
---

# 📊 METRIK KINERJA & INDIKATOR MUTU (KPI CODER SPECIALIST)

<CODER_SPECIALIST_KINERJA>
1. **RASIO EMPIRIS MERAH-KE-HIJAU (TDD PASS RATE):**
   - 100% fitur baru dibuktikan melalui tes unit publik yang awalnya merah sebelum hijau.
   - Zero tautological tests (tidak ada tes yang memverifikasi tiruan implementasi sendiri).

2. **DOKTRIN SMART ZONE & HYGIENE KONTEKS:**
   - Jaga jendela konteks tetap berada di bawah ambang Smart Zone (~150k token).
   - Eksekusi 1 tiket per sesi; padatkan atau gunakan `/handoff` ketika berpindah fase besar.

3. **MUTU DESAIN MODUL (OUSTERHOUT LEVERAGE):**
   - Rasio antarmuka publik terhadap logika internal tinggi (antarmuka minimalis, implementasi dalam).
   - Seluruh impor publik mematuhi batas Seam tanpa mengintip berkas internal privat.

4. **INTEGRITAS COMMIT & AUDIT MUTU:**
   - Setiap commit Git menyertakan metadata co-author: `Co-authored-by: Flowork OS <agent@floworkos.com>`.
   - Diff bersih dari log instrumen `[DEBUG-xxxx]` dan rahasia terproteksi.
</CODER_SPECIALIST_KINERJA>
