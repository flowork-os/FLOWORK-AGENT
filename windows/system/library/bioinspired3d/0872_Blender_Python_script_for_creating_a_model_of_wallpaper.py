# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_creating_a_model_of_wallpaper" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for creating a model of wallpaper.

import bpy
import random

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

class ColorManager:
    @staticmethod
    def get_random_color():
        colors = [
            (1, 0, 0, 1),  # Red
            (0, 1, 0, 1),  # Green
            (0, 0, 1, 1),  # Blue
            (1, 1, 0, 1),  # Yellow
            (1, 0.5, 0, 1),  # Orange
            (1, 1, 1, 1)   # White
        ]
        return random.choice(colors)

# Create a 5x5 grid of toruses
for row in range(5):
    for col in range(5):
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(row, col, 0))
        new_torus = bpy.context.object
        new_torus.name = f"Torus_{row}_{col}"
        chosen_color = ColorManager.get_random_color()
        new_material = bpy.data.materials.new(name=f"Material_{row}_{col}")
        new_material.diffuse_color = chosen_color
        new_torus.data.materials.append(new_material)


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
