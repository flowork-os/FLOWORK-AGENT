# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_elliptical_cylinder_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of elliptical cylinder using blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create an elliptical cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
cylinder = bpy.context.object

# Scale the cylinder to make it elliptical
cylinder.scale[0] = 1.5  # Scale X
cylinder.scale[1] = 0.5  # Scale Y

# Optionally, rename the object
cylinder.name = "EllipticalCylinder"
