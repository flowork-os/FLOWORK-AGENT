# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_creates_a_model_of_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that creates a model of dining table.

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cube
def add_cube(size, location, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    return cube

# Create the table surface
surface = add_cube(2, (0, 0, 0.75), 'Table Surface')
surface.scale = (1.5, 0.9, 0.05)

# Function to create a leg
def add_leg(radius, height, position, leg_number):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    leg = bpy.context.object
    leg.name = f'Leg {leg_number}'

# Define leg parameters
leg_height = 0.7
leg_radius = 0.05
leg_positions = [(-1.4, -0.8, leg_height / 2), (1.4, -0.8, leg_height / 2), (-1.4, 0.8, leg_height / 2), (1.4, 0.8, leg_height / 2)]

# Create table legs
for index, pos in enumerate(leg_positions):
    add_leg(leg_radius, leg_height, pos, index + 1)
