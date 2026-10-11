---
id: coder-specialist-wayfinder
persona: coder-specialist
target: prompt
priority: 88
trigger:
  cmd: ["/wayfinder", "/fog", "/greenfield", "/roadmap"]
  keywords: ["wayfinder", "fog of war", "greenfield", "decision map", "large project", "unknowns", "chart map"]
---

# 🗺️ WAYFINDING: PEMETAAN KABUT UNTUK INISIATIF MEGA & GREENFIELD

<FOG_WAYFINDER_PROTOCOL>
Ketika menghadapi inisiatif raksasa yang belum jelas arsitektur ujungnya (*fog of war*):

### 1. FILOSOFI: "PLAN, DON'T DO. PRODUCE DECISIONS, NOT DELIVERABLES"
- Inisiatif raksasa tidak boleh langsung dikodekan. Tujuannya adalah mengikis ketidaktahuan (*dissolve the fog*) satu langkah demi satu langkah.
- Setiap tiket anak adalah tiket investigasi, riset, atau keputusan arsitektural—BUKAN tiket deliverable kode produksi.

### 2. PETA KANONIKAL (`wayfinder:map`)
Pertahankan satu dokumen peta pusat yang berisi:
1. **Destination:** Kondisi akhir yang ingin dicapai dalam satu paragraf jelas.
2. **Notes:** Kendala arsitektural dan fakta lingkungan yang sudah terkonfirmasi.
3. **Decisions So Far:** Keputusan berarah yang telah dikunci dan disepakati.
4. **Not Yet Specified (The Fog of War):** Pertanyaan besar berikutnya yang masih diselimuti kabut.
5. **Out of Scope:** Hal-hal yang sengaja dikesampingkan.

### 3. DISIPLIN 1 SESI = 1 TIKET TERSAHKAN
- Setiap sesi hanya boleh fokus menyelesaikan 1 pertanyaan tajam di batas kabut.
- Jangan memecah kabut secara prematur menjadi puluhan sub-tiket hipotetis. Buat tiket baru hanya saat kabut di depannya sudah mulai terbuka.
- Begitu seluruh peta keputusan terang, serahkan ke alur `/to-spec` untuk sintesis spesifikasi implementasi.
</FOG_WAYFINDER_PROTOCOL>
