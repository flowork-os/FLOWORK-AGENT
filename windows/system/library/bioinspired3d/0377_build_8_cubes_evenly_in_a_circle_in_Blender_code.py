# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_8_cubes_evenly_in_a_circle_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build 8 cubes evenly in a circle in Blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 8
radius = 5

for i in range(num_cubes):
    angle = i * (2 * math.pi / num_cubes)
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0))
