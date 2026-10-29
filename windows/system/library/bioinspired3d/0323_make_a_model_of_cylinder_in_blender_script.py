# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_cylinder_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of cylinder in blender script

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
