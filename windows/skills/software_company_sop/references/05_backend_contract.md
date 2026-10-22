# Backend Contract & API Definition SOP

## 1. Role Mandate & Core Standard
The Backend Engineer owns the implementation contracts. All service boundaries, database schemas, and IPC channels must publish explicit type definitions before downstream consumers write UI or glue code.

## 2. Mandatory Contract Invariants
1. **Strict Type Signatures:** No ambient `any` or loose dictionaries; declare all request and response structures explicitly.
2. **Deterministic Error Schemas:** Every error returns a standardized payload with machine-readable error codes and human-readable messages.
3. **Multi-OS File & Path Independence:** Path operations must dynamically use platform path separators; hardcoding host paths is strictly forbidden.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE DELIVERABLES BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before creating or modifying deliverables, you MUST inspect the specific example blueprint:
`view_file` -> `skills/software_company_sop/example/05_api_service_contract.ts`
Adhere strictly to the structure and schema defined in this blueprint.
