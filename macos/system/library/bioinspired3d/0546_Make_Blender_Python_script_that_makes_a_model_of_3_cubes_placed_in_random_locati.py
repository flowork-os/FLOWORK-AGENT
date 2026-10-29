# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_Blender_Python_script_that_makes_a_model_of_3_cubes_placed_in_random_locati" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make Blender Python script that makes a model of 3 cubes placed in random locations around a 3x3x3 grid.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create 3 cubes in random locations within a 3x3x3 grid
for _ in range(3):
    # Generate random coordinates within the grid
    x = random.uniform(-1.5, 1.5)
    y = random.uniform(-1.5, 1.5)
    z = random.uniform(-1.5, 1.5)
    
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
