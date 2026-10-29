# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_code_create_a_model_of_pencil" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender code create a model of pencil.

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with different names
mat_yellow = bpy.data.materials.new(name='Bright Yellow')
mat_yellow.diffuse_color = (1, 1, 0, 1)
mat_pink = bpy.data.materials.new(name='Soft Pink')
mat_pink.diffuse_color = (1, 0.75, 0.8, 1)
mat_gray = bpy.data.materials.new(name='Neutral Gray')
mat_gray.diffuse_color = (0.5, 0.5, 0.5, 1)
mat_wood = bpy.data.materials.new(name='Natural Wood')
mat_wood.diffuse_color = (0.8, 0.52, 0.25, 1)

# Create shapes using procedural functions

# Create pencil body
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.1, depth=2, location=(0, 0, 1))
pencil = bpy.context.object
pencil.name = 'Pencil Body'
pencil.data.materials.append(mat_yellow)

# Create sharpened tip
bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.1, radius2=0, depth=0.3, location=(0, 0, 2.15))
tip = bpy.context.object
tip.name = 'Sharpened Tip'
tip.data.materials.append(mat_wood)

# Create eraser holder
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.11, depth=0.1, location=(0, 0, 0.05))
eraser_holder = bpy.context.object
eraser_holder.name = 'Eraser Holder'
eraser_holder.data.materials.append(mat_gray)

# Create eraser
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.1, depth=0.1, location=(0, 0, -0.05))
eraser = bpy.context.object
eraser.name = 'Eraser'
eraser.data.materials.append(mat_pink)


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
