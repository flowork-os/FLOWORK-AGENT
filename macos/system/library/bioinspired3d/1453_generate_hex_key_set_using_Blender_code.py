# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_hex_key_set_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate hex key set using Blender code

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the components
metallic_color = bpy.data.materials.new(name='Metal Color')
metallic_color.diffuse_color = (0.5, 0.5, 0.5, 1)

dark_color = bpy.data.materials.new(name='Dark Holder')
dark_color.diffuse_color = (0.1, 0.1, 0.1, 1)

# Create hex keys using a loop
sizes = [0.1, 0.12, 0.15, 0.18, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45]
for idx in range(len(sizes)):
    bpy.ops.mesh.primitive_cylinder_add(radius=sizes[idx], depth=2, location=(idx * 0.5, 0, 1))
    key = bpy.context.object
    key.name = f'Key {idx + 1}'
    key.data.materials.append(metallic_color)
    bpy.ops.transform.rotate(value=math.pi / 2, orient_axis='X')

# Add the holder
bpy.ops.mesh.primitive_cube_add(size=1, location=(2.25, 0, 0.5))
holder = bpy.context.object
holder.scale = (5, 0.5, 1)
holder.name = 'Key Holder'
holder.data.materials.append(dark_color)


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
