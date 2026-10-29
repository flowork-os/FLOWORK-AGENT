# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_script_to_make_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender script to make a model of bookshelf

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material for the bookshelf
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a panel

def create_panel(location, scale, name):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    panel = bpy.context.object
    panel.scale = scale
    panel.name = name
    panel.data.materials.append(wood_material)

# Create the left and right panels
create_panel((-1, 0, 1), (0.1, 1, 2), 'Left Panel')
create_panel((1, 0, 1), (0.1, 1, 2), 'Right Panel')

# Function to create shelves

def create_shelf(z_position, name):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (1, 1, 0.1)
    shelf.name = name
    shelf.data.materials.append(wood_material)

# Create shelves at different heights
for index in range(3):
    create_shelf(0.5 + index, f'Shelf {index + 1}')


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
