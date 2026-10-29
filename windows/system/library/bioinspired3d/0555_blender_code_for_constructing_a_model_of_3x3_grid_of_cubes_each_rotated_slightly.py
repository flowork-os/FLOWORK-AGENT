# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_constructing_a_model_of_3x3_grid_of_cubes_each_rotated_slightly" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for constructing a model of 3x3 grid of cubes each rotated slightly in Z.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the grid
grid_size = 3
cube_size = 1
rotation_angle = math.radians(10)  # Rotate 10 degrees in radians

# Create a 3x3 grid of cubes
for x in range(grid_size):
    for y in range(grid_size):
        # Create a cube
        bpy.ops.mesh.primitive_cube_add(size=cube_size, location=(x * cube_size, y * cube_size, 0))
        cube = bpy.context.object
        
        # Rotate the cube slightly around the Z-axis
        cube.rotation_euler[2] = rotation_angle * (x + y)  # Vary rotation based on position
