# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_Python_script__create_chocolate_chip_cookies" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender Python script, create chocolate chip cookies.

import bpy

# Remove all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up materials for the cookie and chocolate chips
cookie_texture = bpy.data.materials.new(name='CookieTexture')
cookie_texture.diffuse_color = (0.82, 0.71, 0.55, 1)
chip_texture = bpy.data.materials.new(name='ChocolateTexture')
chip_texture.diffuse_color = (0.1, 0.05, 0.02, 1)

# Function to generate cookies and their chips

def generate_cookie_and_chips(i, j):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(i, j, 0))
    cookie_object = bpy.context.object
    cookie_object.name = f'Cookie_{i * 3 + j}'
    cookie_object.data.materials.append(cookie_texture)
    
    for chip_index in range(5):
        x_offset = i + 0.2 * (chip_index % 2) - 0.1
        y_offset = j + 0.2 * (chip_index // 2) - 0.1
        z_offset = 0.5
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_offset, y_offset, z_offset))
        chip_object = bpy.context.object
        chip_object.name = f'Chip_{i * 3 + j}_{chip_index}'
        chip_object.data.materials.append(chip_texture)

# Create a grid layout of cookies
for x in range(4):
    for y in range(3):
        generate_cookie_and_chips(x, y)


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
