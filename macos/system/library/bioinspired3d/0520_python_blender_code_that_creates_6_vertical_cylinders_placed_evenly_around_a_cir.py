# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_creates_6_vertical_cylinders_placed_evenly_around_a_cir" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that creates 6 vertical cylinders placed evenly around a circle

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cylinders = 6
radius = 5
height = 2

for i in range(num_cylinders):
    angle = i * (2 * math.pi / num_cylinders)
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=height, location=(x, y, height / 2))
