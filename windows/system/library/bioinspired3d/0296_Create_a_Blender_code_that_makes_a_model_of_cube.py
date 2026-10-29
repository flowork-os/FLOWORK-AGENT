# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_Blender_code_that_makes_a_model_of_cube" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a Blender code that makes a model of cube.

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
