# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_Blender_code_that_creates_cubes_stacked_with_incremental_rotation_to_form" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create Blender code that creates cubes stacked with incremental rotation to form a spiral.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 30
height_increment = 0.5
angle_increment = 15  # degrees

for i in range(num_cubes):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * height_increment))
    cube = bpy.context.object
    cube.rotation_euler[2] = math.radians(i * angle_increment)  # Rotate around Z-axis
