# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_code_generate_a_model_of_3x3x3_grid_of_cylinders" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender code generate a model of 3x3x3 grid of cylinders.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the grid
grid_size = 3
cylinder_radius = 0.1
cylinder_height = 1

# Create a 3x3 grid of cylinders
for x in range(grid_size):
    for y in range(grid_size):
        # Calculate the position for each cylinder
        x_pos = x * 2  # spacing between cylinders
        y_pos = y * 2  # spacing between cylinders
        
        # Create a cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=cylinder_radius, depth=cylinder_height, location=(x_pos, y_pos, cylinder_height / 2))
