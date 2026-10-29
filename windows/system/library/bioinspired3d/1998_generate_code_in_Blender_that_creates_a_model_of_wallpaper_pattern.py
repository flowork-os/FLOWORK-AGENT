# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_code_in_Blender_that_creates_a_model_of_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate code in Blender that creates a model of wallpaper pattern.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

hex_color_material = bpy.data.materials.new(name='HexColorMaterial')
hex_color_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Gray shade

def add_hexagon(x_pos, y_pos):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=1, fill_type='NGON', location=(x_pos, y_pos, 0))
    hex_shape = bpy.context.object
    hex_shape.data.materials.append(hex_color_material)

grid_rows = 5
grid_cols = 5
for row in range(grid_rows):
    for col in range(grid_cols):
        x_position = col * 1.5
        y_position = row * math.sqrt(3)
        if col % 2 == 1:
            y_position += math.sqrt(3) / 2
        add_hexagon(x_position, y_position)


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
