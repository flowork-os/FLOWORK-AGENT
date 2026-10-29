# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_generates_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that generates bookshelf.

import bpy

# Clear existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the bookshelf
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Set to a brown shade

# Define shelf parameters
height_of_shelf = 0.1
width_of_shelf = 0.5
depth_of_shelf = 0.2
number_of_shelves = 5
spacing_between_shelves = 0.4

# Function to create shelves
for index in range(number_of_shelves):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing_between_shelves))
    shelf_object = bpy.context.object
    shelf_object.scale = (width_of_shelf / 2, depth_of_shelf / 2, height_of_shelf / 2)
    shelf_object.name = f'Shelf {index + 1}'
    shelf_object.data.materials.append(wood_material)

# Function to create side panels
side_panel_thickness = 0.05
height_of_panels = number_of_shelves * spacing_between_shelves

for side in range(2):
    x_position = (width_of_shelf / 2) * (side * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, height_of_panels / 2))
    panel_object = bpy.context.object
    panel_object.scale = (side_panel_thickness / 2, depth_of_shelf / 2, height_of_panels / 2)
    panel_object.name = f'Side Panel {side + 1}'
    panel_object.data.materials.append(wood_material)


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
