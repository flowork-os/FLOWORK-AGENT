---
id: fl-coder-spec-dag
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-spec
    - /fl-task-graph
  keywords:
    - spec
    - dag
    - task graph
    - tickets
    - frontier
---

# 📋 REKAYASA SPESIFIKASI & GRAF TIKET BERARAH (DAG)

<SPEC_AND_DAG_ENGINE>
1. **SINTESIS SPESIFIKASI NOL-WAWANCARA (ZERO-REINTERVIEW SPEC):**
   - Sintesiskan spesifikasi formal dari hasil alignment sebelumnya.
   - Cantumkan:
     - User stories dan acceptance criteria `- [ ]` yang teruji.
     - Tipe antarmuka dan kontrak seam yang eksplisit.
     - **DILARANG MENCANTUMKAN PATH FILE & NOMOR BARIS RAPUH** di dalam brief agar spesifikasi tidak lapuk (*drift*).

2. **DEKOMPOSISI GRAF TIKET BERARAH (DAG TASK GRAPH):**
   - Setiap tugas wajib memiliki relasi ketergantungan eksplisit (`blocked_by`).
   - Ukuran satu tiket: Dapat diselesaikan dalam 1 sesi jendela konteks bersih (~100k token).

3. **EVALUASI FRONTIER AKTIF & POLA EXPAND-CONTRACT:**
   - Gunakan tool `fl_dag_task_graph` aksi `evaluate_frontier` untuk memvalidasi asiklisitas graf (bebas circular dependency) dan menemukan tiket yang siap dieksekusi paralel.
   - Jalankan pola *Expand-Contract* saat mengubah skema/API: perkenalkan endpoint baru berdampingan, migrasikan callers, lalu hapus endpoint lama.
</SPEC_AND_DAG_ENGINE>
