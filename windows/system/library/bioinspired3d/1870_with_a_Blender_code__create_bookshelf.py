# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code__create_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code, create bookshelf

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define the material for the shelves
shelf_material = bpy.data.materials.new(name='Shelf Material')
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf specifications
shelf_dimensions = {'width': 3, 'height': 0.1, 'depth': 0.5, 'spacing': 1.2}
number_of_shelves = 5

# Create shelves in a loop
for i in range(number_of_shelves):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, i * shelf_dimensions['spacing']))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_dimensions['width'] / 2, shelf_dimensions['depth'] / 2, shelf_dimensions['height'] / 2)
    current_shelf.name = f'Shelf_{i + 1}'
    current_shelf.data.materials.append(shelf_material)

# Create side panels
panel_thickness = 0.05
panel_full_height = (number_of_shelves - 1) * shelf_dimensions['spacing'] + shelf_dimensions['height']

for i in range(2):
    x_position = (shelf_dimensions['width'] / 2) * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_full_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, shelf_dimensions['depth'] / 2, panel_full_height / 2)
    side_panel.name = f'Side_Panel_{i + 1}'
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
