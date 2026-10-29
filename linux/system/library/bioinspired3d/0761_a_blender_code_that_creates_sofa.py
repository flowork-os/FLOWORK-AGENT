# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_creates_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that creates sofa

import bpy

# Start with a clean slate
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material setup for the sofa
sofa_material = bpy.data.materials.new(name="Sofa Color")
sofa_material.diffuse_color = (0.5, 0.2, 0.2, 1)

# Class to handle sofa parts
class SofaPart:
    def __init__(self, name, location, scale):
        self.name = name
        self.location = location
        self.scale = scale
        self.create_part()

    def create_part(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=self.location)
        part = bpy.context.object
        part.name = self.name
        part.scale = self.scale
        part.data.materials.append(sofa_material)

# Define and create all parts of the sofa
SofaPart("Seat", (0, 0, 0.5), (2, 1, 0.2))
SofaPart("Backrest", (0, -0.9, 1.1), (2, 0.2, 0.6))
for i in range(2):
    x_position = 2 * (i * 2 - 1)
    SofaPart(f"Armrest {i + 1}", (x_position, 0, 0.9), (0.2, 1, 0.6))


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
