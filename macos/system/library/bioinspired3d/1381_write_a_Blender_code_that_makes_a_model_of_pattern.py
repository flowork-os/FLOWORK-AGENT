# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_makes_a_model_of_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that makes a model of pattern

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material with a specific shade
shade_material = bpy.data.materials.new(name='ShadeMaterial')
shade_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Light gray color

# Function to add cubes in a grid

def add_cubes(size):
    for x in range(-size, size + 1):
        for y in range(-size, size + 1):
            bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, 0))
            current_cube = bpy.context.object
            current_cube.data.materials.append(shade_material)

# Create a grid of cubes
add_cubes(2)


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
