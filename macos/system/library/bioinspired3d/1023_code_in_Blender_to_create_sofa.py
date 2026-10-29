# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_create_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to create sofa.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Sofa and cushion materials
brown_material = bpy.data.materials.new(name="BrownMaterial")
brown_material.diffuse_color = (0.5, 0.25, 0.25, 1)
gray_material = bpy.data.materials.new(name="GrayMaterial")
gray_material.diffuse_color = (0.75, 0.75, 0.75, 1)

# Create the main body of the sofa
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
sofa_body = bpy.context.object
sofa_body.name = "Sofa Body"
sofa_body.scale = (2, 1, 0.5)
sofa_body.data.materials.append(brown_material)

# Construct the backrest
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.75, 1.25))
back_support = bpy.context.object
back_support.name = "Back Support"
back_support.scale = (2, 0.25, 0.75)
back_support.data.materials.append(brown_material)

# Generate seat cushions
for index in range(3):
    offset = (index - 1) * 1.3
    bpy.ops.mesh.primitive_cube_add(size=1, location=(offset, 0, 1))
    cushion = bpy.context.object
    cushion.name = f"Cushion {index + 1}"
    cushion.scale = (0.6, 0.9, 0.2)
    cushion.data.materials.append(gray_material)

# Generate backrest cushions
for index in range(3):
    offset = (index - 1) * 1.3
    bpy.ops.mesh.primitive_cube_add(size=1, location=(offset, -0.75, 1.75))
    back_cushion = bpy.context.object
    back_cushion.name = f"Back Cushion {index + 1}"
    back_cushion.scale = (0.6, 0.2, 0.6)
    back_cushion.data.materials.append(gray_material)


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
