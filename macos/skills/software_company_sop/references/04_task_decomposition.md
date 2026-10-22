# Task Decomposition & Dependency DAG SOP

## 1. Role Mandate & Core Standard
The Project Lead / Architect decomposes system requirements into directed acyclic graphs (DAGs). Monolithic, multi-concern tasks are prohibited; each task must be atomic and assigned to a single specialist node.

## 2. Mandatory Task Decomposition Rules
1. **Atomic Work Units:** Each task targets a single module, interface, or test suite.
2. **Explicit Dependency Edges:** Upstream prerequisites must be strictly mapped before downstream execution.
3. **Acceptance Criteria Binding:** Each task carries explicit, verifiable pass/fail criteria.
4. **Execution Role Binding:** Explicitly assigned to Leader, Backend, Frontend, Security, or QC.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE DELIVERABLES BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before creating or modifying deliverables, you MUST inspect the specific example blueprint:
`view_file` -> `skills/software_company_sop/example/04_dag_task_breakdown.md`
Adhere strictly to the structure and schema defined in this blueprint.
