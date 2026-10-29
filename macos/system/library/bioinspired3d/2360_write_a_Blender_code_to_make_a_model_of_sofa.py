# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_to_make_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code to make a model of sofa.

import bpy

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

clear_scene()

cushion_material = bpy.data.materials.new(name="Cushion")
cushion_material.diffuse_color = (0.8, 0.2, 0.2, 1)

class FurniturePiece:
    def __init__(self, name, size, location, scale):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        self.object = bpy.context.object
        self.object.name = name
        self.object.scale = scale
        self.object.data.materials.append(cushion_material)

seat = FurniturePiece("Seat", 2, (0, 0, 0.5), (2, 1, 0.2))
backrest = FurniturePiece("Backrest", 2, (0, -1.1, 1.2), (2, 0.2, 1))

for i in range(2):
    armrest_position = 2.1 * (i * 2 - 1)
    FurniturePiece(f"Armrest {i + 1}", 2, (armrest_position, 0, 1), (0.2, 1, 0.5))


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
