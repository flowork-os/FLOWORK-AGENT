# GTK 4 & Libadwaita Linux Desktop Architecture
<!-- Keyword: gtk_linux -->

## 🐧 GTK 4 Invariants
1. **Libadwaita Widgets:** Use `AdwHeaderBar`, `AdwPreferencesGroup`, and `AdwActionRow` for modern GNOME design.
2. **Dynamic Dark Style:** Support `AdwStyleManager` for seamless light/dark mode transitions.
3. **Responsive Clamp:** Wrap forms in `AdwClamp` to restrict maximum line widths on wide monitors.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE CODE BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before implementing GTK Linux views, you MUST inspect the official reference template via `view_file`:
`skills/ui_ux_pro_max/example/15_gtk_adwaita_window.py`
Adhere strictly to the Libadwaita preferences hierarchy demonstrated in this blueprint.
