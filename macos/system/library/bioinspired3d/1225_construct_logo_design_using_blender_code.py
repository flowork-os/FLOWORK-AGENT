# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_logo_design_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct logo design using blender code

import bpy
import math

# Start fresh by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a material with a blue hue
blue_material = bpy.data.materials.new(name='BlueMaterial')
blue_material.diffuse_color = (0.1, 0.5, 0.8, 1)

# Create torus rings with different orientations
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(0, 0, 0))
first_ring = bpy.context.object
first_ring.name = 'FirstTorus'
first_ring.data.materials.append(blue_material)

bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
second_ring = bpy.context.object
second_ring.name = 'SecondTorus'
second_ring.data.materials.append(blue_material)

bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
third_ring = bpy.context.object
third_ring.name = 'ThirdTorus'
third_ring.data.materials.append(blue_material)


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
