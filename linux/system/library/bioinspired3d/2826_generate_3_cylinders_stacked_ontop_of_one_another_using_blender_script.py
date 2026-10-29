# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_3_cylinders_stacked_ontop_of_one_another_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate 3 cylinders stacked ontop of one another using blender script

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create three cylinders stacked on top of each other
for i in range(3):
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, i * 2))
