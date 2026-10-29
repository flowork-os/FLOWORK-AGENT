# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_bookshelf_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of bookshelf in python blender code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Define shelf parameters
width = 2.0
height = 0.1
depth = 0.4
number_of_shelves = 5
spacing = 0.6

# Function to create shelves

def create_shelves():
    for index in range(number_of_shelves):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
        current_shelf = bpy.context.object
        current_shelf.scale = (width / 2, depth / 2, height / 2)
        current_shelf.name = f'Shelf_{index + 1}'
        current_shelf.data.materials.append(wood_material)

create_shelves()

# Function to create side panels

def create_panels():
    panel_thickness = 0.05
    total_height = number_of_shelves * spacing
    for index in range(2):
        x_location = (width / 2) * (index * 2 - 1)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x_location, 0, total_height / 2))
        current_panel = bpy.context.object
        current_panel.scale = (panel_thickness / 2, depth / 2, total_height / 2)
        current_panel.name = f'Panel_{index + 1}'
        current_panel.data.materials.append(wood_material)

create_panels()


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
