# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_code_create_keyboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender code create keyboard.

import bpy

# Step 1: Clear Existing Meshes
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create Materials for Keyboard
body_material = bpy.data.materials.new(name='Body Material')
body_material.diffuse_color = (0.1, 0.1, 0.1, 1)
key_material = bpy.data.materials.new(name='Key Material')
key_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Step 2: Build Keyboard Base
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
keyboard_base = bpy.context.object
keyboard_base.name = 'Keyboard Base'
keyboard_base.scale = (4, 1.5, 0.1)
keyboard_base.data.materials.append(body_material)

# Step 3: Generate Keys
key_count_row = 5
key_count_col = 14
key_dimensions = (0.5, 0.5, 0.1)

for r in range(key_count_row):
    for c in range(key_count_col):
        x_position = c * (key_dimensions[0] + 0.05) - (key_count_col * (key_dimensions[0] + 0.05) / 2) + (key_dimensions[0] / 2)
        y_position = r * (key_dimensions[1] + 0.05) - (key_count_row * (key_dimensions[1] + 0.05) / 2) + (key_dimensions[1] / 2)
        z_position = 0.1
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x_position, y_position, z_position))
        key = bpy.context.object
        key.scale = (key_dimensions[0] / 2, key_dimensions[1] / 2, key_dimensions[2] / 2)
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
