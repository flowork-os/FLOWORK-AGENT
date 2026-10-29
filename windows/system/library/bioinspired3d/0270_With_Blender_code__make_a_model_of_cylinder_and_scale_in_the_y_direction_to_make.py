# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_code__make_a_model_of_cylinder_and_scale_in_the_y_direction_to_make" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender code, make a model of cylinder and scale in the y direction to make it elliptical.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))

# Scale the cylinder in the Y direction to make it elliptical
bpy.ops.transform.resize(value=(1, 2, 1))
