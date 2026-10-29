# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_python_blender_code__create_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with python blender code, create a model of bookshelf.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the shelves
shelf_material = bpy.data.materials.new(name="ShelfMaterial")
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color resembling wood

# Shelf dimensions and settings
height_of_shelf = 0.1
shelf_depth = 0.4
shelf_width = 0.8
spacing_between_shelves = 0.6
number_of_shelves = 5

# Function to create a shelf
def create_shelf(index):
    z_position = index * spacing_between_shelves
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_width / 2, shelf_depth / 2, height_of_shelf / 2)
    current_shelf.name = f"Shelf {index + 1}"
    current_shelf.data.materials.append(shelf_material)

# Create all shelves
for idx in range(number_of_shelves):
    create_shelf(idx)

# Dimensions for side panels
thickness_of_panel = 0.05
height_of_panels = number_of_shelves * spacing_between_shelves

# Function to create a side panel
def create_panel(index):
    x_position = (shelf_width / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, height_of_panels / 2))
    current_panel = bpy.context.object
    current_panel.scale = (thickness_of_panel / 2, shelf_depth / 2, height_of_panels / 2)
    current_panel.name = f"Side Panel {index + 1}"
    current_panel.data.materials.append(shelf_material)

# Create both side panels
for idx in range(2):
    create_panel(idx)


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
