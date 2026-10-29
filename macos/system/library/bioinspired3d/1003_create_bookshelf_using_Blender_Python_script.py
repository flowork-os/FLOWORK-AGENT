# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_bookshelf_using_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create bookshelf using Blender Python script

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define wood material
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf and support dimensions
shelf_width = 2.0
shelf_height = 0.1
shelf_depth = 0.4
shelf_spacing = 0.6
num_of_shelves = 5
support_dimensions = (0.05, num_of_shelves * shelf_spacing, 0.05)

# Function to add shelves

def add_shelves(number):
    for i in range(number):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, i * shelf_spacing))
        shelf = bpy.context.object
        shelf.scale = (shelf_width / 2, shelf_depth / 2, shelf_height / 2)
        shelf.name = f'Shelf_{i + 1}'
        shelf.data.materials.append(wood_material)

# Function to add supports

def add_supports():
    for i in range(2):
        x_position = shelf_width / 2 * (i * 2 - 1)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, support_dimensions[1] / 2))
        support = bpy.context.object
        support.scale = (support_dimensions[0] / 2, support_dimensions[2] / 2, support_dimensions[1] / 2)
        support.name = f'Support_{i + 1}'
        support.data.materials.append(wood_material)

# Execute shelf and support creation
add_shelves(num_of_shelves)
add_supports()


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
