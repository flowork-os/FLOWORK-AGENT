# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_bookshelf_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of bookshelf in a Blender script

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
shelf_material = bpy.data.materials.new(name="ShelfMaterial")
shelf_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf dimensions and configuration
width = 2
height = 0.1
depth = 0.4
spacing = 0.6
shelf_count = 5

# Function to create a shelf

def create_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f"Shelf_{index + 1}"
    shelf.data.materials.append(shelf_material)

# Generate shelves
for i in range(shelf_count):
    create_shelf(i)

# Vertical side dimensions
side_width = 0.05
full_height = shelf_count * spacing

# Function to create a side

def create_side(index):
    x_position = (width / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, full_height / 2))
    side = bpy.context.object
    side.scale = (side_width / 2, depth / 2, full_height / 2)
    side.name = f"Side_{index + 1}"
    side.data.materials.append(shelf_material)

# Generate sides
for i in range(2):
    create_side(i)


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
