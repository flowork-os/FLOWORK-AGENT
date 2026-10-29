# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_building_quilt" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for building quilt

import bpy

# Reset the scene by removing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define two materials for the cubes
mat_red = bpy.data.materials.new(name='Red')
mat_red.diffuse_color = (0.8, 0.2, 0.2, 1)
mat_green = bpy.data.materials.new(name='Green')
mat_green.diffuse_color = (0.2, 0.8, 0.2, 1)

# Create a grid of cubes using a nested loop
for x in range(5):
    for y in range(5):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0))
        cube_instance = bpy.context.object
        cube_instance.name = f'Cube_{x}_{y}'
        cube_instance.data.materials.append(mat_red if (x + y) % 2 == 0 else mat_green)


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
