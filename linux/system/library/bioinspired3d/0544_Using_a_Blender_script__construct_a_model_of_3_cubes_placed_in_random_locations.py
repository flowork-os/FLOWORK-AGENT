# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script__construct_a_model_of_3_cubes_placed_in_random_locations" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script, construct a model of 3 cubes placed in random locations around a 3x3x3 grid.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create 3 cubes in random locations within a 3x3x3 grid
for _ in range(3):
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=1)
    cube = bpy.context.object
    
    # Randomly position the cube within the grid
    cube.location.x = random.uniform(-1.5, 1.5)
    cube.location.y = random.uniform(-1.5, 1.5)
    cube.location.z = random.uniform(-1.5, 1.5)
