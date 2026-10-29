# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_generates_a_model_of_cylinder_and_scale_in_the_y_direction_t" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that generates a model of cylinder and scale in the y direction to make it elliptical.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))

# Get the active object (the cylinder we just created)
cylinder = bpy.context.active_object

# Scale the cylinder in the Y direction to make it elliptical
cylinder.scale[1] = 0.5  # Scale Y by 0.5 to create an ellipse
