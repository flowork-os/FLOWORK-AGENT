# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_modular_bookshelf_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of modular bookshelf in blender code

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

shelf_material = bpy.data.materials.new(name='ShelfColor')
shelf_material.diffuse_color = (0.6, 0.3, 0.1, 1)

class BookshelfUnit:
    def __init__(self, position):
        self.create_unit(position)

    def create_unit(self, position):
        bpy.ops.mesh.primitive_cube_add(size=1, location=position)
        self.cube = bpy.context.object
        self.cube.name = 'Bookshelf Cube'
        self.cube.data.materials.append(shelf_material)
        
        base_position = (position[0], position[1], position[2] - 0.55)
        bpy.ops.mesh.primitive_cube_add(size=1.1, scale=(1, 1, 0.1), location=base_position)
        self.base = bpy.context.object
        self.base.name = 'Bookshelf Base'
        self.base.data.materials.append(shelf_material)

for i in range(2):
    for j in range(2):
        BookshelfUnit((i * 1.2, j * 1.2, 0.5))


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
