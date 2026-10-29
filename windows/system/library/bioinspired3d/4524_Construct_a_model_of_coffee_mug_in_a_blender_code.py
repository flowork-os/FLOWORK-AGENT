# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_coffee_mug_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of coffee mug in a blender code

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_white = bpy.data.materials.new(name="Material White")
material_white.diffuse_color = (1, 1, 1, 1)  # Define white color

def build_mug():
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
    body = bpy.context.object
    body.name = "Mug Body"
    body.data.materials.append(material_white)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=1.4, location=(0, 0, 0.8))
    inner = bpy.context.object
    inner.name = "Inner Mug"

    hollow_modifier = body.modifiers.new(type="BOOLEAN", name="Hollow Modifier")
    hollow_modifier.operation = 'DIFFERENCE'
    hollow_modifier.object = inner
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Hollow Modifier")
    bpy.data.objects.remove(inner)

    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(1.5, 0, 0.75), major_radius=0.5, minor_radius=0.1, rotation=(math.pi/2, 0, 0))
    handle = bpy.context.object
    handle.name = "Mug Handle"
    handle.data.materials.append(material_white)

    attach_modifier = body.modifiers.new(type="BOOLEAN", name="Attach Handle Modifier")
    attach_modifier.operation = 'UNION'
    attach_modifier.object = handle
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Attach Handle Modifier")
    bpy.data.objects.remove(handle)

build_mug()


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
