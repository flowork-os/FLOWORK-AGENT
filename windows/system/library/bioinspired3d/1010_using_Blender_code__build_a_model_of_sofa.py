# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code__build_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code, build a model of sofa.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the sofa and cushions
brown_material = bpy.data.materials.new(name='Brown Sofa')
brown_material.diffuse_color = (0.5, 0.25, 0.1, 1)
gray_material = bpy.data.materials.new(name='Gray Cushion')
gray_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Create the sofa's components
sofa_base = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
bpy.context.object.name = 'Sofa Base'
bpy.context.object.scale = (2, 1, 0.5)
bpy.context.object.data.materials.append(brown_material)

backrest = bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.75, 1.25))
bpy.context.object.name = 'Backrest'
bpy.context.object.scale = (2, 0.1, 1)
bpy.context.object.data.materials.append(brown_material)

# Generate cushions using a loop
for i in range(3):
    cushion_position = (i - 1) * 1.3
    cushion = bpy.ops.mesh.primitive_cube_add(size=1, location=(cushion_position, 0, 1.1))
bpy.context.object.name = f'Cushion {i + 1}'
bpy.context.object.scale = (0.6, 0.8, 0.4)
bpy.context.object.data.materials.append(gray_material)


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
