# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_to_create_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script to create sofa

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_for_cushion = bpy.data.materials.new(name="Cushion Material")
material_for_cushion.diffuse_color = (0.8, 0.2, 0.2, 1)  # Red color

def create_cube(name, size, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material_for_cushion)
    return cube

create_cube("Seat", 2, (0, 0, 0.5), (2, 1, 0.2))
create_cube("Backrest", 2, (0, -1.1, 1.2), (2, 0.2, 1))

for index in range(2):
    position_x = 2.1 * (index * 2 - 1)
    create_cube(f"Armrest {index + 1}", 2, (position_x, 0, 1), (0.2, 1, 0.5))


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
