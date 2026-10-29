# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_code_in_Blender__construct_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with code in Blender, construct a model of bookshelf.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the wood
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a shelf

def create_shelf(index, width, depth, height, spacing):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f'Shelf_{index + 1}'
    shelf.data.materials.append(wood_material)

# Shelf parameters
shelf_height = 0.1
shelf_depth = 0.5
shelf_width = 2
shelf_spacing = 0.6
num_shelves = 5

# Create shelves using the helper function
for i in range(num_shelves):
    create_shelf(i, shelf_width, shelf_depth, shelf_height, shelf_spacing)

# Function to create side panels

def create_side(location, thickness, height):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    side = bpy.context.object
    side.scale = (thickness / 2, shelf_depth / 2, height / 2)
    side.data.materials.append(wood_material)
    return side

# Side parameters
side_thickness = 0.1
side_height = num_shelves * shelf_spacing

# Create left and right sides
create_side((-shelf_width / 2 + side_thickness / 2, 0, side_height / 2), side_thickness, side_height)
create_side((shelf_width / 2 - side_thickness / 2, 0, side_height / 2), side_thickness, side_height)


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
