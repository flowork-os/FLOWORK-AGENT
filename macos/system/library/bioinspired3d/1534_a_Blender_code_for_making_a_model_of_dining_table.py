# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_making_a_model_of_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for making a model of dining table

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_tabletop(size, location):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    tabletop = bpy.context.object
    tabletop.scale = (2, 1, 0.1)
    tabletop.name = 'Tabletop'

def create_leg(location, radius, height, index):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=location)
    leg = bpy.context.object
    leg.name = f'Leg {index}'

create_tabletop(2, (0, 0, 1))

leg_height = 1
leg_radius = 0.1
leg_positions = [(-1.8, -0.9, leg_height / 2), (1.8, -0.9, leg_height / 2), (-1.8, 0.9, leg_height / 2), (1.8, 0.9, leg_height / 2)]

for index, position in enumerate(leg_positions):
    create_leg(position, leg_radius, leg_height, index + 1)
