---
id: fl-coder-tdd
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-red-green
    - /fl-tdd
  keywords:
    - test
    - tdd
    - unit test
    - red green
---

# 🧪 SIKLUS TDD TRACER-BULLET & BATAS MOCKING KEDAULATAN

<TDD_SEAM_DOCTRINE>
1. **TRACER-BULLET IRISAN VERTIKAL (VERTICAL SLICES):**
   - Bangun irisan fungsionalitas tipis yang memotong seluruh lapisan sistem (skema -> domain logic -> antarmuka publik -> assertions) dan dapat dieksekusi langsung.
   - Hindari pengerjaan horizontal layer-pertama (seperti membuat seluruh DB schema tanpa ada kode logika yang memanggilnya).

2. **DOKTRIN BATAS MOCKING KETAT:**
   - DILARANG MENGUJI INTERNAL IMPLEMENTATION DETAIL (fungsi privat atau struktur internal).
   - DILARANG MEMBUAT MOCK PADA KOLABORATOR INTERNAL SENDIRI.
   - Mocking HANYA SAH pada batas sistem eksternal: Jam sistem / waktu, generator bilangan acak, dan API pihak ketiga non-deterministik.

3. **SIKLUS TDD MERAH-KE-HIJAU PADA SEAM PUBLIK:**
   - Tahap Merah: Tulis tes yang gagal karena perilaku belum ada, bukan karena syntax error.
   - Tahap Hijau: Tulis kode minimal untuk meloloskan tes (Exit Code 0).
   - Tahap Refaktor: Perbaiki kedalaman modul dan hilangkan duplikasi dengan rasa aman karena tes tetap hijau.
</TDD_SEAM_DOCTRINE>
