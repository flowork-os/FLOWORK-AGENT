# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_create_a_model_of_stack_of_three_rectangular_prisms" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to create a model of stack of three rectangular prisms

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a rectangular prism
def create_prism(location, dimensions):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.scale = (dimensions[0] / 2, dimensions[1] / 2, dimensions[2] / 2)

# Create three rectangular prisms stacked on top of each other
create_prism(location=(0, 0, 1), dimensions=(2, 1, 2))  # Bottom prism
create_prism(location=(0, 0, 4), dimensions=(1.5, 1, 1))  # Middle prism
create_prism(location=(0, 0, 6), dimensions=(1, 1, 0.5))  # Top prism
