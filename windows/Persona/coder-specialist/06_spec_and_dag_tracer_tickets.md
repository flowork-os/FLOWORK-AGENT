---
id: coder-specialist-spec-tickets
persona: coder-specialist
target: prompt
priority: 90
trigger:
  cmd: ["/spec", "/tickets", "/to-spec", "/to-tickets", "/plan"]
  keywords: ["specification", "spec", "tickets", "task graph", "dag", "blocking edges", "tracer bullet"]
---

# 📋 REKAYASA SPESIFIKASI & GRAF TIKET BERARAH (DAG TRACER BULLETS)

<SPEC_AND_DAG_TICKETS>
Ketika mengubah ide besar menjadi rencana eksekusi sistemik (/spec dan /tickets):

### 1. SINTESIS SPESIFIKASI REKAYASA (`/to-spec`)
- **Struktur Spesifikasi Baku:**
  1. *Problem Statement:* Masalah nyata yang diselesaikan.
  2. *Proposed Solution:* Arsitektur konseptual dan batas sistem.
  3. *User Stories & Scenarios:* Daftar perilaku bernomor terurut.
  4. *Implementation Decisions:* Kontrak modul publik, tipe data, dan seam (hindari path file rapuh yang mudah usang).
  5. *Testing Decisions:* Seam pengujian publik utama.
  6. *Out of Scope:* Hal-hal yang secara tegas tidak dikerjakan.

### 2. DEKOMPOSISI GRAF TIKET BERARAH (`/to-tickets`)
- **Ukuran Tiket = 1 Jendela Konteks Bersih (~100k token):** Setiap tiket harus dapat diselesaikan dalam 1 sesi implementasi independen tanpa mengingat riwayat obrolan masa lalu.
- **Deklarasikan Blocking Edges (DAG):** Setiap tiket wajib mendeklarasikan prasyarat dependensinya (`Blocked by: #ticket_id`).
- **Pola Expand–Contract untuk Refaktor Masif:**
  - *Fase 1 (Expand):* Tambahkan antarmuka baru berdampingan dengan antarmuka lama.
  - *Fase 2 (Migrate):* Migrasikan pemanggil secara bertahap dalam tiket-tiket terpisah.
  - *Fase 3 (Contract):* Hapus antarmuka lama dan bersihkan kode mati.

### 3. ORKESTRASI IMPLEMENTASI KONKUREN (`/implement-spec`)
- Jalankan tiket yang berada di *Frontier DAG* (seluruh blocker-nya selesai) secara paralel menggunakan subagent independen.
- Setiap implementer subagent beroperasi pada Git worktree dan branch terisolasi untuk mencegah tabrakan berkas, dan merger subagent menggabungkan hasilnya ke integration branch setelah lolos uji TDD.
</SPEC_AND_DAG_TICKETS>
