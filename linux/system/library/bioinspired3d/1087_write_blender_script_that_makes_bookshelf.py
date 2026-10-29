# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_script_that_makes_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender script that makes bookshelf.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the bookshelf
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Define parameters for the sides of the bookshelf
thickness = 0.1
height = 2.0
depth = 0.3
positions = [(-0.5, 0, 1), (0.5, 0, 1)]

# Function to create bookshelf sides
def create_side(position):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    side = bpy.context.object
    side.scale = (thickness, depth, height)
    side.name = 'Bookshelf Side'
    side.data.materials.append(wood_material)

# Create each side
for pos in positions:
    create_side(pos)

# Parameters for the shelves
shelf_thickness = 0.1
shelf_width = 1.0
shelf_depth = 0.3
shelf_count = 5
shelf_spacing = height / (shelf_count + 1)

# Function to create shelves
def create_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, shelf_spacing * (index + 1)))
    shelf = bpy.context.object
    shelf.scale = (shelf_width, shelf_depth, shelf_thickness)
    shelf.name = f'Shelf {index + 1}'
    shelf.data.materials.append(wood_material)

# Create all shelves
for i in range(shelf_count):
    create_shelf(i)


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
