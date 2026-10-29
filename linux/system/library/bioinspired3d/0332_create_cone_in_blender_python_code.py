# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_cone_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create cone in blender python code

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0))
