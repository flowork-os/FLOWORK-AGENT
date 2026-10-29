# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code_make_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code make a model of bookshelf.

import bpy

# Start by clearing the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define material for the shelves
material_wood = bpy.data.materials.new(name="MaterialWood")
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf specifications
shelf_width = 2.0
shelf_height = 0.1
shelf_depth = 0.4
shelf_spacing = 0.6
number_of_shelves = 5

# Create shelves using a loop
for index in range(number_of_shelves):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * shelf_spacing))
    new_shelf = bpy.context.object
    new_shelf.scale = (shelf_width / 2, shelf_depth / 2, shelf_height / 2)
    new_shelf.name = f"Shelf_{index + 1}"
    new_shelf.data.materials.append(material_wood)

# Side dimensions
side_width = 0.05
full_shelf_height = number_of_shelves * shelf_spacing

# Create the vertical sides
for side_index in range(2):
    position_x = (shelf_width / 2) * (side_index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(position_x, 0, full_shelf_height / 2))
    new_side = bpy.context.object
    new_side.scale = (side_width / 2, shelf_depth / 2, full_shelf_height / 2)
    new_side.name = f"Side_{side_index + 1}"
    new_side.data.materials.append(material_wood)


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
