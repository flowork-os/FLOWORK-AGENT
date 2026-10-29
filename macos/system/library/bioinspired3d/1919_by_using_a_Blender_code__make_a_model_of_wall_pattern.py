# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code__make_a_model_of_wall_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code, make a model of wall pattern.

import bpy

# Step 1: Remove all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Constants for hexagon dimensions
radius_of_hexagon = 1.0
thickness_of_hexagon = 0.1
spacing_between_hexagons = 1.5

# Class to create a hexagonal grid
class HexagonGrid:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def create_hexagon(self, x, y):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius_of_hexagon, depth=thickness_of_hexagon, location=(x, y, 0))

    def generate_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                x_pos = c * radius_of_hexagon * 2
                y_pos = r * radius_of_hexagon * 2
                self.create_hexagon(x_pos, y_pos)

# Step 2: Instantiate and create the hexagon grid
hex_grid = HexagonGrid(5, 5)
hex_grid.generate_grid()

# Step 3: Ensure all objects are selected for uniform adjustments
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.transform.resize(value=(1, 1, 1))
bpy.ops.object.select_all(action='DESELECT')
