# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_script_that_generates_cube_and_place_at_a_random_location_withi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender script that generates cube and place at a random location within 3x3x3 grid

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Generate a cube
bpy.ops.mesh.primitive_cube_add(size=1)

# Get the active object (the cube we just created)
cube = bpy.context.active_object

# Generate random coordinates within the 3x3x3 grid
x = random.uniform(-1.5, 1.5)
y = random.uniform(-1.5, 1.5)
z = random.uniform(-1.5, 1.5)

# Set the cube's location
cube.location = (x, y, z)
