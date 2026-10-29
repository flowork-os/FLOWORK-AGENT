# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_constructing_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for constructing bookshelf

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
shelf_material = bpy.data.materials.new(name='Shelf Material')
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Wood color

# Define dimensions for the shelves
shelf_dimensions = {'height': 0.1, 'depth': 0.4, 'width': 0.6}
spacing = 0.5
shelves_count = 4

# Create shelves using a loop
for index in range(shelves_count):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_dimensions['width'] / 2, shelf_dimensions['depth'] / 2, shelf_dimensions['height'] / 2)
    current_shelf.name = f'Shelf {index + 1}'
    current_shelf.data.materials.append(shelf_material)

# Set side panel parameters
panel_thickness = 0.05
panel_height = shelves_count * spacing

# Create side panels
for index in range(2):
    position_x = (shelf_dimensions['width'] / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(position_x, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, shelf_dimensions['depth'] / 2, panel_height / 2)
    side_panel.name = f'Side Panel {index + 1}'
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
