# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_building_basketball" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for building basketball

import bpy

# Reset the scene by removing all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials
mat_orange = bpy.data.materials.new(name='BasketballOrange')
mat_orange.diffuse_color = (1.0, 0.55, 0.0, 1)
mat_black = bpy.data.materials.new(name='BasketballBlack')
mat_black.diffuse_color = (0, 0, 0, 1)

# Add a basketball sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
ball = bpy.context.object
ball.name = 'Basketball'
ball.data.materials.append(mat_orange)

# Create lines using a loop
line_angles = [(1.5708, 'Horizontal Line'), (0, 'Vertical Line'), (0.7854, 'Diagonal Line 1'), (-0.7854, 'Diagonal Line 2')]
for angle, name in line_angles:
    bpy.ops.mesh.primitive_cylinder_add(radius=1.01, depth=0.05, location=(0, 0, 0), rotation=(angle, 0, 0))
    line_object = bpy.context.object
    line_object.name = name
    line_object.data.materials.append(mat_black)


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
