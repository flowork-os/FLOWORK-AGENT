# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_3x3x3_grid_of_cylinders_using_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create 3x3x3 grid of cylinders using a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the grid
grid_size = 3
cylinder_radius = 0.5
cylinder_depth = 1.0
spacing = 1.5

# Create a 3x3x3 grid of cylinders
for x in range(grid_size):
    for y in range(grid_size):
        for z in range(grid_size):
            bpy.ops.mesh.primitive_cylinder_add(
                radius=cylinder_radius,
                depth=cylinder_depth,
                location=(x * spacing, y * spacing, z * spacing)
            )
