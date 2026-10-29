# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_that_makes_decorative_wall_panel" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code that makes decorative wall panel

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the panel and cubes
panel_mat = bpy.data.materials.new(name="PanelMat")
panel_mat.diffuse_color = (0.8, 0.8, 0.8, 1)
cube_mat = bpy.data.materials.new(name="CubeMat")
cube_mat.diffuse_color = (0.2, 0.2, 0.2, 1)

# Add the main panel
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
panel_plane = bpy.context.object
panel_plane.name = "PanelSurface"
panel_plane.data.materials.append(panel_mat)

# Create the grid of cubes
for x in range(-4, 5):
    for y in range(-4, 5):
        bpy.ops.mesh.primitive_cube_add(size=0.1, location=(x * 0.2, y * 0.2, 0.01))
        cube_object = bpy.context.object
        cube_object.name = f"CubeGrid_{x}_{y}"
        cube_object.data.materials.append(cube_mat)


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
