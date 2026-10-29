# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script__generate_chess_set" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script, generate chess set.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_dark = bpy.data.materials.new(name="Dark Material")
mat_dark.diffuse_color = (0.1, 0.1, 0.1, 1)
mat_light = bpy.data.materials.new(name="Light Material")
mat_light.diffuse_color = (0.9, 0.9, 0.9, 1)

size = 8
square_dim = 1
for x in range(size):
    for y in range(size):
        bpy.ops.mesh.primitive_plane_add(size=square_dim, location=(x * square_dim, y * square_dim, 0))
        plane = bpy.context.object
        plane.data.materials.append(mat_light if (x + y) % 2 == 0 else mat_dark)

def create_piece(type, pos):
    if type == 'pawn':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(pos[0], pos[1], pos[2] + 0.2))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(pos[0], pos[1], pos[2]))
    elif type == 'rook':
        bpy.ops.mesh.primitive_cube_add(size=0.4, location=(pos[0], pos[1], pos[2] + 0.2))
    elif type == 'knight':
        bpy.ops.mesh.primitive_cone_add(radius1=0.2, depth=0.4, location=(pos[0], pos[1], pos[2] + 0.2))
    elif type == 'bishop':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(pos[0], pos[1], pos[2] + 0.2))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(pos[0], pos[1], pos[2]))
    elif type == 'queen':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(pos[0], pos[1], pos[2] + 0.3))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.6, location=(pos[0], pos[1], pos[2]))
    elif type == 'king':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(pos[0], pos[1], pos[2] + 0.3))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.6, location=(pos[0], pos[1], pos[2]))

for i in range(size):
    create_piece('pawn', (i * square_dim, 1 * square_dim, 0))
    create_piece('pawn', (i * square_dim, 6 * square_dim, 0))

create_piece('rook', (0 * square_dim, 0 * square_dim, 0))
create_piece('rook', (7 * square_dim, 0 * square_dim, 0))
create_piece('rook', (0 * square_dim, 7 * square_dim, 0))
create_piece('rook', (7 * square_dim, 7 * square_dim, 0))

create_piece('knight', (1 * square_dim, 0 * square_dim, 0))
create_piece('knight', (6 * square_dim, 0 * square_dim, 0))
create_piece('knight', (1 * square_dim, 7 * square_dim, 0))
create_piece('knight', (6 * square_dim, 7 * square_dim, 0))

create_piece('bishop', (2 * square_dim, 0 * square_dim, 0))
create_piece('bishop', (5 * square_dim, 0 * square_dim, 0))
create_piece('bishop', (2 * square_dim, 7 * square_dim, 0))
create_piece('bishop', (5 * square_dim, 7 * square_dim, 0))

create_piece('queen', (3 * square_dim, 0 * square_dim, 0))
create_piece('queen', (3 * square_dim, 7 * square_dim, 0))

create_piece('king', (4 * square_dim, 0 * square_dim, 0))
create_piece('king', (4 * square_dim, 7 * square_dim, 0))


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
