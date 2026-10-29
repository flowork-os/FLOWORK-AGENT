# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_to_create_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender to create a model of bookshelf.

import bpy

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Constants for shelf dimensions
SHELF_WIDTH = 2.0
SHELF_HEIGHT = 0.1
SHELF_DEPTH = 0.5
SHELF_SPACING = 1.0
TILT_ANGLE = 0.1  # Tilt in radians

# Create shelves using a loop
for index in range(3):
    position_z = index * SHELF_SPACING
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, position_z))
    current_shelf = bpy.context.object
    current_shelf.scale = (SHELF_WIDTH, SHELF_DEPTH, SHELF_HEIGHT)
    current_shelf.rotation_euler = (TILT_ANGLE, 0, 0)
    current_shelf.name = f'Shelf_{index + 1}'

# Panel dimensions
PANEL_THICKNESS = 0.1
PANEL_HEIGHT = 3 * SHELF_SPACING
PANEL_DEPTH = SHELF_DEPTH + 0.2

# Create side panels
for index in range(2):
    position_x = (SHELF_WIDTH / 2 + PANEL_THICKNESS / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(position_x, 0, PANEL_HEIGHT / 2 - SHELF_HEIGHT / 2))
    current_panel = bpy.context.object
    current_panel.scale = (PANEL_THICKNESS, PANEL_DEPTH, PANEL_HEIGHT)
    current_panel.name = f'Side_Panel_{index + 1}'
