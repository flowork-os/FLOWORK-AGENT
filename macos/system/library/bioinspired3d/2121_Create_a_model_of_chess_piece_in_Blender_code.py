# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_chess_piece_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of chess piece in Blender code

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to add a primitive shape
def add_shape(primitive_type, params, name):
    if primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params[0], depth=params[1], location=params[2])
    elif primitive_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=params[0], location=params[1])
    obj = bpy.context.object
    obj.name = name

# Create the components of the model
add_shape('cylinder', (1, 0.2, (0, 0, 0)), 'Base')
add_shape('cylinder', (0.6, 1.5, (0, 0, 0.85)), 'Body')
add_shape('cylinder', (0.4, 0.3, (0, 0, 1.85)), 'Neck')
add_shape('sphere', (0.5, (0, 0, 2.3)), 'Head')
