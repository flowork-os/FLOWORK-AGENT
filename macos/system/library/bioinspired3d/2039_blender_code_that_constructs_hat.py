# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_constructs_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that constructs hat

import bpy

# Clear all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the hat
material_for_hat = bpy.data.materials.new(name='HatColor')
material_for_hat.diffuse_color = (0.5, 0.25, 0.1, 1)  # A warm brown color

# Create the brim
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.1, location=(0, 0, 0))
brim_part = bpy.context.object
brim_part.name = 'Brim'
brim_part.data.materials.append(material_for_hat)

# Now create the crown
bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=1, location=(0, 0, 0.55))
crown_part = bpy.context.object
crown_part.name = 'Crown'
crown_part.data.materials.append(material_for_hat)


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
