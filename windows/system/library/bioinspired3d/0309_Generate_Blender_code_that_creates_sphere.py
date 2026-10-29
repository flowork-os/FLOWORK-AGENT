# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_code_that_creates_sphere" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender code that creates sphere

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
