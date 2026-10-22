# WCAG AA Accessibility & Contrast Invariants
<!-- Keyword: wcag_contrast -->

## 👁️ Accessibility Invariants
1. **Contrast Ratio:** Minimum 4.5:1 for standard body copy; minimum 3.0:1 for large headings (>=18pt or bold >=14pt) and UI component boundaries.
2. **Focus Visibility:** Never set `outline: none` or `outline: 0` without providing a high-contrast replacement `:focus-visible` ring (minimum 2px solid with 2px offset).
3. **Screen Readers:** All non-text content (`<img>`, icons) must have descriptive `alt` text or `aria-label`. Decorative elements must have `aria-hidden="true"`.
4. **Touch Targets:** Minimum 44x44 CSS pixels on touch devices; 32x32 CSS pixels on desktop.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE CODE BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before implementing interactive styles or focus states, you MUST inspect the official reference template via `view_file`:
`skills/ui_ux_pro_max/example/04_wcag_accessible_button.html`
Apply the exact focus offset rings and contrast values shown in this blueprint.
