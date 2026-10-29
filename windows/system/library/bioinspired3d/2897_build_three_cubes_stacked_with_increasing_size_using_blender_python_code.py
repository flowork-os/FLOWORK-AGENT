# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_three_cubes_stacked_with_increasing_size_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build three cubes stacked with increasing size using blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create three cubes with increasing sizes
sizes = [1, 2, 3]  # Sizes for the cubes
z_offset = 0      # Initial Z offset for stacking

for size in sizes:
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, z_offset + size / 2))
    z_offset += size  # Update the Z offset for the next cube
