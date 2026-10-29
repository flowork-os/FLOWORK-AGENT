# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_creating_a_model_of_ottoman" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for creating a model of ottoman.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

ottoman_material = bpy.data.materials.new(name="Ottoman Material")
ottoman_material.diffuse_color = (0.6, 0.3, 0.15, 1)  # A lighter brown tint

def create_cube(size, location, scale, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    return cube

ottoman_base = create_cube(1, (0, 0, 0.25), (1, 1, 0.2), "Ottoman Base")
ottoman_base.data.materials.append(ottoman_material)

def create_leg(location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.25, location=location)
    leg = bpy.context.object
    leg.name = name
    leg.data.materials.append(ottoman_material)

for index in range(4):
    leg_x = 0.5 * (index % 2 * 2 - 1)
    leg_y = 0.5 * (index // 2 * 2 - 1)
    create_leg((leg_x, leg_y, 0.125), f"Leg {index + 1}")


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
