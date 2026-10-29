# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_elliptical_cylinder_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of elliptical cylinder in a blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create an elliptical cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))

# Get the newly created cylinder
cylinder = bpy.context.object

# Scale the cylinder to make it elliptical
cylinder.scale[0] = 1.5  # Scale X for the ellipse
cylinder.scale[1] = 0.5  # Scale Y for the ellipse

# Optionally, rename the object
cylinder.name = "EllipticalCylinder"
