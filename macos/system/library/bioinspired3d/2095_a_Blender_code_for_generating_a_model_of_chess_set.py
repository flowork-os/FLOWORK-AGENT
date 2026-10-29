# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_generating_a_model_of_chess_set" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for generating a model of chess set.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_dark = bpy.data.materials.new(name="Material Dark")
material_dark.diffuse_color = (0.1, 0.1, 0.1, 1)
material_light = bpy.data.materials.new(name="Material Light")
material_light.diffuse_color = (0.9, 0.9, 0.9, 1)

board_dimension = 8
size_of_square = 1
for row in range(board_dimension):
    for col in range(board_dimension):
        bpy.ops.mesh.primitive_plane_add(size=size_of_square, location=(row * size_of_square, col * size_of_square, 0))
        current_square = bpy.context.object
        if (row + col) % 2 == 0:
            current_square.data.materials.append(material_light)
        else:
            current_square.data.materials.append(material_dark)

def add_pawn(pos):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(pos[0], pos[1], pos[2] + 0.2))

def add_rook(pos):
    bpy.ops.mesh.primitive_cube_add(size=0.4, location=(pos[0], pos[1], pos[2] + 0.2))

def add_knight(pos):
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, depth=0.4, location=(pos[0], pos[1], pos[2] + 0.2))

def add_bishop(pos):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(pos[0], pos[1], pos[2] + 0.2))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(pos[0], pos[1], pos[2]))

def add_queen(pos):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(pos[0], pos[1], pos[2] + 0.3))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.6, location=(pos[0], pos[1], pos[2]))

def add_king(pos):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(pos[0], pos[1], pos[2] + 0.3))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.6, location=(pos[0], pos[1], pos[2]))

for i in range(board_dimension):
    add_pawn((i * size_of_square, 1 * size_of_square, 0))
    add_pawn((i * size_of_square, 6 * size_of_square, 0))

add_rook((0 * size_of_square, 0 * size_of_square, 0))
add_rook((7 * size_of_square, 0 * size_of_square, 0))
add_rook((0 * size_of_square, 7 * size_of_square, 0))
add_rook((7 * size_of_square, 7 * size_of_square, 0))

add_knight((1 * size_of_square, 0 * size_of_square, 0))
add_knight((6 * size_of_square, 0 * size_of_square, 0))
add_knight((1 * size_of_square, 7 * size_of_square, 0))
add_knight((6 * size_of_square, 7 * size_of_square, 0))

add_bishop((2 * size_of_square, 0 * size_of_square, 0))
add_bishop((5 * size_of_square, 0 * size_of_square, 0))
add_bishop((2 * size_of_square, 7 * size_of_square, 0))
add_bishop((5 * size_of_square, 7 * size_of_square, 0))

add_queen((3 * size_of_square, 0 * size_of_square, 0))
add_queen((3 * size_of_square, 7 * size_of_square, 0))

add_king((4 * size_of_square, 0 * size_of_square, 0))
add_king((4 * size_of_square, 7 * size_of_square, 0))


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
