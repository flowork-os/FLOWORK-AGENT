# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_build_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to build a model of sofa

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa
sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.6, 0.3, 0.1, 1)  # Light brown color

# Define a function to create a sofa component
def make_sofa_part(part_name, location, dimensions):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    part = bpy.context.object
    part.scale = dimensions
    part.name = part_name
    part.data.materials.append(sofa_material)

# Create the main components of the sofa
make_sofa_part('Base', (0, 0, 0.5), (2, 1, 0.2))
make_sofa_part('Backrest', (0, -1, 1.1), (2, 0.2, 0.6))

# Create armrests
for i in range(2):
    armrest_x = 1.8 * (i * 2 - 1)
    make_sofa_part(f'Armrest_{i + 1}', (armrest_x, 0, 0.8), (0.2, 1, 0.4))

# Create cushions
for i in range(3):
    cushion_x = (i - 1) * 1.2
    make_sofa_part(f'Cushion_{i + 1}', (cushion_x, 0, 0.7), (0.4, 1, 0.2))


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
