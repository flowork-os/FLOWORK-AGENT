# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_generates_bedside_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that generates bedside table.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Table dimensions in meters
height_of_table = 0.6096  # 2 feet
thickness_of_top = 0.05
height_of_drawer = 0.3
thickness_of_legs = 0.05
size_of_top = 0.6

# Function to create a cube at a specific location with given dimensions
def create_cube(size, location, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    return cube

# Create the table top
create_cube(size_of_top, (0, 0, height_of_table - thickness_of_top / 2), 'Table Top').scale[2] = thickness_of_top / size_of_top

# Generate table legs
for index in range(4):
    leg_x = (size_of_top / 2 - thickness_of_legs / 2) * (1 if index % 2 == 0 else -1)
    leg_y = (size_of_top / 2 - thickness_of_legs / 2) * (1 if index // 2 == 0 else -1)
    leg = create_cube(thickness_of_legs, (leg_x, leg_y, height_of_table / 2), f'Leg {index + 1}')
    leg.scale[2] = (height_of_table - thickness_of_top) / thickness_of_legs

# Create the drawer
create_cube(size_of_top * 0.8, (0, 0, height_of_table - thickness_of_top - height_of_drawer / 2), 'Drawer').scale[2] = height_of_drawer / (size_of_top * 0.8)
