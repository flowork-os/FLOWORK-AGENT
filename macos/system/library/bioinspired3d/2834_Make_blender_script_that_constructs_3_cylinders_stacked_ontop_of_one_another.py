# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_script_that_constructs_3_cylinders_stacked_ontop_of_one_another" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender script that constructs 3 cylinders stacked ontop of one another.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cylinders
radius = 1
depth = 2
cylinder_count = 3

# Create cylinders stacked on top of each other
for i in range(cylinder_count):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=(0, 0, i * depth))
