# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code_construct_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code construct a model of bookshelf.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Shelf dimensions
width = 2
height = 0.1
depth = 0.4
spacing = 0.6
shelves_count = 5
total_shelves_height = shelves_count * spacing

# Function to create a shelf
def create_shelf(index):
    z_position = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f'Shelf_{index + 1}'

# Generate shelves
for idx in range(shelves_count):
    create_shelf(idx)

# Panel dimensions
thickness = 0.05
panel_full_height = total_shelves_height + height

# Function to create a side panel
def create_panel(index):
    x_position = width / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_full_height / 2))
    panel = bpy.context.object
    panel.scale = (thickness / 2, depth / 2, panel_full_height / 2)
    panel.name = f'Side_Panel_{index + 1}'

# Generate side panels
for idx in range(2):
    create_panel(idx)
