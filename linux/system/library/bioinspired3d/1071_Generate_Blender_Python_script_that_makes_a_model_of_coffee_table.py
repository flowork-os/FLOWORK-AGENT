# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_that_makes_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script that makes a model of coffee table

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Dimensions for the table
TABLE_LENGTH = 1.0  # 40 inches
TABLE_WIDTH = 0.5   # 20 inches
TABLE_HEIGHT = 0.45  # 18 inches
LEG_RADIUS = 0.05
LEG_HEIGHT = TABLE_HEIGHT - 0.05

# Create the table top
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, TABLE_HEIGHT))
table_top = bpy.context.object

table_top.scale = (TABLE_LENGTH / 2, TABLE_WIDTH / 2, 0.05)
table_top.name = "Table_Top"

# Define leg positions
leg_positions = [
    (TABLE_LENGTH / 2 - LEG_RADIUS, TABLE_WIDTH / 2 - LEG_RADIUS, LEG_HEIGHT / 2),
    (TABLE_LENGTH / 2 - LEG_RADIUS, -TABLE_WIDTH / 2 + LEG_RADIUS, LEG_HEIGHT / 2),
    (-TABLE_LENGTH / 2 + LEG_RADIUS, TABLE_WIDTH / 2 - LEG_RADIUS, LEG_HEIGHT / 2),
    (-TABLE_LENGTH / 2 + LEG_RADIUS, -TABLE_WIDTH / 2 + LEG_RADIUS, LEG_HEIGHT / 2)
]

# Create the legs
for index, position in enumerate(leg_positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=LEG_RADIUS, depth=LEG_HEIGHT, location=position)
    leg = bpy.context.object
    leg.name = f"Leg_{index + 1}"
