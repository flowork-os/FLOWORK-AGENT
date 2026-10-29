# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_bookshelf_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of bookshelf using Blender Python script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

shelf_length = 2.0
shelf_thickness = 0.1
shelf_depth = 0.4
shelf_count = 5
spacing_between_shelves = 0.6

for index in range(shelf_count):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing_between_shelves))
    new_shelf = bpy.context.object
    new_shelf.dimensions = (shelf_length, shelf_depth, shelf_thickness)
    new_shelf.name = f'Shelf_{index + 1}'
    new_shelf.data.materials.append(wood_texture)

panel_width = 0.05
panel_height = shelf_count * spacing_between_shelves

for index in range(2):
    x_pos = (shelf_length / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_pos, 0, panel_height / 2))
    new_panel = bpy.context.object
    new_panel.dimensions = (panel_width, shelf_depth, panel_height)
    new_panel.name = f'Panel_{index + 1}'
    new_panel.data.materials.append(wood_texture)


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
