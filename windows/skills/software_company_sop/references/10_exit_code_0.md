# Terminal Execution & Exit Code 0 Verification SOP

## 1. Role Mandate & Core Standard
The Quality Control (QC) Engineer owns the execution gate. Per OpenHands principles, no task can be marked complete based on verbal statements or unverified code snippets; empirical terminal execution with Exit Code 0 is required.

## 2. Mandatory Verification Invariants
1. **Physical Shell Execution:** Execute the test suite, build command, or linter via `run_command` in the actual operating environment.
2. **Deterministic Exit Code 0:** The execution process must terminate with a clean exit status (code 0) without unhandled exceptions or panic traces.
3. **Log Evidence Capture:** Retain stdout/stderr output as cryptographic empirical proof in the verification report.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE DELIVERABLES BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before creating or modifying deliverables, you MUST inspect the specific example blueprint:
`view_file` -> `skills/software_company_sop/example/10_terminal_qc_verification.sh`
Adhere strictly to the structure and schema defined in this blueprint.
