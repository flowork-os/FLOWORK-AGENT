# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_chess_set_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of chess set in a Blender code

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_dark = bpy.data.materials.new(name="Dark_Material")
mat_dark.diffuse_color = (0.15, 0.15, 0.15, 1)
mat_light = bpy.data.materials.new(name="Light_Material")
mat_light.diffuse_color = (0.85, 0.85, 0.85, 1)

for x in range(8):
    for y in range(8):
        position_x = x - 3.5
        position_y = y - 3.5
        material = mat_dark if (x + y) % 2 == 0 else mat_light
        bpy.ops.mesh.primitive_cube_add(size=1, location=(position_x, position_y, 0))
        square = bpy.context.object
        square.name = f"BoardSquare_{x}_{y}"
        square.data.materials.append(material)

def add_pawn(pos):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.1, location=pos)

def add_rook(pos):
    bpy.ops.mesh.primitive_cube_add(size=0.8, location=pos)

def add_knight(pos):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.1, location=pos)
    bpy.ops.mesh.primitive_cone_add(radius1=0.25, radius2=0, depth=0.3, location=(pos[0], pos[1], pos[2] + 0.25))

def add_bishop(pos):
    bpy.ops.mesh.primitive_cone_add(radius1=0.3, radius2=0.1, depth=0.8, location=pos)

def add_queen(pos):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=pos)

def add_king(pos):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.15, location=pos)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(pos[0], pos[1], pos[2] + 0.2))

for i in range(8):
    add_pawn((i - 3.5, -2.5, 0.05))
add_rook((-3.5, -3.5, 0.05))
add_rook((3.5, -3.5, 0.05))
add_knight((-2.5, -3.5, 0.05))
add_knight((2.5, -3.5, 0.05))
add_bishop((-1.5, -3.5, 0.05))
add_bishop((1.5, -3.5, 0.05))
add_queen((0.5, -3.5, 0.05))
add_king((-0.5, -3.5, 0.05))


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
