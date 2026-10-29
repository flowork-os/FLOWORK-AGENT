# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_Python_script__generate_a_model_of_3_cylinders_stacked_ontop_of_one" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender Python script, generate a model of 3 cylinders stacked ontop of one another

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cylinders
cylinder_radius = 0.5
cylinder_height = 2.0
cylinder_count = 3

# Create cylinders
for i in range(cylinder_count):
    bpy.ops.mesh.primitive_cylinder_add(radius=cylinder_radius, depth=cylinder_height, location=(0, 0, i * cylinder_height))
