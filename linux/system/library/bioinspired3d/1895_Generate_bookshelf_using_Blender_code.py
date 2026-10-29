# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_bookshelf_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate bookshelf using Blender code

import bpy

# Clear the scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Shelf parameters
shelf_w = 2
shelf_h = 0.1
shelf_d = 0.4
spacing_between_shelves = 0.6
shelves_total = 5
shelves_full_height = shelves_total * spacing_between_shelves

# Create shelves using a loop
for idx in range(shelves_total):
    z_position = idx * spacing_between_shelves
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf_object = bpy.context.object
    shelf_object.scale = (shelf_w / 2, shelf_d / 2, shelf_h / 2)
    shelf_object.name = f'Shelf_{idx + 1}'

# Panel specifications
side_panel_thickness = 0.05
side_panel_height = shelves_full_height + shelf_h

# Create side panels
for idx in range(2):
    x_position = shelf_w / 2 * (idx * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, side_panel_height / 2))
    side_panel_object = bpy.context.object
    side_panel_object.scale = (side_panel_thickness / 2, shelf_d / 2, side_panel_height / 2)
    side_panel_object.name = f'Side_Panel_{idx + 1}'
