# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_Python_script_create_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender Python script create a model of bookshelf.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bookshelf_material = bpy.data.materials.new(name='Bookshelf Wood')
bookshelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)

side_width = 0.1
side_height = 2.0
side_depth = 0.3
side_coordinates = [(-0.5, 0, 1), (0.5, 0, 1)]

for coordinates in side_coordinates:
    bpy.ops.mesh.primitive_cube_add(size=1, location=coordinates)
    side_object = bpy.context.object
    side_object.scale = (side_width, side_depth, side_height)
    side_object.name = 'Bookshelf Side'
    side_object.data.materials.append(bookshelf_material)

shelf_thickness = 0.1
shelf_length = 1.0
shelf_depth = 0.3
number_of_shelves = 5
shelf_spacing = side_height / (number_of_shelves + 1)

for index in range(number_of_shelves):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, shelf_spacing * (index + 1)))
    shelf_object = bpy.context.object
    shelf_object.scale = (shelf_length, shelf_depth, shelf_thickness)
    shelf_object.name = f'Shelf {index + 1}'
    shelf_object.data.materials.append(bookshelf_material)


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
