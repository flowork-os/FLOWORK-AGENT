---
id: fl-coder-review
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-review
    - /fl-pr
  keywords:
    - code review
    - review diff
    - pr
    - fowler smells
---

# 🛡️ ULASAN KODE DUA-SUMBU & ANALISIS PINTU RISIKO

<TWO_AXIS_REVIEW_ENGINE>
1. **ULASAN DUA-SUMBU PARALEL INDEPENDEN:**
   - Evaluasi diff kode menggunakan tool `fl_code_review` secara terpisah pada 2 sumbu:
     - **Sumbu 1 (Standards & Fowler Smells):** Mendeteksi nesting >4 level, fungsi >60 baris, kebocoran secret, dead code, TODO menggantung, dan duplikasi.
     - **Sumbu 2 (Spec Conformance):** Memverifikasi pemenuhan acceptance criteria dan mencegah *scope creep* (perubahan liar tak berizin).
   - **DILARANG MERATING ULANG (NO RE-RANKING):** Jangan biarkan kesempurnaan gaya kode menutupi kegagalan pemenuhan spesifikasi.

2. **DOKTRIN PINTU SATU-ARAH VS DUA-ARAH (ONE-WAY VS TWO-WAY DOORS):**
   - *Two-Way Door:* Perubahan yang mudah dibalik (ubah warna, refaktor fungsi privat). Izinkan meluncur cepat.
   - *One-Way Door:* Keputusan mahal (perubahan skema database produksi, public API contract, pilihan library inti). Wajib audit ketat dan ADR tertulis.

3. **RINGKASAN PR VISUAL PADAT:**
   - Sajikan bukti terminal Exit Code 0, tautan diff, dan sorotan keputusan terbuka.
</TWO_AXIS_REVIEW_ENGINE>
