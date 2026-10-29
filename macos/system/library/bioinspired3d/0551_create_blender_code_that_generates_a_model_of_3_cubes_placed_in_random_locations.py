# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_code_that_generates_a_model_of_3_cubes_placed_in_random_locations" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender code that generates a model of 3 cubes placed in random locations around a 3x3x3 grid

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a 3x3x3 grid
grid_size = 3
num_cubes = 3

for _ in range(num_cubes):
    x = random.randint(-grid_size, grid_size)
    y = random.randint(-grid_size, grid_size)
    z = random.randint(-grid_size, grid_size)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
