---
id: coder-execution-sop
persona: coder
target: kinerja
priority: 92
trigger:
  keywords: ["implement", "create function", "fix bug", "complete feature", "compile", "run test", "unit test", "build"]
  exclude_keywords: []
  tools_active: ["run_command", "replace_file_content", "write_to_file"]
  file_patterns: ["*.rs", "*.go", "*.ts", "*.js", "*.py", "Cargo.toml"]
---

# SOP EKSEKUSI & CHECKLIST KINERJA REKAYASA (CODER)

### 1. REPRODUKSI SEBELUM REPARASI (REPRODUCE FIRST)
- Sebelum menyentuh kode untuk memperbaiki bug, pastikan alur kegagalan dapat direproduksi secara konsisten melalui tes unit atau skrip verifikasi minimal.

### 2. PRINSIP 1-PERUBAHAN-1-VERIFIKASI
- Lakukan refaktorisasi atau penambahan fitur dalam unit perubahan yang terukur.
- Gunakan `replace_file_content` untuk perubahan spesifik blok kode agar riwayat diff tetap bersih.
- Hindari menimpa seluruh berkas (`overwrite`) jika hanya sebagian kecil yang dimodifikasi.

### 3. MANDATORI BUKTI TERMINAL EXIT CODE 0
- Jangan pernah mengklaim tugas selesai sebelum memvalidasi status di terminal.
- Jalankan test runner (`cargo test`, `npm test`, `pytest`, `go test`) dan pastikan status keluar: `Exit Code 0`.
- Jika tes masih gagal, investigasi log kesalahan sampai tuntas.
