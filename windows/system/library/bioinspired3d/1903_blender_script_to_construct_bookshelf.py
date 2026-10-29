# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_construct_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to construct bookshelf

import bpy

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_finish = bpy.data.materials.new(name='WoodFinish')
wood_finish.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf dimensions and properties
shelf_specs = {'width': 0.5, 'height': 0.1, 'depth': 0.2}
spacing_between = 0.4
number_of_shelves = 3

# Function to add shelves
def add_shelves(num):
    for idx in range(num):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, idx * spacing_between))
        shelf_obj = bpy.context.object
        shelf_obj.scale = (shelf_specs['width'] / 2, shelf_specs['depth'] / 2, shelf_specs['height'] / 2)
        shelf_obj.name = f'Shelf_{idx + 1}'
        shelf_obj.data.materials.append(wood_finish)

# Create the shelves
add_shelves(number_of_shelves)

# Panel dimensions
panel_width = 0.05
panel_total_height = number_of_shelves * spacing_between

# Function to add side panels
def add_side_panels():
    for idx in range(2):
        x_offset = shelf_specs['width'] / 2 * (idx * 2 - 1)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x_offset, 0, panel_total_height / 2 - shelf_specs['height'] / 2))
        side_panel_obj = bpy.context.object
        side_panel_obj.scale = (panel_width / 2, shelf_specs['depth'] / 2, panel_total_height / 2)
        side_panel_obj.name = f'SidePanel_{idx + 1}'
        side_panel_obj.data.materials.append(wood_finish)

# Create the side panels
add_side_panels()


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
