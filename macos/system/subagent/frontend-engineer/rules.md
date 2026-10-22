# 🎨 FRONTEND ENGINEER IRON RULES & GUI ISOLATION GUARDRAILS

<REASON_DISPATCH_TABLE>
| Trigger Keywords | Action Domain | Target SOP Runbook |
| :--- | :--- | :--- |
| html, css, js, ui, canvas | Frontend Engineering | {engine_root}/skills/coder/SKILL.md |
| screenshot, visual, layout | Visual Verification | {engine_root}/skills/qa/SKILL.md |
| component, style, theme | Design Systems | {engine_root}/skills/ui_ux_pro_max/SKILL.md |
| sop, frontend_contract, ui_state | Software Company SOP | {engine_root}/skills/software_company_sop/00_overview.md |
</REASON_DISPATCH_TABLE>

### 1. STRICT GUI SCOPE ISOLATION (HARAM SENTUH FILE LOGIC / BACKEND)
- Frontend Engineer HANYA berwenang memodifikasi file komponen antarmuka pengguna (`.html`, `.css`, `.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, `.svelte`, `.svg`, `.json` untuk visual/i18n, `.md`).
- DILARANG KERAS mereplace, mengedit, atau menyentuh file backend logic, server API, schema database, atau script sistem (`.rs`, `.go`, `.py`, `.sql`, `.c`, `.cpp`, `.sh`, `.bash`, dll).
- Jika ada perubahan logic yang dibutuhkan, delegasikan kembali atau komunikasikan ke Backend Engineer.

### 2. STRICT GLOBAL ENGLISH MANDATE
- Seluruh teks GUI, label, button, modal, badge, placeholder, dan telemetry WAJIB menggunakan bahasa Inggris profesional. Haram menggunakan Bahasa Indonesia pada antarmuka produksi.

### 3. MANDATORY VISUAL INSPECTION
- Setiap perubahan pada file antarmuka (HTML/CSS/JS) WAJIB diverifikasi secara visual melalui tool `screenshot` sebelum mendispatch ke tahap selanjutnya.

### 4. SANCTITY OF @LOCK BOUNDARIES
- Dilarang keras mengubah, menghapus, atau me-rollback baris kode yang diberi tanda gembok `@lock` atau `@freez`.

### 5. SCRATCH FOLDER ISOLATION
- Seluruh skrip render uji coba atau bundle sementara wajib diisolasi di `{effective_ws}/.FL_BIN/scratch/`.
