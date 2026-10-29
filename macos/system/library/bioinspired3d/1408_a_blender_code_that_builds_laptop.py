# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_builds_laptop" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that builds laptop.

import bpy

# Clear all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a black material for the laptop
black_material = bpy.data.materials.new(name="BlackSurface")
black_material.diffuse_color = (0.0, 0.0, 0.0, 1)  # Setting to black

# Class to represent a Laptop
class Laptop:
    def __init__(self):
        self.base = self.create_part((0, 0, 0.1), (1.5, 1, 0.05), "LaptopBase")
        self.screen = self.create_part((0, 1.05, 1.1), (1.5, 0.05, 1), "LaptopScreen")
        self.create_keyboard(5, 10, 0.2, 0.05)

    def create_part(self, location, scale, name):
        bpy.ops.mesh.primitive_cube_add(size=2, location=location)
        part = bpy.context.object
        part.scale = scale
        part.name = name
        part.data.materials.append(black_material)
        return part

    def create_keyboard(self, rows, cols, key_size, key_spacing):
        for row in range(rows):
            for col in range(cols):
                x = (col - cols / 2) * (key_size + key_spacing) + (key_size + key_spacing) / 2
                y = (row - rows / 2) * (key_size + key_spacing) + (key_size + key_spacing) / 2
                self.create_part((x, y, 0.15), (1, 1, 1), f"Key_{row}_{col}")

# Instantiate the Laptop object
laptop = Laptop()


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
