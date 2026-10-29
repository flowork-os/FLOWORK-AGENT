# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_generating_a_model_of_bedside_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for generating a model of bedside table

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Dimensions of the table in meters
TABLE_HEIGHT_M = 0.6096  # 2 feet
TOP_THICKNESS_M = 0.05
DRAWER_HEIGHT_M = 0.3
LEG_THICKNESS_M = 0.05
TOP_SIZE_M = 0.6

# Create the table elements

def build_table():
    # Create the table top
    table_top = bpy.ops.mesh.primitive_cube_add(size=TOP_SIZE_M, location=(0, 0, TABLE_HEIGHT_M - TOP_THICKNESS_M / 2))
    bpy.context.object.name = 'Table Top'
    bpy.context.object.scale[2] = TOP_THICKNESS_M / TOP_SIZE_M

    # Create the legs
    for i in range(4):
        leg_x = (TOP_SIZE_M / 2 - LEG_THICKNESS_M / 2) * (1 if i % 2 == 0 else -1)
        leg_y = (TOP_SIZE_M / 2 - LEG_THICKNESS_M / 2) * (1 if i // 2 == 0 else -1)
        leg = bpy.ops.mesh.primitive_cube_add(size=LEG_THICKNESS_M, location=(leg_x, leg_y, TABLE_HEIGHT_M / 2))
        bpy.context.object.name = f'Leg {i + 1}'
        bpy.context.object.scale[2] = (TABLE_HEIGHT_M - TOP_THICKNESS_M) / LEG_THICKNESS_M

    # Create the drawer
    drawer = bpy.ops.mesh.primitive_cube_add(size=TOP_SIZE_M * 0.8, location=(0, 0, TABLE_HEIGHT_M - TOP_THICKNESS_M - DRAWER_HEIGHT_M / 2))
    bpy.context.object.name = 'Drawer'
    bpy.context.object.scale[2] = DRAWER_HEIGHT_M / (TOP_SIZE_M * 0.8)

build_table()
