# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_to_make_a_model_of_wallpaper_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script to make a model of wallpaper design

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Materials with colors defined
red_color = bpy.data.materials.new(name='RedColor')
red_color.diffuse_color = (0.8, 0.2, 0.2, 1)
blue_color = bpy.data.materials.new(name='BlueColor')
blue_color.diffuse_color = (0.2, 0.2, 0.8, 1)

# Create a torus shape
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3, location=(0, 0, 0))
base_torus = bpy.context.object
base_torus.name = 'BaseTorus'
base_torus.data.materials.append(red_color)

# Duplicate and arrange toruses in a grid
for i in range(3):
    for j in range(3):
        if i == 0 and j == 0:
            continue  # Skip the original torus
        bpy.ops.object.duplicate()
        new_torus = bpy.context.object
        new_torus.location = (i * 2, j * 2, 0)
        new_torus.data.materials[0] = red_color if (i + j) % 2 == 0 else blue_color


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
