# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender_create_a_model_of_modular_shelving_unit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender create a model of modular shelving unit

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

shelf_material = bpy.data.materials.new(name='LightGray')
shelf_material.diffuse_color = (0.8, 0.8, 0.8, 1)

shelf_params = {'width': 2, 'height': 0.1, 'depth': 0.5}

for index in range(4):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, index))
    shelf = bpy.context.object
    shelf.scale = (shelf_params['width'], shelf_params['depth'], shelf_params['height'])
    shelf.name = f'Shelf_{index + 1}'
    shelf.data.materials.append(shelf_material)

support_params = {'width': 0.1, 'height': 4, 'depth': 0.5}

for index in range(2):
    x_position = shelf_params['width'] * (index * 2 - 1) / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_position, 0, support_params['height'] / 2 - 0.5))
    support = bpy.context.object
    support.scale = (support_params['width'], support_params['depth'], support_params['height'])
    support.name = f'Support_{index + 1}'
    support.data.materials.append(shelf_material)


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
