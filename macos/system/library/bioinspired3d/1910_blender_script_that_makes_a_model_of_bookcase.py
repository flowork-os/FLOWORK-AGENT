# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_makes_a_model_of_bookcase" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that makes a model of bookcase.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Define shelf dimensions
width = 2
height = 0.1
depth = 0.4
spacing = 0.5
shelf_count = 3

# Function to create a shelf
def create_shelf(index):
    z_position = index * spacing
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf_object = bpy.context.object
    shelf_object.scale = (width / 2, depth / 2, height / 2)
    shelf_object.name = f'Shelf {index + 1}'
    shelf_object.data.materials.append(wood_material)

# Create shelves using the helper function
for i in range(shelf_count):
    create_shelf(i)

# Create the top surface
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, shelf_count * spacing))
top_surface = bpy.context.object
top_surface.scale = (width / 2, depth / 2, 0.05)
top_surface.name = 'Top Surface'
top_surface.data.materials.append(wood_material)

# Function to create side panels
def create_side_panel(index):
    x_position = width / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, shelf_count * spacing / 2))
    side_panel = bpy.context.object
    side_panel.scale = (0.025, depth / 2, shelf_count * spacing / 2)
    side_panel.name = f'Side Panel {index + 1}'
    side_panel.data.materials.append(wood_material)

# Create side panels
for i in range(2):
    create_side_panel(i)


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
