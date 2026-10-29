# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_to_make_a_model_of_cat_scratcher" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code to make a model of cat scratcher

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

weathered_material = bpy.data.materials.new(name="Weathered Material")
weathered_material.diffuse_color = (0.5, 0.3, 0.2, 1)  # A faded brown shade

def add_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(material)
    return cube

def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

base_cube = add_cube(2, (0, 0, -0.5), "Base Cube", weathered_material)
scratching_post = add_cylinder(0.3, 3, (0, 0, 1), "Scratching Post", weathered_material)
worn_surface_cylinder = add_cylinder(0.32, 2.8, (0, 0, 1), "Worn Scratching Surface", weathered_material)
platform = add_cube(1, (0, 0, 2.5), "Top Platform", weathered_material)


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
