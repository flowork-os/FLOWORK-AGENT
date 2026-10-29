# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_code_that_creates_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender code that creates bookshelf

import bpy

# Clear the existing scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the wood
wood_material = bpy.data.materials.new(name="Wood Material")
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Constants for shelf dimensions
width = 0.5
height = 0.1
depth = 0.2
spacing = 0.4
shelf_count = 3

# Function to create shelves
def create_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f"Shelf {index + 1}"
    shelf.data.materials.append(wood_material)

# Generate shelves
for i in range(shelf_count):
    create_shelf(i)

# Function to create side panels
def create_panel(index):
    x_position = width / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, (shelf_count * spacing) / 2 - height / 2))
    panel = bpy.context.object
    panel.scale = (0.025, depth / 2, (shelf_count * spacing) / 2)
    panel.name = f"Side Panel {index + 1}"
    panel.data.materials.append(wood_material)

# Generate side panels
for i in range(2):
    create_panel(i)


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
