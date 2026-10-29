# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_puzzle_cube_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of puzzle cube using blender code

import bpy

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set of colors for the cubes
color_set = [
    (0.8, 0.1, 0.1, 1),  # Dark Red
    (0.1, 0.8, 0.1, 1),  # Dark Green
    (0.1, 0.1, 0.8, 1),  # Dark Blue
    (0.8, 0.8, 0.1, 1),  # Dark Yellow
    (0.8, 0.5, 0.1, 1),  # Dark Orange
    (0.9, 0.9, 0.9, 1)   # Light Gray
]

# Function to create a cube with a specific material

def create_cube_with_material(location, size, color):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube_object = bpy.context.object
    new_material = bpy.data.materials.new(name='CubeMaterial')
    new_material.diffuse_color = color
    cube_object.data.materials.append(new_material)

# Parameters for cube creation
cube_side_length = 1
spacing_between_cubes = 0.1

# Loop to create a 3D array of cubes
for i in range(3):
    for j in range(3):
        for k in range(3):
            cube_position = (i * (cube_side_length + spacing_between_cubes), j * (cube_side_length + spacing_between_cubes), k * (cube_side_length + spacing_between_cubes))
            selected_color = color_set[(i + j + k) % len(color_set)]
            create_cube_with_material(cube_position, cube_side_length, selected_color)


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
