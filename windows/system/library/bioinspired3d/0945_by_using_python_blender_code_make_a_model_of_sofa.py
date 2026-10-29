# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code_make_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code make a model of sofa

import bpy

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define the sofa material
brown_material = bpy.data.materials.new(name='BrownMaterial')
brown_material.diffuse_color = (0.5, 0.25, 0.25, 1)

# Create the main components of the sofa
# Base
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base_part = bpy.context.object
base_part.scale = (1.5, 0.5, 0.2)
base_part.name = 'SofaBase'
base_part.data.materials.append(brown_material)

# Backrest
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.6, 1.1))
backrest_part = bpy.context.object
backrest_part.scale = (1.5, 0.1, 0.6)
backrest_part.name = 'SofaBackrest'
backrest_part.data.materials.append(brown_material)

# Armrests using a loop
armrest_positions = [-1.5, 1.5]
for pos in armrest_positions:
    bpy.ops.mesh.primitive_cube_add(size=2, location=(pos, 0, 0.75))
    armrest_part = bpy.context.object
    armrest_part.scale = (0.1, 0.5, 0.4)
    armrest_part.name = f'Armrest_{int((pos + 1.5) / 3)}'
    armrest_part.data.materials.append(brown_material)


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
