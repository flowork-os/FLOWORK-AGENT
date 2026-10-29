# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_three_cubes_stacked_with_increasing_size_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of three cubes stacked with increasing size in a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create three cubes with increasing sizes
sizes = [1, 2, 3]  # Sizes of the cubes
z_position = 0     # Initial z position

for size in sizes:
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_position + size / 2))
    z_position += size  # Update z position for the next cube
