# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code_build_pet_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code build pet bed.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bed_material = bpy.data.materials.new(name='Bed Material')
bed_material.diffuse_color = (0.55, 0.35, 0.15, 1)  # Another variation of brown

def construct_bed_base():
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.2, location=(0, 0, 0))
    bed_base = bpy.context.object
    bed_base.name = 'Bed Base'
    bed_base.data.materials.append(bed_material)
    return bed_base

def construct_bed_rim():
    bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.2, location=(0, 0, 0.2))
    bed_rim = bpy.context.object
    bed_rim.name = 'Bed Rim'
    bed_rim.data.materials.append(bed_material)
    return bed_rim

base = construct_bed_base()
rim = construct_bed_rim()


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
