# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_code_that_creates_a_model_of_chair" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender code that creates a model of chair.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

light_gray_material = bpy.data.materials.new(name='LightGray')
light_gray_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Soft gray tone

def add_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(light_gray_material)

for index in range(4):
    x_coord = 0.7 * (index % 2) - 0.35
    y_coord = 0.7 * (index // 2) - 0.35
    add_cylinder(0.05, 0.9, (x_coord, y_coord, -0.45), f'Leg_{index + 1}')

add_cylinder(0.5, 0.1, (0, 0, 0), 'Seat')

add_cylinder(0.5, 0.1, (0, -0.3, 0.3), 'Backrest')
bpy.context.object.rotation_euler = (math.pi / 2, 0, 0)


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
