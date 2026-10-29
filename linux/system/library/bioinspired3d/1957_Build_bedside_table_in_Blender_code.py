# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_bedside_table_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build bedside table in Blender code

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

TABLE_HEIGHT = 0.6096  # 2 feet
TOP_THICKNESS = 0.05
DRAWER_HEIGHT = 0.3
LEG_THICKNESS = 0.05
TOP_SIZE = 0.6

def add_cube(size, position, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.name = name
    return cube

add_cube(TOP_SIZE, (0, 0, TABLE_HEIGHT - TOP_THICKNESS / 2), 'Table Top').scale[2] = TOP_THICKNESS / TOP_SIZE

for leg_index in range(4):
    leg_x_position = (TOP_SIZE / 2 - LEG_THICKNESS / 2) * (1 if leg_index % 2 == 0 else -1)
    leg_y_position = (TOP_SIZE / 2 - LEG_THICKNESS / 2) * (1 if leg_index // 2 == 0 else -1)
    leg = add_cube(LEG_THICKNESS, (leg_x_position, leg_y_position, TABLE_HEIGHT / 2), f'Leg {leg_index + 1}')
    leg.scale[2] = (TABLE_HEIGHT - TOP_THICKNESS) / LEG_THICKNESS

add_cube(TOP_SIZE * 0.8, (0, 0, TABLE_HEIGHT - TOP_THICKNESS - DRAWER_HEIGHT / 2), 'Drawer').scale[2] = DRAWER_HEIGHT / (TOP_SIZE * 0.8)
