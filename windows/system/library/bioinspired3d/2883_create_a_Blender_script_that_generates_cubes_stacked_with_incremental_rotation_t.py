# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_Blender_script_that_generates_cubes_stacked_with_incremental_rotation_t" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a Blender script that generates cubes stacked with incremental rotation to form a spiral.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 30  # Number of cubes
height_increment = 0.5  # Height increment for each cube
rotation_increment = 15  # Rotation increment in degrees

for i in range(num_cubes):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * height_increment))
    cube = bpy.context.object
    cube.rotation_euler[2] = math.radians(i * rotation_increment)  # Rotate around Z-axis
