# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script__generate_hex_key_set" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script, generate hex key set

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metal_material = bpy.data.materials.new(name='Metallic Finish')
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)

holder_material = bpy.data.materials.new(name='Holder Material')
holder_material.diffuse_color = (0.1, 0.1, 0.1, 1)

def add_hex_key(index, radius):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=2, location=(index * 0.5, 0, 1))
    hex_key = bpy.context.object
    hex_key.name = f'Hex Key {index + 1}'
    hex_key.data.materials.append(metal_material)
    bpy.ops.transform.rotate(value=math.pi / 2, orient_axis='X')

hex_key_sizes = [0.1, 0.12, 0.15, 0.18, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45]
for i, size in enumerate(hex_key_sizes):
    add_hex_key(i, size)

bpy.ops.mesh.primitive_cube_add(size=1, location=(2.25, 0, 0.5))
holder = bpy.context.object
holder.scale = (5, 0.5, 1)
holder.name = 'Hex Key Holder'
holder.data.materials.append(holder_material)


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
