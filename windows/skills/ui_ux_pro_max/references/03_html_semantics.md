# HTML5 Semantics & Landmark Architecture
<!-- Keyword: html_semantics -->

## 🌐 Semantic Landmarks
1. **Zero Div Soup:** Never construct pages entirely from nested `<div>` tags. Use `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<aside>`, and `<footer>`.
2. **Heading Cadence:** Maintain strict heading order (`h1` -> `h2` -> `h3`). Never skip heading levels for visual styling.
3. **Interactive Elements:** Always use native `<button>` for clickable actions and `<a>` for navigational URLs. Never attach `onClick` handlers to non-interactive `<div>` or `<span>` without ARIA roles.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE CODE BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before creating HTML markup, you MUST inspect the official reference template via `view_file`:
`skills/ui_ux_pro_max/example/03_html_landmarks.html`
Structure all document landmarks in exact accordance with this blueprint.
