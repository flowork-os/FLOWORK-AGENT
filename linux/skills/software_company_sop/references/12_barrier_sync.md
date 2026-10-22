# Phase Barrier Synchronization & DAG Orchestration SOP

## 1. Role Mandate & Core Standard
The Swarm Leader manages phase execution barriers. Multi-agent execution operates as a directed acyclic graph (DAG) where downstream squads cannot execute until upstream milestones pass validation gates.

## 2. Mandatory Synchronization Invariants
1. **Barrier 1 (Architecture Ready):** Backend & Frontend cannot code until PRD and Architecture documents are signed off.
2. **Barrier 2 (Implementation Frozen):** Security and QC cannot audit until code implementation files are physically written.
3. **Barrier 3 (Release Clearance):** Release deployment cannot proceed without dual Security (0 High/Critical CVEs) and QC (Exit Code 0) clearance.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE DELIVERABLES BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before creating or modifying deliverables, you MUST inspect the specific example blueprint:
`view_file` -> `skills/software_company_sop/example/12_dag_barrier_synchronization.json`
Adhere strictly to the structure and schema defined in this blueprint.
