# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__construct_a_model_of_logo_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, construct a model of logo design

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_blue = bpy.data.materials.new(name='MaterialBlue')
material_blue.diffuse_color = (0.1, 0.5, 0.8, 1)

def create_torus(name, major_radius, minor_radius, location, rotation):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, location=location, rotation=rotation)
    torus = bpy.context.object
    torus.name = name
    torus.data.materials.append(material_blue)
    return torus

create_torus('FirstRing', 1, 0.1, (0, 0, 0), (0, 0, 0))
create_torus('SecondRing', 1, 0.1, (0, 0, 0), (math.pi/2, 0, 0))
create_torus('ThirdRing', 1, 0.1, (0, 0, 0), (0, math.pi/2, 0))


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
