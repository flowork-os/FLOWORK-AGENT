# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_chair_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of chair using python blender code

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_gray = bpy.data.materials.new(name='Gray Material')
material_gray.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray

def create_leg(index):
    position_x = 0.7 * (index % 2) - 0.35
    position_y = 0.7 * (index // 2) - 0.35
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.9, location=(position_x, position_y, -0.45))
    leg = bpy.context.object
    leg.name = f'Leg_{index + 1}'
    leg.data.materials.append(material_gray)

for i in range(4):
    create_leg(i)

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
seat_object = bpy.context.object
seat_object.name = 'Seat'
seat_object.data.materials.append(material_gray)

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, -0.3, 0.3), rotation=(math.pi / 2, 0, 0))
backrest_object = bpy.context.object
backrest_object.name = 'Backrest'
backrest_object.data.materials.append(material_gray)


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
