# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code_generate_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code generate sofa

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_sofa = bpy.data.materials.new(name="Sofa Color")
material_sofa.diffuse_color = (0.5, 0.2, 0.2, 1)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
seat_obj = bpy.context.object
seat_obj.name = "Seat"
seat_obj.scale[0] = 2
seat_obj.scale[1] = 1
seat_obj.scale[2] = 0.2
seat_obj.data.materials.append(material_sofa)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.9, 1.1))
backrest_obj = bpy.context.object
backrest_obj.name = "Backrest"
backrest_obj.scale[0] = 2
backrest_obj.scale[1] = 0.2
backrest_obj.scale[2] = 0.6
backrest_obj.data.materials.append(material_sofa)

for i in range(2):
    position_x = 2 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(position_x, 0, 0.9))
    armrest_obj = bpy.context.object
    armrest_obj.name = f"Armrest {i + 1}"
    armrest_obj.scale[0] = 0.2
    armrest_obj.scale[1] = 1
    armrest_obj.scale[2] = 0.6
    armrest_obj.data.materials.append(material_sofa)


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
