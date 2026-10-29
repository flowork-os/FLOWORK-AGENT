# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_make_a_model_of_chessboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to make a model of chessboard

import bpy

# Clear all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the chessboard
material_black = bpy.data.materials.new(name='Material_Black')
material_black.diffuse_color = (0, 0, 0, 1)
material_white = bpy.data.materials.new(name='Material_White')
material_white.diffuse_color = (1, 1, 1, 1)

# Function to create a square at a given position
def create_square(x, y, size, material):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(x, y, 0))
    square = bpy.context.object
    square.data.materials.append(material)

# Generate the chessboard
size_of_square = 1
size_of_board = 8 * size_of_square
for row in range(8):
    for col in range(8):
        x_pos = col * size_of_square - (size_of_board / 2) + (size_of_square / 2)
        y_pos = row * size_of_square - (size_of_board / 2) + (size_of_square / 2)
        mat = material_white if (row + col) % 2 == 0 else material_black
        create_square(x_pos, y_pos, size_of_square, mat)


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
