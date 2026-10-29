# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_creates_chess_board" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that creates chess board

import bpy

# Clear existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the chess pieces
material_black = bpy.data.materials.new(name="Material Black")
material_black.diffuse_color = (0, 0, 0, 1)
material_white = bpy.data.materials.new(name="Material White")
material_white.diffuse_color = (1, 1, 1, 1)

# Define board dimensions
board_dimension = 18
individual_square_size = board_dimension / 8

# Generate the chessboard
for row in range(8):
    for col in range(8):
        bpy.ops.mesh.primitive_plane_add(size=individual_square_size, location=(col * individual_square_size - board_dimension / 2 + individual_square_size / 2, row * individual_square_size - board_dimension / 2 + individual_square_size / 2, 0))
        square_plane = bpy.context.object
        square_plane.data.materials.append(material_white if (row + col) % 2 == 0 else material_black)

# Function to create a chess piece
def add_chess_piece(piece_name, piece_location, piece_material):
    bpy.ops.mesh.primitive_cylinder_add(radius=individual_square_size / 4, depth=individual_square_size / 2, location=piece_location)
    chess_piece = bpy.context.object
    chess_piece.name = piece_name
    chess_piece.data.materials.append(piece_material)

# Create pawns
for index in range(8):
    add_chess_piece(f"White Pawn {index + 1}", (index * individual_square_size - board_dimension / 2 + individual_square_size / 2, -board_dimension / 2 + 1.5 * individual_square_size, individual_square_size / 4), material_white)
    add_chess_piece(f"Black Pawn {index + 1}", (index * individual_square_size - board_dimension / 2 + individual_square_size / 2, board_dimension / 2 - 1.5 * individual_square_size, individual_square_size / 4), material_black)

# Create rooks
add_chess_piece("White Rook 1", (-board_dimension / 2 + individual_square_size / 2, -board_dimension / 2 + individual_square_size / 2, individual_square_size / 4), material_white)
add_chess_piece("White Rook 2", (board_dimension / 2 - individual_square_size / 2, -board_dimension / 2 + individual_square_size / 2, individual_square_size / 4), material_white)
add_chess_piece("Black Rook 1", (-board_dimension / 2 + individual_square_size / 2, board_dimension / 2 - individual_square_size / 2, individual_square_size / 4), material_black)
add_chess_piece("Black Rook 2", (board_dimension / 2 - individual_square_size / 2, board_dimension / 2 - individual_square_size / 2, individual_square_size / 4), material_black)

# Create knights
add_chess_piece("White Knight 1", (-board_dimension / 2 + 1.5 * individual_square_size, -board_dimension / 2 + individual_square_size / 2, individual_square_size / 4), material_white)
add_chess_piece("White Knight 2", (board_dimension / 2 - 1.5 * individual_square_size, -board_dimension / 2 + individual_square_size / 2, individual_square_size / 4), material_white)
add_chess_piece("Black Knight 1", (-board_dimension / 2 + 1.5 * individual_square_size, board_dimension / 2 - individual_square_size / 2, individual_square_size / 4), material_black)
add_chess_piece("Black Knight 2", (board_dimension / 2 - 1.5 * individual_square_size, board_dimension / 2 - individual_square_size / 2, individual_square_size / 4), material_black)

# Create bishops
add_chess_piece("White Bishop 1", (-board_dimension / 2 + 2.5 * individual_square_size, -board_dimension / 2 + individual_square_size / 2, individual_square_size / 4), material_white)
add_chess_piece("White Bishop 2", (board_dimension / 2 - 2.5 * individual_square_size, -board_dimension / 2 + individual_square_size / 2, individual_square_size / 4), material_white)
add_chess_piece("Black Bishop 1", (-board_dimension / 2 + 2.5 * individual_square_size, board_dimension / 2 - individual_square_size / 2, individual_square_size / 4), material_black)
add_chess_piece("Black Bishop 2", (board_dimension / 2 - 2.5 * individual_square_size, board_dimension / 2 - individual_square_size / 2, individual_square_size / 4), material_black)

# Create queens
add_chess_piece("White Queen", (-board_dimension / 2 + 3.5 * individual_square_size, -board_dimension / 2 + individual_square_size / 2, individual_square_size / 4), material_white)
add_chess_piece("Black Queen", (-board_dimension / 2 + 3.5 * individual_square_size, board_dimension / 2 - individual_square_size / 2, individual_square_size / 4), material_black)

# Create kings
add_chess_piece("White King", (-board_dimension / 2 + 4.5 * individual_square_size, -board_dimension / 2 + individual_square_size / 2, individual_square_size / 4), material_white)
add_chess_piece("Black King", (-board_dimension / 2 + 4.5 * individual_square_size, board_dimension / 2 - individual_square_size / 2, individual_square_size / 4), material_black)


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
