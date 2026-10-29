# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_chess_set_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of chess set in Blender code

import bpy

# Clear the existing scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create chessboard materials
material_dark = bpy.data.materials.new(name="Chessboard_Dark")
material_dark.diffuse_color = (0.25, 0.25, 0.25, 1)
material_light = bpy.data.materials.new(name="Chessboard_Light")
material_light.diffuse_color = (0.75, 0.75, 0.75, 1)

# Generating the chessboard
for i in range(8):
    for j in range(8):
        pos_x = i - 3.5
        pos_y = j - 3.5
        mat_choice = material_dark if (i + j) % 2 == 0 else material_light
        bpy.ops.mesh.primitive_cube_add(size=1, location=(pos_x, pos_y, 0))
        board_square = bpy.context.object
        board_square.name = f"GridSquare_{i}_{j}"
        board_square.data.materials.append(mat_choice)

# Piece creation functions
def create_chess_piece_cylinder(radius, height, position):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)

def create_chess_piece_cube(size, position):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)

def create_chess_piece_cone(radius_top, radius_bottom, height, position):
    bpy.ops.mesh.primitive_cone_add(radius1=radius_top, radius2=radius_bottom, depth=height, location=position)

def create_chess_piece_sphere(radius, position):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=position)

# Create chess pieces
for idx in range(8):
    create_chess_piece_cylinder(0.3, 0.1, (idx - 3.5, -2.5, 0.05))
create_chess_piece_cube(0.8, (-3.5, -3.5, 0.05))
create_chess_piece_cube(0.8, (3.5, -3.5, 0.05))
create_chess_piece_cylinder(0.25, 0.1, (-2.5, -3.5, 0.05))
create_chess_piece_cylinder(0.25, 0.1, (2.5, -3.5, 0.05))
create_chess_piece_cone(0.3, 0.1, 0.8, (-1.5, -3.5, 0.05))
create_chess_piece_cone(0.3, 0.1, 0.8, (1.5, -3.5, 0.05))
create_chess_piece_sphere(0.35, (0.5, -3.5, 0.05))
create_chess_piece_cylinder(0.3, 0.15, (-0.5, -3.5, 0.05))
create_chess_piece_sphere(0.25, (-0.5, -3.5, 0.25))


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
