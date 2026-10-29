# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_code_in_Blender_that_makes_a_model_of_3x3x3_grid_of_cylinders" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate code in Blender that makes a model of 3x3x3 grid of cylinders

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
        position = (x, y, cylinder_height / 2)
        
        # Add a cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=cylinder_radius, depth=cylinder_height, location=position)
