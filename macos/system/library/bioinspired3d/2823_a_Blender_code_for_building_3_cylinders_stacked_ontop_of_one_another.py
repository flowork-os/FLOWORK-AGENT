# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_building_3_cylinders_stacked_ontop_of_one_another" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for building 3 cylinders stacked ontop of one another.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cylinders
cylinder_radius = 1
cylinder_depth = 2
cylinder_count = 3

# Create cylinders stacked on top of each other
for i in range(cylinder_count):
    bpy.ops.mesh.primitive_cylinder_add(radius=cylinder_radius, depth=cylinder_depth, location=(0, 0, i * cylinder_depth))
