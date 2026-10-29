# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code__create_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code, create sofa

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for sofa and cushions
sofa_material = bpy.data.materials.new(name='Sofa')
sofa_material.diffuse_color = (0.5, 0.25, 0.1, 1)
cushion_material = bpy.data.materials.new(name='Cushion')
cushion_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Create the sofa base
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
sofa_base = bpy.context.object
sofa_base.name = 'Base'
sofa_base.scale = (2, 1, 0.5)
sofa_base.data.materials.append(sofa_material)

# Add the backrest to the sofa
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.75, 1.25))
backrest = bpy.context.object
backrest.name = 'Backrest'
backrest.scale = (2, 0.1, 1)
backrest.data.materials.append(sofa_material)

# Generate cushions in a loop
for index in range(3):
    cushion_x = (index - 1) * 1.3
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cushion_x, 0, 1.1))
    cushion = bpy.context.object
    cushion.name = f'Cushion {index + 1}'
    cushion.scale = (0.6, 0.8, 0.4)
    cushion.data.materials.append(cushion_material)


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
