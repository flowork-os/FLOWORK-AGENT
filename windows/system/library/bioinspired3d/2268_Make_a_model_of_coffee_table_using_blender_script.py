# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_coffee_table_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of coffee table using blender script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_scaled_cube(size, location, scale_factors, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale_factors
    cube.name = name
    return cube

create_scaled_cube(2, (0, 0, 0.5), (1.5, 0.75, 0.1), 'Tabletop')

def create_leg(location, radius, height, index):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=location)
    leg = bpy.context.object
    leg.name = f'Leg {index}'

leg_height = 0.5
leg_radius = 0.05
leg_positions = [(-1.4, -0.7, leg_height / 2), (1.4, -0.7, leg_height / 2), (-1.4, 0.7, leg_height / 2), (1.4, 0.7, leg_height / 2)]

for index, position in enumerate(leg_positions):
    create_leg(position, leg_radius, leg_height, index + 1)
