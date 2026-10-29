# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_that_makes_a_model_of_emblem_of_unity" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code that makes a model of emblem of unity.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

gray_material = bpy.data.materials.new(name='Emblem Material')
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Medium gray color

TORUS_RADIUS = 1
GAP = TORUS_RADIUS * math.sqrt(3)

for index, position in enumerate([(0, GAP / 2, 0), (GAP / 2, -GAP / 4, 0), (-GAP / 2, -GAP / 4, 0)]):
    bpy.ops.mesh.primitive_torus_add(major_radius=TORUS_RADIUS, minor_radius=0.1, location=position)
    torus = bpy.context.object
    torus.name = f'Circle {index + 1}'
    torus.data.materials.append(gray_material)


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
