# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_stack_of_three_rectangular_prisms_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of stack of three rectangular prisms in blender code

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a stack of three rectangular prisms
heights = [1, 1.5, 2]  # Heights of the prisms
width = 1               # Width of the prisms
depth = 0.5             # Depth of the prisms

for i, height in enumerate(heights):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, sum(heights[:i]) + height / 2))
    obj = bpy.context.object
    obj.scale[0] = width / 2  # Scale width
    obj.scale[1] = depth / 2   # Scale depth
    obj.scale[2] = height / 2   # Scale height
