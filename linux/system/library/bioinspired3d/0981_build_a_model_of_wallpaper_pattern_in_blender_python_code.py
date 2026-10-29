# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_wallpaper_pattern_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of wallpaper pattern in blender python code

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up a material for the circles
circle_material = bpy.data.materials.new(name='Material for Circles')
circle_material.diffuse_color = (0.8, 0.2, 0.2, 1)

# Functional approach to create circles

def create_torus(x, y):
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(x, y, 0))
    new_torus = bpy.context.object
    new_torus.name = f'Circle_{x}_{y}'
    new_torus.data.materials.append(circle_material)

# Generate a grid of toruses
for x in range(5):
    for y in range(5):
        create_torus(x, y)


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
