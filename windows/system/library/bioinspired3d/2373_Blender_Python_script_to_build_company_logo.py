# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_build_company_logo" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to build company logo.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_blue = bpy.data.materials.new(name='MaterialBlue')
material_blue.diffuse_color = (0.0, 0.0, 1.0, 1)

circle_radius = 1
circle_positions = [(0, 1, 0), (-math.sqrt(3)/2, -0.5, 0), (math.sqrt(3)/2, -0.5, 0)]

def create_circle(location):
    bpy.ops.mesh.primitive_torus_add(location=location, major_radius=circle_radius, minor_radius=0.1)
    new_circle = bpy.context.object
    new_circle.data.materials.append(material_blue)

for position in circle_positions:
    create_circle(position)


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
