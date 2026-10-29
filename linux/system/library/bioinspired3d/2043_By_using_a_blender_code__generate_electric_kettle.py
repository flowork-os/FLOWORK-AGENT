# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code__generate_electric_kettle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code, generate electric kettle.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

body_material = bpy.data.materials.new(name='Body Material')
body_material.diffuse_color = (0.5, 0.5, 0.5, 1)
base_material = bpy.data.materials.new(name='Base Material')
base_material.diffuse_color = (0.1, 0.1, 0.1, 1)

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

kettle_body = create_cylinder(1, 2, (0, 0, 1), 'Kettle Body', body_material)

spout_location = (1.1, 0, 1.5)
spout_rotation = (0, math.pi / 4, 0)
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=spout_location, rotation=spout_rotation)
spout = bpy.context.object
spout.name = 'Spout'
spout.data.materials.append(body_material)

bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.1, location=(-1.5, 0, 1.5), rotation=(math.pi / 2, 0, 0))
handle = bpy.context.object
handle.name = 'Handle'
handle.data.materials.append(body_material)

base = create_cylinder(1.2, 0.2, (0, 0, 0.1), 'Base', base_material)


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
