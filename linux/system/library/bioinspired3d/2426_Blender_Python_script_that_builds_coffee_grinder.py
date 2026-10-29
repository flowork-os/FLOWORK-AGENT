# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_builds_coffee_grinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that builds coffee grinder.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metallic_color = bpy.data.materials.new(name='Metallic Grey')
metallic_color.diffuse_color = (0.5, 0.5, 0.5, 1)
wooden_color = bpy.data.materials.new(name='Dark Wood')
wooden_color.diffuse_color = (0.55, 0.27, 0.07, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.2, location=(0, 0, 0))
base_part = bpy.context.object
base_part.name = 'Base'
base_part.data.materials.append(wooden_color)

bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=1.5, location=(0, 0, 0.85))
main_body = bpy.context.object
main_body.name = 'Body'
main_body.data.materials.append(metallic_color)

bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=0.1, location=(0, 0, 1.55))
top_section = bpy.context.object
top_section.name = 'Top'
top_section.data.materials.append(metallic_color)

bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(0.9, 0, 1.65), rotation=(0, math.pi/2, 0))
handle_part = bpy.context.object
handle_part.name = 'Handle'
handle_part.data.materials.append(metallic_color)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(1.45, 0, 1.65))
knob_part = bpy.context.object
knob_part.name = 'Knob'
knob_part.data.materials.append(wooden_color)


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
