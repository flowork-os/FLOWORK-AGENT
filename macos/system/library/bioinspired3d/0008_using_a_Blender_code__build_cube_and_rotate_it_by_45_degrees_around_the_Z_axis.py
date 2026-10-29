# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_code__build_cube_and_rotate_it_by_45_degrees_around_the_Z_axis" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender code, build cube and rotate it by 45 degrees around the Z axis

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2)

# Rotate the cube by 45 degrees around the Z axis
bpy.context.object.rotation_euler[2] = math.radians(45)
