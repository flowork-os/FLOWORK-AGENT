# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_make_geometric_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to make geometric pattern.

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a unique material for the triangles
triangle_color = bpy.data.materials.new(name='Red Triangle')
triangle_color.diffuse_color = (0.8, 0.5, 0.2, 1)  # Orange color

# Function to instantiate a triangle

def instantiate_triangle(x_pos, y_pos):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=1, depth=0.1, location=(x_pos, y_pos, 0))
    triangle_instance = bpy.context.object
    triangle_instance.name = f'Triangle_{x_pos}_{y_pos}'
    triangle_instance.data.materials.append(triangle_color)

# Generate triangles in a grid format
for x in range(10):
    for y in range(10):
        instantiate_triangle(x, y)


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
