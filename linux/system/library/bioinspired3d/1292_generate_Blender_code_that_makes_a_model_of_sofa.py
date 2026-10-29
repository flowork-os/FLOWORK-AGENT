# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_makes_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that makes a model of sofa.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the sofa
sofa_texture = bpy.data.materials.new(name='SofaTexture')
sofa_texture.diffuse_color = (0.6, 0.1, 0.1, 1)  # A slightly different shade

# Function to create a cube with specified parameters

def create_cube(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(sofa_texture)
    return cube

# Create the seat
create_cube('SofaSeat', (0, 0, 0.5), (2, 1, 0.2))

# Create the backrest
create_cube('SofaBackrest', (0, -0.9, 1.2), (2, 0.2, 1))

# Create armrests with a loop
for index in range(2):
    position_x = 2 * (index * 2 - 1)
    create_cube(f'Armrest_{index + 1}', (position_x, 0, 0.9), (0.2, 1, 0.7))


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
