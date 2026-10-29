# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_code_in_Blender__construct_abstract_symbol" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with code in Blender, construct abstract symbol

import bpy
import math

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material with a specific color
gray_material = bpy.data.materials.new(name="Gray")
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Create tori with varying orientations
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(0, 0, 0))
torus1 = bpy.context.object
torus1.name = "Torus1"
torus1.data.materials.append(gray_material)

bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(0, 0, 0), rotation=(math.pi/2, 0, 0))
torus2 = bpy.context.object
torus2.name = "Torus2"
torus2.data.materials.append(gray_material)

bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(0, 0, 0), rotation=(0, math.pi/2, 0))
torus3 = bpy.context.object
torus3.name = "Torus3"
torus3.data.materials.append(gray_material)


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
