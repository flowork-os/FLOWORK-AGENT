# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_Python_script__construct_a_model_of_floor_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender Python script, construct a model of floor lamp.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

base_material = bpy.data.materials.new(name="Base Material")
base_material.diffuse_color = (0.25, 0.25, 0.25, 1)  # Slightly lighter gray
shade_material = bpy.data.materials.new(name="Shade Material")
shade_material.diffuse_color = (1, 1, 0.85, 1)  # Soft yellow

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

def create_cone(radius1, radius2, depth, location, name, material):
    bpy.ops.mesh.primitive_cone_add(radius1=radius1, radius2=radius2, depth=depth, location=location)
    cone = bpy.context.object
    cone.name = name
    cone.data.materials.append(material)
    return cone

base = create_cylinder(0.2, 0.05, (0, 0, 0.025), "Lamp Base", base_material)
stand = create_cylinder(0.05, 2, (0, 0, 1.025), "Lamp Stand", base_material)
lampshade = create_cone(0.5, 0.2, 0.6, (0, 0, 2.3), "Lamp Shade", shade_material)

bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0.1, 0, 0.5))
switch = bpy.context.object
switch.name = "Lamp Switch"
switch.data.materials.append(base_material)


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
