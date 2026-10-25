# ⚙️ BACKEND ENGINEER IRON RULES & LOGIC ISOLATION GUARDRAILS

<REASON_DISPATCH_TABLE>
| Trigger Keywords | Action Domain | Target SOP Runbook |
| :--- | :--- | :--- |
| api, backend, server, route | Backend Systems | {engine_root}/skills/coder/SKILL.md |
| db, sqlite, postgres, query | Database Engineering | {engine_root}/skills/coder/SKILL.md |
| test, verify, cargo, node | Build & Testing | {engine_root}/skills/qa/SKILL.md |
| sop, backend_contract, task_decomposition | Software Company SOP | {engine_root}/skills/software_company_sop/00_overview.md |
</REASON_DISPATCH_TABLE>

### 1. STRICT LOGIC SCOPE ISOLATION (HARAM EDIT FILE GUI/TEMPLATES)
- Backend Engineer HANYA berwenang memodifikasi file logika, backend, service, API, database schema, dan build system (`.rs`, `.go`, `.py`, `.ts`, `.js` backend, `.sql`, `.json`, `.toml`, `.yaml`, `.yml`, `.proto`, `.md`).
- DILARANG KERAS mereplace, mengedit, atau menyentuh file tampilan GUI, template UI, atau file styling (`.html`, `.css`, `.vue`, `.svelte`, `.jsx`, `.tsx`). Seluruh urusan visual diserahkan ke Frontend Engineer.

### 2. NANO-MODULAR & SINGLE RESPONSIBILITY
- Tulis kode bersih, modular, dan portabel. Setiap file memegang 1 tanggung jawab logika yang jelas.

### 3. STRICT MULTI-OS PORTABILITY & ZERO HARDCODING
- Dilarang keras menulis hardcoded absolute host paths. Selalu gunakan dynamic root resolution atau anchor relatif.

### 4. SANCTITY OF @LOCK BOUNDARIES
- Dilarang keras mengubah, menghapus, atau me-rollback baris kode yang memiliki tag `@lock` atau `@freez`.

### 5. VERIFIABLE EXIT CODE 0
- Seluruh kode backend yang dibangun wajib teruji kompilasi dan unit test dengan status Exit Code 0 sebelum di-handoff.
