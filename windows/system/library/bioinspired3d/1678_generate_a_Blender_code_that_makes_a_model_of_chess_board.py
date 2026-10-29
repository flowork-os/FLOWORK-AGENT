# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_code_that_makes_a_model_of_chess_board" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender code that makes a model of chess board

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_black = bpy.data.materials.new(name="Dark")
mat_black.diffuse_color = (0, 0, 0, 1)
mat_white = bpy.data.materials.new(name="Light")
mat_white.diffuse_color = (1, 1, 1, 1)

total_size = 18
square_dim = total_size / 8

for i in range(8):
    for j in range(8):
        bpy.ops.mesh.primitive_plane_add(size=square_dim, location=(j * square_dim - total_size / 2 + square_dim / 2, i * square_dim - total_size / 2 + square_dim / 2, 0))
        current_square = bpy.context.object
        current_square.data.materials.append(mat_white if (i + j) % 2 == 0 else mat_black)

def place_piece(name, pos, color):
    bpy.ops.mesh.primitive_cylinder_add(radius=square_dim / 4, depth=square_dim / 2, location=pos)
    piece = bpy.context.object
    piece.name = name
    piece.data.materials.append(color)

for idx in range(8):
    place_piece(f"Pawn White {idx + 1}", (idx * square_dim - total_size / 2 + square_dim / 2, -total_size / 2 + 1.5 * square_dim, square_dim / 4), mat_white)
    place_piece(f"Pawn Black {idx + 1}", (idx * square_dim - total_size / 2 + square_dim / 2, total_size / 2 - 1.5 * square_dim, square_dim / 4), mat_black)

place_piece("Rook White 1", (-total_size / 2 + square_dim / 2, -total_size / 2 + square_dim / 2, square_dim / 4), mat_white)
place_piece("Rook White 2", (total_size / 2 - square_dim / 2, -total_size / 2 + square_dim / 2, square_dim / 4), mat_white)
place_piece("Rook Black 1", (-total_size / 2 + square_dim / 2, total_size / 2 - square_dim / 2, square_dim / 4), mat_black)
place_piece("Rook Black 2", (total_size / 2 - square_dim / 2, total_size / 2 - square_dim / 2, square_dim / 4), mat_black)

place_piece("Knight White 1", (-total_size / 2 + 1.5 * square_dim, -total_size / 2 + square_dim / 2, square_dim / 4), mat_white)
place_piece("Knight White 2", (total_size / 2 - 1.5 * square_dim, -total_size / 2 + square_dim / 2, square_dim / 4), mat_white)
place_piece("Knight Black 1", (-total_size / 2 + 1.5 * square_dim, total_size / 2 - square_dim / 2, square_dim / 4), mat_black)
place_piece("Knight Black 2", (total_size / 2 - 1.5 * square_dim, total_size / 2 - square_dim / 2, square_dim / 4), mat_black)

place_piece("Bishop White 1", (-total_size / 2 + 2.5 * square_dim, -total_size / 2 + square_dim / 2, square_dim / 4), mat_white)
place_piece("Bishop White 2", (total_size / 2 - 2.5 * square_dim, -total_size / 2 + square_dim / 2, square_dim / 4), mat_white)
place_piece("Bishop Black 1", (-total_size / 2 + 2.5 * square_dim, total_size / 2 - square_dim / 2, square_dim / 4), mat_black)
place_piece("Bishop Black 2", (total_size / 2 - 2.5 * square_dim, total_size / 2 - square_dim / 2, square_dim / 4), mat_black)

place_piece("Queen White", (-total_size / 2 + 3.5 * square_dim, -total_size / 2 + square_dim / 2, square_dim / 4), mat_white)
place_piece("Queen Black", (-total_size / 2 + 3.5 * square_dim, total_size / 2 - square_dim / 2, square_dim / 4), mat_black)

place_piece("King White", (-total_size / 2 + 4.5 * square_dim, -total_size / 2 + square_dim / 2, square_dim / 4), mat_white)
place_piece("King Black", (-total_size / 2 + 4.5 * square_dim, total_size / 2 - square_dim / 2, square_dim / 4), mat_black)


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
