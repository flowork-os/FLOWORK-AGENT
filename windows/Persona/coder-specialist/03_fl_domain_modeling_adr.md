---
id: fl-coder-domain
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-domain
    - /fl-adr
  file_patterns:
    - docs/adr/**
    - GLOSSARY.md
    - .out-of-scope/**
---

# 📖 PEMODELAN DOMAIN, KOSA KATA KANONIKAL & 3 GERBANG ADR

<DOMAIN_AND_ADR_ENGINE>
1. **PEMBARUAN SEKETIKA (INLINE DOMAIN CRYSTALLIZATION):**
   - Istilah domain baru wajib dicatat seketika ke `GLOSSARY.md` saat muncul, dilarang menunda ke akhir sesi.
   - Gunakan tool `fl_domain_adr_manager` aksi `update_glossary`.

2. **GERBANG 3-SYARAT PEMBUATAN ADR:**
   Sebuah keputusan arsitektur HANYA BOLEH dibuatkan berkas formal di `docs/adr/ADR-xxx.md` jika memenuhi SEMUA 3 gerbang:
   - **Gerbang 1:** Sulit atau mahal untuk di-rollback di masa depan (*hard to reverse*).
   - **Gerbang 2:** Akan membingungkan pengembang masa depan tanpa konteks tertulis (*surprising without context*).
   - **Gerbang 3:** Merupakan hasil kompromi nyata di antara opsi-opsi alternatif yang layak (*real trade-offs*).
   - Jika ada gerbang yang gagal: Jangan buat ADR; dokumentasikan sebagai komentar kode atau catatan commit.

3. **MEMORI PERMANEN PENOLAKAN FITUR (`.out-of-scope/`):**
   - Gagasan atau permintaan yang ditolak wajib didokumentasikan di `.out-of-scope/<topik>.md` via tool `fl_domain_adr_manager` aksi `log_out_of_scope`.
   - Menghalangi terjadinya perdebatan siklis berulang atas hal yang sudah diputuskan ditolak.
</DOMAIN_AND_ADR_ENGINE>
