# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_python_blender_code_build_chair" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With python blender code build chair.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_light_gray = bpy.data.materials.new(name='LightGrayMaterial')
material_light_gray.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light grey

class ChairComponent:
    def __init__(self, radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        self.object = bpy.context.object
        self.object.name = name
        self.object.data.materials.append(material_light_gray)

for leg_index in range(4):
    leg_x = 0.7 * (leg_index % 2) - 0.35
    leg_y = 0.7 * (leg_index // 2) - 0.35
    ChairComponent(0.05, 0.9, (leg_x, leg_y, -0.45), f'Leg_{leg_index + 1}')

ChairComponent(0.5, 0.1, (0, 0, 0), 'Seat')

backrest = ChairComponent(0.5, 0.1, (0, -0.3, 0.3), 'Backrest')
backrest.object.rotation_euler = (math.pi / 2, 0, 0)


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
