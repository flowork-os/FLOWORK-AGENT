# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_script_make_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender script make puzzle cube

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Color definitions
color_options = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0.5, 0, 1),  # Orange
    (1, 1, 1, 1)   # White
]

# Initialize cube properties
size_of_cube = 1
spacing_between_cubes = 0.1

# Create a grid of cubes using a single function

def add_cube_grid():
    for i in range(3):
        for j in range(3):
            for k in range(3):
                location = (i * (size_of_cube + spacing_between_cubes), j * (size_of_cube + spacing_between_cubes), k * (size_of_cube + spacing_between_cubes))
                bpy.ops.mesh.primitive_cube_add(size=size_of_cube, location=location)
                cube_instance = bpy.context.object
                cube_instance.name = f"Cube_{i}_{j}_{k}"
                mat = bpy.data.materials.new(name=f"Material_{i}_{j}_{k}")
                mat.diffuse_color = color_options[(i + j + k) % len(color_options)]
                cube_instance.data.materials.append(mat)

# Execute the function to create the cubes
add_cube_grid()


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
