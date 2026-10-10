---
id: coder-desain-modul-mendalam
persona: coder
target: prompt
priority: 87
trigger:
  tools_active: ["replace_file_content"]
  file_patterns: ["*.rs", "*.ts", "*.go", "*.py"]
  keywords: ["deep module", "deep modules", "information hiding", "module architecture", "shallow module"]
  exclude_keywords: ["forex", "trading crypto", "eurusd", "gbpusd"]
---

<!-- [DEEP_MODULES_ARCHITECTURE_DOCTRINE:START] -->
<DEEP_MODULES_ARCHITECTURE_DOCTRINE>
🏛️ DOKTRIN REKAYASA MODUL MENDALAM & BATAS PUBLIK (DEEP MODULES & SEAMS):
Seluruh perancangan, refaktorisasi, dan pengujian arsitektur dalam ekosistem Flowork OS berpegang teguh pada prinsip Modul Mendalam (*Deep Modules*): menghadirkan kapabilitas kaya di balik antarmuka kecil yang ringkas, terisolasi pada batas publik (*seam*) yang kokoh, dan dapat diuji penuh melalui antarmuka tersebut.

1. 📖 KAMUS ISTILAH DOMAIN BAKU (GLOSSARY ARCHITECTURE):
   Wajib gunakan istilah presisi berikut secara konsisten tanpa mencampuradukkannya dengan konsep ambigu:
   - Module: Segala konstruksi logika yang memiliki antarmuka dan implementasi (fungsi, struct/class, berkas nano-modular, atau subsistem). Dilarang menggantinya dengan "component", "service", atau "unit".
   - Interface: Segala hal yang wajib diketahui pemanggil untuk menggunakan modul secara benar (tipe input/output, invarian, kontrak error, karakteristik performa). Hindari istilah "API" atau sekadar "signature".
   - Implementation: Logika dan detail internal di dalam modul yang tersembunyi sepenuhnya dari dunia luar di balik batas publik.
   - Depth (Kedalaman): Rasio daya ungkit (*leverage*) pada antarmuka. Modul Mendalam (*Deep Module*) memiliki antarmuka yang sangat ringkas namun menyembunyikan implementasi yang kaya. Modul Dangkal (*Shallow Module*) memiliki antarmuka yang rumit namun implementasi tipis (*pass-through/wrapper*).
   - Seam: Batas fisik atau logis tempat antarmuka modul hidup, di mana perilaku modul dapat diubah atau diuji tanpa memodifikasi kode pemanggil. Hindari istilah "boundary".
   - Adapter: Implementasi konkret yang memenuhi kontrak antarmuka pada suatu seam.
   - Leverage: Keuntungan pemanggil: kapabilitas maksimal diperoleh hanya dengan mempelajari antarmuka yang sangat sederhana.
   - Locality: Keuntungan pemelihara: perbaikan bug, state, dan logika terpusat di satu tempat (perbaiki satu titik, benar di seluruh sistem).

2. 📐 SINTESIS MODUL MENDALAM DENGAN NANO-MODULAR SURGICAL (20–80 BARIS):
   - Modul Mendalam BUKAN monolit raksasa ribuan baris.
   - Dalam ekosistem Flowork OS, Modul Mendalam diwujudkan melalui orkestrasi nano-modular:
     * Fasad publik (Public Entrypoint): Diekspos sebagai antarmuka tunggal yang ramping dan berdaya ungkit tinggi.
     * Implementasi internal: Dipecah secara bedah menjadi berkas-berkas nano-modular 20–80 baris (1 berkas 1 logika/fungsi) di balik seam privat.
     * Hasil: Pemanggil luar menikmati antarmuka mendalam tanpa beban kognitif, sementara kode internal tetap membatasi radius kesalahan (blast radius) dan mudah dirawat.
