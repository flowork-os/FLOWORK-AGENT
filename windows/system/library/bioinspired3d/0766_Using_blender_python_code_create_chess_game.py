# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_python_code_create_chess_game" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender python code create chess game

import bpy

# Function to clear the scene of mesh objects

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

# Function to create a chessboard

def create_chessboard(size):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    return bpy.context.object

# Function to generate square materials

def get_square_material(is_white):
    material_name = 'White Square' if is_white else 'Black Square'
    color = (1, 1, 1, 1) if is_white else (0, 0, 0, 1)
    material = bpy.data.materials.new(name=material_name)
    material.diffuse_color = color
    return material

# Clear the scene
clear_scene()

# Create the chessboard
chess_board = create_chessboard(8)
chess_board.name = 'Chess Board'

# Create squares
for row in range(8):
    for col in range(8):
        is_white = (row + col) % 2 == 0
        square_material = get_square_material(is_white)
        square_position = (row - 3.5, col - 3.5, 0.01)
        square = bpy.ops.mesh.primitive_plane_add(size=1, location=square_position)
        square_obj = bpy.context.object
        square_obj.data.materials.append(square_material)
        square_obj.name = f'Square_{row}_{col}'

# Function to create a piece

def place_piece(name, position, color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=position)
    piece = bpy.context.object
    piece.name = name
    piece_material = bpy.data.materials.new(name=f'{name} Material')
    piece_material.diffuse_color = color
    piece.data.materials.append(piece_material)

# Define colors
white_color = (1, 1, 1, 1)
black_color = (0, 0, 0, 1)

# Create pawns
for index in range(8):
    place_piece(f'White Pawn {index + 1}', (index - 3.5, -2.5, 0.3), white_color)
    place_piece(f'Black Pawn {index + 1}', (index - 3.5, 2.5, 0.3), black_color)

# Create other pieces
pieces = [
    ('White Rook 1', (-3.5, -3.5, 0.3), white_color),
    ('White Rook 2', (3.5, -3.5, 0.3), white_color),
    ('Black Rook 1', (-3.5, 3.5, 0.3), black_color),
    ('Black Rook 2', (3.5, 3.5, 0.3), black_color),
    ('White Knight 1', (-2.5, -3.5, 0.3), white_color),
    ('White Knight 2', (2.5, -3.5, 0.3), white_color),
    ('Black Knight 1', (-2.5, 3.5, 0.3), black_color),
    ('Black Knight 2', (2.5, 3.5, 0.3), black_color),
    ('White Bishop 1', (-1.5, -3.5, 0.3), white_color),
    ('White Bishop 2', (1.5, -3.5, 0.3), white_color),
    ('Black Bishop 1', (-1.5, 3.5, 0.3), black_color),
    ('Black Bishop 2', (1.5, 3.5, 0.3), black_color),
    ('White Queen', (0.5, -3.5, 0.3), white_color),
    ('Black Queen', (0.5, 3.5, 0.3), black_color),
    ('White King', (-0.5, -3.5, 0.3), white_color),
    ('Black King', (-0.5, 3.5, 0.3), black_color)
]

for piece in pieces:
    place_piece(*piece)


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
