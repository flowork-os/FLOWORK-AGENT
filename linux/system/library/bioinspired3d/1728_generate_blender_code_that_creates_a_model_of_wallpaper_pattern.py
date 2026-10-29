# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_that_creates_a_model_of_wallpaper_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code that creates a model of wallpaper pattern.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat1 = bpy.data.materials.new(name="Material_Red")
mat1.diffuse_color = (0.7, 0.2, 0.2, 1)
mat2 = bpy.data.materials.new(name="Material_Green")
mat2.diffuse_color = (0.2, 0.7, 0.2, 1)

def add_cubes_in_grid(rows, cols):
    for x in range(rows):
        for y in range(cols):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0))
            cube = bpy.context.object
            cube.name = f"GridCube_{x}_{y}"
            cube.data.materials.append(mat1 if (x + y) % 2 == 0 else mat2)

add_cubes_in_grid(5, 5)


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
