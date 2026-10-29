# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_code_in_Blender_construct_a_model_of_wall_decal" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With code in Blender construct a model of wall decal

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a light gray material for the wall
wall_material = bpy.data.materials.new(name='Wall Material')
wall_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Add the main wall surface
bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, 0))
main_wall = bpy.context.object
main_wall.name = 'Main Wall'
main_wall.data.materials.append(wall_material)

# Create a dark gray material for the squares
square_material = bpy.data.materials.new(name='Square Material')
square_material.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to create a square at a given position

def create_square(x, y):
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(x, y, 0.01))
    square_object = bpy.context.object
    square_object.name = f'Square_{x+2}_{y+2}'
    square_object.data.materials.append(square_material)

# Generate squares in a grid
for x in range(-2, 3):
    for y in range(-2, 3):
        create_square(x, y)


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
