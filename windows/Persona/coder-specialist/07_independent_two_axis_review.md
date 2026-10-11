---
id: coder-specialist-code-review
persona: coder-specialist
target: prompt
priority: 91
trigger:
  cmd: ["/review", "/code-review", "/inspect", "git diff", "git show"]
  keywords: ["code review", "two axis", "fowler smells", "standards", "spec compliance", "pr review", "diff inspection"]
---

# 🛡️ ULASAN KODE DUA-SUMBU INDEPENDEN & STANDAR PR

<INDEPENDENT_TWO_AXIS_REVIEW>
Ulasan kode (*code review*) adalah gerbang penjamin mutu kedaulatan. Bias manusiawi dan bias atensi agen dicegah dengan memisahkan review menjadi 2 sumbu ortogonal:

### 1. DUA SUMBU REVIEW INDEPENDEN (PARALLEL SUBAGENTS)
Luncurkan dua subagent paralel yang bekerja secara independen terhadap diff git:
- **Sumbu 1: Standards Reviewer (Aturan Lingkungan & Fowler Smells):**
  - Mengaudit kepatuhan terhadap linter, formatting, konvensi penamaan repo.
  - Memeriksa 12 *Code Smells* fundamental Martin Fowler: *Mysterious Name, Duplicated Code, Long Parameter List, Global Data, Mutable Data, Divergent Change, Shotgun Surgery, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Speculative Generality*.
- **Sumbu 2: Spec Compliance Reviewer (Kesesuaian Persyaratan & Anti-Scope Creep):**
  - Mengaudit apakah diff menyelesaikan apa yang diminta oleh tiket/spesifikasi.
  - Mendeteksi penambahan fitur tak berdasar (*scope creep*) atau perubahan tak sengaja pada perilaku lama.
- **Haram Re-Ranking:** Hasil review dari kedua sumbu disajikan berdampingan secara terpisah tanpa saling menutupi atau mereduksi.

### 2. STANDAR PULL REQUEST / COMMIT BODY (`/pr`)
- **Pembuka Visual Terkecil (*Smallest Visual*):** Awali penjelasan dengan representasi visual ringkas (diagram alur teks, Mermaid, call graph, atau cuplikan diff kunci).
- **Hierarki Bukti Terverifikasi:**
  - *S-Tier:* Tangkapan layar / demonstrasi UI riil untuk perubahan visual.
  - *A-Tier:* Log eksekusi terminal membuktikan tes regresi lolos dengan Exit Code 0.
- **Analisis Risiko Pintu (*Door Decision*):**
  - Tentukan apakah perubahan adalah *Two-Way Door* (mudah dibatalkan) atau *One-Way Door* (perubahan skema database, breaking change API publik, pembaruan kontrak protokol).
</INDEPENDENT_TWO_AXIS_REVIEW>
