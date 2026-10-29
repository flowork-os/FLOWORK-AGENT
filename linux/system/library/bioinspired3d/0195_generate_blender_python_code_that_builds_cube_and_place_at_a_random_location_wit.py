# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_python_code_that_builds_cube_and_place_at_a_random_location_wit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender python code that builds cube and place at a random location within 3x3x3 grid

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=1)

# Get the newly created cube
cube = bpy.context.active_object

# Generate random coordinates within a 3x3x3 grid
x = random.uniform(-1.5, 1.5)
y = random.uniform(-1.5, 1.5)
z = random.uniform(-1.5, 1.5)

# Set the cube's location
cube.location = (x, y, z)
