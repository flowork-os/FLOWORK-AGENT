# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_bookshelf_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make bookshelf in code in Blender

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Constants for shelf dimensions
WIDTH = 2.0
HEIGHT = 0.1
DEPTH = 0.4
SPACING = 0.6
SHELF_COUNT = 5

# Create shelves using a function

def add_shelves():
    for i in range(SHELF_COUNT):
        z_position = i * SPACING
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        shelf = bpy.context.object
        shelf.scale = (WIDTH / 2, DEPTH / 2, HEIGHT / 2)
        shelf.name = f'Shelf_{i + 1}'

# Generate shelves
add_shelves()

# Function to create side panels

def add_side_panels():
    thickness = 0.05
    height = SHELF_COUNT * SPACING
    for i in range(2):
        x_position = WIDTH / 2 * (i * 2 - 1)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, height / 2))
        panel = bpy.context.object
        panel.scale = (thickness / 2, DEPTH / 2, height / 2)
        panel.name = f'SidePanel_{i + 1}'

# Create the side panels
add_side_panels()
