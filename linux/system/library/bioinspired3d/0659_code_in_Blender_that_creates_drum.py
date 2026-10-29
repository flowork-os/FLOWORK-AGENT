# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_creates_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that creates drum

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define drum materials
material_drum_body = bpy.data.materials.new('DrumMaterial')
material_drum_body.diffuse_color = (0.5, 0.25, 0.1, 1)
material_drum_top = bpy.data.materials.new('TopMaterial')
material_drum_top.diffuse_color = (0.8, 0.8, 0.8, 1)

# Create the drum components using a loop
for name, radius, depth, z_offset, material in [
    ('Drum Body', 1, 0.5, 0, material_drum_body),
    ('Drum Top', 1.05, 0.1, 0.3, material_drum_top),
    ('Drum Bottom', 1.05, 0.1, -0.3, material_drum_body)
]:
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=(0, 0, z_offset))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)


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
