# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script_build_cone_ontop_of_a_cylinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script build cone ontop of a cylinder

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))

# Create a cone on top of the cylinder
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 3))
