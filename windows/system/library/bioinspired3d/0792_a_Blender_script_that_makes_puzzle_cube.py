# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_makes_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that makes puzzle cube

import bpy

# Clear existing mesh objects from the scene
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

# Function to create a cube at a specific location with a specific color
def create_colored_cube(x, y, z, color):
    bpy.ops.mesh.primitive_cube_add(size=0.9, location=(x, y, z))
    cube = bpy.context.object
    cube.name = f"Cube_{x}_{y}_{z}"
    material = bpy.data.materials.new(name=f"Material_{x}_{y}_{z}")
    material.diffuse_color = color
    cube.data.materials.append(material)

# Generate the cubes in a 3x3x3 grid
spacing = 0.1
for i in range(3):
    for j in range(3):
        for k in range(3):
            create_colored_cube(i * (0.9 + spacing), j * (0.9 + spacing), k * (0.9 + spacing), palette[(i + j + k) % len(palette)])


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
