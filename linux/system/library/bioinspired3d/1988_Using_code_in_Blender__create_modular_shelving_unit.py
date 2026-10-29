# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender__create_modular_shelving_unit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender, create modular shelving unit.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_for_shelves = bpy.data.materials.new(name='MaterialForShelves')
material_for_shelves.diffuse_color = (0.85, 0.85, 0.85, 1)  # Light silver color

width_of_shelf = 2.0
height_of_shelf = 0.1
depth_of_shelf = 0.5

for shelf_index in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, shelf_index * 1.2))
    shelf_object = bpy.context.object
    shelf_object.scale = (width_of_shelf, depth_of_shelf, height_of_shelf)
    shelf_object.name = f'Shelf_{shelf_index + 1}'
    shelf_object.data.materials.append(material_for_shelves)

width_of_support = 0.1
height_of_support = 3.5
depth_of_support = 0.1

for support_index in range(4):
    x_pos = (support_index % 2) * (width_of_shelf - width_of_support) - (width_of_shelf / 2 - width_of_support / 2)
    y_pos = (support_index // 2) * (depth_of_shelf - depth_of_support) - (depth_of_shelf / 2 - depth_of_support / 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, y_pos, height_of_support / 2 - height_of_shelf / 2))
    support_object = bpy.context.object
    support_object.scale = (width_of_support, depth_of_support, height_of_support)
    support_object.name = f'Support_{support_index + 1}'
    support_object.data.materials.append(material_for_shelves)


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
