# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_three_cubes_stacked_with_increasing_size_in_python_blender_cod" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of three cubes stacked with increasing size in python blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create three cubes with increasing sizes
sizes = [1, 2, 3]  # Sizes of the cubes
z_offset = 0      # Initial z position

for size in sizes:
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_offset + size / 2))
    z_offset += size  # Update z_offset for the next cube
