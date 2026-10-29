# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_code_to_make_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender code to make a model of bookshelf.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

shelf_dims = {'width': 2, 'height': 0.1, 'depth': 0.4}
shelf_spacing = 0.6
shelf_total_height = 3
number_of_shelves = 5

for index in range(number_of_shelves):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * shelf_spacing))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_dims['width'] / 2, shelf_dims['depth'] / 2, shelf_dims['height'] / 2)
    current_shelf.name = f'Shelf {index + 1}'

side_panel_thickness = 0.05
side_panel_height = shelf_total_height

for side in range(2):
    x_coord = (shelf_dims['width'] / 2) * (side * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_coord, 0, side_panel_height / 2 - shelf_dims['height'] / 2))
    side_panel = bpy.context.object
    side_panel.scale = (side_panel_thickness / 2, shelf_dims['depth'] / 2, side_panel_height / 2)
    side_panel.name = f'Side Panel {side + 1}'
