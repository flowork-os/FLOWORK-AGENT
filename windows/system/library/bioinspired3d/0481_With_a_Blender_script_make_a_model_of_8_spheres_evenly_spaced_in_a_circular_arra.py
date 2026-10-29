# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_script_make_a_model_of_8_spheres_evenly_spaced_in_a_circular_arra" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender script make a model of 8 spheres evenly spaced in a circular arrangement

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

num_spheres = 8
radius = 5

for i in range(num_spheres):
    angle = (2 * math.pi / num_spheres) * i
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, y, 0))
