# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_bookshelf_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct bookshelf using Blender code

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Shelf dimensions and parameters
width = 2.0
height = 0.1
depth = 0.4
spacing = 0.6
shelf_count = 3
support_diameter = 0.1
support_length = shelf_count * spacing

# Function to create shelves

def create_shelves(count, width, depth, height, spacing):
    for index in range(count):
        z_position = index * spacing
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        shelf = bpy.context.object
        shelf.scale = (width / 2, depth / 2, height / 2)
        shelf.name = f'Shelf_{index + 1}'

# Create shelves
create_shelves(shelf_count, width, depth, height, spacing)

# Function to create supports

def create_supports(count, width, depth, height):
    for index in range(count):
        x_position = width / 2 * (1 if index % 2 == 0 else -1)
        y_position = depth / 2 * (1 if index // 2 == 0 else -1)
        bpy.ops.mesh.primitive_cylinder_add(radius=support_diameter / 2, depth=height, location=(x_position, y_position, height / 2))
        support = bpy.context.object
        support.name = f'Support_{index + 1}'

# Create supports
create_supports(4, width, depth, support_length)
