# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_bookshelf_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of bookshelf in blender script

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Shelf specifications
width = 2
height = 0.1
depth = 0.4
spacing = 0.6
total_shelves_height = 3
shelves_count = 5

# Function to create shelves
def create_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f'Shelf {index + 1}'

# Create all shelves
for i in range(shelves_count):
    create_shelf(i)

# Panel specifications
thickness = 0.05
panel_full_height = total_shelves_height

# Function to create side panels
def create_panel(index):
    x_position = (width / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_full_height / 2 - height / 2))
    panel = bpy.context.object
    panel.scale = (thickness / 2, depth / 2, panel_full_height / 2)
    panel.name = f'Side Panel {index + 1}'

# Create side panels
for i in range(2):
    create_panel(i)
