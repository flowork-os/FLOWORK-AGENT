# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_makes_wallpaper" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that makes wallpaper.

import bpy
import random

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a palette of colors
color_palette = [
    (1, 0, 0, 1),  # Bright Red
    (0, 1, 0, 1),  # Lush Green
    (0, 0, 1, 1),  # Deep Blue
    (1, 1, 0, 1),  # Vivid Yellow
    (1, 0.5, 0, 1),  # Bright Orange
    (1, 1, 1, 1)   # Pure White
]

# Generate a grid of toruses
for x in range(5):
    for y in range(5):
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(x, y, 0))
        torus = bpy.context.object
        torus.name = f"Torus_{x}_{y}"
        selected_color = random.choice(color_palette)
        material = bpy.data.materials.new(name=f"Material_{x}_{y}")
        material.diffuse_color = selected_color
        torus.data.materials.append(material)


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
