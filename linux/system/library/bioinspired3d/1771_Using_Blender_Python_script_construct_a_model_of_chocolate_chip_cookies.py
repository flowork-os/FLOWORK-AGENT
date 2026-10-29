# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_Python_script_construct_a_model_of_chocolate_chip_cookies" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender Python script construct a model of chocolate chip cookies

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for cookies and chocolate chips
cookie_mat = bpy.data.materials.new(name='CookieMaterial')
cookie_mat.diffuse_color = (0.82, 0.71, 0.55, 1)
chip_mat = bpy.data.materials.new(name='ChipMaterial')
chip_mat.diffuse_color = (0.1, 0.05, 0.02, 1)

# Class to represent a cookie and its chips
class Cookie:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.create_cookie()
        self.add_chips()

    def create_cookie(self):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(self.x, self.y, 0))
        self.cookie_object = bpy.context.object
        self.cookie_object.name = f'Cookie_{self.x}_{self.y}'
        self.cookie_object.data.materials.append(cookie_mat)

    def add_chips(self):
        for k in range(5):
            chip_x = self.x + 0.2 * (k % 2) - 0.1
            chip_y = self.y + 0.2 * (k // 2) - 0.1
            chip_z = 0.5
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(chip_x, chip_y, chip_z))
            chip_object = bpy.context.object
            chip_object.name = f'Chip_{self.x}_{self.y}_{k}'
            chip_object.data.materials.append(chip_mat)

# Generate cookies in a grid
for i in range(4):
    for j in range(3):
        Cookie(i, j)


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
