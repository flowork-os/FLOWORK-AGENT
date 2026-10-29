# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_script_that_creates_cylinder_and_stretch_along_the_Z_axis_by_2_t" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender script that creates cylinder and stretch along the Z axis by 2 times.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, location=(0, 0, 0))

# Stretch the cylinder along the Z axis by 2 times
bpy.ops.transform.resize(value=(1, 1, 2))
