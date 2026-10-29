# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_birthday_cake_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of birthday cake in Blender code

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

cake_color = bpy.data.materials.new(name='Cake Color')
cake_color.diffuse_color = (0.8, 0.6, 0.4, 1)
icings_color = bpy.data.materials.new(name='Icing Color')
icings_color.diffuse_color = (1, 0.8, 0.8, 1)

radii = [1, 0.8, 0.6]
depths = [0.3, 0.3, 0.3]
positions = [0, 0.3, 0.6]
names = ["Base Layer", "Middle Layer", "Top Layer"]
for radius, depth, z, name in zip(radii, depths, positions, names):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=(0, 0, z))
    layer = bpy.context.object
    layer.name = name
    layer.data.materials.append(cake_color)

bpy.ops.mesh.primitive_cylinder_add(radius=0.65, depth=0.1, location=(0, 0, 0.75))
icings = bpy.context.object
icings.name = "Icing"
icings.data.materials.append(icings_color)


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
