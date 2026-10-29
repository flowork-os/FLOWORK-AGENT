# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_generating_a_model_of_wallpaper" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for generating a model of wallpaper.

import bpy
import random

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_colored_torus(x, y):
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(x, y, 0))
    torus = bpy.context.object
    torus.name = f"Torus_{x}_{y}"
    color_choice = random.choice([
        (1, 0, 0, 1),
        (0, 1, 0, 1),
        (0, 0, 1, 1),
        (1, 1, 0, 1),
        (1, 0.5, 0, 1),
        (1, 1, 1, 1)
    ])
    mat = bpy.data.materials.new(name=f"Material_{x}_{y}")
    mat.diffuse_color = color_choice
    torus.data.materials.append(mat)

for i in range(5):
    for j in range(5):
        create_colored_torus(i, j)


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
