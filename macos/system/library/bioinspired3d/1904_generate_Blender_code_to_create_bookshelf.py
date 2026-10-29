# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_to_create_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code to create bookshelf.

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Dimensions for the shelf
width = 1.0
height = 0.1
depth = 0.5
length = 3.0
spacing = 1.0
shelf_count = 4
full_height = shelf_count * spacing

# Create a wood material
wood_material = bpy.data.materials.new(name="WoodMaterial")
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a shelf
def create_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
    shelf = bpy.context.object
    shelf.scale = (length / 2, depth / 2, height / 2)
    shelf.name = f"Shelf_{index + 1}"
    shelf.data.materials.append(wood_material)

# Generate shelves
for idx in range(shelf_count):
    create_shelf(idx)

# Function to create side panels
def create_side_panel(index):
    x_position = (length / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, full_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (0.05, depth / 2, full_height / 2)
    side_panel.name = f"Side_{index + 1}"
    side_panel.data.materials.append(wood_material)

# Generate side panels
for idx in range(2):
    create_side_panel(idx)


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
