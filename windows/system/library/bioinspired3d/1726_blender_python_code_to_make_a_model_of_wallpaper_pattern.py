# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_make_a_model_of_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to make a model of wallpaper pattern

import bpy
import math

# Step 1: Clear the Scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with distinct names
red_material = bpy.data.materials.new(name="RedMaterial")
red_material.diffuse_color = (0.8, 0.1, 0.1, 1)
green_material = bpy.data.materials.new(name="GreenMaterial")
green_material.diffuse_color = (0.1, 0.8, 0.1, 1)

# Step 2: Generate grid of cubes with alternating colors
for row in range(5):
    for col in range(5):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(row, col, 0))
        current_cube = bpy.context.object
        current_cube.name = f"Cube_{row}_{col}"
        material_to_use = red_material if (row + col) % 2 == 0 else green_material
        current_cube.data.materials.append(material_to_use)


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
