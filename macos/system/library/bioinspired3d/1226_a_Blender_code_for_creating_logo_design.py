# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_creating_logo_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for creating logo design

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the logo in a blue tone
logo_material = bpy.data.materials.new(name='LogoMaterial')
logo_material.diffuse_color = (0.1, 0.5, 0.8, 1)

# Define a function to add a torus with specific parameters

def add_torus(torus_name, major_rad, minor_rad, loc, rot):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_rad, minor_radius=minor_rad, location=loc, rotation=rot)
    new_torus = bpy.context.object
    new_torus.name = torus_name
    new_torus.data.materials.append(logo_material)

# Create three rings with different rotations
add_torus('TorusOne', 1, 0.1, (0, 0, 0), (0, 0, 0))
add_torus('TorusTwo', 1, 0.1, (0, 0, 0), (math.pi / 2, 0, 0))
add_torus('TorusThree', 1, 0.1, (0, 0, 0), (0, math.pi / 2, 0))


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
