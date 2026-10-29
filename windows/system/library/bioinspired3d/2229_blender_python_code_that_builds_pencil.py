# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_builds_pencil" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that builds pencil

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

yellow_color = bpy.data.materials.new(name='YellowColor')
yellow_color.diffuse_color = (1, 1, 0, 1)
pink_color = bpy.data.materials.new(name='PinkColor')
pink_color.diffuse_color = (1, 0.75, 0.8, 1)
gray_color = bpy.data.materials.new(name='GrayColor')
gray_color.diffuse_color = (0.5, 0.5, 0.5, 1)

bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.1, depth=2, location=(0, 0, 1))
body = bpy.context.object
body.name = 'PencilBody'
body.data.materials.append(yellow_color)

bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.1, radius2=0, depth=0.2, location=(0, 0, 2.1))
tip = bpy.context.object
tip.name = 'PencilTip'
tip.data.materials.append(gray_color)

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.11, depth=0.1, location=(0, 0, -0.05))
holder = bpy.context.object
holder.name = 'EraserHolder'
holder.data.materials.append(gray_color)

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.1, depth=0.2, location=(0, 0, -0.15))
eraser = bpy.context.object
eraser.name = 'Eraser'
eraser.data.materials.append(pink_color)


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
