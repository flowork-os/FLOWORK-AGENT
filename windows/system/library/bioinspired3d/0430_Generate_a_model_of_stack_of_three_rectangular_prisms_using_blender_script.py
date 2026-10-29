# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_stack_of_three_rectangular_prisms_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of stack of three rectangular prisms using blender script

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
prism_dimensions = [(1, 2, 0.5), (1.5, 1.5, 1), (2, 1, 1.5)]

# Create the stack of prisms
for i, dimensions in enumerate(prism_dimensions):
    create_prism(location=(0, 0, sum(dim[2] for dim in prism_dimensions[:i]) + dimensions[2] / 2), dimensions=dimensions)
