# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_makes_a_model_of_8_cubes_evenly_in_a_circle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that makes a model of 8 cubes evenly in a circle

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_cubes = 8
radius = 5
angle_increment = 2 * math.pi / num_cubes

for i in range(num_cubes):
    angle = i * angle_increment
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0))
