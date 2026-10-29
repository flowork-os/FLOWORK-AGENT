# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_python_code__build_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender python code, build bookshelf.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

shelf_width = 2.0
shelf_height = 0.1
shelf_depth = 0.4
shelf_spacing = 0.6
number_of_shelves = 5

for index in range(number_of_shelves):
    z_position = index * shelf_spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    new_shelf = bpy.context.object
    new_shelf.scale = (shelf_width / 2, shelf_depth / 2, shelf_height / 2)
    new_shelf.name = f'Shelf_{index + 1}'

panel_thickness = 0.05
panel_height = number_of_shelves * shelf_spacing

for index in range(2):
    x_position = (shelf_width / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, shelf_depth / 2, panel_height / 2)
    side_panel.name = f'SidePanel_{index + 1}'
