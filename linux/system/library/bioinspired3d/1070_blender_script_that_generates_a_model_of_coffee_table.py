# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_generates_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that generates a model of coffee table

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Table dimensions
length = 1.0  # 40 inches
width = 0.5   # 20 inches
height = 0.45  # 18 inches
radius = 0.05
leg_height = height - 0.05

# Function to create a cube for the tabletop

def create_tabletop():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, height))
    tabletop = bpy.context.object
    tabletop.scale = (length / 2, width / 2, 0.05)
    tabletop.name = "Tabletop"

# Function to create a leg at a specified position

def create_leg(position, index):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=leg_height, location=position)
    leg = bpy.context.object
    leg.name = f"Leg_{index + 1}"

# Create the tabletop
create_tabletop()

# Positions for the legs
leg_positions = [
    (length / 2 - radius, width / 2 - radius, leg_height / 2),
    (length / 2 - radius, -width / 2 + radius, leg_height / 2),
    (-length / 2 + radius, width / 2 - radius, leg_height / 2),
    (-length / 2 + radius, -width / 2 + radius, leg_height / 2)
]

# Create each leg
for index, position in enumerate(leg_positions):
    create_leg(position, index)
