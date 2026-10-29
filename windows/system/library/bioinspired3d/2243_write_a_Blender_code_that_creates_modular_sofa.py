# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_creates_modular_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that creates modular sofa.

import bpy

# Clear the current mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the sofa
material_sofa = bpy.data.materials.new(name='SofaMaterial')
material_sofa.diffuse_color = (0.5, 0.3, 0.2, 1)  # Original brown color

# Create the main components of the sofa
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base = bpy.context.object
base.name = 'SofaBase'
base.scale = (1.5, 0.75, 0.25)
base.data.materials.append(material_sofa)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.75, 1.25))
backrest = bpy.context.object
backrest.name = 'Backrest'
backrest.scale = (1.5, 0.1, 0.75)
backrest.data.materials.append(material_sofa)

# Create armrests
armrest_positions = [(-1.5, 0, 0.75), (1.5, 0, 0.75)]
for index, position in enumerate(armrest_positions):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    armrest = bpy.context.object
    armrest.name = f'Armrest_{index + 1}'
    armrest.scale = (0.1, 0.75, 0.5)
    armrest.data.materials.append(material_sofa)


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
