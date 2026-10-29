# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_makes_sphere" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that makes sphere

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
