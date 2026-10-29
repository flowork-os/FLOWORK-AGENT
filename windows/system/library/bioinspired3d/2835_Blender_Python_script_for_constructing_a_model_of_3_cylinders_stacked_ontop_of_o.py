# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_constructing_a_model_of_3_cylinders_stacked_ontop_of_o" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for constructing a model of 3 cylinders stacked ontop of one another

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the cylinders
radius = 1
height = 2
cylinder_count = 3

# Create cylinders
for i in range(cylinder_count):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=(0, 0, i * height))
    cylinder = bpy.context.object
    cylinder.name = f"Cylinder_{i + 1}"
