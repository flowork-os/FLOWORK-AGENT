# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_that_makes_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script that makes bookshelf.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Shelf dimensions
width = 2.0
height = 0.1
depth = 0.5
spacing = 1.0
angle = 0.1  # Tilt angle in radians

# Function to create a shelf
def create_shelf(index):
    z_position = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (width, depth, height)
    shelf.rotation_euler = (angle, 0, 0)
    shelf.name = f'Shelf {index + 1}'

# Create shelves
for i in range(3):
    create_shelf(i)

# Side panel dimensions
thickness = 0.1
panel_height = 3 * spacing
panel_depth = depth + 0.2

# Function to create side panels
def create_side_panel(index):
    x_position = (width / 2 + thickness / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_position, 0, panel_height / 2 - height / 2))
    panel = bpy.context.object
    panel.scale = (thickness, panel_depth, panel_height)
    panel.name = f'Side Panel {index + 1}'

# Create side panels
for i in range(2):
    create_side_panel(i)
