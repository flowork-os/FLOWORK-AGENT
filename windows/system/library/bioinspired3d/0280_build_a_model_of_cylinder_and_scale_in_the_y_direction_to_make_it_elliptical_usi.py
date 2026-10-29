# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_cylinder_and_scale_in_the_y_direction_to_make_it_elliptical_usi" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of cylinder and scale in the y direction to make it elliptical using a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))

# Get the created cylinder object
cylinder = bpy.context.object

# Scale the cylinder in the Y direction to make it elliptical
cylinder.scale[1] = 0.5  # Scale Y to 0.5 for an elliptical shape
