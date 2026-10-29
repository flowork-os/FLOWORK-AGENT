# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_cube_and_rotate_it_by_45_degrees_around_the_Z_axis_using_blender_scrip" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct cube and rotate it by 45 degrees around the Z axis using blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))

# Rotate the cube 45 degrees around the Z axis
bpy.context.object.rotation_euler[2] = math.radians(45)
