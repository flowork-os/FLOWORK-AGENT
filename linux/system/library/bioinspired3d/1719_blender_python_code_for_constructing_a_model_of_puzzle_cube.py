# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_constructing_a_model_of_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for constructing a model of puzzle cube

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Color palette for cubes
palette = [
    (1, 0, 0, 1),  # Bright Red
    (0, 1, 0, 1),  # Bright Green
    (0, 0, 1, 1),  # Bright Blue
    (1, 1, 0, 1),  # Bright Yellow
    (1, 0.5, 0, 1),  # Bright Orange
    (1, 1, 1, 1)   # Bright White
]

# Function to create cubes with materials
def create_colored_cube(position, size, color):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    material = bpy.data.materials.new(name='Material')
    material.diffuse_color = color
    cube.data.materials.append(material)
    return cube

# Generate cubes in a 3x3x3 grid
cube_dimension = 1
spacing = 0.1
for i in range(3):
    for j in range(3):
        for k in range(3):
            loc = (i * (cube_dimension + spacing), j * (cube_dimension + spacing), k * (cube_dimension + spacing))
            color_index = (i + j + k) % len(palette)
            create_colored_cube(loc, cube_dimension, palette[color_index])


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
