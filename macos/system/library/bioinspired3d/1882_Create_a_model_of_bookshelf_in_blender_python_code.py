# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_bookshelf_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of bookshelf in blender python code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up shelf parameters
width = 2.0
height = 0.1
depth = 0.4
spacing = 0.6
shelf_count = 5

# Function to create a shelf
def create_shelf(index):
    z_position = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    current_shelf = bpy.context.object
    current_shelf.scale = (width / 2, depth / 2, height / 2)
    current_shelf.name = f'Shelf_{index + 1}'

# Generate shelves
for i in range(shelf_count):
    create_shelf(i)

# Function to create side panels
def create_side_panel(index):
    x_position = width / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, (shelf_count * spacing) / 2))
    current_panel = bpy.context.object
    current_panel.scale = (0.025, depth / 2, (shelf_count * spacing) / 2)
    current_panel.name = f'SidePanel_{index + 1}'

# Create side panels
for i in range(2):
    create_side_panel(i)
