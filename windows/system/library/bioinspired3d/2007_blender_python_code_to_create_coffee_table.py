# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_create_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to create coffee table

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

length = 1.0  # 40 inches
width = 0.5   # 20 inches
height = 0.45  # 18 inches
radius = 0.05
leg_height = height - 0.05

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, height))
table_top = bpy.context.object
table_top.scale = (length / 2, width / 2, 0.05)
table_top.name = "Tabletop"

def add_legs():
    positions = [
        (length / 2 - radius, width / 2 - radius, leg_height / 2),
        (length / 2 - radius, -width / 2 + radius, leg_height / 2),
        (-length / 2 + radius, width / 2 - radius, leg_height / 2),
        (-length / 2 + radius, -width / 2 + radius, leg_height / 2)
    ]
    for i, pos in enumerate(positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=leg_height, location=pos)
        leg = bpy.context.object
        leg.name = f"TableLeg_{i + 1}"

add_legs()
