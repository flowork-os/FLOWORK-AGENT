# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script__generate_a_model_of_chess_board" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script, generate a model of chess board.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_black = bpy.data.materials.new(name="Black Material")
mat_black.diffuse_color = (0, 0, 0, 1)
mat_white = bpy.data.materials.new(name="White Material")
mat_white.diffuse_color = (1, 1, 1, 1)

total_board_size = 18
size_of_square = total_board_size / 8

for row in range(8):
    for col in range(8):
        bpy.ops.mesh.primitive_plane_add(size=size_of_square, location=(col * size_of_square - total_board_size / 2 + size_of_square / 2, row * size_of_square - total_board_size / 2 + size_of_square / 2, 0))
        current_square = bpy.context.object
        current_square.data.materials.append(mat_white if (row + col) % 2 == 0 else mat_black)

def create_chess_piece(piece_title, piece_position, piece_color):
    bpy.ops.mesh.primitive_cylinder_add(radius=size_of_square / 4, depth=size_of_square / 2, location=piece_position)
    chess_piece = bpy.context.object
    chess_piece.name = piece_title
    chess_piece.data.materials.append(piece_color)

for index in range(8):
    create_chess_piece(f"Pawn White {index + 1}", (index * size_of_square - total_board_size / 2 + size_of_square / 2, -total_board_size / 2 + 1.5 * size_of_square, size_of_square / 4), mat_white)
    create_chess_piece(f"Pawn Black {index + 1}", (index * size_of_square - total_board_size / 2 + size_of_square / 2, total_board_size / 2 - 1.5 * size_of_square, size_of_square / 4), mat_black)

create_chess_piece("Rook White 1", (-total_board_size / 2 + size_of_square / 2, -total_board_size / 2 + size_of_square / 2, size_of_square / 4), mat_white)
create_chess_piece("Rook White 2", (total_board_size / 2 - size_of_square / 2, -total_board_size / 2 + size_of_square / 2, size_of_square / 4), mat_white)
create_chess_piece("Rook Black 1", (-total_board_size / 2 + size_of_square / 2, total_board_size / 2 - size_of_square / 2, size_of_square / 4), mat_black)
create_chess_piece("Rook Black 2", (total_board_size / 2 - size_of_square / 2, total_board_size / 2 - size_of_square / 2, size_of_square / 4), mat_black)

create_chess_piece("Knight White 1", (-total_board_size / 2 + 1.5 * size_of_square, -total_board_size / 2 + size_of_square / 2, size_of_square / 4), mat_white)
create_chess_piece("Knight White 2", (total_board_size / 2 - 1.5 * size_of_square, -total_board_size / 2 + size_of_square / 2, size_of_square / 4), mat_white)
create_chess_piece("Knight Black 1", (-total_board_size / 2 + 1.5 * size_of_square, total_board_size / 2 - size_of_square / 2, size_of_square / 4), mat_black)
create_chess_piece("Knight Black 2", (total_board_size / 2 - 1.5 * size_of_square, total_board_size / 2 - size_of_square / 2, size_of_square / 4), mat_black)

create_chess_piece("Bishop White 1", (-total_board_size / 2 + 2.5 * size_of_square, -total_board_size / 2 + size_of_square / 2, size_of_square / 4), mat_white)
create_chess_piece("Bishop White 2", (total_board_size / 2 - 2.5 * size_of_square, -total_board_size / 2 + size_of_square / 2, size_of_square / 4), mat_white)
create_chess_piece("Bishop Black 1", (-total_board_size / 2 + 2.5 * size_of_square, total_board_size / 2 - size_of_square / 2, size_of_square / 4), mat_black)
create_chess_piece("Bishop Black 2", (total_board_size / 2 - 2.5 * size_of_square, total_board_size / 2 - size_of_square / 2, size_of_square / 4), mat_black)

create_chess_piece("Queen White", (-total_board_size / 2 + 3.5 * size_of_square, -total_board_size / 2 + size_of_square / 2, size_of_square / 4), mat_white)
create_chess_piece("Queen Black", (-total_board_size / 2 + 3.5 * size_of_square, total_board_size / 2 - size_of_square / 2, size_of_square / 4), mat_black)

create_chess_piece("King White", (-total_board_size / 2 + 4.5 * size_of_square, -total_board_size / 2 + size_of_square / 2, size_of_square / 4), mat_white)
create_chess_piece("King Black", (-total_board_size / 2 + 4.5 * size_of_square, total_board_size / 2 - size_of_square / 2, size_of_square / 4), mat_black)


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
