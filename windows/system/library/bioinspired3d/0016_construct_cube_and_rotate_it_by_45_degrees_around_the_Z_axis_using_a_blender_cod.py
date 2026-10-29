# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_cube_and_rotate_it_by_45_degrees_around_the_Z_axis_using_a_blender_cod" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct cube and rotate it by 45 degrees around the Z axis using a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))

# Rotate the cube 45 degrees around the Z axis
bpy.ops.transform.rotate(value=math.radians(45), orient_axis='Z')
