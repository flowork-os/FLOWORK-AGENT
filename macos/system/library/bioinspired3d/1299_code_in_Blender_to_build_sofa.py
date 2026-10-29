# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_build_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to build sofa.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize material for the sofa
material_sofa = bpy.data.materials.new(name='Material Sofa')
material_sofa.diffuse_color = (0.2, 0.2, 0.2, 1)  # Set to dark gray

# Create the main components of the sofa
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base = bpy.context.object
base.name = 'Sofa Base'
base.scale = (2, 1, 0.2)
base.data.materials.append(material_sofa)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.9, 1.1))
backrest = bpy.context.object
backrest.name = 'Sofa Backrest'
backrest.scale = (2, 0.2, 0.6)
backrest.data.materials.append(material_sofa)

# Add armrests to the sofa
for i in range(2):
    x_position = 1.9 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, 0.9))
    armrest = bpy.context.object
    armrest.name = f'Armrest {i + 1}'
    armrest.scale = (0.2, 1, 0.5)
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
