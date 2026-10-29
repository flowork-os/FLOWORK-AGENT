# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_makes_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that makes a model of bookshelf

import bpy

# Clear the current Blender scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a material for the bookshelf
material_wood = bpy.data.materials.new(name='Wooden Finish')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Constants for the bookshelf construction
thickness_sides = 0.1
height_sides = 2.0
depth_sides = 0.3
positions_sides = [(-0.5, 0, 1), (0.5, 0, 1)]

# Create bookshelf sides
for position in positions_sides:
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    side_mesh = bpy.context.object
    side_mesh.scale = (thickness_sides, depth_sides, height_sides)
    side_mesh.name = 'Bookshelf Side'
    side_mesh.data.materials.append(material_wood)

# Shelf dimensions
thickness_shelves = 0.1
width_shelves = 1.0
depth_shelves = 0.3
shelf_count = 5
height_between_shelves = height_sides / (shelf_count + 1)

# Create shelves
for i in range(shelf_count):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height_between_shelves * (i + 1)))
    shelf_mesh = bpy.context.object
    shelf_mesh.scale = (width_shelves, depth_shelves, thickness_shelves)
    shelf_mesh.name = f'Shelf {i + 1}'
    shelf_mesh.data.materials.append(material_wood)


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
