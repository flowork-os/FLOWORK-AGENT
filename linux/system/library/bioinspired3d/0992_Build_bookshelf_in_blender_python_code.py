# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_bookshelf_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build bookshelf in blender python code

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the shelves
shelf_material = bpy.data.materials.new(name='ShelfMaterial')
shelf_material.diffuse_color = (0.54, 0.26, 0.06, 1)  # Slightly different wood color

# Shelf dimensions and settings
height_of_shelf = 0.1
width_of_shelf = 0.6
depth_of_shelf = 0.4
spacing_between_shelves = 0.5
number_of_shelves = 4

# Function to create shelves

def create_shelf(index):
    z_position = index * spacing_between_shelves
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    current_shelf = bpy.context.object
    current_shelf.scale = (width_of_shelf / 2, depth_of_shelf / 2, height_of_shelf / 2)
    current_shelf.name = f'Shelf_{index + 1}'
    current_shelf.data.materials.append(shelf_material)

# Create all shelves
for index in range(number_of_shelves):
    create_shelf(index)

# Side panel dimensions
panel_width = 0.05
panel_total_height = number_of_shelves * spacing_between_shelves

# Function to create side panels

def create_panel(side):
    x_position = width_of_shelf / 2 * (side * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_total_height / 2))
    current_panel = bpy.context.object
    current_panel.scale = (panel_width / 2, depth_of_shelf / 2, panel_total_height / 2)
    current_panel.name = f'SidePanel_{side + 1}'
    current_panel.data.materials.append(shelf_material)

# Create side panels
for side in range(2):
    create_panel(side)


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
