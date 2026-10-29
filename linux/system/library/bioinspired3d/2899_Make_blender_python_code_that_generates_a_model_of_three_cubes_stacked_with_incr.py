# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_python_code_that_generates_a_model_of_three_cubes_stacked_with_incr" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender python code that generates a model of three cubes stacked with increasing size

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Define the sizes and positions for the cubes
sizes = [1, 1.5, 2]  # Sizes of the cubes
z_positions = [0, 1, 2]  # Z positions for stacking

# Create the cubes
for size, z in zip(sizes, z_positions):
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z))
