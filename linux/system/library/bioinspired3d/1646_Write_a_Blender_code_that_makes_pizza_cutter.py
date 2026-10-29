# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_that_makes_pizza_cutter" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code that makes pizza cutter

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

blade = bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.05, location=(0, 0, 0))
blade_obj = bpy.context.object
blade_obj.name = 'Blade'
blade_material = bpy.data.materials.new(name='BladeMaterial')
blade_material.diffuse_color = (0.75, 0.75, 0.75, 1)
blade_obj.data.materials.append(blade_material)

handle = bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1, location=(0, -0.6, 0))
handle_obj = bpy.context.object
handle_obj.name = 'Handle'
handle_obj.rotation_euler = (math.pi / 2, 0, 0)
handle_material = bpy.data.materials.new(name='HandleMaterial')
handle_material.diffuse_color = (0.1, 0.1, 0.1, 1)
handle_obj.data.materials.append(handle_material)

pivot = bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.15, location=(0, 0, 0.025))
pivot_obj = bpy.context.object
pivot_obj.name = 'Pivot'
pivot_material = bpy.data.materials.new(name='PivotMaterial')
pivot_material.diffuse_color = (0.4, 0.4, 0.4, 1)
pivot_obj.data.materials.append(pivot_material)

bpy.context.view_layer.objects.active = pivot_obj
blade_obj.select_set(True)
pivot_obj.select_set(True)
bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)


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
