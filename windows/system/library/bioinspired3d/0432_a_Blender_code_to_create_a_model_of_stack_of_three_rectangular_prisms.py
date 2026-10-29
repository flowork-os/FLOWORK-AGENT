# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_to_create_a_model_of_stack_of_three_rectangular_prisms" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code to create a model of stack of three rectangular prisms

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a stack of three rectangular prisms
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * 1.5))
    # Scale the cube to make it a rectangular prism
    bpy.ops.transform.resize(value=(1, 0.5, 0.5))
