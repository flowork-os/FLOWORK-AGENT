# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_Python_script__create_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender Python script, create dining table

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a rectangular tabletop
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
table_surface = bpy.context.object
# Adjust the dimensions of the tabletop
table_surface.scale[0] = 2.0  # Length
table_surface.scale[1] = 1.0  # Width
table_surface.scale[2] = 0.1  # Thickness

# Define leg specifications
height_of_legs = 1.0
radius_of_legs = 0.1
positions_of_legs = [(-1.8, -0.9, height_of_legs / 2), (1.8, -0.9, height_of_legs / 2), (-1.8, 0.9, height_of_legs / 2), (1.8, 0.9, height_of_legs / 2)]

# Generate the legs using a loop
for i, position in enumerate(positions_of_legs):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_legs, depth=height_of_legs, location=position)
    leg_object = bpy.context.object
    leg_object.name = f'Leg_{i + 1}'
