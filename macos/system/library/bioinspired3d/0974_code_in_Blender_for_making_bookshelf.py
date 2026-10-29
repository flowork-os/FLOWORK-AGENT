# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_making_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for making bookshelf

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Shelf configuration
shelf_width = 1.0
shelf_height = 0.1
shelf_depth = 0.5
shelf_length = 3.0
spacing_between_shelves = 1.0
number_of_shelves = 4
overall_height = number_of_shelves * spacing_between_shelves

# Material setup
wood_texture = bpy.data.materials.new(name="WoodTexture")
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create shelves using a loop
for index in range(number_of_shelves):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing_between_shelves))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_length / 2, shelf_depth / 2, shelf_height / 2)
    current_shelf.name = f"Shelf_{index + 1}"
    current_shelf.data.materials.append(wood_texture)

# Create vertical sides
for index in range(2):
    x_coordinate = (shelf_length / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_coordinate, 0, overall_height / 2))
    vertical_side = bpy.context.object
    vertical_side.scale = (0.05, shelf_depth / 2, overall_height / 2)
    vertical_side.name = f"VerticalSide_{index + 1}"
    vertical_side.data.materials.append(wood_texture)


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
