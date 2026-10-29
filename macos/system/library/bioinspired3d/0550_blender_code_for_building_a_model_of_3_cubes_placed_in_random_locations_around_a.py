# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_building_a_model_of_3_cubes_placed_in_random_locations_around_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for building a model of 3 cubes placed in random locations around a 3x3x3 grid.

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a 3x3x3 grid of possible positions
positions = [(x, y, z) for x in range(3) for y in range(3) for z in range(3)]

# Randomly select 3 unique positions
selected_positions = random.sample(positions, 3)

# Create cubes at the selected positions
for pos in selected_positions:
    bpy.ops.mesh.primitive_cube_add(location=(pos[0], pos[1], pos[2]))
