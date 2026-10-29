# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code__generate_a_model_of_8_cubes_evenly_in_a_circle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code, generate a model of 8 cubes evenly in a circle.

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
