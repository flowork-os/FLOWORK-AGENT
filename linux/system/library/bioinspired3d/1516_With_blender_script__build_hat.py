# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script__build_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script, build hat.

import bpy

# Clear the current mesh objects in the Blender scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Materials for the hat and band
material_hat = bpy.data.materials.new(name='MaterialHat')
material_hat.diffuse_color = (0.5, 0.25, 0.1, 1)  # Color for the hat
material_band = bpy.data.materials.new(name='MaterialBand')
material_band.diffuse_color = (0.1, 0.1, 0.1, 1)  # Color for the band

# Create the brim
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.1, location=(0, 0, 0))
brim_object = bpy.context.object
brim_object.name = 'Brim'
brim_object.data.materials.append(material_hat)

# Create the crown
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.75, location=(0, 0, 0.5))
crown_object = bpy.context.object
crown_object.name = 'Crown'
crown_object.data.materials.append(material_hat)

# Create the band
bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.2, location=(0, 0, 0.3))
band_object = bpy.context.object
band_object.name = 'Band'
band_object.data.materials.append(material_band)


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
