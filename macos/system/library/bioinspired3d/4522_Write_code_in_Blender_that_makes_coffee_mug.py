# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_that_makes_coffee_mug" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender that makes coffee mug.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

white_material = bpy.data.materials.new(name="White Material")
white_material.diffuse_color = (1, 1, 1, 1)  # Set color to white

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(white_material)
    return cylinder

mug_body = create_cylinder(1, 1.5, (0, 0, 0.75), "Mug Body")
mug_inner = create_cylinder(0.9, 1.4, (0, 0, 0.8), "Mug Inner")

bool_modifier = mug_body.modifiers.new(type="BOOLEAN", name="Hollowing Modifier")
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = mug_inner
bpy.context.view_layer.objects.active = mug_body
bpy.ops.object.modifier_apply(modifier="Hollowing Modifier")
bpy.data.objects.remove(mug_inner)

bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(1.5, 0, 0.75), major_radius=0.5, minor_radius=0.1, rotation=(math.pi/2, 0, 0))
handle = bpy.context.object
handle.name = "Mug Handle"
handle.data.materials.append(white_material)

handle_modifier = mug_body.modifiers.new(type="BOOLEAN", name="Attach Handle")
handle_modifier.operation = 'UNION'
handle_modifier.object = handle
bpy.context.view_layer.objects.active = mug_body
bpy.ops.object.modifier_apply(modifier="Attach Handle")
bpy.data.objects.remove(handle)


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
