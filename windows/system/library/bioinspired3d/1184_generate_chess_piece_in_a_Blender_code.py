# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_chess_piece_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate chess piece in a Blender code

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder at a specified location

def create_cylinder(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the main components of the model
base = create_cylinder(1, 0.2, (0, 0, 0), 'Base')
body = create_cylinder(0.6, 1.5, (0, 0, 0.85), 'Body')
neck = create_cylinder(0.4, 0.3, (0, 0, 1.85), 'Neck')

# Create the head using a UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 2.3))
head = bpy.context.object
head.name = 'Head'
