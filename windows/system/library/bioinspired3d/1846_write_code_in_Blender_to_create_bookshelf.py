# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_code_in_Blender_to_create_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write code in Blender to create bookshelf.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
shelf_material = bpy.data.materials.new(name='ShelfMaterial')
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color resembling wood

# Function to create shelves
def create_shelf(index, height, depth, width, spacing):
    z_position = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f'Shelf_{index + 1}'
    shelf.data.materials.append(shelf_material)

# Parameters for shelves
shelf_height = 0.1
shelf_depth = 0.3
shelf_width = 0.5
shelf_spacing = 0.4
number_of_shelves = 4

# Create shelves
for i in range(number_of_shelves):
    create_shelf(i, shelf_height, shelf_depth, shelf_width, shelf_spacing)

# Create side panels
side_panel_thickness = 0.05
side_panel_height = number_of_shelves * shelf_spacing

for j in range(2):
    x_position = (shelf_width / 2) * (j * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, side_panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (side_panel_thickness / 2, shelf_depth / 2, side_panel_height / 2)
    side_panel.name = f'SidePanel_{j + 1}'
    side_panel.data.materials.append(shelf_material)


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
