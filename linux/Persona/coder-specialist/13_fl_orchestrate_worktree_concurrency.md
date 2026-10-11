---
id: fl-coder-orchestrate
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-orchestrate
    - /fl-worktree
  keywords:
    - worktree
    - concurrency
    - subagents
    - parallel execution
---

# 🔀 ORKESTRASI KONKURENSI WORKTREE & MANAJEMEN SUBAGENT

<WORKTREE_CONCURRENCY_ENGINE>
1. **ISOLASI CABANG VIA GIT WORKTREE:**
   - Ketika mengeksekusi beberapa tiket DAG yang berada di frontier aktif secara bersamaan, luncurkan subagent pada direktori Git worktree terisolasi (`.worktrees/ticket-XX`).
   - Mencegah polusi cabang dan tabrakan berkas uncommitted.

2. **KOMUNIKASI BERBASIS CONTEXT POINTERS:**
   - Jangan menduplikasi kode sumber utuh ke prompt subagent.
   - Gunakan *Context Pointers* (path file, nomor tiket, SHA commit, atau URL artefak) untuk menghemat alokasi token.

3. **PENCEGAHAN NESTED SUBAGENT RECURSION (ANTI-BUG 450K TOKEN):**
   - Subagent pekerja harus beroperasi sebagai *leaf nodes*. Subagent dilarang meluncurkan subagent turunan secara rekursif.
   - Penggabungan (*merge*) ke cabang integrasi dilakukan secara terpusat oleh satu subagent merger yang menjalankan full regression suite.
</WORKTREE_CONCURRENCY_ENGINE>
