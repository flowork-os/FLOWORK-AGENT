# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_3x3_grid_of_cubes_each_rotated_slightly_in_Z_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create 3x3 grid of cubes each rotated slightly in Z in blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a 3x3 grid of cubes
for x in range(3):
    for y in range(3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x * 2, y * 2, 0))
        cube = bpy.context.object
        # Rotate the cube slightly around the Z axis
        cube.rotation_euler[2] = math.radians(15)  # Rotate 15 degrees
