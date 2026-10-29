# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script_make_pencil" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script make pencil.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for the pencil
yellow_material = bpy.data.materials.new(name='YellowMaterial')
yellow_material.diffuse_color = (1, 1, 0, 1)
pink_material = bpy.data.materials.new(name='PinkMaterial')
pink_material.diffuse_color = (1, 0.75, 0.8, 1)
gray_material = bpy.data.materials.new(name='GrayMaterial')
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create pencil components
body = create_cylinder(0.1, 2, (0, 0, 1), 'PencilBody', yellow_material)
tip = bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.1, radius2=0, depth=0.2, location=(0, 0, 2.1))
tip = bpy.context.object

tip.name = 'PencilTip'
tip.data.materials.append(gray_material)

holder = create_cylinder(0.11, 0.1, (0, 0, -0.05), 'EraserHolder', gray_material)
eraser = create_cylinder(0.1, 0.2, (0, 0, -0.15), 'Eraser', pink_material)


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
