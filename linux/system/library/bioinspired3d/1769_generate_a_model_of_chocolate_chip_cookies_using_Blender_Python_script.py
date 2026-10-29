# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_chocolate_chip_cookies_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of chocolate chip cookies using Blender Python script

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for cookies and chips
cookie_material = bpy.data.materials.new(name='CookieMaterial')
cookie_material.diffuse_color = (0.82, 0.71, 0.55, 1)
chip_material = bpy.data.materials.new(name='ChipMaterial')
chip_material.diffuse_color = (0.1, 0.05, 0.02, 1)

# Function to create a cookie with chips
def create_cookie_with_chips(x, y):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(x, y, 0))
    cookie = bpy.context.object
    cookie.name = f'Cookie_{x}_{y}'
    cookie.data.materials.append(cookie_material)
    
    for k in range(5):
        chip_x = x + 0.2 * (k % 2) - 0.1
        chip_y = y + 0.2 * (k // 2) - 0.1
        chip_z = 0.5
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(chip_x, chip_y, chip_z))
        chip = bpy.context.object
        chip.name = f'Chip_{x}_{y}_{k}'
        chip.data.materials.append(chip_material)

# Create a grid of cookies
for row in range(4):
    for col in range(3):
        create_cookie_with_chips(row, col)


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
