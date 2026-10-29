# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_to_create_a_model_of_keyboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script to create a model of keyboard.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

keyboard_material = bpy.data.materials.new(name='Main Keyboard Material')
keyboard_material.diffuse_color = (0.1, 0.1, 0.1, 1)
key_material = bpy.data.materials.new(name='Key Color Material')
key_material.diffuse_color = (0.8, 0.8, 0.8, 1)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
keyboard = bpy.context.object
keyboard.name = 'Keyboard Structure'
keyboard.scale = (4, 1.5, 0.1)
keyboard.data.materials.append(keyboard_material)

key_rows = 5
key_columns = 14
key_width = 0.5
key_height = 0.5
key_depth = 0.1

for i in range(key_rows):
    for j in range(key_columns):
        x_pos = j * (key_width + 0.05) - (key_columns * (key_width + 0.05) / 2) + (key_width / 2)
        y_pos = i * (key_height + 0.05) - (key_rows * (key_height + 0.05) / 2) + (key_height / 2)
        z_pos = 0.1
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, y_pos, z_pos))
        key = bpy.context.object
        key.scale = (key_width / 2, key_height / 2, key_depth / 2)
        key.data.materials.append(key_material)


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
