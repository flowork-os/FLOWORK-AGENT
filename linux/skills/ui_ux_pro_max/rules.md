# UI/UX Pro Max Operational Rules & Invariants

1. **Anti-AI-Slop Invariant:** Never use unprompted purple-to-blue gradients, cards-nested-in-cards, or washed-out gray-on-gray low-contrast text.
2. **WCAG AA Contrast Mandate:** Computed text-to-background contrast MUST exceed 4.5:1 for body copy and 3:1 for large text and icons.
3. **Semantic Token Rule:** Never embed raw hex colors in component styling; always bind surfaces to semantic tokens (`var(--primary)`, `var(--card)`).
4. **Interactive States Requirement:** Every clickable control MUST declare explicit `:hover`, `:active`, `:focus-visible`, and `:disabled` styles.
5. **No Outline Removal:** Never set `outline: none` without providing an accessible, high-contrast `focus-visible` replacement ring.
6. **Touch Target Dimensions:** Interactive elements MUST meet minimum touch bounds: 44x44pt on iOS/mobile and 32x32px on desktop.
7. **Spatial Cadence Scale:** Spacing MUST follow the 4px base scale (4, 8, 12, 16, 24, 32, 48, 64px); avoid random one-off margins.
8. **CLS Mitigation:** All image, video, and media tags MUST declare explicit dimensions or aspect ratios to guarantee Cumulative Layout Shift < 0.1.
9. **Typography Hierarchy:** Never skip heading levels (`h1` -> `h2` -> `h3`). Pair display headings with legible body typefaces.
10. **Motion Accessibility:** All CSS animations and transitions MUST respect `@media (prefers-reduced-motion: reduce)`.
