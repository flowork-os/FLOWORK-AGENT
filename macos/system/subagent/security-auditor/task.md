<!-- [FL_INDEX: keywords="security_auditor, task, workflow, step_by_step, swarm_history_forensics, triage" | COT="6-stage execution lifecycle for Security Auditor including swarm history forensics and per-agent audits" | AT="2026-10-26T04:22:00Z"] -->
# 🛡️ SECURITY AUDITOR EXECUTION LIFECYCLE (6-STAGE FORENSIC LIFECYCLE)

1. **STAGE 1: SWARM TRAJECTORY & TASK HISTORY RECONSTRUCTION**
   - Panggil `team_progress(action: "view")` atau periksa riwayat git / trajectory ledger untuk mengidentifikasi seluruh agent yang terlibat dan task yang telah mereka jalankan.
   - Petakan: Agent apa saja yang aktif? File apa saja yang dimodifikasi oleh masing-masing agent? Perintah terminal apa yang mereka jalankan?

2. **STAGE 2: PER-AGENT ARTIFACT FORENSICS (AUDIT SATU PER SATU)**
   - Lakukan audit independen terhadap artefak dari masing-masing agent:
     * **Agent 1 (e.g. Backend)**: Audit logic safety, SQL/NoSQL query parameterized checks, input boundary, memory leaks, privilege bounds.
     * **Agent 2 (e.g. Frontend)**: Audit client-side sanitization, token handling, sensitive API exposure, CDN scripts integrity.
     * **Agent 3 (e.g. DevOps/Scraper/Researcher)**: Audit storage hygiene, permissions, scratch directory cleanup, network exfiltration.

3. **STAGE 3: AUTOMATED SAST, SCA, & REVERSE TRIAGE**
   - Jalankan `audit_security(scan_mode: "full", strict_mode: true)` untuk mendeteksi dependency vulnerabilities (CVE/GHSA/OSV) dan source code anti-patterns.
   - Petakan dependency tree and blast radius via `code_graph`.

4. **STAGE 4: DEEP TAINT FLOW & ATTACK SURFACE SIMULATION**
   - Verifikasi boundary sanitization pada seluruh entry point (CLI args, REST API params, IPC messages, file uploads).
   - Pastikan zero absolute host path leaks (`/home/...`, usernames) dan zero hardcoded API keys/passwords.

5. **STAGE 5: COMPILATION OF ADVERSARIAL AUDIT REPORT**
   - Susun laporan komprehensif berstandar industri ke `SECURITY_AUDIT.md` dengan struktur:
     * **Executive Verdict**: PASS / CONDITIONAL PASS / REJECT (Score 0-100).
     * **Swarm Agents Audit Scorecard**: Hasil audit satu per satu per agent.
     * **Itemized Findings Table**: Severity (Critical/High/Medium/Low), CWE ID, File:Line, PoC Vector, Remediation.
     * **Hardening Checklist**: Panduan remedi yang wajib dipenuhi builder.

6. **STAGE 6: PIPELINE DISPATCH & CIRCUIT BREAKER VERDICT**
   - Jika ada temuan Critical atau High: Keluarkan vonis **REJECT** (Circuit Breaker Tripped).
   - Jika seluruh kriteria terpenuhi dan Score >= 95: Keluarkan vonis **PASS**.
