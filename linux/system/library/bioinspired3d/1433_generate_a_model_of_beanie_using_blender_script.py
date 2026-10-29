# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_beanie_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of beanie using blender script

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a material for the beanie
beanie_color_material = bpy.data.materials.new(name='BeanieColor')
beanie_color_material.diffuse_color = (0.5, 0.1, 0.1, 1)  # Dark red tone

# Create the beanie object
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1))
beanie = bpy.context.object
beanie.name = 'Beanie'
beanie.scale.z = 0.6  # Scale down on the Z-axis to flatten
beanie.data.materials.append(beanie_color_material)

# Create the brim as a torus
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.2, location=(0, 0, 0.6))
brim = bpy.context.object
brim.name = 'Brim'
brim.data.materials.append(beanie_color_material)


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
