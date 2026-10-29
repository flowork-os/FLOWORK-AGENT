# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_creates_3x3x3_grid_of_cylinders" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that creates 3x3x3 grid of cylinders.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the grid
grid_size = 3
cylinder_radius = 0.1
cylinder_height = 1

# Create a 3x3x3 grid of cylinders
for x in range(grid_size):
    for y in range(grid_size):
        for z in range(grid_size):
            bpy.ops.mesh.primitive_cylinder_add(radius=cylinder_radius, depth=cylinder_height, location=(x, y, z * cylinder_height))
