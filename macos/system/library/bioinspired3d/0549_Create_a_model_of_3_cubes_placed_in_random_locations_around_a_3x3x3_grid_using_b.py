# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_3_cubes_placed_in_random_locations_around_a_3x3x3_grid_using_b" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of 3 cubes placed in random locations around a 3x3x3 grid using blender python code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a 3x3x3 grid
grid_size = 3
num_cubes = 3

for _ in range(num_cubes):
    # Generate random positions within the grid
    x = random.uniform(-grid_size / 2, grid_size / 2)
    y = random.uniform(-grid_size / 2, grid_size / 2)
    z = random.uniform(-grid_size / 2, grid_size / 2)
    
    # Create a cube at the random position
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
