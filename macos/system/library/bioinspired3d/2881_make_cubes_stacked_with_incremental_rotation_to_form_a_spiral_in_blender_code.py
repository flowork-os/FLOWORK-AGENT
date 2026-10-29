# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_cubes_stacked_with_incremental_rotation_to_form_a_spiral_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make cubes stacked with incremental rotation to form a spiral in blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 20
distance = 0.5
angle_increment = math.radians(15)

for i in range(num_cubes):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * distance))
    cube = bpy.context.object
    cube.rotation_euler[2] = i * angle_increment
