# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_code_to_create_chessboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender code to create chessboard

import bpy

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up materials for the board
black_material = bpy.data.materials.new(name='BlackMaterial')
black_material.diffuse_color = (0, 0, 0, 1)
white_material = bpy.data.materials.new(name='WhiteMaterial')
white_material.diffuse_color = (1, 1, 1, 1)

# Chessboard dimensions
square_dim = 1
board_dim = 8 * square_dim

# Create the chessboard using nested loops
for r in range(8):
    for c in range(8):
        x_coord = c * square_dim - (board_dim / 2) + (square_dim / 2)
        y_coord = r * square_dim - (board_dim / 2) + (square_dim / 2)
        bpy.ops.mesh.primitive_plane_add(size=square_dim, location=(x_coord, y_coord, 0))
        plane = bpy.context.object
        plane.name = f'Square_{r * 8 + c + 1}'
        plane.data.materials.append(white_material if (r + c) % 2 == 0 else black_material)


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
