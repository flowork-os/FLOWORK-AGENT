# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_that_makes_dog_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code that makes dog bed.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_bed = bpy.data.materials.new(name='MaterialBed')
material_bed.diffuse_color = (0.6, 0.4, 0.2, 1)  # Lighter brown

def create_bed_part(name, pos, scale_factors):
    bpy.ops.mesh.primitive_cube_add(size=2, location=pos)
    part = bpy.context.object
    part.scale = scale_factors
    part.name = name
    part.data.materials.append(material_bed)
    return part

create_bed_part('BedBase', (0, 0, 0.1), (1.5, 1, 0.1))

height = 0.2
thickness = 0.1

create_bed_part('FrontEdge', (0, 1 - thickness, height / 2), (1.5, thickness, height))
create_bed_part('BackEdge', (0, -(1 - thickness), height / 2), (1.5, thickness, height))
create_bed_part('LeftEdge', (1.5 - thickness, 0, height / 2), (thickness, 1, height))
create_bed_part('RightEdge', (-(1.5 - thickness), 0, height / 2), (thickness, 1, height))


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
