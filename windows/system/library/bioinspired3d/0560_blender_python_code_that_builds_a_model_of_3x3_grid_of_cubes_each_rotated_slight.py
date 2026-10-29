# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_builds_a_model_of_3x3_grid_of_cubes_each_rotated_slight" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that builds a model of 3x3 grid of cubes each rotated slightly in Z

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a 3x3 grid of cubes
for x in range(3):
    for y in range(3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x * 2, y * 2, 0))
        cube = bpy.context.object
        # Rotate the cube slightly in the Z axis
        cube.rotation_euler[2] = math.radians(15)  # Rotate 15 degrees
