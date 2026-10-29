# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_creating_a_model_of_chessboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for creating a model of chessboard.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the chessboard
mat_black = bpy.data.materials.new(name='DarkMaterial')
mat_black.diffuse_color = (0, 0, 0, 1)
mat_white = bpy.data.materials.new(name='LightMaterial')
mat_white.diffuse_color = (1, 1, 1, 1)

# Function to add a square with a specific material

def add_square(x, y, size, material):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(x, y, 0))
    square_obj = bpy.context.object
    square_obj.data.materials.append(material)

# Create chessboard layout
board_square_size = 1
full_board_size = 8 * board_square_size
for i in range(8):
    for j in range(8):
        x_pos = j * board_square_size - (full_board_size / 2) + (board_square_size / 2)
        y_pos = i * board_square_size - (full_board_size / 2) + (board_square_size / 2)
        add_square(x_pos, y_pos, board_square_size, mat_white if (i + j) % 2 == 0 else mat_black)


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
