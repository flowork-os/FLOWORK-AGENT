# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_makes_chess_set" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that makes chess set

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_black = bpy.data.materials.new(name="Black Material")
mat_black.diffuse_color = (0.1, 0.1, 0.1, 1)
mat_white = bpy.data.materials.new(name="White Material")
mat_white.diffuse_color = (0.9, 0.9, 0.9, 1)

size_of_board = 8
square_length = 1
for row in range(size_of_board):
    for column in range(size_of_board):
        bpy.ops.mesh.primitive_plane_add(size=square_length, location=(row * square_length, column * square_length, 0))
        plane_object = bpy.context.object
        plane_object.data.materials.append(mat_white if (row + column) % 2 == 0 else mat_black)

def create_chess_piece(piece_type, position):
    if piece_type == 'pawn':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(position[0], position[1], position[2] + 0.2))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(position[0], position[1], position[2]))
    elif piece_type == 'rook':
        bpy.ops.mesh.primitive_cube_add(size=0.4, location=(position[0], position[1], position[2] + 0.2))
    elif piece_type == 'knight':
        bpy.ops.mesh.primitive_cone_add(radius1=0.2, depth=0.4, location=(position[0], position[1], position[2] + 0.2))
    elif piece_type == 'bishop':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(position[0], position[1], position[2] + 0.2))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(position[0], position[1], position[2]))
    elif piece_type == 'queen':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(position[0], position[1], position[2] + 0.3))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.6, location=(position[0], position[1], position[2]))
    elif piece_type == 'king':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(position[0], position[1], position[2] + 0.3))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.6, location=(position[0], position[1], position[2]))

for i in range(size_of_board):
    create_chess_piece('pawn', (i * square_length, 1 * square_length, 0))
    create_chess_piece('pawn', (i * square_length, 6 * square_length, 0))

create_chess_piece('rook', (0 * square_length, 0 * square_length, 0))
create_chess_piece('rook', (7 * square_length, 0 * square_length, 0))
create_chess_piece('rook', (0 * square_length, 7 * square_length, 0))
create_chess_piece('rook', (7 * square_length, 7 * square_length, 0))

create_chess_piece('knight', (1 * square_length, 0 * square_length, 0))
create_chess_piece('knight', (6 * square_length, 0 * square_length, 0))
create_chess_piece('knight', (1 * square_length, 7 * square_length, 0))
create_chess_piece('knight', (6 * square_length, 7 * square_length, 0))

create_chess_piece('bishop', (2 * square_length, 0 * square_length, 0))
create_chess_piece('bishop', (5 * square_length, 0 * square_length, 0))
create_chess_piece('bishop', (2 * square_length, 7 * square_length, 0))
create_chess_piece('bishop', (5 * square_length, 7 * square_length, 0))

create_chess_piece('queen', (3 * square_length, 0 * square_length, 0))
create_chess_piece('queen', (3 * square_length, 7 * square_length, 0))

create_chess_piece('king', (4 * square_length, 0 * square_length, 0))
create_chess_piece('king', (4 * square_length, 7 * square_length, 0))


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
