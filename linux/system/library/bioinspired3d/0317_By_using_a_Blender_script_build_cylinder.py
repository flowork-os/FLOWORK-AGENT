# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_build_cylinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script build cylinder.

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
