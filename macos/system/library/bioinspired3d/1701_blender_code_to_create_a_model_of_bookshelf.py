# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_to_create_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code to create a model of bookshelf

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Dimensions for the shelf
width = 2.0
height = 0.1
depth = 0.4
spacing = 0.6
shelf_count = 5
thickness = 0.1

# Create a new material for the wood
wood_material = bpy.data.materials.new(name="WoodMaterial")
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a shelf
def create_shelf(index):
    z_position = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf_object = bpy.context.object
    shelf_object.scale = (width / 2, depth / 2, height / 2)
    shelf_object.name = f"Shelf_{index + 1}"
    shelf_object.data.materials.append(wood_material)

# Create shelves using a loop
for idx in range(shelf_count):
    create_shelf(idx)

# Function to create side panels
def create_side(index):
    x_position = width / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, (shelf_count * spacing) / 2))
    side_object = bpy.context.object
    side_object.scale = (thickness / 2, depth / 2, (shelf_count * spacing) / 2)
    side_object.name = f"Side_{index + 1}"
    side_object.data.materials.append(wood_material)

# Create side panels
for idx in range(2):
    create_side(idx)


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
