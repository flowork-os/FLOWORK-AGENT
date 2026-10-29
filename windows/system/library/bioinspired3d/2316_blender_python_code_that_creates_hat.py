# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_creates_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that creates hat.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder
def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the base of the model
brim_part = create_cylinder(1.5, 0.1, (0, 0, 0), 'Base')

# Create the upper part of the model
crown_part = create_cylinder(0.75, 1, (0, 0, 0.55), 'Top')
