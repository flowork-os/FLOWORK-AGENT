# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_script__build_stack_of_three_rectangular_prisms" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender script, build stack of three rectangular prisms

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a rectangular prism
def create_prism(location, dimensions):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.scale = (dimensions[0] / 2, dimensions[1] / 2, dimensions[2] / 2)

# Create three rectangular prisms stacked on top of each other
create_prism(location=(0, 0, 1), dimensions=(2, 1, 2))  # Bottom prism
create_prism(location=(0, 0, 3), dimensions=(1.5, 1, 1.5))  # Middle prism
create_prism(location=(0, 0, 4.5), dimensions=(1, 1, 1))  # Top prism
