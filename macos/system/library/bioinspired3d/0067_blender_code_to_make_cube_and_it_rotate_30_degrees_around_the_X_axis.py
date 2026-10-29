# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_make_cube_and_it_rotate_30_degrees_around_the_X_axis" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to make cube and it rotate 30 degrees around the X axis.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2)

# Rotate the cube 30 degrees around the X axis
bpy.context.object.rotation_euler[0] = math.radians(30)
