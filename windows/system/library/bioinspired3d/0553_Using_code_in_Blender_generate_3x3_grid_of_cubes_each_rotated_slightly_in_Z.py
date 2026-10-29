# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender_generate_3x3_grid_of_cubes_each_rotated_slightly_in_Z" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender generate 3x3 grid of cubes each rotated slightly in Z.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a 3x3 grid of cubes
for i in range(3):
    for j in range(3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 2, j * 2, 0))
        cube = bpy.context.object
        cube.rotation_euler[2] = math.radians(15 * (i + j))  # Rotate slightly in Z
