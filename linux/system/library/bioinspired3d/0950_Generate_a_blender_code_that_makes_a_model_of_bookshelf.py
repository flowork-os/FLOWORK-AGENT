# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_that_makes_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code that makes a model of bookshelf

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood = bpy.data.materials.new(name='Wooden Finish')
wood.diffuse_color = (0.55, 0.27, 0.07, 1)  # Set to brown

# Function to add a shelf
def add_shelf(level, width, depth, height, spacing, mat):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, level * spacing))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f'Shelf {level + 1}'
    shelf.data.materials.append(mat)

# Shelf parameters
shelf_height = 0.1
shelf_depth = 0.4
shelf_width = 0.6
shelf_spacing = 0.5
num_shelves = 4

# Create shelves
for level in range(num_shelves):
    add_shelf(level, shelf_width, shelf_depth, shelf_height, shelf_spacing, wood)

# Function to add side panel

def add_side_panel(index, thickness, depth, height, mat):
    x_pos = (shelf_width / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_pos, 0, height / 2))
    panel = bpy.context.object
    panel.scale = (thickness / 2, depth / 2, height / 2)
    panel.name = f'Side Panel {index + 1}'
    panel.data.materials.append(mat)

# Side panel parameters
side_panel_thickness = 0.05
side_panel_height = num_shelves * shelf_spacing
for index in range(2):
    add_side_panel(index, side_panel_thickness, shelf_depth, side_panel_height, wood)


# --- 3DCodeVerse geo variant: neutralize materials (auto-derived, do not edit) ---
import bpy as _bpy_geo
_geo_mat = _bpy_geo.data.materials.get("geo_neutral") or _bpy_geo.data.materials.new("geo_neutral")
try:
    _geo_mat.use_nodes = False
except Exception:
    pass
try:
    _geo_mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
except Exception:
    pass
for _geo_obj in list(_bpy_geo.data.objects):
    if _geo_obj.type == "MESH" and _geo_obj.data is not None:
        try:
            _geo_obj.data.materials.clear()
            _geo_obj.data.materials.append(_geo_mat)
        except Exception:
            pass
# --- end geo variant ---
