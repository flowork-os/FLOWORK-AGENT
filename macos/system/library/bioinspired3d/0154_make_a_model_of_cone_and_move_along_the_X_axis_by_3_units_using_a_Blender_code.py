# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_cone_and_move_along_the_X_axis_by_3_units_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of cone and move along the X axis by 3 units using a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cone
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0))

# Move the cone along the X axis by 3 units
bpy.ops.transform.translate(value=(3, 0, 0))
