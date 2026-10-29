# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code__construct_cone_and_move_along_the_X_axis_by_3_units" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code, construct cone and move along the X axis by 3 units.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cone
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0))

# Move the cone along the X axis by 3 units
bpy.ops.transform.translate(value=(3, 0, 0))
