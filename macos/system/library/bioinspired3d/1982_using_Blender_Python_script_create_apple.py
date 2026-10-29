# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script_create_apple" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script create apple

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

red_material = bpy.data.materials.new(name='Red Apple')
red_material.diffuse_color = (0.8, 0.1, 0.1, 1)
brown_material = bpy.data.materials.new(name='Brown Stem')
brown_material.diffuse_color = (0.4, 0.2, 0.1, 1)

def create_apple():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    apple_object = bpy.context.object
    apple_object.name = 'Apple'
    apple_object.data.materials.append(red_material)
    return apple_object

def create_stem():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.3, location=(0, 0, 1.15))
    stem_object = bpy.context.object
    stem_object.name = 'Stem'
    stem_object.data.materials.append(brown_material)
    return stem_object

apple = create_apple()
stem = create_stem()


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
