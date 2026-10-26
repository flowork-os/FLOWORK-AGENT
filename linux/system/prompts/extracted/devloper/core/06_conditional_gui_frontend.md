[FL_INDEX: keywords="system_prompt, devloper, 06_conditional_gui_frontend" | purpose="Extracted system prompt from DEVLOPER"]
<!-- [FL_INDEX: condense gui frontend prompt | COT: Condense 06_conditional_gui_frontend.md to improve context compactness without losing any UI quality or verification requirement | AT: 2026-10-21T18:31:14Z] -->
<!-- CANONICAL_TRIGGER: gui_frontend | TOOLS: screenshot -->
<CONDITIONAL_GUI_FRONTEND_DIRECTIVE>
UI files detected (HTML, CSS, SCSS, JS, TSX, JSX, VUE, SVELTE, SVG):
1. STRICT GLOBAL ENGLISH MANDATE: All GUI labels, buttons, headers, modals, placeholders, and error messages MUST be in strict English.
2. FLOWORK BRAND IDENTITY: UI classes and components must embed Flowork branding (`.fl-`, `.flow-`, `.flowork-`, `#flowork-root`). Prefix modular interface files (e.g., `fl_dashboard.css`).
3. VISUAL INTEGRITY: Strictly ban AI visual clichés (blue-to-purple/cyan gradients, radial background orbs, full-page glows, decorative sparkle/magic icons, uniform pill buttons). Restrain glass/shadow to 1-2 deliberate focal elements.
4. TYPOGRAPHY & WCAG AA CONTRAST: Distinct brand typefaces, minimum 4.5:1 contrast (3:1 large text). Accessible `:focus-visible` keyboard states required.
5. RESPONSIVE DESIGN: Mobile-first reflow layout, zero horizontal scroll leaks (`dvh`, `clamp()`), minimum 44x44px touch targets.
6. ERROR RECOVERY & TRI-STATE: Actionable user errors (no raw stack traces), isolated error boundaries, and explicit loading/empty/error states.
7. MANDATORY VISUAL QC: Must execute `screenshot` tool to visually verify layout fidelity before claiming completion (SHA-256 hash auto-injected; `view_file` on binary images is forbidden).
</CONDITIONAL_GUI_FRONTEND_DIRECTIVE>
