# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_code_that_creates_food_processor" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender code that creates food processor.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a mesh object with specific parameters

def create_mesh(primitive_type, size, location, name):
    if primitive_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    elif primitive_type == 'plane':
        bpy.ops.mesh.primitive_plane_add(size=size, location=location)
    elif primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=size[0], depth=size[1], location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

# Create the base of the model
base = create_mesh('cube', 2, (0, 0, -1), 'Base')

# Create the control panel
control_panel = create_mesh('plane', 0.5, (0, 1.01, -0.75), 'Control Panel')

# Create the bowl
bowl = create_mesh('cylinder', (0.7, 1.2), (0, 0, 0.6), 'Bowl')

# Create the lid
lid = create_mesh('cylinder', (0.75, 0.1), (0, 0, 1.3), 'Lid')

# Create the feeding tube
feeding_tube = create_mesh('cylinder', (0.2, 0.6), (0, 0.6, 1.5), 'Feeding Tube')
