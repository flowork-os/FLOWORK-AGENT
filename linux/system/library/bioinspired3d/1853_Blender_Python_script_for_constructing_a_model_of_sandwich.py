# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_constructing_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for constructing a model of sandwich.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def add_cube(name, size, position, scale_factor, color_tuple):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.name = name
    cube.scale[2] = scale_factor
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color_tuple
    cube.data.materials.append(material)

layer_params = [
    ('Bottom Bread', 2, (0, 0, 0), 0.1, (0.96, 0.87, 0.70, 1)),
    ('Lettuce', 1.8, (0, 0, 0.2), 0.05, (0.13, 0.55, 0.13, 1)),
    ('Tomato', 1.8, (0, 0, 0.3), 0.05, (0.89, 0.15, 0.07, 1)),
    ('Cheese', 1.8, (0, 0, 0.4), 0.05, (1.0, 0.83, 0.0, 1)),
    ('Meat', 1.8, (0, 0, 0.5), 0.1, (0.55, 0.27, 0.07, 1)),
    ('Top Bread', 2, (0, 0, 0.7), 0.1, (0.96, 0.87, 0.70, 1))
]

for params in layer_params:
    add_cube(*params)


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
