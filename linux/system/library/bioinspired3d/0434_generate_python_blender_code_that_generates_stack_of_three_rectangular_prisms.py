# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_generates_stack_of_three_rectangular_prisms" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that generates stack of three rectangular prisms.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Parameters for the prisms
width = 2
depth = 1
height = 1

# Create three rectangular prisms
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * height + height / 2))
    obj = bpy.context.object
    obj.scale[0] = width / 2  # Scale X
    obj.scale[1] = depth / 2   # Scale Y
    obj.scale[2] = height / 2  # Scale Z
