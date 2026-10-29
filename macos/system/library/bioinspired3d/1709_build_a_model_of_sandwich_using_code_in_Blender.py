# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_sandwich_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of sandwich using code in Blender

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

def build_sandwich_layer(name, location, height, color):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    layer = bpy.context.object
    layer.name = name
    layer.scale[2] = height
    layer.data.materials.append(create_material(name, color))

colors = {
    'Bread': (0.96, 0.87, 0.70, 1),
    'Lettuce': (0.13, 0.55, 0.13, 1),
    'Tomato': (0.8, 0.1, 0.1, 1),
    'Cheese': (1, 0.9, 0.5, 1),
    'Ham': (0.91, 0.59, 0.48, 1)
}

build_sandwich_layer('Bottom Bread', (0, 0, 0), 0.1, colors['Bread'])
build_sandwich_layer('Lettuce', (0, 0, 0.2), 0.05, colors['Lettuce'])
build_sandwich_layer('Tomato', (0, 0, 0.3), 0.05, colors['Tomato'])
build_sandwich_layer('Cheese', (0, 0, 0.4), 0.05, colors['Cheese'])
build_sandwich_layer('Ham', (0, 0, 0.5), 0.05, colors['Ham'])
build_sandwich_layer('Top Bread', (0, 0, 0.7), 0.1, colors['Bread'])


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
