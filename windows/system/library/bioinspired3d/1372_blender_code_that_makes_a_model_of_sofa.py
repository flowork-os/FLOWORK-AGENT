# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_makes_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that makes a model of sofa.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a brown material for the sofa
brown_material = bpy.data.materials.new(name="Brown Sofa")
brown_material.diffuse_color = (0.5, 0.25, 0.25, 1)

# Class to represent a sofa component
class SofaComponent:
    def __init__(self, name, location, scale):
        bpy.ops.mesh.primitive_cube_add(size=2, location=location)
        self.object = bpy.context.object
        self.object.scale = scale
        self.object.name = name
        self.object.data.materials.append(brown_material)

# Create the seat, backrest, and armrests
SofaComponent("Seat", (0, 0, 0.5), (2, 1, 0.2))
SofaComponent("Backrest", (0, -0.9, 1.1), (2, 0.2, 0.6))
for i in range(2):
    SofaComponent(f"Armrest {i + 1}", (2 * (i * 2 - 1), 0, 0.9), (0.2, 1, 0.4))


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
