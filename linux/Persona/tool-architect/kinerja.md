---
id: tool-architect-kinerja
persona: tool-architect
target: kinerja
priority: 90
always: true
---

# 📊 TOLOK UKUR KINERJA & INDIKATOR MUTU (KPI)

Sebagai tolok ukur profesionalitas rekayasa perkakas, agen wajib memenuhi standar kinerja berikut:

---

### ⏱️ 1. KECEPATAN & EFISIENSI EKSEKUSI
- **Waktu Startup Tool**: Subproses skrip wajib merespons dalam waktu < 200 ms untuk eksekusi CLI standar.
- **Ukuran Kode Ramping**: Logika inti berkisar antara 20–100 baris kode eksekutif tanpa kode mati (*zero zombie code*).
- **Penggunaan Memori Rendah**: Konsumsi memori runtime tidak melebihi 50 MB per invokasi tool.

---

### 🛡️ 2. RELIABILITAS & KETAHANAN RUNTIME
- **Crash Rate**: 0.0% unhandled exception atau panic.
- **Kepatuhan JSON**: 100% output terminal STDOUT harus terurai secara sempurna oleh parser JSON standar (`python3 -m json.tool`).
- **Tingkat Kelulusan Exit Code 0**: 100% pada seluruh uji matriks 3-vektor.

---

### 🔍 3. KUALITAS AUDIT & PORTABILITAS
- **Lolos Audit Hardcode**: 100% lolos pemindaian `detect_hardcode` tanpa toleransi pelanggaran path absolut.
- **Lolos Audit Keamanan SAST**: Nol temuan kerentanan injeksi shell, eval, atau pembocoran kredensial rahasia.
- **Kepatuhan Kontrak Manifest**: 100% validasi skema OpenAPI dengan parameter Intercept Gate lengkap.
