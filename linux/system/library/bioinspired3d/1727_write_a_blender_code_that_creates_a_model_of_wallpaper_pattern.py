# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_blender_code_that_creates_a_model_of_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a blender code that creates a model of wallpaper pattern.

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create and assign materials
mat_red = bpy.data.materials.new(name="Red")
mat_red.diffuse_color = (0.9, 0.1, 0.1, 1)
mat_green = bpy.data.materials.new(name="Green")
mat_green.diffuse_color = (0.1, 0.9, 0.1, 1)

# Function to create a cube at a given position
def create_colored_cube(x, y):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0))
    cube = bpy.context.object
    cube.name = f"Cube_{x}_{y}"
    cube.data.materials.append(mat_red if (x + y) % 2 == 0 else mat_green)

# Generate cubes in a grid pattern
for x in range(5):
    for y in range(5):
        create_colored_cube(x, y)


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
