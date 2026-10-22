# Apple macOS & iOS SwiftUI Architecture
<!-- Keyword: swiftui_macos -->

## 🍎 SwiftUI Invariants
1. **Adaptive Stacks:** Use `ViewThatFits` and responsive `LazyVGrid` for dynamic window resizing.
2. **System Materials:** Use `.background(.ultraThinMaterial)` with vibrant SF Symbols for native macOS feel.
3. **Accessibility:** Apply `.accessibilityLabel()` and `.accessibilityHint()` to custom controls.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE CODE BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before implementing SwiftUI views, you MUST inspect the official reference template via `view_file`:
`skills/ui_ux_pro_max/example/12_swiftui_adaptive_view.swift`
Follow the native state handling and window padding defined in this blueprint.
