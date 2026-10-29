# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_hat_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of hat in Blender code

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the hat
hat_color = bpy.data.materials.new(name='Hat Color')
hat_color.diffuse_color = (0.5, 0.25, 0.1, 1)

band_color = bpy.data.materials.new(name='Band Color')
band_color.diffuse_color = (0.1, 0.1, 0.1, 1)

# Create brim
bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=0.1, location=(0, 0, 0))
brim = bpy.context.object
brim.name = 'Brim'
brim.data.materials.append(hat_color)

# Create crown
bpy.ops.mesh.primitive_cone_add(radius1=1, radius2=0.8, depth=2, location=(0, 0, 1.05))
crown = bpy.context.object
crown.name = 'Crown'
crown.data.materials.append(hat_color)

# Create band
bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.2, location=(0, 0, 0.9))
band = bpy.context.object
band.name = 'Band'
band.data.materials.append(band_color)


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
