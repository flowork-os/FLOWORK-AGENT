# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_to_make_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code to make bookshelf.

import bpy

# Clear existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
shelf_material = bpy.data.materials.new(name='ShelfMaterial')
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color resembling wood

# Function to add shelves

def add_shelves(num, width, depth, height, spacing):
    for index in range(num):
        position_z = (index + 1) * spacing
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, position_z))
        shelf = bpy.context.object
        shelf.scale = (width, depth, height)
        shelf.name = f'Shelf_{index + 1}'
        shelf.data.materials.append(shelf_material)

# Shelf dimensions
shelf_height = 0.1
shelf_width = 1.0
shelf_depth = 0.3
num_shelves = 5
full_height = 2.0
spacing_between = full_height / (num_shelves + 1)

# Add shelves to the scene
add_shelves(num_shelves, shelf_width, shelf_depth, shelf_height, spacing_between)

# Function to create panels

def create_panel(location, scale, name):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    panel = bpy.context.object
    panel.scale = scale
    panel.name = name
    panel.data.materials.append(shelf_material)

# Panel dimensions
panel_thickness = 0.05
panel_height = full_height + 2 * shelf_height
panel_depth = shelf_depth + 2 * panel_thickness

# Create side panels
create_panel((-shelf_width / 2 - panel_thickness / 2, 0, full_height / 2), (panel_thickness, panel_depth, panel_height), 'Left_Panel')
create_panel((shelf_width / 2 + panel_thickness / 2, 0, full_height / 2), (panel_thickness, panel_depth, panel_height), 'Right_Panel')

# Create the back panel
create_panel((0, -shelf_depth / 2 - panel_thickness / 2, full_height / 2), (shelf_width + 2 * panel_thickness, panel_thickness, panel_height), 'Back_Panel')


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
