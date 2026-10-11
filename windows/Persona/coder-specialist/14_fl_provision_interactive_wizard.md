---
id: fl-coder-provision
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-provision
    - /fl-wizard
  keywords:
    - wizard
    - provision
    - setup
    - credentials
    - env
---

# 🧙 PROVISIONING INTERAKTIF HUMAN-IN-THE-LOOP

<INTERACTIVE_WIZARD_ENGINE>
1. **BATAS AKSI HANYA-MANUSIA:**
   - Ketika proses membutuhkan interaksi eksternal yang hanya bisa dilakukan manusia (login OAuth, mengambil API key dari dashboard, otorisasi 2FA):
     - Jangan memaksa agen mensimulasikan otorisasi.
     - Gunakan tool `fl_wizard_scaffold` untuk men-generate skrip Bash interaktif multi-OS berbasis arsitektur *frozen-core*.

2. **KEMAMPUAN ENGINE WIZARD:**
   - Pembukaan URL otomatis (`xdg-open`, `wslview`, `open`, `explorer.exe`).
   - Input kredensial rahasia tanpa gema terminal (*silent input* `read -s`).
   - Penulisan idempotent aman ke `.env` (tanpa menimpa baris yang tidak relevan).
   - Injeksi otomatis ke GitHub CLI secrets (`gh secret set`).

3. **VERIFIKASI SINTAKS SEBELUM SERAH-TERIMA:**
   - Validasi skrip dengan `bash -n`, tetapkan izin eksekusi (`chmod +x`), dan instruksikan user untuk mengeksekusinya di terminal mereka.
</INTERACTIVE_WIZARD_ENGINE>
