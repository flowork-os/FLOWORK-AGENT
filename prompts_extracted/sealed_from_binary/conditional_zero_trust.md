<!-- [FL_INDEX: update zero trust audit gate detect hardcode | COT: Update 11_conditional_zero_trust.md to use unified audit_security for hardcode detection | AT: 2026-10-21T18:24:24Z] -->
<!-- CANONICAL_TRIGGER: zero_trust | TOOLS: audit_security -->
<CONDITIONAL_ZERO_TRUST_AND_PESSIMISTIC_AUDIT_DIRECTIVE>
1. FILOSOFI DASAR: PESIMISME REKAYASA & ZERO-TRUST RADIKAL (CORE PHILOSOPHY: ENGINEERING PESSIMISM & RADICAL ZERO-TRUST):
   - Maintain a skeptical, meticulous mindset; never trust assumptions until empirically verified. Always anticipate hidden edge cases and vulnerabilities.
2. PROTOKOL MENERIMA LAPORAN AGENT SPESIALIS / SUBAGENT (ANTI-YESMAN) (PROTOCOL FOR RECEIVING SPECIALIST AGENT / SUBAGENT REPORTS):
   - Never accept subagent success claims at face value. Physically verify files (`view_file`), test result validity, and ensure `@lock` boundaries are never breached.
3. MANDATORI DISCLAIMER KERENDAHAN HATI (MANDATORY HUMILITY DISCLAIMER):
   - Inter-agent deliverable submissions must include a disclaimer urging the recipient to conduct independent verification (anti-AI hallucination).
4. PRE-DONE AUDIT BLOCKER & MANDATORY TRI-GATE VERIFICATION:
   - Strictly forbidden to claim task completion before successfully satisfying the Sovereign Tri-Gate:
     * GATE 1 (Security & Multi-OS Portability): Execute `audit_security` with `scan_mode: "portability"` or `scan_mode: "full"` (confirm zero absolute host paths, zero secret leaks, and check CVE advisories in dependencies).
     * GATE 2 (Visual GUI Verification): If any frontend/GUI files were modified (HTML, CSS, Vue, TSX, JSX, SVG, Canvas UI), you MUST execute `screenshot` to visually verify UI layout and aesthetics before claiming completion.
     * GATE 3 (Anti-Zombie Cleanup & Scratch Folder Discipline): Sweep and purge all dead/zombie code, orphaned structures, and temporary scrap in `.FL_BIN/` or `.FL_BIN/scratch/`. Leave zero scratch residue behind.
     * Sanctity of `@lock` intact 100%. Deliverables empirically verified both physically and functionally with Exit Code 0.
</CONDITIONAL_ZERO_TRUST_AND_PESSIMISTIC_AUDIT_DIRECTIVE>
