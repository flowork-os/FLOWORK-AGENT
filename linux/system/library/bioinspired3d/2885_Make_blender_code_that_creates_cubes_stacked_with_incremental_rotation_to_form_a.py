# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_code_that_creates_cubes_stacked_with_incremental_rotation_to_form_a" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender code that creates cubes stacked with incremental rotation to form a spiral

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 20
angle_increment = math.radians(15)  # 15 degrees in radians
height_increment = 0.5

for i in range(num_cubes):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * height_increment))
    cube = bpy.context.object
    cube.rotation_euler[2] = i * angle_increment  # Rotate around Z-axis
