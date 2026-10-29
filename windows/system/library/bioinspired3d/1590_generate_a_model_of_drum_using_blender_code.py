# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_drum_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of drum using blender code

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder
def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the main body of the drum
body = create_cylinder(1, 1.5, (0, 0, 0.75), 'Drum Body')

# Create the drumhead
head = create_cylinder(1.05, 0.1, (0, 0, 1.55), 'Drumhead')
