# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_to_make_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script to make a model of bookshelf

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color resembling wood

# Function to create a shelf
def create_shelf(index, width, height, depth, spacing):
    z_position = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf_object = bpy.context.object
    shelf_object.scale = (width / 2, depth / 2, height / 2)
    shelf_object.name = f'Shelf_{index + 1}'
    shelf_object.data.materials.append(wood_material)

# Parameters for shelves
shelf_width = 2
shelf_height = 0.1
shelf_depth = 0.4
shelf_spacing = 0.5
number_of_shelves = 5

# Create multiple shelves
for index in range(number_of_shelves):
    create_shelf(index, shelf_width, shelf_height, shelf_depth, shelf_spacing)

# Function to create side panels
def create_panel(index, thickness, height, depth):
    x_position = (shelf_width / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, height / 2))
    panel_object = bpy.context.object
    panel_object.scale = (thickness / 2, depth / 2, height / 2)
    panel_object.name = f'SidePanel_{index + 1}'
    panel_object.data.materials.append(wood_material)

# Panel parameters
panel_thickness = 0.05
panel_height = number_of_shelves * shelf_spacing

# Create side panels
for index in range(2):
    create_panel(index, panel_thickness, panel_height, shelf_depth)


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
