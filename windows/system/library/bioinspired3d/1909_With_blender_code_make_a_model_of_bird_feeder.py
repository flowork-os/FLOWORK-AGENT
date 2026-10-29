# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_code_make_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender code make a model of bird feeder.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

wood_material = bpy.data.materials.new(name="Wood")
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, location=(0, 0, 0.5))
main_body = bpy.context.object
main_body.name = "Body"
main_body.data.materials.append(wood_material)

bpy.ops.mesh.primitive_cone_add(radius1=0.5, radius2=0.1, depth=0.5, location=(0, 0, 1.25))
roof = bpy.context.object
roof.name = "Top"
roof.data.materials.append(wood_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.0, location=(0, 0.55, 0.5), rotation=(1.57, 0, 0))
perch = bpy.context.object
perch.name = "Perch"
perch.data.materials.append(wood_material)


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
