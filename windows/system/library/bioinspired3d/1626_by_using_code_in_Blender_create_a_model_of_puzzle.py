# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_code_in_Blender_create_a_model_of_puzzle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using code in Blender create a model of puzzle

import bpy
import random

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

grid_rows = 10
grid_columns = 10
cell_width = 1
cell_height = 1

def add_piece_to_scene(x_pos, y_pos):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x_pos, y_pos, 0))
    new_piece = bpy.context.object
    new_piece.name = f"Tile_{x_pos}_{y_pos}"
    return new_piece

for row in range(grid_rows):
    for col in range(grid_columns):
        x_coordinate = col * cell_width
        y_coordinate = row * cell_height
        add_piece_to_scene(x_coordinate, y_coordinate)

def create_interlock(piece, side):
    vertices = piece.data.vertices
    if side == 'top':
        vertices[1].co.z += random.uniform(0.1, 0.3)
        vertices[2].co.z += random.uniform(0.1, 0.3)
    elif side == 'bottom':
        vertices[0].co.z -= random.uniform(0.1, 0.3)
        vertices[3].co.z -= random.uniform(0.1, 0.3)
    elif side == 'left':
        vertices[0].co.x -= random.uniform(0.1, 0.3)
        vertices[1].co.x -= random.uniform(0.1, 0.3)
    elif side == 'right':
        vertices[2].co.x += random.uniform(0.1, 0.3)
        vertices[3].co.x += random.uniform(0.1, 0.3)

for row in range(grid_rows):
    for col in range(grid_columns):
        current_tile = bpy.data.objects[f"Tile_{col * cell_width}_{row * cell_height}"]
        if row < grid_rows - 1:
            create_interlock(current_tile, 'top')
        if row > 0:
            create_interlock(current_tile, 'bottom')
        if col < grid_columns - 1:
            create_interlock(current_tile, 'right')
        if col > 0:
            create_interlock(current_tile, 'left')

for tile in bpy.data.objects:
    if "Tile_" in tile.name:
        tile.select_set(True)
        bpy.ops.object.duplicate_move()
        bpy.context.object.name = tile.name + "_copy"
        tile.select_set(False)

bpy.ops.object.select_all(action='DESELECT')
