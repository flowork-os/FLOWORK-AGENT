# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code_generate_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code generate bookshelf

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf parameters
shelf_width = 2.0
shelf_height = 0.1
shelf_depth = 0.4
shelf_gap = 0.5
number_of_shelves = 5
shelf_total_height = number_of_shelves * shelf_gap

# Create shelves using a loop
for index in range(number_of_shelves):
    z_position = index * shelf_gap
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, z_position))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_width / 2, shelf_depth / 2, shelf_height / 2)
    current_shelf.name = f'Shelf_{index + 1}'
    current_shelf.data.materials.append(wood_material)

# Create side panels
for side in range(2):
    x_position = (shelf_width / 2) * (side * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(x_position, 0, shelf_total_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (0.025, shelf_depth / 2, shelf_total_height / 2)
    side_panel.name = f'SidePanel_{side + 1}'
    side_panel.data.materials.append(wood_material)


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
