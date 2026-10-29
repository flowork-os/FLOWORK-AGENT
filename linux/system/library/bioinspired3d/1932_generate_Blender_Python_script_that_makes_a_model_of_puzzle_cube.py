# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_Python_script_that_makes_a_model_of_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender Python script that makes a model of puzzle cube

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set color variations
color_list = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0.5, 0, 1),  # Orange
    (1, 1, 1, 1)   # White
]

# Function to add a cube with a specific color
def add_cube(x, y, z, color):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    cube_object = bpy.context.object
    cube_object.name = f'Cube_{x}_{y}_{z}'
    material = bpy.data.materials.new(name=f'Material_{x}_{y}_{z}')
    material.diffuse_color = color
    cube_object.data.materials.append(material)

# Generate a 3x3x3 cube arrangement
for x in range(3):
    for y in range(3):
        for z in range(3):
            position_x = x * 1.1
            position_y = y * 1.1
            position_z = z * 1.1
            color_choice = color_list[(x + y + z) % len(color_list)]
            add_cube(position_x, position_y, position_z, color_choice)


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
