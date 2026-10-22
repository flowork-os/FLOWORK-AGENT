# Release Gate & Tri-Gate Delivery SOP

## 1. Role Mandate & Core Standard
The Swarm Leader and Quality Control lead enforce release clearance. Deliverables must satisfy all three sovereign release gates before being marked ready for deployment or community publication.

## 2. Mandatory Release Gate Checklist
1. **Gate 1 (Security & Multi-OS):** Zero secret leaks, 0 high/critical CVEs, and 0 hardcoded absolute host paths.
2. **Gate 2 (Functional Integrity):** 100% of functional requirements pass with deterministic Exit Code 0 test output.
3. **Gate 3 (Hygiene & Sanctity):** Teardown of scratch files, zero zombie processes, and 100% sanctity of `@lock` blocks.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE DELIVERABLES BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before creating or modifying deliverables, you MUST inspect the specific example blueprint:
`view_file` -> `skills/software_company_sop/example/13_tri_gate_release_checklist.md`
Adhere strictly to the structure and schema defined in this blueprint.
