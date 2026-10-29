# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_creates_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that creates a model of sofa.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.5, 0.3, 0.2, 1)  # A warm brown tone

# Function to add a cube with specific properties

def add_cube(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(sofa_material)
    return cube

# Create the main components of the sofa
base = add_cube('Base', (0, 0, 0.5), (3, 1, 0.5))
backrest = add_cube('Backrest', (0, -1, 1.5), (3, 0.2, 1))

# Create armrests
for index in range(2):
    position_x = 3 * (index * 2 - 1)
    add_cube(f'Armrest_{index + 1}', (position_x, 0, 1), (0.2, 1, 1))

# Create seat cushions
for index in range(3):
    position_x = 2 * (index - 1)
    add_cube(f'Seat_{index + 1}', (position_x, 0, 1), (0.9, 1, 0.2))


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
