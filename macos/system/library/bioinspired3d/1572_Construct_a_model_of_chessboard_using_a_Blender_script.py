# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_chessboard_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of chessboard using a Blender script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_black = bpy.data.materials.new(name='Deep Black')
mat_black.diffuse_color = (0, 0, 0, 1)
mat_white = bpy.data.materials.new(name='Bright White')
mat_white.diffuse_color = (1, 1, 1, 1)

def setup_chessboard():
    square_length = 1
    for row in range(8):
        for col in range(8):
            bpy.ops.mesh.primitive_plane_add(size=square_length, location=(col * square_length, row * square_length, 0))
            square = bpy.context.object
            square.name = f'Square_{row}_{col}'
            square.data.materials.append(mat_white if (row + col) % 2 == 0 else mat_black)

setup_chessboard()


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
