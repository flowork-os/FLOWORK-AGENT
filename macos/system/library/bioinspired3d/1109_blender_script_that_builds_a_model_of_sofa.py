# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_builds_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that builds a model of sofa.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # Medium brown color

# Function to add a cube with specific parameters

def add_cube(size, location, name, scale_factors, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale_factors
    cube.data.materials.append(material)
    return cube

# Create the base of the sofa
add_cube(2, (0, 0, 0.5), 'SofaBase', (2, 1, 0.2), sofa_material)

# Create the backrest
add_cube(2, (0, -0.9, 1.1), 'SofaBackrest', (2, 0.1, 0.6), sofa_material)

# Create armrests with a loop
for index in range(2):
    position_x = 1.9 * (index * 2 - 1)
    add_cube(2, (position_x, 0, 0.7), f'SofaArmrest{index + 1}', (0.1, 1, 0.4), sofa_material)


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
