---
id: fl-coder-guardrails
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-guardrails
    - /fl-git-guard
  keywords:
    - git guardrails
    - git safety
    - force push
    - reset hard
    - branch protection
---

# 🛑 PENGAMAN INTEGRITAS GIT & INTERSEPTOR PERINTAH DESTRUKTIF

<GIT_GUARDRAILS_ENGINE>
1. **INTERSEPSI PRE-TOOL PERINTAH DESTRUKTIF:**
   - Gunakan tool `fl_git_guardrails` aksi `validate_command` untuk memeriksa setiap perintah Git sebelum dieksekusi.
   - Operasi berikut DIBLOKIR TOTAL secara fail-closed:
     - `git push` dengan `--force` / `-f` / `+`
     - `git reset --hard`
     - `git clean -f` / `git clean -fd`
     - `git branch -D`
     - `git checkout .` / `git restore .`
     - `git rebase --abort` (tanpa menganalisis akar konflik)

2. **DOKTRIN RESOLUSI KONFLIK BERBASIS INTENSI PRIMER:**
   - Konflik Git adalah benturan dua intensi manusia, bukan sekadar benturan baris teks.
   - Telusuri commit history, PR, atau issue dari kedua cabang sebelum menyentuh hunk konflik.
   - Dilarang keras blind `--ours` atau `--theirs`. Jalankan loop pengujian otomatis (typecheck + test suite) hingga Exit Code 0 sebelum menuntaskan merge.
</GIT_GUARDRAILS_ENGINE>
