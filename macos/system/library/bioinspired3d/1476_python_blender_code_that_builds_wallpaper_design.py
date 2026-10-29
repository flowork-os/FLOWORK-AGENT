# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_builds_wallpaper_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that builds wallpaper design.

import bpy

# Clear the existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create new materials for the shapes
red_material = bpy.data.materials.new(name='RedMaterial')
red_material.diffuse_color = (0.8, 0.2, 0.2, 1)
blue_material = bpy.data.materials.new(name='BlueMaterial')
blue_material.diffuse_color = (0.2, 0.2, 0.8, 1)

# Add a toroidal shape to the scene
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3, location=(0, 0, 0))
torus_base = bpy.context.object
torus_base.name = 'TorusBase'
torus_base.data.materials.append(red_material)

# Generate a grid of duplicated toruses
for x in range(3):
    for y in range(3):
        if x == 0 and y == 0:
            continue  # Skip the original torus
        bpy.ops.object.duplicate()
        new_torus = bpy.context.object
        new_torus.location = (x * 2, y * 2, 0)
        new_torus.data.materials[0] = red_material if (x + y) % 2 == 0 else blue_material


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
