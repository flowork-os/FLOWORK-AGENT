# Scalable Vector Graphics & Iconography
<!-- Keyword: svg_vector -->

## 📐 Vector Iconography Invariants
1. **Crisp ViewBoxes:** Standardize icon dimensions on a 24x24 pixel grid (`viewBox="0 0 24 24"`).
2. **CurrentColor Inheritance:** Set `fill="none"` and `stroke="currentColor"` so SVGs naturally inherit parent typography colors.
3. **No Embedded Bitmaps:** Never embed base64 PNGs or raster assets inside SVG files.

### 🛠️ Mandatory Implementation Blueprint:
DO NOT IMPROVISE CODE BEFORE INSPECTING THE OFFICIAL BLUEPRINT!
Before implementing vector icons, you MUST inspect the official reference template via `view_file`:
`skills/ui_ux_pro_max/example/14_crisp_icon_set.svg`
Use the clean vector paths and stroke inheritance rules defined in this blueprint.
