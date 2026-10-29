# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code__create_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code, create bookshelf.

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the shelves
shelf_material = bpy.data.materials.new(name="ShelfMaterial")
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Wood-like color

# Shelf dimensions
width = 2
height = 0.1
depth = 0.4
spacing = 0.5
shelf_count = 5
full_height = shelf_count * spacing

# Function to create a shelf
def create_shelf(index):
    z_position = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f"Shelf_{index + 1}"
    shelf.data.materials.append(shelf_material)

# Create shelves using the helper function
for i in range(shelf_count):
    create_shelf(i)

# Panel properties
panel_width = 0.05
panel_full_height = full_height

# Function to create a side panel
def create_panel(side):
    x_position = width / 2 * (side * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_full_height / 2))
    panel = bpy.context.object
    panel.scale = (panel_width / 2, depth / 2, panel_full_height / 2)
    panel.name = f"SidePanel_{side + 1}"
    panel.data.materials.append(shelf_material)

# Create side panels
for j in range(2):
    create_panel(j)


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
