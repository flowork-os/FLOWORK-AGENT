# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_building_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for building wallpaper pattern

import bpy
import math

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Parameters for the hexagonal structure
hex_size = 1
hex_thickness = 0.1
num_rows = 5
num_cols = 5

# Class to handle hexagon creation
class HexagonGrid:
    def __init__(self, size, thickness):
        self.size = size
        self.thickness = thickness

    def add_hexagon(self, x, y, z):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=self.size, depth=self.thickness, location=(x, y, z))

# Instantiate the hexagon grid
hex_grid = HexagonGrid(hex_size, hex_thickness)

# Build the hexagonal layout
for row in range(num_rows):
    for col in range(num_cols):
        x_position = col * 1.5 * hex_size
        y_position = row * math.sqrt(3) * hex_size + (col % 2) * (math.sqrt(3) / 2 * hex_size)
        hex_grid.add_hexagon(x_position, y_position, 0)
