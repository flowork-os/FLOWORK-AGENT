# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_that_creates_puzzle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code that creates puzzle.

import bpy
import random

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

total_rows = 10
total_columns = 10
block_width = 1
block_height = 1

class Puzzle:
    def __init__(self, rows, cols, width, height):
        self.rows = rows
        self.cols = cols
        self.width = width
        self.height = height

    def create_piece(self, x, y):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, 0))
        piece = bpy.context.object
        piece.name = f"Block_{x}_{y}"
        return piece

    def build_puzzle(self):
        for i in range(self.rows):
            for j in range(self.cols):
                x_position = j * self.width
                y_position = i * self.height
                self.create_piece(x_position, y_position)

    def interlock_edges(self):
        for i in range(self.rows):
            for j in range(self.cols):
                current_piece = bpy.data.objects[f"Block_{j * self.width}_{i * self.height}"]
                if i < self.rows - 1:
                    self.adjust_edge(current_piece, 'top')
                if i > 0:
                    self.adjust_edge(current_piece, 'bottom')
                if j < self.cols - 1:
                    self.adjust_edge(current_piece, 'right')
                if j > 0:
                    self.adjust_edge(current_piece, 'left')

    def adjust_edge(self, piece, direction):
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

    def ensure_unique_pieces(self):
        for obj in bpy.data.objects:
            if "Block_" in obj.name:
                obj.select_set(True)
                bpy.ops.object.duplicate_move()
                bpy.context.object.name = obj.name + "_variant"
                obj.select_set(False)

puzzle = Puzzle(total_rows, total_columns, block_width, block_height)
puzzle.build_puzzle()
puzzle.interlock_edges()
puzzle.ensure_unique_pieces()

bpy.ops.object.select_all(action='DESELECT')
