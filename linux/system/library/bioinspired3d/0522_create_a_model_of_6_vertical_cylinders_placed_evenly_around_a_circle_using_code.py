# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_6_vertical_cylinders_placed_evenly_around_a_circle_using_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of 6 vertical cylinders placed evenly around a circle using code in Blender

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters
num_cylinders = 6
radius = 5
height = 2
radius_cylinder = 0.5

# Create cylinders
for i in range(num_cylinders):
    angle = i * (2 * math.pi / num_cylinders)
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_cylinder, depth=height, location=(x, y, height / 2))
