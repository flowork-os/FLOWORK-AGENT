# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_cone_and_rotate_it_90_degrees_around_the_Y_axis_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create cone and rotate it 90 degrees around the Y axis in a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cone
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0))

# Rotate the cone 90 degrees around the Y axis
bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Y')
