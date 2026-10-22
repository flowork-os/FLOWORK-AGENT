# Bento Grid Topology & Asymmetric Layouts
<!-- Keyword: bento_grid -->

## 🍱 Bento Grid Architecture
1. **Grid Base:** 12-column grid (`grid-template-columns: repeat(12, 1fr)`) with explicit column spans (`span 4`, `span 8`, `span 12`).
2. **Container Queries:** Use `@container (max-width: ...)` to reflow internal card content without relying exclusively on global viewport breakpoints.
3. **Card Hygiene:** Cards must have subtle borders (`1px solid var(--border)`), intentional padding (`var(--space-6)`), and no nested cards.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE CODE BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before implementing Bento Grid layouts, you MUST inspect the official reference template via `view_file`:
`skills/ui_ux_pro_max/example/08_bento_grid_layout.html`
Follow the exact 12-column span hierarchy and responsive collapse rules in this blueprint.
