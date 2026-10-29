# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_makes_chessboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that makes chessboard

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the chessboard
material_black = bpy.data.materials.new(name='Material Black')
material_black.diffuse_color = (0, 0, 0, 1)
material_white = bpy.data.materials.new(name='Material White')
material_white.diffuse_color = (1, 1, 1, 1)

# Function to create a single square
def create_square(x, y, size, material):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(x, y, 0))
    square = bpy.context.object
    square.data.materials.append(material)

# Generate the chessboard
square_dimension = 1
for i in range(8):
    for j in range(8):
        current_material = material_white if (i + j) % 2 == 0 else material_black
        create_square(j * square_dimension, i * square_dimension, square_dimension, current_material)


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
