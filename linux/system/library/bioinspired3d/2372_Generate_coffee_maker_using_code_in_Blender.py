# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_coffee_maker_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate coffee maker using code in Blender

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

materials = {
    'body': bpy.data.materials.new(name="DarkGrayBody"),
    'spout': bpy.data.materials.new(name="DarkGraySpout"),
    'handle': bpy.data.materials.new(name="DarkGrayHandle"),
    'lid': bpy.data.materials.new(name="DarkGrayLid")
}
for mat in materials.values():
    mat.diffuse_color = (0.2, 0.2, 0.2, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
body = bpy.context.object
body.name = "MainBody"
body.data.materials.append(materials['body'])

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(1.1, 0, 1.5), rotation=(0, math.pi/4, 0))
spout = bpy.context.object
spout.name = "SpoutPart"
spout.data.materials.append(materials['spout'])

bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.1, location=(-1.5, 0, 1.5), rotation=(math.pi/2, 0, 0))
handle = bpy.context.object
handle.name = "HandlePart"
handle.data.materials.append(materials['handle'])

bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=0.1, location=(0, 0, 2.05))
lid = bpy.context.object
lid.name = "LidPart"
lid.data.materials.append(materials['lid'])


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
