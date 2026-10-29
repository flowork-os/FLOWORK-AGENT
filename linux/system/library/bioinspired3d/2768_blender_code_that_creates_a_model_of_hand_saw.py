# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_creates_a_model_of_hand_saw" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that creates a model of hand saw.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_blade = bpy.data.materials.new(name="MaterialBlade")
material_blade.diffuse_color = (0.5, 0.5, 0.5, 1)
material_handle = bpy.data.materials.new(name="MaterialHandle")
material_handle.diffuse_color = (0.8, 0.4, 0.1, 1)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
blade = bpy.context.object
blade.scale = (4, 0.1, 0.5)
blade.name = "Blade"
blade.data.materials.append(material_blade)

for i in range(8):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.1, depth=0.2, location=(-3.5 + i, 0, -0.5))
    tooth = bpy.context.object
    tooth.rotation_euler[1] = math.pi / 2
    tooth.name = f"Tooth_{i + 1}"
    tooth.data.materials.append(material_blade)

bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.5, location=(4.5, 0, 0))
handle = bpy.context.object
handle.rotation_euler[1] = math.pi / 2
handle.name = "Handle"
handle.data.materials.append(material_handle)

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(5.2, 0, 0))
hole = bpy.context.object
hole.rotation_euler[1] = math.pi / 2
bpy.context.view_layer.objects.active = handle
bpy.ops.object.modifier_add(type='BOOLEAN')
handle.modifiers["Boolean"].operation = 'DIFFERENCE'
handle.modifiers["Boolean"].object = hole
bpy.ops.object.modifier_apply(modifier="Boolean")
bpy.data.objects.remove(hole)


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
