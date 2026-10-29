# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_constructing_a_model_of_stack_of_three_rectangular_prisms" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for constructing a model of stack of three rectangular prisms

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a rectangular prism
def create_prism(location, dimensions):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.scale = (dimensions[0] / 2, dimensions[1] / 2, dimensions[2] / 2)

# Dimensions for the three prisms
dimensions = [(1, 2, 0.5), (1, 2, 1), (1, 2, 1.5)]  # (width, depth, height)

# Create three prisms stacked on top of each other
for i, dim in enumerate(dimensions):
    create_prism(location=(0, 0, sum(d[2] for d in dimensions[:i]) + dim[2] / 2), dimensions=dim)
