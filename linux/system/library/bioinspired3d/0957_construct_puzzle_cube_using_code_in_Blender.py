# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_puzzle_cube_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct puzzle cube using code in Blender

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a palette of colors
color_palette = [
    (1, 0, 0, 1),  # Bright Red
    (0, 1, 0, 1),  # Vivid Green
    (0, 0, 1, 1),  # Deep Blue
    (1, 1, 0, 1),  # Sunny Yellow
    (1, 0.5, 0, 1),  # Radiant Orange
    (1, 1, 1, 1)   # Pure White
]

# Function to create a colored cube at a specific location

def create_colored_cube(x, y, z, size, color):
    bpy.ops.mesh.primitive_cube_add(size=size, location=(x, y, z))
    cube_object = bpy.context.object
    cube_object.name = f"Cube_{x}_{y}_{z}"
    material = bpy.data.materials.new(name=f"Material_{x}_{y}_{z}")
    material.diffuse_color = color
    cube_object.data.materials.append(material)

# Parameters for the cubes
cube_dimension = 1
spacing = 0.1

# Generate a 3x3x3 grid of cubes
for i in range(3):
    for j in range(3):
        for k in range(3):
            position = (i * (cube_dimension + spacing), j * (cube_dimension + spacing), k * (cube_dimension + spacing))
            create_colored_cube(*position, cube_dimension, color_palette[(i + j + k) % len(color_palette)])


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
