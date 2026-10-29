# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_3_cylinders_stacked_ontop_of_one_another_using_blender_scri" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of 3 cylinders stacked ontop of one another using blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create three cylinders
for i in range(3):
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, i * 2))
