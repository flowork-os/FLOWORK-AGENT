# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_to_create_a_model_of_emblem_of_unity" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code to create a model of emblem of unity.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

emblem_mat = bpy.data.materials.new(name='Emblem Gray')
emblem_mat.diffuse_color = (0.5, 0.5, 0.5, 1)  # Setting to a medium gray color

circle_diameter = 1
circle_offset = circle_diameter * math.sqrt(3)

def add_circle(pos, circle_name):
    bpy.ops.mesh.primitive_torus_add(major_radius=circle_diameter, minor_radius=0.1, location=pos)
    new_circle = bpy.context.object
    new_circle.name = circle_name
    new_circle.data.materials.append(emblem_mat)

positions = [(0, circle_offset / 2, 0), (circle_offset / 2, -circle_offset / 4, 0), (-circle_offset / 2, -circle_offset / 4, 0)]

for idx, pos in enumerate(positions):
    add_circle(pos, f'Circle {idx + 1}')


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
