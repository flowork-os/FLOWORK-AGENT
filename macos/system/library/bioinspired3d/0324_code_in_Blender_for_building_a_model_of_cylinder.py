# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_building_a_model_of_cylinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for building a model of cylinder.

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
