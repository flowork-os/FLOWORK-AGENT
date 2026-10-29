# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_makes_a_model_of_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that makes a model of wallpaper pattern.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

hex_material = bpy.data.materials.new(name='HexMaterial')
hex_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Medium gray color

class HexagonGrid:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def create_hexagon(self, location):
        bpy.ops.mesh.primitive_circle_add(vertices=6, radius=1, fill_type='NGON', location=location)
        hex_obj = bpy.context.object
        hex_obj.data.materials.append(hex_material)

    def build_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                x = c * 1.5
                y = r * math.sqrt(3)
                if c % 2 == 1:
                    y += math.sqrt(3) / 2
                self.create_hexagon((x, y, 0))

hex_grid = HexagonGrid(5, 5)
hex_grid.build_grid()


# --- 3DCodeVerse geo variant: neutralize materials (auto-derived, do not edit) ---
import bpy as _bpy_geo
_geo_mat = _bpy_geo.data.materials.get("geo_neutral") or _bpy_geo.data.materials.new("geo_neutral")
try:
    _geo_mat.use_nodes = False
except Exception:
    pass
try:
    _geo_mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
except Exception:
    pass
for _geo_obj in list(_bpy_geo.data.objects):
    if _geo_obj.type == "MESH" and _geo_obj.data is not None:
        try:
            _geo_obj.data.materials.clear()
            _geo_obj.data.materials.append(_geo_mat)
        except Exception:
            pass
# --- end geo variant ---
