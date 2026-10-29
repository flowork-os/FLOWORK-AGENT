# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code_generate_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code generate a model of sofa

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Sofa material definition
sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.6, 0.35, 0.35, 1)  # A different shade of brown

# Create the Sofa geometry using a functional approach
def add_cube(name, loc, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(sofa_material)

# Adding different parts of the sofa
add_cube('Seat', (0, 0, 0.5), (2, 1, 0.2))
add_cube('Backrest', (0, -1.1, 1.2), (2, 0.2, 1))

# Create armrests
for index in range(2):
    armrest_pos = (2.1 * (index * 2 - 1), 0, 0.9)
    add_cube(f'Armrest {index + 1}', armrest_pos, (0.2, 1, 0.6))

# Create legs
for index in range(4):
    leg_position = (1.8 * (index % 2) - 0.9, 0.8 * (index // 2) - 0.4, 0.1)
    add_cube(f'Leg {index + 1}', leg_position, (0.2, 0.2, 0.5))


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
