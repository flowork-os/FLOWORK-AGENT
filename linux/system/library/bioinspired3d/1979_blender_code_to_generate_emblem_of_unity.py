# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_generate_emblem_of_unity" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to generate emblem of unity

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_gray = bpy.data.materials.new(name="Gray Material")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)  # Set to medium gray

circle_radius = 1
spacing = circle_radius * math.sqrt(3)

def create_circle(location, name):
    bpy.ops.mesh.primitive_torus_add(major_radius=circle_radius, minor_radius=0.1, location=location)
    circle_object = bpy.context.object
    circle_object.name = name
    circle_object.data.materials.append(material_gray)

create_circle((0, spacing / 2, 0), "Circle 1")
create_circle((spacing / 2, -spacing / 4, 0), "Circle 2")
create_circle((-spacing / 2, -spacing / 4, 0), "Circle 3")


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
