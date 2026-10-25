[FL_INDEX: keywords="red_team_task, pentest_lifecycle, attack_flow, remediation_matrix, execution_template" | purpose="Standard task breakdown template for red-team penetration testing cycles"]
# 📋 Red Team Pentest & Adversary Emulation Lifecycle

## Phase 1: Target Scoping & Reconnaissance
- [ ] Map active attack surface, open ports, exposed APIs, and daemon sockets.
- [ ] Inspect dependency trees for known CVEs and outdated package advisories.
- [ ] Catalog authorization boundaries, token flows, and access control models.

## Phase 2: Vulnerability Analysis & Weaponization Check
- [ ] Test authentication, session management, and JWT signature validation.
- [ ] Check injection vectors (SQLi, Command Injection, Path Traversal, SSRF).
- [ ] Evaluate misconfigurations in environment isolation, CORS, and permission gates.

## Phase 3: Simulated Exploitation & Impact Verification
- [ ] Execute safe, isolated PoC verification to demonstrate exploitability.
- [ ] Trace privilege escalation potential (horizontal and vertical).
- [ ] Check sensitive secret exposure, credential leakage, and insecure logging.

## Phase 4: Reporting & Remediation Handoff
- [ ] Build Executive Summary and Technical Finding Matrix.
- [ ] Provide patch snippets and defensive architectural recommendations.
- [ ] Verify fix verification with Security Auditor and Lead Architect.
