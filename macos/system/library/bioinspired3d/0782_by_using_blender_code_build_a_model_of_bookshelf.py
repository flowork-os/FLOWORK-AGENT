# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_code_build_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender code build a model of bookshelf.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Constants for shelf dimensions
WIDTH = 2
HEIGHT = 0.1
DEPTH = 0.4
SPACING = 0.6
TOTAL_HEIGHT = 3
NUM_SHELVES = 5

# Function to add a shelf
def add_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * SPACING))
    shelf_obj = bpy.context.object
    shelf_obj.scale = (WIDTH / 2, DEPTH / 2, HEIGHT / 2)
    shelf_obj.name = f'Shelf {index + 1}'

# Create shelves
for i in range(NUM_SHELVES):
    add_shelf(i)

# Panel parameters
PANEL_THICKNESS = 0.05

# Function to create side panels

def add_side_panel(index):
    x_position = (WIDTH / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, TOTAL_HEIGHT / 2 - HEIGHT / 2))
    panel_obj = bpy.context.object
    panel_obj.scale = (PANEL_THICKNESS / 2, DEPTH / 2, TOTAL_HEIGHT / 2)
    panel_obj.name = f'Side Panel {index + 1}'

# Create side panels
for i in range(2):
    add_side_panel(i)
