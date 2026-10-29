# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_8_spheres_evenly_spaced_in_a_circular_arrangement_using_ble" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of 8 spheres evenly spaced in a circular arrangement using blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters
num_spheres = 8
radius = 5
sphere_radius = 0.5

# Create spheres in a circular arrangement
for i in range(num_spheres):
    angle = 2 * math.pi * i / num_spheres
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=sphere_radius, location=(x, y, 0))
