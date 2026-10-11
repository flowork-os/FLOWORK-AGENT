---
id: coder-specialist-deep-modules
persona: coder-specialist
target: prompt
priority: 91
trigger:
  cmd: ["/deep-design", "/architecture", "/seam", "/module"]
  keywords: ["deep module", "seam", "ousterhout", "interface", "architecture", "abstraction", "adapter", "leverage"]
  file_patterns: ["*.ts", "*.rs", "*.go", "*.py"]
---

# 🏛️ DESAIN MODUL MENDALAM & ARSITEKTUR SEAM (OUSTERHOUT & FEATHERS)

<DEEP_MODULES_ARCHITECTURE>
Terapkan prinsip rekayasa perangkat lunak modern untuk menjaga kesehatan basis kode jangka panjang:

### 1. DOKTRIN MODUL MENDALAM (*OUSTERHOUT DEEP MODULES*)
- **Module:** Lapisan logis yang menyatukan antarmuka (*interface*) dan implementasi (*implementation*).
- **Interface:** Seluruh beban kognitif yang wajib dipahami pemanggil untuk menggunakan modul dengan benar (bukan sekadar daftar nama fungsi atau tipe TypeScript).
- **Depth (Kedalaman):** Rasio antara kompleksitas fungsionalitas yang disediakan terhadap kesederhanaan antarmuka. Modul terbaik adalah antarmuka kecil yang menyembunyikan implementasi besar (*high depth*).
- **Tolak Modul Dangkal (*Shallow Modules*):** Hindari kelas atau pembungkus (*wrapper*) tipis yang membutuhkan pemahaman implementasi internal pemanggil hanya untuk mendelegasikan 1 baris kode.

### 2. DOKTRIN SEAM & THE DELETION TEST
- **Seam (Michael Feathers):** Titik publik pada sistem di mana perilaku dapat diubah atau diamati dalam pengujian tanpa mengedit kode sumber internal modul.
- **The Deletion Test:** Jika sebuah modul dihapus dari basis kode, kompleksitas internalnya harus hilang bersamanya, bukan malah tercerai-berai dan bocor ke seluruh pemanggil (*callers*).
- **Aturan Adapter Sejati:**
  - *1 Adapter = Hipotesis Seam* (jangan buat abstraksi fleksibilitas khayalan sebelum ada dua implementasi riil).
  - *2 Adapter Riil = Seam Terbukti* (baru sah diekstraksi menjadi antarmuka publik).

### 3. POLA DESIGN IT TWICE
- Ketika merancang modul baru yang kritis, jangan langsung menggunakan draf pertama.
- Rancang minimal 2 pendekatan alternatif dengan filosofi berbeda (misal: Callback vs Event Stream, Sync State vs Immutable Log), evaluasi trade-off kedalaman antarmuka, lalu pilih yang paling sederhana bagi pemanggil.
</DEEP_MODULES_ARCHITECTURE>
