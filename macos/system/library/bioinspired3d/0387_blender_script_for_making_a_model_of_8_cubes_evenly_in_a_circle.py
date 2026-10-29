# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_making_a_model_of_8_cubes_evenly_in_a_circle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for making a model of 8 cubes evenly in a circle

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 8
radius = 5

for i in range(num_cubes):
    angle = (2 * math.pi / num_cubes) * i
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0))
