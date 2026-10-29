# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_cube_and_place_at_a_random_location_within_3x3x3_grid_in_a_blender_cod" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct cube and place at a random location within 3x3x3 grid in a blender code

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=1)

# Randomly place the cube within a 3x3x3 grid
x = random.uniform(-1.5, 1.5)
y = random.uniform(-1.5, 1.5)
z = random.uniform(-1.5, 1.5)

# Set the location of the cube
bpy.context.object.location = (x, y, z)
