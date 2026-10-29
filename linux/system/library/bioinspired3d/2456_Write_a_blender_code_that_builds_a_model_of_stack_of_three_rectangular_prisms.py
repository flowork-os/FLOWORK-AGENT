# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_that_builds_a_model_of_stack_of_three_rectangular_prisms" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code that builds a model of stack of three rectangular prisms

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a rectangular prism
def create_prism(name, dimensions, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (dimensions[0] / 2, dimensions[1] / 2, dimensions[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Create three rectangular prisms
create_prism("Prism1", (2, 1, 0.5), (0, 0, 0.25))
create_prism("Prism2", (1.5, 1, 0.75), (0, 0, 1.25))
create_prism("Prism3", (1, 1, 1), (0, 0, 2.25))
