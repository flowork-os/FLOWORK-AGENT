# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code__make_a_model_of_three_cubes_lined_up_in_a_straight_row" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code, make a model of three cubes lined up in a straight row.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create three cubes
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 2, 0, 0))
