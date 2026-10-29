# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_creates_chessboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that creates chessboard

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define colors for the chessboard
black_material = bpy.data.materials.new(name='Black Material')
black_material.diffuse_color = (0, 0, 0, 1)
white_material = bpy.data.materials.new(name='White Material')
white_material.diffuse_color = (1, 1, 1, 1)

# Create the chessboard using object-oriented approach
class Chessboard:
    def __init__(self, size):
        self.size = size

    def add_square(self, x, y, material):
        bpy.ops.mesh.primitive_plane_add(size=self.size, location=(x, y, 0))
        square = bpy.context.object
        square.data.materials.append(material)

# Instantiate the chessboard
board = Chessboard(1)
for row in range(8):
    for col in range(8):
        mat = white_material if (row + col) % 2 == 0 else black_material
        board.add_square(col, row, mat)


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
