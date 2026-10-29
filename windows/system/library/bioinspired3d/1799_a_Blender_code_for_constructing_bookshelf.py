# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_constructing_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for constructing bookshelf

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Constants for shelf and support dimensions
shelf_w = 2.0
shelf_h = 0.1
shelf_d = 0.4
spacing_between_shelves = 0.6
total_shelves = 3
support_radius = 0.05
support_height = total_shelves * spacing_between_shelves

# Create shelves using a loop
for i in range(total_shelves):
    z_position = i * spacing_between_shelves
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_w / 2, shelf_d / 2, shelf_h / 2)
    current_shelf.name = f'Shelf_{i + 1}'

# Generate vertical supports
for j in range(4):
    x_pos = shelf_w / 2 * (1 if j % 2 == 0 else -1)
    y_pos = shelf_d / 2 * (1 if j // 2 == 0 else -1)
    bpy.ops.mesh.primitive_cylinder_add(radius=support_radius, depth=support_height, location=(x_pos, y_pos, support_height / 2))
    current_support = bpy.context.object
    current_support.name = f'Support_{j + 1}'
