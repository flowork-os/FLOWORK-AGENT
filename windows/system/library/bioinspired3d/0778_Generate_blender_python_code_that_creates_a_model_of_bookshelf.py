# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_that_creates_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code that creates a model of bookshelf

import bpy

# Remove all mesh objects from the active scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Shelf parameters
shelf_width = 2.0
shelf_height = 0.1
shelf_depth = 0.4
shelf_spacing = 0.6
number_of_shelves = 5
side_panel_thickness = 0.1

# Material setup for wood
wood_texture = bpy.data.materials.new(name="WoodTexture")
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create shelves in a more structured way
for shelf_index in range(number_of_shelves):
    z_position = shelf_index * shelf_spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_width / 2, shelf_depth / 2, shelf_height / 2)
    current_shelf.name = f"Shelf_{shelf_index + 1}"
    current_shelf.data.materials.append(wood_texture)

# Create vertical side pieces
for side_index in range(2):
    x_position = shelf_width / 2 * (side_index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, (number_of_shelves * shelf_spacing) / 2))
    current_side = bpy.context.object
    current_side.scale = (side_panel_thickness / 2, shelf_depth / 2, (number_of_shelves * shelf_spacing) / 2)
    current_side.name = f"Side_{side_index + 1}"
    current_side.data.materials.append(wood_texture)


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
