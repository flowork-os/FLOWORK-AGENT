# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_dining_table_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of dining table in a blender code

import bpy

# Clear existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cube for the table top
def create_table_top(size, location):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    top = bpy.context.object
    top.scale = (1.5, 1, 0.1)  # Rectangular shape
    top.name = 'Table Surface'

# Function to create table legs
def create_leg(location, radius, height):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=(location[0], location[1], height / 2))
    leg = bpy.context.object
    leg.name = f'Leg {location}'

# Step 1: Create the table top
create_table_top(size=2, location=(0, 0, 0.75))

# Step 2: Define leg parameters
leg_height = 0.7
leg_radius = 0.05
leg_positions = [(-1.4, -0.9, 0), (1.4, -0.9, 0), (-1.4, 0.9, 0), (1.4, 0.9, 0)]

# Step 3: Create each leg using the defined function
for position in leg_positions:
    create_leg(location=position, radius=leg_radius, height=leg_height)
