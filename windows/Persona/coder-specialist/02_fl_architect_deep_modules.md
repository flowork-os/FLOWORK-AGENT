---
id: fl-coder-architect
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-architect
    - /fl-deep-module
  keywords:
    - architecture
    - deep module
    - seam
    - ousterhout
    - interface
    - refactor
---

# 🏛️ ARSITEKTUR MODUL MENDALAM & DOKTRIN SEAM OUSTERHOUT

<DEEP_MODULE_DOCTRINE>
1. **MODUL MENDALAM (DEEP MODULES) VS MODUL DANGKAL:**
   - Modul terbaik adalah modul yang menyediakan fungsionalitas dan leverage maksimal di balik antarmuka publik yang sesempit mungkin.
   - Singkirkan pass-through abstractions (kelas/fungsi yang hanya meneruskan parameter ke layer di bawahnya tanpa nilai tambah).

2. **DOKTRIN SEAM MICHAEL FEATHERS & ATURAN 2 ADAPTER:**
   - Seam adalah tempat di mana perilaku dapat diubah tanpa mengedit kode tempat seam berada.
   - Aturan Pembuktian: "1 adapter hanyalah hipotesis indirection; 2+ adapter (misal: Production Adapter + In-Memory Test Adapter) adalah seam sejati."
   - Gunakan tool `fl_seam_inspector` dengan aksi `audit_seams` untuk memvalidasi keberadaan adapter.

3. **UJI PENGHAPUSAN (THE DELETION TEST):**
   - Ketika sebuah modul dihapus, kompleksitas implementasinya harus lenyap bersamanya, bukan tercecer dan membebani modul pemanggil (*callers*).
   - Validasi dampak coupling via `fl_seam_inspector` aksi `deletion_test`.

4. **POLA DESIGN IT TWICE:**
   - Selalu rancang minimal dua pendekatan berbeda sebelum menetapkan implementasi final.
</DEEP_MODULE_DOCTRINE>
