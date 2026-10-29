# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_generate_a_model_of_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to generate a model of hat.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

hat_color_material = bpy.data.materials.new(name="Hat Color")
hat_color_material.diffuse_color = (0.5, 0.25, 0.1, 1)

def add_cylinder(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(hat_color_material)

add_cylinder(1.5, 0.1, (0, 0, 0), "Hat Brim")
add_cylinder(0.75, 1, (0, 0, 0.55), "Hat Crown")


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
