# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_builds_umbrella" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that builds umbrella.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

black_material = bpy.data.materials.new(name='DarkMaterial')
black_material.diffuse_color = (0.0, 0.0, 0.0, 1)

def add_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(black_material)
    return obj

handle = add_cylinder(0.05, 0.2, (0, 0, -0.1), 'Handle')
add_cylinder(0.02, 0.02, (0, 0.05, 0), 'Button')
add_cylinder(0.02, 1.0, (0, 0, 0.5), 'Shaft')

bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.6, radius2=0.02, depth=0.7, location=(0, 0, 1.2))
canopy = bpy.context.object
canopy.name = 'Canopy'
canopy.data.materials.append(black_material)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.transform.shrink_fatten(value=-0.3)
bpy.ops.object.mode_set(mode='OBJECT')


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
