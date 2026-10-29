# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_creates_a_model_of_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that creates a model of wallpaper pattern.

import bpy

# Clear the scene of existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the circles
red_material = bpy.data.materials.new(name='Red Material')
red_material.diffuse_color = (0.8, 0.2, 0.2, 1)

# Function to create a torus at specified coordinates

def add_circle(x, y):
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(x, y, 0))
    torus = bpy.context.object
    torus.name = f'Circle_{x}_{y}'
    torus.data.materials.append(red_material)

# Generate interlocking circles
for row in range(5):
    for col in range(5):
        add_circle(row, col)


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
