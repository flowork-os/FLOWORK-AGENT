# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_Blender_code_that_builds_a_model_of_3_cylinders_stacked_ontop_of_one_anot" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a Blender code that builds a model of 3 cylinders stacked ontop of one another.

import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Function to create a cylinder
def create_cylinder(name, radius, depth, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name

# Parameters for the cylinders
radius = 1
depth = 2
offset = depth / 2

# Create three cylinders stacked on top of each other
create_cylinder("Cylinder_1", radius, depth, (0, 0, offset))
create_cylinder("Cylinder_2", radius, depth, (0, 0, offset * 3))
create_cylinder("Cylinder_3", radius, depth, (0, 0, offset * 5))
