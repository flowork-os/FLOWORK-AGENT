# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_code_that_creates_a_model_of_chess_game" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender code that creates a model of chess game

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a square

def create_square(position, name):
    bpy.ops.mesh.primitive_plane_add(size=1, location=position)
    square = bpy.context.object
    square.name = name
    return square

# Create the chessboard
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
board = bpy.context.object
board.name = 'Chess Board'

# Generate squares on the board
for row in range(8):
    for col in range(8):
        square_position = (row - 3.5, col - 3.5, 0.01)
        square = create_square(square_position, f'Square_{row}_{col}')
        material_name = 'White Square' if (row + col) % 2 == 0 else 'Black Square'
        square_material = bpy.data.materials.new(name=material_name)
        square_material.diffuse_color = (1, 1, 1, 1) if material_name == 'White Square' else (0, 0, 0, 1)
        square.data.materials.append(square_material)

# Function to create a chess piece

def add_piece(piece_name, piece_location, piece_color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=piece_location)
    piece = bpy.context.object
    piece.name = piece_name
    material = bpy.data.materials.new(name=f'{piece_name} Material')
    material.diffuse_color = piece_color
    piece.data.materials.append(material)

# Colors for pieces
white_color = (1, 1, 1, 1)
black_color = (0, 0, 0, 1)

# Create pawns
for index in range(8):
    add_piece(f'White Pawn {index + 1}', (index - 3.5, -2.5, 0.3), white_color)
    add_piece(f'Black Pawn {index + 1}', (index - 3.5, 2.5, 0.3), black_color)

# Create rooks
add_piece('White Rook 1', (-3.5, -3.5, 0.3), white_color)
add_piece('White Rook 2', (3.5, -3.5, 0.3), white_color)
add_piece('Black Rook 1', (-3.5, 3.5, 0.3), black_color)
add_piece('Black Rook 2', (3.5, 3.5, 0.3), black_color)

# Create knights
add_piece('White Knight 1', (-2.5, -3.5, 0.3), white_color)
add_piece('White Knight 2', (2.5, -3.5, 0.3), white_color)
add_piece('Black Knight 1', (-2.5, 3.5, 0.3), black_color)
add_piece('Black Knight 2', (2.5, 3.5, 0.3), black_color)

# Create bishops
add_piece('White Bishop 1', (-1.5, -3.5, 0.3), white_color)
add_piece('White Bishop 2', (1.5, -3.5, 0.3), white_color)
add_piece('Black Bishop 1', (-1.5, 3.5, 0.3), black_color)
add_piece('Black Bishop 2', (1.5, 3.5, 0.3), black_color)

# Create queens
add_piece('White Queen', (0.5, -3.5, 0.3), white_color)
add_piece('Black Queen', (0.5, 3.5, 0.3), black_color)

# Create kings
add_piece('White King', (-0.5, -3.5, 0.3), white_color)
add_piece('Black King', (-0.5, 3.5, 0.3), black_color)


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
