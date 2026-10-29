# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_bookcase_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct bookcase in Blender code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the shelves
shelf_material = bpy.data.materials.new(name='Shelf Material')
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf dimensions
shelf_width = 2.0
shelf_thickness = 0.1
shelf_length = 0.4
shelf_gap = 0.5
number_of_shelves = 3

# Create shelves in a loop
for index in range(number_of_shelves):
    position_z = index * shelf_gap
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, position_z))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_width / 2, shelf_length / 2, shelf_thickness / 2)
    current_shelf.name = f'Shelf {index + 1}'
    current_shelf.data.materials.append(shelf_material)

# Add the top surface
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, number_of_shelves * shelf_gap))
top_surface = bpy.context.object
top_surface.scale = (shelf_width / 2, shelf_length / 2, 0.05)
top_surface.name = 'Top Surface'
top_surface.data.materials.append(shelf_material)

# Create side panels
panel_width = 0.05
panel_height = number_of_shelves * shelf_gap
for index in range(2):
    position_x = shelf_width / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(position_x, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_width / 2, shelf_length / 2, panel_height / 2)
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
