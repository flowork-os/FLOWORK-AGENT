# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_code_in_Blender_that_builds_a_model_of_3_cylinders_stacked_ontop_of_one" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate code in Blender that builds a model of 3 cylinders stacked ontop of one another

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a cylinder
def create_cylinder(name, radius, depth, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name

# Create three cylinders stacked on top of each other
create_cylinder("Cylinder_1", 1, 2, (0, 0, 1))
create_cylinder("Cylinder_2", 1, 2, (0, 0, 3))
create_cylinder("Cylinder_3", 1, 2, (0, 0, 5))
