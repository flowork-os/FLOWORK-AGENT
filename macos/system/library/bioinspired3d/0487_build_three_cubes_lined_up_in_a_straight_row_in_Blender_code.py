# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_three_cubes_lined_up_in_a_straight_row_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build three cubes lined up in a straight row in Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 2, 0, 0))
