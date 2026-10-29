# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_to_make_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script to make puzzle cube.

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define cube colors
cube_colors = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0.5, 0, 1),  # Orange
    (1, 1, 1, 1)   # White
]

# Class to handle cube creation
class CubeGenerator:
    def __init__(self, size, gap):
        self.size = size
        self.gap = gap

    def add_cube(self, position, color):
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=position)
        cube = bpy.context.object
        mat = bpy.data.materials.new(name='CubeMaterial')
        mat.diffuse_color = color
        cube.data.materials.append(mat)

# Initialize cube generator
generator = CubeGenerator(1, 0.1)

# Create a 3D grid of cubes
for x in range(3):
    for y in range(3):
        for z in range(3):
            position = (x * (generator.size + generator.gap), y * (generator.size + generator.gap), z * (generator.size + generator.gap))
            color_choice = cube_colors[(x + y + z) % len(cube_colors)]
            generator.add_cube(position, color_choice)


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
