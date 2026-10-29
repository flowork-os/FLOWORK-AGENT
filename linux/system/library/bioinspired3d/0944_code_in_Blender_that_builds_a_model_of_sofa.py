# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_builds_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that builds a model of sofa.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)

# Function to create a cube mesh

def create_cube(size, location, scale, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.object
    obj.scale = scale
    obj.name = name
    obj.data.materials.append(sofa_material)
    return obj

# Construct the sofa components
base_mesh = create_cube(2, (0, 0, 0.5), (1.5, 0.5, 0.2), 'SofaBase')
backrest_mesh = create_cube(2, (0, -0.6, 1.1), (1.5, 0.1, 0.6), 'Backrest')

# Create armrests
for index in range(2):
    position_x = 1.5 * (index * 2 - 1)
    create_cube(2, (position_x, 0, 0.75), (0.1, 0.5, 0.4), f'Armrest{index + 1}')


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
