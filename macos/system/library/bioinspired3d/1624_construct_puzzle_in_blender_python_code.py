# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_puzzle_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct puzzle in blender python code

import bpy
import random

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Puzzle configuration
num_rows = 10
num_cols = 10
unit_width = 1
unit_height = 1

# Function to generate a puzzle piece
def generate_piece(x_coord, y_coord):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x_coord, y_coord, 0))
    puzzle_piece = bpy.context.object
    puzzle_piece.name = f"PuzzlePiece_{x_coord}_{y_coord}"
    return puzzle_piece

# Create the puzzle pieces
for row in range(num_rows):
    for col in range(num_cols):
        x_pos = col * unit_width
        y_pos = row * unit_height
        generate_piece(x_pos, y_pos)

# Function to modify edges for interlocking
def modify_edge(piece, direction):
    vertices = piece.data.vertices
    if direction == 'top':
        vertices[1].co.z += random.uniform(0.1, 0.3)
        vertices[2].co.z += random.uniform(0.1, 0.3)
    elif direction == 'bottom':
        vertices[0].co.z -= random.uniform(0.1, 0.3)
        vertices[3].co.z -= random.uniform(0.1, 0.3)
    elif direction == 'left':
        vertices[0].co.x -= random.uniform(0.1, 0.3)
        vertices[1].co.x -= random.uniform(0.1, 0.3)
    elif direction == 'right':
        vertices[2].co.x += random.uniform(0.1, 0.3)
        vertices[3].co.x += random.uniform(0.1, 0.3)

# Adjust edges for interlocking
for row in range(num_rows):
    for col in range(num_cols):
        current_piece = bpy.data.objects[f"PuzzlePiece_{col * unit_width}_{row * unit_height}"]
        if row < num_rows - 1:
            modify_edge(current_piece, 'top')
        if row > 0:
            modify_edge(current_piece, 'bottom')
        if col < num_cols - 1:
            modify_edge(current_piece, 'right')
        if col > 0:
            modify_edge(current_piece, 'left')

# Create unique pieces
for obj in bpy.data.objects:
    if "PuzzlePiece_" in obj.name:
        obj.select_set(True)
        bpy.ops.object.duplicate_move()
        bpy.context.object.name = obj.name + "_copy"
        obj.select_set(False)

bpy.ops.object.select_all(action='DESELECT')
