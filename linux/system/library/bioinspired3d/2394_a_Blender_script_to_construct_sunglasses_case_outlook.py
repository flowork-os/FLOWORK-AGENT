# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_construct_sunglasses_case_outlook" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to construct sunglasses case outlook.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the case
case_material = bpy.data.materials.new(name='Case Material')
case_material.diffuse_color = (0.2, 0.2, 0.2, 1)  # Dark gray color

# Create the main body and bottom part using a loop for efficiency
parts = []
for i, (loc, scale, name) in enumerate([((0, 0, 0), (2, 1, 0.5), 'Main Body'), ((0, 0, -0.5), (2, 1, 0.25), 'Bottom Part')]):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc)
    part = bpy.context.object
    part.name = name
    part.scale = scale
    part.data.materials.append(case_material)
    parts.append(part)

# Select and join the created parts
bpy.ops.object.select_all(action='DESELECT')
for part in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()


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
