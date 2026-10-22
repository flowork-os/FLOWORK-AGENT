# Frontend Contract & UI Component SOP

## 1. Role Mandate & Core Standard
The Frontend Engineer owns client interfaces, state management, and user interaction. All views must bind strictly to backend contracts and conform to WCAG AA accessibility standards.

## 2. Mandatory UI Invariants
1. **Tri-State Completeness:** Every data-dependent component must implement explicit Loading, Error (retryable), and Empty states.
2. **Strict Semantic Tokens:** Bind colors, borders, and typography to semantic CSS custom properties; no hardcoded styling.
3. **Responsive Boundaries:** Flexible layout scaling across viewports with zero horizontal overflow leaks.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE DELIVERABLES BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before creating or modifying deliverables, you MUST inspect the specific example blueprint:
`view_file` -> `skills/software_company_sop/example/06_frontend_state_interface.ts`
Adhere strictly to the structure and schema defined in this blueprint.
