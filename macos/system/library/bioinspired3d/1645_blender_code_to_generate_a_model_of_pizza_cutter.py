# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_generate_a_model_of_pizza_cutter" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to generate a model of pizza cutter.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_cylinder(radius, depth, location, name, color):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    material = bpy.data.materials.new(name=name + "Material")
    material.diffuse_color = color
    obj.data.materials.append(material)
    return obj

blade = create_cylinder(0.3, 0.05, (0, 0, 0), "Blade", (0.8, 0.8, 0.8, 1))
handle = create_cylinder(0.1, 1, (0, -0.6, 0), "Handle", (0.2, 0.2, 0.2, 1))
pivot = create_cylinder(0.05, 0.15, (0, 0, 0.025), "Pivot", (0.5, 0.5, 0.5, 1))

handle.rotation_euler = (math.pi / 2, 0, 0)

bpy.context.view_layer.objects.active = pivot
blade.select_set(True)
pivot.select_set(True)
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
