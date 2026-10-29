# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_script_that_constructs_cone" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender script that constructs cone.

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0))
