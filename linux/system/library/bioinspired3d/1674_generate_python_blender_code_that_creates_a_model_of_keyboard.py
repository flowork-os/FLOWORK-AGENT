# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_python_blender_code_that_creates_a_model_of_keyboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate python blender code that creates a model of keyboard.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the keyboard
keyboard_mat = bpy.data.materials.new(name='Keyboard Material')
keyboard_mat.diffuse_color = (0.1, 0.1, 0.1, 1)
key_mat = bpy.data.materials.new(name='Key Material')
key_mat.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a key at a specific location
def create_key(x, y, z, width, height, depth):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    key = bpy.context.object
    key.scale = (width / 2, height / 2, depth / 2)
    key.data.materials.append(key_mat)

# Generate the keyboard body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
keyboard = bpy.context.object
keyboard.name = 'Keyboard'
keyboard.scale[0] = 4
keyboard.scale[1] = 1.5
keyboard.scale[2] = 0.1
keyboard.data.materials.append(keyboard_mat)

# Create keys
rows = 5
cols = 14
key_size = (0.5, 0.5, 0.1)
for row in range(rows):
    for col in range(cols):
        x = col * (key_size[0] + 0.05) - (cols * (key_size[0] + 0.05) / 2) + (key_size[0] / 2)
        y = row * (key_size[1] + 0.05) - (rows * (key_size[1] + 0.05) / 2) + (key_size[1] / 2)
        create_key(x, y, 0.1, key_size[0], key_size[1], key_size[2])


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
