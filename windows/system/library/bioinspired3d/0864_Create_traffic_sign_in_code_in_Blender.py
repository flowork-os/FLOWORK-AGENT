# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_traffic_sign_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create traffic sign in code in Blender

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sign and text
sign_mat = bpy.data.materials.new(name='Red Sign')
sign_mat.diffuse_color = (0.8, 0.2, 0.2, 1)

text_mat = bpy.data.materials.new(name='White Text')
text_mat.diffuse_color = (1, 1, 1, 1)

# Creating the octagonal sign
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1, depth=0.1, location=(0, 0, 0))
sign = bpy.context.object
sign.name = 'Stop Sign'
sign.data.materials.append(sign_mat)

# Adding the STOP text
bpy.ops.object.text_add(location=(0, 0, 0.1))
text = bpy.context.object
text.data.body = 'STOP'
text.data.align_x = 'CENTER'
text.data.align_y = 'CENTER'
text.data.size = 0.5
text.data.materials.append(text_mat)

# Adjusting text position
text.location.z += 0.1
text.scale = (0.5, 0.5, 0.5)


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
