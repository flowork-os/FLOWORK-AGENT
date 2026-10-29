# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_script_build_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender script build a model of bookshelf

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf dimensions and parameters
width = 3.0
height = 0.1
depth = 0.5
spacing = 1.2
shelves_count = 5

# Function to create a shelf

def create_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
    shelf = bpy.context.object
    shelf.scale = (width / 2, depth / 2, height / 2)
    shelf.name = f'Shelf {index + 1}'
    shelf.data.materials.append(wood_material)

# Create shelves using the helper function
for i in range(shelves_count):
    create_shelf(i)

# Side panel parameters
panel_width = 0.05
panel_total_height = (shelves_count - 1) * spacing + height

# Function to create a side panel

def create_panel(index):
    x_position = (width / 2) * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_total_height / 2))
    panel = bpy.context.object
    panel.scale = (panel_width / 2, depth / 2, panel_total_height / 2)
    panel.name = f'Side Panel {index + 1}'
    panel.data.materials.append(wood_material)

# Create side panels
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
