# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_bookshelf_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of bookshelf using blender script

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Constants for the shelf dimensions
shelf_w = 2.0
shelf_h = 0.1
shelf_d = 0.4
spacing_between_shelves = 0.6
total_shelves = 5
panel_thickness = 0.1

# Create wood material
wood_mat = bpy.data.materials.new(name="WoodMaterial")
wood_mat.diffuse_color = (0.55, 0.27, 0.07, 1)

# Generate shelves
for idx in range(total_shelves):
    height_position = idx * spacing_between_shelves
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, height_position))
    shelf_obj = bpy.context.object
    shelf_obj.scale = (shelf_w / 2, shelf_d / 2, shelf_h / 2)
    shelf_obj.name = f"Shelf_{idx + 1}"
    shelf_obj.data.materials.append(wood_mat)

# Generate side panels
for idx in range(2):
    pos_x = shelf_w / 2 * (idx * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(pos_x, 0, (total_shelves * spacing_between_shelves) / 2))
    side_obj = bpy.context.object
    side_obj.scale = (panel_thickness / 2, shelf_d / 2, (total_shelves * spacing_between_shelves) / 2)
    side_obj.name = f"Side_{idx + 1}"
    side_obj.data.materials.append(wood_mat)


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
