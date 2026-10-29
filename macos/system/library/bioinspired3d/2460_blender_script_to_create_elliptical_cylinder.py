# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_create_elliptical_cylinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to create elliptical cylinder

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create an elliptical cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
cylinder = bpy.context.object

# Scale the cylinder to make it elliptical
cylinder.scale[0] = 1.5  # Scale X for ellipse
cylinder.scale[1] = 0.5  # Scale Y for ellipse

# Optionally, apply the scale to make the changes permanent
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
