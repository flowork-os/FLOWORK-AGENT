# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_code_in_Blender_that_builds_a_model_of_cone" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create code in Blender that builds a model of cone

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Add a cone to the scene
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1, depth=2, location=(0, 0, 0))
