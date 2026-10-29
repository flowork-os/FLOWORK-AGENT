# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_python_code_create_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender python code create bookshelf

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the wood appearance
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create shelves

def create_shelves(count, width, height, depth, spacing):
    for index in range(count):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
        shelf = bpy.context.object
        shelf.scale = (width / 2, depth / 2, height / 2)
        shelf.name = f'Shelf_{index + 1}'
        shelf.data.materials.append(wood_material)

# Create 5 shelves
create_shelves(5, 2, 0.1, 0.4, 0.6)

# Function to create vertical supports

def create_supports(count, width, height, depth):
    for index in range(count):
        x_position = width / 2 * (index * 2 - 1)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, height / 2))
        support = bpy.context.object
        support.scale = (0.025, depth / 2, height / 2)
        support.name = f'Support_{index + 1}'
        support.data.materials.append(wood_material)

# Create 2 vertical supports
create_supports(2, 2, 3.0, 0.05)


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
