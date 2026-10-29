# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_chess_game_using_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct chess game using a blender code

import bpy

# Function to delete all mesh objects from the scene

def remove_mesh_objects():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

# Create the chessboard

def setup_chessboard():
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    board = bpy.context.object
    board.name = 'Chess Board'
    return board

# Function to create a square with a specific material

def create_square_with_material(position, is_white):
    bpy.ops.mesh.primitive_plane_add(size=1, location=position)
    square = bpy.context.object
    material = bpy.data.materials.new(name='White' if is_white else 'Black')
    material.diffuse_color = (1, 1, 1, 1) if is_white else (0, 0, 0, 1)
    square.data.materials.append(material)
    return square

# Clear the scene before creating a new board
remove_mesh_objects()

# Create the chessboard
setup_chessboard()

# Create squares on the chessboard
for x in range(8):
    for y in range(8):
        create_square_with_material((x - 3.5, y - 3.5, 0.01), (x + y) % 2 == 0)

# Function for adding a chess piece

def add_chess_piece(name, location, color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=location)
    piece = bpy.context.object
    piece.name = name
    material = bpy.data.materials.new(name=f'{name} Material')
    material.diffuse_color = color
    piece.data.materials.append(material)

# Define piece colors
white_color = (1, 1, 1, 1)
black_color = (0, 0, 0, 1)

# Add pawns
for index in range(8):
    add_chess_piece(f'White Pawn {index + 1}', (index - 3.5, -2.5, 0.3), white_color)
    add_chess_piece(f'Black Pawn {index + 1}', (index - 3.5, 2.5, 0.3), black_color)

# Define positions for other pieces
piece_positions = {
    'White Rook 1': (-3.5, -3.5, 0.3),
    'White Rook 2': (3.5, -3.5, 0.3),
    'Black Rook 1': (-3.5, 3.5, 0.3),
    'Black Rook 2': (3.5, 3.5, 0.3),
    'White Knight 1': (-2.5, -3.5, 0.3),
    'White Knight 2': (2.5, -3.5, 0.3),
    'Black Knight 1': (-2.5, 3.5, 0.3),
    'Black Knight 2': (2.5, 3.5, 0.3),
    'White Bishop 1': (-1.5, -3.5, 0.3),
    'White Bishop 2': (1.5, -3.5, 0.3),
    'Black Bishop 1': (-1.5, 3.5, 0.3),
    'Black Bishop 2': (1.5, 3.5, 0.3),
    'White Queen': (0.5, -3.5, 0.3),
    'Black Queen': (0.5, 3.5, 0.3),
    'White King': (-0.5, -3.5, 0.3),
    'Black King': (-0.5, 3.5, 0.3)
}

# Create other pieces
for piece_name, position in piece_positions.items():
    color = white_color if 'White' in piece_name else black_color
    add_chess_piece(piece_name, position, color)


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
