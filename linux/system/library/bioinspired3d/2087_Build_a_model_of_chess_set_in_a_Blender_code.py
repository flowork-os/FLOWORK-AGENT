# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_chess_set_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of chess set in a Blender code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the chessboard squares
mat_dark = bpy.data.materials.new(name="Material_Dark")
mat_dark.diffuse_color = (0.1, 0.1, 0.1, 1)
mat_light = bpy.data.materials.new(name="Material_Light")
mat_light.diffuse_color = (0.9, 0.9, 0.9, 1)

# Function to generate the chessboard
for row in range(8):
    for col in range(8):
        pos_x = row - 3.5
        pos_y = col - 3.5
        selected_material = mat_dark if (row + col) % 2 == 0 else mat_light
        bpy.ops.mesh.primitive_cube_add(size=1, location=(pos_x, pos_y, 0))
        square = bpy.context.object
        square.name = f"Tile_{row}_{col}"
        square.data.materials.append(selected_material)

# Functions to create chess pieces
def create_piece_cylinder(radius, height, position):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)

def create_piece_cube(size, position):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)

def create_piece_cone(radius_top, radius_bottom, height, position):
    bpy.ops.mesh.primitive_cone_add(radius1=radius_top, radius2=radius_bottom, depth=height, location=position)

def create_piece_sphere(radius, position):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=position)

# Create chess pieces
for idx in range(8):
    create_piece_cylinder(0.3, 0.1, (idx - 3.5, -2.5, 0.05))
create_piece_cube(0.8, (-3.5, -3.5, 0.05))
create_piece_cube(0.8, (3.5, -3.5, 0.05))
create_piece_cylinder(0.25, 0.1, (-2.5, -3.5, 0.05))
create_piece_cylinder(0.25, 0.1, (2.5, -3.5, 0.05))
create_piece_cone(0.3, 0.1, 0.8, (-1.5, -3.5, 0.05))
create_piece_cone(0.3, 0.1, 0.8, (1.5, -3.5, 0.05))
create_piece_sphere(0.35, (0.5, -3.5, 0.05))
create_piece_cylinder(0.3, 0.15, (-0.5, -3.5, 0.05))
create_piece_sphere(0.25, (-0.5, -3.5, 0.25))


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
