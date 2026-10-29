# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_script__make_a_model_of_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender script, make a model of wallpaper pattern

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the cubes
material = bpy.data.materials.new(name='Material')
material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Set to medium gray

# Function to create a cube at a specific position
def create_cube_at(x, y):
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, 0))
    cube = bpy.context.object
    cube.data.materials.append(material)

# Generate a grid of cubes using nested loops
for i in range(5):
    for j in range(5):
        create_cube_at(i, j)  # Using default spacing of 1.0


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
