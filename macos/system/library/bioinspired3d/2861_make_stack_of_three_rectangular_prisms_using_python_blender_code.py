# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_stack_of_three_rectangular_prisms_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make stack of three rectangular prisms using python blender code

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
height = 1

# Create three stacked prisms
create_prism((0, 0, height), (width, depth, height))
create_prism((0, 0, 2 * height), (width, depth, height))
create_prism((0, 0, 3 * height), (width, depth, height))
