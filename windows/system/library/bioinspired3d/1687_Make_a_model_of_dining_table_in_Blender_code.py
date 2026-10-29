# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_dining_table_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of dining table in Blender code

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the rectangular table surface
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.75))
table_surface = bpy.context.object

# Adjust the scale for the table surface
bpy.ops.transform.resize(value=(1.5, 1, 0.1))
table_surface.name = 'Surface'

# Define parameters for the legs
height_of_leg = 0.7
radius_of_leg = 0.05
positions_of_legs = [(-1.4, -0.9, 0), (1.4, -0.9, 0), (-1.4, 0.9, 0), (1.4, 0.9, 0)]

# Create each leg at specified positions
for index, position in enumerate(positions_of_legs):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_leg, depth=height_of_leg, location=(position[0], position[1], height_of_leg / 2))
    bpy.context.object.name = f'Leg_{index + 1}'
