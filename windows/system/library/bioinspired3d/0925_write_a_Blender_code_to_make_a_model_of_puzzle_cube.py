# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_to_make_a_model_of_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code to make a model of puzzle cube.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a list of colors
color_list = [
    (1, 0, 0, 1),  # Red Color
    (0, 1, 0, 1),  # Green Color
    (0, 0, 1, 1),  # Blue Color
    (1, 1, 0, 1),  # Yellow Color
    (1, 0.5, 0, 1),  # Orange Color
    (1, 1, 1, 1)   # White Color
]

# Class to manage cube creation
class CubeManager:
    def __init__(self, size, gap):
        self.size = size
        self.gap = gap

    def add_cube(self, position, color):
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=position)
        cube = bpy.context.object
        cube.name = f"Cube_{position}"
        material = bpy.data.materials.new(name=f"Material_{position}")
        material.diffuse_color = color
        cube.data.materials.append(material)

# Instantiate CubeManager
cube_creator = CubeManager(size=1, gap=0.1)

# Create a 3x3x3 arrangement of cubes
for x in range(3):
    for y in range(3):
        for z in range(3):
            cube_creator.add_cube((x * (cube_creator.size + cube_creator.gap), y * (cube_creator.size + cube_creator.gap), z * (cube_creator.size + cube_creator.gap)), color_list[(x + y + z) % len(color_list)])


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
