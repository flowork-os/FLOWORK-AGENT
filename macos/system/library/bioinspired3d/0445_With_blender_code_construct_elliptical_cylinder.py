# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_code_construct_elliptical_cylinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender code construct elliptical cylinder.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create an elliptical cylinder
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1, depth=2, location=(0, 0, 0))
elliptical_cylinder = bpy.context.object

# Scale the cylinder to make it elliptical
elliptical_cylinder.scale[0] = 1.5  # Scale X
elliptical_cylinder.scale[1] = 0.5  # Scale Y
