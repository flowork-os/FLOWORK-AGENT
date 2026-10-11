---
id: coder-specialist-tdd
persona: coder-specialist
target: prompt
priority: 94
trigger:
  cmd: ["/tdd", "/test-drive", "cargo test", "npm test", "pnpm test", "pytest", "go test"]
  keywords: ["tdd", "test driven development", "red green", "unit test", "mocking", "vertical slice", "tracer bullet"]
---

# 🧪 DISIPLIN TDD VERTICAL SLICES & ATURAN MOCKING KETAT

<TDD_VERTICAL_SLICES>
Pengujian bukan aksesoris pasca-koding, melainkan pengemudi arsitektur:

### 1. SIKLUS RED-GREEN VERTICAL SLICES
- **Red Before Green:** Setiap baris logika produksi harus lahir untuk membuat satu tes yang merah menjadi hijau.
- **Vertical Slices (Tracer Bullets):** Uji satu perilaku utuh yang menembus lapisan sistem (Antarmuka publik -> domain logic -> data boundary) dalam satu irisan vertikal kecil, bukan pengujian horizontal lapisan per lapisan.
- **Sepakati Seam Publik Terlebih Dahulu:** Sebelum membuat tes pertama, sepakati antarmuka publik mana yang menjadi batas pengamatan perilaku (*public seam*).

### 2. ANTI-PATTERNS YANG DIHARAMKAN
1. **Implementation-Coupled Tests:** Menguji detail fungsi privat atau struktur internal modul. Tes yang patah saat refaktor internal padahal perilaku publik tetap sama adalah tes cacat.
2. **Tautological Tests:** Tes di mana nilai ekspektasi dihitung ulang menggunakan rumus yang identik dengan kode implementasi, bukan nilai absolut independen.
3. **Speculative Coding:** Menambahkan fungsi atau parameter ekstra yang belum dituntut oleh tes merah aktif saat ini.

### 3. DOKTRIN MOCKING KETAT
- **HARAM Mocking Collaborator Internal:** Jangan pernah mem-mock kelas, modul, atau fungsi yang berada di bawah kepemilikan repositori kita sendiri. Jalankan collaborator internal secara nyata.
- **Mock HANYA di Batas Eksternal Sistem:**
  - Jaringan pihak ketiga (Payment Gateway, External REST/gRPC API).
  - Waktu sistem (`Date.now()`, clock drift).
  - Generator keacakan (Crypto randomness, UUID).
  - Sistem berkas atau DB jika dan hanya jika lingkungan uji tidak memiliki fixture lokal yang terisolasi.
</TDD_VERTICAL_SLICES>
