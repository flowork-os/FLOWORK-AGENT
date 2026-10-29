# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_bookshelf_using_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create bookshelf using blender python code

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Parameters for the shelf structure
shelf_dim_x = 2.0
shelf_dim_y = 0.1
shelf_dim_z = 0.4
vertical_spacing = 0.6
shelf_quantity = 3
support_thickness = 0.05
support_full_height = shelf_quantity * vertical_spacing

# Create shelves in a single function
for level in range(shelf_quantity):
    position_z = level * vertical_spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, position_z))
    shelf_item = bpy.context.object
    shelf_item.scale = (shelf_dim_x / 2, shelf_dim_z / 2, shelf_dim_y / 2)
    shelf_item.name = f'Shelf_{level + 1}'

# Creating supports using a loop
for support_index in range(4):
    x_coord = shelf_dim_x / 2 * (1 if support_index % 2 == 0 else -1)
    y_coord = shelf_dim_z / 2 * (1 if support_index // 2 == 0 else -1)
    bpy.ops.mesh.primitive_cylinder_add(radius=support_thickness, depth=support_full_height, location=(x_coord, y_coord, support_full_height / 2))
    support_item = bpy.context.object
    support_item.name = f'Support_{support_index + 1}'
