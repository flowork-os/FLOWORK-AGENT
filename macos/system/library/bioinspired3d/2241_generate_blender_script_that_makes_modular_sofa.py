# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_that_makes_modular_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script that makes modular sofa

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.4, 0.2, 0.1, 1)  # A darker brown color

# Function to create a cube with specific parameters
def create_cube(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(sofa_material)
    return cube

# Create the sofa components
base = create_cube('SofaBase', (0, 0, 0.5), (1.5, 0.75, 0.25))
backrest = create_cube('Backrest', (0, -0.75, 1.25), (1.5, 0.1, 0.75))

# Create armrests
for index in range(2):
    position_x = 1.5 * (index * 2 - 1)
    create_cube(f'Armrest_{index + 1}', (position_x, 0, 0.75), (0.1, 0.75, 0.5))


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
