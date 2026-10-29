# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_cylinder_and_stretch_along_the_Z_axis_by_2_times_using_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of cylinder and stretch along the Z axis by 2 times using blender python code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, location=(0, 0, 0))

# Get the active object (the cylinder we just created)
cylinder = bpy.context.active_object

# Scale the cylinder along the Z axis by 2 times
cylinder.scale[2] *= 2
