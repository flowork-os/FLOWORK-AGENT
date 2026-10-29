# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_python_code__generate_a_model_of_cube_and_place_at_a_random_locati" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender python code, generate a model of cube and place at a random location within 3x3x3 grid

import bpy
import math
import random

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=1)

# Get the newly created cube
cube = bpy.context.object

# Generate random location within a 3x3x3 grid
random_location = (
    random.uniform(-1.5, 1.5),  # X coordinate
    random.uniform(-1.5, 1.5),  # Y coordinate
    random.uniform(-1.5, 1.5)   # Z coordinate
)

# Set the cube's location
cube.location = random_location
