# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_python_blender_code__construct_a_model_of_hammer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with python blender code, construct a model of hammer.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metal_material = bpy.data.materials.new(name='Hammer Metal')
metal_material.diffuse_color = (0.4, 0.4, 0.4, 1)
wood_material = bpy.data.materials.new(name='Hammer Wood')
wood_material.diffuse_color = (0.6, 0.3, 0.1, 1)

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0.25))
head = bpy.context.object
head.name = 'HammerHead'
head.scale[0] = 1.5
head.data.materials.append(metal_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(0, 0, -1))
handle = bpy.context.object
handle.name = 'HammerHandle'
handle.data.materials.append(wood_material)


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
