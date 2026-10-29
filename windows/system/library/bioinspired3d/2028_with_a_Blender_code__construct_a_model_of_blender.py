# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code__construct_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code, construct a model of blender

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder with specified parameters
def create_cylinder(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the components of the model
base_component = create_cylinder(1, 0.5, (0, 0, 0.25), 'Base')
jar_component = create_cylinder(0.8, 2, (0, 0, 1.5), 'Jar')
lid_component = create_cylinder(0.85, 0.2, (0, 0, 2.6), 'Lid')
