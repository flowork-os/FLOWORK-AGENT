# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_blender_code_generate_a_model_of_3_cylinders_stacked_ontop_of_one_anothe" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a blender code generate a model of 3 cylinders stacked ontop of one another

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cylinders
radius = 1
height = 2
cylinder_count = 3

# Create cylinders
for i in range(cylinder_count):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=(0, 0, i * height))
