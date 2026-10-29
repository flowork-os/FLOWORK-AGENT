# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_3_cubes_placed_in_random_locations_around_a_3x3x3_grid_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create 3 cubes placed in random locations around a 3x3x3 grid in code in Blender

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create 3 cubes in random locations within a 3x3x3 grid
for _ in range(3):
    x = random.uniform(-1.5, 1.5)
    y = random.uniform(-1.5, 1.5)
    z = random.uniform(-1.5, 1.5)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
