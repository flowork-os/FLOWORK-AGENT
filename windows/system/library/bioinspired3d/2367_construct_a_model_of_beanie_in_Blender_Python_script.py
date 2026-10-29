# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_beanie_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of beanie in Blender Python script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

beanie_material_instance = bpy.data.materials.new(name='BeanieMaterialInstance')
beanie_material_instance.diffuse_color = (0.5, 0.1, 0.1, 1)  # Dark red color

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1))
beanie_object = bpy.context.object
beanie_object.name = 'Beanie'
beanie_object.scale[2] = 0.6  # Adjust height for beanie shape
beanie_object.data.materials.append(beanie_material_instance)

bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.2, location=(0, 0, 0.6))
brim_object = bpy.context.object
brim_object.name = 'Brim'
brim_object.data.materials.append(beanie_material_instance)


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
