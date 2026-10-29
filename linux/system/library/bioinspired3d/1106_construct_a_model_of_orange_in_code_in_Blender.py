# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_orange_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of orange in code in Blender

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up materials for the orange and stem
orange_mat = bpy.data.materials.new(name='OrangeMaterial')
orange_mat.diffuse_color = (1.0, 0.55, 0.0, 1)

stem_mat = bpy.data.materials.new(name='StemMaterial')
stem_mat.diffuse_color = (0.33, 0.42, 0.18, 1)

# Create the orange fruit
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 0))
fruit = bpy.context.object
fruit.name = 'Orange'
fruit.data.materials.append(orange_mat)

# Create the stem
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.2, location=(0, 0, 1.6))
stem = bpy.context.object
stem.name = 'Stem'
stem.data.materials.append(stem_mat)


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
