# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_making_cylinder_and_lay_it_on_its_side" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for making cylinder and lay it on its side

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))

# Rotate the cylinder to lay it on its side
bpy.ops.transform.rotate(value=math.radians(90), orient_axis='X')
