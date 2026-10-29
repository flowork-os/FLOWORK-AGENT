# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_cube_and_rotate_it_by_45_degrees_around_the_Z_axis_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create cube and rotate it by 45 degrees around the Z axis in blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2)

# Rotate the cube by 45 degrees around the Z axis
bpy.context.object.rotation_euler[2] = math.radians(45)
