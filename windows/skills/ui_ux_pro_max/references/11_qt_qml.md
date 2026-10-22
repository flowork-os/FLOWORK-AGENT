# Qt 6 & QML Desktop GUI Architecture
<!-- Keyword: qt_qml -->

## 🐧 Desktop QML Invariants
1. **Declarative Layouts:** Use `ColumnLayout` and `RowLayout` from `QtQuick.Layouts`. Avoid hardcoded absolute pixel coordinates (`x: 120, y: 350`).
2. **Theme Binding:** Bind colors to a centralized `Theme.qml` singleton mapping system tokens.
3. **C++ Bridge:** Keep heavy computational processing in C++ `QObject` models; keep QML purely visual.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE CODE BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before implementing Qt/QML views, you MUST inspect the official reference template via `view_file`:
`skills/ui_ux_pro_max/example/11_qt_desktop_panel.qml`
Use the declarative layout properties and margins demonstrated in this blueprint.
