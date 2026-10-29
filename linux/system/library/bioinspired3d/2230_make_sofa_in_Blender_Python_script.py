# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_sofa_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make sofa in Blender Python script

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_material = bpy.data.materials.new(name='Sofa Material')
sofa_material.diffuse_color = (0.2, 0.2, 0.2, 1)  # Dark gray color

# Function to create a cube with specific properties
def create_cube(size, location, name, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(sofa_material)
    return cube

# Create the sofa components
base_scale = (2, 1, 0.2)
create_cube(2, (0, 0, 0.5), 'Base', base_scale)

backrest_scale = (2, 0.2, 0.6)
create_cube(2, (0, -0.9, 1.1), 'Backrest', backrest_scale)

# Create armrests using a loop
for index in range(2):
    armrest_position = (1.9 * (index * 2 - 1), 0, 0.9)
    armrest_scale = (0.2, 1, 0.5)
    create_cube(2, armrest_position, f'Armrest {index + 1}', armrest_scale)


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
