# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_script_that_makes_three_cubes_lined_up_in_a_straight_row" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender script that makes three cubes lined up in a straight row.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 2, 0, 0))
