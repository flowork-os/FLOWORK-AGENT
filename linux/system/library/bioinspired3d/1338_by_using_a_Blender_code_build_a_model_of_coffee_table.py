# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code_build_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code build a model of coffee table

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the main components of the table

def build_table():
    # Add the table surface
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
    surface = bpy.context.object
    surface.scale[0] = 1.5
    surface.scale[1] = 0.75
    surface.scale[2] = 0.1
    surface.name = 'Table Surface'

    # Add the legs at specified positions
    leg_height = 0.5
    leg_radius = 0.05
    leg_positions = [(-1.4, -0.7, leg_height / 2), (1.4, -0.7, leg_height / 2), (-1.4, 0.7, leg_height / 2), (1.4, 0.7, leg_height / 2)]

    for index, position in enumerate(leg_positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=position)
        leg = bpy.context.object
        leg.name = f'Leg {index + 1}'

# Execute the table building function
build_table()
