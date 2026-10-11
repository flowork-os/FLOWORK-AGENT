---
id: fl-coder-snapshot
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-snapshot
    - /fl-handoff
  keywords:
    - handoff
    - snapshot
    - context window
    - save state
---

# 📦 PENYELAMATAN STATE SESI (SESSION SNAPSHOT & HANDOFF)

<SESSION_SNAPSHOT_ENGINE>
1. **PENYELAMATAN SEBELUM BATAS DEGRADASI (~150K SMART ZONE):**
   - Ketika konteks kerja mulai membengkak atau sebelum beralih ke sesi tiket implementasi baru:
     - Jangan biarkan penalaran terdegradasi.
     - Simpan snapshot lengkap ke direktori OS sementara (`$TMPDIR/fl-snapshot-<timestamp>.md`).

2. **FORMAT STRUKTUR SNAPSHOT:**
   - **Tujuan Sesi:** Definisi ringkas tugas yang sedang dikerjakan.
   - **Keputusan Terkunci:** ADR atau kesepakatan arsitektur yang sudah final.
   - **Status Berkas & Diff:** Rangkuman file yang diubah dan pengujian yang sudah lolos.
   - **Pertanyaan Terbuka:** Isu yang belum terselesaikan untuk sesi berikutnya.
   - **Rekomendasi Rantai Skill:** Skill/command berikutnya yang disarankan (misal: `/fl-execute`, `/fl-review`).

3. **PEMULIHAN KONTINU:**
   - Sesi baru membaca snapshot ini sebagai sumber primer dan dapat langsung beroperasi dengan jendela konteks 100% bersih dan tajam.
</SESSION_SNAPSHOT_ENGINE>
