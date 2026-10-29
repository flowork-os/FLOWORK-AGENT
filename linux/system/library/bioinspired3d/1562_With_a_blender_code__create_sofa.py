# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_blender_code__create_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a blender code, create sofa.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

brown_material = bpy.data.materials.new(name='Brown Material')
brown_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # Earthy brown

class Sofa:
    def __init__(self):
        self.create_base()
        self.create_armrests()
        self.create_backrest()

    def create_base(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        base = bpy.context.object
        base.scale = (3, 1.5, 0.5)
        base.name = 'Base'
        base.data.materials.append(brown_material)

    def create_armrests(self):
        for i in range(2):
            x_pos = 3 * (i * 2 - 1)
            bpy.ops.mesh.primitive_cube_add(size=2, location=(x_pos, 0, 1.25))
            armrest = bpy.context.object
            armrest.scale = (0.2, 1.5, 0.75)
            armrest.name = f'Armrest {i + 1}'
            armrest.data.materials.append(brown_material)

    def create_backrest(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -1.5, 1.25))
        backrest = bpy.context.object
        backrest.scale = (3, 0.2, 0.75)
        backrest.name = 'Backrest'
        backrest.data.materials.append(brown_material)

sofa = Sofa()


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
