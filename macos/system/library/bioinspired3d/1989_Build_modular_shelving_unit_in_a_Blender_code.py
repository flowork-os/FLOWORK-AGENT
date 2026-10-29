# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_modular_shelving_unit_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build modular shelving unit in a Blender code

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize material for the shelves
shelf_material = bpy.data.materials.new(name='ShelfMaterial')
shelf_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Gray color

# Using a class to create shelves
class Shelf:
    def __init__(self, index):
        self.index = index
        self.create_shelf()

    def create_shelf(self):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, self.index * 1.2))
        shelf = bpy.context.object
        shelf.scale = (2, 0.5, 0.1)
        shelf.name = f'Shelf_{self.index + 1}'
        shelf.data.materials.append(shelf_material)

# Create shelves
for i in range(3):
    Shelf(i)

# Using a class to create supports
class Support:
    def __init__(self, index):
        self.index = index
        self.create_support()

    def create_support(self):
        x = (self.index % 2) * (2 - 0.1) - (2 / 2 - 0.1 / 2)
        y = (self.index // 2) * (0.5 - 0.1) - (0.5 / 2 - 0.1 / 2)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 3.5 / 2 - 0.1 / 2))
        support = bpy.context.object
        support.scale = (0.1, 0.1, 3.5)
        support.name = f'Support_{self.index + 1}'
        support.data.materials.append(shelf_material)

# Create supports
for i in range(4):
    Support(i)


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
