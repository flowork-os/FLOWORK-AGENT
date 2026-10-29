# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_constructing_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for constructing a model of bookshelf.

import bpy

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Constants for the shelf
shelf_length = 2
shelf_thickness = 0.1
shelf_depth = 0.4
shelf_gap = 0.6
number_of_shelves = 5
full_height = number_of_shelves * shelf_gap

# Create shelves in the scene
for i in range(number_of_shelves):
    height_position = i * shelf_gap
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, height_position))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_length / 2, shelf_depth / 2, shelf_thickness / 2)
    current_shelf.name = f'Shelf_{i + 1}'

# Define side panel dimensions
panel_width = 0.05
panel_total_height = full_height + shelf_thickness

# Create side panels
for i in range(2):
    x_position = shelf_length / 2 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_total_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_width / 2, shelf_depth / 2, panel_total_height / 2)
    side_panel.name = f'Side_Panel_{i + 1}'
