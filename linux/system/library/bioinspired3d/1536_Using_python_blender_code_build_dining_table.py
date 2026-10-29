# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_python_blender_code_build_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using python blender code build dining table.

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the main tabletop using a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
tabletop_object = bpy.context.object
# Set the scale for the tabletop
tabletop_object.scale = (2, 1, 0.1)

# Create legs for the table
legs_data = [(-1.8, -0.9, 0.5), (1.8, -0.9, 0.5), (-1.8, 0.9, 0.5), (1.8, 0.9, 0.5)]
leg_height = 1.0
leg_radius = 0.1

# Function to add a leg
def add_leg(pos, radius, height):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=pos)
    return bpy.context.object

# Loop through positions to create each leg
for index, position in enumerate(legs_data):
    leg_instance = add_leg(position, leg_radius, leg_height)
    leg_instance.name = f'Leg_{index + 1}'
