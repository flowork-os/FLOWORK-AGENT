# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_makes_a_model_of_cylinder_and_move_to_location__0__0__5" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that makes a model of cylinder and move to location (0, 0, 5)

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))

# Move the cylinder to location (0, 0, 5)
bpy.ops.transform.translate(value=(0, 0, 5))
