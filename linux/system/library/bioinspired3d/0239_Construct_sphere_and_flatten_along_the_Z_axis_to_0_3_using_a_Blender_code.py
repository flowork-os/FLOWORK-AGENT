# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_sphere_and_flatten_along_the_Z_axis_to_0_3_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct sphere and flatten along the Z axis to 0.3 using a Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))

# Flatten the sphere along the Z axis
bpy.ops.transform.resize(value=(1, 1, 0.3))
