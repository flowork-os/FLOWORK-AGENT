# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_constructs_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that constructs a model of sofa.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_material = bpy.data.materials.new(name='Sofa Material')
sofa_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # A warm brown tone

# Function to create a cube with specified parameters

def create_cube(size, location, scale, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(sofa_material)
    return cube

# Create the main body of the sofa
base_cube = create_cube(2, (0, 0, 0.5), (3, 1.5, 0.5), 'Sofa Base')

# Generate armrests
for index in range(2):
    x_position = 3 * (index * 2 - 1)
    create_cube(2, (x_position, 0, 1.25), (0.2, 1.5, 0.75), f'Armrest {index + 1}')

# Create the backrest
create_cube(2, (0, -1.5, 1.25), (3, 0.2, 0.75), 'Sofa Backrest')


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
