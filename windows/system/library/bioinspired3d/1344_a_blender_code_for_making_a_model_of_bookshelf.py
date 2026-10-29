# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_making_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for making a model of bookshelf.

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Shelf parameters
shelf_params = {
    'width': 2.0,
    'height': 0.1,
    'depth': 0.5,
    'spacing': 1.0,
    'angle': 0.1
}

# Function to add a shelf

def add_shelf(index):
    z_coord = index * shelf_params['spacing']
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z_coord))
    shelf_object = bpy.context.object
    shelf_object.scale = (shelf_params['width'], shelf_params['depth'], shelf_params['height'])
    shelf_object.rotation_euler = (shelf_params['angle'], 0, 0)
    shelf_object.name = f'Shelf_{index + 1}'

# Create three shelves
for i in range(3):
    add_shelf(i)

# Panel dimensions
panel_dimensions = {
    'thickness': 0.1,
    'height': 3 * shelf_params['spacing'],
    'depth': shelf_params['depth'] + 0.2
}

# Function to add side panels

def add_side_panel(index):
    x_coord = (shelf_params['width'] / 2 + panel_dimensions['thickness'] / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_coord, 0, panel_dimensions['height'] / 2 - shelf_params['height'] / 2))
    panel_object = bpy.context.object
    panel_object.scale = (panel_dimensions['thickness'], panel_dimensions['depth'], panel_dimensions['height'])
    panel_object.name = f'Side_Panel_{index + 1}'

# Create two side panels
for i in range(2):
    add_side_panel(i)
