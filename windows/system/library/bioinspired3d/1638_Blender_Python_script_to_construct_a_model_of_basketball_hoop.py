# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_construct_a_model_of_basketball_hoop" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to construct a model of basketball hoop

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_dark_wood = bpy.data.materials.new(name="DarkWood")
material_dark_wood.diffuse_color = (0.26, 0.14, 0.09, 1)
material_green = bpy.data.materials.new(name="Green")
material_green.diffuse_color = (0.13, 0.26, 0.13, 1)

def add_cylinder(radius, depth, location, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    if rotation:
        bpy.context.object.rotation_euler = rotation
    return bpy.context.object

legs = []
for i in range(4):
    leg_x = 0.7 * (i % 2) - 0.35
    leg_y = 0.7 * (i // 2) - 0.35
    leg = add_cylinder(0.05, 0.9, (leg_x, leg_y, -0.45))
    leg.data.materials.append(material_dark_wood)
    legs.append(leg)

seat = add_cylinder(0.5, 0.1, (0, 0, 0))
seat.data.materials.append(material_green)

backrest = add_cylinder(0.5, 0.1, (0, -0.3, 0.3), rotation=(math.pi / 2, 0, 0))
backrest.data.materials.append(material_dark_wood)

for j in range(2):
    arm_x = 0.45 * (j * 2 - 1)
    add_cylinder(0.03, 0.6, (arm_x, 0, 0.3), rotation=(math.pi / 2, 0, 0)).data.materials.append(material_dark_wood)
    add_cylinder(0.03, 0.3, (arm_x, 0, 0.15), rotation=(0, 0, math.pi / 2)).data.materials.append(material_dark_wood)


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
