# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_sofa_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of sofa in blender code

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the couch
couch_material = bpy.data.materials.new(name='Couch Material')
couch_material.diffuse_color = (0.5, 0.25, 0.25, 1)  # Rich brown color

# Function to add a cube to the scene

def add_cube(size, position, scale_factor, identifier):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.scale = scale_factor
    cube.name = identifier
    cube.data.materials.append(couch_material)

# Create the sofa components
add_cube(2, (0, 0, 0.5), (3, 1.5, 0.5), 'Couch Base')

# Create armrests at specified positions
for j in range(2):
    pos_x = 3 * (j * 2 - 1)
    add_cube(2, (pos_x, 0, 1.25), (0.2, 1.5, 0.75), f'Armrest {j + 1}')

# Add the backrest
add_cube(2, (0, -1.5, 1.25), (3, 0.2, 0.75), 'Couch Backrest')


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
