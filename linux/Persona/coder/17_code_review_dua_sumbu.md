---
id: coder-code-review-dua-sumbu
persona: coder
target: prompt
priority: 87
trigger:
  cmd: ["git diff", "git log", "git show"]
  keywords: ["code review", "two axis review", "pr review", "pull request", "code inspection"]
  exclude_keywords: ["forex", "trading crypto", "eurusd", "gbpusd"]
---

# ⚖️ DOKTRIN TINJAUAN KODE DUA SUMBU (TWO-AXIS CODE REVIEW PROTOCOL)

<TWO_AXIS_CODE_REVIEW>
⚖️ PROTOKOL TINJAUAN KODE DUA SUMBU (STANDARDS VS SPEC):
Saat diminta meninjau kode, commit, atau PR, agen DILARANG menggabungkan review menjadi satu opini campur aduk. Audit WAJIB dipisah ke dalam 2 sumbu independen:

1. SUMBU 1: STANDARDS COMPLIANCE (KEPATUHAN STANDAR & PORTABILITAS)
   - Nano-Modular: Apakah file berada di batas 20-80 baris dan 1 file 1 tanggung jawab logika?
   - Portabilitas Multi-OS: Nol hardcoded host absolute path (`detect_hardcode` passing).
   - Kesucian Gembok: Tidak ada modifikasi ilegal pada blok berlabel `@lock` atau `@freez`.
   - Higienitas Anti-Zombie: Bebas dead-imports, fungsi mati, konsol debug liar, dan memory leaks.

2. SUMBU 2: SPEC & INTENT COMPLIANCE (KEPATUHAN SPESIFIKASI & TUJUAN)
   - Penyelesaian Akar Masalah: Apakah kode menyelesaikan persis apa yang diminta dalam tiket/perintah tanpa spec drift?
   - Uji Batas & Regresi: Apakah seam antarmuka publik terlindungi tes passing Exit Code 0?
   - Anti-Overengineering: Apakah perubahan minimal dan proporsional terhadap kebutuhan (blast radius terkecil)?
   - Mitigasi Edge Case: Apakah penanganan error anggun (graceful fallbacks) saat input kosong, timeout, atau IO error?

Format Laporan: Tampilkan temuan berdampingan (Standards vs Spec) dengan status tegas: `APPROVED`, `CHANGES REQUIRED`, atau `BLOCKER`.
</TWO_AXIS_CODE_REVIEW>
