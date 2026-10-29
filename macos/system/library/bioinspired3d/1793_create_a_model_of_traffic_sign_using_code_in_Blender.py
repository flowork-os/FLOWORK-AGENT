# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_traffic_sign_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of traffic sign using code in Blender

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_sign = bpy.data.materials.new(name='Stop Sign Color')
material_sign.diffuse_color = (0.8, 0.2, 0.2, 1)

material_text = bpy.data.materials.new(name='Text Color')
material_text.diffuse_color = (1, 1, 1, 1)

bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1, depth=0.1, location=(0, 0, 0))
sign_object = bpy.context.object
sign_object.name = 'Stop Sign'
sign_object.data.materials.append(material_sign)

bpy.ops.object.text_add(location=(0, 0, 0.1))
text_object = bpy.context.object
text_object.data.body = 'STOP'
text_object.data.align_x = 'CENTER'
text_object.data.align_y = 'CENTER'
text_object.data.size = 0.5
text_object.data.materials.append(material_text)

text_object.location.z += 0.1
text_object.scale = (0.5, 0.5, 0.5)


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
