# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_constructs_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that constructs puzzle cube.

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Cube color palette
cube_colors = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0.5, 0, 1),  # Orange
    (1, 1, 1, 1)   # White
]

# Function to create a colored cube at a specific position
def create_cube(x, y, z, color_index):
    bpy.ops.mesh.primitive_cube_add(size=0.9, location=(x, y, z))
    current_cube = bpy.context.object
    current_cube.name = f"Cube_{x}_{y}_{z}"
    new_material = bpy.data.materials.new(name=f"Material_{x}_{y}_{z}")
    new_material.diffuse_color = cube_colors[color_index]
    current_cube.data.materials.append(new_material)

# Generate cubes in a 3x3x3 formation
for i in range(3):
    for j in range(3):
        for k in range(3):
            create_cube(i * 1.0, j * 1.0, k * 1.0, (i + j + k) % len(cube_colors))


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
