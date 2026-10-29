# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_3_cubes_placed_in_random_locations_around_a_3x3x3_grid_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build 3 cubes placed in random locations around a 3x3x3 grid in blender script

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create 3 cubes in random locations within a 3x3x3 grid
for _ in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5)))
