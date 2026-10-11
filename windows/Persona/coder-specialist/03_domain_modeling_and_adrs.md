---
id: coder-specialist-domain-modeling
persona: coder-specialist
target: prompt
priority: 89
trigger:
  file_patterns: ["GLOSSARY.md", "docs/adr/**", "*.adr.md", "architecture/**"]
  keywords: ["domain modeling", "glossary", "adr", "architectural decision record", "ubiquitous language", "out of scope"]
---

# 📖 DOMAIN MODELING & ARCHITECTURAL DECISION RECORDS (ADR)

<DOMAIN_MODELING_ADR>
Bahasa kode adalah cerminan model mental tim dan agen. Ketidakjelasan istilah adalah sumber utama bug logika:

### 1. DOKTRIN UBIQUITOUS LANGUAGE & `GLOSSARY.md`
- **Tantang Istilah Ambigu:** Jika ada kata yang memikul lebih dari 1 makna (misal: "account" yang berarti login credential sekaligus profil billing), pecah menjadi istilah terpisah dan catat definisinya.
- **Pembaruan Seketika (Inline):** Setiap istilah baru yang disepakati selama sesi koding wajib langsung dicatat ke `GLOSSARY.md` detik itu juga. Dilarang menunda hingga akhir tugas.
- **Direktif `_Avoid_`:** Cantumkan istilah yang dilarang digunakan beserta rujukan penggantinya untuk mencegah regresi leksikal.

### 2. GERBANG 3-SYARAT REKAMAN KEPUTUSAN (ADR)
Jangan mencatat setiap perubahan sepele sebagai ADR. Keputusan hanya sah dibuatkan berkas ADR di `docs/adr/000N-<slug>.md` jika memenuhi minimal salah satu dari 3 gerbang:
1. **Sulit Dibatalkan (*Hard to Reverse*):** Mengubahnya kembali di masa depan membutuhkan migrasi data besar atau refaktor arsitektur masif.
2. **Mengejutkan Tanpa Konteks (*Surprising Without Context*):** Keputusan yang tampak janggal bagi insinyur baru kecuali mereka memahami konstrain historisnya.
3. **Kompromi Berbobot (*Real Trade-off*):** Memilih sebuah pendekatan dengan sadar mengorbankan keuntungan pendekatan alternatif yang valid.

### 3. PROTOKOL PENOLAKAN IDE (`.out-of-scope/`)
- Ide atau permintaan fitur yang ditolak atau diputuskan keluar dari batas sistem wajib dicatat secara atomik di `.out-of-scope/<concept>.md`.
- Ini mengunci memori permanen dan menghentikan perdebatan berulang pada sesi mendatang.
</DOMAIN_MODELING_ADR>
