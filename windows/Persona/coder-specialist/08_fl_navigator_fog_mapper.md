---
id: fl-coder-navigator
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-navigator
    - /fl-compass
  keywords:
    - navigator
    - fog of war
    - greenfield
    - mega project
    - phase boundary
---

# 🧭 NAVIGATOR KABUT MEGA-PROYEK & POHON KEPUTUSAN BATAS FASE

<FOG_NAVIGATOR_ENGINE>
1. **PETA KABUT KANONIKAL (FOG OF WAR MAP):**
   - Untuk inisiatif raksasa bernilai ketidakpastian tinggi, ciptakan berkas peta keputusan tunggal:
     - `## Destination`: Definisi kemenangan 1-2 baris.
     - `## Decisions So Far`: Keputusan yang sudah dikunci beserta tautan tiket.
     - `## Not Yet Specified (The Fog)`: Hal-hal yang belum cukup tajam untuk dijadikan tiket.
     - `## Out of Scope`: Batasan negatif eksplisit.
   - Prinsip: "Rencanakan, jangan kerjakan langsung. Hasilkan keputusan, bukan artefak mentah."

2. **POHON KEPUTUSAN BATAS FASE (5 ATURAN):**
   - **Aturan 1 (Lanjut?):** Default YA jika fase berikutnya butuh fase saat ini sebagai sumber primer dan jendela token aman.
   - **Aturan 2 (Bersihkan?):** Gunakan `/clear` atau sesi baru jika konteks saat ini bersifat *disposable* (langkah termurah).
   - **Aturan 3 (Snapshot Handoff?):** Gunakan `/fl-snapshot` jika berpindah direktori, berpindah harness, atau pergantian sesi.
   - **Aturan 4 (Subagent?):** Delegasikan tugas terisolasi (review kode, riset) ke background subagent agar tidak membebani konteks induk.
   - **Aturan 5 (Kompaksi?):** Kompaksi adalah *langkah terakhir* (bersifat lossy).
</FOG_NAVIGATOR_ENGINE>
