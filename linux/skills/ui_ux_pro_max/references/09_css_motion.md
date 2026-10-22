# Micro-Interactions & CSS Motion Curves
<!-- Keyword: css_motion -->

## 🌊 Motion Principles
1. **Physical Curves:** Never use linear transitions for UI states. Always use cubic-bezier deceleration: `cubic-bezier(0.33, 1, 0.68, 1)`.
2. **Duration Cap:** Micro-interactions (hover, focus, tab changes) must complete between 150ms and 250ms. Never exceed 300ms for routine UI interactions.
3. **Reduced Motion:** Always wrap animated transforms in `@media (prefers-reduced-motion: reduce)` to disable non-essential animations.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE CODE BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before implementing animations or transitions, you MUST inspect the official reference template via `view_file`:
`skills/ui_ux_pro_max/example/09_css_motion_curves.css`
Apply the exact cubic-bezier timing functions and accessibility media queries defined in this blueprint.
