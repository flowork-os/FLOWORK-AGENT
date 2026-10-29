# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_generates_puzzle_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that generates puzzle cube

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a selection of colors
color_options = [
    (1, 0, 0, 1),  # Red
    (0, 1, 0, 1),  # Green
    (0, 0, 1, 1),  # Blue
    (1, 1, 0, 1),  # Yellow
    (1, 0.5, 0, 1),  # Orange
    (1, 1, 1, 1)   # White
]

# Class to represent a colored cube
class ColoredCube:
    def __init__(self, position, color):
        bpy.ops.mesh.primitive_cube_add(size=1, location=position)
        self.cube = bpy.context.object
        self.cube.name = f'Cube_{position}'
        mat = bpy.data.materials.new(name=f'Material_{position}')
        mat.diffuse_color = color
        self.cube.data.materials.append(mat)

# Create the cubes in a 3D grid
spacing = 1.1
for x in range(3):
    for y in range(3):
        for z in range(3):
            position = (x * spacing, y * spacing, z * spacing)
            color = color_options[(x + y + z) % len(color_options)]
            ColoredCube(position, color)


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
