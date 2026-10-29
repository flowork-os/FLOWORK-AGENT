# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_script_build_pet_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender script build pet bed.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bed_surface = bpy.data.materials.new(name='Bed Surface')
bed_surface.diffuse_color = (0.6, 0.4, 0.3, 1)
cushion_surface = bpy.data.materials.new(name='Cushion Surface')
cushion_surface.diffuse_color = (0.85, 0.85, 0.85, 1)

def create_named_cube(size, position, scale_factor, identifier, mat):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.scale = scale_factor
    cube.name = identifier
    cube.data.materials.append(mat)

create_named_cube(2, (0, 0, 0.25), (1, 1.5, 0.1), 'Bed Base', bed_surface)
create_named_cube(2, (0, -1.5, 0.75), (1, 0.1, 0.5), 'Front Side', bed_surface)
create_named_cube(2, (0, 1.5, 0.75), (1, 0.1, 0.5), 'Back Side', bed_surface)
create_named_cube(2, (-1, 0, 0.75), (0.1, 1.5, 0.5), 'Left Side', bed_surface)
create_named_cube(2, (1, 0, 0.75), (0.1, 1.5, 0.5), 'Right Side', bed_surface)
create_named_cube(2, (0, 0, 0.35), (0.9, 1.4, 0.05), 'Cushion', cushion_surface)


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
