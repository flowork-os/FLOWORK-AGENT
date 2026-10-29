# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_dining_table_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of dining table using blender script

import bpy

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create the main table surface
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.75))
table_surface = bpy.context.object

table_surface.name = 'Main Table'
table_surface.scale[0] = 1.5

table_surface.scale[1] = 0.9

table_surface.scale[2] = 0.05

# Define leg dimensions
height_of_legs = 0.7
radius_of_legs = 0.05
leg_positions = [(-1.4, -0.8), (1.4, -0.8), (-1.4, 0.8), (1.4, 0.8)]

# Generate the legs using a loop
for index, position in enumerate(leg_positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_legs, depth=height_of_legs, location=(position[0], position[1], height_of_legs / 2))
    leg = bpy.context.object
    leg.name = f'Leg {index + 1}'
