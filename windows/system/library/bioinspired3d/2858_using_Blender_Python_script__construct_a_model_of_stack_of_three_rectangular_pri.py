# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script__construct_a_model_of_stack_of_three_rectangular_pri" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script, construct a model of stack of three rectangular prisms.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a rectangular prism
def create_prism(location, dimensions):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.scale = (dimensions[0] / 2, dimensions[1] / 2, dimensions[2] / 2)

# Dimensions for the prisms
width = 2
depth = 1
height1 = 1
height2 = 1.5
height3 = 2

# Create three prisms stacked on top of each other
create_prism((0, 0, height1 / 2), (width, depth, height1))
create_prism((0, 0, height1 + height2 / 2), (width, depth, height2))
create_prism((0, 0, height1 + height2 + height3 / 2), (width, depth, height3))
