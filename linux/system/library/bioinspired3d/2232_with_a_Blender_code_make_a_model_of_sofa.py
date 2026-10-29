# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code_make_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code make a model of sofa.

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a dark gray material for the sofa
sofaShade = bpy.data.materials.new(name='Sofa Shade')
sofaShade.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to add a cube and set its properties
def add_cube(size, position, name, dimensions):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.name = name
    cube.scale = dimensions
    cube.data.materials.append(sofaShade)

# Construct the sofa
add_cube(2, (0, 0, 0.5), 'Sofa Base', (2, 1, 0.2))
add_cube(2, (0, -0.9, 1.1), 'Sofa Backrest', (2, 0.2, 0.6))

# Create armrests using a loop
for j in range(2):
    armrestLoc = (1.9 * (j * 2 - 1), 0, 0.9)
    add_cube(2, armrestLoc, f'Armrest {j + 1}', (0.2, 1, 0.5))


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
