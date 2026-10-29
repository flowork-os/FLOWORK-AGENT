# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_that_creates_a_model_of_cylinder_and_scale_in_the_y_direct" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender that creates a model of cylinder and scale in the y direction to make it elliptical

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))

# Scale the cylinder in the y direction to make it elliptical
bpy.ops.transform.resize(value=(1, 2, 1))
