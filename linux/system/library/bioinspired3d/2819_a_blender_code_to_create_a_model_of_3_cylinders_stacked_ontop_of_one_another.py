# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_create_a_model_of_3_cylinders_stacked_ontop_of_one_another" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to create a model of 3 cylinders stacked ontop of one another

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a cylinder
def create_cylinder(location, radius=1, depth=2):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)

# Create three cylinders stacked on top of each other
create_cylinder(location=(0, 0, 1))  # Bottom cylinder
create_cylinder(location=(0, 0, 3))  # Middle cylinder
create_cylinder(location=(0, 0, 5))  # Top cylinder
