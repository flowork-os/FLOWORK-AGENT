# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_drum_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of drum using Blender code

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_body = bpy.data.materials.new(name="Drum Body Material")
mat_body.diffuse_color = (0.8, 0.2, 0.2, 1)
mat_head = bpy.data.materials.new(name="Drumhead Material")
mat_head.diffuse_color = (0.9, 0.9, 0.9, 1)
mat_stick = bpy.data.materials.new(name="Drumstick Material")
mat_stick.diffuse_color = (0.5, 0.25, 0.1, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
body = bpy.context.object
body.name = "Drum Body"
body.data.materials.append(mat_body)

bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 1.5))
drumhead = bpy.context.object
drumhead.name = "Drumhead"
drumhead.data.materials.append(mat_head)

stick_locations = [-1.2, 1.2]
for idx, loc in enumerate(stick_locations):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=(loc, 0, 0.75), rotation=(1.5708, 0, 0))
    stick = bpy.context.object
    stick.name = f"Drumstick {idx + 1}"
    stick.data.materials.append(mat_stick)


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
