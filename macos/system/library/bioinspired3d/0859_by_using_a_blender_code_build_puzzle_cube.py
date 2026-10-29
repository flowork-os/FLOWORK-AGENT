# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_blender_code_build_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a blender code build puzzle cube.

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Color definitions for the cubes
palette = [
    (1, 0, 0, 1),  # Bright Red
    (0, 1, 0, 1),  # Vivid Green
    (0, 0, 1, 1),  # Deep Blue
    (1, 1, 0, 1),  # Bright Yellow
    (1, 0.5, 0, 1),  # Lively Orange
    (1, 1, 1, 1)   # Pure White
]

# Function to create a cube with a specific color

def create_colored_cube(position, size, color):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube_object = bpy.context.object
    material = bpy.data.materials.new(name=f"Material_{position}")
    material.diffuse_color = color
    cube_object.data.materials.append(material)
    cube_object.name = f"Cube_{position[0]}_{position[1]}_{position[2]}"

# Cube dimensions and spacing
cube_dimension = 0.95
spacing = 0.05

# Create the cubes in a 3x3x3 arrangement
for x in range(3):
    for y in range(3):
        for z in range(3):
            create_colored_cube((x * (cube_dimension + spacing), y * (cube_dimension + spacing), z * (cube_dimension + spacing)), cube_dimension, palette[(x + y + z) % len(palette)])


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
