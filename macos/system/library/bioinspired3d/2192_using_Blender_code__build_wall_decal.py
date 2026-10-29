# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code__build_wall_decal" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code, build wall decal

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the wall with light gray color
wall_color = bpy.data.materials.new(name='Light Gray')
wall_color.diffuse_color = (0.8, 0.8, 0.8, 1)

# Create the wall using a plane
bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, 0))
wall_plane = bpy.context.object
wall_plane.name = 'Wall Plane'
wall_plane.data.materials.append(wall_color)

# Define a material for the pattern squares
pattern_material = bpy.data.materials.new(name='Dark Gray')
pattern_material.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to add a square at specific coordinates
def add_square(x_pos, y_pos):
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(x_pos, y_pos, 0.01))
    new_square = bpy.context.object
    new_square.name = f'Square_{x_pos+3}_{y_pos+3}'
    new_square.data.materials.append(pattern_material)

# Create a grid of squares
for x in range(-2, 3):
    for y in range(-2, 3):
        add_square(x, y)


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
