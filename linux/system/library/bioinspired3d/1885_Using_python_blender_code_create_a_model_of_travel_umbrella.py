# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_python_blender_code_create_a_model_of_travel_umbrella" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using python blender code create a model of travel umbrella

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

canopy_material = bpy.data.materials.new(name='CanopyMaterial')
canopy_material.diffuse_color = (0.8, 0.1, 0.1, 1)  # Bright red for the canopy
shaft_material = bpy.data.materials.new(name='ShaftMaterial')
shaft_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray for the shaft

def create_canopy():
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1, depth=0.5, location=(0, 0, 0.25))
    canopy_object = bpy.context.object
    canopy_object.name = 'Canopy'
    canopy_object.data.materials.append(canopy_material)

def create_shaft():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0, 0, -1))
    shaft_object = bpy.context.object
    shaft_object.name = 'Shaft'
    shaft_object.data.materials.append(shaft_material)

def create_handle():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(0, 0, -2.25))
    handle_object = bpy.context.object
    handle_object.name = 'Handle'
    handle_object.data.materials.append(shaft_material)

create_canopy()
create_shaft()
create_handle()


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
