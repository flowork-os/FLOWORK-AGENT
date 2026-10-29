# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_creates_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that creates puzzle cube.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a list of colors for the cubes
color_list = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0.5, 0, 1),  # Orange
    (1, 1, 1, 1)   # White
]

# Create a cube and assign a color to it
def add_cube_with_color(coords, color):
    bpy.ops.mesh.primitive_cube_add(size=0.9, location=coords)
    cube_obj = bpy.context.object
    cube_obj.name = f"Cube_{coords}"
    material = bpy.data.materials.new(name=f"Material_{coords}")
    material.diffuse_color = color
    cube_obj.data.materials.append(material)

# Loop through the positions to create a grid of cubes
for x in range(3):
    for y in range(3):
        for z in range(3):
            pos = (x * 1.0, y * 1.0, z * 1.0)
            add_cube_with_color(pos, color_list[(x + y + z) % len(color_list)])


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
