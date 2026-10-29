# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_code_that_makes_birthday_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender code that makes birthday cake

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

cake_layer_material = bpy.data.materials.new(name='Cake Layer Material')
cake_layer_material.diffuse_color = (0.9, 0.7, 0.5, 1)

layer_specs = [
    (1.5, 0.5, 0.25, 'Bottom Layer'),
    (1.2, 0.5, 0.75, 'Middle Layer'),
    (0.9, 0.5, 1.25, 'Top Layer')
]

for radius, depth, z_pos, name in layer_specs:
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=(0, 0, z_pos))
    layer = bpy.context.object
    layer.name = name
    layer.data.materials.append(cake_layer_material)


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
